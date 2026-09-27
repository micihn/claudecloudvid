// PORTOKO — Point of View. 30 s, 1920x1080, 30 fps. window.renderFrame(t) draws the frame at time t.
//
//   0.00  tangle   threads and fragments of a business (sheets, chats, a barcode) knot together
//   6.97  Look.    silence, five clicks, five characters
//   8.05  search   every hit jumps to another point of view on the knot, glitching
//  12.87  orbit    one continuous move toward the one true angle, while the knot slowly untangles
//  22.90  lock     from here the tangle IS a flower. It flattens, is painted, and blooms
//  26.72  exhale   the petals fly; a glitch burst opens onto the wordmark
//  29.12  silence  everything holds
import * as THREE from 'three';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { ShaderPass } from 'three/addons/postprocessing/ShaderPass.js';
import { LineSegments2 } from 'three/addons/lines/LineSegments2.js';
import { LineSegmentsGeometry } from 'three/addons/lines/LineSegmentsGeometry.js';
import { LineMaterial } from 'three/addons/lines/LineMaterial.js';
import { T, TICKS, FPS } from './timeline.js';
import { rng, clamp, lerp, smooth, smoother, easeOut, easeIn, ramp, pulse, hex, mixc, grad } from './util.js';
import { EYE, buildFlower, tanglePoint, petalPoint } from './flower.js';
import { buildFragments } from './fragments.js';
import { petalMaterial, FinalShader, glowTexture } from './shaders.js';
import { loadOverlay, drawOverlay } from './overlay.js';

const W = 1920, H = 1080;
const lin = c => c.map(v => Math.pow(v, 2.2));           // sRGB -> linear for vertex colours
const LINE_GAIN = 0.1;                                    // hundreds of additive threads overlap

// ------------------------------------------------------------------ renderer + post
const renderer = new THREE.WebGLRenderer({ antialias: false, preserveDrawingBuffer: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(1); renderer.setSize(W, H);
renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.0;
document.body.appendChild(renderer.domElement);
const scene = new THREE.Scene(); scene.background = new THREE.Color(0x030304);
const camera = new THREE.PerspectiveCamera(32, W / H, 0.05, 200);
const target = new THREE.WebGLRenderTarget(W, H, { type: THREE.HalfFloatType, samples: 4 });
const composer = new EffectComposer(renderer, target);
composer.addPass(new RenderPass(scene, camera));
const bloom = new UnrealBloomPass(new THREE.Vector2(W, H), 0.8, 0.55, 0.12); composer.addPass(bloom);
composer.addPass(new OutputPass());
const final = new ShaderPass(FinalShader); composer.addPass(final);
const overTex = new THREE.CanvasTexture(document.createElement('canvas')); overTex.colorSpace = THREE.SRGBColorSpace;

// ------------------------------------------------------------------ the flower as threads
const F = buildFlower();
const TH = F.threads;
let nSeg = 0; TH.forEach(th => { th.seg0 = nSeg; nSeg += th.pts.length - 1; });
const lineGeo = new LineSegmentsGeometry();
lineGeo.setPositions(new Float32Array(nSeg * 6)); lineGeo.setColors(new Float32Array(nSeg * 6));
const lineMat = new LineMaterial({ linewidth: 1.6, vertexColors: true, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, worldUnits: false });
lineMat.resolution.set(W, H);
const lines = new LineSegments2(lineGeo, lineMat); lines.frustumCulled = false; scene.add(lines);
const LP = lineGeo.attributes.instanceStart.data.array, LC = lineGeo.attributes.instanceColorStart.data.array;

// colour of each thread: calm white-green while tangled, petalcore once it untangles
const CH = [[0, hex('#e6fbff')], [0.5, hex('#c6f4dc')], [1, hex('#3ae59a')]];
TH.forEach(th => {
  th.cChaos = grad(CH, th.hue);
  if (th.kind === 'petal') {
    const p = F.petals[th.petal];
    th.cOrder = p.layer === 0 ? grad([[0, hex('#5ee0e8')], [0.55, hex('#9d8bff')], [1, hex('#ff7ad9')]], th.depth)
                              : grad([[0, hex('#ff7ad9')], [0.6, hex('#ff8a80')], [1, hex('#ffe27a')]], th.depth);
  } else th.cOrder = th.kind === 'ring' ? hex('#c6e84a') : hex('#ffe27a');
});
// order of appearance in the opening: the first petal outline starts it, then the rest
const order = TH.map((th, i) => i).sort((a, b) => TH[a].start - TH[b].start);
order.splice(order.indexOf(0), 1); order.unshift(0);
order.forEach((i, r) => { TH[i].appear = r === 0 ? 0.1 : 0.55 + 5.55 * Math.pow(r / order.length, 0.62); });

// ------------------------------------------------------------------ fragments of a tangled business
const FR = buildFragments();
let fSeg = 0; FR.forEach(f => { f.seg0 = fSeg; f.lines.forEach(l => fSeg += l.length - 1); });
const fragGeo = new LineSegmentsGeometry();
fragGeo.setPositions(new Float32Array(fSeg * 6)); fragGeo.setColors(new Float32Array(fSeg * 6));
const fragMat = new LineMaterial({ linewidth: 1.3, vertexColors: true, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false });
fragMat.resolution.set(W, H);
const frags = new LineSegments2(fragGeo, fragMat); frags.frustumCulled = false; scene.add(frags);
const FP = fragGeo.attributes.instanceStart.data.array, FC = fragGeo.attributes.instanceColorStart.data.array;

// ------------------------------------------------------------------ painted petals
const GU = 48, GV = 14;
const PALETTE = [
  ['#0f4f3f', '#9d8bff', '#ff7ad9', '#5ee0e8'],     // outer: deep green heart, lilac, pink tips, cyan edge
  ['#3a1f5c', '#ff7ad9', '#ffe27a', '#ff8a80'],     // inner: violet heart, pink, warm yellow tips, coral edge
];
const petalMeshes = F.petals.map((p, i) => {
  const g = new THREE.BufferGeometry();
  const pos = new Float32Array(GU * GV * 3), uv = new Float32Array(GU * GV * 2), idx = [];
  for (let a = 0; a < GU; a++) for (let b = 0; b < GV; b++) { const k = a * GV + b; uv[k * 2] = a / (GU - 1); uv[k * 2 + 1] = b / (GV - 1) * 2 - 1; }
  for (let a = 0; a < GU - 1; a++) for (let b = 0; b < GV - 1; b++) { const k = a * GV + b; idx.push(k, k + GV, k + 1, k + 1, k + GV, k + GV + 1); }
  g.setAttribute('position', new THREE.BufferAttribute(pos, 3)); g.setAttribute('aUV', new THREE.BufferAttribute(uv, 2)); g.setIndex(idx);
  const m = new THREE.Mesh(g, petalMaterial(PALETTE[p.layer], i * 0.37 + 1.3));
  m.frustumCulled = false; m.renderOrder = p.layer ? 3 : 2; scene.add(m);
  return m;
});
// small loose petals for the end
const R = rng(99);
const loose = Array.from({ length: 26 }, (_, i) => {
  const p = F.petals[i % F.petals.length], g = new THREE.BufferGeometry();
  const pos = new Float32Array(GU * GV * 3), s0 = { bloom: 0.6, open: 1, spin: 0 }, v = [0, 0, 0];
  const pl = { ...p, phi: 0 };
  for (let a = 0; a < GU; a++) for (let b = 0; b < GV; b++) {
    const u = a / (GU - 1), hw = F.petalHalfWidth(p.W, u), k = (a * GV + b) * 3;
    petalPoint(pl, u * p.L - 0.06, (b / (GV - 1) * 2 - 1) * hw, s0, v); pos[k] = v[0] - p.L / 2; pos[k + 1] = v[1]; pos[k + 2] = v[2];
  }
  g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  g.setAttribute('aUV', petalMeshes[0].geometry.attributes.aUV); g.setIndex(petalMeshes[0].geometry.index);
  const m = new THREE.Mesh(g, petalMaterial(PALETTE[i % 2], 5 + i * 0.61)); m.frustumCulled = false; m.renderOrder = 4;
  m.material.uniforms.uReveal.value = 1; scene.add(m);
  const th = R() * 6.283, el = (R() - 0.5) * 1.6, r = 2.5 + R() * 6;
  return { m, home: [Math.cos(th) * Math.cos(el) * r, Math.sin(el) * r * 0.6, Math.sin(th) * Math.cos(el) * r * 0.6 - 1],
    vel: [(R() - 0.5) * 0.5, 0.15 + R() * 0.25, (R() - 0.5) * 0.4], rot: [R() * 6, R() * 6, R() * 6], spin: [(R() - 0.5), (R() - 0.5), (R() - 0.5)], s: 0.28 + R() * 0.35 };
});

// ------------------------------------------------------------------ dust and the heart's glow
const dustN = 2600, dp = new Float32Array(dustN * 3), RD = rng(5);
for (let i = 0; i < dustN; i++) {
  const r = 6 + Math.pow(RD(), 0.7) * 40, th = RD() * 6.283, ph = Math.acos(2 * RD() - 1);
  dp[i * 3] = r * Math.sin(ph) * Math.cos(th); dp[i * 3 + 1] = r * Math.cos(ph) * 0.7; dp[i * 3 + 2] = r * Math.sin(ph) * Math.sin(th);
}
const dustGeo = new THREE.BufferGeometry(); dustGeo.setAttribute('position', new THREE.BufferAttribute(dp, 3));
const dustMat = new THREE.PointsMaterial({ size: 1.6, sizeAttenuation: false, color: 0xcfe9ff, transparent: true, opacity: 0.35, blending: THREE.AdditiveBlending, depthWrite: false });
const dust = new THREE.Points(dustGeo, dustMat); scene.add(dust);
const glow = new THREE.Sprite(new THREE.SpriteMaterial({ map: glowTexture(), blending: THREE.AdditiveBlending, depthWrite: false, transparent: true }));
glow.renderOrder = 5; scene.add(glow);
const spark = new THREE.Sprite(new THREE.SpriteMaterial({ map: glow.material.map, color: 0xdfffee, blending: THREE.AdditiveBlending, depthWrite: false, transparent: true }));
spark.renderOrder = 6; scene.add(spark);                  // the tip of the first thread as it draws itself

// ------------------------------------------------------------------ camera
function sph(az, el, r, tg = [0, 0, 0]) {       // az = 0, el = 0 is the true point of view (on +z)
  return [tg[0] + r * Math.cos(el) * Math.sin(az), tg[1] + r * Math.sin(el), tg[2] + r * Math.cos(el) * Math.cos(az)];
}
function setCam(pos, tg, fov, roll = 0) {
  camera.position.set(...pos); camera.up.set(0, 1, 0); camera.lookAt(...tg); camera.rotateZ(roll);
  camera.fov = fov; camera.updateProjectionMatrix();
}
const tp = [0, 0, 0];
// search shots after the first hit: position, target, fov, roll, drift per second
const SHOTS = [
  { p: [1.6, 0.9, 4.2], tg: [0.3, 0.2, 1.4], fov: 30, roll: 0.25, d: [-0.12, 0.03, -0.05] },
  { p: [0.4, 10.5, 0.8], tg: [0, 0, 0], fov: 34, roll: 1.1, d: [0.2, 0, 0.1] },
  { p: [-8.5, -1.8, -2.5], tg: [0, 0.3, 0], fov: 24, roll: -0.12, d: [0, 0.18, 0.25] },
  { p: [0.25, 0.3, -11], tg: [0, 0, 3], fov: 42, roll: 0.5, d: [0, 0, 0.35] },
  { frag: 0, fov: 28, roll: -0.2 },
  { p: [9, 4.2, 7.5], tg: [0, 0, 0], fov: 30, roll: 0.06, d: [-0.25, 0, 0.1] },
];
let lockPos = null;
function cameraAt(t) {
  if (t < T.cut1) {                                     // the opening: follow the first thread, pull back, spin up
    const k = t / T.cut1, th = TH[0], head = Math.floor(clamp((t - th.appear) / 1.4) * (th.pts.length - 1));
    tanglePoint(F, th, head, FLAT, { depth: 1, lat: 1 }, t, tp);
    const tg = [0, 1, 2].map(a => lerp(tp[a], 0, smooth(ramp(t, 0.9, 4.2))));
    const d = t < 6.1 ? lerp(2.2, 14, smooth(t / 6.1)) : lerp(14, 7, easeIn(ramp(t, 6.1, T.cut1), 2));
    const az = 1.25 + 1.3 * k + 1.2 * Math.pow(k, 4), el = 0.28 + 0.18 * Math.sin(k * 3);
    return { pos: sph(az, el, d, tg), tg, fov: 32, roll: 0.12 * Math.sin(t * 0.9) + 0.25 * Math.pow(k, 5) };
  }
  if (t < T.orbit) {                                    // the search
    const i = Math.max(0, T.shots.filter(c => t >= c).length - 1), s = SHOTS[i], dt = t - T.shots[i];
    if (s.frag !== undefined) {
      const f = FR[s.frag], hp = fragPos(f, t);
      return { pos: [hp[0] + 1.1 - 0.1 * dt, hp[1] + 0.45, hp[2] + 1.7 - 0.2 * dt], tg: hp, fov: s.fov, roll: s.roll, shot: i + 1 };
    }
    return { pos: s.p.map((v, a) => v + s.d[a] * dt), tg: s.tg, fov: s.fov, roll: s.roll, shot: i + 1 };
  }
  if (t < T.align + 1e-6) {                             // the orbit into the true point of view
    const o = ramp(t, T.orbit, T.align), e = 0.45 * smoother(o) + 0.55 * easeOut(o, 2.6);
    const sway = (1 - e) * 0.05;
    const az = lerp(-2.25, 0, e) + sway * Math.sin(t * 1.3), el = lerp(-0.45, 0, e) + sway * Math.sin(t * 0.9 + 1);
    return { pos: sph(az, el, lerp(7.2, 10, smooth(o))), tg: [0, 0, 0], fov: lerp(38, 32, smooth(o)), roll: 0.35 * (1 - e), shot: 7 };
  }
  if (t < T.cut2) {                                     // the bloom: rise off the axis and push in
    const p = ramp(t, T.align + 0.15, T.cut2), e = smoother(p), push = easeIn(ramp(t, T.climax - 0.6, T.cut2), 2.2);
    const tg = [0, 0, 0.35 * e];
    return { pos: sph(0.34 * e, 0.52 * e, lerp(10, 6.6, e) - 2.6 * push, tg), tg, fov: 32 + 4 * push, roll: -0.06 * e, shot: 7 };
  }
  if (!lockPos) lockPos = cameraAt(T.cut2 - 1e-4);      // the end holds the last view, pulled back a little
  const e = easeOut(ramp(Math.min(t, T.silence), T.cut2, T.silence), 2);
  const tg = lockPos.tg;
  return { pos: lockPos.pos.map((v, a) => v + (v - tg[a]) * 0.35 * e), tg, fov: lockPos.fov, roll: lockPos.roll };
}
const FLAT = { bloom: 0, open: 1, spin: 0, stamen: 0 };

// ------------------------------------------------------------------ per-frame state
function flowerState(t) {
  if (t < T.align) return FLAT;
  return {
    bloom: smooth(ramp(t, T.paint - 0.1, 25.7)) + 0.35 * smooth(ramp(t, T.climax, T.cut2)),
    open: 1, spin: 0.3 * Math.pow(ramp(t, T.align, T.cut2), 1.3), stamen: smooth(ramp(t, 24.3, 25.9)),
  };
}
function tangleAmount(t) {
  if (t < T.orbit) return { lat: 1, depth: 1 };
  return { lat: Math.pow(1 - smooth(ramp(t, 13.4, 22.45)), 1.15), depth: 1 - smoother(ramp(t, T.flatten, T.paint)) };
}
function fragPos(f, t) {
  if (t < T.cut1) { const k = easeIn(t / T.cut1, 1.5); const r = lerp(f.r0, 2.2, k); return f.dir.map(v => v * r); }
  return f.home.map((v, a) => v + 0.12 * Math.sin(t * 0.4 + a + f.rot[a]));
}

function updateThreads(t) {
  const fs = flowerState(t), g = tangleAmount(t), p = [0, 0, 0], q = [0, 0, 0];
  const opening = t < T.cut1, k = t / T.cut1;
  const orderMix = smooth(ramp(t, 15.5, T.align));
  const early = opening ? lerp(7, 1, smooth(ramp(t, 0.3, 3.8))) : 1;     // while there are few threads, each is bright
  const gain = opening ? 0.3 + 1.1 * Math.pow(k, 3)
    : t < T.orbit ? 0.75
    : t < T.align ? 0.8 + 1.7 * smooth(ramp(t, 14.5, T.align))            // brighter as it untangles, with the build
    : lerp(2.6, 1.3, smooth(ramp(t, T.paint, 25.2))) + 4 * pulse(t, T.align, 0.35);
  for (const th of TH) {
    const n = th.pts.length - 1;
    const frac = opening ? clamp((t - th.appear) / 1.4) : 1;
    const c = mixc(th.cChaos, th.cOrder, orderMix), cl = lin(c);
    let prev = tanglePoint(F, th, 0, fs, g, t, p).slice();
    for (let s = 0; s < n; s++) {
      tanglePoint(F, th, s + 1, fs, g, t, q);
      const o = (th.seg0 + s) * 6;
      LP[o] = prev[0]; LP[o + 1] = prev[1]; LP[o + 2] = prev[2]; LP[o + 3] = q[0]; LP[o + 4] = q[1]; LP[o + 5] = q[2];
      prev[0] = q[0]; prev[1] = q[1]; prev[2] = q[2];
      const u = s / n, vis = u < frac ? 1 : 0;
      const head = opening && frac < 1 ? 1.4 * Math.exp(-(frac - u) * n / 8) : 0;      // the hot drawing tip
      const b = vis * ((gain * LINE_GAIN * early) + head) * (th.kind === 'stamen' ? 1.3 : 1);
      LC[o] = cl[0] * b; LC[o + 1] = cl[1] * b; LC[o + 2] = cl[2] * b; LC[o + 3] = cl[0] * b; LC[o + 4] = cl[1] * b; LC[o + 5] = cl[2] * b;
    }
  }
  lineGeo.attributes.instanceStart.data.needsUpdate = true; lineGeo.attributes.instanceColorStart.data.needsUpdate = true;
  lineMat.linewidth = t < T.cut1 ? 1.1 + 0.6 * k : t > T.align ? 1.6 : 1.25;
}

const e3 = new THREE.Euler(), m4 = new THREE.Matrix4(), v3 = new THREE.Vector3();
function updateFrags(t) {
  const col = lin(hex('#e6fbff'));
  for (const f of FR) {
    const fade = t < T.cut1 ? smooth(ramp(t, 0.8, 2.2)) * 0.75 : (1 - smooth(ramp(t, f.fade, f.fade + 1.1))) * 0.8;
    const pos = fragPos(f, t), sc = f.size * (t < T.cut1 ? lerp(1.1, 0.7, t / T.cut1) : 0.85) * (1 - 0.6 * smooth(ramp(t, f.fade, f.fade + 1.1)));
    e3.set(f.rot[0] + f.spin[0] * t, f.rot[1] + f.spin[1] * t, f.rot[2] + f.spin[2] * t);
    m4.makeRotationFromEuler(e3).scale(v3.set(sc, sc, sc)).setPosition(...pos);
    let o = f.seg0 * 6;
    for (const l of f.lines) for (let s = 0; s < l.length - 1; s++, o += 6) {
      for (let e = 0; e < 2; e++) {
        v3.set(l[s + e][0], l[s + e][1], 0).applyMatrix4(m4);
        FP[o + e * 3] = v3.x; FP[o + e * 3 + 1] = v3.y; FP[o + e * 3 + 2] = v3.z;
        FC[o + e * 3] = col[0] * fade; FC[o + e * 3 + 1] = col[1] * fade; FC[o + e * 3 + 2] = col[2] * fade;
      }
    }
  }
  fragGeo.attributes.instanceStart.data.needsUpdate = true; fragGeo.attributes.instanceColorStart.data.needsUpdate = true;
}

const petalFreeze = { done: false };
function updatePetals(t) {
  const fs = flowerState(Math.min(t, T.cut2 - 1e-4)), v = [0, 0, 0];
  F.petals.forEach((p, i) => {
    const m = petalMeshes[i], pos = m.geometry.attributes.position.array, U = m.material.uniforms;
    const rev = smooth(ramp(t, T.paint + 0.07 * i, T.paint + 1.35 + 0.07 * i));
    U.uReveal.value = rev; m.visible = rev > 0;
    U.uGain.value = 0.85 + 0.45 * smooth(ramp(t, T.climax, T.cut2));
    if (t < T.cut2) {
      for (let a = 0; a < GU; a++) for (let b = 0; b < GV; b++) {
        const u = a / (GU - 1), hw = F.petalHalfWidth(p.W, u), k = (a * GV + b) * 3;
        petalPoint(p, u * p.L, (b / (GV - 1) * 2 - 1) * hw * 0.985, fs, v); pos[k] = v[0]; pos[k + 1] = v[1]; pos[k + 2] = v[2];
      }
      m.geometry.attributes.position.needsUpdate = true; m.position.set(0, 0, 0); m.rotation.set(0, 0, 0); m.userData.c = null;
    } else {
      // exhale: each petal lets go, drifting out and toward us, tumbling, slower and slower; holds in the silence
      if (!m.userData.c) {
        // the petal as it was at the cut, re-centred on itself so it can tumble (any frame order works)
        for (let a = 0; a < GU; a++) for (let b = 0; b < GV; b++) {
          const u = a / (GU - 1), hw = F.petalHalfWidth(p.W, u), k = (a * GV + b) * 3;
          petalPoint(p, u * p.L, (b / (GV - 1) * 2 - 1) * hw * 0.985, fs, v); pos[k] = v[0]; pos[k + 1] = v[1]; pos[k + 2] = v[2];
        }
        const c = [0, 0, 0]; for (let k = 0; k < pos.length; k += 3) { c[0] += pos[k]; c[1] += pos[k + 1]; c[2] += pos[k + 2]; }
        c.forEach((x, a) => c[a] = x / (pos.length / 3));
        for (let k = 0; k < pos.length; k += 3) { pos[k] -= c[0]; pos[k + 1] -= c[1]; pos[k + 2] -= c[2]; }
        m.geometry.attributes.position.needsUpdate = true;
        const r = Math.hypot(c[0], c[1]) || 1, Rr = rng(40 + i);
        m.userData = { c, vel: [c[0] / r * (1.6 + Rr()), c[1] / r * (1.6 + Rr()), 0.5 + Rr() * 1.1], spin: [Rr() - 0.5, Rr() - 0.5, Rr() - 0.5].map(x => x * 2.2) };
      }
      const d = m.userData, e = Math.min(t, T.silence) - T.cut2, s = 1.6 * (1 - Math.exp(-e / 1.1)) + 0.08 * e;
      m.position.set(d.c[0] + d.vel[0] * s, d.c[1] + d.vel[1] * s, d.c[2] + d.vel[2] * s);
      m.rotation.set(d.spin[0] * s, d.spin[1] * s, d.spin[2] * s);
      U.uGain.value = 0.9; U.uOpacity.value = 0.95 - 0.45 * smooth(ramp(t, T.burst2, T.burst2End + 0.4));
    }
  });
  loose.forEach((L, i) => {
    const on = t >= T.cut2, m = L.m; m.visible = on; if (!on) return;
    const e = Math.min(t, T.silence) - T.cut2, s = 1.4 * (1 - Math.exp(-e / 0.9)) + 0.18 * e;
    m.position.set(L.home[0] * (0.25 + 0.75 * (1 - Math.exp(-e / 0.8))) + L.vel[0] * s, L.home[1] * (0.25 + 0.75 * (1 - Math.exp(-e / 0.8))) + L.vel[1] * s, L.home[2] + L.vel[2] * s + 1.5);
    m.rotation.set(L.rot[0] + L.spin[0] * s, L.rot[1] + L.spin[1] * s, L.rot[2] + L.spin[2] * s); m.scale.setScalar(L.s);
    m.material.uniforms.uOpacity.value = 0.55 * smooth(ramp(t, T.cut2, T.cut2 + 0.15)); m.material.uniforms.uGain.value = 0.8;
  });
}

// ------------------------------------------------------------------ glitch, flash and the rest of the grade
function glitchAt(t) {
  let g = 0;
  for (const s of T.shots) g = Math.max(g, pulse(t, s, 0.09) * 0.9);
  if (t >= T.hit0 && t < 8.7) g = Math.max(g, 0.14 + (t >= T.step ? 0.1 : 0));      // the stepped tone
  for (const [s, a] of TICKS) g = Math.max(g, pulse(t, s, 0.05) * a);
  if (t >= T.burst1 && t < T.orbit + 0.05) g = 1;
  g = Math.max(g, pulse(t, T.orbit + 0.05, 0.12) * 0.7);
  if (t >= T.burst2 && t < T.burst2End) g = Math.max(g, 0.75 + 0.25 * Math.sin(t * 90));
  g = Math.max(g, pulse(t, T.burst2End, 0.08) * 0.6, pulse(t, T.glitch2, 0.06) * 0.7, pulse(t, T.cut2, 0.05) * 0.5);
  for (const f of FR) g = Math.max(g, (t > f.fade && t < f.fade + 0.07) ? 0.12 : 0);
  return g;
}

let ready = false;
window.renderFrame = function (t, quality = 0.95) {
  const frame = Math.round(t * FPS);
  const blackout = t >= T.cut1 && t < T.hit0;                            // "Look."
  const cam = cameraAt(t); setCam(cam.pos, cam.tg, cam.fov, cam.roll);
  lines.visible = !blackout && t < T.cut2;
  frags.visible = !blackout && t < 18.8;
  dust.visible = !blackout;
  if (lines.visible) updateThreads(t);
  if (frags.visible) updateFrags(t);
  updatePetals(blackout ? 0 : t);
  dustMat.opacity = t < T.cut1 ? 0.12 + 0.3 * t / T.cut1 : 0.32;

  // the heart of the flower: a light that swells into the climax, then an afterglow
  const heat = t < T.align || t >= T.cut2 ? 0 : 0.3 * smooth(ramp(t, T.paint, 25.3)) + 0.55 * easeIn(ramp(t, T.climax, T.cut2), 2.6);
  const after = t >= T.cut2 ? 0.7 * Math.exp(-(t - T.cut2) / 0.14) : 0;
  glow.visible = heat + after > 0.01; glow.material.opacity = Math.min(1, heat + after);
  glow.position.set(0, 0, 0.35); glow.scale.setScalar(1.4 + 2.2 * (heat + after));

  const th0 = TH[0], f0 = clamp((t - th0.appear) / 1.4);
  spark.visible = !blackout && t < 2.4;
  if (spark.visible) {
    tanglePoint(F, th0, Math.floor(f0 * (th0.pts.length - 1)), FLAT, { depth: 1, lat: 1 }, t, tp);
    spark.position.set(...tp); spark.scale.setScalar(0.22 + 0.05 * Math.sin(t * 23));
    spark.material.opacity = smooth(ramp(t, 0.05, 0.3)) * (1 - smooth(ramp(t, 1.5, 2.4)));
  }
  // bloom breathes with the music
  const k = t / T.cut1;
  bloom.strength = t < T.cut1 ? 0.5 + 1.5 * Math.pow(k, 3) : t < T.orbit ? 0.75 : t < T.cut2 ? 0.7 + 0.35 * smooth(ramp(t, 16, T.align)) + 0.5 * easeIn(ramp(t, T.climax, T.cut2), 2) : 0.6;
  bloom.strength *= 0.6; bloom.radius = 0.5; bloom.threshold = 0.45;

  // overlay text
  const hud = cam.shot ? hudFrom(cam, t) : null;
  overTex.image = drawOverlay(t, hud); overTex.needsUpdate = true;
  const U = final.uniforms;
  U.tOver.value = overTex; U.uFrame.value = frame;
  const g0 = glitchAt(t), g = g0 < 0.01 ? 0 : g0; U.uGlitch.value = g;     // tails of pulses are not glitches U.uSeed.value = (frame * 7.13) % 97;
  U.uSplit.value = 1.5 + 30 * g;
  U.uScan.value = t >= T.blip[0] && t < T.blip[1] ? 1 - ramp(t, T.blip[0], T.blip[1]) : -1;
  U.uFlash.value = t < T.cut2 ? 0.12 * easeIn(ramp(t, T.cut2 - 0.2, T.cut2), 2) : 0;
  const fadeIn = smooth(ramp(t, 0, 0.8));
  U.uFade.value = blackout ? 1 : fadeIn;
  U.uGrain.value = 0.05;
  composer.render();
  return renderer.domElement.toDataURL('image/jpeg', quality);
};

function hudFrom(cam, t) {
  const d = new THREE.Vector3(...cam.pos).sub(new THREE.Vector3(...cam.tg));
  const r = d.length(), el = Math.asin(d.y / r), az = Math.atan2(d.x, d.z);
  const align = t >= T.align ? 1 : 0;
  return { az: az * 180 / Math.PI, el: el * 180 / Math.PI, r, shot: cam.shot, align };
}

await loadOverlay();
window.renderFrame(0.5);
window.__ready = true;
