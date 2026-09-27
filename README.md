# PORTOKO — brand film and teaser

| File | What |
|---|---|
| `PORTOKO_showreel.mp4` | 20 s brand film, 1080p60, bold motion graphics |
| `PORTOKO_teaser.mp4` | 30 s teaser, 1080p24: calm, painted real footage (see below) |
| `PORTOKO_film.mp4` | 20 s cinematic film, 1080p24: a match-cut montage of 39 real photographs on one circle, three words, then the O becomes the logo |
| `PORTOKO_pov.mp4` | 30 s film, 1080p30, cut to *Point of View* (petalcore): a 3D tangle that, from one exact angle, is a flower |

`PORTOKO_showreel.mp4` — 20 s, 1920×1080, 60 fps. The orchestral score is made only from real CC0 recordings.

The story follows [portoko.com](https://www.portoko.com): *a digital atelier with a consulting desk* that untangles how a business works, then configures, builds, connects or redesigns what needs changing in Odoo Community.

| Time | Act | Picture | Sound |
|---|---|---|---|
| 0–2 s | What's tangled | Dot matrix pulses, implodes | Typing, switches, dice; wine glass; timpani roll |
| 2–5 s | Untangle | Big bang; TANGLED → **UN**TANGLED ("5 spreadsheets · 2 WhatsApp groups") | Tutti hit with glass break and gong; pizzicato + glockenspiel hook; key-jingle shaker, switch hats, claps |
| 5–8 s | What we do | CONFIGURE, BUILD, CONNECT, REDESIGN, PROCESS, FLOW, ODOO, one per beat, with the site's subtitles; the last O becomes a portal | One object sound per word (switch, cube twist, glass tap, chime, dice, plop, wine glass) |
| 8–11.5 s | Honest advice | Black hole (from the reference image) | Half-time: string pad, harp, flute, chimes, bowed cymbal |
| 11.5–14 s | Fix the flow | Ink particles condense into the wordmark | Spiccato ostinato, snare + timpani rolls, rising run |
| 14–17.5 s | Portoko | Logo hit, orbiting O's, "A digital atelier · with a consulting desk" | The drop: hook on horns, strings and glock |
| 17.5–20 s | End card | Site colours, headline, "Tell us what's tangled" button, clicked on the last beat | C-major resolve, tubular bell, the final switch click |

## Rebuild
```
cd showreel
node render.mjs frames                                   # frames/*.jpg (Playwright + Chromium)
eval "$(audio/fetch_samples.sh | tail -1)"               # sparse-clone the CC0 samples
(cd audio && python3 compose.py ../score.wav)            # numpy, scipy, soundfile
ffmpeg -framerate 60 -i frames/%05d.jpg -i score.wav -c:v libx264 -crf 17 -pix_fmt yuv420p -c:a aac -b:a 256k -shortest ../PORTOKO_showreel.mp4
```
Preview live by serving `showreel/` over HTTP and opening `index.html` (`?t=9.5` freezes a frame). Sound sources are listed in `showreel/audio/CREDITS.md`.

## Teaser (`teaser/`)
Six still shots of real CC0 footage from Wikimedia Commons, painted as watercolour or acrylic on one sketchbook sheet, with ink captions. The shots change with a wet-wash wipe on each bar of a 60 BPM score.

| Time | Shot | Paint | Caption |
|---|---|---|---|
| 0–4 s | Fog on a lake | watercolour, blooms onto the empty sheet | — |
| 4–8 s | Threads on a loom | watercolour | Every business gets a little tangled. |
| 8–12 s | Glasses on a laptop | acrylic | Five spreadsheets, two WhatsApp groups, and an Odoo nobody trusts. |
| 12–16 s | Hands at a potter's wheel | acrylic | So we sit down, and look at how it really works. |
| 16–20 s | A candle | acrylic | Then we untangle it. Gently. |
| 20–24 s | Sunset | watercolour | Configure · Build · Connect · Redesign |
| 24–30 s | Wordmark painted in brand colours | watercolour | A digital *atelier* with a consulting desk. / Tell us what's tangled. |

Rebuild:
```
cd teaser
python3 tools/commons_get.py footage "Morning Fog on Lake BRoll 10s.webm" ...   # file titles in CREDITS.md
node tools/logo_mask.mjs assets/logo_mask.png                                     # (already committed)
python3 render_teaser.py                                                          # frames/*.jpg (numpy, opencv, pillow)
(cd ../showreel/audio && python3 teaser_score.py ../../teaser/score.wav)
ffmpeg -framerate 24 -i frames/%05d.jpg -i score.wav -c:v libx264 -crf 16 -tune grain -pix_fmt yuv420p -c:a aac -b:a 256k -shortest ../PORTOKO_teaser.mp4
```

## Film (`film/`)
The film is a match-cut montage. 39 public-domain and CC0 photographs, all of round things (the sun, Earth, a 1635 engraving of the moon, tree rings, citrus, pocket watches, rope, charts, a radiolarian, embroidery), are aligned so their circle sits in exactly the same place. The circle turns slowly across the cuts. The cuts speed up from 1.3 s to 0.17 s, and each one is a note of the brand hook on piano and harp, over strings that build.

Only three words appear: *Untangle* (over a knotted rope, then a neat coil), *how things*, *work.* The picture and music cut hard at 16 s. The circle comes back as a thin ring of light around "A digital atelier", then slides into the middle O of PORTOKO, and the wordmark grows out from it.

Rebuild:
```
cd film
python3 tools/fetch_patient.py $(python3 -c "import json;print(' '.join(s['id'] for s in json.load(open('shots.json'))))")   # needs candidates.jsonl
python3 tools/find_circles.py            # circles.json (committed)
python3 render_film.py                   # frames/*.jpg
python3 score.py score.wav               # needs the CC0 samples, see showreel/audio/fetch_samples.sh
ffmpeg -framerate 24 -i frames/%05d.jpg -i score.wav -c:v libx264 -b:v 10M -tune grain -pix_fmt yuv420p -c:a aac -b:a 256k -shortest ../PORTOKO_film.mp4
```


## Point of View (`pov/`)
Portoko untangles how a business works. The film shows that with one idea: a tangle that is really a flower, if you look from the right place.

Every thread of a line-drawn flower is pushed a random distance along the line of sight from one camera position (the *point of view*), plus some sideways noise. From anywhere else it's a 3D knot. As the camera orbits in, the sideways noise fades away. When the camera reaches that exact spot, the knot snaps into the drawing. Then the drawing flattens, is painted in watercolour, and blooms.

Everything is cut to the first 30 s of the music. `pov/src/timeline.js` holds the times measured from the track.

| Time | Music | Picture | Words |
|---|---|---|---|
| 0–6.97 s | Swell, hard stop | One glowing thread draws itself, then hundreds. Line-drawn fragments of a tangled business (spreadsheets, chat bubbles, a barcode, a receipt, a kanban board) are pulled into a growing knot | — |
| 6.97–8.05 s | Silence, five clicks | Black | *Look.*, one character per click |
| 8.05–12.9 s | Sparse hits, glitch tones | Each hit jump-cuts to a new angle on the knot, glitching. A viewfinder reads the camera angle | — |
| 12.9–22.9 s | Sub drone, build | One continuous orbit. The knot untangles and gains colour as the readout counts down to θ 0.0° φ 0.0° | — |
| 22.9–26.7 s | Swell peak, climax | Lock: the knot is a flower. It flattens, the watercolour floods in, and the petals cup and open, lit from the heart | *Untangled.* |
| 26.7–29.1 s | Stop, glitch burst, thump | The petals let go; a glitch burst tears open onto the wordmark | PORTOKO, then *A digital atelier* on the thump |
| 29.1–30 s | Silence | Everything holds | |

Rendered with three.js (lines, painted-petal shaders, bloom, and a final glitch/lens/grain pass) in headless Chromium.

Rebuild (the music is not in the repository; put the track at `pov/music/point.of.view.mp3`):
```
cd pov && npm install
node render.mjs frames 4                 # frames/00000.jpg ... 00899.jpg   (node render.mjs stills 22.9 = one frame)
ffmpeg -framerate 30 -i frames/%05d.jpg -t 30 -i music/point.of.view.mp3 -af "afade=t=out:st=29.9:d=0.1" -c:v libx264 -b:v 12M -maxrate 16M -bufsize 24M -preset slow -tune grain -pix_fmt yuv420p -c:a aac -b:a 256k -shortest -movflags +faststart ../PORTOKO_pov.mp4
```
