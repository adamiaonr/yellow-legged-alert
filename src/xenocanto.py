import time
import wget
import typing
import requests

from pathlib import Path
from urllib.parse import quote

XENO_CANTO_NAME = "xeno-canto"
XENO_CANTO_API_ENDPOINT = "https://www.xeno-canto.org/api/2"

def get_recordings_list(genus:str, subspecies:str) -> dict:
  # sanitize query (contains spaces)
  query = quote(f'query=ssp:"{subspecies}" gen:"{genus}"', safe = '=:')
  url = f"{XENO_CANTO_API_ENDPOINT}/recordings?{query}"
  
  response = requests.get(url, verify = True)
  
  try:
    recordings_list = response.json()['recordings']
  except (requests.exceptions.JSONDecodeError, KeyError):
    recordings_list = []

  return recordings_list

def get_recording_filename(recording:dict) -> str:
    try:
      # audio files saved w/ format {genus}_{species}_{subspecies}_{id}.{ext}
      # in this case, {ext} shall be an audio format (e.g., 'mp3', 'wav')
      file_name = "{genus}_{species}_{subspecies}_{id}{ext}".format(
        genus       = recording['gen'],
        species     = recording['sp'], 
        subspecies  = recording['ssp'],
        id          = recording['id'],
        ext         = Path(recording['file-name']).suffix
      )
    except KeyError:
      raise KeyError("error while generating filename for recording")
    
    return file_name.lower()

def download_recordings(recordings_list:list, output_dir:typing.Union[str, Path], 
  max_records:int = 0, wait:int = 1):

  if wait < 1:
    raise ValueError(f"wait < 1 seconds not allowed : would overload {XENO_CANTO_NAME} API")

  max_records = max_records if max_records > 0 else len(recordings_list)
  for i, rec in enumerate(recordings_list[:max_records]):
    try:
      # url to download the audio file
      url = rec['file']
      # audio should be saved with format {genus}_{species}_{subspecies}_{id}.{ext}
      file_name = get_recording_filename(rec)
    except KeyError:
      pass
    else:
      # do not download if file already exists
      file_path = Path(output_dir) / file_name
      if not file_path.is_file():
        wget.download(url, str(file_path))
        # sleep to avoid xeno-canto API overload
        time.sleep(wait)
