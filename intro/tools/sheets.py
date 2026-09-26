"""Tile the downloaded previews into contact sheets (sheet_N.jpg), labelled with id and search."""
import os, json
import numpy as np, cv2
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(HERE, 'previews')
tiles = []
for c in map(json.loads, open(os.path.join(HERE, 'candidates.jsonl'))):
    f = f"{P}/{c['id']}.jpg"
    im = cv2.imread(f) if os.path.exists(f) and os.path.getsize(f) else None
    if im is None: continue
    t = np.zeros((190, 250, 3), np.uint8); s = min(250 / im.shape[1], 172 / im.shape[0])
    r = cv2.resize(im, None, fx=s, fy=s); t[:r.shape[0], :r.shape[1]] = r
    cv2.putText(t, f"{c['id'][:6]} {c['q'][:22]}", (2, 186), 0, 0.37, (0, 255, 255), 1); tiles.append(t)
for i in range(0, len(tiles), 48):
    ch = tiles[i:i + 48]; ch += [np.zeros_like(tiles[0])] * ((-len(ch)) % 8)
    cv2.imwrite(f"{HERE}/sheet_{i // 48}.jpg", np.vstack([np.hstack(ch[j:j + 8]) for j in range(0, len(ch), 8)]), [cv2.IMWRITE_JPEG_QUALITY, 85])
print(len(tiles), 'previews')
