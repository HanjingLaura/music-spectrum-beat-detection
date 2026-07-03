from __future__ import annotations

import math
import wave
from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass
class AudioData:
    signal: np.ndarray
    sample_rate: int


@dataclass
class AnalysisResult:
    sample_rate: int
    duration: float
    times: np.ndarray
    signal: np.ndarray
    spectrum_freqs: np.ndarray
    spectrum_magnitude: np.ndarray
    stft_times: np.ndarray
    stft_freqs: np.ndarray
    stft_magnitude: np.ndarray
    onset_times: np.ndarray
    onset_envelope: np.ndarray
    beat_times: np.ndarray
    bpm: float


def read_wav(path: str | Path) -> AudioData:
    """Read a PCM WAV file and return mono float samples in [-1, 1]."""
    path = Path(path)
    with wave.open(str(path), "rb") as reader:
        channels = reader.getnchannels()
        sample_rate = reader.getframerate()
        sample_width = reader.getsampwidth()
        frames = reader.getnframes()
        raw = reader.readframes(frames)

    if sample_width == 1:
        data = np.frombuffer(raw, dtype=np.uint8).astype(np.float32)
        data = (data - 128.0) / 128.0
    elif sample_width == 2:
        data = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    elif sample_width == 4:
        data = np.frombuffer(raw, dtype=np.int32).astype(np.float32) / 2147483648.0
    else:
        raise ValueError(f"Unsupported WAV sample width: {sample_width} bytes")

    if channels > 1:
        data = data.reshape(-1, channels).mean(axis=1)

    return AudioData(signal=data.astype(np.float32), sample_rate=sample_rate)


def write_wav(path: str | Path, signal: np.ndarray, sample_rate: int) -> None:
    """Write mono float samples in [-1, 1] to a 16-bit PCM WAV file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    clipped = np.clip(signal, -1.0, 1.0)
    pcm = (clipped * 32767.0).astype(np.int16)
    with wave.open(str(path), "wb") as writer:
        writer.setnchannels(1)
        writer.setsampwidth(2)
        writer.setframerate(sample_rate)
        writer.writeframes(pcm.tobytes())


def generate_demo_audio(path: str | Path, bpm: int = 120, duration: float = 18.0, sample_rate: int = 22050) -> AudioData:
    """Generate a small royalty-free demo track with clear beat accents."""
    t = np.linspace(0.0, duration, int(sample_rate * duration), endpoint=False)
    beat_interval = 60.0 / bpm

    melody = 0.18 * np.sin(2 * np.pi * 220 * t)
    melody += 0.12 * np.sin(2 * np.pi * 330 * t) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.5 * t))
    melody += 0.08 * np.sin(2 * np.pi * 440 * t + 0.3 * np.sin(2 * np.pi * 1.0 * t))

    percussion = np.zeros_like(t)
    for beat_index, beat_time in enumerate(np.arange(0.0, duration, beat_interval)):
        start = int(beat_time * sample_rate)
        length = int(0.09 * sample_rate)
        end = min(start + length, len(percussion))
        if end <= start:
            continue
        n = np.arange(end - start)
        env = np.exp(-n / (0.018 * sample_rate))
        freq = 80 if beat_index % 4 == 0 else 140
        click = np.sin(2 * np.pi * freq * n / sample_rate) * env
        noise = np.random.default_rng(beat_index).normal(0, 0.08, end - start) * env
        percussion[start:end] += 0.72 * click + noise

    signal = melody + percussion
    signal = signal / max(1e-9, np.max(np.abs(signal))) * 0.88
    write_wav(path, signal, sample_rate)
    return AudioData(signal=signal.astype(np.float32), sample_rate=sample_rate)


def frame_signal(signal: np.ndarray, frame_size: int, hop_size: int) -> np.ndarray:
    if len(signal) < frame_size:
        pad = np.zeros(frame_size - len(signal), dtype=signal.dtype)
        signal = np.concatenate([signal, pad])
    frame_count = 1 + math.floor((len(signal) - frame_size) / hop_size)
    frames = np.empty((frame_count, frame_size), dtype=np.float32)
    for i in range(frame_count):
        start = i * hop_size
        frames[i] = signal[start : start + frame_size]
    return frames


def compute_stft(signal: np.ndarray, sample_rate: int, frame_size: int = 2048, hop_size: int = 512) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    frames = frame_signal(signal, frame_size, hop_size)
    window = np.hanning(frame_size).astype(np.float32)
    spectrum = np.fft.rfft(frames * window[None, :], axis=1)
    magnitude = np.abs(spectrum).T
    freqs = np.fft.rfftfreq(frame_size, d=1.0 / sample_rate)
    times = (np.arange(frames.shape[0]) * hop_size + frame_size / 2) / sample_rate
    return times, freqs, magnitude


def compute_spectrum(signal: np.ndarray, sample_rate: int) -> tuple[np.ndarray, np.ndarray]:
    window = np.hanning(len(signal)).astype(np.float32)
    spectrum = np.fft.rfft(signal * window)
    freqs = np.fft.rfftfreq(len(signal), d=1.0 / sample_rate)
    magnitude = np.abs(spectrum)
    magnitude /= max(1e-9, magnitude.max())
    return freqs, magnitude


def spectral_flux(stft_magnitude: np.ndarray) -> np.ndarray:
    diff = np.diff(stft_magnitude, axis=1)
    flux = np.maximum(diff, 0.0).sum(axis=0)
    flux = np.insert(flux, 0, 0.0)
    flux -= flux.min()
    flux /= max(1e-9, flux.max())
    kernel = np.ones(5, dtype=np.float32) / 5.0
    return np.convolve(flux, kernel, mode="same")


def pick_beats(onset_times: np.ndarray, envelope: np.ndarray, min_distance: float = 0.28) -> np.ndarray:
    threshold = float(envelope.mean() + 0.55 * envelope.std())
    peaks: list[int] = []
    last_time = -min_distance
    for i in range(1, len(envelope) - 1):
        is_peak = envelope[i] >= envelope[i - 1] and envelope[i] > envelope[i + 1]
        if is_peak and envelope[i] >= threshold and onset_times[i] - last_time >= min_distance:
            peaks.append(i)
            last_time = float(onset_times[i])
    return onset_times[peaks]


def estimate_bpm(beat_times: np.ndarray) -> float:
    if len(beat_times) < 2:
        return 0.0
    intervals = np.diff(beat_times)
    intervals = intervals[(intervals > 0.25) & (intervals < 1.5)]
    if len(intervals) == 0:
        return 0.0
    bpm = 60.0 / float(np.median(intervals))
    while bpm < 70:
        bpm *= 2
    while bpm > 180:
        bpm /= 2
    return bpm


def analyze_audio(audio: AudioData) -> AnalysisResult:
    signal = audio.signal.astype(np.float32)
    signal = signal - float(signal.mean())
    signal = signal / max(1e-9, float(np.max(np.abs(signal))))

    times = np.arange(len(signal)) / audio.sample_rate
    spectrum_freqs, spectrum_magnitude = compute_spectrum(signal, audio.sample_rate)
    stft_times, stft_freqs, stft_magnitude = compute_stft(signal, audio.sample_rate)
    envelope = spectral_flux(stft_magnitude)
    beat_times = pick_beats(stft_times, envelope)
    bpm = estimate_bpm(beat_times)

    return AnalysisResult(
        sample_rate=audio.sample_rate,
        duration=len(signal) / audio.sample_rate,
        times=times,
        signal=signal,
        spectrum_freqs=spectrum_freqs,
        spectrum_magnitude=spectrum_magnitude,
        stft_times=stft_times,
        stft_freqs=stft_freqs,
        stft_magnitude=stft_magnitude,
        onset_times=stft_times,
        onset_envelope=envelope,
        beat_times=beat_times,
        bpm=bpm,
    )


def analyze_wav(path: str | Path) -> AnalysisResult:
    return analyze_audio(read_wav(path))
