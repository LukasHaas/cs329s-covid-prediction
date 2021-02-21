# Covid-19 Prediction App
This app is a streamlit front end predicting the risk of Covid-19 based on recorded cough sounds.

## Project Setup
It is recommended to first install all required dependencies using a virtual environment.

Go to the project directory to which you have downloaded all of this repo's files and run:
```shell
cd my-project/
pip install virtualenv
virtualenv venv
```

Now activate the newly created virtual environment:
```shell
source venv/bin/activate
```

Next, you need to install all of the project's dependencies:
```shell
pip install -r requirements.txt
```

## Running the Application
Run the following command from your project directory to start the Streamlit app:
```shell
streamlit run app.py
```
This will run the application on your local machine.

Cough sounds will not be saved to any device but are processed using GCP APIs.

## Deployment
In order to deploy the application to Google Cloud's App Engine, run the following command from the root directory of the project:
```shell
make gcloud-deploy
```
