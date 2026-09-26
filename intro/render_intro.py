"""PORTOKO intro — 35 s, 24 fps. Through a lens, out onto a horizon, then the wordmark.

Every image is a real public-domain / CC0 photograph or print from Wikimedia Commons.
  Lens     each image sits in a round aperture inside a dark lens barrel, pushing in slowly,
           dissolving into the next.
  Push     the aperture grows and sinks until its rim is the curve of a horizon.
  Horizon  every shot wraps a texture onto the same planet-sized dome (centre far below frame)
           that turns slowly across the cuts, so twenty-four different surfaces read as one
           world changing its skin. Three phrases sit above the arc.
  End      a dark card with a brand-lit limb, "A digital atelier", then the wordmark.
    python3 render_intro.py [t ...]      # all frames, or stills at the given times
"""
import os, sys, json, multiprocessing as mp
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
from timeline import FPS, DUR, PUSH, HORIZ, END, ATELIER, LOGO, LENS, LENS_X, CUTS, WORDS

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1920, 1080
FT = lambda n: os.path.join(HERE, 'fonts', n)
SHOTS = json.load(open(os.environ.get('INTRO_SHOTS', os.path.join(HERE, 'shots.json'))))   # {"lens": [...], "horizon": [...]}, entries {id, bg?|sky?, dx?, dy?, zoom?}
YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)

# the lens aperture, and the horizon it becomes
LX, LY, LR = W / 2, H / 2, 405
HY, HR = 612, 2000                  # arc top on screen, dome radius
HCX, HCY = W / 2, HY + HR
SPIN = 0.55                         # degrees per second the dome turns, continuous across cuts


def ease(x): x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)


IMAGES = os.environ.get('INTRO_IMAGES', os.path.join(HERE, 'images'))   # previews/ for quick layout tests
_img = {}


def image(sid):
    if sid not in _img:
        _img[sid] = cv2.imread(os.path.join(IMAGES, sid + '.jpg'))[:, :, ::-1].astype(np.float32) / 255
    return _img[sid]


def cover(s, w, h, zoom=1.0):
    """The shot's image scaled to cover w x h (with its own framing offsets), as a float array."""
    im = image(s['id']); ih, iw = im.shape[:2]
    k = max(w / iw, h / ih) * s.get('zoom', 1.0) * zoom
    M = np.float32([[k, 0, w / 2 - (iw / 2 + s.get('dx', 0) * iw) * k], [0, k, h / 2 - (ih / 2 + s.get('dy', 0) * ih) * k]])
    return cv2.warpAffine(im, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)


# ------------------------------------------------------------------ act 1: the lens
def lens_content(t, cx, cy, r):
    """What is seen through the aperture at time t: the lens images, dissolving and pushing in."""
    def one(k):
        s = SHOTS['lens'][k]; local = t - LENS[k]
        z = 1.0 + 0.045 * local                                   # the slow push-in
        size = int(2 * r * 1.08) + 2
        im = cover(s, size, size, z)
        ang = (k % 2 * 2 - 1) * 1.2 * local                       # a slight turn, alternating
        M = cv2.getRotationMatrix2D((size / 2, size / 2), ang, 1.0)
        M[0, 2] += cx - size / 2; M[1, 2] += cy - size / 2
        return cv2.warpAffine(im, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    k = max(i for i, c in enumerate(LENS) if c <= t + 1e-6) if t >= LENS[0] else 0
    out = one(k)
    if k + 1 < len(LENS) and t > LENS[k + 1] - LENS_X:
        out = out * (1 - ease((t - LENS[k + 1] + LENS_X) / LENS_X)) + one(k + 1) * ease((t - LENS[k + 1] + LENS_X) / LENS_X)
    return out


def barrel(cx, cy, r, open_=0.0):
    """Dark lens barrel around an aperture: rubber grooves with a soft top-left sheen. Returns (colour, aperture mask)."""
    d = np.sqrt((XX - cx) ** 2 + (YY - cy) ** 2); u = d / r
    ap = np.clip((r - d) / 1.6 + 0.5, 0, 1)                        # aperture, anti-aliased
    ang = np.arctan2(YY - cy, XX - cx)
    sheen = 0.5 + 0.5 * np.cos(ang + np.pi * 0.72)                 # light from the top-left
    g = u - 1
    grooves = np.abs(np.sin(g * 30)) ** 5 * np.exp(-g * 1.2)       # ridges, fading outward
    lip = np.exp(-(g / 0.02) ** 2)                                 # the bright inner lip
    step = np.exp(-((g - 0.13) / 0.012) ** 2)                      # the front edge of the barrel
    body = 0.03 + 0.09 * grooves * (0.3 + 0.7 * sheen) + 0.3 * lip * (0.35 + 0.65 * sheen) + 0.12 * step * sheen
    body *= np.clip(1 - (g - 0.45) / 0.45, 0, 1) * (1 - open_)     # the barrel ends in black; opens away during the push
    col = body[..., None] * np.array([0.92, 0.95, 1.0], np.float32)
    return col, ap


def lens_frame(t):
    img = lens_content(t, LX, LY, LR)
    # inside the glass: a soft vignette toward the rim and a whisper of chromatic fringe
    u = np.sqrt((XX - LX) ** 2 + (YY - LY) ** 2) / LR
    img = img * (1 - 0.45 * ease((u - 0.72) / 0.28))[..., None]
    col, ap = barrel(LX, LY, LR)
    out = img * ap[..., None] + col * (1 - ap[..., None])
    return out * ease((t - 0.05) / 1.1)                            # up from black


# ------------------------------------------------------------------ act 3: the horizon
def dome(s, t, cy=HCY, r=HR, cx=HCX):
    """The shot's texture wrapped on a dome of radius r (centre cx,cy), turning with t."""
    tex = cover(s, 2400, 1100)
    d = np.sqrt((XX - cx) ** 2 + (YY - cy) ** 2)
    th = np.arctan2(XX - cx, cy - YY) + np.radians(SPIN * t)
    tx = 1200 + th * r * 0.95
    ty = 1000 * (np.pi / 2 - np.arcsin(np.clip(d / r, 0, 1)))       # foreshortened toward the rim, like a sphere
    out = cv2.remap(tex, tx.astype(np.float32), ty.astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    depth = r - d
    out = out * (0.62 + 0.38 * ease(depth / 90))[..., None]         # a little limb darkening
    inside = np.clip(depth + 0.5, 0, 1)
    return out, inside, d


VOID = np.array([0.03, 0.032, 0.038], np.float32)


def sky(s, t):
    if s.get('bg'):                                                  # a flat paper colour behind the dome
        return np.ones((H, W, 3), np.float32) * np.array(s['bg'], np.float32)
    if s.get('sky'):
        return cover({'id': s['sky']}, W, H) * 0.7
    g = np.exp(-np.clip(HY - YY, 0, None) / 520)[..., None]
    return VOID + g * np.array([0.02, 0.025, 0.035])


def horizon_frame(t, k=None):
    if k is None: k = max(i for i, c in enumerate(CUTS) if c <= t + 1e-6)
    s = SHOTS['horizon'][k]
    tex, inside, d = dome(s, t)
    up = sky(s, t)
    tint = np.clip(tex[HY + 40:HY + 200].mean((0, 1)) * 1.3, 0.1, 1)
    halo = np.exp(-np.clip(d - HR, 0, None) / 26)[..., None] * (1 - inside[..., None]) * tint * 0.22
    out = up * (1 - inside[..., None]) + tex * inside[..., None] + halo
    rim = np.exp(-((d - HR) / 1.4) ** 2)[..., None] * 0.18 * tint   # a hairline of light along the edge
    return out + rim


# ------------------------------------------------------------------ act 2: the push through the lens
def push_frame(t):
    m = ease((t - PUSH) / (HORIZ - PUSH))
    m2 = m ** 1.6
    r = np.exp(np.log(LR) + (np.log(HR) - np.log(LR)) * m2)        # zoom in log space
    top = (LY - LR) + (HY - (LY - LR)) * m                         # the top of the rim sinks to the horizon line
    cy = top + r
    # inside: the last lens image hands over to the first horizon texture
    last = lens_content(min(t, LENS[-1] + 1.4), LX, cy, r) if r < 1400 else None
    tex, inside, d = dome(SHOTS['horizon'][0], t, cy=cy, r=r)
    x = ease((t - PUSH - 0.3) / 1.2)
    content = tex if last is None else last * (1 - x) + tex * x
    u = d / r
    content = content * (1 - 0.45 * (1 - m) * ease((u - 0.72) / 0.28))[..., None]
    col, ap = barrel(LX, cy, r, open_=m)
    up = sky(SHOTS['horizon'][0], t) * m
    out = content * ap[..., None] + (col + up) * (1 - ap[..., None])
    tint = np.clip(tex[HY + 40:HY + 200].mean((0, 1)) * 1.3, 0.1, 1)
    halo = np.exp(-np.clip(d - r, 0, None) / 26)[..., None] * (1 - ap[..., None]) * tint * 0.22 * m
    return out + halo


# ------------------------------------------------------------------ words
SERIF = ImageFont.truetype(FT('IBMPlexSerif-400.ttf'), 58)
_wl = {}


def put_word(img, text, a=1.0):
    if text not in _wl:
        im = Image.new('L', (W, H), 0); ImageDraw.Draw(im).text((W / 2, HY - 30), text, font=SERIF, fill=255, anchor='ms')
        _wl[text] = np.asarray(im).astype(np.float32)[..., None] / 255
    m = _wl[text] * a
    near = cv2.dilate(m[..., 0], np.ones((15, 15), np.uint8))
    under = float((img.mean(-1) * near).sum() / max(near.sum(), 1))
    dark = under < 0.55
    ink = np.array([0.965, 0.955, 0.93]) if dark else np.array([0.07, 0.07, 0.08])
    if dark: img = img * (1 - cv2.GaussianBlur(m, (0, 0), 10)[..., None] * 0.35)
    return img * (1 - m) + ink * m


# ------------------------------------------------------------------ end card
LOGO_MASK = cv2.imread(os.path.join(HERE, '..', 'teaser', 'assets', 'logo_mask.png'), 0).astype(np.float32) / 255
WM_W = 560
BRAND = [(0, (243, 242, 238)), (0.4, (198, 244, 220)), (0.65, (111, 232, 176)), (1.0, (1, 218, 125))]
SITE = [(0, (230, 251, 255)), (0.3, (94, 224, 232)), (0.65, (1, 218, 125)), (1.0, (198, 232, 74))]


def ramp(stops, u):
    out = np.zeros(u.shape + (3,), np.float32)
    for (a, ca), (b, cb) in zip(stops[:-1], stops[1:]):
        k = ((u >= a) & (u <= b))[..., None]; f = np.clip((u - a) / (b - a), 0, 1)[..., None]
        out = np.where(k, np.array(ca) * (1 - f) + np.array(cb) * f, out)
    return out / 255


def _text_layer(text, font, size, y):
    im = Image.new('L', (W, H), 0); ImageDraw.Draw(im).text((W / 2, y), text, font=ImageFont.truetype(FT(font), size), fill=255, anchor='mm')
    return np.asarray(im).astype(np.float32) / 255


ATELIER_L = _text_layer('A digital atelier', 'IBMPlexSerif-400.ttf', 44, H * 0.45)
URL_L = _text_layer('portoko.com', 'IBMPlexMono-400.ttf', 25, H * 0.45 + 80)
_mk = cv2.resize(LOGO_MASK[:, 88:3913], (WM_W, int(900 * WM_W / 3825)), interpolation=cv2.INTER_AREA)
WM_L = np.zeros((H, W), np.float32)
_y0 = int(H * 0.45 - _mk.shape[0] / 2); _x0 = int(W / 2 - WM_W / 2)
WM_L[_y0:_y0 + _mk.shape[0], _x0:_x0 + WM_W] = _mk
WM_COL = ramp(BRAND, np.clip((XX - _x0) / WM_W, 0, 1))
LIMB_COL = ramp(SITE, np.clip(XX / W, 0, 1))


def end_card(t):
    img = np.ones((H, W, 3), np.float32) * np.array([0.045, 0.047, 0.055], np.float32)
    # the limb: a dark planet at the bottom whose atmosphere glows in the site colours;
    # it rises a little and brightens at the very end, like the dawn after the title
    rise = ease((t - (LOGO + 2.6)) / 2.0)
    r = 2600; top = H * (0.86 - 0.06 * rise); cy = top + r
    d = np.sqrt((XX - W / 2) ** 2 + (YY - cy) ** 2) - r           # > 0 above the rim, < 0 on the planet
    on = ease((t - END) / 1.4) * (0.8 + 0.45 * rise)
    sky_ = d > 0
    atm = np.exp(-np.clip(d, 0, None) / 38)                        # thin bright band just above the rim
    haze = np.exp(-np.clip(d, 0, None) / 190)                      # wide soft haze
    img = img + LIMB_COL * ((0.62 * atm + 0.26 * haze) * sky_ * on)[..., None]
    rimlit = np.exp(np.clip(d, None, 0) / 10) * (~sky_)            # the planet's own edge catches a little light
    img = np.where(sky_[..., None], img, np.array([0.022, 0.024, 0.028]) + LIMB_COL * (0.16 * rimlit * on)[..., None])
    # text: "A digital atelier" -> the wordmark (+ url)
    a1 = ease((t - ATELIER) / 0.8) * (1 - ease((t - LOGO + 0.6) / 0.5))
    img = img * (1 - ATELIER_L[..., None] * a1) + np.array([0.93, 0.93, 0.9]) * ATELIER_L[..., None] * a1
    a2 = ease((t - LOGO) / 1.0)
    if a2 > 0:
        lift = int(round((1 - a2) * 10))
        m = np.roll(WM_L, lift, axis=0) * a2
        img = img * (1 - m[..., None]) + WM_COL * m[..., None]
        a3 = ease((t - LOGO - 1.1) / 0.9) * 0.9
        img = img * (1 - URL_L[..., None] * a3) + np.array([0.82, 0.83, 0.8]) * URL_L[..., None] * a3
    return img * (1 - ease((t - (DUR - 0.7)) / 0.7))


# ------------------------------------------------------------------ film look
GRAIN = [cv2.GaussianBlur(np.random.default_rng(i).normal(0, 1, (H, W)).astype(np.float32), (0, 0), 0.7) for i in range(6)]
VIGN = (1 - 0.38 * np.clip(((XX - W / 2) / (W * 0.62)) ** 2 + ((YY - H * 0.5) / (H * 0.7)) ** 2, 0, 1) ** 1.3)[..., None]


def grade(x, t, grain=0.032):
    L = x @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    x = x * 0.88 + L[..., None] * 0.12
    x = np.clip(x, 0, 1); x = x * x * (3 - 2 * x) * 0.35 + x * 0.65
    x = x * np.array([1.02, 1.0, 0.96]) + (1 - x) * np.array([0.0, 0.006, 0.018])
    x = 0.022 + x * 0.958
    hi = np.clip(L - 0.72, 0, 1)[..., None]
    x = x + cv2.GaussianBlur(hi, (0, 0), 14)[..., None] * np.array([0.3, 0.1, 0.04])
    x = x * VIGN
    x = x + GRAIN[int(t * FPS) % 6][..., None] * grain * (0.6 + 0.4 * (1 - L[..., None]))
    return np.clip(x, 0, 1)


# ------------------------------------------------------------------ frames
def frame(t):
    if t >= END:
        return grade(end_card(t), t, grain=0.02)
    if t < PUSH: img = lens_frame(t)
    elif t < HORIZ: img = push_frame(t)
    else: img = horizon_frame(t)
    img = grade(np.clip(img, 0, 1.2), t)
    for a, b, w in WORDS:
        if a <= t < b: img = put_word(img, w, ease((t - a) / 0.12))
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
