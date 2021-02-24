# Covid Detection MVP App - Streamlit
# -----------------------------------
# L. Haas, D. Soylu, J. Spencer
#

import io
import os
import time
import json
import uuid
import requests
import numpy as np
import streamlit as st
import streamlit.components.v1 as components

# App modules
import src.SessionState as SessionState
import src.Utils as Utils
from src.CoughDetector import CoughDetector
from src.CustomComponents import CovidRecordButton

# Audio recording + processing
from scipy.io import wavfile
import sounddevice as sd
import soundfile as sf

# Initialization
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'gcp-service-account.json'

# Constants
COVID_IMAGE_URL = './assets/covid.png'
PROJECT = 'cs329s-covid-caugh-prediction'
REGION = 'us-central1'
COUGH_STORAGE_BUCKET = 'cs329s-covid-user-coughs'

# SYMPTOMS = [
#   'fever',
#   'dry cough',
#   'tiredness',
#   'difficulty breathing or shortness of breath',
#   'chest pain or pressure',
#   'loss of speech or movement',
#   'aches and pains',
#   'sore throat',
#   'diarrhoea',
#   'conjunctivitis',
#   'headache',
#   'loss of taste or smell',
#   'a rash on skin, or discolouration of fingers or toes'
# ]

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

def review_recording(recording_url, cough_conf):
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
  inject_audio(recording_url)

def setup_page():
  """
  Applies site-wide settings.
  """
  st.set_page_config(page_title='Covid Risk Evaluation', page_icon=COVID_IMAGE_URL, layout='centered')
  hide_menu()

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

def inject_audio(blob_url):
  """
  Adds audio in form of a blob.

  Args:
    blob_url (str): blob URL
  """
  audio_display = f"""<audio controls src={blob_url} style="width:100%;" type='audio/wav'></audio>"""
  components.html(audio_display, height=70)

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

def information_section():
  """
  Render an information section
  """
  st.subheader('Information')
  st.write('We encourage you to read through the following information sections:')

  with st.beta_expander("Data Privacy Policy"):
    st.write("""
    Your cough recording will exclusively be used in order to serve you
    a Covid-19 risk evaluation. Under no circumstances will we share
    your data with any third parties. In addition, your Covid-19 risk
    evaluation will be generated entirely anonymously.
    """)

  with st.beta_expander("Disclaimer & Algorithm Details"):
    st.write("""
    This site is used for testing purposes and any Covid-19 risk evaluations
    are unaccruate as of this moment. We do not take any responsibility for
    the predictions made by this application.
    """)


def main():
  setup_page()
  session_state = SessionState.get(recording_hash=None, cough_donated=False, cough_uuid=None)

  st.image(COVID_IMAGE_URL, width=50)
  st.title('Covid-19 Risk Evaluation')
  
  st.write('This app evaluates your risk for Covid-19 based on coughs recorded from your device.')

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
    print('Cough features:\n', cough_features)
    review_recording(rec['url'], cough_conf)

    # Check if new recording was submitted and adjust session state.
    check_for_new_recording(recording, session_state)

    # Share your cough for research purposes
    if not session_state.cough_donated:
      consent_cough = st.checkbox('I agree to anonymously donate my cough for research purposes.')

      if consent_cough:
        with st.spinner('Uploading cough ...'):
          Utils.upload_blob(COUGH_STORAGE_BUCKET, recording, f'perm_data/{session_state.cough_uuid}.wav')
        st.success('Successfully donated cough.')
        session_state.cough_donated = True

    # TODO: Implement revoking consent

    # Get Covid-19 Risk Evaluation
    st.subheader('Covid-19 Risk Evaluation')
    st.write('If you click on the button below, your cough will be anonymously submited for a Covid-19 risk evaluation.')
    request_prediction = st.button('Submit Cough For Evaluation')

    if request_prediction:
      with st.spinner('Requesting risk evaluation ...'):
        Utils.upload_blob(COUGH_STORAGE_BUCKET, recording, f'temp_data/{session_state.cough_uuid}.wav')
        # send cough_features to servers

      # TODO: Ask for symptoms
      # st.info('If you are willing to also share your symptoms, this could greatly accelerate research.')
      # consent_symptoms = st.checkbox('I agree to anonymously share my symptoms for research purposes.')
      # if consent_symptoms:
      #   selected_symptoms = st.multiselect('Symptoms (leave empty if you have no symptoms)', SYMPTOMS)

  information_section()


if __name__ == '__main__':
  main()