import librosa as lr
import soundfile as sf
import noisereduce as nr

from pathlib import Path

def _get_file_path(input_file_path:Path, suffix:str, output_dir:Path = None, format = 'WAV') -> Path:
    # file name format : add '{suffix}' to the 'name' of input_filepath
    file_name = f"{input_file_path.stem}_{suffix}.{format}".lower()

    # if no output dir is specified, save file in same directory
    if output_dir:
      output_file_path = output_dir / file_name
    else:
      output_file_path = input_file_path.with_stem(file_name)

    return output_file_path

def split_into_non_silent(input_file_path:Path, output_dir:Path = None, 
  threshold:list = [.5, 1.], format = 'WAV', force = False):
  # load audio file and split into non-silent intervals
  waveform, sample_rate = lr.load(path = input_file_path)
  intervals = lr.effects.split(y = waveform)

  for i, intr in enumerate(intervals):
    # skip intervals w/ duration outside of threshold[] limits
    duration = lr.get_duration(y = waveform[intr[0]:intr[1]], sr = sample_rate)
    if duration < threshold[0] or duration > threshold[1]:
      continue

    output_file_path = _get_file_path(input_file_path, f'{i}', output_dir, format)
    if (not output_file_path.is_file()) or force:
      sf.write(output_file_path, waveform[intr[0]:intr[1]], sample_rate, format = format)

def reduce_background_noise(input_file_path:Path, output_dir:Path = None, format = 'WAV', force = False):
  # output file name format : add '_noisered' suffix to input_filename
  output_file_path = _get_file_path(input_file_path, 'noisered', output_dir, format)
  
  # skip noise removal if file already exists or if force = False
  if (not output_file_path.is_file()) or force:
    # apply non-stationary noise reduction to audio file (https://pypi.org/project/noisereduce/)
    waveform, sample_rate = lr.load(input_file_path)
    waveform_reduced = nr.reduce_noise(y = waveform, sr = sample_rate)
    sf.write(output_file_path, waveform_reduced, sample_rate, format = format)
