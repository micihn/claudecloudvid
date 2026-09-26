"""Write CREDITS.md from shots.json + candidates.jsonl: every image used, its licence and source."""
import os, json
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cands = {c['id']: c for c in map(json.loads, open(os.path.join(HERE, 'candidates.jsonl')))}
shots = json.load(open(os.path.join(HERE, 'shots.json')))
rows, seen = [], set()
for act in ('lens', 'horizon'):
    for s in shots[act]:
        for i in (s['id'], s.get('sky')):
            if not i or i in seen: continue
            seen.add(i); c = cands[i]
            rows.append(f"| {act} | [{c['title'][5:]}]({c['page']}) | {c['artist'] or '—'} | {c['lic']} |")
out = ['# Intro credits', '',
       'Every image is public domain or CC0, from Wikimedia Commons. Artists as recorded on each file page.', '',
       '| Act | File | Artist | Licence |', '|---|---|---|---|'] + rows + ['',
       'Sound: the CC0 recordings listed in `../showreel/audio/CREDITS.md` (VSCO 2 CE, VCSL, CC0 SFX) plus the VCSL Steinway B grand piano.',
       'Fonts: IBM Plex Serif and IBM Plex Mono (SIL Open Font License).', '']
open(os.path.join(HERE, 'CREDITS.md'), 'w').write('\n'.join(out))
print(len(rows), 'images credited')
