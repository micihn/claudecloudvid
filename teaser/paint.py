"""Paint grades for the PORTOKO teaser: turn footage into watercolour or acrylic.

Everything that could flicker between frames (paper, pigment granulation, edge wobble,
stroke layout, impasto relief) is built once per shot and reused, so a slightly moving
shot reads as one painting with the light moving in it.
"""
import numpy as np, cv2

W, H = 1920, 1080
PAPER = np.array([0.953, 0.925, 0.872])      # warm cotton paper
WARM = dict(shadow=np.array([0.32, 0.22, 0.17]), light=np.array([1.0, 0.95, 0.86]))


def fbm(h, w, seed, scales=(256, 96, 32, 12), weights=(0.5, 0.25, 0.15, 0.1)):
    rng = np.random.default_rng(seed); out = np.zeros((h, w), np.float32)
    for s, wt in zip(scales, weights):
        small = rng.random((max(2, int(h / s) + 2), max(2, int(w / s) + 2))).astype(np.float32)
        out += wt * cv2.resize(small, (w, h), interpolation=cv2.INTER_CUBIC)
    out -= out.min(); return out / (out.max() + 1e-6)


def to_float(img_bgr, w=W, h=H):
    img = cv2.resize(img_bgr, (w, h), interpolation=cv2.INTER_AREA if img_bgr.shape[1] > w else cv2.INTER_CUBIC)
    return img[:, :, ::-1].astype(np.float32) / 255.0


def warm_grade(x, amount=1.0):
    """Lift and warm the shadows, soften highlights to cream, gently desaturate."""
    L = (x @ np.array([0.299, 0.587, 0.114], np.float32))[..., None]
    y = x * 0.82 + L * 0.18                                        # desaturate a touch
    y = WARM['shadow'] * (1 - y) + WARM['light'] * y * 1.0         # map into a warm range
    y = np.clip(y, 0, 1) ** 0.92
    return (x * (1 - amount) + y * amount).astype(np.float32)


class Paper:
    def __init__(self, seed=1, w=W, h=H):
        self.w, self.h = w, h
        fib = fbm(h, w, seed, (64, 16, 4, 2), (0.2, 0.3, 0.3, 0.2))
        tooth = cv2.GaussianBlur(np.random.default_rng(seed + 1).random((h, w)).astype(np.float32), (0, 0), 0.8)
        self.tex = 0.94 + 0.05 * fib + 0.03 * (tooth - 0.5)                    # multiplicative tone
        self.gran = fbm(h, w, seed + 2, (24, 8, 3, 1.5), (0.2, 0.3, 0.3, 0.2))  # pigment settling
        wx = fbm(h, w, seed + 3, (180, 60, 20, 8)) - 0.5; wy = fbm(h, w, seed + 4, (180, 60, 20, 8)) - 0.5
        gx, gy = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
        self.mapx, self.mapy = gx + wx * 14, gy + wy * 14                         # wobbly wet edges
        # the painting doesn't reach the edge of the sheet
        m = np.zeros((h, w), np.float32); pad = int(0.035 * w)
        m[pad:h - pad, pad:w - pad] = 1
        m = cv2.GaussianBlur(m, (0, 0), 18) + (fbm(h, w, seed + 5, (90, 30, 10, 4)) - 0.5) * 0.9
        self.margin = np.clip((m - 0.35) * 4, 0, 1)

    def surface(self):
        return (PAPER * self.tex[..., None]).astype(np.float32)


def watercolor(x, paper, bands=7, edge=0.55, granulate=0.35, detail=0.25, margin=True):
    """x: float RGB in [0,1] at paper size. Returns a watercolour rendering."""
    h, w = paper.h, paper.w
    # 1. washes: flatten texture while keeping shapes
    small = cv2.resize(x.astype(np.float32), (w // 3, h // 3), interpolation=cv2.INTER_AREA)
    for _ in range(3): small = cv2.bilateralFilter(small, 9, 0.12, 6)
    wash = cv2.resize(small, (w, h), interpolation=cv2.INTER_CUBIC)
    wash = cv2.remap(wash, paper.mapx, paper.mapy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    # 2. layered glazes: soft-quantised value, like several transparent passes
    L = wash @ np.array([0.299, 0.587, 0.114], np.float32)
    q = np.floor(L * bands) / bands
    frac = L * bands - np.floor(L * bands)
    Lq = q + (1 / bands) / (1 + np.exp(-(frac - 0.5) * 14))
    wash = np.clip(wash * ((Lq + 0.02) / (L + 0.02))[..., None], 0, 1)
    # 3. darkened wet edges where glazes meet
    gxy = cv2.Sobel(Lq, cv2.CV_32F, 1, 0) ** 2 + cv2.Sobel(Lq, cv2.CV_32F, 0, 1) ** 2
    e = cv2.GaussianBlur(np.sqrt(gxy), (0, 0), 1.6); e = np.clip(e / (np.percentile(e, 99) + 1e-6), 0, 1)
    wash = wash * (1 - edge * e[..., None] * (1 - wash) * 1.4)
    # 4. a little of the original drawing back in, as soft pencil
    if detail > 0:
        g = cv2.GaussianBlur((x @ np.array([0.299, 0.587, 0.114], np.float32)), (0, 0), 1.0)
        lap = np.abs(cv2.Laplacian(g, cv2.CV_32F, ksize=3)); lap = np.clip(lap / (np.percentile(lap, 99.5) + 1e-6), 0, 1)
        wash = wash * (1 - detail * lap[..., None] * 0.6)
    # 5. subtractive on paper: pigment = absorption, granulation in the darks
    absorb = 1 - wash
    absorb = absorb * (1 + granulate * (paper.gran[..., None] - 0.5) * 2 * np.sqrt(absorb))
    if margin: absorb = absorb * paper.margin[..., None]
    out = paper.surface() * (1 - np.clip(absorb, 0, 1))
    return np.clip(out, 0, 1)


class Acrylic:
    """Stroke-based painting. Strokes are laid out once from a key frame; colours are
    re-sampled from every frame, so the painting stays put while its light changes."""

    def __init__(self, key, seed=3, radii=(26, 13, 7), light=(-0.6, -0.7)):
        h, w = key.shape[:2]; self.h, self.w = h, w
        rng = np.random.default_rng(seed)
        g = cv2.GaussianBlur(key @ np.array([0.299, 0.587, 0.114], np.float32), (0, 0), 2)
        gx, gy = cv2.Sobel(g, cv2.CV_32F, 1, 0), cv2.Sobel(g, cv2.CV_32F, 0, 1)
        # structure tensor -> stroke direction along edges
        jxx, jyy, jxy = [cv2.GaussianBlur(a, (0, 0), 8) for a in (gx * gx, gy * gy, gx * gy)]
        ang = 0.5 * np.arctan2(2 * jxy, jxx - jyy) + np.pi / 2
        # where the image has no clear edge, follow one calm, slowly curving hand direction
        coh = np.sqrt((jxx - jyy) ** 2 + 4 * jxy ** 2) / (jxx + jyy + 1e-6)
        calm = -0.55 + (fbm(h, w, seed + 9, (500, 250, 120, 60)) - 0.5) * 1.2
        wgt = np.clip((coh - 0.25) * 2.5, 0, 1)
        ang = np.arctan2(wgt * np.sin(2 * ang) + (1 - wgt) * np.sin(2 * calm), wgt * np.cos(2 * ang) + (1 - wgt) * np.cos(2 * calm)) / 2
        mag = np.sqrt(gx ** 2 + gy ** 2); mag = mag / (np.percentile(mag, 99) + 1e-6)
        detail = cv2.GaussianBlur(np.clip(mag, 0, 1), (0, 0), 10)
        strokes = []
        for li, r in enumerate(radii):
            ys, xs = np.mgrid[r // 2:h:r, r // 2:w:r]
            xs = (xs + rng.uniform(-r / 2, r / 2, xs.shape)).clip(0, w - 1).astype(int)
            ys = (ys + rng.uniform(-r / 2, r / 2, ys.shape)).clip(0, h - 1).astype(int)
            xs, ys = xs.ravel(), ys.ravel()
            if li > 0:  # finer strokes only where there is detail
                keep = rng.random(len(xs)) < np.clip(detail[ys, xs] * (2.2 if li == 1 else 3.0), 0.06, 1)
                xs, ys = xs[keep], ys[keep]
            a = ang[ys, xs] + rng.normal(0, 0.1, len(xs))
            ln = r * rng.uniform(2.2, 3.6, len(xs)); wd = r * rng.uniform(0.8, 1.1, len(xs))
            for i in rng.permutation(len(xs)):
                strokes.append((xs[i], ys[i], a[i], ln[i], wd[i], li))
        self.s = np.array(strokes, np.float32)
        self.order = np.argsort(self.s[:, 5], kind='stable')
        # impasto relief: every stroke is a few bristle ridges
        hm = np.zeros((h, w), np.float32)
        for k in self.order:
            x0, y0, a, ln, wd, li = self.s[k]
            dx, dy = np.cos(a) * ln / 2, np.sin(a) * ln / 2; nx, ny = -np.sin(a), np.cos(a)
            for b in range(4):
                o = (b - 1.5) / 4 * wd
                p1 = (int(x0 - dx + nx * o), int(y0 - dy + ny * o)); p2 = (int(x0 + dx + nx * o), int(y0 + dy + ny * o))
                cv2.line(hm, p1, p2, float(0.5 + 0.5 * rng.random()), max(1, int(wd / 4)), cv2.LINE_AA)
        hm = cv2.GaussianBlur(hm, (0, 0), 1.8)
        nxm, nym = cv2.Sobel(hm, cv2.CV_32F, 1, 0, ksize=3), cv2.Sobel(hm, cv2.CV_32F, 0, 1, ksize=3)
        lx, ly = light; lz = 1.0; ln_ = np.sqrt(lx * lx + ly * ly + lz * lz)
        nz = 1.0 / np.sqrt(nxm ** 2 + nym ** 2 + 1)
        shade = (-(nxm * lx + nym * ly) * nz + nz * lz) / ln_
        self.shade = (0.9 + 0.22 * (shade - shade.mean())).astype(np.float32)
        self.spec = np.clip((shade - np.percentile(shade, 97)) * 4, 0, 1).astype(np.float32)

    def render(self, x, reveal=1.0, seed=0):
        """x: float RGB frame. reveal < 1 paints only the first strokes (it paints itself in)."""
        base = cv2.GaussianBlur(x, (0, 0), 2.5)
        canvas = cv2.GaussianBlur(x, (0, 0), 12).astype(np.float32)  # underpainting
        n = int(len(self.order) * np.clip(reveal, 0, 1))
        s = self.s
        for k in self.order[:n]:
            x0, y0, a, ln, wd, li = s[k]
            c = base[int(y0), int(x0)]
            dx, dy = np.cos(a) * ln / 2, np.sin(a) * ln / 2
            cv2.line(canvas, (int(x0 - dx), int(y0 - dy)), (int(x0 + dx), int(y0 + dy)), c.tolist(), max(1, int(wd)), cv2.LINE_AA)
        out = canvas * self.shade[..., None] + self.spec[..., None] * 0.12
        return np.clip(out, 0, 1)


def wash_wipe(a, b, t, paper, seed=7, direction=(1, 0.3)):
    """Reveal b over a with a spreading wet wash; the moving edge leaves a pigment line."""
    h, w = paper.h, paper.w
    n = fbm(h, w, seed, (320, 110, 36, 12))
    gx, gy = np.meshgrid(np.linspace(0, 1, w, dtype=np.float32), np.linspace(0, 1, h, dtype=np.float32))
    d = (gx * direction[0] + gy * direction[1]) / (abs(direction[0]) + abs(direction[1]))
    field = d * 0.75 + n * 0.25
    th = -0.1 + t * 1.2
    m = np.clip((th - field) * 18, 0, 1)
    edge = np.exp(-((th - field) * 30) ** 2) * (t > 0) * (t < 1)
    out = a * (1 - m[..., None]) + b * m[..., None]
    return np.clip(out * (1 - 0.35 * edge[..., None] * (1 - out * 0.6)), 0, 1)
