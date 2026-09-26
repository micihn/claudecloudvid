"""Detect the dominant circle in each candidate image and write circles.json + review sheets.

The film aligns every shot on one circle, so each image needs (cx, cy, r) in pixels.
Scoring: Hough proposals, re-scored by how strongly the image gradient points across the
circumference (a real rim) and how much of the rim is visible inside the image.
"""
import os, sys, json, glob
import numpy as np, cv2

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def rim_score(gx, gy, mag, cx, cy, r):
    h, w = mag.shape; th = np.linspace(0, 2 * np.pi, 360, endpoint=False)
    xs, ys = cx + r * np.cos(th), cy + r * np.sin(th)
    inside = (xs >= 1) & (xs < w - 1) & (ys >= 1) & (ys < h - 1)
    if inside.mean() < 0.55: return 0, inside.mean()
    xi, yi = xs[inside].astype(int), ys[inside].astype(int)
    nx, ny = np.cos(th[inside]), np.sin(th[inside])
    radial = np.abs(gx[yi, xi] * nx + gy[yi, xi] * ny) / (mag[yi, xi] + 1e-6)
    strength = mag[yi, xi] / (np.percentile(mag, 95) + 1e-6)
    support = np.mean((radial > 0.7) & (strength > 0.35))
    return support * inside.mean(), inside.mean()


def detect(path):
    im = cv2.imread(path)
    if im is None: return None
    s = 640 / max(im.shape[:2]); small = cv2.resize(im, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
    g = cv2.GaussianBlur(cv2.cvtColor(small, cv2.COLOR_BGR2GRAY), (0, 0), 2)
    gx, gy = cv2.Sobel(g, cv2.CV_32F, 1, 0), cv2.Sobel(g, cv2.CV_32F, 0, 1); mag = np.sqrt(gx ** 2 + gy ** 2)
    h, w = g.shape; mn = min(h, w)
    props = []
    for p2 in (40, 28, 18):
        c = cv2.HoughCircles(g, cv2.HOUGH_GRADIENT, dp=1.5, minDist=mn / 8, param1=90, param2=p2,
                             minRadius=int(mn * 0.18), maxRadius=int(mn * 0.75))
        if c is not None: props += [tuple(x) for x in c[0][:12]]
    best = None
    for cx, cy, r in props:
        sc, vis = rim_score(gx, gy, mag, cx, cy, r)
        sc *= (r / mn) ** 0.5            # prefer the big, hero circle
        if best is None or sc > best[0]: best = (sc, cx / s, cy / s, r / s, vis)
    return best


if __name__ == '__main__':
    out = {}
    files = sorted(glob.glob(os.path.join(HERE, 'images', '*.jpg')))
    for f in files:
        b = detect(f)
        if b: out[os.path.basename(f)[:-4]] = dict(score=round(float(b[0]), 3), cx=float(b[1]), cy=float(b[2]), r=float(b[3]), vis=round(float(b[4]), 2))
    json.dump(out, open(os.path.join(HERE, 'circles.json'), 'w'), indent=1)
    # review sheets: best first, circle drawn in
    keys = sorted(out, key=lambda k: -out[k]['score'])
    tiles = []
    for k in keys:
        im = cv2.imread(os.path.join(HERE, 'images', k + '.jpg')); c = out[k]
        cv2.circle(im, (int(c['cx']), int(c['cy'])), int(c['r']), (0, 0, 255), max(2, im.shape[1] // 250))
        t = cv2.resize(im, (256, int(256 * im.shape[0] / im.shape[1])))[:192] if im.shape[1] >= im.shape[0] else cv2.resize(im, (int(192 * im.shape[1] / im.shape[0]), 192))
        tile = np.zeros((192, 256, 3), np.uint8); tile[:t.shape[0], :t.shape[1]] = t
        cv2.putText(tile, f"{k} {c['score']:.2f}", (3, 12), 0, 0.38, (0, 255, 255), 1); tiles.append(tile)
    per = 48
    for i in range(0, len(tiles), per):
        ch = tiles[i:i + per]; ch += [np.zeros_like(tiles[0])] * ((-len(ch)) % 8)
        cv2.imwrite(os.path.join(HERE, f'review_{i // per}.jpg'), np.vstack([np.hstack(ch[j:j + 8]) for j in range(0, len(ch), 8)]), [cv2.IMWRITE_JPEG_QUALITY, 80])
    print(len(out), 'images;', sum(1 for k in out if out[k]['score'] > 0.25), 'with a confident circle')
