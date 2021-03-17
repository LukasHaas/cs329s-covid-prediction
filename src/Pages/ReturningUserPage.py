import time
import streamlit as st
from src.MockData.KeyPhrases import KEY_PHRASES

def app(session_state):
  st.subheader('Upload Your PCR Result')
  st.write("""
  Thank you for coming back. Please enter the unique phrase you have chosen
  when you provided your cough samples.
  """)

  phrase = st.text_input('Type your phrase', key='returningUserPhrase')
  test_date = st.date_input("Enter the date of the PCR Test")
  st.selectbox('What was your PCR test result?', ['Negative', 'Positive'])
  upload_button = st.button('Upload PCR Test Result')
  if upload_button:
    if phrase.strip() not in KEY_PHRASES:
        st.error("""
        We couldn't find a cough sample linked to the provided phrase. Are you
        sure you typed your phrase correctly?
        """)
    else:
      with st.spinner('Uploading the PCR test results ...'):
        try:
          time.sleep(2) # TODO replace with actual upload
          st.success('Successfully uploaded the PCR result!')
        except:
          st.error('An error occured while uploading the PCR result. Please try again.')
          print(e)
