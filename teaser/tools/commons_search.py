"""Search Wikimedia Commons for freely licensed video. Usage: commons_search.py "coffee steam" [...]"""
import sys, json, re, time, urllib.error, urllib.parse, urllib.request

API = 'https://commons.wikimedia.org/w/api.php'
UA = {'User-Agent': 'portoko-teaser/1.0 (+https://github.com/micihn/claudecloudvid)'}
FREE = re.compile(r'^(cc0|public domain|pd|cc-zero)', re.I)


def api(**p):
    p.update(format='json', maxlag=5)
    for attempt in range(6):
        try:
            with urllib.request.urlopen(urllib.request.Request(API + '?' + urllib.parse.urlencode(p), headers=UA), timeout=40) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code != 429 or attempt == 5: raise
            wait = int(e.headers.get('Retry-After') or 0) or 5 * 2 ** attempt
            print(f'  (rate limited, waiting {wait}s)', file=sys.stderr); time.sleep(wait)


def search(q, n=40, only_free=True):
    r = api(action='query', generator='search', gsrsearch=f'{q} filetype:video', gsrnamespace=6, gsrlimit=n,
            prop='imageinfo', iiprop='url|size|mediatype|extmetadata|mime', iiextmetadatafilter='LicenseShortName|Artist|ImageDescription')
    out = []
    for pg in (r.get('query', {}).get('pages', {}) or {}).values():
        ii = pg.get('imageinfo', [{}])[0]; md = ii.get('extmetadata', {})
        lic = md.get('LicenseShortName', {}).get('value', '')
        if only_free and not FREE.match(lic.strip()): continue
        desc = re.sub('<[^>]+>', '', md.get('ImageDescription', {}).get('value', ''))[:110]
        out.append(dict(title=pg['title'], lic=lic, w=ii.get('width'), h=ii.get('height'), dur=round(ii.get('duration') or 0, 1),
                        mb=round((ii.get('size') or 0) / 1e6, 1), url=ii.get('url'), desc=desc))
    return out


if __name__ == '__main__':
    for q in sys.argv[1:]:
        time.sleep(2)
        print(f'\n## {q}')
        for v in sorted(search(q), key=lambda v: -(v['w'] or 0)):
            print(f"{v['w']}x{v['h']} {v['dur']}s {v['mb']}MB [{v['lic']}] {v['title'][5:80]} | {v['desc'][:70]}")
