import math

from multiscope.audio_analysis import AudioAnalyzer


def test_analyze_signal_for_pure_tone_detects_pitch_and_energy():
    analyzer = AudioAnalyzer(sample_rate=4000)
    duration = 0.5
    sample_count = int(analyzer.sample_rate * duration)
    signal = [math.sin(2 * math.pi * 440.0 * i / analyzer.sample_rate) for i in range(sample_count)]

    result = analyzer.analyze_signal(signal, analyzer.sample_rate)

    assert result.key.startswith("A")
    assert result.energy > 0.5
    assert isinstance(result.commentary, str) and len(result.commentary) > 0
