// small deterministic helpers: the film must render the same on every run and in any frame order
export function rng(seed) {
  let a = seed >>> 0;
  return () => { a = (a + 0x6D2B79F5) >>> 0; let t = a; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
}
export const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
export const lerp = (a, b, x) => a + (b - a) * x;
export const smooth = x => { x = clamp(x); return x * x * (3 - 2 * x); };
export const smoother = x => { x = clamp(x); return x * x * x * (x * (x * 6 - 15) + 10); };
export const easeOut = (x, p = 3) => 1 - Math.pow(1 - clamp(x), p);
export const easeIn = (x, p = 3) => Math.pow(clamp(x), p);
export const ramp = (t, a, b) => clamp((t - a) / (b - a));
// a pulse that jumps to 1 at t0 and decays with time constant tau
export const pulse = (t, t0, tau) => (t < t0 ? 0 : Math.exp(-(t - t0) / tau));
export const hex = h => [parseInt(h.slice(1, 3), 16) / 255, parseInt(h.slice(3, 5), 16) / 255, parseInt(h.slice(5, 7), 16) / 255];
export function mixc(a, b, x) { return [lerp(a[0], b[0], x), lerp(a[1], b[1], x), lerp(a[2], b[2], x)]; }
// piecewise gradient over stops [[u, [r,g,b]], ...]
export function grad(stops, u) {
  u = clamp(u);
  for (let i = 1; i < stops.length; i++) if (u <= stops[i][0]) return mixc(stops[i - 1][1], stops[i][1], (u - stops[i - 1][0]) / (stops[i][0] - stops[i - 1][0] || 1));
  return stops[stops.length - 1][1];
}
