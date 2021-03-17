import sounddevice as sd
import googleapiclient.discovery
from google.api_core.client_options import ClientOptions
from google.cloud import storage

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
  default_samplerate = None # default
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