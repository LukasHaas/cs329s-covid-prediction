import io
import os
import time
import json
import uuid
import requests
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt
import streamlit.components.v1 as components

# App modules
import src.Utils as Utils
from src.CoughDetector import CoughDetector
from src.CustomComponents import CovidRecordButton

# Audio recording + processing
from scipy.io import wavfile
import sounddevice as sd
import soundfile as sf

# Initialization
#os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'gcp-service-account.json'

# Constants
PROJECT = 'cs329s-covid-caugh-prediction'
REGION = 'us-central1'
COVID_MODEL = 'MVP_XGBoost'
COUGH_STORAGE_BUCKET = 'cs329s-covid-user-coughs'

SYMPTOMS = [
  'fever',
  'dry cough',
  'tiredness',
  'difficulty breathing or shortness of breath',
  'chest pain or pressure',
  'loss of speech or movement',
  'aches and pains',
  'sore throat',
  'diarrhoea',
  'conjunctivitis',
  'headache',
  'loss of taste or smell',
  'a rash on skin, or discolouration of fingers or toes'
]

COUGH_DETECTOR = CoughDetector()

@st.cache(show_spinner=False)
def detect_cough(recording, sr):
  """
  Predicts whether a cough is present in the recording using model stored in app.

  Args:
    recording (np.array): user recording.
    sr (int): sample rate
  Returns:
    pred_conf (float): predicted confidence of cough existence.
  """
  features = COUGH_DETECTOR.extract_features(recording, sr)
  pred_conf = COUGH_DETECTOR.classify_cough(features)
  return features, pred_conf

def review_recording(recording_url, cough_conf, rate, audio):
  """
  Loads the recorded cough sound and allows user to review.

  Args:
    recording_url (str): url to audio blob file
    cough_conf (float): cough detection model confidence
  """

  st.write('Review your recording:')

  # Check if cough was detected
  if cough_conf < 0.20:
    st.error('We did not detect a cough in your recording. Please try again.')
  elif cough_conf < 0.55:
    st.warning('If possible, please cough more forcefully. Otherwise, proceed.')
  else:
    st.success('Cough sucessfully recorded.')

  # Display audio
  inject_audio_spectogram(rate, audio)
  inject_audio_player(recording_url)

def hide_menu():
  """
  Hides streamlit menu by injecting HTML & CSS.
  """
  hide_streamlit_style = """
  <style>
  #MainMenu {visibility: hidden;}
  footer {visibility: hidden;}
  </style>
  """
  st.markdown(hide_streamlit_style, unsafe_allow_html=True)

def inject_audio_player(blob_url):
  """
  Adds audio in form of a blob.

  Args:
    blob_url (str): blob URL
  """
  audio_display = f"""<audio controls src={blob_url} style="width:100%;" type='audio/wav'></audio>"""
  st.markdown(audio_display, unsafe_allow_html=True)

def inject_audio_spectogram(rate, audio):
  """
  Adds audio spectogram.

  Args:
    rate (int): frequency of the audio.
    audio (): audio recording.
  """
  audio_downscaled = audio / (2.**15)
  sample_points = float(audio_downscaled.shape[0])
  sound_duration =  audio_downscaled.shape[0] / rate
  time_array = np.arange(0, sample_points, 1)
  time_array = time_array / rate
  time_array = time_array * 1000

  fig = plt.figure()
  ax = fig.add_subplot(1,1,1)
  ax.plot(time_array, audio_downscaled)
  ax.set_xlabel("Time (ms) ")
  ax.set_ylabel("Amplitude")
  st.write(fig)

def check_for_new_recording(recording, session_state):
  """
  Checks if a new recoding was made.

  Args:
    recording (str): JSON string of recording
    session_state (SessionState): session state
  """
  if session_state.recording_hash != hash(recording):
    print('New recording recorded.')
    # session_state.cough_donated = False
    session_state.cough_uuid = str(uuid.uuid4())
    session_state.recording_hash = hash(recording)

def consent(session_state):
    # Consent
    st.info("""
    Your cough recording or symptom information will be used for prediction,
    but they won't be stored. You can help accelerate research if you contribute
    your cough for research purposes. If you are willing to, please check the
    box below.""")

    if not session_state.cough_donated:
      consent_cough = st.checkbox('I agree to anonymously donate my cough for research purposes.')
      session_state.cough_donated = True
      if consent_cough:
        with st.spinner('Uploading cough ...'):
          Utils.upload_blob(COUGH_STORAGE_BUCKET, recording, f'perm_data/{session_state.cough_uuid}.wav')
        st.success('Successfully donated cough.')

    # TODO: Implement revoking consent

    if session_state.symptoms_shared and not session_state.symptoms_donated:
      consent_symptoms = st.checkbox('I agree to anonymously share my symptoms for research purposes.')
      session_state.symptoms_donated = True
      # TODO: Upload symptoms
    # TODO: Implement revoking consent

    if session_state.cough_donated or session_state.symptoms_donated:
      # Future steps
      st.subheader('Future Steps')
      st.write("""
      We use PCR test results to better train our models. If you have plan to
      take a PCR test and would like to share your results, below is a unique
      number you can use to log back on when you get back to our app. Once
      you have your results ready, select that you are a returning user in the
      dropdown menu on the top of the page.""")
      st.info(session_state.cough_uuid)

      # # PCR test upload
      # st.write("""
      # If you already have PCR test results ready and would like to share them,
      # you can also do so here.
      # """)
      # # TODO

def app(session_state):
  #default_samplerate, sample_string = Utils.assess_device_samplerate()
  #st.info(f'{sample_string}') #A reasonable recording quality is important to get the most accurate results.\n\n

  st.subheader('Record a 5 Second Cough Sample')
  st.write('Please minimize any background noise.')

  # Custom Streamlit component using javascript to query client-side microphone devices
  recording = CovidRecordButton(duration=5000)

  if recording and recording is not None:

    # Get recording and display audio bar
    rec = json.loads(recording)
    rate, audio = wavfile.read(io.BytesIO(bytes(rec['data'])))
    cough_features, cough_conf = detect_cough(audio, rate)
    print('Cough features:\n', cough_features.tolist())
    review_recording(rec['url'], cough_conf, rate, audio)

    # Check if new recording was submitted and adjust session state.
    check_for_new_recording(recording, session_state)

    # Share symptoms
    st.subheader('Share Extra Information')
    st.write('Our models can work better if you share some extra information about yourself and your symptoms, although doing so isn\'t required for prediction.')
    consent_symptoms_for_prediction = st.checkbox('I would like to share symptoms for prediction.')
    if consent_symptoms_for_prediction:
      # selected_symptoms = st.multiselect('Symptoms (leave empty if you have no symptoms)', SYMPTOMS)
      session_state.symptoms_shared = True

    # Get Covid-19 Risk Evaluation
    st.subheader('Covid-19 Risk Evaluation')
    st.write('Click below to anonymously submit your cough for a Covid-19 risk evaluation.')
    request_prediction = st.button('Submit Cough For Evaluation')

    if request_prediction:
      with st.spinner('Requesting risk evaluation ...'):
        Utils.upload_blob(COUGH_STORAGE_BUCKET, recording, f'temp_data/{session_state.cough_uuid}.wav')

        try:
          covid_pred = Utils.get_inference(PROJECT, COVID_MODEL, cough_features.tolist())[0]
          if covid_pred == 1:
            st.error('It appears you might have Covid-19.')
          else:
            st.success('It appears you are Covid-19 free.')
            session_state.successful_prediction = True
        except:
          st.error('An error occured requesting your Covid-19 risk evaluation.')

        consent(session_state)
