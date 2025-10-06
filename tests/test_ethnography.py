from multiscope.audio_analysis import MusicalAnalysis
from multiscope.dance_analysis import DanceAnalysis
from multiscope.ethnography import CulturalEthnographer


def test_ethnographer_generates_structured_report():
    musical = MusicalAnalysis(
        tempo_bpm=95.0,
        key="D4",
        mode="Major",
        energy=0.4,
        spectral_centroid=1200.0,
        commentary="Moderate tempo with balanced energy and mid-range timbre.",
    )
    dance = DanceAnalysis(
        average_motion=0.08,
        motion_variability=0.03,
        direction_changes=4,
        footwork_intensity=0.06,
        commentary=(
            "High motion energy points to vigorous, full-bodied choreography. "
            "Variation in motion indicates dynamic phrasing and spatial exploration."
        ),
    )

    ethnographer = CulturalEthnographer()
    report = ethnographer.generate(
        musical,
        dance,
        metadata={
            "location": "coastal West Africa",
            "era": "the mid-20th century",
            "performer": "a community ensemble",
            "musical_tradition": "ancestral polyrhythmic ceremonies",
            "dance_lineage": "diasporic circle dances",
            "attire": "vibrant handwoven textiles",
        },
    )

    assert "coastal West Africa" in report.summary
    assert "polyrhythmic" in report.musical_context
    assert "circle dances" in report.dance_context
    assert "community_participation" in report.cultural_indicators
