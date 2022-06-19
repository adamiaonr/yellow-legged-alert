import os
import unittest
import warnings
import librosa as lr
import numpy as np

from pathlib import Path
from src.sound import split_audio_on_silence, split_audio_on_time

class TestSound(unittest.TestCase):

  @classmethod
  def setUpClass(cls) -> None:
    # ignore warnings
    warnings.filterwarnings('ignore')

    cls.data_root = Path(f"{os.path.dirname(__file__)}/data/sound")    
    # build waveform to be used in tests (9 seconds, 22.05 kHz), with this format ('-' : silence, '1' : sound):
    # -1--11---
    cls.sample_rate = 22050
    s1 = np.concatenate([np.zeros(cls.sample_rate * 1), lr.chirp(fmin = 440, fmax = 110 * 64, sr = cls.sample_rate, duration = 1)])
    s2 = np.concatenate([s1, np.zeros(cls.sample_rate * 2)])
    s3 = np.concatenate([s2, lr.chirp(fmin = 440, fmax = 110 * 64, sr = cls.sample_rate, duration = 2)])
    cls.waveform = np.concatenate([s3, np.zeros(cls.sample_rate * 3)])

  def test_split_audio_on_silence_no_limit(self):
    waveforms, sample_rate = split_audio_on_silence(self.waveform, sample_rate = self.sample_rate, 
      remove_noise = False)
    self.assertEqual(len(waveforms), 2)
    self.assertEqual(sample_rate, self.sample_rate)
    self.assertAlmostEqual(lr.get_duration(y = waveforms[0], sr = sample_rate), 1, delta = .15)
    self.assertAlmostEqual(lr.get_duration(y = waveforms[1], sr = sample_rate), 2, delta = .15)
  
  def test_split_audio_on_silence_with_limits(self):
    waveforms, sample_rate = split_audio_on_silence(self.waveform, sample_rate = self.sample_rate, 
      limits = [.5, 1.5], remove_noise = False)
    self.assertEqual(len(waveforms), 1)
    self.assertEqual(sample_rate, self.sample_rate)
    self.assertAlmostEqual(lr.get_duration(y = waveforms[0], sr = sample_rate), 1, delta = .15)

  def test_split_audio_on_silence_noise_reduce(self):
    waveforms, sample_rate = split_audio_on_silence(self.waveform, sample_rate = self.sample_rate, 
      remove_noise = True)
    
    self.assertEqual(len(waveforms), 2)
    self.assertEqual(sample_rate, self.sample_rate)
    self.assertAlmostEqual(lr.get_duration(y = waveforms[0], sr = sample_rate), 1, delta = .15)
    self.assertAlmostEqual(lr.get_duration(y = waveforms[1], sr = sample_rate), 2, delta = .15)

  def test_split_audio_on_time_no_trim(self):
    # test 1 : duration = 1 sec
    waveforms, sample_rate = split_audio_on_time(self.waveform, sample_rate = self.sample_rate, 
      duration = 1)
    self.assertEqual(len(waveforms), 9)
    self.assertEqual(sample_rate, self.sample_rate)
    self.assertTrue(all(len(waveform) == self.sample_rate for waveform in waveforms))

    # test 2 : duration = 2 sec (last interval duration = 1 sec)
    waveforms, sample_rate = split_audio_on_time(self.waveform, sample_rate = self.sample_rate, 
      duration = 2)
    self.assertEqual(len(waveforms), 5)
    self.assertEqual(sample_rate, self.sample_rate)
    self.assertTrue(all(len(waveform) == (self.sample_rate * 2) for waveform in waveforms[:-1]))
    self.assertEqual(len(waveforms[-1]), self.sample_rate * 1)
  
  def test_split_audio_on_time_with_trim(self):
    waveforms, sample_rate = split_audio_on_time(self.waveform, sample_rate = self.sample_rate, 
      duration = 1, trim = True)

    self.assertIn(len(waveforms), [5, 6]) # TODO: must allow at most 1 extra trailing interval (strange lr.trim() behaviour)
    self.assertEqual(sample_rate, self.sample_rate)
    self.assertTrue(all(len(waveform) == self.sample_rate for waveform in waveforms[:5]))
