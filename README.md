[![.github/workflows/google.yml](https://github.com/LukasHaas/cs329s-covid-prediction/actions/workflows/google.yml/badge.svg)](https://github.com/LukasHaas/cs329s-covid-prediction/actions/workflows/google.yml)

# <img src="./assets/covid.png" alt="Covid-19 Evaluation App - QR Code" height="30px" width="30px" /> Covid-19 Prediction App
This app is a Streamlit front end predicting the risk of Covid-19 based on recorded cough sounds.

## Demo
Scan the QR code below or click the link to see the app in action:

<img src="QRCode.jpg"
     alt="Covid-19 Evaluation App - QR Code"
     width="180px"/>
     
[Covid-19 Risk Evaluation App](https://cs329s-covid-caugh-prediction.appspot.com/)

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
make gcloud-deploy-flex
```
This will create a new app version in a "flexible" GCP App Engine environment.

## System Architecture
### MVP
The below diagram illustrates how our system on looked like on Google Cloud Platform when we submitted it for MVP evaluation:

<img src="MVPSystemDiagram.png"
     alt="Covid-19 Evaluation App - MVP System Diagram"
     style="margin: 10px" />
     
### V1: CS329 Demo 
Since our MVP, we added a lot of features. The below diagram illustrates our current system architecture on Google Cloud Platform:

<img src="DemoSystemDiagram.png"
     alt="Covid-19 Evaluation App - V1 System Diagram"
     style="margin: 10px" />
