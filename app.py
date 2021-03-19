# Covid Detection MVP App - Streamlit
# -----------------------------------
# L. Haas, D. Soylu, J. Spencer
#

import logging
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
  with st.beta_expander('Algorithm Details & Accuracy'):

    st.subheader('How Does Our Algorithm Work?')
    st.markdown("""
    Our algorithm is a [Gradient Boosting Tree Classifier](https://en.wikipedia.org/wiki/Gradient_boosting) which leverages
    cough audio recordings and user-provided clinical features to predict one out of three classes: *healthy*, *symptomatic*, 
    and *Covid-19*:

    * **Healthy**:  \n
      The person most likely does not have Covid-19.
    * **Symptomatic**:  \n
      The person likely does not have Covid-19, however the provided audio and clinical information correlates with real world 
      examples of symptomatic users who did not test positive in a PCR test setting.
    * **Covid-19**:  \n
      The person most likely has Covid-19.
    """)

    st.subheader('How Are Covid-19 Risk Evaluations Generated?')
    st.markdown("""
    Our model uses three categories of features to provide a prediction to our user on whether their cough sample may be 
    associated with Covid-19, including: embedding-based features, audio features, and demographic/symptom information.  \n
    * **Embedding-Based Features**:  \n
      When a user submits a cough, our model performs [VGGish embeddings](https://research.google/pubs/pub45611/) on the 
      audio data in the cloud. Through our research, we recognized different patterns in a healthy person's audio embeddings 
      vs a Covid-positive individual's audio embedding. Therefore, we use the provided audio sample embeddings as a feature 
      to help our model gauge the risk factor that the user has Covid-19.  \n

    * **Audio Features**:  \n
      When a user submits a cough, our model calculates various measurements that help capture what the medical community 
      has identified as a 'dry cough' associated with Covid infection. Specifically we look at the max signal (loudest point), 
      median signal (median loudness), spectral bandwidth (the standard deviation of the cough audio frequencies over time), and
      many more. We use these metrics as features in our model.  \n

    * **Demographic/Symptom Information**:  \n
      Lastly, our app uses clinically relevant background information provided by the user to help contribute to its 
      prediction. These features are the patient's age, her history of respiratory conditions and current fever/muscle pain 
      status.  \n
    """
    )

    st.subheader('How Accurate Is Our Covid-19 Risk Evaluation?')
    st.write("""
    It is important to recognize the limitations of our model, in its current iteration we are achieving a 
    [ROC-AUC Score](https://en.wikipedia.org/wiki/Receiver_operating_characteristic) of 71%, with the following accuracy
    breakdown:
    """)

    image = Image.open(ROC_IMAGE_URL)
    st.image(image=image, use_column_width='auto')

    st.write("""\n
    Currently our model is trained on an 2x augmented training set of 5,031 examples (1,677 per class)
    and evaluated on a balanced non-augmented test set of 420 examples (140 per class).  \n
    Displayed below is the confusion matrix our model achieved on the validation dataset.
    """)

    image = Image.open(CONFUSION_IMAGE_URL)
    st.image(image=image, use_column_width='auto')

def disclaimer_section():
  """
  Render a disclaimer section
  """
  st.subheader('Disclaimer')
  st.warning("""
  This site is used for testing purposes and any Covid-19 risk evaluations
  can be inaccurate as of this moment. We do not take any responsibility
  for the predictions of this application.""")

def information_section(session_state):
  """
  Render an information section
  """
  st.subheader('Information')
  st.write('We encourage you to read through the following information sections:')

  model_information()

  with st.beta_expander("Data Privacy Policy"):
    st.write("""
    Your cough recordings will exclusively be used in order to serve you
    Covid-19 risk evaluations. Under no circumstances will we share
    your data with any third parties. In addition, your Covid-19 risk
    evaluation will be generated entirely anonymously.
    """)

if __name__ == '__main__':
  logger = logging.getLogger()
  logger.setLevel(logging.INFO) 

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

  new_user_prompt = '... new user (COVID-19 risk evaluation)'
  returning_user_prompt = '... returning user (submit PCR test)'

  returning_option = st.selectbox('I am a ...',
    ('', new_user_prompt, returning_user_prompt)
  )

  if returning_option == new_user_prompt:
    NewUserPage.app(session_state)
  elif returning_option == returning_user_prompt:
    ReturningUserPage.app(session_state)

  disclaimer_section()
  information_section(session_state)
