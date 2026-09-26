# PORTOKO — brand film

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
