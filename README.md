# PORTOKO — Motion Showreel

`PORTOKO_showreel.mp4` — 20 s, 1920×1080, 60 fps, with a synthesized score.

| Time | Act | What happens |
|---|---|---|
| 0–2 s | Ignition | Dot matrix, ripples on each beat, implosion into a point |
| 2–5 s | Big Bang | Particle burst and shockwaves; MOTION → **E**MOTION; zoom through the O |
| 5–8 s | Kinetic type | One word per beat (TIMING, RHYTHM, PHYSICS, LIGHT, FORM, FLOW, SCOPE), each with its own animation; the O in SCOPE becomes a portal |
| 8–11.5 s | Orbit | Black hole with an accretion disk, gravitational lensing and glass shards (based on the reference image) |
| 11.5–14 s | Flow | 2,600 curl-noise particles that condense into the wordmark |
| 14–17.5 s | Identity | Logo hit, orbit rings around each O, light sweeps, tagline; iris out through the middle O |
| 17.5–20 s | End card | Original brand logo on white |

## Rebuild
```
cd showreel
python3 audio.py score.wav          # numpy
node render.mjs frames              # playwright + chromium -> frames/*.jpg
ffmpeg -framerate 60 -i frames/%05d.jpg -i score.wav -c:v libx264 -crf 17 -pix_fmt yuv420p -c:a aac -b:a 256k -shortest ../PORTOKO_showreel.mp4
```
To preview live, open `showreel/index.html` through any local HTTP server (`?t=9.5` freezes on one frame).
