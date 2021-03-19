import os
import pickle
import logging
import librosa
import numpy as np
import pandas as pd
from math import pi
from scipy.fftpack import fft, hilbert
from sklearn.ensemble import GradientBoostingClassifier
from .gcp_inference import get_vggish_embedding

MEAN_VGGISH_EMBEDDING = 0.63299006
VGGISH_EMBEDDING_INDEX = 33

class CovidClassifier:
    def __init__(self):
        self.model = pickle.load(open(os.path.join('models', 'gbc_ovo_roc_70_5'), 'rb'))

    def classify_cough(self, audio, fs, clinical_features):
        """Classify whether an inputted signal is a cough or not using filtering, feature extraction, and ML classification
        Inputs: 
            features: (np.array) extracted features
        Outputs:
            result: (float) probability that a given file is a cough 
        """
        vggish_features = self.__extract_vggish_features(audio, fs)
        audio_features = self.__extract_audio_features(audio, fs)
        clinical_features = self.__extract_clinical_features(clinical_features)

        logging.debug('VGGish Features:', vggish_features)
        logging.debug('Audio Features:', audio_features)
        logging.debug('Clinical Features:', clinical_features)

        features = np.concatenate((vggish_features, audio_features, clinical_features))
        result = self.model.predict_proba(np.array([features]))
        return result

    def __extract_clinical_features(self, clinical_features):
        """Gets the clinical features and returns them as a numpy array.

        Args:
            clinical_features (dict): clinical features
        """
        print(clinical_features)
        try:
            return np.array([
                float(clinical_features['age']), 
                float(clinical_features['respiratory_condition']),
                float(clinical_features['fever_muscle_pain'])
            ])

        except:
            logging.error('Error extracting clinical features.')
            return np.zeros(3)

    def __extract_vggish_features(self, audio, fs):
        """Gets the VGGish embedding from GCP and returns the relevant features.

        Only works if a max of 4.2 seconds at 16kHz sample rate is submitted.

        Args:
            audio (np.array): audio
            fs (int): sample rate
        """
        try:
            resampled_audio = librosa.resample(audio, fs, 16000, res_type='kaiser_best')
            cut_audio = resampled_audio.tolist()[-int(4.2*16000):]
            embeddings = get_vggish_embedding(os.environ['GCP_PROJECT'], os.environ['GCP_MODEL'], cut_audio)[0]['output_0']
            return np.mean(embeddings, axis=0)[VGGISH_EMBEDDING_INDEX]
        except:
            logging.warning('Could not obtain VGGish embeddings. Check if AI Platform endpoint is enabled and credentials are set.')
            return np.array([MEAN_VGGISH_EMBEDDING])

    def __extract_audio_features(self, signal, fs):
        """Extract part of handcrafted features from the input signal.
        :param signal: the signal the extract features from
        :type signal: numpy.ndarray
        :param signal_sr: the sample rate of the signal
        :type signal_sr: integer
        :return: the populated feature vector
        :rtype: numpy.ndarray
        """
        try:
          frame_len = int(fs / 10)  # 100 ms
          hop = int(frame_len / 2)  # 50% overlap, meaning 5ms hop length

          # normalise the sound signal before processing
          signal = signal / np.max(np.abs(signal))

          # trim the signal to the appropriate length
          trimmed_signal, idc = librosa.effects.trim(signal, frame_length=frame_len, hop_length=hop)

          # extract the signal duration
          signal_duration = librosa.get_duration(y=trimmed_signal, sr=fs)

          # find the onset strength of the trimmed signal
          o_env = librosa.onset.onset_strength(trimmed_signal, sr=fs)

          # find the frames of the onset
          onset_frames = librosa.onset.onset_detect(onset_envelope=o_env, sr=fs)

          # keep only the first onset frame
          onsets = onset_frames.shape[0]

          # decompose the signal into its magnitude and the phase components such that signal = mag * phase
          mag, phase = librosa.magphase(librosa.stft(trimmed_signal, n_fft=frame_len, hop_length=hop))

          # extract the rms from the magnitude component
          rms = librosa.feature.rms(y=trimmed_signal)[0]
          s = pd.Series(rms)
          rms_skew = s.skew()

          # extract the spectral bandwith of the magnitude
          spec_bandwidth = librosa.feature.spectral_bandwidth(S=mag)[0]

          # pack the extracted features into the feature vector to be returned
          signal_features = np.concatenate(
              (
                  np.array([signal_duration, onsets]),
                  self.__get_period(signal, signal_sr=fs),
                  np.array([np.max(rms), np.median(rms), np.percentile(rms, 25), rms_skew]),
                      np.array([np.mean(spec_bandwidth)])
              ),
              axis=0,
          )
          return signal_features

        except:
            logging.error('Error extracting audio features.')
            return np.zeros(8)

    def __get_period(self, signal, signal_sr):
        """Extract the period from the the provided signal
        :param signal: the signal to extract the period from
        :type signal: numpy.ndarray
        :param signal_sr: the sampling rate of the input signal
        :type signal_sr: integer
        :return: a vector containing the signal period
        :rtype: numpy.ndarray
        """

        # perform a sanity check
        if signal is None:
            raise ValueError("Input signal cannot be None")

        # transform the signal to the hilbert space
        hy = hilbert(signal)

        ey = np.sqrt(signal ** 2 + hy ** 2)
        min_time = 1.0 / signal_sr
        tot_time = len(ey) * min_time
        pow_ft = np.abs(fft(ey))
        peak_freq = pow_ft[3: int(len(pow_ft) / 2)]
        peak_freq_pos = peak_freq.argmax()
        peak_freq_val = 2 * pi * (peak_freq_pos + 2) / tot_time
        period = 2 * pi / peak_freq_val

        return np.array([period])