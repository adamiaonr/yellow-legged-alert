import numpy as np
import librosa as lr
import soundfile as sf
import noisereduce as nr

from pathlib import Path

def save_waveform(waveform:np.ndarray, sample_rate:int, file_path:Path, format:str = 'WAV', force:bool = False):
  if (not file_path.is_file()) or force:
    sf.write(file_path, waveform, sample_rate, format = format)

def get_reduced_background_noise(file_path:Path) -> tuple[np.ndarray, int]:
  waveform, sample_rate = lr.load(file_path, sr = None)
  # apply non-stationary noise reduction to audio file (https://pypi.org/project/noisereduce/)
  waveform_reduced = nr.reduce_noise(y = waveform, sr = sample_rate)

  return waveform_reduced, sample_rate

def get_clips(file_path:Path, time:int = 1, trim:bool = False) -> tuple[list[np.ndarray], int]:
  waveform, sample_rate = lr.load(path = file_path, sr = None)
  # if trim is True, trim silence from start and end of waveform
  if trim: 
    waveform, _ = lr.effects.trim(waveform)
  
  duration = lr.get_duration(y = waveform, sr = sample_rate)
  m = time * sample_rate
  waveforms = [waveform[i * m : ((i + 1) * m)] for i in range(int(duration / time) + 1)]

  return waveforms, sample_rate

def get_non_silent_clips(file_path:Path, duration_limits:list = [.5, 1.]) -> tuple[list[np.ndarray], int]:
  waveform, sample_rate = lr.load(path = file_path, sr = None)
  intervals = lr.effects.split(y = waveform)

  waveforms = []
  for interval in intervals:
    # skip intervals w/ duration outside of duration_limits[]
    duration = lr.get_duration(y = waveform[interval[0]:interval[1]], sr = sample_rate)
    if duration < duration_limits[0] or duration > duration_limits[1]:
      continue
    waveforms.append(waveform[interval[0]:interval[1]])

  return waveforms, sample_rate
