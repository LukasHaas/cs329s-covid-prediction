# Covid Detection MVP App - Streamlit
# -----------------------------------
# L. Haas, D. Soylu, J. Spencer
#

import streamlit as st

import src.Pages.NewUserPage as NewUserPage
import src.Pages.ReturningUserPage as ReturningUserPage
import src.SessionState as SessionState

COVID_IMAGE_URL = './assets/covid.png'

def setup_page():
  """
  Applies site-wide settings.
  """
  st.set_page_config(page_title='Covid Risk Evaluation', page_icon=COVID_IMAGE_URL, layout='centered')

def detailed_model_results():
  """
  Shows model results in detail.
  """
  with st.beta_expander("Disclaimer & Personalized Algorithm Details"):
    st.write("""
    This site is used for testing purposes and any Covid-19 risk evaluations
    are inaccruate as of this moment. We do not take any responsibility
    for the predictions made by this application.
    """)

def information_section(session_state):
  """
  Render an information section
  """
  st.subheader('Information')
  st.write('We encourage you to read through the following information sections:')

  if session_state.successful_prediction:
    detailed_model_results()
  else:
    with st.beta_expander("Disclaimer & Algorithm Details"):
      st.write("""
      This site is used for testing purposes and any Covid-19 risk evaluations
      are inaccruate as of this moment. We do not take any responsibility
      for the predictions made by this application.
      """)

  with st.beta_expander("Data Privacy Policy"):
    st.write("""
    Your cough recording will exclusively be used in order to serve you
    a Covid-19 risk evaluation. Under no circumstances will we share
    your data with any third parties. In addition, your Covid-19 risk
    evaluation will be generated entirely anonymously.
    """)

if __name__ == '__main__':
  setup_page()
  session_state = SessionState.get(recording_hash=None,
                                   cough_donated=False,
                                   symptoms_donated=False,
                                   successful_prediction=False,
                                   cough_uuid=None)


  st.image(COVID_IMAGE_URL, width=50)
  st.title('Covid-19 Risk Evaluation')

  st.write(
  """This app evaluates the risk for Covid-19 based on coughs recorded from
  a device. It is meant to be used both by regular users and medical
  practioners. Note that the results shown here are experimental and should
  not be used for any kind of medical decisions.""")

  PAGES = {
    "New": NewUserPage,
    "Returning": ReturningUserPage
  }

  new_user_prompt = 'new user and I would like to get a COVID-19 risk evaluation'
  returning_user_prompt = 'returning user and I would like to submit the result of my PCR test'

  returning_option = st.selectbox('I am a',
    ('', new_user_prompt, returning_user_prompt)
  )

  if returning_option == new_user_prompt:
    NewUserPage.app(session_state)
  elif returning_option == returning_user_prompt:
    ReturningUserPage.app(session_state)

  information_section(session_state)
