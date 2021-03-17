import sounddevice as sd
import googleapiclient.discovery
from google.api_core.client_options import ClientOptions
from google.cloud import storage
import numpy as np


def segment_cough(x, fs, cough_padding=0.2, min_cough_len=0.2, th_l_multiplier=0.1, th_h_multiplier=2):
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

    print("File uploaded to {}.".format(destination_blob_name))


def assess_device_samplerate():
    """
  Returns the device's default sampling rate and a string stating the sampling quality.

  Returns:
    default_samplerate (int): device's default samplerate
    sample_string (str): string indicating microphone quality
  """
    default_samplerate = None  # default
    try:
        default_samplerate = int(sd.query_devices()[sd.default.device[0]]['default_samplerate'])
    except (IndexError):
        default_samplerate = 44100

    sample_string = 'Your device\'s microphone quality: '

    if default_samplerate <= 16000:
        sample_string += ':pensive:'
    elif default_samplerate <= 22100:
        sample_string += ':neutral_face:'
    else:
        sample_string += ':grinning:'

    return default_samplerate, sample_string
