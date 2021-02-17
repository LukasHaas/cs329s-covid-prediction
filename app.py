# Covid Detection MVP App - Streamlit
# -----------------------------------
# L. Haas, D. Soylu, J. Spencer
#

import streamlit as st
import src.SessionState as SessionState

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

def record_and_save(sr, duration=5, channels=1, filename='cough_temp.wav'):
  """
  Records cough sounds and saves them to file
  """
  recording = sd.rec(int(duration * sr), channels=channels).reshape(-1)
  sd.wait()
  sf.write(filename, data=recording, samplerate=sr)
  return recording

def review_recording():
  st.write('Review your recording:')
  audio_file = open('cough_temp.wav', 'rb')
  audio_bytes = audio_file.read()
  st.audio(audio_bytes, format='audio/wav')

def assess_device_samplerate():
  """
  Returns the device's default sampling rate and a string stating the quality.
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

def hide_menu():
  hide_streamlit_style = """
  <style>
  #MainMenu {visibility: hidden;}
  footer {visibility: hidden;}
  </style>

  """
  st.markdown(hide_streamlit_style, unsafe_allow_html=True) 

def main():

  #hide_menu()

  st.title('Covid-19 Risk Evaluation')
  st.write('This app evaluates your risk for Covid-19 based on coughs recorded from your device.')

  default_samplerate, sample_string = assess_device_samplerate()
  st.info(f'A reasonable recording quality is important to get the most accurate results.\n\n{sample_string}')
 
  st.subheader('Record a 5 second cough sample:')
  st.write('Please make sure there is no background noise.')

  if st.button('Start Recording'):
    with st.spinner("Recording..."):
      recording = record_and_save(default_samplerate)
      st.info('Cough saved.')
      review_recording()


if __name__ == '__main__':
  main()