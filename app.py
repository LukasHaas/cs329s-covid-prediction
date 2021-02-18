# Covid Detection MVP App - Streamlit
# -----------------------------------
# L. Haas, D. Soylu, J. Spencer
#

import io
import time

import streamlit as st
import src.SessionState as SessionState

from scipy.io.wavfile import read, write

# Data manipulation
#import numpy as np
#import matplotlib.pyplot as plt

# Feature extraction
#import scipy
#import librosa
#import python_speech_features as mfcc
#import os
#from scipy.io.wavfile import read

# Model training
#from sklearn import preprocessing
#from sklearn.mixture import GaussianMixture as GMM
#import pickle

# Live recording
import sounddevice as sd
import soundfile as sf

COVID_IMAGE_PATH = './assets/covid.png'

def record_cough(progress, status, sr, duration=5, channels=1):
  """
  Records cough sound and returns a wav byte array.
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
  status.success('Cough recorded.')
  progress.empty()

  # Convert to wav bytes object
  bytes_wav = bytes()
  byte_recording = io.BytesIO(bytes_wav)
  write(byte_recording, sr, recording)

  #sf.write(filename, data=recording, samplerate=sr)
  return byte_recording

def review_recording(recording):
  """
  Loads the recorded cough sound and allows user to review.
  """
  st.write('Review your recording:')
  st.audio(recording, format='audio/wav')

def assess_device_samplerate():
  """
  Returns the device's default sampling rate and a string stating the sampling quality.
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
    review_recording(recording)


if __name__ == '__main__':
  main()