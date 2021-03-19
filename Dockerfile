FROM python:3.7.7

## App engine
# Expose port you want your app on
EXPOSE 8080

# Download audio libraries to record sound
RUN apt-get update && apt-get install -y --no-install-recommends apt-utils \
    libportaudio2 \
    libsndfile1

# Add a user
RUN useradd -ms /bin/bash build

# Switch to build user
USER build
ENV HOME /home/build
WORKDIR /home/build/

# Download conda
# http://repo.continuum.io/miniconda/Miniconda-latest-Linux-x86_64.sh
RUN ["/bin/bash", "-c", "wget http://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh -O $HOME/miniconda.sh"]
RUN chmod 0755 $HOME/miniconda.sh
RUN ["/bin/bash", "-c", "$HOME/miniconda.sh -b -p $HOME/conda"]
ENV PATH="$HOME/conda/bin:$PATH"
RUN rm $HOME/miniconda.sh

# update conda
RUN conda update conda
RUN conda install -c conda-forge python-sounddevice
RUN conda uninstall --force portaudio

# Upgrade and install pip dependencies
RUN pip install -U pip
COPY requirements.txt app/requirements.txt
RUN pip install -r app/requirements.txt

# Create a new directory for app (keep it in its own directory)
COPY . $HOME/app
WORKDIR $HOME/app

# Run
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0", "--client.showErrorDetails=false", "--server.enableCORS=false"]