import streamlit as st

def app(session_state):
    st.subheader('Upload Your PCR Result')
    st.write("""
    Thank you for coming back. Please enter the unique identifier provided
    to you when you provided your cough samples.
    """)
    identifier = st.text_input('Type your identifier and hit Enter:')

    # TODO check if valid identifier
    if identifier:
        test_date = st.date_input("Enter the date of the PCR Test")
        st.selectbox('What was your PCR test result?', ['Negative', 'Positive'])
        upload_button = st.button('Upload PCR Test Result')
        if upload_button:
            try:
              # TODO Upload action
              st.success('Successfully uploaded PCR result!')
            except:
              st.error('An error occured while uploading the PCR result. Please try again.')
