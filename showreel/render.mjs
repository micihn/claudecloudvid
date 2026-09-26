// Render the showreel to JPEG frames with headless Chromium.
//   node render.mjs frames            -> all 1200 frames into ./frames (parallel)
//   node render.mjs stills 2.1 8.4    -> single stills into ./stills
import { chromium } from 'playwright';
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';

const ROOT = path.dirname(new URL(import.meta.url).pathname);
const FPS = 60, DUR = 20;
const [mode = 'frames', ...args] = process.argv.slice(2);

const types = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.woff2': 'font/woff2', '.png': 'image/png' };
const server = http.createServer((req, res) => {
  const f = path.join(ROOT, decodeURIComponent(req.url.split('?')[0]));
  fs.readFile(f, (err, data) => {
    if (err) { res.writeHead(404); res.end(); return; }
    res.writeHead(200, { 'Content-Type': types[path.extname(f)] || 'application/octet-stream' }); res.end(data);
  });
}).listen(0);
const url = `http://127.0.0.1:${server.address().port}/index.html?capture=1`;

const browser = await chromium.launch({ args: ['--disable-gpu-vsync', '--force-color-profile=srgb'] });
async function page() {
  const p = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  p.on('pageerror', e => console.error('pageerror', e));
  p.on('console', m => m.type() === 'error' && console.error(m.text()));
  await p.goto(url);
  await p.waitForFunction(() => window.__ready === true, null, { timeout: 120000 });
  return p;
}
const save = (file, dataUrl) => fs.writeFileSync(file, Buffer.from(dataUrl.split(',')[1], 'base64'));

if (mode === 'stills') {
  fs.mkdirSync(path.join(ROOT, 'stills'), { recursive: true });
  const p = await page();
  for (const a of args) save(path.join(ROOT, 'stills', `t${(+a).toFixed(2)}.jpg`), await p.evaluate(t => window.renderFrame(t, 0.9), +a));
} else {
  const out = path.join(ROOT, 'frames'); fs.mkdirSync(out, { recursive: true });
  const total = FPS * DUR, workers = +(args[0] || Math.max(1, os.cpus().length));
  let next = 0, done = 0; const t0 = Date.now();
  await Promise.all(Array.from({ length: workers }, async () => {
    const p = await page();
    while (next < total) {
      const f = next++;
      save(path.join(out, `${String(f).padStart(5, '0')}.jpg`), await p.evaluate(t => window.renderFrame(t, 0.96), f / FPS));
      if (++done % 60 === 0) console.log(`${done}/${total}  ${((Date.now() - t0) / 1000).toFixed(0)}s`);
    }
  }));
}
await browser.close(); server.close();
