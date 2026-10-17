# Free Neighborhood Wi-Fi

The City of Schmeattle's public Wi-Fi sign-in page, at
[freeneighborhoodwifi.com](https://freeneighborhoodwifi.com/). It began as a
prank captive portal on an ESP32 access point; this is the static copy of its
site, served by GitHub Pages.

- `index.html`: the sign-in page. Any tap or link plays the video, with sound.
- Tap the city seal in the header five times for the council chambers: an
  A-Frame room with Blender-baked lighting, a TV, disco lights driven by a
  precomputed beat map, and a dancing resident on the dais. (On the access
  point the chambers are multiplayer with push-to-talk; here you're alone.)

## Your video here
The video here is five seconds of a certain chorus, looped. Make your own,
sized to fit on a 1.44 MB floppy (AV1 + Opus, two-pass, auto-cropped, with an HEVC/AAC copy for
iPhones), plus the beat map the room's lights follow:

    python3 tools/encode.py your.mp4 --out .
    python3 tools/beatmap.py your.mp4 --out beats.json   # --bpm N for clips under ~20 s

Needs ffmpeg built with libaom, libx265 and libopus, and Python 3 with numpy.
`tools/placeholder.py` makes a stand-in test card with a synthesized beat.

## Credits
- [A-Frame](https://aframe.io/) 1.7.0 (MIT), `aframe.min.js`
- The dancer: ["rick-astley"](https://sketchfab.com/3d-models/rick-astley-2aed6f33ce554ac59e2bfa92395ed6fa)
  by DAWCO1987 ([CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)), rigged with
  Make-It-Animatable; the dance is motion-captured with GVHMR from the Fortnite "Never Gonna" emote
- Room modelled and light-baked in Blender
