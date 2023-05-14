from pathlib import Path

import librosa as lr
import noisereduce as nr
import numpy as np
import soundfile as sf


def open_waveform(file_path: Path) -> tuple[np.ndarray, int]:
    waveform, sample_rate = lr.load(path=file_path, sr=None)
    return waveform, sample_rate


def save_waveform(
    waveform: np.ndarray,
    sample_rate: int,
    file_path: Path,
    audio_format: str = "WAV",
    force: bool = False,
):
    if (not file_path.is_file()) or force:
        sf.write(file_path, waveform, sample_rate, format=audio_format)


def reduce_noise(waveform: np.ndarray, sample_rate: int) -> tuple[np.ndarray, int]:
    # apply non-stationary noise reduction to audio file (https://pypi.org/project/noisereduce/)
    return nr.reduce_noise(y=waveform, sr=sample_rate), sample_rate


def split_audio_on_silence(
    waveform: np.ndarray, sample_rate: int, limits: list, remove_noise: bool = True
) -> tuple[list[np.ndarray], int]:
    # (optional) reduce background noise of audio clip beforhand to make splitting easier
    intervals = lr.effects.split(
        y=reduce_noise(waveform, sample_rate)[0] if remove_noise else waveform
    )
    waveforms = [
        waveform[i[0] : i[1]]
        for i in intervals
        if not limits or (limits[0] <= ((i[1] - i[0]) / sample_rate) <= limits[1])
    ]

    return waveforms, sample_rate


def split_audio_on_time(
    waveform: np.ndarray, sample_rate: int, duration: int = 1, trim: bool = False
) -> tuple[list[np.ndarray], int]:
    # (optional) trim silence segments from start and end of waveform
    if trim:
        waveform, _ = lr.effects.trim(waveform, frame_length=256, hop_length=64)
    segment_size = int(duration * sample_rate)
    waveforms = [
        waveform[i : (i + segment_size)] for i in range(0, len(waveform), segment_size)
    ]

    return waveforms, sample_rate
