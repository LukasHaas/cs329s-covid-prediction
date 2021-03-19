import logging
import librosa
import sounddevice as sd
import googleapiclient.discovery
from google.api_core.client_options import ClientOptions
from google.cloud import storage
import numpy as np

def segment_cough(x, fs, cough_padding=0.2, min_cough_len=0.1, th_l_multiplier=0.1, th_h_multiplier=0.5):
    """Preprocess the data by segmenting each file into individual coughs using a hysteresis comparator on the signal power

    Inputs:
    *x (np.array): cough signal
    *fs (float): sampling frequency in Hz
    *cough_padding (float): number of seconds added to the beginning and end of each detected cough to make sure coughs are not cut short
    *min_cough_length (float): length of the minimum possible segment that can be considered a cough
    *th_l_multiplier (float): multiplier of the RMS energy used as a lower threshold of the hysteresis comparator
    *th_h_multiplier (float): multiplier of the RMS energy used as a high threshold of the hysteresis comparator

    Outputs:
    *coughSegments (np.array of np.arrays): a list of cough signal arrays corresponding to each cough
    cough_mask (np.array): an array of booleans that are True at the indices where a cough is in progress"""

    cough_mask = np.array([False] * len(x))

    # Define hysteresis thresholds
    rms = np.sqrt(np.mean(np.square(x)))
    seg_th_l = th_l_multiplier * rms
    seg_th_h = th_h_multiplier * rms

    # Segment coughs
    coughSegments = []
    padding = round(fs * cough_padding)
    min_cough_samples = round(fs * min_cough_len)
    cough_start = 0
    cough_end = 0
    cough_in_progress = False
    tolerance = round(0.01 * fs)
    below_th_counter = 0

    for i, sample in enumerate(x ** 2):
        if cough_in_progress:
            if sample < seg_th_l:
                below_th_counter += 1
                if below_th_counter > tolerance:
                    cough_end = i + padding if (i + padding < len(x)) else len(x) - 1
                    cough_in_progress = False
                    if (cough_end + 1 - cough_start - 2 * padding > min_cough_samples):
                        coughSegments.append(x[cough_start:cough_end + 1])
                        cough_mask[cough_start:cough_end + 1] = True
            elif i == (len(x) - 1):
                cough_end = i
                cough_in_progress = False
                if (cough_end + 1 - cough_start - 2 * padding > min_cough_samples):
                    coughSegments.append(x[cough_start:cough_end + 1])
            else:
                below_th_counter = 0
        else:
            if sample > seg_th_h:
                cough_start = i - padding if (i - padding >= 0) else 0
                cough_in_progress = True

    return coughSegments, cough_mask

def normalize_audio(signal, fs, shouldTrim=True):
    """Normalizes and trims the audio.

    Args:
        signal (np.array): audio as a 1-D numpy array
        fs (int): sample rate

    Returns:
        (np.array): normalized and trimmed audio
    """
    frame_len = int(fs / 10)  # 100 ms
    hop = int(frame_len / 2)  # 50% overlap, meaning 5ms hop length

    # normalise the sound signal before processing
    signal = signal / np.max(np.abs(signal))

    # trim the signal to the appropriate length
    if shouldTrim:
        signal, _ = librosa.effects.trim(signal, frame_length=frame_len, hop_length=hop)

    return signal

def upload_blob(bucket_name, source_object, destination_blob_name):
    """
    Uploads a file object to the bucket.
    
    Example Usage:
    >>> Utils.upload_blob('cs329s-covid-user-coughs', recording, 'temp_data/user_cough.wav')
    
    Args:
      bucket_name (str): GCP storage bucket
      source_object (any): object to be saved to GCP Storage
      destination_blob_name (str): path and filename to save object to
    """
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_string(source_object)
    logging.info('File uploaded.', destination_blob_name)
