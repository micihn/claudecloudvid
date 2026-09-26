"""Round-robin thumbnail fetcher for a throttled connection: on 429, back off briefly and move on."""
import sys, os, json, time, urllib.request, urllib.error
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = {'User-Agent': 'portoko-film/1.0 (+https://github.com/micihn/claudecloudvid)'}
want = sys.argv[1:]
cands = {json.loads(l)['id']: json.loads(l) for l in open(os.path.join(HERE, 'candidates.jsonl'))}
todo = [i for i in want if i in cands and not os.path.exists(os.path.join(HERE, 'images', i + '.jpg'))]
pause = 6
while todo:
    i = todo.pop(0)
    try:
        with urllib.request.urlopen(urllib.request.Request(cands[i]['thumb'], headers=UA), timeout=120) as r: data = r.read()
        open(os.path.join(HERE, 'images', i + '.jpg'), 'wb').write(data); print('ok', i, cands[i]['q'], len(todo), 'left', flush=True)
        pause = max(6, pause * 0.8)
    except urllib.error.HTTPError as e:
        todo.append(i); pause = min(120, pause * 1.6); print(e.code, 'backing off', round(pause), flush=True)
    time.sleep(pause)
