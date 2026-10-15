"""Automated pytest test for demo video artifact."""

from pathlib import Path
from scripts.test_video import test_video as check_video_validity

VIDEO_PATH = Path("outputs/routewatch_demo.mp4")


def test_routewatch_demo_video_artifact():
    """Ensure routewatch_demo.mp4 exists, has valid format, duration, and can be decoded."""
    assert VIDEO_PATH.exists(), f"Demo video {VIDEO_PATH} does not exist"
    assert check_video_validity(play=False) is True
