// Line-drawn fragments of a tangled business: a spreadsheet, chat bubbles, a barcode, a receipt,
// a kanban board, a checkbox. They float into the tangle in the opening and dissolve during the orbit.
import { rng } from './util.js';

const rect = (x, y, w, h) => [[[x, y], [x + w, y], [x + w, y + h], [x, y + h], [x, y]]];
function roundRect(x, y, w, h, r, tail) {
  const p = [], arc = (cx, cy, a0) => { for (let k = 0; k <= 6; k++) { const a = a0 + k * Math.PI / 12; p.push([cx + r * Math.cos(a), cy + r * Math.sin(a)]); } };
  arc(x + w - r, y + r, -Math.PI / 2); arc(x + w - r, y + h - r, 0); arc(x + r, y + h - r, Math.PI / 2);
  if (tail) { p.push([x + 0.05, y + h * 0.3]); p.push([x - 0.16, y - 0.06]); p.push([x + r * 1.6, y]); }
  else arc(x + r, y + r, Math.PI);
  p.push(p[0]); return [p];
}
const line = (a, b, c, d) => [[[a, b], [c, d]]];

const SHAPES = {
  sheet() {
    let l = rect(-0.6, -0.4, 1.2, 0.8);
    for (let i = 1; i < 4; i++) l = l.concat(line(-0.6 + i * 0.3, -0.4, -0.6 + i * 0.3, 0.4));
    for (let i = 1; i < 5; i++) l = l.concat(line(-0.6, -0.4 + i * 0.16, 0.6, -0.4 + i * 0.16));
    return l;
  },
  chat() {
    let l = roundRect(-0.55, -0.3, 1.1, 0.6, 0.14, true);
    for (let i = 0; i < 3; i++) l = l.concat(line(-0.4, 0.14 - i * 0.14, 0.4 - i * 0.18, 0.14 - i * 0.14));
    return l;
  },
  chat2() {
    let l = roundRect(-0.4, -0.22, 0.8, 0.44, 0.12, true);
    for (let i = 0; i < 2; i++) l = l.concat(line(-0.28, 0.07 - i * 0.14, 0.26 - i * 0.2, 0.07 - i * 0.14));
    return l;
  },
  barcode() {
    const R = rng(3); let l = [], x = -0.5;
    while (x < 0.5) { l = l.concat(line(x, -0.3, x, 0.3)); x += 0.025 + R() * 0.06; }
    return l;
  },
  receipt() {
    const p = [[-0.3, 0.5], [0.3, 0.5], [0.3, -0.45]];
    for (let i = 0; i <= 8; i++) p.push([0.3 - i * 0.075, i % 2 ? -0.5 : -0.45]);
    p.push([-0.3, 0.5]);
    let l = [p];
    for (let i = 0; i < 5; i++) l = l.concat(line(-0.2, 0.35 - i * 0.14, i === 4 ? 0.2 : 0.1 - (i % 2) * 0.08, 0.35 - i * 0.14));
    return l.concat(line(0.12, 0.35 - 4 * 0.14 + 0.14, 0.2, 0.35 - 3 * 0.14));
  },
  kanban() {
    let l = [];
    for (let c = 0; c < 3; c++) {
      l = l.concat(rect(-0.6 + c * 0.42, -0.4, 0.36, 0.8));
      for (let k = 0; k < 3 - c; k++) l = l.concat(rect(-0.56 + c * 0.42, 0.22 - k * 0.2, 0.28, 0.13));
    }
    return l;
  },
  check() {
    const p = []; for (let k = 0; k <= 40; k++) { const a = 2 * Math.PI * k / 40; p.push([0.3 * Math.cos(a), 0.3 * Math.sin(a)]); }
    return [p, [[-0.14, 0.0], [-0.03, -0.12], [0.16, 0.12]]];
  },
};

export function buildFragments() {
  const R = rng(11), kinds = ['sheet', 'chat', 'barcode', 'receipt', 'kanban', 'chat2', 'sheet', 'check', 'chat', 'receipt', 'barcode', 'chat2', 'kanban', 'sheet'];
  return kinds.map((k, i) => {
    const th = R() * 6.283, ph = (R() - 0.5) * 1.6;
    const dir = [Math.cos(th) * Math.cos(ph), Math.sin(ph), Math.sin(th) * Math.cos(ph)];
    return {
      kind: k, lines: SHAPES[k](), dir, r0: 5.5 + R() * 3.5,
      home: [(R() - 0.5) * 3.2, (R() - 0.5) * 2.4, (R() - 0.5) * 6],     // where it sits inside the tangle
      rot: [R() * 6.283, R() * 6.283, R() * 6.283], spin: [(R() - 0.5) * 0.5, (R() - 0.5) * 0.5, (R() - 0.5) * 0.3],
      size: 0.55 + R() * 0.45, fade: 15.2 + R() * 2.5,
    };
  });
}
