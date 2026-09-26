"""Fetch a URL with curl. Commons' thumbnail servers throttle Python's urllib here but serve curl fine."""
import subprocess, urllib.error

UA = 'portoko-film/1.0 (+https://github.com/micihn/claudecloudvid)'


def http(url, tries=1):
    r = subprocess.run(['curl', '-sS', '-L', '--max-time', '120', '-A', UA, '-w', '\n%{http_code}', url], capture_output=True)
    body, _, code = r.stdout.rpartition(b'\n')
    code = int(code or 0)
    if code != 200: raise urllib.error.HTTPError(url, code or 599, 'curl', None, None)
    return body
