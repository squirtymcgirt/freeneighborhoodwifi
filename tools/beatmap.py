#!/usr/bin/env python3
"""Precompute a light-show map from a video's audio: web/beats.json.

  env  : bass energy, one hex digit (0-f) per 50 ms step
  kick : '1' on steps where a kick/beat onset lands, else '0'

The room page reads video.currentTime and indexes these strings, so the
lights follow the music with no live audio analysis on the phone.
Usage: beatmap.py input.mp4 [--out web/beats.json]
"""
import argparse, json, os, subprocess
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("input")
ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "..", "web", "beats.json"))
a = ap.parse_args()

SR, HOP = 8000, 400                                   # 50 ms steps
pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", a.input, "-vn", "-ac", "1", "-ar", str(SR),
                      "-f", "s16le", "-"], check=True, stdout=subprocess.PIPE).stdout
x = np.frombuffer(pcm, np.int16).astype(np.float32) / 32768
n = len(x) // HOP
win = np.hanning(1024).astype(np.float32)
pad = np.pad(x, (512, 512))
frames = np.stack([pad[i * HOP:i * HOP + 1024] * win for i in range(n)])
spec = np.abs(np.fft.rfft(frames, axis=1))
freqs = np.fft.rfftfreq(1024, 1 / SR)
bass = spec[:, (freqs >= 40) & (freqs <= 160)].sum(1)

# envelope: log bass, normalised against a ~3 s rolling median so quiet
# verses still breathe and the chorus doesn't just pin at max
lb = np.log1p(bass * 50)
k = 61
med = np.array([np.median(lb[max(0, i - k):i + k]) for i in range(n)])
env = np.clip((lb - med * 0.85) / (np.percentile(lb, 98) - med.mean() * 0.85 + 1e-6), 0, 1)

# kicks: positive spectral flux in the kick band only (so hats/snares on the
# off-beats don't count), peak-picked against a local mean
kb = spec[:, (freqs >= 40) & (freqs <= 120)]
flux = np.maximum(np.diff(np.log1p(kb * 50), axis=0, prepend=0), 0).sum(1)
thr = np.convolve(flux, np.ones(15) / 15, "same") * 1.6 + 1e-6
kick = np.zeros(n, bool)
for i in range(1, n - 1):
    if flux[i] > thr[i] and flux[i] >= flux[i - 1] and flux[i] >= flux[i + 1] and not kick[max(0, i - 7):i].any():
        kick[i] = True                                  # >= 350 ms apart

# tempo: comb search. For each candidate beat period P (fine grid), sum the
# kick-train autocorrelation at P, 2P .. 8P. A wrong multiple (e.g. 3/2 of
# the true period) only lines up at some of those lags, the true one at all.
ks = np.convolve(kick.astype(float), [0.25, 0.5, 1, 0.5, 0.25], "same")
ac = np.array([np.dot(ks[:-L], ks[L:]) if L else 0 for L in range(0, 200)])
acf = lambda x: np.interp(x, np.arange(len(ac)), ac)
periods = np.arange(60 / 170 / 0.05, 60 / 70 / 0.05, 0.005)      # 70..170 BPM
score = [sum(acf(m * P) for m in range(1, 9)) for P in periods]
bpm = 60 / (periods[int(np.argmax(score))] * 0.05)

out = {"step": 0.05, "bpm": round(bpm, 2),
       "env": "".join("%x" % v for v in np.round(env * 15).astype(int)),
       "kick": "".join("1" if b else "0" for b in kick)}
json.dump(out, open(a.out, "w"), separators=(",", ":"))
print(f"beats.json: {n} steps, {kick.sum()} kicks, tempo {bpm:.1f} BPM, {os.path.getsize(a.out)} bytes")
