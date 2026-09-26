"""Find public-domain / CC0 photos on Wikimedia Commons and fetch 1920px thumbnails.

    commons_images.py search "tree rings" "orange slice" ...   -> candidates.jsonl (appends)
    commons_images.py fetch                                     -> images/<id>.jpg for every candidate
Commons asks bulk users to use thumbnails rather than originals, so we only fetch thumbnails.
"""
import sys, os, json, re, time, hashlib, urllib.parse, urllib.request, urllib.error

API = 'https://commons.wikimedia.org/w/api.php'
UA = {'User-Agent': 'portoko-film/1.0 (+https://github.com/micihn/claudecloudvid)'}
FREE = re.compile(r'^(cc0|public domain|pd|cc-zero)', re.I)
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAND = os.path.join(HERE, 'candidates.jsonl')


def http(url, tries=6):
    for a in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code not in (429, 503) or a == tries - 1: raise
            w = min(900, int(e.headers.get('Retry-After') or 0) or 8 * 2 ** a)
            print(f'  ({e.code}, waiting {w}s)', file=sys.stderr, flush=True); time.sleep(w)


def search(q, n=50):
    p = dict(action='query', format='json', generator='search', gsrsearch=f'{q} filetype:bitmap', gsrnamespace=6,
             gsrlimit=n, prop='imageinfo', iiprop='url|size|extmetadata', iiurlwidth=1920,
             iiextmetadatafilter='LicenseShortName|Artist')
    r = json.loads(http(API + '?' + urllib.parse.urlencode(p)))
    out = []
    for pg in (r.get('query', {}).get('pages', {}) or {}).values():
        ii = pg.get('imageinfo', [{}])[0]; md = ii.get('extmetadata', {})
        lic = md.get('LicenseShortName', {}).get('value', '').strip()
        if not FREE.match(lic) or (ii.get('width') or 0) < 1400: continue
        artist = re.sub('<[^>]+>', '', md.get('Artist', {}).get('value', ''))[:80]
        out.append(dict(id=hashlib.md5(pg['title'].encode()).hexdigest()[:10], q=q, title=pg['title'], lic=lic, artist=artist,
                        w=ii['width'], h=ii['height'], thumb=ii.get('thumburl'), page=ii.get('descriptionurl')))
    return out


if __name__ == '__main__':
    cmd, args = sys.argv[1], sys.argv[2:]
    if cmd == 'search':
        seen = set()
        if os.path.exists(CAND): seen = {json.loads(l)['id'] for l in open(CAND)}
        with open(CAND, 'a') as f:
            for q in args:
                res = [c for c in search(q) if c['id'] not in seen]
                for c in res: f.write(json.dumps(c, ensure_ascii=False) + '\n'); seen.add(c['id'])
                print(f'{q}: {len(res)} new', flush=True); time.sleep(3)
    elif cmd == 'fetch':      # fetch [id ...]  (no ids = every candidate)
        os.makedirs(os.path.join(HERE, 'images'), exist_ok=True)
        want = set(args)
        for l in open(CAND):
            c = json.loads(l); fn = os.path.join(HERE, 'images', c['id'] + '.jpg')
            if (want and c['id'] not in want) or os.path.exists(fn) or not c.get('thumb'): continue
            try:
                open(fn, 'wb').write(http(c['thumb'])); print('ok', c['id'], c['q'], flush=True)
            except Exception as e:
                print('fail', c['id'], e, flush=True)
            time.sleep(8)
