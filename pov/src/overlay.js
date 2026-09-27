// Everything typographic, drawn on a 2D canvas the final pass composites (so glitches tear it too).
import { T } from './timeline.js';
import { clamp, smooth, ramp, easeOut } from './util.js';

const W = 1920, H = 1080;
export const canvas = document.createElement('canvas'); canvas.width = W; canvas.height = H;
const x = canvas.getContext('2d');
const INK = '#f3f2ee', GREEN = '#3ae59a';
let WORD = null;

export async function loadOverlay() {
  WORD = new Image(); WORD.src = 'assets/wordmark.png'; await WORD.decode();
  await Promise.all(['200 72px Inter', '300 40px Inter', '400 16px Plex Mono'].map(f => document.fonts.load(f)));
  // the wordmark, filled with the site gradient once
  const w = 800, h = Math.round(w * WORD.height / WORD.width);
  const c = document.createElement('canvas'); c.width = w; c.height = h; const g = c.getContext('2d');
  const lg = g.createLinearGradient(0, 0, w, 0);
  [[0, '#f3f2ee'], [.42, '#c6f4dc'], [.68, '#6fe8b0'], [1, '#01da7d']].forEach(([o, col]) => lg.addColorStop(o, col));
  g.fillStyle = lg; g.fillRect(0, 0, w, h); g.globalCompositeOperation = 'destination-in'; g.drawImage(WORD, 0, 0, w, h);
  WORD.filled = c;
}

function text(s, px, y, { font = 'Inter', weight = 300, color = INK, alpha = 1, track = 0, align = 'center', xpos = W / 2 } = {}) {
  if (alpha <= 0) return;
  x.save(); x.globalAlpha = clamp(alpha); x.fillStyle = color; x.font = `${weight} ${px}px ${font}`;
  x.textAlign = align; x.textBaseline = 'middle'; x.letterSpacing = `${track}px`; x.fillText(s, xpos, y); x.restore();
}

// hud: {az, el, r, shot, align (0..1)} from the camera
export function drawOverlay(t, hud) {
  x.clearRect(0, 0, W, H);
  // "Look." one character per click
  if (t >= T.cut1 && t < T.hit0) {
    const n = T.clicks.filter(c => t >= c).length;
    text('Look.'.slice(0, n), 76, H / 2, { weight: 200, track: 1 });
  }
  // the camera readout: a nerd's viewfinder, counting down to the one true angle
  const hudA = t >= T.hit0 && t < T.flatten + 0.5 ? (1 - smooth(ramp(t, T.flatten, T.flatten + 0.5))) : 0;
  if (hudA > 0 && hud) {
    const locked = hud.align > 0.5;
    const col = locked ? GREEN : INK, a = hudA * (locked ? 0.95 : 0.55);
    const f = v => (v >= 0 ? ' ' : '−') + Math.abs(v).toFixed(1).padStart(5, '0');
    text(`POV ${String(hud.shot).padStart(2, '0')}`, 16, H - 92, { font: 'Plex Mono', weight: 400, color: col, alpha: a, align: 'left', xpos: 64, track: 2 });
    text(`θ${f(hud.az)}°   φ${f(hud.el)}°   r ${hud.r.toFixed(2)}`, 16, H - 64, { font: 'Plex Mono', weight: 400, color: col, alpha: a, align: 'left', xpos: 64, track: 1 });
    // centre crosshair; it closes in and turns green when the view locks
    const gap = 14 - 6 * hud.align, len = 12, cx = W / 2, cy = H / 2;
    x.save(); x.globalAlpha = hudA * (0.35 + 0.55 * hud.align); x.strokeStyle = locked ? GREEN : INK; x.lineWidth = 1.25;
    x.beginPath();
    x.moveTo(cx - gap - len, cy); x.lineTo(cx - gap, cy); x.moveTo(cx + gap, cy); x.lineTo(cx + gap + len, cy);
    x.moveTo(cx, cy - gap - len); x.lineTo(cx, cy - gap); x.moveTo(cx, cy + gap); x.lineTo(cx, cy + gap + len);
    x.stroke(); x.restore();
  }
  // "Untangled."
  const ua = smooth(ramp(t, T.align + 0.45, T.align + 0.95)) * (1 - smooth(ramp(t, 25.3, 25.8)));
  if (ua > 0) text('Untangled.', 40, H * 0.915, { weight: 300, alpha: ua, track: 0.5 });
  // the wordmark, then the line
  if (t >= T.burst2) {
    const w = WORD.filled, s = 1 + 0.012 * (1 - easeOut(ramp(t, T.burst2, T.burst2 + 1.2)));
    const ww = w.width * s, hh = w.height * s;
    x.drawImage(w, W / 2 - ww / 2, H * 0.46 - hh / 2, ww, hh);
    const la = ramp(t, T.thump, T.thump + 0.18);
    if (la > 0) text('A digital atelier', 30, H * 0.46 + hh / 2 + 62, { weight: 300, color: '#cfceca', alpha: la, track: 1.5 + 2 * (1 - easeOut(ramp(t, T.thump, T.thump + 1.2))) });
  }
  return canvas;
}
