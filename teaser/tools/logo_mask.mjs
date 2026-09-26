// Export the vector wordmark (from showreel/scene.js) as a high-res white-on-black mask.
import { chromium } from 'playwright';
import http from 'node:http'; import fs from 'node:fs'; import path from 'node:path';
const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '../../showreel');
const srv = http.createServer((q, r) => fs.readFile(path.join(ROOT, q.url.split('?')[0]), (e, d) => { r.writeHead(e ? 404 : 200); r.end(d); })).listen(0);
const b = await chromium.launch(); const p = await b.newPage();
await p.goto(`http://127.0.0.1:${srv.address().port}/index.html?capture=1`);
await p.waitForFunction(() => window.__ready === true, null, { timeout: 120000 });
const url = await p.evaluate(() => {
  const c = document.createElement('canvas'); c.width = 4000; c.height = 900; const g = c.getContext('2d');
  g.fillStyle = '#000'; g.fillRect(0, 0, c.width, c.height);
  strokeLogo(g, { cx: 2000, cy: 450, s: 2.0 }, '#fff', () => 1);
  return c.toDataURL('image/png');
});
fs.writeFileSync(process.argv[2] || 'logo_mask.png', Buffer.from(url.split(',')[1], 'base64'));
await b.close(); srv.close();
