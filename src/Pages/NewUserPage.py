import io
import os
import time
import json
import uuid
import requests
import logging
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import RendererAgg
import streamlit.components.v1 as components
import librosa
import librosa.display

# App modules
import src.Utils as Utils
from src.CovidClassifier import CovidClassifier
from src.CoughDetector import CoughDetector
from src.CustomComponents import CovidRecordButton
from src.MockData.KeyPhrases import KEY_PHRASES

# Audio recording + processing
from scipy.io import wavfile
import sounddevice as sd
import soundfile as sf

# Initialization
CREDENTIALS_FILE = 'gcp-service-account.json'
if os.path.isfile(CREDENTIALS_FILE):
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = CREDENTIALS_FILE

# Project Constants
PROJECT = os.environ['GCP_PROJECT']
REGION = os.environ['GCP_REGION']
COUGH_STORAGE_BUCKET = os.environ['GCP_COUGH_STORAGE']

# String Constants
NOT_SELECTED = 'No selection'
YES_ANSWER = 'Yes'
NO_ANSWER = 'No'
# BINARY_ANSWERS = [NOT_SELECTED, NO_ANSWER, YES_ANSWER]
BINARY_ANSWERS = [NO_ANSWER, YES_ANSWER]

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

# Classifiers
COUGH_DETECTOR = CoughDetector()
COVID_CLASSIFIER = CovidClassifier()

# Prevent Matplotlib Bug
_lock = RendererAgg.lock


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
    pred_conf = COUGH_DETECTOR.classify_cough(features)[0]
    logging.info('Cough Detection Prediction:', pred_conf)
    return pred_conf

@st.cache(show_spinner=False)
def predict_covid(recording, sr, clinical_features):
    """Predicts if the cough is healthy, symptomatic (could be any class), or Covid-19.

    Args:
        recording (np.array): cough recording
        sr (int): cough's sample rate
    """
    pred_conf = COVID_CLASSIFIER.classify_cough(recording, sr, clinical_features)
    logging.info('Covid Predictions:', pred_conf.tolist())
    return np.argmax(pred_conf)

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
    elif cough_conf < 0.50:
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
    x_values = np.arange(len(audio)) / rate

    with _lock:
        fig = plt.figure(figsize=(10, 3))
        ax = fig.add_subplot(1, 1, 1)
        ax.plot(x_values, audio)
        ax.set_xlabel("Time (s) ")
        ax.set_ylabel("Amplitude")
        st.pyplot(fig)


def check_for_new_recording(recording, session_state):
    """
    Checks if a new recoding was made.

    Args:
      recording (str): JSON string of recording
      session_state (SessionState): session state
    """
    if session_state.recording_hash != hash(recording):
        # session_state.cough_donated = False
        session_state.cough_uuid = str(uuid.uuid4())
        session_state.recording_hash = hash(recording)


def pcr_test_phrase(session_state):
    """
    TODO
    """
    # TODO ask if they have a PCR test result
    if session_state.cough_donated or session_state.symptoms_donated:
        # Future steps
        st.subheader('Future Steps')
        st.write("""
        We use PCR test results to better train our models. If you have plan to
        take a PCR test and would like to share your results, please enter a
        phrase below which we will use to tie your results back to your
        evaluation in our system when you come back. Once
        you have your results ready, select that you are a returning user in the
        dropdown menu on the top of the page and enter your phrase.""")

        phrase = st.text_input('Type your phrase')
        phrase_set_button = st.button('Set Phrase')

        if phrase_set_button:
            if phrase.strip() in KEY_PHRASES:
                st.error("""
                The phrase you typed is already in use. Can you select a different phrase?
                """)
            else:
                with st.spinner('Setting your phrase ...'):
                    try:
                        KEY_PHRASES.append(phrase.strip())
                        time.sleep(2) # TODO replace with actual upload
                        st.success(
                        f"""
                        Successfully set your phrase. When you return, please
                        select the returning user option in the dropdown on
                        top of the page, then enter the phrase {phrase} when asked.
                        """)
                    except:
                        st.error('An error occured setting your phrase. Please try again.')

def inject_segmented_spectrogram(x, fs):
    """Inserts a cough-segmented spectrogram.

    Args:
        signal (np.array): audio as a 1-D numpy array
        fs (int): sample rate
    """
    max_signal = np.max(np.abs(x))
    normalized_audio = Utils.normalize_audio(x, fs, shouldTrim=False)
    cough_segments, cough_mask = Utils.segment_cough(normalized_audio, fs)
    
    if np.max(cough_mask) == 0:
        st.error('We did not detect strong coughs to segment.')

    cough_mask = cough_mask * max_signal
    x_values = np.arange(len(normalized_audio)) / fs

    with _lock:
        seg_fig = plt.figure(figsize=(10, 3))
        ax = seg_fig.add_subplot(1, 1, 1)
        ax.plot(x_values, x)
        ax.plot(x_values, cough_mask)
        ax.set_xlabel("Time (s) ")
        ax.set_ylabel("Amplitude")
        st.pyplot(seg_fig)

def detail_recording(x, fs):
    """
    Loads the recorded cough sound and allows user to review.

    Args:
    recording_url (str): url to audio blob file
    cough_conf (float): cough detection model confidence
    """
    st.write('In order to create features for our model, we look at the cough segments recognized in your audio, as \
              displayed below.')
    # Display audio
    inject_segmented_spectrogram(x, fs)
    st.write('An important step we take before analyzing your audio is applying a Fourier transformation which \
              in simple terms displays the frequencies that are present in your cough in a logarithmic scale.\
              Displayed below is what your audio looks like after this transformation.')
    inject_mel_spectrogram(x, fs)

def inject_mel_spectrogram(x, fs):
    """Displays a mel-spectrogram.

    Args:
        x (np.array): audio input as 1-D numpy array
        fs (int): sample rate
    """
    S = librosa.feature.melspectrogram(y=x, sr=fs)

    with _lock:
        mel_fig, ax = plt.subplots()
        S_dB = librosa.power_to_db(S, ref=np.max)
        img = librosa.display.specshow(S_dB, x_axis='time',
                                    y_axis='mel', sr=fs)
        mel_fig.colorbar(img, ax=ax, format='%+2.0f dB')
        ax.set(title='Mel-frequency spectrogram')
        st.pyplot(mel_fig)

def prediction_explanation(session_state, x, fs):
    st.subheader('Learn more about your prediction')
    st.write('We make our predictions using a model that combines both the cough recording \
              and the extra information you have provided. Click below to learn how our model is deriving your \
              risk factor.')
    learn_more = st.button('Learn more')
    if learn_more:
        detail_recording(x, fs)

    # TODO John, extra personalized prediction info here.

def consent(session_state, recording, cough_conf):
    # Consent
    st.subheader('Contribute to Research')
    st.info("""
    Your cough recording and extra information provided were used for prediction,
    but they aren't stored. You can help accelerate research if you contribute
    your cough and extra information for research purposes. If you are willing
    to, please check the boxes below.""")

    consent_cough = st.checkbox('I agree to anonymously donate my cough and extra information provided for research purposes.')
    if consent_cough and not session_state.cough_donated:
        if cough_conf > 0.5:
            with st.spinner('Uploading information ...'):
                Utils.upload_blob(COUGH_STORAGE_BUCKET, recording, f'user_cough_data/{session_state.cough_uuid}.wav')
        st.success('Successfully uploaded!')
        session_state.cough_donated = True
        session_state.symptoms_donated = True
    # TODO: Implement revoking consent

def risk_evaluation(session_state, recording, audio, sr, extra_information):
    # Get Covid-19 Risk Evaluation
    st.subheader('Covid-19 Risk Evaluation')
    st.write(
        'Click below to anonymously submit your cough and extra information (if provided) for a Covid-19 risk evaluation.')
    request_prediction = st.button('Get Evaluation Results')

    if request_prediction:
      with st.spinner('Requesting risk evaluation ...'):
          try:
              covid_pred = predict_covid(audio, sr, extra_information)
              if covid_pred == 2:
                  st.error('Based off your cough sample and background information we do believe you are at risk for having Covid.')
              elif covid_pred == 1:
                  st.warning('Your cough sample and background information correlates with real world examples of symptomatic \
                  users who did not test positive, please keep in mind there is still a risk you have Covid-19.')
              else:
                  st.success('Based off your cough sample and background information we do not believe you have Covid-19.')
              session_state.successful_prediction = True
          except:
              st.error('An error occured requesting your Covid-19 risk evaluation.')

def get_boolean_value(value):
    if value == YES_ANSWER:
        return True
    elif value == NO_ANSWER:
        return False
    else:
        return None


def app(session_state):
    st.subheader('Record a 5 Second Cough Sample')
    st.write('Please minimize any background noise.')

    # Custom Streamlit component using javascript to query client-side microphone devices
    recording = CovidRecordButton(duration=5000)

    if recording and recording is not None:
        # Get recording and display audio bar
        rec = json.loads(recording)
        x, fs = librosa.load(io.BytesIO(bytes(rec['data'])))
        logging.info('Audio recorded:', x[:10])
        rate, audio = wavfile.read(io.BytesIO(bytes(rec['data'])))
        
        try:
            cough_conf = detect_cough(audio, rate)
            logging.info('Successfully recorded cough.')

        except ValueError:
            cough_conf = 0.0
            logging.error('Error recording cough.')
            st.error('An error occured recording your cough. Please try again using a different input device.')
            
        review_recording(rec['url'], cough_conf, rate, audio)

        # Check if new recording was submitted and adjust session state.
        check_for_new_recording(recording, session_state)

        # Share extra information
        st.subheader('Share Extra Information')
        st.write("""
        Our models work better if you share some extra information about yourself
        and your symptoms, although doing so isn\'t required for prediction. Please
        answer the following short questions.
        """)
        respiratory_condition = st.selectbox('Do you have a history of respiratory issues (e.g. asthma)?', BINARY_ANSWERS)
        col1, col2 = st.beta_columns(2)
        fever = col1.selectbox('Do you have a fever?', BINARY_ANSWERS)
        muscle_pain = col2.selectbox('Do you have muscle pain?', BINARY_ANSWERS)
        age = st.number_input('How old are you?', min_value=0, max_value=140, value=35, step=1, format='%d')
        extra_information = {
            'respiratory_condition': get_boolean_value(respiratory_condition),
            'fever_muscle_pain': get_boolean_value(fever) or get_boolean_value(muscle_pain),
            'age': int(age)
        }

        # Get risk evaluation
        risk_evaluation(session_state, recording, audio, rate, extra_information)
        if session_state.successful_prediction:
            prediction_explanation(session_state, x, fs)
            consent(session_state, recording, cough_conf)
            pcr_test_phrase(session_state)
