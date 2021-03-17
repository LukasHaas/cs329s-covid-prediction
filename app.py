# Covid Detection MVP App - Streamlit
# -----------------------------------
# L. Haas, D. Soylu, J. Spencer
#

import streamlit as st

import src.Pages.NewUserPage as NewUserPage
import src.Pages.ReturningUserPage as ReturningUserPage
import src.SessionState as SessionState
from PIL import Image

COVID_IMAGE_URL = './assets/covid.png'
ROC_IMAGE_URL = './assets/ROC-curve.png'
CONFUSION_IMAGE_URL = './assets/multi_class_confusion_matrix.png'

def setup_page():
  """
  Applies site-wide settings.
  """
  st.set_page_config(page_title='Covid Risk Evaluation', page_icon=COVID_IMAGE_URL, layout='centered')

def model_information():
  """
  Shows model results in detail.
  """
  with st.beta_expander("Disclaimer & Algorithm Details"):
    st.write("""
    This site is used for testing purposes and any Covid-19 risk evaluations
    can be inaccurate as of this moment. We do not take any responsibility
    for the predictions made by this application.
    """)

    st.markdown("""
    Our model uses three categories of features to provide a prediction to our user on whether their cough sample may be 
    associated with Covid-19 including: embedding-based features, audio features, and demographic/symptom information.\

    * *Embedding-Based Features*:
      * When a user submits a cough, our model performs VGGish embeddings on the audio data in the cloud.
       Through our research, we recognized different patterns in a healthy person's audio embeddings vs a Covid-positive 
       individual's audio embedding. Therefore, we use the provided audio sample embeddings as a feature to help our model 
       gauge the risk factor that the user has Covid-19.\

    * *Audio Features:*
      * When a user submits a cough, our model calculates various measurements that help capture what the medical community 
      has identified as a 'dry cough' associated with Covid infection. Specifically we look at the max signal (loudest point), 
      median signal (average loudness), and spectral bandwidth (the duration of the cough in comparision to its peak). We 
      use these metrics as features in our model.\

    * *Demographic/Symptom Information:*
      * Lastly, our app uses clinically relevant background information provided by the user to help contribute to its 
      prediction. These features are the patient's age, respiratory condition and fever/muscle pain status.\
    """
                  )
    st.write("""\n
            It is important to recognize the limitations of our model, in its current iteration we are achieving the following
            accuracy results:
            """)

    image = Image.open(ROC_IMAGE_URL)
    st.image(image=image, width=400)

    st.write("""\n
          Currently our model is trained on an 2X augmented training set of 5,031 examples (1,677 examples)
          per class and evaluated on a 2X augmented test set of 420 examples. Displayed below is the confusion
          matrix of our model on real world test examples.
      """)

    image = Image.open(CONFUSION_IMAGE_URL)
    st.image(image=image, width=400)

def information_section(session_state):
  """
  Render an information section
  """
  st.subheader('Information')
  st.write('We encourage you to read through the following information sections:')

  model_information()

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
