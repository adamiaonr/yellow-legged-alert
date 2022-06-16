import json
import time
import wget
import requests

from pathlib import Path
from urllib.parse import quote
from dataclasses import dataclass
from collections import defaultdict
from typing import Union, Tuple

XENO_CANTO_NAME = "xeno-canto"
XENO_CANTO_API_ENDPOINT = "https://www.xeno-canto.org/api/2"

@dataclass
class Recording:
  id: str
  genus: str
  species: str
  subspecies: str
  url: str
  audio_type: str
  filename: str = ''

  def _generate_filename(self) -> str:
    return "{genus}_{species}_{subspecies}_{id}.{ext}".format(
        genus       = self.genus,
        species     = self.species, 
        subspecies  = self.subspecies,
        id          = self.id,
        ext         = self.audio_type
      ).lower()

  @classmethod
  def from_dict(cls, data:dict) -> "Recording":
    try:
      rec = Recording(
        id =          data['id'],
        genus =       data['gen'].lower(),
        species =     data['sp'].lower(),
        subspecies =  data['ssp'].lower(),
        url  =        data['file'],
        audio_type =  Path(data['file-name']).suffix.strip('.').lower()
      )
    except KeyError:
      raise KeyError("error while generating filename for recording")
    else:
      rec.filename = rec._generate_filename()

    return rec

def _to_recordings(raw_recordings:list) -> list[Recording]:
  recordings = []
  for rr in raw_recordings:
    try:
      recordings.append(Recording.from_dict(rr))
    except KeyError:
      pass

  return recordings

def _requests_adapter(url:str) -> dict:
  return requests.get(url, verify = True).json()

def get_recordings_list(genus:str, subspecies:str, api_adapter = _requests_adapter) -> list[Recording]:
  # sanitize query (contains spaces)
  query = quote(f'query=ssp:"{subspecies}" gen:"{genus}"', safe = '=:')
  url = f"{XENO_CANTO_API_ENDPOINT}/recordings?{query}"

  response = api_adapter(url)
  
  try:
    raw_recordings = response['recordings']
  except KeyError:
    raw_recordings = []

  return _to_recordings(raw_recordings)

def _wget_adapter(url:str, output_path:Path) -> Path:
  return Path(wget.download(url, str(output_path)))

def download_recordings(recordings:list[Recording], output_dir:Union[str, Path], 
  limit:int = 0, wait:int = 1, force:bool = False, download_adapter = _wget_adapter) -> Tuple[defaultdict[Path], int]:

  if wait < 1:
    raise ValueError(f"wait < 1 seconds not allowed : would overload {XENO_CANTO_NAME} API")

  file_paths = defaultdict(Path)
  nr_files_downloaded = 0
  for rec in recordings[:(limit if limit > 0 else len(recordings))]:
    file_path = Path(output_dir) / rec.filename
    # do not download & wait if file already exists
    if not file_path.is_file() or force:
      file_path = download_adapter(rec.url, file_path)
      nr_files_downloaded += 1

      # sleep to avoid xeno-canto API overload
      time.sleep(wait)

    file_paths[rec.id] = file_path

  return file_paths, nr_files_downloaded
