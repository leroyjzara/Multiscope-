"""Audio analysis utilities for extracting musical attributes from video."""

from __future__ import annotations

import math
from collections.abc import Iterable as IterableABC
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Tuple


@dataclass
class MusicalAnalysis:
    """Container for musical findings extracted from audio."""

    tempo_bpm: float
    key: str
    mode: str
    energy: float
    spectral_centroid: float
    commentary: str


class AudioAnalyzer:
    """Analyze the soundtrack of a video to generate musical descriptors."""

    def __init__(self, sample_rate: int = 22_050) -> None:
        self.sample_rate = sample_rate

    def analyze(self, media_path: str | Path) -> MusicalAnalysis:
        """Load audio from *media_path* and compute a :class:`MusicalAnalysis`."""

        signal, sr = self._load_audio(media_path)
        return self.analyze_signal(signal, sr)

    # ------------------------------------------------------------------
    def analyze_signal(self, signal: Iterable[float] | Iterable[Iterable[float]], sample_rate: int | None = None) -> MusicalAnalysis:
        """Compute musical descriptors from a waveform iterable."""

        flattened = self._to_mono(signal)
        sr = sample_rate or self.sample_rate
        if not flattened:
            raise ValueError("Audio signal is empty; unable to perform analysis.")

        normalized = self._normalize(flattened)

        tempo = self._estimate_tempo(normalized, sr)
        key, mode = self._estimate_key_and_mode(normalized, sr)
        energy = self._rms(normalized)
        spectral_centroid = self._spectral_centroid(normalized, sr)
        commentary = self._compose_commentary(tempo, key, mode, energy, spectral_centroid)

        return MusicalAnalysis(
            tempo_bpm=float(tempo),
            key=key,
            mode=mode,
            energy=float(energy),
            spectral_centroid=float(spectral_centroid),
            commentary=commentary,
        )

    # ------------------------------------------------------------------
    def _load_audio(self, media_path: str | Path) -> Tuple[list[float], int]:
        path = Path(media_path)
        if not path.exists():
            raise FileNotFoundError(f"Could not locate media file: {media_path}")

        try:  # pragma: no cover - optional dependency
            import librosa

            signal, sr = librosa.load(path.as_posix(), sr=self.sample_rate)
            return self._tolist(signal), sr
        except ModuleNotFoundError:  # pragma: no cover - optional dependency
            pass

        try:  # pragma: no cover - optional dependency
            from moviepy.editor import AudioFileClip, VideoFileClip

            clip: AudioFileClip | VideoFileClip
            if path.suffix.lower() in {".wav", ".mp3", ".flac", ".ogg", ".m4a"}:
                clip = AudioFileClip(path.as_posix())
            else:
                clip = VideoFileClip(path.as_posix())

            audio_clip = clip.audio
            if audio_clip is None:
                raise RuntimeError(f"Media file '{media_path}' does not contain an audio track.")
            signal = audio_clip.to_soundarray(fps=self.sample_rate)
            clip.close()
            return self._tolist(signal), self.sample_rate
        except ModuleNotFoundError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError(
                "Unable to load audio because neither 'librosa' nor 'moviepy' is installed."
            ) from exc

    def _tolist(self, values: Iterable[float] | Iterable[Iterable[float]]) -> list:
        if hasattr(values, "tolist"):
            converted = values.tolist()
            if isinstance(converted, list):
                return converted
        if isinstance(values, (list, tuple)):
            return [self._tolist(item) if isinstance(item, IterableABC) and not isinstance(item, (str, bytes)) else float(item) for item in values]
        return [float(v) for v in values]

    def _to_mono(self, signal: Iterable[float] | Iterable[Iterable[float]]) -> list[float]:
        data = list(signal)
        if not data:
            return []
        first = data[0]
        if isinstance(first, (list, tuple)):
            sequences = [self._ensure_sequence(sample) for sample in data]
            mono = [sum(sample) / len(sample) if sample else 0.0 for sample in sequences]
            return mono
        return [float(x) for x in data]

    def _ensure_sequence(self, value: Iterable[float]) -> list[float]:
        if isinstance(value, list):
            return [float(component) for component in value]
        if isinstance(value, tuple):
            return [float(component) for component in value]
        if hasattr(value, "tolist"):
            return [float(component) for component in value.tolist()]
        if isinstance(value, IterableABC):
            return [float(component) for component in value]
        return [float(value)]

    def _normalize(self, signal: Iterable[float]) -> list[float]:
        absolute = [abs(x) for x in signal]
        peak = max(absolute)
        if peak == 0:
            return list(signal)
        return [x / peak for x in signal]

    def _rms(self, signal: Iterable[float]) -> float:
        squares = [x * x for x in signal]
        return math.sqrt(sum(squares) / len(squares))

    def _estimate_tempo(self, signal: list[float], sample_rate: int) -> float:
        window = max(1, int(sample_rate * 0.05))
        envelope = self._moving_average([abs(x) for x in signal], window)
        mean_env = sum(envelope) / len(envelope)
        centered = [x - mean_env for x in envelope]
        if all(abs(x) < 1e-9 for x in centered):
            return 0.0

        min_bpm, max_bpm = 40, 200
        min_lag = max(1, int(sample_rate * 60 / max_bpm))
        max_lag = min(len(centered) - 1, int(sample_rate * 60 / max(min_bpm, 1)))
        if max_lag <= min_lag:
            return 0.0

        best_value = float("-inf")
        best_lag = min_lag
        for lag in range(min_lag, max_lag):
            correlation = sum(centered[i] * centered[i + lag] for i in range(len(centered) - lag))
            if correlation > best_value:
                best_value = correlation
                best_lag = lag

        if best_lag == 0:
            return 0.0
        return 60.0 * sample_rate / best_lag

    def _estimate_key_and_mode(self, signal: list[float], sample_rate: int) -> Tuple[str, str]:
        zero_crossings = self._zero_crossings(signal)
        duration = len(signal) / sample_rate
        if zero_crossings == 0 or duration == 0:
            return "Unknown", "Unknown"

        frequency = zero_crossings / (2 * duration)
        key = self._frequency_to_note(frequency)

        positive_energy = sum(max(x, 0) ** 2 for x in signal)
        negative_energy = sum(max(-x, 0) ** 2 for x in signal)
        mode = "Major" if positive_energy >= negative_energy else "Minor"
        return key, mode

    def _spectral_centroid(self, signal: list[float], sample_rate: int) -> float:
        if len(signal) < 2:
            return 0.0
        differences = [abs(signal[i + 1] - signal[i]) for i in range(len(signal) - 1)]
        if not differences:
            return 0.0
        avg_diff = sum(differences) / len(differences)
        return avg_diff * sample_rate / 2

    def _zero_crossings(self, signal: list[float]) -> int:
        count = 0
        for prev, curr in zip(signal, signal[1:]):
            if (prev <= 0 < curr) or (prev >= 0 > curr):
                count += 1
        return count

    def _moving_average(self, values: list[float], window: int) -> list[float]:
        if window <= 1:
            return values
        averaged = []
        cumulative = 0.0
        queue: list[float] = []
        for value in values:
            queue.append(value)
            cumulative += value
            if len(queue) > window:
                cumulative -= queue.pop(0)
            averaged.append(cumulative / len(queue))
        return averaged

    def _frequency_to_note(self, frequency: float) -> str:
        if frequency <= 0:
            return "Unknown"
        note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        midi_number = int(round(69 + 12 * math.log2(frequency / 440.0)))
        octave = midi_number // 12 - 1
        name = note_names[midi_number % 12]
        return f"{name}{octave}"

    def _compose_commentary(
        self,
        tempo: float,
        key: str,
        mode: str,
        energy: float,
        spectral_centroid: float,
    ) -> str:
        descriptors = []
        if tempo == 0:
            descriptors.append("The soundtrack lacks a perceivable pulse, implying an ambient texture.")
        elif tempo < 70:
            descriptors.append("The tempo is slow, suggesting a contemplative or ritual pacing.")
        elif tempo < 110:
            descriptors.append("The moderate tempo leaves room for expressive phrasing.")
        else:
            descriptors.append("The brisk tempo points to lively movement and communal energy.")

        descriptors.append(f"Dominant pitch content centers around {key} ({mode} tonality).")

        if energy < 0.1:
            descriptors.append("Overall dynamics are soft and restrained.")
        elif energy < 0.3:
            descriptors.append("Energy levels remain balanced, with measured intensity.")
        else:
            descriptors.append("High average energy hints at emphatic percussion or dense instrumentation.")

        if spectral_centroid < 500:
            descriptors.append("Timbre leans toward low, resonant textures.")
        elif spectral_centroid < 2000:
            descriptors.append("Mid-range timbres dominate the mix, providing warmth and clarity.")
        else:
            descriptors.append("A bright timbral profile indicates significant high-frequency content.")

        return " ".join(descriptors)

