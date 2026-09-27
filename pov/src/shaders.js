import * as THREE from 'three';

const NOISE = /* glsl */`
float h21(vec2 p){ p = fract(p * vec2(123.34, 456.21)); p += dot(p, p + 45.32); return fract(p.x * p.y); }
float vnoise(vec2 p){ vec2 i = floor(p), f = fract(p); f = f * f * (3. - 2. * f);
  return mix(mix(h21(i), h21(i + vec2(1, 0)), f.x), mix(h21(i + vec2(0, 1)), h21(i + vec2(1, 1)), f.x), f.y); }
float fbm(vec2 p){ float v = 0., a = .5; for (int i = 0; i < 5; i++){ v += a * vnoise(p); p = p * 2.03 + 17.1; a *= .5; } return v; }
`;

// A petal painted in watercolour: pigment that granulates and pools at the edge, fine veins,
// and a wet wipe that brings the paint in from the base.
export function petalMaterial(colors, seed) {
  return new THREE.ShaderMaterial({
    transparent: true, depthWrite: false, side: THREE.DoubleSide,
    uniforms: {
      uBase: { value: new THREE.Color(colors[0]) }, uMid: { value: new THREE.Color(colors[1]) },
      uTip: { value: new THREE.Color(colors[2]) }, uEdge: { value: new THREE.Color(colors[3]) },
      uReveal: { value: 0 }, uOpacity: { value: 1 }, uGain: { value: 1 }, uSeed: { value: seed },
    },
    vertexShader: /* glsl */`
      attribute vec2 aUV; varying vec2 vUV; varying vec3 vPos;
      void main(){ vUV = aUV; vec4 mv = modelViewMatrix * vec4(position, 1.); vPos = mv.xyz; gl_Position = projectionMatrix * mv; }`,
    fragmentShader: /* glsl */`
      uniform vec3 uBase, uMid, uTip, uEdge; uniform float uReveal, uOpacity, uGain, uSeed;
      varying vec2 vUV; varying vec3 vPos;
      ${NOISE}
      void main(){
        float u = vUV.x, e = abs(vUV.y);                       // u along the petal, e: 0 spine .. 1 edge
        vec2 q = vec2(u * 3., vUV.y * 1.4) + uSeed * 7.3;
        float n = fbm(q * 2.2), gran = fbm(q * 18.), bloom = fbm(q * .9 + 3.);
        vec3 col = mix(uBase, uMid, smoothstep(.0, .55, u + (bloom - .5) * .35));
        col = mix(col, uTip, smoothstep(.45, 1., u + (n - .5) * .3));
        col = mix(col, uEdge, smoothstep(.55, 1., e) * .55 * (.6 + .8 * bloom));
        // pigment pools at the edge of the wash, and granulates in the paper
        float pool = smoothstep(.78, .97, e + (n - .5) * .12);
        col *= mix(.78 + .35 * gran, 1., .35) * (1. - .28 * pool) + .35 * pool * col;
        // veins
        float v = pow(abs(sin(vUV.y * 9.5 + n * 1.3 + u * 1.2)), 36.) * smoothstep(.05, .5, u) * (1. - e);
        col += v * .22 * uTip;
        col *= .75 + .5 * smoothstep(1.1, .0, u);                // brighter toward the heart
        // wet wipe from the base, with a darker drying front
        float r = uReveal * 1.25, edge = u + (n - .5) * .22 + e * .08;
        float m = 1. - smoothstep(r - .1, r, edge);
        float front = smoothstep(r - .14, r - .04, edge) * m;
        col = mix(col, col * .6, front * .8);
        float a = m * uOpacity * (.82 + .18 * gran) * smoothstep(1., .96, e);
        gl_FragColor = vec4(col * uGain, a);
      }`,
  });
}

// The last pass, in display space: text overlay, glitch, lens, flash, vignette, grain.
export const FinalShader = {
  uniforms: {
    tDiffuse: { value: null }, tOver: { value: null }, uRes: { value: new THREE.Vector2(1920, 1080) },
    uFrame: { value: 0 }, uGlitch: { value: 0 }, uSeed: { value: 0 }, uSplit: { value: 0 }, uFlash: { value: 0 },
    uFade: { value: 1 }, uScan: { value: -1 }, uGrain: { value: .045 }, uTint: { value: new THREE.Vector3(1, 1, 1) },
  },
  vertexShader: /* glsl */`varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.); }`,
  fragmentShader: /* glsl */`
    uniform sampler2D tDiffuse, tOver; uniform vec2 uRes; uniform float uFrame, uGlitch, uSeed, uSplit, uFlash, uFade, uScan, uGrain;
    uniform vec3 uTint; varying vec2 vUv;
    float h(float x){ return fract(sin(x * 91.3458) * 47453.5453); }
    float h2(vec2 p){ return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453); }
    vec4 over(vec2 uv){ return texture2D(tOver, uv); }
    vec3 scene(vec2 uv){ return texture2D(tDiffuse, uv).rgb; }
    vec3 comp(vec2 uv){ vec4 o = over(uv); return mix(scene(uv), o.rgb, o.a); }
    void main(){
      vec2 uv = vUv; float g = uGlitch, s = uSeed;
      bool on = g > .005;             // float32 hashes hit exactly 0 now and then: never let "0 < tiny" glitch
      // horizontal slices tear sideways
      float rows = mix(14., 70., h(s + 1.));
      float band = floor(uv.y * rows);
      if (on && h(band + s * 13.1) < g * .6) uv.x += (h(band * 7.1 + s) - .5) * .3 * g;
      // blocks jump
      vec2 grid = vec2(16., 9.) * (1. + floor(h(s * 3.7) * 3.));
      vec2 b = floor(uv * grid);
      float hb = h2(b + s);
      if (on && hb < g * .16) uv = fract(uv + (vec2(h2(b + s + 2.), h2(b - s)) - .5) * .12 * g);
      // scan line
      if (uScan >= 0.) { float d = abs(uv.y - uScan); if (d < .004) uv.x += .01 * sin(uv.y * 900.); }
      // lens: chromatic aberration growing to the edges, plus glitch split
      vec2 c = uv - .5; float r2 = dot(c, c);
      vec2 sp = c * (.0035 * r2 * 4.) + vec2(uSplit / uRes.x + g * .012, 0.);
      vec3 col = vec3(comp(uv + sp).r, comp(uv).g, comp(uv - sp).b);
      // corrupted blocks: channel swaps and posterise, the petalcore sparkle
      float hc = h2(b * 1.7 + s * 5.);
      if (on && hc < g * .07) col = col.gbr;
      else if (on && hc < g * .09 && g > .3) col = floor(col * 4.) / 4. + vec3(.2, .04, .16);
      if (uScan >= 0.) col += vec3(.6, .9, .8) * smoothstep(.003, 0., abs(vUv.y - uScan)) * .6;
      col = col * uTint + uFlash;
      col *= 1. - .38 * smoothstep(.25, 1.1, length(c * vec2(1.25, 1.)) * 1.2);   // vignette
      col += (h2(vUv * uRes + uFrame * 1.713) - .5) * uGrain;                          // grain
      gl_FragColor = vec4(col * uFade, 1.);
    }`,
};

export function glowTexture() {
  const c = document.createElement('canvas'); c.width = c.height = 256;
  const x = c.getContext('2d'), g = x.createRadialGradient(128, 128, 0, 128, 128, 128);
  g.addColorStop(0, 'rgba(255,255,255,1)'); g.addColorStop(.18, 'rgba(255,240,250,.55)');
  g.addColorStop(.45, 'rgba(190,170,255,.16)'); g.addColorStop(1, 'rgba(0,0,0,0)');
  x.fillStyle = g; x.fillRect(0, 0, 256, 256);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
}
