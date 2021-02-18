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

# Audio recording + processing
from scipy.io.wavfile import read, write
import sounddevice as sd
import soundfile as sf

# Initialization
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'cs329s-covid-caugh-prediction-63c10ece8027.json'
COVID_IMAGE_PATH = './assets/covid.png'
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

def record_cough(progress, status, sr, duration=5, channels=1):
  """
  Records cough sound and returns a wav byte array.

  Args:
    progress (st.empty): streamlit placeholder for progress bar
    status (st.empty): streamlit placeholder for status bar
    sr (int): sample rate
    duration (int): duration of recording, default 5 seconds
    channels (int): recording channels, default mono
  Returns:
    recording (np.array): user recording
  """
  recording = sd.rec(int(duration * sr), channels=channels).reshape(-1)

  # Show progress bar
  status.warning('Recording... 0.0/5.0s')
  for percent_complete in range(100):
    time.sleep(0.05)
    status.warning(f'Recording... {(percent_complete / 100 * 5):.1f}/5.0s')
    progress.progress(percent_complete + 1)

  # Wait in case there is a mismatch between progress and actual recording
  sd.wait()
  progress.empty()
  return recording

def review_recording(recording, sr, cough_conf, status):
  """
  Loads the recorded cough sound and allows user to review.

  Args:
    recording (np.array): user recording
    sr (int): sample rate
    cough_conf (float): cough detection model confidence
    status (st.empty): streamlit placeholder
  """
  # Convert to wav bytes object
  bytes_wav = bytes()
  byte_recording = io.BytesIO(bytes_wav)
  write(byte_recording, sr, recording)

  st.write('Review your recording:')

  # Check if cough was detected
  if cough_conf < 0.20:
    status.error('We did not detect a cough in your recording. Please try again.')
  elif cough_conf < 0.55:
    status.warning('If possible, please cough more forcefully. Otherwise, proceed.')
  else:
    status.success('Cough sucessfully recorded.')

  st.audio(byte_recording, format='audio/wav')

def assess_device_samplerate():
  """
  Returns the device's default sampling rate and a string stating the sampling quality.

  Returns:
    default_samplerate (int): device's default samplerate
    sample_string (str): string indicating microphone quality
  """
  default_samplerate = int(sd.query_devices()[sd.default.device[0]]['default_samplerate'])
  sample_string = 'Your device\'s microphone quality: '

  if default_samplerate <= 16000:
    sample_string += ':pensive:'
  elif default_samplerate <= 22100:
    sample_string += ':neutral_face:'
  else:
    sample_string += ':grinning:'

  return default_samplerate, sample_string

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

def main():
  setup_page()

  st.image(COVID_IMAGE_PATH, width=80)
  st.title('Covid-19 Risk Evaluation')
  st.write('This app evaluates your risk for Covid-19 based on coughs recorded from your device.')

  default_samplerate, sample_string = assess_device_samplerate()
  st.info(f'{sample_string}') #A reasonable recording quality is important to get the most accurate results.\n\n
 
  st.subheader('Record a 5 Second Cough Sample')
  st.write('Please minimize any background noise.')

  if st.button('Start Recording'):
    status_placeholder = st.empty()
    recording_bar = st.empty()

    recording_bar.progress(0)
    recording = record_cough(recording_bar, status_placeholder, default_samplerate)

    cough_conf = detect_cough(recording, default_samplerate)
    review_recording(recording, default_samplerate, cough_conf, status_placeholder)


if __name__ == '__main__':
  main()