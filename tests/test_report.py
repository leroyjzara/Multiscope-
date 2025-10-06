from multiscope.report import generate_demo_report


def test_generate_demo_report_uses_deterministic_values():
    metadata = {"location": "Test City"}
    report = generate_demo_report(metadata=metadata)

    assert report.musical.key == "D Minor"
    assert report.musical.tempo_bpm == 108.0
    assert report.dance.direction_changes == 7
    assert "Test City" in report.ethnography.summary
