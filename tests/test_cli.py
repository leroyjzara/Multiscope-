import pytest

from multiscope.cli import parse_args


def test_parse_args_requires_media_without_demo():
    with pytest.raises(SystemExit):
        parse_args([])


def test_parse_args_demo_without_media():
    args = parse_args(["--demo"])
    assert args.demo is True
    assert args.media is None


def test_parse_args_demo_with_media_forbidden():
    with pytest.raises(SystemExit):
        parse_args(["--demo", "video.mp4"])
