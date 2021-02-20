FROM python:3.6.9

## App engine
# Expose port you want your app on
EXPOSE 8080

# Upgrade pip 
RUN pip install -U pip
RUN apt-get update && apt-get install -y \
    libportaudio2

COPY requirements.txt app/requirements.txt
RUN pip install -r app/requirements.txt

# Create a new directory for app (keep it in its own directory)
COPY . /app
WORKDIR app

# Run
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]