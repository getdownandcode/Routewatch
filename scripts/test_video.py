"""Verification and health check script for outputs/routewatch_demo.mp4."""

import argparse
import json
import subprocess
import sys
from pathlib import Path

VIDEO_PATH = Path("outputs/routewatch_demo.mp4")


def test_video(play: bool = False) -> bool:
    print(f"🔍 Testing demo video: {VIDEO_PATH}")
    
    # 1. Check existence
    if not VIDEO_PATH.exists():
        print(f"❌ FAIL: File {VIDEO_PATH} does not exist!")
        return False
    
    size_bytes = VIDEO_PATH.stat().st_size
    size_mb = size_bytes / (1024 * 1024)
    print(f"  • File size: {size_mb:.2f} MB ({size_bytes:,} bytes)")
    if size_bytes < 100_000:
        print("❌ FAIL: Video file size is suspiciously small (< 100KB).")
        return False

    # 2. Probe with ffprobe
    ffprobe_bin = "/opt/homebrew/bin/ffprobe"
    cmd = [
        ffprobe_bin,
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        str(VIDEO_PATH),
    ]
    try:
        raw_out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        data = json.loads(raw_out)
    except Exception as e:
        print(f"❌ FAIL: Unable to probe video with ffprobe: {e}")
        return False

    # 3. Validate streams
    streams = data.get("streams", [])
    if not streams:
        print("❌ FAIL: No streams found in media container.")
        return False

    v_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
    if not v_stream:
        print("❌ FAIL: No video stream found.")
        return False

    codec = v_stream.get("codec_name")
    width = int(v_stream.get("width", 0))
    height = int(v_stream.get("height", 0))
    duration = float(v_stream.get("duration", 0.0))
    nb_frames = int(v_stream.get("nb_frames", 0))
    pix_fmt = v_stream.get("pix_fmt")

    print(f"  • Video Codec: {codec}")
    print(f"  • Resolution: {width}x{height}")
    print(f"  • Duration: {duration:.2f} seconds")
    print(f"  • Frame Count: {nb_frames} frames")
    print(f"  • Pixel Format: {pix_fmt}")

    errors = []
    if codec != "h264":
        errors.append(f"Expected codec 'h264', got '{codec}'")
    if width != 1280 or height != 720:
        errors.append(f"Expected resolution 1280x720, got {width}x{height}")
    if duration < 30.0:
        errors.append(f"Duration too short ({duration:.2f}s < 30s)")
    if nb_frames < 800:
        errors.append(f"Frame count too low ({nb_frames} < 800)")
    if pix_fmt != "yuv420p":
        errors.append(f"Pixel format {pix_fmt} is not universally web-compatible (expected yuv420p)")

    # 4. Test frame decode with ffmpeg
    ffmpeg_bin = "/opt/homebrew/bin/ffmpeg"
    decode_cmd = [
        ffmpeg_bin,
        "-v", "error",
        "-ss", "00:00:10",
        "-i", str(VIDEO_PATH),
        "-frames:v", "1",
        "-f", "null",
        "-",
    ]
    try:
        subprocess.check_output(decode_cmd, stderr=subprocess.STDOUT)
        print("  • Decoder check: Frame 00:00:10 decoded successfully (no stream corruption)")
    except subprocess.CalledProcessError as e:
        errors.append(f"FFmpeg decoding failed: {e.output.decode('utf-8', errors='ignore')}")

    if errors:
        print("\n❌ VIDEO VALIDATION FAILED:")
        for err in errors:
            print(f"  - {err}")
        return False

    print("\n✅ ALL VIDEO QUALITY & PLAYABILITY CHECKS PASSED!")

    # 5. Optional playback
    if play:
        print(f"▶️ Opening {VIDEO_PATH} in system player...")
        subprocess.run(["open", str(VIDEO_PATH)])

    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test and inspect demo video integrity.")
    parser.add_argument("--play", action="store_true", help="Launch the video in default player if checks pass.")
    args = parser.parse_args()

    success = test_video(play=args.play)
    sys.exit(0 if success else 1)
