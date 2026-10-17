#!/usr/bin/env python3
"""Make the public site's stand-in video: a Schmeattle test card with a
synthesized 114 BPM beat (so the room's beat map still drives the lights).

Usage: placeholder.py out.mp4 [--seconds 34]
"""
import argparse, subprocess

ap = argparse.ArgumentParser()
ap.add_argument("out")
ap.add_argument("--seconds", type=float, default=34)
a = ap.parse_args()
B = 60 / 114.24                    # one beat at the song's tempo
font = subprocess.run(["fc-match", "-f", "%{file}", "DejaVu Sans:bold"], capture_output=True, text=True).stdout
ph = f"mod(t,{B})"                 # time since the last beat
audio = (f"0.55*sin(2*PI*(42+110*exp(-{ph}*32))*{ph})*exp(-{ph}*8)"                    # kick on every beat
         f"+0.12*(random(0)*2-1)*exp(-mod(t+{B / 2},{B})*70)"                           # hat on the off-beats
         f"+0.22*sin(2*PI*55*(1+0.5*gte(mod(t,{8 * B}),{4 * B}))*t)*exp(-mod(t,{B / 2})*5)")  # bass, two notes
text = lambda s, size, y, col: (f"drawtext=fontfile={font}:text='{s}':fontsize={size}:fontcolor={col}"
                                f":x=(w-text_w)/2:y={y}")
vf = ",".join([
    text("CITY OF SCHMEATTLE", 22, 40, "#c9a227"),
    text("YOUR VIDEO HERE", 54, 120, "#e8d48a"),
    text("python3 tools/encode.py your.mp4", 20, 205, "#c9d6e8"),
    text("python3 tools/beatmap.py your.mp4", 20, 235, "#c9d6e8"),
])
subprocess.run([
    "ffmpeg", "-v", "error", "-y",
    "-f", "lavfi", "-i", f"color=c=#0d2a4f:s=640x360:r=24:d={a.seconds}",
    "-f", "lavfi", "-i", f"aevalsrc='{audio}':s=44100:d={a.seconds}",
    "-filter_complex", f"[1:a]asplit[a][w];[w]showwaves=s=640x60:mode=cline:colors=#c9a227:r=24[wv];"
                       f"[0:v]{vf}[bg];[bg][wv]overlay=0:290[v]",
    "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-crf", "18", "-c:a", "aac", "-b:a", "128k", "-shortest", a.out,
], check=True)
print("wrote", a.out)
