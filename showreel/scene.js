'use strict';
/* PORTOKO — 20s motion showreel.
 * Everything is a pure function of time t (seconds), so any frame can be
 * rendered in any order (the capture script renders in parallel).
 *
 *  0.0 – 2.0   01 IGNITION     dot matrix, beat ripples, implosion
 *  2.0 – 5.0   02 BIG BANG     burst, shockwaves, MOTION -> EMOTION, zoom through the O
 *  5.0 – 8.0   03 KINETIC TYPE word-per-beat typography in a tunnel, O-portal out
 *  8.0 – 11.5  04 ORBIT        accretion disk / black hole (reference image)
 * 11.5 – 14.0  05 FLOW         curl-noise ink that condenses into the wordmark
 * 14.0 – 17.5  06 IDENTITY     logo hit, orbiting O's, light sweeps
 * 17.5 – 20.0  07 END CARD     brand colours on white
 */

const W = 1920, H = 1080, FPS = 60, DUR = 20;
const TAU = Math.PI * 2;

// ---------------------------------------------------------------- utilities
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const lerp = (a, b, t) => a + (b - a) * t;
const prog = (t, a, b) => clamp((t - a) / (b - a));
const E = {
  outExpo: x => (x >= 1 ? 1 : 1 - Math.pow(2, -10 * x)),
  inExpo: x => (x <= 0 ? 0 : Math.pow(2, 10 * x - 10)),
  inOutExpo: x => x <= 0 ? 0 : x >= 1 ? 1 : x < 0.5 ? Math.pow(2, 20 * x - 10) / 2 : (2 - Math.pow(2, -20 * x + 10)) / 2,
  outCubic: x => 1 - Math.pow(1 - x, 3),
  inCubic: x => x * x * x,
  inOutCubic: x => (x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2),
  outQuart: x => 1 - Math.pow(1 - x, 4),
  outBack: (x, s = 1.9) => 1 + (s + 1) * Math.pow(x - 1, 3) + s * Math.pow(x - 1, 2),
  outBounce: x => {
    const n = 7.5625, d = 2.75;
    if (x < 1 / d) return n * x * x;
    if (x < 2 / d) return n * (x -= 1.5 / d) * x + 0.75;
    if (x < 2.5 / d) return n * (x -= 2.25 / d) * x + 0.9375;
    return n * (x -= 2.625 / d) * x + 0.984375;
  },
};
// damped spring, x in seconds since trigger
const spring = (x, freq = 3.2, damp = 7) => (x <= 0 ? 0 : 1 - Math.exp(-damp * x) * Math.cos(freq * TAU * x));
// exponential decay envelope for impacts
const imp = (t, t0, d) => (t < t0 ? 0 : Math.exp(-(t - t0) / d));

function rng(seed) {
  return function () {
    seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
function hash(n) {
  n = Math.imul(n ^ (n >>> 16), 0x45d9f3b);
  n = Math.imul(n ^ (n >>> 16), 0x45d9f3b);
  return (n ^ (n >>> 16)) >>> 0;
}

// Improved Perlin noise (3D)
const PERM = new Uint8Array(512);
{
  const r = rng(7), p = [...Array(256).keys()];
  for (let i = 255; i > 0; i--) { const j = Math.floor(r() * (i + 1)); [p[i], p[j]] = [p[j], p[i]]; }
  for (let i = 0; i < 512; i++) PERM[i] = p[i & 255];
}
function grad3(h, x, y, z) {
  h &= 15;
  const u = h < 8 ? x : y, v = h < 4 ? y : h === 12 || h === 14 ? x : z;
  return ((h & 1) ? -u : u) + ((h & 2) ? -v : v);
}
function noise3(x, y, z) {
  const X = Math.floor(x) & 255, Y = Math.floor(y) & 255, Z = Math.floor(z) & 255;
  x -= Math.floor(x); y -= Math.floor(y); z -= Math.floor(z);
  const u = x * x * x * (x * (x * 6 - 15) + 10), v = y * y * y * (y * (y * 6 - 15) + 10), w = z * z * z * (z * (z * 6 - 15) + 10);
  const A = PERM[X] + Y, AA = PERM[A] + Z, AB = PERM[A + 1] + Z, B = PERM[X + 1] + Y, BA = PERM[B] + Z, BB = PERM[B + 1] + Z;
  return lerp(
    lerp(lerp(grad3(PERM[AA], x, y, z), grad3(PERM[BA], x - 1, y, z), u), lerp(grad3(PERM[AB], x, y - 1, z), grad3(PERM[BB], x - 1, y - 1, z), u), v),
    lerp(lerp(grad3(PERM[AA + 1], x, y, z - 1), grad3(PERM[BA + 1], x - 1, y, z - 1), u), lerp(grad3(PERM[AB + 1], x, y - 1, z - 1), grad3(PERM[BB + 1], x - 1, y - 1, z - 1), u), v),
    w);
}

// ---------------------------------------------------------------- palette
const COL = {
  white: [236, 246, 255], mint: [125, 255, 196], lime: [25, 240, 138], green: [10, 168, 90],
  teal: [25, 211, 197], blue: [47, 123, 255], violet: [139, 92, 255], hot: [255, 250, 215],
};
const PAL = [COL.lime, COL.mint, COL.teal, COL.blue, COL.violet, COL.green, COL.white, COL.lime, COL.teal];
const rgba = (c, a) => `rgba(${c[0] | 0},${c[1] | 0},${c[2] | 0},${a})`;
const mixc = (a, b, t) => [lerp(a[0], b[0], t), lerp(a[1], b[1], t), lerp(a[2], b[2], t)];
const DISK_STOPS = [[0, COL.hot], [0.1, [200, 255, 175]], [0.28, COL.lime], [0.48, COL.teal], [0.7, COL.blue], [1, COL.violet]];
function ramp(stops, f) {
  f = clamp(f);
  for (let i = 1; i < stops.length; i++) {
    if (f <= stops[i][0]) return mixc(stops[i - 1][1], stops[i][1], (f - stops[i - 1][0]) / (stops[i][0] - stops[i - 1][0]));
  }
  return stops[stops.length - 1][1];
}

// ---------------------------------------------------------------- canvases
const cvs = document.getElementById('c');
const ctx = cvs.getContext('2d');
function mk(w, h) { const c = document.createElement('canvas'); c.width = w; c.height = h; return c; }
const layer = mk(W, H), lg = layer.getContext('2d');
const logoLayer = mk(W, H), llg = logoLayer.getContext('2d');
const tmp = mk(W, H), tg = tmp.getContext('2d');
const chan = mk(W, H), cg = chan.getContext('2d');
const b1 = mk(W / 4, H / 4), b1g = b1.getContext('2d');
const b2 = mk(W / 12, H / 12), b2g = b2.getContext('2d');

function setFont(g, fam, wt, px) { g.font = `${wt} ${px}px "${fam}"`; }
// per-character layout (display type, caps only, so no kerning needed)
function layout(g, str, ls = 0) {
  const chars = []; let x = 0;
  for (const ch of str) { const w = g.measureText(ch).width; chars.push({ ch, x, w }); x += w + ls; }
  return { chars, width: x - ls };
}
const GLY = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789#%&*+/<>=';
function scramble(str, p, t, seed = 0) {
  let o = ''; const n = str.length;
  for (let i = 0; i < n; i++) {
    const c = str[i];
    const th = (i / n) * 0.75;
    if (c === ' ' || c === '·' || c === '—') { o += p > th ? c : ' '; continue; }
    if (p >= th + 0.25) o += c;
    else if (p > th) o += GLY[hash(i * 131 + Math.floor(t * 30) * 7 + seed) % GLY.length];
    else o += ' ';
  }
  return o;
}

// ---------------------------------------------------------------- assets
let NEBULA, GRAIN = [], LOGO_IMG, STARS = [];

function buildNebula() {
  const c = mk(2400, 1400), g = c.getContext('2d'), r = rng(2026);
  g.fillStyle = '#000'; g.fillRect(0, 0, c.width, c.height);
  g.globalCompositeOperation = 'lighter';
  const cols = [COL.green, COL.teal, COL.blue, COL.violet, COL.lime, COL.blue];
  // diagonal band like the reference: bottom-left -> top-right
  const band = () => { const u = r(); return [u * 2400, 1250 - u * 1000 + (r() - 0.5) * 700]; };
  for (let i = 0; i < 90; i++) {
    const [x, y] = band(), rad = 120 + r() * 480, c0 = cols[Math.floor(r() * cols.length)];
    const gr = g.createRadialGradient(x, y, 0, x, y, rad);
    gr.addColorStop(0, rgba(c0, 0.03 + r() * 0.06)); gr.addColorStop(1, rgba(c0, 0));
    g.fillStyle = gr; g.fillRect(x - rad, y - rad, rad * 2, rad * 2);
  }
  // ink splatter
  for (let i = 0; i < 1400; i++) {
    const [x, y] = band(), rad = Math.pow(r(), 4) * 14 + 0.6, c0 = cols[Math.floor(r() * cols.length)];
    g.fillStyle = rgba(c0, 0.08 + r() * 0.3);
    g.beginPath(); g.arc(x + (r() - 0.5) * 300, y + (r() - 0.5) * 300, rad, 0, TAU); g.fill();
  }
  const out = mk(2400, 1400), og = out.getContext('2d');
  og.filter = 'blur(2px)'; og.drawImage(c, 0, 0); og.filter = 'none';
  og.globalCompositeOperation = 'lighter'; og.globalAlpha = 0.5; og.drawImage(c, 0, 0);
  return out;
}
function buildGrain() {
  for (let k = 0; k < 4; k++) {
    const c = mk(256, 256), g = c.getContext('2d'), id = g.createImageData(256, 256), r = rng(900 + k);
    for (let i = 0; i < id.data.length; i += 4) { const v = (r() * 255) | 0; id.data[i] = id.data[i + 1] = id.data[i + 2] = v; id.data[i + 3] = 255; }
    g.putImageData(id, 0, 0); GRAIN.push(c);
  }
}
function buildStars() {
  const r = rng(77);
  for (let i = 0; i < 520; i++) STARS.push({ x: r() * W, y: r() * H, z: 0.2 + r() * 0.8, s: 0.4 + Math.pow(r(), 4) * 2.2, tw: r() * TAU });
}
function drawStars(g, t, alpha, drift = 0, cx = W / 2, cy = H / 2, zoom = 1) {
  g.globalCompositeOperation = 'lighter';
  for (const s of STARS) {
    let x = ((s.x + drift * s.z * t) % W + W) % W, y = s.y;
    x = cx + (x - W / 2) * zoom * (1 + (s.z - 0.5) * (zoom - 1) * 0.2); y = cy + (y - H / 2) * zoom;
    const a = alpha * s.z * (0.6 + 0.4 * Math.sin(t * 3 + s.tw));
    g.fillStyle = rgba(COL.white, a);
    g.fillRect(x, y, s.s, s.s);
  }
  g.globalCompositeOperation = 'source-over';
}
function drawNebula(g, alpha, cx, cy, scale, rot) {
  if (alpha <= 0) return;
  g.save(); g.globalAlpha = alpha; g.globalCompositeOperation = 'lighter';
  g.translate(cx, cy); g.rotate(rot); g.scale(scale, scale);
  g.drawImage(NEBULA, -1200, -700);
  g.restore();
}

// ---------------------------------------------------------------- logo geometry
// Traced from the supplied wordmark (2000x440 image units). Strokes are centre-lines
// of a 43u monoline; the whole mark is clipped to the cap band y∈[76,332].
const LOGO = (() => {
  const arc = (cx, cy, r, a0, a1, n) => { const o = []; for (let i = 0; i <= n; i++) { const a = a0 + (a1 - a0) * (i / n); o.push([cx + r * Math.cos(a), cy + r * Math.sin(a)]); } return o; };
  const H2 = Math.PI / 2;
  const P = [[44, 97.5], [175.5, 97.5], ...arc(175.5, 142.5, 45, -H2, 0, 14).slice(1), [220.5, 160], ...arc(175.5, 160, 45, 0, H2, 14).slice(1), [65.5, 205], [65.5, 350]];
  const O = cx => arc(cx, 204, 106.5, -H2, 3 * H2 + 0.02, 120);
  const R = [[641.5, 350], [641.5, 97.5], [746, 97.5], ...arc(746, 142.5, 45, -H2, 0, 14).slice(1), [791, 162], ...arc(746, 162, 45, 0, H2, 14).slice(1), [641.5, 207]];
  const Rleg = [[723.4, 200], [804, 350]];
  const Tbar = [[862, 97.5], [1075, 97.5]], Tstem = [[968.5, 97.5], [968.5, 350]];
  const Kstem = [[1459.5, 60], [1459.5, 350]], Karms = [[1622, 61], [1500, 200], [1622, 347]];
  const letters = [[P], [O(427.5)], [R, Rleg], [Tbar, Tstem], [O(1247.5)], [Kstem, Karms], [O(1828.5)]];
  const paths = [];
  letters.forEach((strokes, li) => strokes.forEach(pts => {
    const p = new Path2D(); p.moveTo(pts[0][0], pts[0][1]);
    let len = 0; const cum = [0];
    for (let i = 1; i < pts.length; i++) { p.lineTo(pts[i][0], pts[i][1]); len += Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]); cum.push(len); }
    paths.push({ li, pts, p, len, cum });
  }));
  // uniform random samples on the filled glyph area
  function samples(n, seed) {
    const r = rng(seed), out = [], total = paths.reduce((a, p) => a + p.len, 0);
    while (out.length < n) {
      let d = r() * total, k = 0;
      while (d > paths[k].len) { d -= paths[k].len; k++; }
      const pa = paths[k]; let i = 1; while (pa.cum[i] < d) i++;
      const a = pa.pts[i - 1], b = pa.pts[i], f = (d - pa.cum[i - 1]) / (pa.cum[i] - pa.cum[i - 1] || 1);
      const dx = b[0] - a[0], dy = b[1] - a[1], l = Math.hypot(dx, dy) || 1, o = (r() - 0.5) * 40;
      const x = a[0] + dx * f - (dy / l) * o, y = a[1] + dy * f + (dx / l) * o;
      if (y < 78 || y > 330) continue;
      out.push([x, y, pa.li]);
    }
    return out;
  }
  return { paths, samples, O: [427.5, 1247.5, 1828.5], cx: 1000, cy: 204, SW: 43 };
})();
// PNG letter columns (image px) for the end card
const LOGO_COLS = [[44, 242], [300, 555], [620, 818], [862, 1075], [1120, 1375], [1439, 1637], [1701, 1956]];

function logoXform(t) {
  const s = 0.78 * (1 + 0.045 * E.inOutCubic(prog(t, 14, 17.4)));
  return { cx: W / 2, cy: H / 2 - 24, s };
}
const L2S = (X, x, y) => [X.cx + (x - LOGO.cx) * X.s, X.cy + (y - LOGO.cy) * X.s];

function logoGradient(g, mode) {
  const gr = g.createLinearGradient(44, 76, 1956, 332);
  if (mode === 'brand') {
    gr.addColorStop(0, '#191b25'); gr.addColorStop(0.45, '#114435'); gr.addColorStop(0.75, '#0b7646'); gr.addColorStop(1, '#05a858');
  } else {
    gr.addColorStop(0, '#f2f8ff'); gr.addColorStop(0.35, '#c9fbe6'); gr.addColorStop(0.7, '#3cf0a0'); gr.addColorStop(1, '#0fcf74');
  }
  return gr;
}
// draw the vector logo in logo space; prog(li) -> 0..1 stroke reveal
function strokeLogo(g, X, style, progFn, lw = LOGO.SW) {
  g.save();
  g.translate(X.cx, X.cy); g.scale(X.s, X.s); g.translate(-LOGO.cx, -LOGO.cy);
  g.beginPath(); g.rect(-100, 76, 2300, 256); g.clip();
  g.lineWidth = lw; g.lineCap = 'butt'; g.lineJoin = 'miter'; g.miterLimit = 4;
  g.strokeStyle = style === 'grad' ? logoGradient(g, 'light') : style;
  for (const pa of LOGO.paths) {
    const p = progFn(pa.li);
    if (p <= 0) continue;
    if (p < 1) g.setLineDash([pa.len * p, pa.len + 100]); else g.setLineDash([]);
    g.stroke(pa.p);
  }
  g.setLineDash([]);
  g.restore();
}

// ---------------------------------------------------------------- precomputed systems
let BURST, RIBBONS, BH, FLOW, SPARKS, DOTS;

function buildBurst() {
  const r = rng(11), parts = [];
  for (let i = 0; i < 2200; i++) {
    const u = r() * 2 - 1, th = r() * TAU, s = Math.sqrt(1 - u * u);
    const flat = 0.45 + r() * 0.55; // squash toward a disk for a more designed silhouette
    parts.push({
      d: [s * Math.cos(th), u * flat, s * Math.sin(th)], v: 300 + Math.pow(r(), 1.6) * 2600, k: 1.4 + r() * 2.4,
      c: PAL[Math.floor(r() * PAL.length)], w: 0.6 + Math.pow(r(), 3) * 3.2, life: 1.1 + r() * 2.2, sw: (r() - 0.5) * 1.2,
    });
  }
  const rib = [];
  for (let i = 0; i < 46; i++) {
    let n = [r() - 0.5, r() * 0.6 + 0.7, r() - 0.5]; const l = Math.hypot(...n); n = n.map(v => v / l);
    const a = Math.abs(n[0]) < 0.9 ? [1, 0, 0] : [0, 1, 0];
    let u = [n[1] * a[2] - n[2] * a[1], n[2] * a[0] - n[0] * a[2], n[0] * a[1] - n[1] * a[0]]; const ul = Math.hypot(...u); u = u.map(v => v / ul);
    const v = [n[1] * u[2] - n[2] * u[1], n[2] * u[0] - n[0] * u[2], n[0] * u[1] - n[1] * u[0]];
    rib.push({ u, v, R: 250 + r() * 1300, k: 1.2 + r() * 1.8, a0: r() * TAU, span: 0.35 + r() * 1.5, om: (0.3 + r() * 1.1) * (r() < 0.5 ? -1 : 1), w: 0.8 + r() * 3, c: PAL[Math.floor(r() * PAL.length)], del: r() * 0.25 });
  }
  BURST = parts; RIBBONS = rib;
}

function buildDots() {
  const d = [], sp = 40;
  for (let y = sp / 2 + 20; y < H; y += sp) for (let x = sp / 2; x < W; x += sp) d.push([x, y, Math.hypot(x - W / 2, y - H / 2)]);
  DOTS = d;
}

function buildBlackHole() {
  const r = rng(404), rings = [], dust = [], shards = [];
  for (let i = 0; i < 64; i++) {
    const f = i / 63, R = 245 + Math.pow(f, 1.3) * 860, arcs = [], na = 1 + Math.floor(r() * 3);
    if (f < 0.3) arcs.push({ a0: r() * TAU, span: TAU * (0.75 + r() * 0.25) });
    else for (let k = 0; k < na; k++) arcs.push({ a0: r() * TAU, span: 0.5 + r() * 2.7 });
    rings.push({ R, f, arcs, w: (0.5 + r() * 2.4) * (1 - f * 0.4) * (f < 0.3 ? 1.8 : 1), om: 1.25 * Math.pow(245 / R, 1.5), h: (r() - 0.5) * 10, c: ramp(DISK_STOPS, f + (r() - 0.5) * 0.12), b: 0.5 + r() * 0.5 });
  }
  for (let i = 0; i < 2600; i++) {
    const f = Math.pow(r(), 0.85), R = 235 + f * 1000 + (r() - 0.5) * 30;
    dust.push({ R, f, a: r() * TAU, om: 1.25 * Math.pow(245 / R, 1.5), h: (r() - 0.5) * 26 * f, s: 0.7 + Math.pow(r(), 3) * 2.4, c: ramp(DISK_STOPS, f + (r() - 0.5) * 0.3), b: 0.25 + r() * 0.75 });
  }
  for (let i = 0; i < 16; i++) {
    const R = 360 + r() * 900;
    shards.push({ R, a: r() * TAU, om: 1.25 * Math.pow(245 / R, 1.5), h: (r() - 0.5) * 220, sz: 40 + r() * 120, asp: 0.25 + r() * 0.6, rx: r() * TAU, ry: r() * TAU, sp: (r() - 0.5) * 2.2 });
  }
  BH = { rings, dust, shards };
}

// curl-noise ink, integrated once
const FLOW_T0 = 11.3, FLOW_T1 = 14.35, FLOW_N = 2600;
function buildFlow() {
  const r = rng(99), steps = Math.ceil((FLOW_T1 - FLOW_T0) * FPS) + 1;
  const psi = (x, y, tm) => 430 * noise3(x / 560, y / 560, tm * 0.22) + 150 * noise3(x / 230 + 40, y / 230, tm * 0.4 + 9);
  const pos = new Float32Array(FLOW_N * steps * 2), parts = [];
  const targets = LOGO.samples(FLOW_N, 5);
  for (let i = 0; i < FLOW_N; i++) {
    const u = r();
    let x = -250 + u * (W + 500), y = H * 0.95 - u * H * 0.8 + (r() - 0.5) * 900;
    const sp = 0.8 + r() * 0.5;
    for (let s = 0; s < steps; s++) {
      const tm = s / FPS, e = 1.2;
      let vx = (psi(x, y + e, tm) - psi(x, y - e, tm)) / (2 * e);
      let vy = -(psi(x + e, y, tm) - psi(x - e, y, tm)) / (2 * e);
      const dx = x - W / 2, dy = y - H / 2, d = Math.hypot(dx, dy) + 1, sw = 1.1 * Math.exp(-d / 900);
      vx = vx * 330 * sp - (dy / d) * sw * 260; vy = vy * 330 * sp + (dx / d) * sw * 260;
      x += vx / FPS; y += vy / FPS;
      pos[(i * steps + s) * 2] = x; pos[(i * steps + s) * 2 + 1] = y;
    }
    const tg = targets[i];
    parts.push({ c: PAL[Math.floor(r() * PAL.length)], w: 0.7 + Math.pow(r(), 3) * 2.4, a: 0.25 + r() * 0.35, del: Math.pow(r(), 1.3) * 0.5, tx: tg[0], ty: tg[1], li: tg[2], fat: r() < 0.04 });
  }
  FLOW = { pos, parts, steps };
  // sparks thrown off the logo at the 14.0 hit
  const r2 = rng(314), sp = [], st = LOGO.samples(320, 8);
  for (const [x, y] of st) {
    const a = Math.atan2(y - LOGO.cy, x - LOGO.cx) + (r2() - 0.5) * 1.6, v = 200 + r2() * 1300;
    sp.push({ x, y, vx: Math.cos(a) * v, vy: Math.sin(a) * v * 0.6 - 150, k: 2 + r2() * 3, life: 0.5 + r2() * 1.1, c: r2() < 0.5 ? COL.mint : COL.white, w: 0.8 + r2() * 1.8 });
  }
  SPARKS = sp;
}

// ---------------------------------------------------------------- section 01: ignition
function S1(g, t) {
  const cx = W / 2, cy = H / 2;
  const implode = E.inExpo(prog(t, 1.15, 1.93));
  // dot matrix
  g.globalCompositeOperation = 'lighter';
  const beats = [0, 0.5, 1.0, 1.5];
  for (const [x, y, d] of DOTS) {
    const appear = E.outCubic(prog(t, 0.05 + d / 2600, 0.45 + d / 2600));
    if (appear <= 0) continue;
    let rip = 0;
    for (const b of beats) { if (t < b) continue; const front = (t - b) * 1500; rip += Math.exp(-Math.pow((d - front) / 60, 2)) * Math.exp(-(t - b) * 1.2); }
    const k = 1 - implode;
    const px = cx + (x - cx) * k, py = cy + (y - cy) * k;
    const a = appear * (0.16 + rip * 0.9) * (1 - implode * 0.3);
    const s = 1.6 + rip * 2.4;
    const c = mixc(COL.white, COL.lime, clamp(rip));
    g.fillStyle = rgba(c, a);
    if (implode > 0.02) {
      const k2 = 1 - E.inExpo(prog(t - 0.03, 1.15, 1.93));
      g.strokeStyle = rgba(c, a); g.lineWidth = s;
      g.beginPath(); g.moveTo(cx + (x - cx) * k2, cy + (y - cy) * k2); g.lineTo(px, py); g.stroke();
    } else g.fillRect(px - s / 2, py - s / 2, s, s);
  }
  // cross hairlines
  const hl = E.outExpo(prog(t, 0.12, 0.95)) * (1 - E.inExpo(prog(t, 1.35, 1.9)));
  if (hl > 0) {
    const grd = g.createLinearGradient(cx - W / 2, 0, cx + W / 2, 0);
    grd.addColorStop(0, rgba(COL.white, 0)); grd.addColorStop(0.5, rgba(COL.white, 0.7)); grd.addColorStop(1, rgba(COL.white, 0));
    g.fillStyle = grd; g.fillRect(cx - (W / 2) * hl, cy - 0.5, W * hl, 1);
    const grv = g.createLinearGradient(0, cy - H / 2, 0, cy + H / 2);
    grv.addColorStop(0, rgba(COL.white, 0)); grv.addColorStop(0.5, rgba(COL.white, 0.5)); grv.addColorStop(1, rgba(COL.white, 0));
    g.fillStyle = grv; g.fillRect(cx - 0.5, cy - (H / 2) * hl, 1, H * hl);
    // ruler ticks
    for (let i = -24; i <= 24; i++) {
      const x = cx + i * 40; if (Math.abs(i * 40) > (W / 2) * hl) continue;
      const big = i % 4 === 0; g.fillStyle = rgba(COL.white, big ? 0.55 : 0.25);
      g.fillRect(x - 0.5, cy - (big ? 9 : 4), 1, big ? 18 : 8);
    }
  }
  // contracting rings
  for (let k = 0; k < 7; k++) {
    const p = prog(t, 0.95 + k * 0.1, 1.9);
    if (p <= 0 || p >= 1) continue;
    const R = lerp(1100 - k * 90, 4, E.inCubic(p));
    g.strokeStyle = rgba(k % 2 ? COL.lime : COL.white, 0.5 * Math.sin(p * Math.PI)); g.lineWidth = 1 + k * 0.3;
    g.beginPath(); g.arc(cx, cy, R, 0, TAU); g.stroke();
  }
  // core
  let pulse = 0; for (const b of beats) pulse += imp(t, b, 0.12);
  const core = 5 + E.outCubic(prog(t, 0, 1.9)) * 14 + pulse * 10 + implode * 60;
  const cg2 = g.createRadialGradient(cx, cy, 0, cx, cy, core * 6);
  cg2.addColorStop(0, rgba(COL.white, 1)); cg2.addColorStop(0.08, rgba(COL.mint, 0.9)); cg2.addColorStop(0.3, rgba(COL.lime, 0.25)); cg2.addColorStop(1, rgba(COL.green, 0));
  g.fillStyle = cg2; g.fillRect(cx - core * 6, cy - core * 6, core * 12, core * 12);
  g.globalCompositeOperation = 'source-over';
  // type
  const ta = prog(t, 0.25, 0.4) * (1 - prog(t, 1.35, 1.6));
  if (ta > 0) {
    g.textAlign = 'center'; g.textBaseline = 'middle';
    setFont(g, 'Space Grotesk', 300, 46); g.letterSpacing = '38px';
    g.fillStyle = rgba(COL.white, 0.95 * ta);
    g.fillText(scramble('PORTOKO', prog(t, 0.3, 1.0), t, 1), cx + 19, cy - 120);
    setFont(g, 'JetBrains Mono', 400, 17); g.letterSpacing = '9px';
    g.fillStyle = rgba(COL.mint, 0.75 * ta);
    g.fillText(scramble('A MOTION DESIGN SHOWREEL', prog(t, 0.55, 1.2), t, 2), cx + 4, cy + 118);
    g.letterSpacing = '0px';
  }
  // collapse flash
  const fl = E.inExpo(prog(t, 1.8, 2.0));
  if (fl > 0) {
    const R = 30 + fl * 1400;
    const fg = g.createRadialGradient(cx, cy, 0, cx, cy, R);
    fg.addColorStop(0, rgba([255, 255, 255], fl)); fg.addColorStop(0.5, rgba(COL.mint, fl * 0.6)); fg.addColorStop(1, rgba(COL.green, 0));
    g.globalCompositeOperation = 'lighter'; g.fillStyle = fg; g.fillRect(0, 0, W, H); g.globalCompositeOperation = 'source-over';
  }
}

// ---------------------------------------------------------------- section 02: big bang + MOTION -> EMOTION
function S2(g, t) {
  const tau = t - 2.0, cx = W / 2, cy = H / 2;
  if (tau < 0) return;
  // zoom through the "O" at the end
  const zp = E.inExpo(prog(t, 4.45, 5.0));
  const word = { size: 230 };
  setFont(g, 'Unbounded', 800, word.size); g.letterSpacing = '0px';
  const Lm = layout(g, 'MOTION', 0), eW = g.measureText('E').width;
  const eIn = E.outExpo(prog(t, 4.0, 4.28));
  const mLeft = cx - Lm.width / 2 + (eW / 2) * eIn;
  const oChar = Lm.chars[1];
  const ox = mLeft + oChar.x + oChar.w / 2, oy = cy + 4;
  const Z = Math.exp(zp * Math.log(46));

  g.save();
  if (zp > 0) { g.translate(ox, oy); g.scale(Z, Z); g.translate(-ox, -oy); }
  const bgFade = 1 - prog(t, 4.6, 4.9);

  // nebula + stars
  drawNebula(g, 0.38 * E.outCubic(prog(tau, 0, 1.2)) * bgFade, cx, cy, 0.9 + tau * 0.05, -0.1 + tau * 0.02);
  drawStars(g, t, 0.8 * prog(tau, 0, 0.6) * bgFade, -20);

  g.globalCompositeOperation = 'lighter';
  // shockwaves
  const waves = [[0, 0.3, 1600, 26], [0.06, 0.25, 1200, 14], [0.18, 0.18, 2000, 6], [2.0, 0.22, 900, 10]];
  for (const [d, ry, Rm, lw] of waves) {
    const p = prog(tau, d, d + 1.5); if (p <= 0 || p >= 1) continue;
    const R = Rm * E.outExpo(p), a = Math.pow(1 - p, 1.6);
    g.save(); g.translate(cx, cy); g.rotate(-0.18);
    g.strokeStyle = rgba(d === 0.06 ? COL.teal : COL.mint, a * 0.9); g.lineWidth = lw * (1 - p) + 1;
    g.beginPath(); g.ellipse(0, 0, R, R * ry, 0, 0, TAU); g.stroke();
    g.strokeStyle = rgba(COL.white, a * 0.5); g.lineWidth = 1;
    g.beginPath(); g.ellipse(0, 0, R * 0.985, R * ry * 0.985, 0, 0, TAU); g.stroke();
    g.restore();
  }
  // circular wave
  {
    const p = prog(tau, 0, 1.1);
    if (p < 1) { const R = 1400 * E.outExpo(p); g.strokeStyle = rgba(COL.white, 0.6 * (1 - p)); g.lineWidth = 3 * (1 - p) + 0.5; g.beginPath(); g.arc(cx, cy, R, 0, TAU); g.stroke(); }
  }
  // 3D ribbons
  const F = 1500, camZ = -tau * 120;
  const proj = (x, y, z) => { const zz = z - camZ + F; const s = F / Math.max(zz, 60); return [cx + x * s, cy + y * s, s]; };
  for (const rb of RIBBONS) {
    const tt = tau - rb.del; if (tt <= 0) continue;
    const R = rb.R * (1 - Math.exp(-rb.k * tt)), fade = clamp(tt * 4) * (1 - prog(tau, 1.6, 2.7));
    if (fade <= 0) continue;
    const n = 36, a0 = rb.a0 + rb.om * tt;
    let prev = null;
    for (let j = 0; j <= n; j++) {
      const a = a0 + (rb.span * j) / n, ca = Math.cos(a), sa = Math.sin(a);
      const p3 = [R * (rb.u[0] * ca + rb.v[0] * sa), R * (rb.u[1] * ca + rb.v[1] * sa), R * (rb.u[2] * ca + rb.v[2] * sa)];
      const q = proj(p3[0], p3[1] * 0.55, p3[2]);
      if (prev) {
        const taper = Math.sin((Math.PI * j) / n);
        g.strokeStyle = rgba(rb.c, 0.75 * taper * fade); g.lineWidth = rb.w * q[2] * taper + 0.3;
        g.beginPath(); g.moveTo(prev[0], prev[1]); g.lineTo(q[0], q[1]); g.stroke();
      }
      prev = q;
    }
  }
  // particles
  for (const p of BURST) {
    if (tau > p.life) continue;
    const life = 1 - tau / p.life, a = Math.pow(life, 1.4) * clamp(tau * 30);
    const pos = tt => { const d = (p.v * (1 - Math.exp(-p.k * tt))) / p.k, sw = p.sw * tt; const c = Math.cos(sw), s = Math.sin(sw); const x = p.d[0] * d, z = p.d[2] * d; return proj(x * c - z * s, p.d[1] * d, x * s + z * c); };
    const q1 = pos(tau), q0 = pos(Math.max(0, tau - 0.04));
    g.strokeStyle = rgba(p.c, a); g.lineWidth = p.w * q1[2];
    g.beginPath(); g.moveTo(q0[0], q0[1]); g.lineTo(q1[0] + 0.3, q1[1]); g.stroke();
  }
  // bang flash
  const fl = imp(t, 2.0, 0.18);
  if (fl > 0.01) {
    const fg = g.createRadialGradient(cx, cy, 0, cx, cy, 900);
    fg.addColorStop(0, rgba([255, 255, 255], fl)); fg.addColorStop(0.3, rgba(COL.mint, fl * 0.5)); fg.addColorStop(1, rgba(COL.green, 0));
    g.fillStyle = fg; g.fillRect(0, 0, W, H);
  }
  anamorphic(g, cx, cy, imp(t, 2.0, 0.5), COL.teal);
  g.globalCompositeOperation = 'source-over';

  // ---- type
  if (t >= 2.45) {
    g.textBaseline = 'alphabetic'; g.textAlign = 'left';
    setFont(g, 'Unbounded', 800, word.size);
    const base = cy + word.size * 0.36, top = cy - word.size * 0.46, bot = cy + word.size * 0.42;
    // echo outlines, pulsing on the beat
    const echo = E.outExpo(prog(t, 2.9, 3.6));
    let beat = 0; for (let b = 3; b < 4.5; b += 0.5) beat += imp(t, b, 0.15);
    if (echo > 0) {
      for (let k = 6; k >= 1; k--) {
        const s = 1 + k * (0.055 + beat * 0.012) * echo;
        g.save(); g.translate(cx + (eW / 2) * eIn * 0, cy); g.scale(s, s); g.translate(-cx, -cy);
        g.strokeStyle = rgba(k % 2 ? COL.lime : COL.teal, (0.34 - k * 0.045) * echo * (1 - zp)); g.lineWidth = 1.5 / s;
        Lm.chars.forEach(c => g.strokeText(c.ch, mLeft + c.x, base));
        g.restore();
      }
    }
    g.save();
    g.beginPath(); g.rect(0, top, W, bot - top); g.clip();
    Lm.chars.forEach((c, i) => {
      const p = E.outExpo(prog(t, 2.5 + i * 0.045, 2.5 + i * 0.045 + 0.7));
      const dy = (1 - p) * word.size * 1.05;
      g.fillStyle = '#f4fbff';
      g.fillText(c.ch, mLeft + c.x, base + dy);
    });
    g.restore();
    // the E slams in
    if (t >= 3.9) {
      const pe = E.outExpo(prog(t, 3.9, 4.02));
      const ex = lerp(-eW - 200, mLeft - eW, pe);
      const smear = (1 - pe);
      g.fillStyle = rgba(COL.lime, 1);
      if (smear > 0.02) for (let k = 1; k <= 5; k++) { g.globalAlpha = 0.12; g.fillText('E', ex - k * 60 * smear, base); }
      g.globalAlpha = 1;
      g.fillText('E', ex, base);
      const hit = imp(t, 4.0, 0.1);
      if (hit > 0.01) { g.globalCompositeOperation = 'lighter'; g.fillStyle = rgba(COL.white, hit); g.fillText('E', ex, base); g.globalCompositeOperation = 'source-over'; }
    }
    // underline sweep + caption
    const ul = E.outExpo(prog(t, 3.1, 3.8)) * (1 - zp);
    if (ul > 0) {
      const totalW = Lm.width + eW * eIn, left = cx - totalW / 2;
      g.fillStyle = rgba(COL.lime, 0.9); g.fillRect(left, bot + 28, totalW * ul, 3);
      setFont(g, 'JetBrains Mono', 400, 16); g.letterSpacing = '6px'; g.fillStyle = rgba(COL.white, 0.6 * ul);
      g.fillText(t < 4.0 ? scramble('FIG.01 — MOVEMENT', prog(t, 3.2, 3.7), t, 3) : scramble('FIG.02 — FEELING', prog(t, 4.02, 4.4), t, 4), left, bot + 70);
      g.letterSpacing = '0px';
    }
  }
  g.restore();
}

function anamorphic(g, x, y, a, c) {
  if (a < 0.01) return;
  const op = g.globalCompositeOperation; g.globalCompositeOperation = 'lighter';
  const gr = g.createLinearGradient(0, 0, W, 0);
  gr.addColorStop(0, rgba(c, 0)); gr.addColorStop(clamp(x / W - 0.3), rgba(c, 0)); gr.addColorStop(clamp(x / W), rgba([255, 255, 255], a)); gr.addColorStop(clamp(x / W + 0.3), rgba(c, 0)); gr.addColorStop(1, rgba(c, 0));
  g.fillStyle = gr; g.fillRect(0, y - 1.5, W, 3);
  g.globalAlpha = 0.35; g.fillRect(0, y - 14, W, 28); g.globalAlpha = 1;
  g.globalCompositeOperation = op;
}

// ---------------------------------------------------------------- section 03: kinetic type
const WORDS = [
  [5.0, 'TIMING', 'spring'], [5.5, 'RHYTHM', 'slice'], [6.0, 'PHYSICS', 'bounce'], [6.5, 'LIGHT', 'light'],
  [7.0, 'FORM', 'extrude'], [7.25, 'FLOW', 'wave'], [7.5, 'SCOPE', 'track'],
];
function tunnel(g, t, alpha, inv) {
  const cx = W / 2, cy = H / 2, F = 700, hw = 1500, hh = 860, sp = 420, depth = 6300, speed = 2600;
  const roll = Math.sin(t * 0.9) * 0.05;
  const col = inv ? [0, 40, 20] : COL.lime;
  g.save(); g.translate(cx, cy); g.rotate(roll);
  const n = Math.ceil(depth / sp);
  for (let i = 0; i < n; i++) {
    const z = ((i * sp - (t - 5) * speed) % depth + depth) % depth + 60;
    const s = F / z, a = alpha * clamp(1 - z / depth) * clamp(z / 400);
    g.strokeStyle = rgba(col, a * 0.5); g.lineWidth = Math.max(0.6, 2.2 * s);
    g.strokeRect(-hw * s, -hh * s, hw * 2 * s, hh * 2 * s);
  }
  // longitudinal rails
  g.strokeStyle = rgba(col, alpha * 0.18); g.lineWidth = 1;
  for (let k = -4; k <= 4; k++) {
    const segs = [[k * hw / 4, -hh], [k * hw / 4, hh], [-hw, k * hh / 4], [hw, k * hh / 4]];
    for (const [x, y] of segs) { g.beginPath(); g.moveTo(x * F / 60, y * F / 60); g.lineTo(x * F / depth, y * F / depth); g.stroke(); }
  }
  g.restore();
}
function S3(g, t) {
  const cx = W / 2, cy = H / 2;
  let wi = -1; for (let i = 0; i < WORDS.length; i++) if (t >= WORDS[i][0]) wi = i;
  if (wi < 0) return;
  const [t0, word, fx] = WORDS[wi];
  const lt = t - t0;
  const inv = fx === 'slice';
  if (inv) { g.fillStyle = '#0aa85a'; g.fillRect(0, 0, W, H); }
  tunnel(g, t, inv ? 0.9 : 0.8 + imp(t, t0, 0.2) * 0.6, inv);
  // background marquee
  g.save();
  setFont(g, 'Unbounded', 800, 120); g.textBaseline = 'middle'; g.textAlign = 'left';
  for (let r = 0; r < 7; r++) {
    const y = 60 + r * 160, dir = r % 2 ? 1 : -1, off = (((t - 5) * 420 * dir + r * 333) % 1400 + 1400) % 1400;
    g.strokeStyle = inv ? 'rgba(0,0,0,0.12)' : 'rgba(236,246,255,0.05)'; g.lineWidth = 1.2;
    for (let x = -1400 - off; x < W + 200; x += 1400) g.strokeText('PORTOKO', x, y);
  }
  g.restore();

  const size = { TIMING: 220, RHYTHM: 220, PHYSICS: 210, LIGHT: 250, FORM: 270, FLOW: 270, SCOPE: 170 }[word];
  setFont(g, 'Unbounded', 800, size); g.textBaseline = 'alphabetic'; g.textAlign = 'left'; g.letterSpacing = '0px';
  let ls = 0;
  if (fx === 'track') ls = E.outExpo(prog(lt, 0, 0.35)) * 70;
  const L = layout(g, word, ls), left = cx - L.width / 2, base = cy + size * 0.36;
  const fill = inv ? '#03120a' : '#f4fbff';
  g.fillStyle = fill;

  if (fx === 'spring') {
    L.chars.forEach((c, i) => {
      const s = spring(lt - i * 0.03, 2.6, 6.5);
      if (s <= 0) return;
      const x = left + c.x + c.w / 2;
      g.save(); g.translate(x, base - size * 0.36); g.scale(s, s); g.rotate((1 - Math.min(1, s)) * 0.6);
      g.fillText(c.ch, -c.w / 2, size * 0.36); g.restore();
    });
  } else if (fx === 'slice') {
    const ns = 9, top = base - size * 0.78, hgt = size * 0.86;
    for (let k = 0; k < ns; k++) {
      const p = E.outExpo(prog(lt, k * 0.018, k * 0.018 + 0.3));
      const dx = (1 - p) * (k % 2 ? 1 : -1) * 900 + Math.sin(k * 7 + Math.floor(t * 30)) * 12 * (1 - p);
      g.save(); g.beginPath(); g.rect(0, top + (hgt * k) / ns, W, hgt / ns + 0.5); g.clip();
      L.chars.forEach(c => g.fillText(c.ch, left + c.x + dx, base));
      g.restore();
    }
  } else if (fx === 'bounce') {
    L.chars.forEach((c, i) => {
      const p = prog(lt, i * 0.035, i * 0.035 + 0.38);
      if (p <= 0) return;
      const y = (1 - E.outBounce(p)) * -700;
      const rot = (1 - E.outCubic(p)) * (i % 2 ? 0.3 : -0.3);
      const x = left + c.x + c.w / 2;
      g.save(); g.translate(x, base + y); g.rotate(rot); g.fillText(c.ch, -c.w / 2, 0); g.restore();
    });
  } else if (fx === 'light') {
    const p = E.outCubic(prog(lt, 0, 0.35));
    g.strokeStyle = rgba(COL.white, 0.9); g.lineWidth = 2;
    L.chars.forEach(c => g.strokeText(c.ch, left + c.x, base));
    g.save(); g.beginPath(); g.rect(left - 20, 0, (L.width + 40) * p, H); g.clip();
    const lgd = g.createLinearGradient(left, 0, left + L.width, 0);
    lgd.addColorStop(0, '#eafff5'); lgd.addColorStop(0.5, '#7dffc4'); lgd.addColorStop(1, '#19f08a');
    g.fillStyle = lgd; L.chars.forEach(c => g.fillText(c.ch, left + c.x, base));
    g.restore();
    // volumetric streaks
    g.globalCompositeOperation = 'lighter';
    for (let k = 1; k <= 14; k++) {
      const s = 1 + k * 0.035 * p;
      g.save(); g.translate(cx, cy); g.scale(s, s); g.translate(-cx, -cy);
      g.fillStyle = rgba(COL.lime, 0.05 * p * (1 - k / 15));
      L.chars.forEach(c => g.fillText(c.ch, left + c.x, base)); g.restore();
    }
    g.globalCompositeOperation = 'source-over';
  } else if (fx === 'extrude') {
    const p = E.outBack(prog(lt, 0, 0.22), 1.4), depth = 26 * p, ang = -2.4 + lt * 1.5;
    for (let k = Math.round(depth); k >= 1; k--) {
      const c0 = mixc(COL.green, [2, 30, 18], k / 26);
      g.fillStyle = rgba(c0, 1);
      L.chars.forEach(c => g.fillText(c.ch, left + c.x + Math.cos(ang) * k * 1.6, base + Math.sin(ang) * k * 1.6 + (1 - p) * 60));
    }
    g.fillStyle = fill; L.chars.forEach(c => g.fillText(c.ch, left + c.x, base + (1 - p) * 60));
  } else if (fx === 'wave') {
    const wg = g.createLinearGradient(left, 0, left + L.width, 0);
    wg.addColorStop(0, '#7dffc4'); wg.addColorStop(0.5, '#19d3c5'); wg.addColorStop(1, '#8b5cff');
    g.fillStyle = wg;
    const a = E.outCubic(prog(lt, 0, 0.12));
    L.chars.forEach((c, i) => g.fillText(c.ch, left + c.x, base + Math.sin(lt * 16 - i * 1.1) * 38 * (1 - lt * 2.5) * a + (1 - a) * 80));
  } else if (fx === 'track') {
    const a = E.outCubic(prog(lt, 0, 0.15));
    g.globalAlpha = a; L.chars.forEach((c, i) => { if (i !== 2 || t < 7.73) g.fillText(c.ch, left + c.x, base); }); g.globalAlpha = 1;
  }
  // index tag
  setFont(g, 'JetBrains Mono', 700, 16); g.letterSpacing = '4px';
  g.fillStyle = inv ? 'rgba(0,0,0,0.75)' : rgba(COL.lime, 0.9);
  g.fillText(`0${wi + 1}/07`, left, base - size * 0.95);
  setFont(g, 'JetBrains Mono', 400, 16);
  g.fillStyle = inv ? 'rgba(0,0,0,0.6)' : 'rgba(236,246,255,0.55)';
  g.textAlign = 'right'; g.fillText(scramble(`${word.toLowerCase()}.fx`, prog(lt, 0, 0.2), t, wi), left + L.width, base - size * 0.95);
  g.textAlign = 'left'; g.letterSpacing = '0px';
}

// ---------------------------------------------------------------- section 04: orbit / black hole
function bhCam(t) {
  const dive = E.inExpo(prog(t, 10.95, 11.6));
  const g0 = lerp(0.82, 1.02, E.inOutCubic(prog(t, 7.8, 11))) * Math.exp(dive * Math.log(9));
  return { g: g0, el: 0.3 + 0.05 * Math.sin(t * 0.4) + dive * 0.25, roll: -0.3 + (t - 8) * 0.025, cx: W * 0.55 - dive * 100, cy: H * 0.5, dive };
}
function bhProj(C, R, a, h) {
  const xd = R * Math.cos(a), yd = R * Math.sin(a);
  const se = Math.sin(C.el), ce = Math.cos(C.el);
  let Y = -yd * se - h * ce; const depth = yd * ce - h * se;
  const ps = 2600 / (2600 + depth * 0.8);
  let X = xd * ps; Y *= ps;
  const cr = Math.cos(C.roll), sr = Math.sin(C.roll);
  return [C.cx + (X * cr - Y * sr) * C.g, C.cy + (X * sr + Y * cr) * C.g, depth, ps];
}
function S4(g, t) {
  const C = bhCam(t), Cp = bhCam(t - 1 / 60);
  const Rs = 205 * C.g;
  drawNebula(g, 0.55, W * 0.5 + (t - 8) * -12, H * 0.5, 1.0 + (t - 8) * 0.03 + C.dive * 0.5, -0.35 + (t - 8) * 0.01);
  drawStars(g, t, 0.9, -8, C.cx, C.cy, 1 + C.dive * 2);

  const doppler = a => 0.3 + 0.7 * Math.pow(0.5 + 0.5 * Math.cos(a - Math.PI * 0.92), 1.5);
  const drawDisk = back => {
    g.globalCompositeOperation = 'lighter'; g.lineCap = 'round';
    for (const rg of BH.rings) {
      for (const ac of rg.arcs) {
        const a0 = ac.a0 + rg.om * t, n = Math.max(10, Math.floor((ac.span * rg.R * C.g) / 16));
        let prev = bhProj(C, rg.R, a0, rg.h);
        for (let j = 1; j <= n; j++) {
          const a = a0 + (ac.span * j) / n, q = bhProj(C, rg.R, a, rg.h);
          if ((q[2] > 0) === back) {
            const taper = Math.pow(Math.sin((Math.PI * j) / n), 0.7);
            g.strokeStyle = rgba(rg.c, 0.8 * taper * rg.b * doppler(a));
            g.lineWidth = rg.w * C.g * q[3] * (0.6 + taper * 0.6);
            g.beginPath(); g.moveTo(prev[0], prev[1]); g.lineTo(q[0], q[1]); g.stroke();
          }
          prev = q;
        }
      }
    }
    for (const d of BH.dust) {
      const a = d.a + d.om * t, q = bhProj(C, d.R, a, d.h);
      if ((q[2] > 0) !== back) continue;
      const q0 = bhProj(Cp, d.R, a - d.om / 60 - 0.004, d.h);
      g.strokeStyle = rgba(d.c, d.b * doppler(a) * 0.9); g.lineWidth = d.s * Math.sqrt(C.g) * q[3];
      g.beginPath(); g.moveTo(q0[0], q0[1]); g.lineTo(q[0], q[1]); g.stroke();
    }
    g.globalCompositeOperation = 'source-over';
    // glass shards
    for (const s of BH.shards) {
      const a = s.a + s.om * t, q = bhProj(C, s.R, a, s.h);
      if ((q[2] > 0) !== back) continue;
      const sz = s.sz * C.g * q[3], rot = s.rx + t * s.sp, sq = Math.abs(Math.cos(s.ry + t * s.sp * 0.7)) * 0.9 + 0.1;
      g.save(); g.translate(q[0], q[1]); g.rotate(rot); g.scale(1, sq);
      const gg = g.createLinearGradient(-sz, -sz * s.asp, sz, sz * s.asp);
      gg.addColorStop(0, 'rgba(220,255,240,0.02)'); gg.addColorStop(0.5, 'rgba(200,255,235,0.16)'); gg.addColorStop(1, 'rgba(160,200,255,0.03)');
      g.fillStyle = gg; g.strokeStyle = 'rgba(225,255,245,0.55)'; g.lineWidth = 1.1 / sq;
      g.beginPath(); g.moveTo(-sz, -sz * s.asp); g.lineTo(sz * 0.9, -sz * s.asp * 1.1); g.lineTo(sz, sz * s.asp); g.lineTo(-sz * 0.85, sz * s.asp * 0.9); g.closePath();
      g.fill(); g.stroke(); g.restore();
    }
  };
  drawDisk(true);
  // gravitational lensing: the far side of the disk bent over (and under) the sphere
  g.save(); g.translate(C.cx, C.cy); g.rotate(C.roll); g.globalCompositeOperation = 'lighter'; g.lineCap = 'butt';
  for (let i = 0; i < 26; i++) {
    const rg = BH.rings[i], f = i / 25;
    const R = Rs * (1.06 + f * 0.62), wob = Math.sin(t * 2 + i) * 0.04;
    const n = 28;
    for (let j = 0; j < n; j++) {
      const a1 = Math.PI + 0.12 + wob + ((Math.PI - 0.24) * j) / n, a2 = a1 + (Math.PI - 0.24) / n;
      const taper = Math.pow(Math.sin(((j + 0.5) / n) * Math.PI), 0.5);
      g.strokeStyle = rgba(rg.c, (0.95 - f * 0.6) * taper * doppler(a1 - Math.PI / 2 + Math.PI));
      g.lineWidth = rg.w * C.g * 1.4;
      g.beginPath(); g.arc(0, 0, R, a1, a2); g.stroke();
    }
    if (i < 10) {
      g.strokeStyle = rgba(rg.c, 0.25 * (1 - i / 10)); g.lineWidth = rg.w * C.g * 0.6;
      g.beginPath(); g.arc(0, 0, Rs * (1.03 + i * 0.012), 0.3, Math.PI - 0.3); g.stroke();
    }
  }
  g.restore();
  // event horizon
  g.globalCompositeOperation = 'source-over';
  const sg = g.createRadialGradient(C.cx, C.cy, Rs * 0.2, C.cx, C.cy, Rs);
  sg.addColorStop(0, '#000'); sg.addColorStop(0.9, '#000'); sg.addColorStop(1, '#010604');
  g.fillStyle = sg; g.beginPath(); g.arc(C.cx, C.cy, Rs, 0, TAU); g.fill();
  g.globalCompositeOperation = 'lighter';
  const pr = g.createRadialGradient(C.cx, C.cy, Rs, C.cx, C.cy, Rs * 1.35);
  pr.addColorStop(0, rgba(COL.mint, 0.55)); pr.addColorStop(0.15, rgba(COL.lime, 0.18)); pr.addColorStop(1, rgba(COL.teal, 0));
  g.fillStyle = pr; g.beginPath(); g.arc(C.cx, C.cy, Rs * 1.35, 0, TAU); g.arc(C.cx, C.cy, Rs, 0, TAU, true); g.fill();
  g.strokeStyle = rgba(COL.mint, 0.95); g.lineWidth = 3 * C.g;
  g.beginPath(); g.arc(C.cx, C.cy, Rs * 1.012, 0, TAU); g.stroke();
  g.strokeStyle = rgba(COL.white, 0.5); g.lineWidth = 1;
  g.beginPath(); g.arc(C.cx, C.cy, Rs * 1.004, 0, TAU); g.stroke();
  g.globalCompositeOperation = 'source-over';
  drawDisk(false);
  anamorphic(g, C.cx, C.cy, imp(t, 8.0, 0.6) * 0.9 + 0.12, COL.teal);
  // caption
  const ca = prog(t, 8.4, 8.8) * (1 - prog(t, 10.7, 11.0));
  if (ca > 0) {
    g.textAlign = 'left'; g.textBaseline = 'alphabetic';
    setFont(g, 'Space Grotesk', 300, 64); g.letterSpacing = '6px';
    g.fillStyle = rgba(COL.white, 0.92 * ca);
    g.fillText(scramble('GRAVITY', prog(t, 8.4, 9.0), t, 5), 150, 830);
    setFont(g, 'JetBrains Mono', 400, 16); g.letterSpacing = '5px'; g.fillStyle = rgba(COL.mint, 0.7 * ca);
    g.fillText(scramble('EVERY FRAME PULLS YOU IN', prog(t, 8.7, 9.4), t, 6), 154, 872);
    g.fillStyle = rgba(COL.lime, 0.9 * ca); g.fillRect(154, 760, 60 * E.outExpo(prog(t, 8.4, 9.0)), 3);
    g.letterSpacing = '0px';
  }
}

// ---------------------------------------------------------------- section 05: flow -> logo
function S5(g, t) {
  const { pos, parts, steps } = FLOW;
  const s1 = Math.min(steps - 1, Math.floor((t - FLOW_T0) * FPS));
  if (s1 < 1) return;
  const X = logoXform(13.95);
  const nfade = prog(t, 11.3, 11.9) * (1 - prog(t, 13.6, 14.1));
  drawNebula(g, 0.45 * nfade, W / 2, H / 2, 1.15 - (t - 11.3) * 0.04, 0.2 - (t - 11.3) * 0.03);
  const fin = prog(t, 11.3, 11.75), fout = 1 - prog(t, 13.97, 14.35);
  g.globalCompositeOperation = 'lighter'; g.lineCap = 'round'; g.lineJoin = 'round';
  const TR = 16;
  for (let i = 0; i < parts.length; i++) {
    const p = parts[i];
    const conv = st => E.inOutCubic(prog(FLOW_T0 + st / FPS, 12.85 + p.del, 13.97));
    const [tx, ty] = L2S(X, p.tx, p.ty);
    const s0 = Math.max(0, s1 - TR);
    g.beginPath();
    for (let s = s0; s <= s1; s++) {
      const k = (i * steps + s) * 2, c = conv(s);
      const x = lerp(pos[k], tx, c), y = lerp(pos[k + 1], ty, c);
      s === s0 ? g.moveTo(x, y) : g.lineTo(x, y);
    }
    const cNow = conv(s1);
    const col = mixc(p.c, COL.white, cNow * 0.6);
    if (p.fat) { g.strokeStyle = rgba(col, 0.06 * fin * fout * (1 - cNow)); g.lineWidth = 14 + p.w * 6; g.stroke(); }
    g.strokeStyle = rgba(col, p.a * fin * fout * (1 - 0.72 * cNow)); g.lineWidth = p.w * (1 - cNow * 0.35);
    g.stroke();
  }
  g.globalCompositeOperation = 'source-over';
  const ca = prog(t, 11.8, 12.1) * (1 - prog(t, 12.9, 13.2));
  if (ca > 0) {
    g.textAlign = 'right'; g.textBaseline = 'alphabetic';
    setFont(g, 'Space Grotesk', 300, 64); g.letterSpacing = '6px'; g.fillStyle = rgba(COL.white, 0.9 * ca);
    g.fillText(scramble('FLUIDITY', prog(t, 11.8, 12.3), t, 7), W - 150, 250);
    setFont(g, 'JetBrains Mono', 400, 16); g.letterSpacing = '5px'; g.fillStyle = rgba(COL.mint, 0.7 * ca);
    g.fillText(scramble('CURL NOISE · 2,600 PARTICLES', prog(t, 12.0, 12.6), t, 8), W - 150, 292);
    g.textAlign = 'left'; g.letterSpacing = '0px';
  }
}

// ---------------------------------------------------------------- section 06: identity
function orbitRing(g, X, t, k, back) {
  const ox = LOGO.O[k], grow = E.outExpo(prog(t, 14.12 + k * 0.09, 14.9 + k * 0.09));
  if (grow <= 0) return;
  const R = lerp(106.5, 168 + k * 6, grow), a = grow * (1 - E.inExpo(prog(t, 17.05, 17.35)));
  const ph = t * 0.55 + k * 2.1;
  let n = [0.42 * Math.sin(ph), 1, 0.42 * Math.cos(ph)]; const nl = Math.hypot(...n); n = n.map(v => v / nl);
  const rot = [0.35, -0.2, 0.15][k];
  let u = [1, 0, 0]; const d = u[0] * n[0]; u = [u[0] - d * n[0], u[1] - d * n[1], u[2] - d * n[2]]; const ul = Math.hypot(...u); u = u.map(v => v / ul);
  const v = [n[1] * u[2] - n[2] * u[1], n[2] * u[0] - n[0] * u[2], n[0] * u[1] - n[1] * u[0]];
  const cr = Math.cos(rot), sr = Math.sin(rot);
  const P = th => { const x = R * (u[0] * Math.cos(th) + v[0] * Math.sin(th)), y = R * (u[1] * Math.cos(th) + v[1] * Math.sin(th)), z = R * (u[2] * Math.cos(th) + v[2] * Math.sin(th)); return [x * cr - y * sr, x * sr + y * cr, z]; };
  g.save(); g.globalCompositeOperation = 'lighter';
  const N = 90;
  for (let j = 0; j < N; j++) {
    const q0 = P((j / N) * TAU), q1 = P(((j + 1) / N) * TAU);
    if ((q0[2] + q1[2] > 0) !== back) continue;
    const [x0, y0] = L2S(X, ox + q0[0], LOGO.cy + q0[1]), [x1, y1] = L2S(X, ox + q1[0], LOGO.cy + q1[1]);
    g.strokeStyle = rgba(COL.mint, a * (back ? 0.35 : 0.8)); g.lineWidth = back ? 1.2 : 2;
    g.beginPath(); g.moveTo(x0, y0); g.lineTo(x1, y1); g.stroke();
  }
  const sat = P(t * 2.4 + k * 2);
  if ((sat[2] > 0) === back) {
    const [x, y] = L2S(X, ox + sat[0], LOGO.cy + sat[1]);
    const sg = g.createRadialGradient(x, y, 0, x, y, 22);
    sg.addColorStop(0, rgba(COL.white, a)); sg.addColorStop(0.25, rgba(COL.lime, a * 0.6)); sg.addColorStop(1, rgba(COL.lime, 0));
    g.fillStyle = sg; g.fillRect(x - 22, y - 22, 44, 44);
  }
  g.restore();
}
function S6(g, t) {
  const X = logoXform(t), cx = W / 2, cy = H / 2;
  const on = prog(t, 13.9, 14.3);
  drawNebula(g, 0.3 * on, cx, cy, 1.2 + (t - 14) * 0.02, 0.4 + (t - 14) * 0.01);
  drawStars(g, t, 0.6 * on, -14);
  // back halves of orbits
  for (let k = 0; k < 3; k++) orbitRing(g, X, t, k, true);
  // logo on its own layer (for the light sweep)
  llg.setTransform(1, 0, 0, 1, 0, 0); llg.globalCompositeOperation = 'source-over'; llg.clearRect(0, 0, W, H);
  const draw = li => E.inOutCubic(prog(t, 13.35 + li * 0.04, 13.35 + li * 0.04 + 0.4 + (li === 0 ? 0.08 : 0)));
  strokeLogo(llg, X, 'grad', draw);
  const hot = imp(t, 14.0, 0.28);
  if (hot > 0.01) { llg.globalAlpha = hot; strokeLogo(llg, X, '#ffffff', draw); llg.globalAlpha = 1; }
  // light sweeps
  for (const [s0, s1] of [[14.05, 14.6], [15.2, 15.9], [16.6, 17.2]]) {
    const p = prog(t, s0, s1); if (p <= 0 || p >= 1) continue;
    const x = lerp(cx - 1100, cx + 1100, E.inOutCubic(p));
    llg.globalCompositeOperation = 'source-atop';
    llg.save(); llg.translate(x, cy); llg.transform(1, 0, -0.45, 1, 0, 0);
    const sw = llg.createLinearGradient(-160, 0, 160, 0);
    sw.addColorStop(0, 'rgba(255,255,255,0)'); sw.addColorStop(0.5, 'rgba(255,255,255,0.95)'); sw.addColorStop(1, 'rgba(255,255,255,0)');
    llg.fillStyle = sw; llg.fillRect(-160, -400, 320, 800); llg.restore();
    llg.globalCompositeOperation = 'source-over';
  }
  const outro = E.inExpo(prog(t, 17.1, 17.5));
  g.drawImage(logoLayer, 0, 0);
  for (let k = 0; k < 3; k++) orbitRing(g, X, t, k, false);

  g.globalCompositeOperation = 'lighter';
  // impact ring + sparks
  {
    const p = prog(t, 14.0, 14.9);
    if (p > 0 && p < 1) {
      const R = 60 + 1500 * E.outExpo(p);
      g.strokeStyle = rgba(COL.mint, 0.7 * (1 - p)); g.lineWidth = 12 * (1 - p) + 1;
      g.beginPath(); g.ellipse(cx, X.cy, R, R * 0.42, 0, 0, TAU); g.stroke();
    }
    const tau = t - 14.0;
    if (tau > 0 && tau < 1.7) {
      for (const s of SPARKS) {
        if (tau > s.life) continue;
        const pos = tt => { const f = (1 - Math.exp(-s.k * tt)) / s.k; return L2S(X, s.x + s.vx * f / X.s * 0.8, s.y + (s.vy * f + 180 * tt * tt) / X.s * 0.8); };
        const [x1, y1] = pos(tau), [x0, y0] = pos(Math.max(0, tau - 0.03));
        g.strokeStyle = rgba(s.c, Math.pow(1 - tau / s.life, 1.3)); g.lineWidth = s.w;
        g.beginPath(); g.moveTo(x0, y0); g.lineTo(x1 + 0.2, y1); g.stroke();
      }
    }
  }
  anamorphic(g, cx, X.cy, imp(t, 14.0, 0.5) * 1.1, COL.teal);
  g.globalCompositeOperation = 'source-over';
  // tagline
  const ty = X.cy + 175;
  const lp = E.outExpo(prog(t, 14.55, 15.3)) * (1 - outro);
  if (lp > 0) {
    const lw = 640 * lp;
    const lgr = g.createLinearGradient(cx - lw / 2, 0, cx + lw / 2, 0);
    lgr.addColorStop(0, rgba(COL.lime, 0)); lgr.addColorStop(0.5, rgba(COL.lime, 0.9)); lgr.addColorStop(1, rgba(COL.lime, 0));
    g.fillStyle = lgr; g.fillRect(cx - lw / 2, ty - 40, lw, 1.5);
    g.textAlign = 'center'; g.textBaseline = 'middle';
    setFont(g, 'JetBrains Mono', 400, 22); g.letterSpacing = '12px';
    g.fillStyle = rgba(COL.white, 0.85 * lp);
    g.fillText(scramble('MOTION DESIGN · SHOWREEL 2026', prog(t, 14.8, 15.6), t, 9), cx + 6, ty);
    g.letterSpacing = '0px';
  }
  // iris out through the middle O
  if (outro > 0) {
    const [ox, oy] = L2S(X, LOGO.O[1], LOGO.cy);
    const R = X.s * 85 * (1 + outro * 40);
    g.fillStyle = '#ffffff';
    g.beginPath(); g.arc(ox, oy, R * outro, 0, TAU); g.fill();
  }
}

// ---------------------------------------------------------------- section 07: end card
function S7(g, t) {
  g.fillStyle = '#ffffff'; g.fillRect(0, 0, W, H);
  const sc = 0.56, iw = 2000 * sc, ih = 440 * sc, ix = W / 2 - iw / 2, iy = H / 2 - ih / 2 - 46;
  LOGO_COLS.forEach(([a, b], i) => {
    const p = E.outExpo(prog(t, 17.55 + i * 0.05, 17.55 + i * 0.05 + 0.9));
    if (p <= 0) return;
    g.save(); g.beginPath(); g.rect(ix + (a - 3) * sc, iy + 70 * sc, (b - a + 6) * sc, 270 * sc); g.clip();
    g.drawImage(LOGO_IMG, ix, iy + (1 - p) * 200, iw, ih);
    g.restore();
  });
  // brand-green orbit around the final O
  const op = E.outExpo(prog(t, 18.05, 19.0));
  if (op > 0) {
    const ox = ix + 1828.5 * sc, oy = iy + 204 * sc, R = 128 * sc + 44 * op;
    g.save(); g.translate(ox, oy); g.rotate(-0.35 + (t - 18) * 0.05);
    g.strokeStyle = `rgba(10,168,90,${0.55 * op})`; g.lineWidth = 2;
    g.beginPath(); g.ellipse(0, 0, R * 1.12, R * 0.34, 0, -Math.PI * 0.95 * op - 0.2, 0.2 + Math.PI * 0.95 * op); g.stroke();
    g.fillStyle = '#0aa858'; const a = t * 2.2; g.beginPath(); g.arc(Math.cos(a) * R * 1.12, Math.sin(a) * R * 0.34, 5 * op, 0, TAU); g.fill();
    g.restore();
  }
  const ly = iy + ih + 44;
  const lp = E.outExpo(prog(t, 18.0, 18.8));
  const lg2 = g.createLinearGradient(W / 2 - 340, 0, W / 2 + 340, 0);
  lg2.addColorStop(0, '#191b25'); lg2.addColorStop(1, '#05a858');
  g.fillStyle = lg2; g.fillRect(W / 2 - 340 * lp, ly, 680 * lp, 2);
  const tp = E.outCubic(prog(t, 18.25, 18.9));
  if (tp > 0) {
    g.textAlign = 'center'; g.textBaseline = 'alphabetic';
    setFont(g, 'Space Grotesk', 500, 30); g.letterSpacing = '16px';
    g.fillStyle = `rgba(25,27,37,${tp})`;
    g.fillText('MOTION DESIGN SHOWREEL', W / 2 + 8, ly + 66 + (1 - tp) * 20);
    setFont(g, 'JetBrains Mono', 400, 17); g.letterSpacing = '10px';
    g.fillStyle = `rgba(10,168,90,${E.outCubic(prog(t, 18.5, 19.1))})`;
    g.fillText(scramble('2026 · PORTOKO', prog(t, 18.5, 19.2), t, 10), W / 2 + 5, ly + 112);
    g.letterSpacing = '0px';
  }
  // flash from the iris
  const fl = 1 - E.outCubic(prog(t, 17.5, 17.9));
  if (fl > 0) { g.fillStyle = `rgba(255,255,255,${fl})`; g.fillRect(0, 0, W, H); }
  // final fade
  const ff = prog(t, 19.72, 20);
  if (ff > 0) { g.fillStyle = `rgba(255,255,255,${ff * 0.0})`; g.fillRect(0, 0, W, H); }
}

// ---------------------------------------------------------------- HUD
const SECTIONS = [[0, '01', 'IGNITION'], [2, '02', 'BIG BANG'], [5, '03', 'KINETIC TYPE'], [7.95, '04', 'ORBIT'], [11.4, '05', 'FLOW'], [13.95, '06', 'IDENTITY']];
function HUD(g, t, inv) {
  const a = prog(t, 0.1, 0.5) * (1 - prog(t, 17.1, 17.4));
  if (a <= 0) return;
  const c = inv ? [3, 18, 10] : COL.white, m = 54, L = 34;
  const dr = E.outExpo(prog(t, 0.1, 0.8));
  g.strokeStyle = rgba(c, 0.55 * a); g.lineWidth = 1.5;
  for (const [x, y, sx, sy] of [[m, m, 1, 1], [W - m, m, -1, 1], [m, H - m, 1, -1], [W - m, H - m, -1, -1]]) {
    g.beginPath(); g.moveTo(x, y + sy * L * dr); g.lineTo(x, y); g.lineTo(x + sx * L * dr, y); g.stroke();
  }
  g.textBaseline = 'middle';
  setFont(g, 'JetBrains Mono', 700, 14); g.letterSpacing = '5px'; g.textAlign = 'left';
  g.fillStyle = rgba(c, 0.8 * a); g.fillText(scramble('PORTOKO', prog(t, 0.15, 0.7), t, 20), m + 20, m + 20);
  setFont(g, 'JetBrains Mono', 400, 14); g.fillStyle = rgba(c, 0.5 * a);
  g.fillText('/ REEL 2026', m + 138, m + 20);
  // section
  let sec = SECTIONS[0]; for (const s of SECTIONS) if (t >= s[0]) sec = s;
  g.textAlign = 'right';
  g.fillStyle = rgba(c, 0.8 * a);
  g.fillText(scramble(`${sec[1]} — ${sec[2]}`, prog(t, sec[0], sec[0] + 0.35), t, 21 + +sec[1]), W - m - 20, m + 20);
  // timecode
  const fr = Math.floor(t * FPS + 1e-6), ss = Math.floor(fr / FPS), ff = fr % FPS;
  g.textAlign = 'left'; g.fillStyle = rgba(c, 0.6 * a);
  g.fillText(`TC 00:00:${String(ss).padStart(2, '0')}:${String(ff).padStart(2, '0')}`, m + 20, H - m - 20);
  // progress
  g.textAlign = 'right';
  g.fillText('1920×1080 · 60P', W - m - 20, H - m - 20);
  const pw = 180, px = W - m - 20 - pw - 230;
  g.fillStyle = rgba(c, 0.18 * a); g.fillRect(px, H - m - 21, pw, 2);
  g.fillStyle = rgba(inv ? c : COL.lime, 0.9 * a); g.fillRect(px, H - m - 21, pw * (t / DUR), 2);
  g.letterSpacing = '0px';
}

// ---------------------------------------------------------------- post
function bloom(strength) {
  if (strength <= 0) return;
  b1g.globalCompositeOperation = 'copy'; b1g.filter = 'contrast(1.5) blur(3px)'; b1g.drawImage(cvs, 0, 0, W / 4, H / 4); b1g.filter = 'none';
  b2g.globalCompositeOperation = 'copy'; b2g.filter = 'blur(4px)'; b2g.drawImage(b1, 0, 0, W / 12, H / 12); b2g.filter = 'none';
  ctx.globalCompositeOperation = 'lighter';
  ctx.globalAlpha = Math.min(1, strength * 0.7); ctx.drawImage(b1, 0, 0, W, H);
  ctx.globalAlpha = Math.min(1, strength * 0.9); ctx.drawImage(b2, 0, 0, W, H);
  ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over';
}
function chroma(amt) {
  if (amt < 0.5) return;
  tg.globalCompositeOperation = 'copy'; tg.drawImage(cvs, 0, 0);
  ctx.globalCompositeOperation = 'source-over'; ctx.fillStyle = '#000'; ctx.fillRect(0, 0, W, H);
  for (const [col, k] of [['#ff0000', 1], ['#00ff00', 0], ['#0000ff', -1]]) {
    const s = 1 + (k * amt) / (W / 2);
    cg.globalCompositeOperation = 'copy';
    cg.setTransform(s, 0, 0, s, (W / 2) * (1 - s), (H / 2) * (1 - s)); cg.drawImage(tmp, 0, 0); cg.setTransform(1, 0, 0, 1, 0, 0);
    cg.globalCompositeOperation = 'multiply'; cg.fillStyle = col; cg.fillRect(0, 0, W, H);
    ctx.globalCompositeOperation = 'lighter'; ctx.drawImage(chan, 0, 0);
  }
  ctx.globalCompositeOperation = 'source-over';
}
function vignette(a) {
  const vg = ctx.createRadialGradient(W / 2, H / 2, H * 0.35, W / 2, H / 2, H * 1.05);
  vg.addColorStop(0, 'rgba(0,0,0,0)'); vg.addColorStop(1, `rgba(0,0,0,${a})`);
  ctx.fillStyle = vg; ctx.fillRect(0, 0, W, H);
}
function grain(t, a) {
  const fr = Math.floor(t * FPS);
  const pat = ctx.createPattern(GRAIN[fr % 4], 'repeat');
  ctx.save(); ctx.globalCompositeOperation = 'overlay'; ctx.globalAlpha = a;
  ctx.translate((hash(fr) % 256), (hash(fr + 7) % 256));
  ctx.fillStyle = pat; ctx.fillRect(-256, -256, W + 512, H + 512);
  ctx.restore();
}
function withLayer(alpha, fn) {
  if (alpha <= 0) return;
  if (alpha >= 0.999) { fn(ctx); return; }
  lg.setTransform(1, 0, 0, 1, 0, 0); lg.globalCompositeOperation = 'source-over'; lg.globalAlpha = 1;
  lg.clearRect(0, 0, W, H);
  lg.setTransform(ctx.getTransform());
  fn(lg);
  lg.setTransform(1, 0, 0, 1, 0, 0);
  ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = alpha; ctx.drawImage(layer, 0, 0); ctx.restore();
}

// ---------------------------------------------------------------- main
const IMPACTS = [[2.0, 1.0], [4.0, 0.45], [5.5, 0.25], [6.0, 0.25], [7.0, 0.3], [8.0, 0.9], [14.0, 1.0]];
function render(t) {
  t = clamp(t, 0, DUR - 1e-6);
  ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over'; ctx.filter = 'none';
  ctx.fillStyle = '#020405'; ctx.fillRect(0, 0, W, H);
  if (t >= 17.5) { S7(ctx, t); grain(t, 0.05); return; }

  let shake = 0, ca = 0.0;
  for (const [t0, k] of IMPACTS) { shake += k * imp(t, t0, 0.14); ca += k * imp(t, t0, 0.22); }
  shake += 0.5 * E.inExpo(prog(t, 10.9, 11.55)) * (1 - prog(t, 11.55, 11.7));
  ctx.save();
  if (shake > 0.01) ctx.translate(noise3(t * 30, 0.5, 1) * 40 * shake, noise3(0.5, t * 30, 2) * 40 * shake);

  if (t < 2.02) S1(ctx, t);
  if (t >= 2.0 && t < 5.0) S2(ctx, t);
  // S3 with the O-portal into S4
  const portalP = E.inExpo(prog(t, 7.74, 8.02));
  const Rp = 70 + portalP * 1800, ringW = Rp * 0.2;
  const inner = Rp - ringW / 2;
  if (t >= 5.0 && t < 8.02 && inner < 1110) {
    S3(ctx, t);
    if (t >= 7.72) {
      const cx = W / 2, cy = H / 2, pin = E.outBack(prog(t, 7.72, 7.8), 2.5);
      const r0 = Math.max(0.1, (inner) * pin);
      ctx.save(); ctx.beginPath(); ctx.arc(cx, cy, r0, 0, TAU); ctx.clip();
      ctx.fillStyle = '#000'; ctx.fillRect(0, 0, W, H); S4(ctx, t); ctx.restore();
      const rg = ctx.createLinearGradient(cx - Rp, cy - Rp, cx + Rp, cy + Rp);
      rg.addColorStop(0, '#f2f8ff'); rg.addColorStop(0.5, '#7dffc4'); rg.addColorStop(1, '#0fcf74');
      ctx.strokeStyle = rg; ctx.lineWidth = ringW * pin;
      ctx.beginPath(); ctx.arc(cx, cy, Rp * pin, 0, TAU); ctx.stroke();
    }
  } else if (t >= 7.72 && t < 11.75) {
    withLayer(1 - prog(t, 11.45, 11.72), g => S4(g, t));
  }
  if (t >= 11.3 && t < 14.4) S5(ctx, t);
  if (t >= 13.3) S6(ctx, t);
  ctx.restore();

  // post
  const bl = 0.42 + 0.8 * imp(t, 2.0, 0.4) + 0.6 * imp(t, 8.0, 0.4) + 0.9 * imp(t, 14.0, 0.45);
  bloom(bl);
  chroma(ca * 14 + E.inExpo(prog(t, 10.9, 11.55)) * (1 - prog(t, 11.55, 11.8)) * 18);
  vignette(0.6);
  grain(t, 0.09);
  const inv = t >= 5.5 && t < 6.0;
  HUD(ctx, t, inv);
  // iris white must stay pure over the post stack
  if (t > 17.1) {
    const X = logoXform(t), outro = E.inExpo(prog(t, 17.1, 17.5));
    const [ox, oy] = L2S(X, LOGO.O[1], LOGO.cy);
    ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.arc(ox, oy, X.s * 85 * (1 + outro * 40) * outro, 0, TAU); ctx.fill();
  }
}

// ---------------------------------------------------------------- boot
const READY = (async () => {
  await Promise.all([
    document.fonts.load('800 100px "Unbounded"'), document.fonts.load('300 100px "Unbounded"'),
    document.fonts.load('300 100px "Space Grotesk"'), document.fonts.load('500 100px "Space Grotesk"'), document.fonts.load('700 100px "Space Grotesk"'),
    document.fonts.load('400 20px "JetBrains Mono"'), document.fonts.load('700 20px "JetBrains Mono"'),
  ]);
  LOGO_IMG = new Image(); LOGO_IMG.src = 'logo.png'; await LOGO_IMG.decode();
  NEBULA = buildNebula(); buildGrain(); buildStars(); buildBurst(); buildDots(); buildBlackHole(); buildFlow();
  window.__ready = true;
})();
window.renderFrame = (t, q = 0.95) => { render(t); return cvs.toDataURL('image/jpeg', q); };
