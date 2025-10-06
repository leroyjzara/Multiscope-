"""Video motion analysis focused on dance movement characteristics."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


@dataclass
class DanceAnalysis:
    """Quantitative and qualitative measures describing movement."""

    average_motion: float
    motion_variability: float
    direction_changes: int
    footwork_intensity: float
    commentary: str


class DanceAnalyzer:
    """Analyze frame sequences to characterise dance-oriented motion."""

    def __init__(self, frame_sample_rate: int = 3):
        self.frame_sample_rate = frame_sample_rate

    def analyze(self, video_path: str | Path) -> DanceAnalysis:
        frames, fps = self._load_video_frames(video_path)
        return self.analyze_frames(frames, fps)

    def analyze_frames(self, frames: Sequence[Sequence[Sequence[float]]], fps: float) -> DanceAnalysis:
        if not frames:
            raise ValueError("At least one frame is required for dance analysis.")

        gray_frames = [self._to_grayscale(self._to_matrix(frame)) for frame in frames]
        motion_profile = self._motion_profile(gray_frames)
        movement_vectors = self._center_of_mass_trajectory(gray_frames)

        average_motion = float(sum(motion_profile) / len(motion_profile)) if motion_profile else 0.0
        motion_variability = float(self._stddev(motion_profile)) if motion_profile else 0.0
        direction_changes = self._count_direction_changes(movement_vectors)
        footwork_intensity = float(self._estimate_footwork_intensity(gray_frames))
        commentary = self._compose_commentary(
            average_motion, motion_variability, direction_changes, footwork_intensity, fps
        )

        return DanceAnalysis(
            average_motion=average_motion,
            motion_variability=motion_variability,
            direction_changes=direction_changes,
            footwork_intensity=footwork_intensity,
            commentary=commentary,
        )

    # ------------------------------------------------------------------
    def _load_video_frames(self, video_path: str | Path) -> tuple[list[list[list[float]]], float]:
        path = Path(video_path)
        if not path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        try:  # pragma: no cover - optional dependency
            import cv2
        except ModuleNotFoundError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("OpenCV (cv2) is required for video based dance analysis.") from exc

        capture = cv2.VideoCapture(path.as_posix())
        if not capture.isOpened():
            raise RuntimeError(f"Unable to open video: {video_path}")

        fps = capture.get(cv2.CAP_PROP_FPS) or 30.0
        stride = max(1, int(fps // self.frame_sample_rate))

        frames: list[list[list[float]]] = []
        frame_index = 0
        while True:
            ret, frame = capture.read()
            if not ret:
                break
            if frame_index % stride == 0:
                frames.append(self._to_matrix(frame))
            frame_index += 1
        capture.release()

        if not frames:
            raise RuntimeError("No frames were read from the provided video.")
        return frames, fps

    def _to_matrix(self, frame: Sequence) -> list[list[float]]:
        if hasattr(frame, "tolist"):
            return self._to_matrix(frame.tolist())
        if isinstance(frame, list) and frame:
            first = frame[0]
            if isinstance(first, list) and first and isinstance(first[0], (list, tuple)):
                return [
                    [[float(channel) for channel in pixel] for pixel in row]
                    for row in frame
                ]
            if isinstance(first, (list, tuple)):
                return [[float(value) for value in row] for row in frame]
            if isinstance(first, (int, float)):
                return [[float(value) for value in frame]]
        if isinstance(frame, Iterable):
            return [list(row) for row in frame]
        raise TypeError("Unsupported frame format")

    def _to_grayscale(self, frame: list[list[float]]) -> list[list[float]]:
        if frame and frame[0] and isinstance(frame[0][0], (list, tuple)):
            return [
                [0.2989 * pixel[0] + 0.5870 * pixel[1] + 0.1140 * pixel[2] for pixel in row]
                for row in frame
            ]
        return frame

    def _motion_profile(self, frames: Sequence[list[list[float]]]) -> list[float]:
        diffs: list[float] = []
        for prev, curr in zip(frames, frames[1:]):
            total = 0.0
            count = 0
            for y in range(min(len(prev), len(curr))):
                for x in range(min(len(prev[y]), len(curr[y]))):
                    total += abs(curr[y][x] - prev[y][x])
                    count += 1
            diffs.append(total / count if count else 0.0)
        return diffs

    def _center_of_mass_trajectory(self, frames: Sequence[list[list[float]]]) -> list[tuple[float, float]]:
        centers: list[tuple[float, float]] = []
        for frame in frames:
            total = sum(sum(row) for row in frame)
            if total == 0:
                centers.append((len(frame) / 2.0, len(frame[0]) / 2.0 if frame else 0.0))
                continue
            y_sum = 0.0
            x_sum = 0.0
            for y, row in enumerate(frame):
                for x, value in enumerate(row):
                    y_sum += y * value
                    x_sum += x * value
            centers.append((y_sum / total, x_sum / total))
        return centers

    def _count_direction_changes(self, trajectory: Sequence[tuple[float, float]]) -> int:
        if len(trajectory) < 3:
            return 0
        changes = 0
        prev_sign = 0
        for (prev_y, prev_x), (curr_y, curr_x) in zip(trajectory, trajectory[1:]):
            delta_x = curr_x - prev_x
            sign = 1 if delta_x > 0 else -1 if delta_x < 0 else 0
            if prev_sign != 0 and sign != 0 and sign != prev_sign:
                changes += 1
            if sign != 0:
                prev_sign = sign
        return changes

    def _estimate_footwork_intensity(self, frames: Sequence[list[list[float]]]) -> float:
        gradients: list[float] = []
        for frame in frames:
            total = 0.0
            count = 0
            for y in range(len(frame)):
                for x in range(len(frame[y])):
                    center = frame[y][x]
                    right = frame[y][x + 1] if x + 1 < len(frame[y]) else center
                    down = frame[y + 1][x] if y + 1 < len(frame) else center
                    total += ((right - center) ** 2 + (down - center) ** 2) ** 0.5
                    count += 1
            gradients.append(total / count if count else 0.0)
        return sum(gradients) / len(gradients) if gradients else 0.0

    def _stddev(self, values: Sequence[float]) -> float:
        if not values:
            return 0.0
        mean_value = sum(values) / len(values)
        variance = sum((value - mean_value) ** 2 for value in values) / len(values)
        return variance ** 0.5

    def _compose_commentary(
        self,
        average_motion: float,
        motion_variability: float,
        direction_changes: int,
        footwork_intensity: float,
        fps: float,
    ) -> str:
        descriptors = []

        if average_motion < 0.01:
            descriptors.append("Movement is minimal, indicating either stillness or slow gestures.")
        elif average_motion < 0.05:
            descriptors.append("The dance exhibits contained motion with deliberate control.")
        else:
            descriptors.append("High motion energy points to vigorous, full-bodied choreography.")

        if motion_variability < 0.01:
            descriptors.append("Motion variance is low, suggesting repeated, cyclical phrases.")
        else:
            descriptors.append("Variation in motion indicates dynamic phrasing and spatial exploration.")

        if direction_changes == 0:
            descriptors.append("The dancer maintains a consistent facing with minimal turns.")
        elif direction_changes < 3:
            descriptors.append("A handful of direction changes provide accent and contrast.")
        else:
            descriptors.append("Frequent turns and reorientations signal intricate partnering or folk steps.")

        if footwork_intensity < 0.02:
            descriptors.append("Footwork articulation is subtle, favouring upper-body expression.")
        elif footwork_intensity < 0.05:
            descriptors.append("Balanced footwork supports gestures across the body.")
        else:
            descriptors.append("Pronounced footwork dominates the choreography, highlighting rhythmic grounding.")

        effective_sampling = fps / max(1, fps // self.frame_sample_rate) if fps else 0
        descriptors.append(
            "Frame sampling at approximately "
            f"{effective_sampling:.1f} fps captures the movement envelope."
        )

        return " ".join(descriptors)

