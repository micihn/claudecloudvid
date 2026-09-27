// The flower, as threads. Every thread is a polyline in "flower space"; at time t each point has a
// 3D target (the drawing, flat or blooming), and the tangle is made from that target by pushing each
// point along the ray from the one true point of view EYE. Seen from EYE, the tangle IS the drawing.
import { rng } from './util.js';

export const EYE = [0, 0, 10];            // the point of view
const OUTER = { n: 8, L: 2.4, W: 0.62, nest: 9, rot: 0 };
const INNER = { n: 8, L: 1.5, W: 0.44, nest: 7, rot: Math.PI / 8 };

// petal half-width along its length (u = 0 base .. 1 tip): slim, widest a little before the middle, pointed tip
const HW_K = 1 / (Math.pow(0.45, 0.8) * Math.pow(0.55, 0.98));
function petalHalfWidth(W, u) {
  u = Math.min(1, Math.max(0, u));
  return W * HW_K * Math.pow(u, 0.8) * Math.pow(1 - u, 0.98);
}

export function buildFlower() {
  const R = rng(7);
  const petals = [];                      // {layer, idx, phi, L, W}
  for (const [li, P] of [OUTER, INNER].entries())
    for (let i = 0; i < P.n; i++) petals.push({ layer: li, idx: i, phi: P.rot + i * 2 * Math.PI / P.n, L: P.L, W: P.W });

  const threads = [];                     // {kind, petal?, pts:[[x,y]...] local, closed, color, seed...}
  petals.forEach((p, pi) => {
    const P = p.layer ? INNER : OUTER;
    for (let j = 0; j < P.nest; j++) {
      const s = 1 - j * (0.75 / P.nest), cx = 0.12 * p.L, pts = [];
      const N = p.layer ? 180 : 240;
      for (let k = 0; k <= N; k++) {                // up one side and back down the other, dense at the ends
        const h = k <= N / 2 ? k / (N / 2) : 2 - k / (N / 2), u = (1 - Math.cos(Math.PI * h)) / 2;
        const x = p.L * u, y = (k <= N / 2 ? 1 : -1) * petalHalfWidth(p.W, u);
        pts.push([cx + (x - cx) * s, y * s]);
      }
      threads.push({ kind: 'petal', petal: pi, pts, closed: true, j, depth: j / P.nest });
    }
    const rib = [];                                 // the midrib
    for (let k = 0; k <= 60; k++) rib.push([p.L * (0.04 + 0.9 * k / 60), 0]);
    threads.push({ kind: 'petal', petal: pi, pts: rib, closed: false, j: 0, depth: 0.5 });
  });
  for (let i = 0; i < 5; i++) {           // the centre: rings
    const r = 0.07 + i * 0.07, pts = [];
    for (let k = 0; k <= 90; k++) { const a = 2 * Math.PI * k / 90; pts.push([r * Math.cos(a), r * Math.sin(a)]); }
    threads.push({ kind: 'ring', pts, closed: true, r });
  }
  for (let i = 0; i < 26; i++) {          // stamens: short curls that rise when the flower blooms
    const a0 = i * 2 * Math.PI / 26 + R() * 0.2, len = 0.32 + R() * 0.25, pts = [];
    for (let k = 0; k <= 26; k++) {
      const u = k / 26, a = a0 + u * u * 0.9, r = 0.1 + u * len;
      pts.push([r * Math.cos(a), r * Math.sin(a), u]);   // third value: height weight
    }
    threads.push({ kind: 'stamen', pts, closed: false, len });
  }
  // per-thread randomness for the tangle: integer frequencies keep closed threads closed
  threads.forEach((th, i) => {
    const f = () => 1 + Math.floor(R() * 3);
    th.i = i;
    th.lat = [0, 1, 2].map(() => [0, 1, 2].map(() => ({ f: f(), ph: R() * 6.283, w: (R() - 0.5) * 0.9, a: 0.4 + R() * 0.6 })));
    th.dep = [0, 1, 2].map(() => ({ f: f() + 1, ph: R() * 6.283, w: (R() - 0.5) * 1.2, a: 0.4 + R() * 0.6 }));
    th.start = R();                        // order threads appear in during the opening
    th.hue = R();
  });
  return { petals, threads, petalHalfWidth };
}

// state s: { bloom (0 flat .. 1 open), spin (rad), open (petal lift), stamen (0..1) }
// local petal point (x along, y across) -> flower space 3D
export function petalPoint(p, x, y, s, out) {
  const beta = s.bloom * (p.layer ? 0.95 : 0.55) * s.open;     // lift toward the eye, inner petals more
  const cup = s.bloom * 0.22 * (y / p.W) * (y / p.W) * p.L;    // edges curl up
  const lx = x * Math.cos(beta) - cup * Math.sin(beta) * 0.3;
  const lz = x * Math.sin(beta) + cup * Math.cos(beta);
  const a = p.phi + s.spin, c = Math.cos(a), sn = Math.sin(a);
  const base = 0.06 + p.layer * 0.02;
  out[0] = (base + lx) * c - y * sn; out[1] = (base + lx) * sn + y * c; out[2] = lz;
  return out;
}

const tmp = [0, 0, 0];
// target (drawing) position of point k of a thread
export function targetPoint(F, th, k, s, out) {
  const q = th.pts[k];
  if (th.kind === 'petal') return petalPoint(F.petals[th.petal], q[0], q[1], s, out);
  const c = Math.cos(s.spin), sn = Math.sin(s.spin);
  out[0] = q[0] * c - q[1] * sn; out[1] = q[0] * sn + q[1] * c;
  out[2] = th.kind === 'ring' ? s.bloom * 0.08 : s.bloom * s.stamen * q[2] * th.len * 1.3;
  return out;
}

// the tangle: push the target along the eye ray (invisible from EYE), plus lateral noise that is not
function wave(ws, u, t) { let v = 0; for (const w of ws) v += w.a * Math.sin(6.2832 * w.f * u + w.ph + w.w * t); return v / ws.length; }

export function tanglePoint(F, th, k, s, g, t, out) {
  targetPoint(F, th, k, s, tmp);
  const u = k / (th.pts.length - 1);
  const lam = Math.exp(g.depth * 0.85 * wave(th.dep, u, t));   // position along the eye ray; never reaches the eye
  out[0] = EYE[0] + lam * (tmp[0] - EYE[0]);
  out[1] = EYE[1] + lam * (tmp[1] - EYE[1]);
  out[2] = EYE[2] + lam * (tmp[2] - EYE[2]);
  if (g.lat > 0) for (let a = 0; a < 3; a++) out[a] += g.lat * 1.45 * wave(th.lat[a], u, t);
  return out;
}
