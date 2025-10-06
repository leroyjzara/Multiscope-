"""Tests for the Multiscope web preview application."""

from __future__ import annotations

import io
from urllib.parse import urlencode

import pytest
from wsgiref.util import setup_testing_defaults

from multiscope import webapp
from multiscope.webapp import create_app


@pytest.fixture()
def app():
    return create_app()


def _request(app, method: str = "GET", data: dict[str, str] | None = None):
    environ: dict[str, object] = {}
    setup_testing_defaults(environ)
    environ["REQUEST_METHOD"] = method

    body = b""
    if data is not None:
        body = urlencode(data, doseq=True).encode("utf-8")
        environ["CONTENT_TYPE"] = "application/x-www-form-urlencoded"
    environ["CONTENT_LENGTH"] = str(len(body))
    environ["wsgi.input"] = io.BytesIO(body)

    captured: dict[str, object] = {}

    def start_response(status: str, headers: list[tuple[str, str]]):
        captured["status"] = status
        captured["headers"] = {key: value for key, value in headers}

    response_body = b"".join(app(environ, start_response))
    return captured["status"], captured["headers"], response_body


def test_get_index(app):
    status, headers, body = _request(app)
    assert status == "200 OK"
    assert headers["Content-Type"].startswith("text/html")
    assert b"Multiscope preview" in body


def test_demo_submission(app):
    status, _, body = _request(app, method="POST", data={"demo": "1"})
    text = body.decode("utf-8")
    assert status == "200 OK"
    assert "Musical" in text
    assert "Dance" in text
    assert "Ethnography" in text


def test_requires_media_when_not_demo(app):
    status, _, body = _request(app, method="POST", data={})
    assert status == "200 OK"
    assert b"Please provide a media file or enable demo mode" in body


def test_metadata_validation_error(app):
    status, _, body = _request(app, method="POST", data={"metadata": "[]", "demo": "1"})
    assert status == "200 OK"
    assert b"Metadata must be a JSON object" in body


def test_main_cli_arguments(monkeypatch, capsys):
    captured: dict[str, object] = {}

    class DummyServer:
        def __enter__(self):
            captured["entered"] = True
            return self

        def __exit__(self, exc_type, exc, tb):  # noqa: D401 - standard context manager signature
            captured["exited"] = True
            return False

        def serve_forever(self):
            captured["served"] = True

    def fake_server(host, port, app):
        captured["host"] = host
        captured["port"] = port
        captured["app"] = app
        return DummyServer()

    monkeypatch.setattr(webapp, "create_app", lambda: "stub-app")
    monkeypatch.setattr(webapp, "make_server", fake_server)

    webapp.main(["--host", "0.0.0.0", "--port", "8001"])

    assert captured["host"] == "0.0.0.0"
    assert captured["port"] == 8001
    assert captured["app"] == "stub-app"
    assert captured["entered"] is True
    assert captured["served"] is True
    assert captured["exited"] is True
