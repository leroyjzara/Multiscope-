# Multiscope

Multiscope is a proof-of-concept multimodal analysis toolkit capable of extracting
musical, dance, and cultural ethnographic insights from a single video asset. The
project demonstrates how audio and motion descriptors can be fused into
human-readable reports for researchers, curators, or artists exploring cultural
performances.

## Features

- **Musical analysis** – estimates tempo, key, mode, spectral centroid, and
  generates descriptive commentary about the soundtrack.
- **Dance analysis** – samples video frames to measure motion energy, variation,
  directional changes, and footwork articulation.
- **Cultural ethnography** – transforms musical and choreographic descriptors
  (plus optional metadata) into a contextual narrative and indicator matrix.
- **Command line interface** – run the full pipeline on a video and export the
  structured report as JSON.

## Installation

Create and activate a virtual environment, then install the dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Some analysis features rely on optional multimedia libraries (`librosa`,
`moviepy`, `numpy`, and `opencv-python`). Install system codecs such as `ffmpeg`
for wide format support when running locally. When these scientific libraries
are unavailable, Multiscope falls back to pure Python heuristics so the toolkit
remains functional for lightweight experiments.

## Usage

Analyse a video and print the resulting report:

```bash
python -m multiscope.cli path/to/performance.mp4
```

Preview the software without supplying media by generating a deterministic demo report:

```bash
python -m multiscope.cli --demo
```

You can still attach metadata to the demo mode to see how contextual information is
incorporated into the narrative output.

### Web preview interface

Launch the built-in web application for an interactive experience:

```bash
python -m multiscope.webapp
```

Override the bind address or port if you want to reach the preview from other devices on
your network:

```bash
python -m multiscope.webapp --host 0.0.0.0 --port 8000
```

Visit <http://127.0.0.1:5000> (or the host/port you configured) to upload a media file or
toggle demo mode, paste optional metadata as JSON, and review the rendered report directly
in your browser. The page works entirely offline and mirrors the CLI pipeline, making it
easy to share previews with collaborators.

Optionally provide metadata to enrich the ethnographic narrative:

```bash
python -m multiscope.cli path/to/performance.mp4 \
  --metadata docs/context.json \
  --output reports/performance.json
```

The output JSON contains three top-level sections (`musical`, `dance`, and
`ethnography`) that can be ingested by downstream archival or presentation
systems.

## Testing

Run the automated test suite with:

```bash
pytest
```

The included tests focus on deterministic, dependency-free components of the
pipeline such as the mathematical feature extraction and ethnographic
translation logic.

