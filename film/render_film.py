"""PORTOKO film — 20 s, 24 fps. A match-cut montage on one circle, then the O becomes the logo.

Every shot is a real photograph (public domain / CC0, Wikimedia Commons) transformed so its
round subject sits on the same circle: centre C, radius R. The circle keeps turning slowly
across the cuts, so thirty-nine different things read as one object changing its skin.
    python3 render_film.py [t ...]      # all frames, or stills at the given times
"""
import os, sys, json, multiprocessing as mp
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
from timeline import FPS, DUR, END, LOGO, CUTS, SHOT_ENDS, WORDS

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1920, 1080
CX, CY, R = 960, 596, 380          # the one circle
SPIN = 1.5                          # degrees per second, continuous across cuts
FT = lambda n: os.path.join(HERE, 'fonts', n)
CIRCLES = json.load(open(os.path.join(HERE, 'circles.json')))
SHOTS = json.load(open(os.path.join(HERE, 'shots.json')))     # [{id, rot?, circle?:[cx,cy,r]}], one per cut


# ------------------------------------------------------------------ one shot
VOID = np.array([0.035, 0.035, 0.04], np.float32)
YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
_img = {}


def image(sid):
    if sid not in _img:
        im = cv2.imread(os.path.join(HERE, 'images', sid + '.jpg'))[:, :, ::-1].astype(np.float32) / 255
        _img[sid] = im
    return _img[sid]


def shot_frame(k, t):
    s = SHOTS[k]; im = image(s['id'])
    cx, cy, r = s.get('circle') or (CIRCLES[s['id']]['cx'], CIRCLES[s['id']]['cy'], CIRCLES[s['id']]['r'])
    local = t - CUTS[k]
    scale = (R / r) * (1.0 + 0.012 * local)                     # a breath of push-in
    ang = s.get('rot', 0) + SPIN * t
    M = cv2.getRotationMatrix2D((cx, cy), ang, scale)
    M[0, 2] += CX - cx; M[1, 2] += CY - cy
    out = cv2.warpAffine(im, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    # where the photo doesn't reach the frame, its surroundings fade into a dark void,
    # so the object floats like a planet; photos that cover the frame stay full-bleed
    valid = cv2.warpAffine(np.ones(im.shape[:2], np.float32), M, (W, H), flags=cv2.INTER_LINEAR, borderValue=0)
    if valid.min() < 0.999:
        dist = np.sqrt((XX - CX) ** 2 + (YY - CY) ** 2)
        reach = dist[valid < 0.5].min()
        inner = max(R * 1.06, reach - R * 0.55); outer = max(inner + R * 0.25, reach - 4)
        f = np.clip((dist - inner) / (outer - inner), 0, 1); f = (f * f * (3 - 2 * f))[..., None]
        tint = np.clip(im.mean((0, 1)) * 0.12, 0, 0.05)
        out = out * (1 - f) + (VOID + tint) * f
    return out


# ------------------------------------------------------------------ film look
GRAIN = [cv2.GaussianBlur(np.random.default_rng(i).normal(0, 1, (H, W)).astype(np.float32), (0, 0), 0.7) for i in range(6)]
VIGN = (1 - 0.42 * np.clip(((XX - W / 2) / (W * 0.62)) ** 2 + ((YY - H * 0.52) / (H * 0.7)) ** 2, 0, 1) ** 1.3)[..., None]


def grade(x, t, grain=0.035):
    L = x @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    x = x * 0.88 + L[..., None] * 0.12                                   # slightly calmer colour
    x = np.clip(x, 0, 1); x = x * x * (3 - 2 * x) * 0.35 + x * 0.65      # gentle S-curve
    x = x * np.array([1.02, 1.0, 0.96]) + (1 - x) * np.array([0.0, 0.006, 0.018])  # warm highs, cool lows
    x = 0.025 + x * 0.955                                                # lifted, filmic blacks
    hi = np.clip(L - 0.72, 0, 1)[..., None]                              # halation
    x = x + cv2.GaussianBlur(hi, (0, 0), 14)[..., None] * np.array([0.35, 0.12, 0.05])
    x = x * VIGN
    x = x + GRAIN[int(t * FPS) % 6][..., None] * grain * (0.6 + 0.4 * (1 - L[..., None]))
    return np.clip(x, 0, 1)


# ------------------------------------------------------------------ words
SERIF = ImageFont.truetype(FT('IBMPlexSerif-400.ttf'), 66)


def word_layer(text):
    im = Image.new('L', (W, H), 0); d = ImageDraw.Draw(im)
    d.text((CX, CY - R - 34), text, font=SERIF, fill=255, anchor='ms')
    return np.asarray(im).astype(np.float32)[..., None] / 255


WORD_L = {w: word_layer(w) for _, _, w in WORDS}


def put_word(img, text):
    m = WORD_L[text]
    near = cv2.dilate(m[..., 0], np.ones((15, 15), np.uint8))          # the letters and a little around them
    under = float((img.mean(-1) * near).sum() / near.sum())
    ink = np.array([0.965, 0.955, 0.93]) if under < 0.55 else np.array([0.07, 0.07, 0.08])   # like the reference
    halo = cv2.GaussianBlur(m, (0, 0), 10)[..., None] * (0.35 if under < 0.55 else 0.0)
    img = img * (1 - halo)
    return img * (1 - m) + ink * m


# ------------------------------------------------------------------ end card: the O becomes the wordmark
LOGO_MASK = cv2.imread(os.path.join(HERE, '..', 'teaser', 'assets', 'logo_mask.png'), 0).astype(np.float32) / 255
# logo_mask.png was drawn at s=2.0 with logo centre (1000,204) at (2000,450): logo unit u -> 2000+(u-1000)*2
LOGO_O2 = (2000 + (1247.5 - 1000) * 2, 450)           # centre of the middle O in the mask
LOGO_O_R = 106.5 * 2                                  # its centre-line radius in the mask
LOGO_SW = 43 * 2
WM_W = 1000                                           # final wordmark width on screen (logo units 44..1956)
WM_S = WM_W / (1912 * 2)                              # mask px -> screen px
LETTERS_X = [(44, 242), (300, 555), (620, 818), (862, 1075), (1120, 1375), (1439, 1637), (1701, 1956)]
BRAND = [(0, (243, 242, 238)), (0.4, (198, 244, 220)), (0.65, (111, 232, 176)), (1.0, (1, 218, 125))]
SITE = [(0, (230, 251, 255)), (0.3, (94, 224, 232)), (0.65, (1, 218, 125)), (1.0, (198, 232, 74))]


def ramp(stops, u):
    out = np.zeros(u.shape + (3,), np.float32)
    for (a, ca), (b, cb) in zip(stops[:-1], stops[1:]):
        k = ((u >= a) & (u <= b))[..., None]; f = np.clip((u - a) / (b - a), 0, 1)[..., None]
        out = np.where(k, np.array(ca) * (1 - f) + np.array(cb) * f, out)
    return out / 255


def ease(x): x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)


def ring(img, cx, cy, r, width, color, glow=0.0, alpha=1.0):
    d = np.abs(np.sqrt((XX - cx) ** 2 + (YY - cy) ** 2) - r)
    core = np.clip(width / 2 + 0.75 - d, 0, 1)[..., None] * alpha
    # seamless gradient around the ring: light at the top-left, green to lime at the bottom-right
    ang = 0.5 - 0.5 * np.cos(np.arctan2(YY - cy, XX - cx) - np.pi * 1.25)
    col = ramp(SITE, ang) if color is None else np.array(color, np.float32)
    img = img * (1 - core) + col * core
    if glow > 0:
        g = np.exp(-(d / (width * 3 + 10)) ** 2)[..., None] * glow * alpha
        img = img + col * g * 0.6
    return img


def end_card(t):
    bg = np.array([0.055, 0.056, 0.064], np.float32)
    img = np.ones((H, W, 3), np.float32) * bg
    # a faint horizon of brand light along the bottom (a nod to the planet limb)
    glow = np.exp(-((YY - H * 1.18) / (H * 0.26)) ** 2)[..., None] * ramp(SITE, XX / W) * 0.22
    img = img + glow * ease((t - END) / 1.2)
    # where the O ends up
    wm_x0 = W / 2 - WM_W / 2; wm_cy = CY - 40
    o2x = wm_x0 + (LOGO_O2[0] - 88) * WM_S; o2y = wm_cy
    m = ease((t - LOGO) / 0.9)                      # ring -> O
    cx, cy = CX + (o2x - CX) * m, CY + (o2y - CY) * m
    r = R + (LOGO_O_R * WM_S - R) * m
    wdt = 2.2 + (LOGO_SW * WM_S - 2.2) * m
    appear = ease((t - END) / 0.35)
    img = ring(img, cx, cy, r, wdt, None, glow=0.9 * (1 - m) + 0.15, alpha=appear)
    # "A digital atelier" inside the ring, before it moves
    ta = ease((t - END - 0.25) / 0.5) * (1 - ease((t - LOGO + 0.15) / 0.35))
    if ta > 0:
        im = Image.new('L', (W, H), 0); d = ImageDraw.Draw(im)
        d.text((CX, CY + 14), 'A digital atelier', font=ImageFont.truetype(FT('IBMPlexSerif-300i.ttf'), 44), fill=255, anchor='mm')
        a = np.asarray(im).astype(np.float32)[..., None] / 255 * ta
        img = img * (1 - a) + np.array([0.93, 0.93, 0.9]) * a
    # the wordmark grows from the O outward
    if t > LOGO + 0.35:
        mk = cv2.resize(LOGO_MASK[:, 88:3913], (WM_W, int(900 * WM_S)), interpolation=cv2.INTER_AREA)
        layer = np.zeros((H, W), np.float32)
        y0 = int(wm_cy - 450 * WM_S); x0 = int(wm_x0)
        layer[y0:y0 + mk.shape[0], x0:x0 + mk.shape[1]] = mk
        u = np.clip((XX - x0) / WM_W, 0, 1)
        col = ramp(BRAND, u)
        # letters reveal by distance from the O, each sliding up a little
        alpha = np.zeros((H, W), np.float32)
        for li, (a0, a1) in enumerate(LETTERS_X):
            if li == 4: continue                       # the O is the ring itself
            dist = abs(li - 4)
            p = ease((t - LOGO - 0.35 - dist * 0.09) / 0.7)
            if p <= 0: continue
            xa, xb = int(wm_x0 + (a0 * 2 - 88) * WM_S) - 3, int(wm_x0 + (a1 * 2 - 88) * WM_S) + 3
            shift = int((1 - p) * 18)
            sl = np.zeros((H, W), np.float32); sl[:, xa:xb] = layer[:, xa:xb]
            sl = np.roll(sl, shift, axis=0) * p
            alpha = np.maximum(alpha, sl)
        img = img * (1 - alpha[..., None]) + col * alpha[..., None]
        # the O takes the brand colour once it lands
        if m >= 1:
            oc = ramp(BRAND, np.array([(o2x - x0) / WM_W]))[0]
            img = ring(img, cx, cy, r, wdt, oc, glow=0.0, alpha=ease((t - LOGO - 0.9) / 0.4))
        # click: a single soft pulse of the O
        cp = t - (LOGO + 0.9)
        if 0 < cp < 0.8:
            img = ring(img, cx, cy, r + cp * 40, 1.5, (0.8, 1.0, 0.9), alpha=(1 - cp / 0.8) * 0.5)
    ua = ease((t - LOGO - 1.4) / 0.8)
    if ua > 0:
        im = Image.new('L', (W, H), 0); d = ImageDraw.Draw(im)
        d.text((W / 2, CY + 150), 'portoko.com', font=ImageFont.truetype(FT('IBMPlexMono-400.ttf'), 26), fill=255, anchor='mm')
        a = np.asarray(im).astype(np.float32)[..., None] / 255 * ua * 0.8
        img = img * (1 - a) + np.array([0.85, 0.85, 0.82]) * a
    img = img * (1 - ease((t - (DUR - 0.6)) / 0.6))
    return img


# ------------------------------------------------------------------ frames
def frame(t):
    if t >= END:
        return grade(end_card(t), t, grain=0.02)
    k = max(i for i, c in enumerate(CUTS) if c <= t + 1e-6)
    img = shot_frame(k, t)
    img = grade(img, t)
    for a, b, w in WORDS:
        if a <= t < b: img = put_word(img, w)
    img = img * ease(t / 0.35)
    return img


def render_range(rng_):
    os.makedirs(os.path.join(HERE, 'frames'), exist_ok=True)
    for i in range(*rng_):
        fn = os.path.join(HERE, 'frames', f'{i:05d}.jpg')
        cv2.imwrite(fn, (frame(i / FPS)[:, :, ::-1] * 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 95])
    return rng_[1]


if __name__ == '__main__':
    if len(sys.argv) > 1:
        os.makedirs(os.path.join(HERE, 'stills'), exist_ok=True)
        for s in sys.argv[1:]:
            cv2.imwrite(os.path.join(HERE, 'stills', f't{float(s):05.2f}.jpg'), (frame(float(s))[:, :, ::-1] * 255).astype(np.uint8))
    else:
        n = int(DUR * FPS)
        with mp.Pool(4) as p:
            for d in p.imap_unordered(render_range, [(i, min(n, i + 24)) for i in range(0, n, 24)]): print('frames', d, flush=True)
