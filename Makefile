.PHONY: run run-container gcloud-deploy-flex

APP_NAME ?= covid-risk-evaluation

run:
	@streamlit run app.py --server.port=8080 --server.address=0.0.0.0 --client.showErrorDetails=false

run-container:
	@docker build . -t ${APP_NAME}
	@docker run -p 8080:8080 ${APP_NAME}

gcloud-deploy-flex:
	@gcloud app deploy app_flex.yaml

gcloud-deploy-standard:
	@gcloud app deploy app_standard.yaml