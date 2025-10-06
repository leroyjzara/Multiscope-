from multiscope.dance_analysis import DanceAnalyzer


def _moving_square_frames(num_frames: int = 6, size: int = 32) -> list[list[list[float]]]:
    frames: list[list[list[float]]] = []
    for i in range(num_frames):
        frame = [[0.0 for _ in range(size)] for _ in range(size)]
        start = min(size - 8, i * 2)
        for y in range(8, 16):
            for x in range(start, start + 8):
                frame[y][x] = 1.0
        frames.append(frame)
    return frames


def test_analyze_frames_reports_motion():
    analyzer = DanceAnalyzer(frame_sample_rate=2)
    frames = _moving_square_frames()

    result = analyzer.analyze_frames(frames, fps=24.0)

    assert result.average_motion > 0
    assert result.footwork_intensity > 0
    assert "movement" in result.commentary.lower()
