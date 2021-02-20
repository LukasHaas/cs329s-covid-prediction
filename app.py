# Covid Detection MVP App - Streamlit
# -----------------------------------
# L. Haas, D. Soylu, J. Spencer
#

import io
import os
import time
import json
import requests
import numpy as np
import streamlit as st

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
__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'gcp-service-account.json'

COVID_IMAGE_PATH = os.path.join(__location__, 'assets', 'covid.png')
PROJECT = 'cs329s-covid-caugh-prediction'
REGION = 'us-central1'

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
  pred_conf = COUGH_DETECTOR.classify_cough(recording, sr)
  return pred_conf

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
  st.set_page_config(page_title='Covid Risk Evaluation', page_icon=COVID_IMAGE_PATH, layout='centered')
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
    st.markdown(audio_display, unsafe_allow_html=True)

def main():
  setup_page()

  st.image(COVID_IMAGE_PATH, width=80)
  st.title('Covid-19 Risk Evaluation')
  st.write('This app evaluates your risk for Covid-19 based on coughs recorded from your device.')

  default_samplerate, sample_string = Utils.assess_device_samplerate()
  st.info(f'{sample_string}') #A reasonable recording quality is important to get the most accurate results.\n\n
 
  st.subheader('Record a 5 Second Cough Sample')
  st.write('Please minimize any background noise.')

  # Custom Streamlit component using javascript to query client-side microphone devices
  recording = CovidRecordButton(duration=5000)

  if recording and recording is not None:
    rec = json.loads(recording)
    #Utils.upload_blob('cs329s-covid-user-coughs', recording, 'temp_data/user_cough.wav')
    rate, audio = wavfile.read(io.BytesIO(bytes(rec['data'])))
    cough_conf = detect_cough(audio, rate)
    review_recording(rec['url'], cough_conf)


if __name__ == '__main__':
  main()