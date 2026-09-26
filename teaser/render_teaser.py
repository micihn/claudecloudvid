"""PORTOKO teaser — 30 s, 24 fps. Real CC0 / public-domain footage painted onto a sheet of paper.

Each shot is a still, framed painting (watercolour or acrylic) on one sketchbook sheet with an
ink caption; only the footage inside moves, slowed down. Shots change with a wet-wash wipe on
the bar lines of teaser_score.py (60 BPM, 4 s bars).

    python3 render_teaser.py          # -> frames/*.jpg, then encode with the score
"""
import os, sys, subprocess, multiprocessing as mp
import numpy as np, cv2, imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont
from paint import W, H, Paper, Acrylic, watercolor, warm_grade, wash_wipe

HERE = os.path.dirname(os.path.abspath(__file__))
FF = imageio_ffmpeg.get_ffmpeg_exe()
FPS, DUR = 24, 30.0
NF = int(FPS * DUR)
FT = lambda n: os.path.join(HERE, 'fonts', n)
INK = (43, 36, 30)
GREEN = (5, 150, 84)
F = lambda p: os.path.join(HERE, 'footage', p)

LAND = (210, 64, 1500, 844)      # x, y, w, h on the sheet
PORT_L = (330, 90, 506, 900)
PORT_R = (1084, 90, 506, 900)
SQ_L = (250, 130, 720, 820)

SHOTS = [
    dict(name='fog', src=F('Morning_Fog_on_Lake_BRoll_10s.webm'), ss=0.5, speed=0.7, style='water', rect=LAND,
         t0=0.0, t1=4.6, seed=11, caption=None),
    dict(name='loom', src=F('Beneath_the_loom_2.webm'), ss=0.4, speed=0.45, style='water', rect=SQ_L, crop=(0.0, 0.0, 1.0, 0.64),
         wc=dict(detail=0.55, bands=8, edge=0.45), t0=3.4, t1=8.6, seed=12,
         caption='Every business\ngets a little\ntangled.', cap_at=(1090, 540, 'la')),
    dict(name='laptop', src=F('Glasses_lying_on_a_laptop_keyboard,_while_a_TV_broadcast_is_reflected_in_the_glasses_and_on_the_laptop_screen.webm'),
         ss=1.0, speed=0.6, style='acrylic', rect=LAND, t0=7.4, t1=12.6, seed=13, desat=0.75,
         caption='Five spreadsheets, two WhatsApp groups, and an Odoo nobody trusts.'),
    dict(name='pottery', src=F('Грнчарско_колце.webm'), ss=5.5, speed=0.55, style='acrylic', rect=PORT_R,
         t0=11.4, t1=16.6, seed=14, caption='So we sit down,\nand look at how\nit really works.', cap_at=(330, 540, 'la')),
    dict(name='candle', src=F('Corona.Candle.webm'), ss=0.3, speed=0.8, style='acrylic', rect=LAND, crop=(0.24, 0.28, 0.62, 0.62),
         t0=15.4, t1=20.6, seed=15, caption='Then we untangle it. Gently.'),
    dict(name='sunset', src=F('နေဝင်ဆည်းဆာ_မိုးတိမ်ကောင်းကင်.webm'), ss=2.0, speed=0.9, style='water', rect=LAND,
         t0=19.4, t1=24.6, seed=16, caption='Configure  ·  Build  ·  Connect  ·  Redesign'),
]
CUTS = [4.0, 8.0, 12.0, 16.0, 20.0, 24.0]   # wash wipes centred here, 1 s long
END_T = 24.0

# ------------------------------------------------------------------ the sheet (shared by everything)
SHEET = Paper(seed=1)


def sheet_light(t):
    """Morning window light falling across the sketchbook, drifting very slowly."""
    gx, gy = np.meshgrid(np.linspace(0, 1, W, dtype=np.float32), np.linspace(0, 1, H, dtype=np.float32))
    cx, cy = 0.28 + t * 0.006, 0.18
    d = np.sqrt(((gx - cx) * 1.6) ** 2 + (gy - cy) ** 2)
    warm = 1.0 + 0.06 * np.exp(-d * 2.2) - 0.1 * np.clip(d - 0.55, 0, 1)
    return np.stack([warm * 1.01, warm, warm * 0.975], -1).astype(np.float32)


LIGHTS = {}


def light(t):
    k = round(t, 1)
    if k not in LIGHTS: LIGHTS[k] = sheet_light(k)
    return LIGHTS[k]


# ------------------------------------------------------------------ footage
def decode(shot):
    x, y, w, h = shot['rect']
    n_src = int(np.ceil((shot['t1'] - shot['t0']) * shot['speed'] * 30)) + 8
    vf = []
    if 'crop' in shot:
        cx, cy, cw, ch = shot['crop']; vf.append(f'crop=iw*{cw}:ih*{ch}:iw*{cx}:ih*{cy}')
    vf += [f'fps=30', f'scale={w}:{h}:force_original_aspect_ratio=increase', f'crop={w}:{h}']
    p = subprocess.run([FF, '-v', 'error', '-ss', str(shot['ss']), '-i', shot['src'], '-frames:v', str(n_src),
                        '-vf', ','.join(vf), '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True, check=True)
    fr = np.frombuffer(p.stdout, np.uint8).reshape(-1, h, w, 3)
    return fr


def sample(frames, st):
    """Blend neighbouring frames for smooth slow motion."""
    f = min(st * 30, len(frames) - 1.001); i = int(f); a = f - i
    return (frames[i].astype(np.float32) * (1 - a) + frames[i + 1].astype(np.float32) * a) / 255.0


def paint_shot(shot):
    """Render every frame of one shot's painting (rect-sized), cached to disk."""
    out_dir = os.path.join(HERE, 'cache', shot['name']); os.makedirs(out_dir, exist_ok=True)
    frames = decode(shot)
    x, y, w, h = shot['rect']
    paper = Paper(seed=shot['seed'], w=w, h=h)
    paper.tex = SHEET.tex[y:y + h, x:x + w]            # same sheet, so edges are seamless
    ts = np.arange(int(shot['t0'] * FPS), int(np.ceil(shot['t1'] * FPS)) + 1) / FPS
    src_t = lambda t: (t - shot['t0']) * shot['speed']
    ac = None
    if shot['style'] == 'acrylic':
        ac = Acrylic(warm_grade(sample(frames, src_t((shot['t0'] + shot['t1']) / 2))), seed=shot['seed'], radii=(18, 9, 5))  # layout only
        edge = np.clip((paper.margin - 0.45) * 5, 0, 1)[..., None]
    prev = None
    for t in ts:
        fn = os.path.join(out_dir, f'{int(round(t * FPS)):05d}.png')
        if os.path.exists(fn): prev = None; continue
        x0 = sample(frames, src_t(t))
        if shot.get('desat'):
            L = x0 @ np.array([0.299, 0.587, 0.114], np.float32)
            x0 = x0 * (1 - shot['desat']) + L[..., None] * shot['desat']
        x0 = warm_grade(x0)
        if ac is not None:
            img = ac.render(x0)
            img = paper.surface() * (1 - edge) + img * edge
        else:
            img = watercolor(x0, paper, **shot.get('wc', {}))
        if prev is not None: img = img * 0.7 + prev * 0.3   # a little persistence: paint doesn't flicker
        prev = img
        cv2.imwrite(fn, (np.clip(img, 0, 1)[:, :, ::-1] * 255).astype(np.uint8))
    return shot['name']


# ------------------------------------------------------------------ typography
def text_layer(txt, size, fill, anchor_xy, align='la', font='IBMPlexMono-500.ttf', spacing=1.55, italic_word=None, italic_fill=None):
    """RGBA layer with the text; returns float arrays (rgb, alpha)."""
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    fnt = ImageFont.truetype(FT(font), size)
    x, y, anc = anchor_xy
    lines = txt.split('\n'); lh = int(size * spacing); total = lh * len(lines)
    y0 = y - total / 2 if anc[1] == 'a' and len(lines) > 1 else y
    for i, ln in enumerate(lines):
        yy = y0 + i * lh
        if italic_word and italic_word in ln:
            fi = ImageFont.truetype(FT('IBMPlexMono-600i.ttf'), size)
            pre, post = ln.split(italic_word, 1)
            widths = [d.textlength(pre, font=fnt), d.textlength(italic_word, font=fi), d.textlength(post, font=fnt)]
            xx = x - sum(widths) / 2 if anc[0] == 'm' else x
            d.text((xx, yy), pre, font=fnt, fill=fill, anchor='l' + anc[1])
            d.text((xx + widths[0], yy), italic_word, font=fi, fill=italic_fill or fill, anchor='l' + anc[1])
            d.text((xx + widths[0] + widths[1], yy), post, font=fnt, fill=fill, anchor='l' + anc[1])
        else:
            d.text((x, yy), ln, font=fnt, fill=fill, anchor=anc)
    a = np.asarray(im).astype(np.float32) / 255.0
    return a[..., :3], a[..., 3:4]


def ink(img, layer, alpha):
    """Ink sits in the paper: multiply, slightly broken by the paper tooth."""
    rgb, a = layer
    a = a * alpha * (0.88 + 0.12 * SHEET.tex[..., None] / SHEET.tex.max())
    return img * (1 - a) + rgb * a


CAPS = {}


def caption_for(shot):
    if shot['name'] not in CAPS:
        if shot.get('cap_at'):
            CAPS[shot['name']] = text_layer(shot['caption'], 34, INK + (255,), shot['cap_at'])
        else:
            CAPS[shot['name']] = text_layer(shot['caption'], 30, INK + (255,), (W // 2, 975, 'mm'))
    return CAPS[shot['name']]


# ------------------------------------------------------------------ end card: the wordmark in watercolour
def build_logo():
    m = cv2.imread(os.path.join(HERE, 'assets', 'logo_mask.png'), 0).astype(np.float32) / 255
    ys, xs = np.nonzero(m > 0.5); m = m[ys.min() - 20:ys.max() + 20, xs.min() - 20:xs.max() + 20]
    lw = 1180; lh = int(m.shape[0] * lw / m.shape[1])
    m = cv2.resize(m, (lw, lh), interpolation=cv2.INTER_AREA)
    ox, oy = (W - lw) // 2, 330
    mask = np.zeros((H, W), np.float32); mask[oy:oy + lh, ox:ox + lw] = m
    wob = cv2.GaussianBlur(mask, (0, 0), 1.2)
    # brand gradient (the original logo colours) as pigment, diagonal
    gx, gy = np.meshgrid(np.linspace(0, 1, W, dtype=np.float32), np.linspace(0, 1, H, dtype=np.float32))
    u = np.clip((gx - ox / W) / (lw / W) * 0.9 + (gy - oy / H) * 0.15, 0, 1)
    stops = [(0, (25, 27, 37)), (0.45, (17, 68, 53)), (0.75, (11, 118, 70)), (1.0, (5, 168, 88))]
    col = np.zeros((H, W, 3), np.float32)
    for (a, ca), (b, cb) in zip(stops[:-1], stops[1:]):
        k = ((u >= a) & (u <= b))[..., None]; f = ((u - a) / (b - a))[..., None]
        col = np.where(k, np.array(ca) * (1 - f) + np.array(cb) * f, col)
    col /= 255
    # watercolour behaviour: pooled darker edges, granulation, a lighter body
    edge = np.clip(wob - cv2.GaussianBlur(wob, (0, 0), 3.5), 0, 1) * 2.4
    body = 0.78 + 0.22 * edge + 0.12 * (SHEET.gran - 0.5)
    absorb = (1 - col) * np.clip(body, 0, 1.2)[..., None] * wob[..., None]
    return absorb, (ox, oy, lw, lh)


LOGO = None
TAG = None
CTA = None
URL = None


def end_card(img, t):
    global LOGO, TAG, CTA, URL
    if LOGO is None:
        LOGO = build_logo()
        TAG = text_layer('A digital atelier with a consulting desk.', 34, INK + (255,), (W // 2, 640, 'mm'), italic_word='atelier', italic_fill=GREEN + (255,))
        CTA = text_layer("Tell us what's tangled.", 30, GREEN + (255,), (W // 2, 740, 'mm'))
        URL = text_layer('portoko.com', 22, (120, 110, 100, 255), (W // 2, 818, 'mm'))
    absorb, (ox, oy, lw, lh) = LOGO
    # the wash spreads left to right, wet edge first
    p = np.clip((t - 24.3) / 1.7, 0, 1)
    p = 1 - (1 - p) ** 2
    gx = np.linspace(0, 1, W, dtype=np.float32)[None, :]
    field = (gx - ox / W) / (lw / W) + (SHEET.gran - 0.5) * 0.25
    m = np.clip((p * 1.25 - field) * 8, 0, 1)[..., None]
    img = img * (1 - absorb * m)
    img = ink(img, TAG, np.clip((t - 26.2) / 0.9, 0, 1))
    img = ink(img, CTA, np.clip((t - 27.0) / 0.5, 0, 1))
    # a hand-drawn underline, drawn on the switch click (27.2 s)
    u = np.clip((t - 27.2) / 0.35, 0, 1)
    if u > 0:
        line = np.zeros((H, W), np.float32)
        x0, x1 = W // 2 - 205, W // 2 - 205 + int(410 * (1 - (1 - u) ** 3))
        pts = np.array([[x, 772 + 3 * np.sin(x / 70.0)] for x in range(x0, x1, 4)], np.int32)
        if len(pts) > 1: cv2.polylines(line, [pts], False, 1.0, 3, cv2.LINE_AA)
        line = cv2.GaussianBlur(line, (0, 0), 0.8)[..., None]
        img = img * (1 - line * 0.85) + np.array(GREEN, np.float32) / 255 * line * 0.85
    img = ink(img, URL, np.clip((t - 27.8) / 0.8, 0, 1))
    return img


# ------------------------------------------------------------------ compositor
def shot_frame(shot, t):
    fn = os.path.join(HERE, 'cache', shot['name'], f'{int(round(t * FPS)):05d}.png')
    base = SHEET.surface().copy()
    im = cv2.imread(fn)
    if im is None: return base
    x, y, w, h = shot['rect']
    base[y:y + h, x:x + w] = im[:, :, ::-1].astype(np.float32) / 255
    if shot['caption']:
        a = np.clip((t - shot['t0'] - 0.9) / 0.8, 0, 1) * np.clip((shot['t1'] - 1.1 - t) / 0.5, 0, 1)  # gone before the wipe
        if a > 0: base = ink(base, caption_for(shot), a)
    return base


def frame(t):
    active = [s for s in SHOTS if s['t0'] <= t <= s['t1']]
    blank = SHEET.surface()
    if t < 1.6:   # the first painting blooms onto the empty sheet
        img = wash_wipe(blank, shot_frame(SHOTS[0], t), min(1, t / 1.6), SHEET, seed=3, direction=(0.6, 1))
    elif t >= END_T + 0.5:
        img = end_card(blank.copy(), t)
    else:
        img = None
        for c, (a, b) in zip(CUTS, zip(SHOTS, SHOTS[1:] + [None])):
            if c - 0.5 <= t <= c + 0.5:
                fa = shot_frame(a, t)
                fb = shot_frame(b, t) if b else end_card(blank.copy(), t)
                img = wash_wipe(fa, fb, (t - (c - 0.5)), SHEET, seed=int(c * 7), direction=(1, 0.35))
                break
        if img is None:
            img = shot_frame(active[-1], t) if active else blank.copy()
    img = img * light(t)
    return np.clip(img, 0, 1)


def render_range(args):
    i0, i1 = args
    os.makedirs(os.path.join(HERE, 'frames'), exist_ok=True)
    for i in range(i0, i1):
        fn = os.path.join(HERE, 'frames', f'{i:05d}.jpg')
        if os.path.exists(fn): continue
        cv2.imwrite(fn, (frame(i / FPS)[:, :, ::-1] * 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 95])
    return i1


if __name__ == '__main__':
    only = sys.argv[1:]
    with mp.Pool(4) as pool:
        for n in pool.imap_unordered(paint_shot, SHOTS): print('painted', n, flush=True)
        if only:  # stills: render_teaser.py 5.2 9.0 ...
            os.makedirs(os.path.join(HERE, 'stills'), exist_ok=True)
            for s in only:
                t = float(s); cv2.imwrite(os.path.join(HERE, 'stills', f't{t:05.2f}.jpg'), (frame(t)[:, :, ::-1] * 255).astype(np.uint8))
        else:
            chunks = [(i, min(NF, i + 30)) for i in range(0, NF, 30)]
            for n in pool.imap_unordered(render_range, chunks): print('frames', n, flush=True)
