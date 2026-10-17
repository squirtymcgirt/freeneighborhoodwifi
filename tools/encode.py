#!/usr/bin/env python3
"""Turn a video into the two files the ESP32 serves.

  rr.webm : AV1 + Opus, two-pass, sized to fit a 1.44 MB floppy. Chrome and
            Firefox decode AV1 everywhere (dav1d), Safari on recent hardware.
  rr.mp4  : HEVC + AAC fallback for iPhones without AV1 decode.

Low-bitrate tricks: letterbox bars auto-cropped (no bits spent on black),
long GOP (keyframes are the expensive part), 48-frame lookahead, and 60 ms
Opus frames, which cut WebM per-packet overhead by ~40 KB over 3.5 minutes.

Usage: encode.py input.mp4 [--vk 40 --ak 14 --budget 1474560]
"""
import argparse, os, subprocess, tempfile

ap = argparse.ArgumentParser()
ap.add_argument("input")
ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "..", "web"))
ap.add_argument("--vk", type=int, default=40, help="video kbps")
ap.add_argument("--ak", type=int, default=14, help="Opus kbps")
ap.add_argument("--budget", type=int, default=1474560, help="warn if rr.webm exceeds (bytes)")
ap.add_argument("--no-hevc", action="store_true")
a = ap.parse_args()
os.makedirs(a.out, exist_ok=True)
tmp = tempfile.mkdtemp()
ff = lambda *x: subprocess.run(["ffmpeg", "-v", "error", "-y", *x], check=True)

det = subprocess.run(["ffmpeg", "-v", "info", "-i", a.input, "-vf", "cropdetect=24:2:0",
                      "-frames:v", "600", "-f", "null", "-"], stderr=subprocess.PIPE, text=True).stderr
crops = [l.rsplit("crop=", 1)[1].split()[0] for l in det.splitlines() if "crop=" in l]
vf = ["-vf", "crop=" + max(set(crops), key=crops.count)] if crops else []
print("filter", vf)

def two_pass(codec_args, out, audio_args):
    log = os.path.join(tmp, "pass")
    ff("-i", a.input, *vf, *codec_args, "-pass", "1", "-passlogfile", log, "-an", "-f", "null", "-")
    ff("-i", a.input, *vf, *codec_args, "-pass", "2", "-passlogfile", log, *audio_args,
       "-map_metadata", "-1", out)

webm = os.path.join(a.out, "rr.webm")
two_pass(["-c:v", "libaom-av1", "-b:v", f"{a.vk}k", "-cpu-used", "3", "-row-mt", "1",
          "-lag-in-frames", "48", "-g", "300"], webm,
         ["-ac", "1", "-c:a", "libopus", "-b:a", f"{a.ak}k", "-frame_duration", "60",
          "-application", "audio"])
n = os.path.getsize(webm)
print(f"rr.webm {n} bytes" + ("  (fits a floppy)" if n <= a.budget else f"  OVER budget by {n - a.budget}"))

if not a.no_hevc:
    mp4 = os.path.join(a.out, "rr.mp4")
    two_pass(["-c:v", "libx265", "-preset", "slow", "-b:v", f"{a.vk}k", "-tag:v", "hvc1",
              "-x265-params", "log-level=error:keyint=300"], mp4,
             ["-ac", "1", "-ar", "22050", "-c:a", "aac", "-b:a", "32k", "-movflags", "+faststart"])
    print(f"rr.mp4  {os.path.getsize(mp4)} bytes")
