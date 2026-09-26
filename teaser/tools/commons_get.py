"""Download Commons files by title (URL derived from the filename hash, no API call)."""
import sys, os, hashlib, time, urllib.parse, urllib.request, urllib.error

UA = {'User-Agent': 'portoko-teaser/1.0 (+https://github.com/micihn/claudecloudvid)'}


def url_for(title):
    name = title.replace('File:', '').replace(' ', '_')
    h = hashlib.md5(name.encode()).hexdigest()
    return f'https://upload.wikimedia.org/wikipedia/commons/{h[0]}/{h[:2]}/{urllib.parse.quote(name)}'


def candidates(title):
    """Commons throttles originals for busy shared IPs, so prefer the 720p transcode."""
    orig = url_for(title); head, name = orig.rsplit('/', 1); h = head.split('/commons/')[1]
    base = f'https://upload.wikimedia.org/wikipedia/commons/transcoded/{h}/{name}/{name}'
    return [base + '.720p.vp9.webm', base + '.720p.webm', base + '.480p.vp9.webm', orig]


def get(title, dest):
    out = os.path.join(dest, title.replace('File:', '').replace(' ', '_'))
    if os.path.exists(out): return out
    for url in candidates(title):
        for attempt in range(3):
            try:
                with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=300) as r, open(out + '.part', 'wb') as f:
                    while chunk := r.read(1 << 20): f.write(chunk)
                os.rename(out + '.part', out); return out
            except urllib.error.HTTPError as e:
                if e.code == 404: break
                if e.code != 429: raise
                time.sleep(min(60, int(e.headers.get('Retry-After') or 0) or 10 * 2 ** attempt))
    raise RuntimeError('could not download ' + title)


if __name__ == '__main__':
    dest = sys.argv[1]
    for t in sys.argv[2:]:
        p = get(t, dest); print(os.path.getsize(p) // 1_000_000, 'MB', p, flush=True); time.sleep(4)
