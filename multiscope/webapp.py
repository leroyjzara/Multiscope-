"""Minimal WSGI web application for previewing Multiscope reports."""

from __future__ import annotations

import argparse
import html
import io
import json
import tempfile
from collections.abc import Sequence
from dataclasses import asdict
from pathlib import Path
from typing import Any, Callable, Iterable
from wsgiref.simple_server import make_server

from .report import MultiscopeReport, generate_demo_report, generate_report


StartResponse = Callable[[str, list[tuple[str, str]]], None]
WSGIApp = Callable[[dict[str, Any], StartResponse], Iterable[bytes]]


def create_app() -> WSGIApp:
    """Return a WSGI application that renders the preview interface."""

    def app(environ: dict[str, Any], start_response: StartResponse) -> Iterable[bytes]:
        method = environ.get("REQUEST_METHOD", "GET").upper()

        if method == "POST":
            status, headers, body = _handle_post(environ)
        else:
            status, headers, body = _render_response()

        start_response(status, headers)
        return [body.encode("utf-8")]

    return app


def _handle_post(environ: dict[str, Any]) -> tuple[str, list[tuple[str, str]], str]:
    form = _parse_form(environ)
    metadata_raw = form.get("metadata", "").strip()
    demo_requested = form.get("demo") == "1"

    error: str | None = None
    metadata: dict[str, Any] = {}

    if metadata_raw:
        try:
            parsed = json.loads(metadata_raw)
        except json.JSONDecodeError as exc:
            error = f"Metadata must be valid JSON: {exc.msg}."
        else:
            if not isinstance(parsed, dict):
                error = "Metadata must be a JSON object."
            else:
                metadata = parsed

    media_field = form.get("media_file")
    if not demo_requested and error is None:
        if media_field is None or media_field.filename == "":
            error = "Please provide a media file or enable demo mode."

    if error:
        body = _render_template(error, metadata_raw, demo_requested, None)
        return _build_response(body)

    try:
        if demo_requested:
            report = generate_demo_report(metadata=metadata)
        else:
            assert media_field is not None  # for type checkers
            suffix = Path(media_field.filename).suffix or ".mp4"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                media_field.file.seek(0)
                tmp.write(media_field.file.read())
                temp_path = Path(tmp.name)
            try:
                report = generate_report(temp_path, metadata=metadata)
            finally:
                temp_path.unlink(missing_ok=True)
    except Exception as exc:
        body = _render_template(str(exc), metadata_raw, demo_requested, None)
        return _build_response(body)

    sections = _format_report(report)
    body = _render_template(None, metadata_raw, demo_requested, sections)
    return _build_response(body)


def _parse_form(environ: dict[str, Any]) -> dict[str, Any]:
    content_type = environ.get("CONTENT_TYPE", "")
    content_length = int(environ.get("CONTENT_LENGTH", "0") or 0)
    body = environ.get("wsgi.input", io.BytesIO()).read(content_length)
    environ["wsgi.input"] = io.BytesIO(body)

    if content_type.startswith("multipart/form-data"):
        from cgi import FieldStorage

        environ_copy = environ.copy()
        environ_copy["QUERY_STRING"] = ""
        environ_copy["CONTENT_LENGTH"] = str(len(body))
        environ_copy["wsgi.input"] = io.BytesIO(body)
        field_storage = FieldStorage(fp=environ_copy["wsgi.input"], environ=environ_copy, keep_blank_values=True)
        fields: dict[str, Any] = {}
        if getattr(field_storage, "list", None):
            for field in field_storage.list:
                if field.name == "media":
                    fields["media_file"] = field
                elif field.name:
                    fields[field.name] = field.value
        return fields

    if body:
        decoded = body.decode("utf-8")
        params = {}
        for key, values in _parse_qs(decoded).items():
            params[key] = values[-1]
        return params

    return {}


def _parse_qs(query: str) -> dict[str, list[str]]:
    from urllib.parse import parse_qs

    return parse_qs(query, keep_blank_values=True)


def _render_template(
    error: str | None,
    metadata_source: str,
    demo: bool,
    report: list[dict[str, Any]] | None,
) -> str:
    error_block = f'<div class="error">{html.escape(error)}</div>' if error else ""
    demo_checked = "checked" if demo else ""
    metadata_html = html.escape(metadata_source)
    report_block = ""

    if report:
        sections_html = []
        for section in report:
            entries_html = []
            for entry in section["entries"]:
                label = html.escape(entry["label"])
                value = html.escape(entry["value"])
                entries_html.append(
                    f'<li class="entry"><strong>{label}</strong>: {value}</li>'
                )
            if entries_html:
                entries_markup = "<ul>" + "\n".join(entries_html) + "</ul>"
            else:
                entries_markup = '<p class="empty">No findings available.</p>'
            sections_html.append(
                f"<article><h2>{html.escape(section['title'])}</h2>{entries_markup}</article>"
            )
        report_block = f"<section>{''.join(sections_html)}</section>"

    return (
        TEMPLATE
        .replace("{{ERROR_BLOCK}}", error_block)
        .replace("{{METADATA_SOURCE}}", metadata_html)
        .replace("{{DEMO_CHECKED}}", demo_checked)
        .replace("{{REPORT_BLOCK}}", report_block)
    )


def _render_response() -> tuple[str, list[tuple[str, str]], str]:
    body = _render_template(None, "", False, None)
    return _build_response(body)


def _build_response(body: str) -> tuple[str, list[tuple[str, str]], str]:
    headers = [
        ("Content-Type", "text/html; charset=utf-8"),
        ("Content-Length", str(len(body.encode("utf-8")))),
    ]
    return "200 OK", headers, body


def _format_report(report: MultiscopeReport) -> list[dict[str, Any]]:
    data = asdict(report)
    sections: list[dict[str, Any]] = []
    for section_key, values in data.items():
        title = section_key.replace("_", " ").title()
        entries: list[dict[str, str]] = []
        if isinstance(values, dict):
            for key, value in values.items():
                entries.append({
                    "label": key.replace("_", " ").capitalize(),
                    "value": _format_value(value),
                })
        else:
            entries.append({"label": "Result", "value": _format_value(values)})
        sections.append({"title": title, "entries": entries})
    return sections


def _format_value(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.3f}".rstrip("0").rstrip(".")
    if isinstance(value, list):
        return ", ".join(_format_value(item) for item in value) if value else "—"
    if isinstance(value, dict):
        return json.dumps(value)
    return str(value)


TEMPLATE = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>Multiscope Preview</title>
    <style>
      :root {
        font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
        background-color: #f3f4f6;
        color: #111827;
      }
      body {
        margin: 0;
        padding: 2rem;
        display: flex;
        justify-content: center;
      }
      main {
        max-width: 960px;
        width: 100%;
        background: white;
        padding: 2rem;
        border-radius: 12px;
        box-shadow: 0 10px 30px rgba(15, 23, 42, 0.12);
      }
      h1 {
        margin-top: 0;
        font-size: 2rem;
      }
      form {
        display: grid;
        gap: 1rem;
        margin-bottom: 2rem;
      }
      label {
        font-weight: 600;
      }
      input[type="file"],
      textarea,
      button {
        font: inherit;
        padding: 0.6rem 0.75rem;
        border-radius: 8px;
        border: 1px solid #d1d5db;
      }
      textarea {
        min-height: 140px;
        resize: vertical;
      }
      button {
        background-color: #2563eb;
        color: white;
        border: none;
        cursor: pointer;
        transition: background-color 0.2s ease;
        justify-self: flex-start;
      }
      button:hover {
        background-color: #1d4ed8;
      }
      .checkbox {
        display: flex;
        align-items: center;
        gap: 0.5rem;
      }
      .error {
        background-color: #fee2e2;
        border: 1px solid #f87171;
        color: #b91c1c;
        padding: 0.75rem 1rem;
        border-radius: 8px;
        margin-bottom: 1.5rem;
      }
      section {
        margin-top: 2rem;
        border-top: 1px solid #e5e7eb;
        padding-top: 2rem;
      }
      h2 {
        margin-top: 0;
      }
      ul {
        padding-left: 1.25rem;
      }
      .entry {
        margin-bottom: 0.5rem;
      }
      .entry strong {
        display: inline-block;
        min-width: 180px;
      }
      .empty {
        font-style: italic;
        color: #6b7280;
      }
    </style>
  </head>
  <body>
    <main>
      <h1>Multiscope preview</h1>
      <p>
        Generate a multimodal analysis report from a video or quickly explore the
        deterministic demo output. Provide optional contextual metadata as JSON to
        enrich the cultural ethnography section.
      </p>

      {{ERROR_BLOCK}}

      <form method="post" enctype="multipart/form-data">
        <div>
          <label for="media">Media file</label><br />
          <input id="media" name="media" type="file" accept="video/*,audio/*" />
        </div>

        <div>
          <label for="metadata">Metadata (JSON object)</label><br />
          <textarea id="metadata" name="metadata" placeholder='{"location": "Lisbon", "era": "1960s"}'>{{METADATA_SOURCE}}</textarea>
        </div>

        <label class="checkbox">
          <input type="checkbox" name="demo" value="1" {{DEMO_CHECKED}} />
          Use demo report (skip media upload)
        </label>

        <button type="submit">Generate report</button>
      </form>

      {{REPORT_BLOCK}}
    </main>
  </body>
</html>
"""


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Launch the Multiscope preview WSGI application."
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Hostname or IP interface to bind (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="Port to listen on (default: 5000)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    args = _build_parser().parse_args(list(argv) if argv is not None else None)

    with make_server(args.host, args.port, create_app()) as server:
        print(f"Serving Multiscope preview on http://{args.host}:{args.port}")
        server.serve_forever()


if __name__ == "__main__":  # pragma: no cover - script execution path
    main()
