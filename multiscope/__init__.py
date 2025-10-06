"""Multiscope multimodal analysis toolkit."""

from .audio_analysis import AudioAnalyzer, MusicalAnalysis
from .dance_analysis import DanceAnalyzer, DanceAnalysis
from .ethnography import CulturalEthnographer
from .report import MultiscopeReport, generate_demo_report, generate_report
from .webapp import create_app

__all__ = [
    "AudioAnalyzer",
    "MusicalAnalysis",
    "DanceAnalyzer",
    "DanceAnalysis",
    "CulturalEthnographer",
    "MultiscopeReport",
    "generate_demo_report",
    "generate_report",
    "create_app",
]
