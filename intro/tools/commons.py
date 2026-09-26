"""Search public-domain / CC0 photos on Wikimedia Commons and fetch thumbnails, for the intro.

    commons.py search "lace doily" "leaf macro" ...   -> candidates.jsonl (appends)
    commons.py fetch [id ...]                          -> images/<id>.jpg (round-robin, backs off on 429)
Uses the film's search code; Commons asks bulk users to fetch thumbnails, not originals.
"""
import sys, os, re, json, time, urllib.error
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, '..', 'film', 'tools')); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from commons_images import search
from curl_get import http

CAND = os.path.join(HERE, 'candidates.jsonl')


def thumb_url(c):
    """Commons returns the original file for images narrower than 1920px, and originals are rate-limited;
    ask for a 1280px (or 960px) thumbnail of it instead."""
    m = re.match(r'(https://upload\.wikimedia\.org/wikipedia/commons)/(\w/\w\w)/([^?]+)', c['thumb'])
    if not m: return c['thumb']
    px = 1280 if c['w'] > 1280 else 960
    return f'{m.group(1)}/thumb/{m.group(2)}/{m.group(3)}/{px}px-{m.group(3)}'

if __name__ == '__main__':
    cmd, args = sys.argv[1], sys.argv[2:]
    if cmd == 'search':
        seen = {json.loads(l)['id'] for l in open(CAND)} if os.path.exists(CAND) else set()
        with open(CAND, 'a') as f:
            for q in args:
                res = [c for c in search(q, 30) if c['id'] not in seen]
                for c in res: f.write(json.dumps(c, ensure_ascii=False) + '\n'); seen.add(c['id'])
                print(f'{q}: {len(res)} new', flush=True); time.sleep(3)
    elif cmd == 'fetch':
        os.makedirs(os.path.join(HERE, 'images'), exist_ok=True)
        cands = {c['id']: c for c in map(json.loads, open(CAND))}
        todo = [i for i in (args or cands) if cands[i].get('thumb') and not os.path.exists(os.path.join(HERE, 'images', i + '.jpg'))]
        pause = 5
        while todo:
            i = todo.pop(0)
            try:
                data = http(thumb_url(cands[i]), tries=1)            # download before creating the file
                open(os.path.join(HERE, 'images', i + '.jpg'), 'wb').write(data)
                print('ok', i, cands[i]['q'], len(todo), 'left', flush=True); pause = max(5, pause * 0.8)
            except urllib.error.HTTPError as e:
                todo.append(i); pause = min(120, pause * 1.6); print(e.code, 'backing off', round(pause), flush=True)
            time.sleep(pause)
