"""Ilustraciones vectoriales (dibujadas con PIL) de las 7 maravillas del mundo moderno.
Cada función devuelve una imagen RGB de 2304x1296 (1.2x de 1080p, para poder hacer zoom/paneo)."""
import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

CW, CH = 3840, 2160          # lienzo de dibujo (2x, para suavizado)
OW, OH = 2304, 1296          # tamaño final


def finish(img):
    return img.resize((OW, OH), Image.LANCZOS)


def grad(top, bot, w=CW, h=CH, mid=None):
    ys = np.linspace(0, 1, h)[:, None, None]
    top = np.array(top, np.float32); bot = np.array(bot, np.float32)
    if mid is None:
        arr = top + (bot - top) * ys
    else:
        m = np.array(mid, np.float32)
        arr = np.where(ys < 0.5, top + (m - top) * (ys / 0.5), m + (bot - m) * ((ys - 0.5) / 0.5))
    arr = np.broadcast_to(arr, (h, w, 3))
    return Image.fromarray(arr.clip(0, 255).astype(np.uint8))


def glow(img, cx, cy, r, col, strength=0.8):
    h, w = img.size[1], img.size[0]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / r
    a = (np.exp(-d * d) * strength)[..., None]
    arr = np.asarray(img).astype(np.float32)
    arr = arr * (1 - a) + np.array(col, np.float32) * a
    return Image.fromarray(arr.clip(0, 255).astype(np.uint8))


def ridge(seed, base, amp, x0=0, x1=CW, step=12, freqs=((1, 900), (0.5, 380), (0.25, 160))):
    rnd = random.Random(seed)
    ph = [rnd.uniform(0, 6.28) for _ in freqs]
    pts = []
    for x in range(x0, x1 + step, step):
        y = base
        for (a, per), p in zip(freqs, ph):
            y -= amp * a * math.sin(x / per * 2 * math.pi / 6.28 * 1.0 + p)
        pts.append((x, y))
    return pts


def fill_ridge(d, pts, col, bottom=CH):
    d.polygon(pts + [(pts[-1][0], bottom), (pts[0][0], bottom)], fill=col)


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def cloud(d, cx, cy, s, col):
    for dx, dy, r in [(-1.2, 0.2, 0.7), (-0.5, -0.25, 0.9), (0.4, -0.35, 1.0), (1.2, 0.1, 0.75), (0, 0.25, 0.8)]:
        d.ellipse([cx + (dx - r) * s, cy + (dy - r * 0.6) * s, cx + (dx + r) * s, cy + (dy + r * 0.6) * s], fill=col)


def soft_layer(base, draw_fn, blur=30):
    lay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(lay))
    lay = lay.filter(ImageFilter.GaussianBlur(blur))
    out = base.convert("RGBA")
    out.alpha_composite(lay)
    return out.convert("RGB")


def texture(img, amount=10, seed=1):
    rnd = np.random.default_rng(seed)
    n = rnd.normal(0, amount, (img.size[1] // 4, img.size[0] // 4, 1)).astype(np.float32)
    n = np.asarray(Image.fromarray(((n[..., 0] + 64).clip(0, 255)).astype(np.uint8)).resize(img.size, Image.BICUBIC)).astype(np.float32) - 64
    arr = np.asarray(img).astype(np.float32) + n[..., None]
    return Image.fromarray(arr.clip(0, 255).astype(np.uint8))


# ------------------------------------------------------------------ 1. Gran Muralla China
def gran_muralla():
    img = grad((86, 118, 178), (252, 205, 160), mid=(205, 170, 190))
    img = glow(img, 2900, 760, 520, (255, 236, 190), 0.9)
    d = ImageDraw.Draw(img)
    d.ellipse([2900 - 120, 760 - 120, 2900 + 120, 760 + 120], fill=(255, 246, 220))
    hazes = [(1050, 150, (150, 150, 190)), (1250, 180, (120, 130, 165)), (1480, 200, (88, 108, 120))]
    for i, (b, a, c) in enumerate(hazes):
        fill_ridge(d, ridge(10 + i, b, a), c)
    # muralla lejana
    far = ridge(2, 1480, 200)
    for j in range(len(far) - 1):
        (x0, y0), (x1, y1) = far[j], far[j + 1]
        d.polygon([(x0, y0 - 18), (x1, y1 - 18), (x1, y1 + 6), (x0, y0 + 6)], fill=(150, 140, 125))
    for k in range(0, len(far), 26):
        x, y = far[k]
        d.rectangle([x - 22, y - 60, x + 22, y + 4], fill=(140, 128, 112))
    # cresta principal
    def yf(x):
        return 1600 - 230 * math.sin(x / 700 + 0.8) - 90 * math.sin(x / 260 + 2.0)
    pts = [(x, yf(x)) for x in range(0, CW + 10, 10)]
    fill_ridge(d, [(x, y + 30) for x, y in pts], (58, 92, 62))
    fill_ridge(d, [(x, y + 160) for x, y in pts], (46, 76, 52))
    wall_top = [(x, y - 70) for x, y in pts]
    d.polygon(wall_top + [(x, y + 40) for x, y in reversed(pts)], fill=(176, 156, 126))
    d.polygon([(x, y + 10) for x, y in pts] + [(x, y + 40) for x, y in reversed(pts)], fill=(132, 114, 92))
    for x in range(0, CW, 44):
        y = yf(x) - 70
        d.rectangle([x, y - 34, x + 24, y + 2], fill=(176, 156, 126))
    # piedras
    for x in range(0, CW, 60):
        for r in range(3):
            y = yf(x) - 50 + r * 22
            d.line([(x + (r % 2) * 30, y), (x + (r % 2) * 30 + 50, y)], fill=(150, 132, 106), width=3)
    for tx in [420, 1450, 2480, 3450]:
        ty = yf(tx)
        w, h = 210, 330
        d.rectangle([tx - w / 2, ty - h, tx + w / 2, ty + 40], fill=(186, 166, 136))
        d.rectangle([tx + w / 2 - 50, ty - h, tx + w / 2, ty + 40], fill=(150, 132, 106))
        for k in range(5):
            cx = tx - w / 2 + 12 + k * 42
            d.rectangle([cx, ty - h - 40, cx + 26, ty - h], fill=(186, 166, 136))
        for k in (-1, 1):
            ax = tx + k * 45
            d.rectangle([ax - 18, ty - h + 90, ax + 18, ty - h + 170], fill=(60, 50, 45))
            d.ellipse([ax - 18, ty - h + 72, ax + 18, ty - h + 108], fill=(60, 50, 45))
    # árboles en primer plano
    rnd = random.Random(4)
    for _ in range(60):
        x = rnd.uniform(0, CW); y = rnd.uniform(1950, 2200); s = rnd.uniform(50, 110)
        d.ellipse([x - s, y - s * 1.2, x + s, y + s], fill=mix((34, 62, 40), (50, 86, 56), rnd.random()))
    img = soft_layer(img, lambda dd: [dd.ellipse([x - 700, 1150, x + 700, 1350], fill=(255, 235, 225, 70)) for x in (700, 2300, 3600)], 60)
    return finish(texture(img, 6))


# ------------------------------------------------------------------ 2. Petra
def petra():
    img = Image.new("RGB", (CW, CH), (196, 112, 88))
    arr = np.asarray(img).astype(np.float32)
    xs = np.arange(CW)[None, :]
    streak = (np.sin(xs / 37.0) * 6 + np.sin(xs / 11.0) * 4 + np.sin(xs / 140.0) * 10)
    ys = np.linspace(0, 1, CH)[:, None]
    arr += (streak + ys * -20)[..., None]
    img = Image.fromarray(arr.clip(0, 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    light = (232, 150, 120); mid = (205, 122, 96); sh = (150, 78, 66); dark = (70, 34, 32)
    cx = 1920
    # nivel inferior
    d.rectangle([cx - 760, 1060, cx + 760, 1880], fill=mid)
    d.rectangle([cx - 760, 1040, cx + 760, 1150], fill=light)
    d.rectangle([cx - 760, 1130, cx + 760, 1150], fill=sh)
    cols = [-640, -420, -200, 200, 420, 640]
    for c in cols:
        x = cx + c
        d.rectangle([x - 48, 1150, x + 48, 1840], fill=light)
        d.rectangle([x + 22, 1150, x + 48, 1840], fill=sh)
        d.rectangle([x - 62, 1150, x + 62, 1200], fill=light)
        d.rectangle([x - 58, 1810, x + 58, 1850], fill=light)
    d.rectangle([cx - 130, 1300, cx + 130, 1860], fill=dark)
    d.polygon([(cx - 520, 1040), (cx + 520, 1040), (cx, 830)], fill=light)
    d.polygon([(cx - 440, 1020), (cx + 440, 1020), (cx, 870)], fill=sh)
    d.rectangle([cx - 800, 1850, cx + 800, 1900], fill=light)
    # nivel superior
    d.rectangle([cx - 760, 820, cx + 760, 900], fill=light)
    d.rectangle([cx - 760, 890, cx + 760, 905], fill=sh)
    for side in (-1, 1):
        px = cx + side * 560
        d.rectangle([px - 200, 380, px + 200, 820], fill=mid)
        for c in (-150, 150):
            d.rectangle([px + c - 38, 420, px + c + 38, 820], fill=light)
            d.rectangle([px + c + 14, 420, px + c + 38, 820], fill=sh)
        d.rectangle([px - 220, 360, px + 220, 420], fill=light)
        inner = px - side * 200
        outer = px + side * 220
        d.polygon([(outer, 360), (inner, 360), (inner, 250)], fill=light)
        d.polygon([(outer - side * 20, 345), (inner + side * 10, 345), (inner + side * 10, 280)], fill=sh)
    # tholos
    d.rectangle([cx - 230, 400, cx + 230, 820], fill=mid)
    for c in (-180, -60, 60, 180):
        d.rectangle([cx + c - 34, 420, cx + c + 34, 820], fill=light)
        d.rectangle([cx + c + 12, 420, cx + c + 34, 820], fill=sh)
    d.rectangle([cx - 250, 360, cx + 250, 420], fill=light)
    d.polygon([(cx - 250, 362), (cx + 250, 362), (cx + 60, 220), (cx - 60, 220)], fill=light)
    d.polygon([(cx + 30, 362), (cx + 250, 362), (cx + 60, 220)], fill=sh)
    d.ellipse([cx - 60, 110, cx + 60, 230], fill=light)
    d.rectangle([cx - 20, 70, cx + 20, 120], fill=light)
    # erosión / sombras de la roca
    img = soft_layer(img, lambda dd: [dd.rectangle([0, 0, CW, 200], fill=(90, 40, 35, 160)),
                                      dd.rectangle([0, 1880, CW, CH], fill=(120, 60, 50, 90))], 80)
    d = ImageDraw.Draw(img)
    # paredes del cañón (Siq) en primer plano
    left = [(0, 0), (900, 0), (760, 300), (820, 700), (620, 1100), (700, 1500), (540, 1900), (600, CH), (0, CH)]
    right = [(CW, 0), (2950, 0), (3100, 350), (3000, 800), (3240, 1250), (3150, 1700), (3300, CH), (CW, CH)]
    d.polygon(left, fill=(96, 44, 40))
    d.polygon(right, fill=(88, 40, 38))
    d.polygon([(0, 0), (700, 0), (560, 400), (620, 900), (430, 1400), (480, CH), (0, CH)], fill=(70, 32, 30))
    # suelo y personas
    d.polygon([(540, 1900), (3300, 1900), (3600, CH), (300, CH)], fill=(214, 160, 120))
    for px, s in [(1500, 1.0), (1580, 0.95), (2300, 1.05)]:
        y = 1980
        d.ellipse([px - 14 * s, y - 120 * s, px + 14 * s, y - 92 * s], fill=(40, 30, 30))
        d.rectangle([px - 16 * s, y - 92 * s, px + 16 * s, y - 30 * s], fill=(40, 30, 30))
        d.rectangle([px - 14 * s, y - 32 * s, px + 14 * s, y], fill=(40, 30, 30))
    img = glow(img, 1920, 1300, 1400, (255, 200, 150), 0.18)
    return finish(texture(img, 9, 2))


# ------------------------------------------------------------------ 3. Cristo Redentor
def cristo():
    img = grad((60, 50, 120), (255, 160, 100), mid=(200, 100, 130))
    img = glow(img, 2400, 1450, 600, (255, 210, 140), 0.9)
    d = ImageDraw.Draw(img)
    # mar
    sea = grad((200, 110, 110), (40, 40, 80), CW, CH - 1500)
    img.paste(sea, (0, 1500))
    d = ImageDraw.Draw(img)
    for i in range(40):
        y = 1520 + i * 15
        w = 300 - i * 4
        d.line([(2400 - w, y), (2400 + w, y)], fill=(255, 200, 150), width=4)
    # Pan de Azúcar
    d.polygon([(2700, 1520), (2850, 1200), (2950, 1050), (3080, 1010), (3180, 1100), (3300, 1350), (3420, 1520)], fill=(70, 50, 90))
    d.polygon([(3350, 1520), (3480, 1360), (3600, 1330), (3700, 1430), (3800, 1520)], fill=(80, 60, 100))
    # Corcovado
    cor = [(0, 1600), (300, 1450), (700, 1300), (1100, 1000), (1350, 760), (1450, 640), (1540, 620), (1620, 700), (1800, 980), (2100, 1250), (2500, 1500), (2700, 1580), (2700, CH), (0, CH)]
    d.polygon(cor, fill=(40, 36, 70))
    d.polygon([(1540, 620), (1620, 700), (1800, 980), (2100, 1250), (2500, 1500), (2700, 1580), (2700, 1620), (2000, 1380), (1650, 900)], fill=(55, 48, 88))
    # ciudad
    d.polygon([(0, 1700), (2700, 1620), (3840, 1640), (3840, CH), (0, CH)], fill=(30, 28, 55))
    rnd = random.Random(7)
    for _ in range(900):
        x = rnd.uniform(0, CW); y = rnd.uniform(1660, CH)
        r = rnd.uniform(2, 5)
        d.ellipse([x - r, y - r, x + r, y + r], fill=rnd.choice([(255, 220, 140), (255, 190, 110), (255, 240, 200)]))
    # estatua
    sx, sy = 1500, 610
    stone = (238, 232, 222); shd = (190, 178, 180)
    d.rectangle([sx - 60, sy - 40, sx + 60, sy + 20], fill=shd)                    # pedestal
    d.polygon([(sx - 70, sy - 40), (sx + 70, sy - 40), (sx + 46, sy - 330), (sx - 46, sy - 330)], fill=stone)  # túnica
    d.polygon([(sx + 10, sy - 40), (sx + 70, sy - 40), (sx + 46, sy - 330), (sx + 20, sy - 330)], fill=shd)
    d.polygon([(sx - 250, sy - 330), (sx + 250, sy - 330), (sx + 250, sy - 300), (sx + 40, sy - 280), (sx - 40, sy - 280), (sx - 250, sy - 300)], fill=stone)  # brazos
    d.polygon([(sx - 50, sy - 345), (sx + 50, sy - 345), (sx + 40, sy - 300), (sx - 40, sy - 300)], fill=stone)
    d.ellipse([sx - 26, sy - 410, sx + 26, sy - 340], fill=stone)
    img = glow(img, sx, sy - 250, 420, (255, 230, 200), 0.18)
    # estrellas
    d = ImageDraw.Draw(img)
    for _ in range(120):
        x = rnd.uniform(0, CW); y = rnd.uniform(0, 600); r = rnd.uniform(1.5, 3.5)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 245, 230))
    return finish(texture(img, 5, 3))


# ------------------------------------------------------------------ 4. Machu Picchu
def machu_picchu():
    img = grad((120, 170, 225), (225, 235, 240))
    d = ImageDraw.Draw(img)
    for cx, cy, s in [(600, 300, 140), (2100, 220, 120), (3300, 380, 160)]:
        cloud(d, cx, cy, s, (250, 250, 252))
    fill_ridge(d, ridge(31, 1000, 260), (150, 175, 190))
    fill_ridge(d, ridge(32, 1200, 220), (110, 145, 150))
    # Huayna Picchu
    hp = [(1700, 1500), (1950, 1000), (2100, 650), (2250, 420), (2380, 360), (2480, 430), (2620, 700), (2800, 1050), (3100, 1350), (3400, 1500)]
    d.polygon(hp, fill=(62, 104, 70))
    d.polygon([(2380, 360), (2480, 430), (2620, 700), (2800, 1050), (3100, 1350), (3400, 1500), (2700, 1500), (2500, 900)], fill=(48, 86, 58))
    for ln in range(8):
        y = 700 + ln * 70
        d.line([(2250 - ln * 20, y), (2450 + ln * 40, y + 30)], fill=(80, 120, 85), width=6)
    fill_ridge(d, ridge(33, 1550, 80, step=20), (120, 150, 90))
    # explanada
    d.polygon([(0, 1450), (900, 1380), (2600, 1420), (3840, 1500), (3840, CH), (0, CH)], fill=(110, 160, 80))
    # terrazas
    for k in range(10):
        y = 1500 + k * 62
        x0 = 0; x1 = 1300 - k * 40
        d.rectangle([x0, y, x1, y + 62], fill=mix((120, 170, 85), (95, 140, 70), k / 10))
        d.rectangle([x0, y + 46, x1, y + 62], fill=(130, 122, 110))
    # edificios de piedra
    rnd = random.Random(5)
    stone = (160, 154, 142); sdark = (120, 114, 104)
    for bx, by, bw, bh in [(1500, 1430, 260, 140), (1800, 1440, 300, 160), (2150, 1450, 220, 130), (2420, 1470, 280, 150),
                           (2750, 1490, 240, 130), (1650, 1600, 320, 150), (2050, 1620, 300, 140), (2450, 1640, 340, 160),
                           (2900, 1650, 260, 130), (3250, 1600, 300, 140), (1450, 1780, 360, 170), (1950, 1800, 300, 150), (2400, 1820, 380, 170)]:
        d.rectangle([bx, by - bh, bx + bw, by], fill=stone)
        d.polygon([(bx, by - bh), (bx + bw / 2, by - bh - 70), (bx + bw, by - bh)], fill=stone)
        d.rectangle([bx + bw - 30, by - bh, bx + bw, by], fill=sdark)
        for wx in range(int(bx + 40), int(bx + bw - 40), 80):
            d.polygon([(wx, by - bh + 90), (wx + 34, by - bh + 90), (wx + 30, by - bh + 40), (wx + 4, by - bh + 40)], fill=(60, 56, 50))
        for r in range(1, int(bh / 30)):
            d.line([(bx, by - r * 30), (bx + bw - 30, by - r * 30)], fill=(140, 134, 124), width=2)
    # primer plano
    d.polygon([(0, 2000), (1200, 1950), (2600, 2050), (3840, 1980), (3840, CH), (0, CH)], fill=(80, 125, 60))
    img = soft_layer(img, lambda dd: [dd.ellipse([x - 900, y - 110, x + 900, y + 110], fill=(255, 255, 255, 150)) for x, y in ((600, 1250), (2900, 1300), (1700, 1180))], 50)
    return finish(texture(img, 5, 4))


# ------------------------------------------------------------------ 5. Chichén Itzá
def chichen_itza():
    img = grad((40, 110, 200), (175, 215, 240))
    d = ImageDraw.Draw(img)
    for cx, cy, s in [(500, 350, 150), (3200, 280, 170), (2000, 180, 100)]:
        cloud(d, cx, cy, s, (255, 255, 255))
    # selva
    rnd = random.Random(9)
    for x in range(-100, CW + 100, 70):
        y = 1620 + rnd.uniform(-40, 30); r = rnd.uniform(70, 130)
        d.ellipse([x - r, y - r, x + r, y + r], fill=mix((40, 90, 50), (60, 115, 60), rnd.random()))
    d.rectangle([0, 1640, CW, CH], fill=(110, 165, 80))
    for _ in range(400):
        x = rnd.uniform(0, CW); y = rnd.uniform(1700, CH)
        d.line([(x, y), (x + 6, y - 18)], fill=(90, 145, 65), width=3)
    cx = 1920; base = 1780; top = 860
    tiers = 9
    bw, tw = 2100, 760
    th = (base - top) / tiers
    for i in range(tiers):
        y0 = base - i * th; y1 = y0 - th
        w0 = bw - (bw - tw) * i / tiers; w1 = bw - (bw - tw) * (i + 1) / tiers
        inset = 18
        d.polygon([(cx - w0 / 2, y0), (cx + w0 / 2, y0), (cx + w0 / 2 - inset, y1 + 14), (cx - w0 / 2 + inset, y1 + 14)], fill=(196, 182, 150))
        d.rectangle([cx - w1 / 2 - 6, y1, cx + w1 / 2 + 6, y1 + 14], fill=(222, 210, 178))
        d.polygon([(cx + w0 / 2 - 260, y0), (cx + w0 / 2, y0), (cx + w0 / 2 - inset, y1 + 14), (cx + w0 / 2 - 260, y1 + 14)], fill=(170, 156, 128))
        d.line([(cx - w0 / 2, y0 - th * 0.5), (cx + w0 / 2, y0 - th * 0.5)], fill=(180, 166, 136), width=3)
    # escalinata
    sw0, sw1 = 380, 300
    d.polygon([(cx - sw0 / 2, base), (cx + sw0 / 2, base), (cx + sw1 / 2, top), (cx - sw1 / 2, top)], fill=(214, 202, 172))
    n = 45
    for k in range(n):
        y = base - (base - top) * k / n
        w = sw0 + (sw1 - sw0) * k / n
        d.line([(cx - w / 2, y), (cx + w / 2, y)], fill=(170, 158, 130), width=4)
    for side in (-1, 1):
        d.polygon([(cx + side * sw0 / 2, base), (cx + side * (sw0 / 2 + 40), base), (cx + side * (sw1 / 2 + 34), top), (cx + side * sw1 / 2, top)], fill=(186, 172, 142))
    # serpiente de luz (equinoccio) sobre la alfarda izquierda
    for k in range(7):
        y0 = top + (base - top) * k / 7; y1 = top + (base - top) * (k + 1) / 7
        x0 = cx - (sw1 / 2 + 34 + (sw0 - sw1) / 2 * k / 7) - 6
        d.polygon([(x0, y0 + 10), (x0 - 30, (y0 + y1) / 2), (x0, y1 - 10)], fill=(250, 238, 200))
    for side in (-1, 1):
        hx = cx + side * (sw0 / 2 + 20)
        d.polygon([(hx - 40, base), (hx + 40, base), (hx + 34, base - 60), (hx - 34, base - 60)], fill=(160, 146, 120))
    # templo superior
    d.rectangle([cx - 330, top - 280, cx + 330, top], fill=(204, 190, 158))
    d.rectangle([cx + 200, top - 280, cx + 330, top], fill=(176, 162, 134))
    d.rectangle([cx - 350, top - 320, cx + 350, top - 260], fill=(222, 210, 178))
    for dx in (-190, 0, 190):
        d.rectangle([cx + dx - 55, top - 200, cx + dx + 55, top], fill=(70, 56, 46))
    img = glow(img, 3000, 200, 900, (255, 250, 230), 0.25)
    return finish(texture(img, 6, 5))


# ------------------------------------------------------------------ 6. Coliseo
def coliseo():
    img = grad((120, 160, 210), (250, 215, 170))
    img = glow(img, 600, 500, 700, (255, 235, 200), 0.6)
    d = ImageDraw.Draw(img)
    for cx, cy, s in [(1100, 300, 120), (2900, 420, 150)]:
        cloud(d, cx, cy, s, (255, 245, 235))
    fill_ridge(d, ridge(61, 1500, 50), (150, 150, 140))
    d.rectangle([0, 1840, CW, CH], fill=(170, 150, 120))
    trav = (222, 196, 156); tshade = (190, 164, 126); arch = (78, 62, 54)
    cx = 1920; R = 1650; NA = 16
    levels = [(1840, 1530), (1530, 1230), (1230, 940), (940, 720)]  # (abajo, arriba)
    def cut(theta):
        # parte derecha derrumbada: menos niveles
        return 2 if theta > 0.38 else 4
    # anillo interior (visible donde la pared exterior falta)
    for i in range(-NA, NA + 1):
        th0 = i / NA * 1.35; th1 = (i + 1) / NA * 1.35
        if th0 < 0.38:
            continue
        x0 = cx + R * 0.86 * math.sin(th0); x1 = cx + R * 0.86 * math.sin(th1)
        d.rectangle([x0, 1000, x1, 1530], fill=(176, 150, 116))
        aw = (x1 - x0) * 0.5
        mx = (x0 + x1) / 2
        for (yb, yt) in ((1530, 1260), (1260, 1010)):
            d.rectangle([mx - aw / 2, yt + 60, mx + aw / 2, yb - 20], fill=(100, 80, 66))
    for i in range(-NA, NA):
        th0 = i / NA * 1.35; th1 = (i + 1) / NA * 1.35
        x0 = cx + R * math.sin(th0); x1 = cx + R * math.sin(th1)
        thm = (th0 + th1) / 2
        lv = cut(thm)
        shade = 0.25 * abs(math.sin(thm)) + (0.15 if thm > 0 else 0)
        col = mix(trav, tshade, shade)
        for li in range(lv):
            yb, yt = levels[li]
            sag = 40 * math.cos(thm)
            yb2, yt2 = yb + sag * 0.3, yt + sag * 0.3
            d.rectangle([x0, yt2, x1 + 1, yb2], fill=col)
            w = x1 - x0
            if li < 3:
                aw = w * 0.56
                mx = (x0 + x1) / 2
                top_y = yt2 + 30 + aw * 0.5
                d.rectangle([mx - aw / 2, top_y, mx + aw / 2, yb2 - 10], fill=arch)
                d.ellipse([mx - aw / 2, top_y - aw / 2, mx + aw / 2, top_y + aw / 2], fill=arch)
                d.rectangle([x0, yt2, x1 + 1, yt2 + 24], fill=mix(col, (240, 220, 185), 0.4))
                d.rectangle([x0, yt2 + 24, x0 + w * 0.12, yb2], fill=mix(col, (240, 220, 185), 0.25))
            else:
                if i % 2 == 0:
                    mx = (x0 + x1) / 2
                    d.rectangle([mx - w * 0.15, yt2 + 90, mx + w * 0.15, yt2 + 150], fill=arch)
                d.rectangle([x0, yt2, x1 + 1, yt2 + 20], fill=mix(col, (240, 220, 185), 0.4))
        if lv == 2 and abs(thm - 0.38) < 0.04:
            pass
    # borde roto
    xb = cx + R * math.sin(0.38)
    d.polygon([(xb - 30, 720), (xb + 40, 720), (xb + 80, 900), (xb + 160, 1050), (xb + 220, 1230), (xb - 30, 1230)], fill=mix(trav, tshade, 0.3))
    for i in range(-NA, NA):
        thm = (i + 0.5) / NA * 1.35
        if thm > 0.38:
            x = cx + R * math.sin(thm)
            d.rectangle([x - 4, 1220, x + 4, 1240], fill=(150, 126, 96))
    # pinos
    for px in (300, 3550):
        d.rectangle([px - 14, 1300, px + 14, 1850], fill=(80, 60, 45))
        d.ellipse([px - 260, 1120, px + 260, 1360], fill=(50, 85, 55))
    # personas
    for px in range(700, 3200, 230):
        y = 1950 + (px % 3) * 30
        d.ellipse([px - 12, y - 100, px + 12, y - 76], fill=(60, 50, 50))
        d.rectangle([px - 14, y - 76, px + 14, y], fill=(60, 50, 50))
    return finish(texture(img, 6, 6))


# ------------------------------------------------------------------ 7. Taj Mahal
def onion(cx, by, R, H, n=60):
    pts_r = []
    for k in range(n + 1):
        s = k / n
        if s < 0.55:
            r = R * (0.82 + 0.18 * math.sin(math.pi / 2 * s / 0.55))
        else:
            r = R * math.cos((s - 0.55) / 0.45 * math.pi / 2) ** 1.6
        pts_r.append((cx + r, by - s * H))
    pts_l = [(2 * cx - x, y) for x, y in reversed(pts_r)]
    return pts_r + pts_l


def taj_building(d, cx, base, white, shade, dark):
    # plataforma
    d.rectangle([cx - 1150, base - 90, cx + 1150, base], fill=shade)
    d.rectangle([cx - 1150, base - 110, cx + 1150, base - 90], fill=white)
    # minaretes
    for mx in (cx - 1080, cx + 1080):
        d.polygon([(mx - 42, base - 110), (mx + 42, base - 110), (mx + 30, base - 1000), (mx - 30, base - 1000)], fill=white)
        d.polygon([(mx + 8, base - 110), (mx + 42, base - 110), (mx + 30, base - 1000), (mx + 6, base - 1000)], fill=shade)
        for by in (base - 380, base - 680, base - 1000):
            d.rectangle([mx - 60, by - 12, mx + 60, by + 10], fill=white)
        d.rectangle([mx - 38, base - 1120, mx + 38, base - 1000], fill=white)
        for px in (mx - 32, mx - 6, mx + 20):
            d.rectangle([px, base - 1100, px + 12, base - 1010], fill=dark)
        d.polygon(onion(mx, base - 1120, 52, 90, 30), fill=white)
        d.line([(mx, base - 1210), (mx, base - 1250)], fill=(200, 180, 120), width=6)
    # cuerpo principal
    bw = 900; bh = 430; top = base - 110 - bh
    d.rectangle([cx - bw / 2, top, cx + bw / 2, base - 110], fill=white)
    d.polygon([(cx - bw / 2, top), (cx - bw / 2 - 90, top + 60), (cx - bw / 2 - 90, base - 110), (cx - bw / 2, base - 110)], fill=shade)
    d.polygon([(cx + bw / 2, top), (cx + bw / 2 + 90, top + 60), (cx + bw / 2 + 90, base - 110), (cx + bw / 2, base - 110)], fill=mix(white, shade, 0.5))
    # iwan central
    iw = 300
    d.rectangle([cx - iw / 2 - 30, top - 40, cx + iw / 2 + 30, base - 110], fill=white)
    d.rectangle([cx - iw / 2, top + 140, cx + iw / 2, base - 110], fill=shade)
    d.polygon([(cx - iw / 2, top + 140), (cx - iw / 2 + 20, top + 60), (cx, top + 20), (cx + iw / 2 - 20, top + 60), (cx + iw / 2, top + 140)], fill=shade)
    d.rectangle([cx - 60, top + 300, cx + 60, base - 110], fill=dark)
    d.polygon([(cx - 60, top + 300), (cx, top + 240), (cx + 60, top + 300)], fill=dark)
    # arcos laterales en dos pisos
    for side in (-1, 1):
        for k in (0, 1):
            ax = cx + side * (230 + k * 150 - 30)
            for y0 in (top + 60, top + 320):
                d.rectangle([ax - 50, y0 + 60, ax + 50, y0 + 220], fill=shade)
                d.polygon([(ax - 50, y0 + 60), (ax, y0 + 10), (ax + 50, y0 + 60)], fill=shade)
    # chhatris
    for ox in (-330, 330):
        x = cx + ox
        d.rectangle([x - 90, top - 160, x + 90, top], fill=white)
        for px in (x - 80, x - 25, x + 30):
            d.rectangle([px, top - 140, px + 40, top - 20], fill=shade)
        d.polygon(onion(x, top - 160, 100, 170, 40), fill=white)
        d.line([(x, top - 330), (x, top - 380)], fill=(200, 180, 120), width=8)
    # tambor y cúpula
    d.rectangle([cx - 240, top - 230, cx + 240, top - 30], fill=white)
    d.rectangle([cx + 120, top - 230, cx + 240, top - 30], fill=mix(white, shade, 0.6))
    DH = 470
    dome = onion(cx, top - 230, 280, DH)
    d.polygon(dome, fill=white)
    d.polygon([(x, y) for x, y in dome if x >= cx + 60] + [(cx + 60, top - 230)], fill=mix(white, shade, 0.55))
    d.line([(cx, top - 230 - DH + 10), (cx, top - 230 - DH - 110)], fill=(205, 182, 120), width=12)
    d.ellipse([cx - 20, top - 230 - DH - 70, cx + 20, top - 230 - DH - 30], fill=(205, 182, 120))


def taj_mahal():
    img = grad((120, 150, 210), (250, 215, 205), mid=(220, 190, 215))
    img = glow(img, 1920, 1200, 900, (255, 230, 220), 0.35)
    d = ImageDraw.Draw(img)
    white = (246, 242, 238); shade = (206, 198, 210); dark = (90, 80, 96)
    base = 1440
    # árboles detrás
    rnd = random.Random(12)
    for x in range(-50, CW + 50, 90):
        if 700 < x < 3140:
            h = 1240
        else:
            h = 1180
        r = rnd.uniform(70, 110)
        d.ellipse([x - r, h - r * 1.3, x + r, base], fill=mix((60, 100, 80), (80, 125, 95), rnd.random()))
    taj_building(d, cx=1920, base=base, white=white, shade=shade, dark=dark)
    # jardín y estanque con reflejo
    d.rectangle([0, base, CW, CH], fill=(80, 130, 80))
    refl = img.crop((0, 0, CW, base)).transpose(Image.FLIP_TOP_BOTTOM).resize((CW, int(base * 0.55)))
    refl = Image.blend(refl, Image.new("RGB", refl.size, (90, 120, 170)), 0.35)
    mask = Image.new("L", (CW, CH), 0)
    md = ImageDraw.Draw(mask)
    pool = [(1920 - 260, base), (1920 + 260, base), (1920 + 520, CH), (1920 - 520, CH)]
    md.polygon(pool, fill=255)
    layer = Image.new("RGB", (CW, CH), (0, 0, 0))
    layer.paste(refl, (0, base))
    img.paste(layer, (0, 0), mask)
    d = ImageDraw.Draw(img)
    for side in (-1, 1):
        d.polygon([(1920 + side * 260, base), (1920 + side * 300, base), (1920 + side * 600, CH), (1920 + side * 520, CH)], fill=(225, 210, 200))
    # cipreses
    for k in range(7):
        t = k / 6
        for side in (-1, 1):
            x = 1920 + side * (340 + t * 560 + 90 * t)
            y = base + 40 + t * (CH - base - 40)
            s = 0.6 + t * 1.6
            d.ellipse([x - 30 * s, y - 220 * s, x + 30 * s, y], fill=(36, 70, 50))
    return finish(texture(img, 4, 7))


# ------------------------------------------------------------------ Pirámides de Guiza (mención de honor)
def piramides():
    img = grad((40, 50, 100), (250, 170, 100), mid=(190, 110, 110))
    img = glow(img, 3000, 1350, 500, (255, 220, 150), 0.9)
    d = ImageDraw.Draw(img)
    d.ellipse([3000 - 110, 1350 - 110, 3000 + 110, 1350 + 110], fill=(255, 230, 170))
    d.rectangle([0, 1460, CW, CH], fill=(214, 156, 100))
    for cx, w, h in [(800, 1100, 700), (1900, 1500, 950), (2950, 700, 430)]:
        b = 1520
        d.polygon([(cx - w / 2, b), (cx, b - h), (cx + w * 0.12, b)], fill=(226, 170, 110))
        d.polygon([(cx + w * 0.12, b), (cx, b - h), (cx + w / 2, b)], fill=(150, 96, 70))
        for k in range(1, 14):
            y = b - h * k / 14
            hw = w / 2 * (1 - k / 14)
            d.line([(cx - hw, y), (cx + w * 0.12 * (1 - k / 14), y)], fill=(204, 150, 96), width=3)
    rnd = random.Random(3)
    for k in range(6):
        y = 1600 + k * 100
        pts = [(x, y + 30 * math.sin(x / 400 + k)) for x in range(0, CW + 20, 20)]
        fill_ridge(d, pts, mix((220, 160, 104), (180, 120, 80), k / 6))
    # camellos
    for cx in (900, 1050):
        y = 1980
        d.ellipse([cx - 80, y - 150, cx + 80, y - 70], fill=(60, 40, 35))
        d.ellipse([cx - 40, y - 200, cx + 20, y - 120], fill=(60, 40, 35))
        d.polygon([(cx + 60, y - 120), (cx + 140, y - 230), (cx + 170, y - 230), (cx + 90, y - 100)], fill=(60, 40, 35))
        for lx in (-60, -30, 40, 70):
            d.rectangle([cx + lx - 8, y - 90, cx + lx + 8, y], fill=(60, 40, 35))
    return finish(texture(img, 6, 8))


ALL = {
    "muralla": gran_muralla, "petra": petra, "cristo": cristo, "machu": machu_picchu,
    "chichen": chichen_itza, "coliseo": coliseo, "taj": taj_mahal, "piramides": piramides,
}

if __name__ == "__main__":
    import sys, os
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    for k, fn in ALL.items():
        fn().resize((960, 540), Image.LANCZOS).save(os.path.join(out, k + ".png"))
        print(k)
