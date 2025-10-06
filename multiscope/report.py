"""Top level orchestration of the multimodal Multiscope analysis pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .audio_analysis import AudioAnalyzer, MusicalAnalysis
from .dance_analysis import DanceAnalyzer, DanceAnalysis
from .ethnography import CulturalEthnographer, EthnographicReport


@dataclass
class MultiscopeReport:
    """Bundled representation of the different analytical outputs."""

    musical: MusicalAnalysis
    dance: DanceAnalysis
    ethnography: EthnographicReport


def generate_report(
    media_path: str | Path,
    *,
    audio_analyzer: Optional[AudioAnalyzer] = None,
    dance_analyzer: Optional[DanceAnalyzer] = None,
    ethnographer: Optional[CulturalEthnographer] = None,
    metadata: Optional[dict] = None,
) -> MultiscopeReport:
    """Run the full Multiscope pipeline on the supplied media file."""

    audio_analyzer = audio_analyzer or AudioAnalyzer()
    dance_analyzer = dance_analyzer or DanceAnalyzer()
    ethnographer = ethnographer or CulturalEthnographer()

    musical = audio_analyzer.analyze(media_path)
    dance = dance_analyzer.analyze(media_path)
    ethnography = ethnographer.generate(musical, dance, metadata)

    return MultiscopeReport(musical=musical, dance=dance, ethnography=ethnography)


def generate_demo_report(
    *,
    ethnographer: Optional[CulturalEthnographer] = None,
    metadata: Optional[dict] = None,
) -> MultiscopeReport:
    """Return a deterministic demo report for previewing Multiscope output."""

    ethnographer = ethnographer or CulturalEthnographer()
    metadata = metadata or {}

    musical = MusicalAnalysis(
        tempo_bpm=108.0,
        key="D Minor",
        mode="Minor",
        energy=0.62,
        spectral_centroid=1450.0,
        commentary=(
            "Steady mid-tempo pulse with expressive dynamics and a darker modal colour."
        ),
    )

    dance = DanceAnalysis(
        average_motion=0.318,
        motion_variability=0.142,
        direction_changes=7,
        footwork_intensity=0.487,
        commentary=(
            "Controlled yet expressive phrasing with grounded footwork and measured spins."
        ),
    )

    ethnography = ethnographer.generate(musical, dance, metadata)

    return MultiscopeReport(musical=musical, dance=dance, ethnography=ethnography)

