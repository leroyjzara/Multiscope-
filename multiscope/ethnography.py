"""Generate cultural and ethnographic narratives from analysis signals."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from .audio_analysis import MusicalAnalysis
from .dance_analysis import DanceAnalysis


@dataclass
class EthnographicReport:
    """Structured cultural interpretation of the analysed performance."""

    summary: str
    musical_context: str
    dance_context: str
    cultural_indicators: Dict[str, str]


class CulturalEthnographer:
    """Compose cultural insights from musical and choreographic descriptors."""

    def generate(
        self,
        musical: MusicalAnalysis,
        dance: DanceAnalysis,
        metadata: Optional[dict] = None,
    ) -> EthnographicReport:
        metadata = metadata or {}

        summary = self._build_summary(musical, dance, metadata)
        musical_context = self._build_musical_context(musical, metadata)
        dance_context = self._build_dance_context(dance, metadata)
        cultural_indicators = self._build_indicators(musical, dance, metadata)

        return EthnographicReport(
            summary=summary,
            musical_context=musical_context,
            dance_context=dance_context,
            cultural_indicators=cultural_indicators,
        )

    def _build_summary(self, musical: MusicalAnalysis, dance: DanceAnalysis, metadata: dict) -> str:
        location = metadata.get("location", "an unspecified locale")
        era = metadata.get("era", "contemporary times")
        performer = metadata.get("performer", "the featured performers")

        return (
            f"Set in {location} during {era}, {performer} present a performance where "
            f"music in {musical.key} ({musical.mode}) converges with a dance exhibiting "
            f"{dance.commentary.lower()}"
        )

    def _build_musical_context(self, musical: MusicalAnalysis, metadata: dict) -> str:
        instruments = metadata.get("instruments", "percussion and melodic instruments")
        tradition = metadata.get("musical_tradition", "regional folk traditions")

        return (
            f"Tempo around {musical.tempo_bpm:.1f} BPM and {musical.commentary.lower()} "
            f"hint at {tradition}. Instrumentation likely features {instruments}."
        )

    def _build_dance_context(self, dance: DanceAnalysis, metadata: dict) -> str:
        dance_lineage = metadata.get("dance_lineage", "community-based line dances")
        attire = metadata.get("attire", "ceremonial garments")

        return (
            f"Movement quality marked by average motion {dance.average_motion:.3f} and "
            f"{dance.commentary.lower()} connects to {dance_lineage}. Costuming such as {attire} "
            "would complement the choreography."
        )

    def _build_indicators(
        self, musical: MusicalAnalysis, dance: DanceAnalysis, metadata: dict
    ) -> Dict[str, str]:
        indicators = {
            "community_participation": (
                "High",
                "Energetic tempo and frequent direction changes suggest group engagement.",
            ),
            "ritual_significance": (
                "Moderate" if musical.tempo_bpm > 0 else "Speculative",
                "Sustained rhythmic pulse implies repeated ceremonial use.",
            ),
            "gender_roles": (
                metadata.get("gender_roles", "Fluid"),
                "No direct indicators from movement; consider oral histories for clarity.",
            ),
        }

        return {key: f"{level}: {note}" for key, (level, note) in indicators.items()}

