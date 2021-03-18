# CODE ADAPTED FROM: https://c4science.ch/diffusion/10770/

import numpy as np
import librosa
import logging
import xgboost
from scipy import signal
from scipy.io import wavfile
from scipy.signal import butter,filtfilt
from scipy.signal import cwt
from scipy.signal import hilbert
from scipy.signal import resample
from scipy.signal import decimate
from scipy.signal import spectrogram
from scipy.signal.windows import get_window

import os
import pickle
from .feature_class import features 

class CoughDetector:
    def __init__(self):
        self.model = pickle.load(open(os.path.join('models', 'cough_classifier'), 'rb'))
        self.scaler = pickle.load(open(os.path.join('models','cough_classification_scaler'), 'rb'))

    def classify_cough(self, features):
        """Classify whether an inputted signal is a cough or not using filtering, feature extraction, and ML classification
        Inputs: 
            features: (np.array) extracted features
        Outputs:
            result: (float) probability that a given file is a cough 
        """
        feature_values_scaled = self.scaler.transform(features)
        result = self.model.predict_proba(feature_values_scaled)[:,1]
        return result

    def extract_features(self, x, fs):
        """Feature extraction for determining if a sound is a cough or not
        Inputs: 
            x: (float array) raw cough signal
            fs: (int) sampling rate of raw signal
        Outputs:
            result: (np.array) extracted features
        """
        try: 
            x,fs = self.__preprocess_cough(x,fs)
            data = (fs,x)
            FREQ_CUTS = [(0,200),(300,425),(500,650),(950,1150),(1400,1800),(2300,2400),(2850,2950),(3800,3900)]
            features_fct_list = ['EEPD','ZCR','RMSP','DF','spectral_features','SF_SSTD','SSL_SD','MFCC','CF','LGTH','PSD']
            feature_values_vec = []
            obj = features(FREQ_CUTS)
            for feature in features_fct_list:
                feature_values, feature_names = getattr(obj,feature)(data)
                for value  in feature_values:
                    if isinstance(value,np.ndarray):
                        feature_values_vec.append(value[0])
                    else:
                        feature_values_vec.append(value)
            return np.array(feature_values_vec).reshape(1,-1)

        except:
            logging.error('Error extracting cough detection audio features.')
            return 0

    def __preprocess_cough(self, x, fs, cutoff = 6000, normalize = True, filter_ = True, downsample = True):
        """
        Normalize, lowpass filter, and downsample cough samples in a given data folder 
        
        Inputs: x*: (float array) time series cough signal
        fs*: (int) sampling frequency of the cough signal in Hz
        cutoff: (int) cutoff frequency of lowpass filter
        normalize: (bool) normailzation on or off
        filter: (bool) filtering on or off
        downsample: (bool) downsampling on or off
        *: mandatory input
        
        Outputs: x: (float32 array) new preprocessed cough signal
        fs: (int) new sampling frequency
        """
        
        fs_downsample = cutoff*2
        
        #Preprocess Data
        if len(x.shape)>1:
            x = np.mean(x,axis=1)                          # Convert to mono
        if normalize:
            x = x/(np.max(np.abs(x))+1e-17)                # Norm to range between -1 to 1
        if filter_:
            b, a = butter(4, fs_downsample/fs, btype='lowpass') # 4th order butter lowpass filter
            x = filtfilt(b, a, x)
        if downsample:
            x = signal.decimate(x, int(fs/fs_downsample)) # Downsample for anti-aliasing
        
        fs_new = fs_downsample
        return np.float32(x), fs_new