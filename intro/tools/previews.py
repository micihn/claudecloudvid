"""Fetch 330px previews of the candidates (all, or the ids given) for choosing shots; tools/sheets.py tiles them."""
import os, sys, json, time, re, urllib.error
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, '..', 'film', 'tools')); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from curl_get import http
P = os.path.join(HERE, 'previews'); os.makedirs(P, exist_ok=True)
cands = [json.loads(l) for l in open(os.path.join(HERE, 'candidates.jsonl'))]
have = lambda c: os.path.exists(f"{P}/{c['id']}.jpg") and os.path.getsize(f"{P}/{c['id']}.jpg") > 0
only = set(sys.argv[1:])                     # optional: just these ids
todo = [c for c in cands if c.get('thumb') and not have(c) and (not only or c['id'] in only)]
pause = 1.0
while todo:
    c = todo.pop(0)
    try:
        data = http(re.sub(r'/\d+px-', '/330px-', c['thumb']), tries=1)
        open(f"{P}/{c['id']}.jpg", 'wb').write(data); pause = max(1.0, pause * 0.8)
    except urllib.error.HTTPError as e:
        if e.code == 404: continue
        todo.append(c); pause = min(90, pause * 1.7); print(e.code, round(pause), len(todo), flush=True)
    time.sleep(pause)
print('done; now run tools/sheets.py')
