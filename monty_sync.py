import os, sys, math, random, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H = 1920, 1080
FPS = 30
TOTAL = 186.0
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out2")
os.makedirs(OUT, exist_ok=True)

FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
_fc = {}
def font(sz):
    sz = int(sz)
    if sz not in _fc:
        _fc[sz] = ImageFont.truetype(FB, sz)
    return _fc[sz]

WHITE = (255, 255, 255); AMBER = (255, 196, 92); TEAL = (80, 220, 190)
CORAL = (255, 112, 100); SOFT = (196, 208, 236); DARK = (14, 20, 36)
BGC = (17, 22, 42)

def smooth(a, b, t):
    if t <= a: return 0.0
    if t >= b: return 1.0
    u = (t - a) / (b - a)
    return u * u * (3 - 2 * u)

def pulse(t, a, b, fi=0.4, fo=0.4):
    return smooth(a, a + fi, t) * (1 - smooth(b - fo, b, t))

def C(col, a=1.0):
    return tuple(col) + (int(255 * max(0.0, min(1.0, a))),)

def make_bg():
    ys = np.linspace(0, 1, H)[:, None, None]
    top = np.array([26, 34, 64], np.float32); bot = np.array([12, 15, 30], np.float32)
    arr = np.broadcast_to(top + (bot - top) * ys, (H, W, 3)).copy()
    xs = np.linspace(-1, 1, W)[None, :, None]
    arr *= (1 - 0.18 * xs ** 2)
    return Image.fromarray(arr.clip(0, 255).astype(np.uint8))

BG = make_bg()
VEIL = Image.new("RGB", (W, H), BGC)

# ---------------------------------------------------------------- simulation
def simulate(n=1000, seed=11):
    rnd = random.Random(seed)
    cs, cw = [], []
    a = b = 0
    for _ in range(n):
        car = rnd.randrange(3); pick = 0
        host = rnd.choice([x for x in range(3) if x != pick and x != car])
        other = [x for x in range(3) if x != pick and x != host][0]
        a += 1 if pick == car else 0
        b += 1 if other == car else 0
        cs.append(a); cw.append(b)
    return cs, cw

CS, CW = simulate()
STAY_N, SW_N = CS[-1], CW[-1]

# ---------------------------------------------------------------- captions (also the voice-over script)
CAPS = [
    (0.5, 5.0, "En 1990, una columnista de revista respondió un problema de probabilidad."),
    (5.2, 10.5, "Recibió miles de cartas diciendo que se había equivocado. Muchas, de gente con doctorados."),
    (10.8, 14.5, "Pero ella tenía razón. Veamos por qué."),
    (15.0, 19.5, "Imagina que estás en un concurso. Hay tres puertas."),
    (19.8, 25.5, "Detrás de una hay un auto. Detrás de cada una de las otras dos, una cabra."),
    (25.8, 30.5, "Tú eliges una puerta. Supongamos que eliges la número 1."),
    (31.0, 36.5, "Ahora el presentador, que sabe dónde está el auto, abre otra puerta."),
    (36.8, 41.5, "Siempre abre una puerta con una cabra. Digamos que abre la número 3."),
    (42.0, 46.8, "Y te pregunta: ¿quieres cambiar a la puerta 2, o te quedas con la 1?"),
    (47.5, 53.0, "Casi todos piensan lo mismo: quedan dos puertas, así que es 50 y 50."),
    (53.3, 58.2, "Parece lógico. Pero es incorrecto: cambiar te da el doble de probabilidades."),
    (59.0, 64.5, "Al principio, tu puerta tiene 1 probabilidad entre 3 de esconder el auto."),
    (64.8, 70.5, "Las otras dos puertas, juntas, tienen 2 entre 3."),
    (70.8, 77.0, "El presentador sabe dónde está el auto y nunca lo abre. Siempre revela una cabra."),
    (77.3, 84.0, "Por eso, cuando abre la puerta 3, esos 2 tercios no desaparecen: pasan completos a la puerta que queda cerrada."),
    (84.3, 89.5, "Tu puerta sigue valiendo 1 tercio. La otra vale 2 tercios."),
    (89.8, 94.4, "Cambiar duplica tus posibilidades de ganar."),
    (95.5, 100.5, "Si todavía dudas, miremos los tres casos posibles. Siempre eliges la puerta 1."),
    (101.0, 107.0, "Caso A: el auto está en la 1. Si cambias, pierdes."),
    (107.3, 113.5, "Caso B: el auto está en la 2. El presentador abre la 3. Si cambias, ganas."),
    (113.8, 120.0, "Caso C: el auto está en la 3. El presentador abre la 2. Si cambias, ganas."),
    (120.3, 126.5, "Cambiando ganas en 2 de 3 casos. Quedándote, solo en 1 de 3."),
    (127.5, 132.5, "Para comprobarlo, simulé este juego 1.000 veces en una computadora."),
    (132.8, 139.0, "En cada partida comparé qué habría pasado quedándose y qué habría pasado cambiando."),
    (139.3, 146.0, "El resultado: quedarse ganó %d veces y cambiar ganó %d." % (STAY_N, SW_N)),
    (146.3, 152.5, "Muy cerca de un tercio contra dos tercios, como predice la teoría."),
    (153.6, 160.0, "Ojo: esto funciona porque el presentador sabe dónde está el auto y nunca lo abre."),
    (160.3, 166.3, "Si abriera una puerta al azar, el resultado sería distinto."),
    (166.8, 172.8, "La intuición nos engaña porque ignora lo que sabe el presentador."),
    (173.2, 179.2, "Si te gustó, suscríbete para ver más ideas explicadas con animaciones."),
]

def wrap(d, txt, f, maxw):
    words, lines, cur = txt.split(), [], ""
    for w in words:
        t2 = (cur + " " + w).strip()
        if d.textlength(t2, font=f) <= maxw: cur = t2
        else:
            lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines

def captions(fr, t):
    d = ImageDraw.Draw(fr, "RGBA")
    f = font(42)
    for t0, t1, txt in CAPS:
        a = pulse(t, t0, t1, 0.3, 0.3)
        if a <= 0.01: continue
        lines = wrap(d, txt, f, 1560)
        if len(lines) == 2 and len(lines[1]) < 14:
            lines = wrap(d, txt, f, 1100)
        lh = 54; bh = lh * len(lines); y0 = 995 - bh / 2
        mw = max(d.textlength(l, font=f) for l in lines)
        d.rounded_rectangle((960 - mw / 2 - 36, y0 - 20, 960 + mw / 2 + 36, y0 + bh + 14), radius=30, fill=(0, 0, 0, int(135 * a)))
        for i, l in enumerate(lines):
            d.text((960, y0 + i * lh + lh / 2), l, font=f, fill=(255, 255, 255, int(255 * a)), anchor="mm")

# ---------------------------------------------------------------- drawing helpers
def text_c(d, x, y, s, f, fill, a=1.0, anchor="mm", shadow=True):
    if a <= 0.01: return
    if shadow: d.text((x + 3, y + 4), s, font=f, fill=(0, 0, 0, int(150 * a)), anchor=anchor)
    d.text((x, y), s, font=f, fill=C(fill, a), anchor=anchor)

def pill(d, cx, cy, s, size, fill, txt=DARK, a=1.0, padx=34, pady=16):
    if a <= 0.01: return
    f = font(size); tw = d.textlength(s, font=f)
    w = tw + 2 * padx; h = size + 2 * pady
    d.rounded_rectangle((cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), radius=h / 2, fill=C(fill, a * 0.95))
    d.text((cx, cy), s, font=f, fill=C(txt, a), anchor="mm")

def draw_content(d, x0, base, s, content, a=1.0):
    def P(x, y): return (x0 + x * s, base - y * s)
    lw = lambda v: max(1, int(v * s))
    if content == "car":
        d.rounded_rectangle((*P(30, 125), *P(270, 60)), radius=int(18 * s), fill=C((214, 60, 60), a))
        d.polygon([P(85, 125), P(125, 185), P(215, 185), P(250, 125)], fill=C((190, 48, 52), a))
        d.polygon([P(100, 128), P(130, 172), P(168, 172), P(168, 128)], fill=C((170, 220, 240), a))
        d.polygon([P(176, 128), P(176, 172), P(210, 172), P(236, 128)], fill=C((170, 220, 240), a))
        for cx in (85, 215):
            d.ellipse((*P(cx - 32, 88), *P(cx + 32, 24)), fill=C((28, 28, 38), a))
            d.ellipse((*P(cx - 14, 70), *P(cx + 14, 42)), fill=C((170, 176, 190), a))
        d.ellipse((*P(258, 108), *P(272, 92)), fill=C((255, 230, 150), a))
    else:
        body = C((232, 228, 218), a)
        d.ellipse((*P(60, 150), *P(220, 80)), fill=body)
        for lx in (80, 108, 168, 196):
            d.rectangle((*P(lx, 95), *P(lx + 14, 30)), fill=C((210, 205, 194), a))
            d.rectangle((*P(lx, 34), *P(lx + 14, 28)), fill=C((60, 50, 44), a))
        d.polygon([P(185, 135), P(215, 150), P(232, 170), P(215, 185)], fill=body)
        d.ellipse((*P(205, 205), *P(275, 160)), fill=body)
        d.line([P(228, 200), P(222, 232)], fill=C((130, 110, 86), a), width=lw(6))
        d.line([P(246, 200), P(258, 232)], fill=C((130, 110, 86), a), width=lw(6))
        d.ellipse((*P(205, 196), *P(225, 184)), fill=C((205, 198, 186), a))
        d.ellipse((*P(252, 190), *P(260, 182)), fill=C((30, 30, 40), a))
        d.ellipse((*P(266, 178), *P(276, 168)), fill=C((200, 160, 160), a))
        d.polygon([P(255, 162), P(268, 162), P(262, 138)], fill=C((240, 238, 230), a))
        d.polygon([P(60, 140), P(40, 160), P(66, 128)], fill=body)

def door(d, cx, base, s, num, openv, content, outline=None, dim=0.0, a=1.0):
    w = 300 * s; h = 480 * s; x0 = cx - w / 2; top = base - h
    d.rectangle((x0 - 14 * s, top - 14 * s, x0 + w + 14 * s, base), fill=C((74, 46, 30), a))
    d.rectangle((x0, top, x0 + w, base), fill=C((9, 11, 24), a))
    if openv > 0.02 and content:
        draw_content(d, x0, base, s, content, a)
    pw = w * (1 - 0.86 * openv); sk = openv * 46 * s
    if pw > 4:
        d.polygon([(x0, top), (x0 + pw, top + sk), (x0 + pw, base - sk * 0.4), (x0, base)], fill=C((176, 112, 60), a))
        if openv < 0.35:
            ins = 26 * s
            d.rectangle((x0 + ins, top + ins, x0 + pw - ins, top + h * 0.45), outline=C((140, 86, 46), a), width=max(1, int(5 * s)))
            d.rectangle((x0 + ins, top + h * 0.55, x0 + pw - ins, base - ins), outline=C((140, 86, 46), a), width=max(1, int(5 * s)))
        kx = x0 + pw - 30 * s; ky = base - h * 0.45; kr = 11 * s
        d.ellipse((kx - kr, ky - kr, kx + kr, ky + kr), fill=C((240, 200, 90), a))
        if openv < 0.4 and num:
            d.text((x0 + pw / 2, top + h * 0.22), num, font=font(110 * s), fill=C((250, 230, 200), a * (1 - openv / 0.4)), anchor="mm")
    if dim > 0:
        d.rectangle((x0 - 14 * s, top - 14 * s, x0 + w + 14 * s, base), fill=(8, 10, 22, int(160 * dim)))
    if outline:
        d.rectangle((x0 - 22 * s, top - 22 * s, x0 + w + 22 * s, base + 8 * s), outline=outline, width=max(2, int(8 * s)))

def presenter(d, cx, a):
    d.polygon([(cx - 52, 600), (cx + 52, 600), (cx + 64, 800), (cx - 64, 800)], fill=C((52, 62, 108), a))
    d.polygon([(cx - 18, 600), (cx + 18, 600), (cx, 660)], fill=C((240, 240, 246), a))
    d.polygon([(cx - 20, 628), (cx, 640), (cx - 20, 652)], fill=C(CORAL, a))
    d.polygon([(cx + 20, 628), (cx, 640), (cx + 20, 652)], fill=C(CORAL, a))
    d.ellipse((cx - 40, 520, cx + 40, 600), fill=C((236, 190, 150), a))
    d.pieslice((cx - 42, 512, cx + 42, 598), 180, 360, fill=C((50, 40, 36), a))
    d.ellipse((cx - 17, 556, cx - 9, 564), fill=C((30, 30, 40), a))
    d.ellipse((cx + 9, 556, cx + 17, 564), fill=C((30, 30, 40), a))
    d.arc((cx - 16, 566, cx + 16, 588), 20, 160, fill=C((150, 70, 60), a), width=3)
    d.line([(cx + 60, 690), (cx + 98, 646)], fill=C((30, 30, 40), a), width=6)
    d.ellipse((cx + 90, 632, cx + 112, 654), fill=C((90, 96, 110), a))
    text_c(d, cx, 836, "PRESENTADOR", font(26), SOFT, a)

def envelope(d, cx, cy, ang, a):
    w, h = 130, 86
    def R(x, y):
        c, s = math.cos(ang), math.sin(ang)
        return (cx + x * c - y * s, cy + x * s + y * c)
    d.polygon([R(-w / 2, -h / 2), R(w / 2, -h / 2), R(w / 2, h / 2), R(-w / 2, h / 2)], fill=(238, 232, 214, int(255 * a)))
    ln = (170, 160, 140, int(255 * a))
    d.line([R(-w / 2, -h / 2), R(0, 8), R(w / 2, -h / 2)], fill=ln, width=3)
    d.line([R(-w / 2, h / 2), R(-14, -6)], fill=ln, width=3)
    d.line([R(w / 2, h / 2), R(14, -6)], fill=ln, width=3)

_er = random.Random(5)
ENV = []
for i in range(26):
    side = _er.random() < 0.5
    x = _er.randint(70, 235) if side else _er.randint(1665, 1860)
    y = _er.randint(100, 540) if _er.random() < 0.55 else _er.randint(740, 880)
    ENV.append((5.0 + (10.8 - 5.0) * i / 25.0 + _er.uniform(-0.1, 0.1), x, y, _er.uniform(-0.45, 0.45)))

# ---------------------------------------------------------------- scenes
def scene_A(fr, d, t):
    text_c(d, 960, 360, "LA PARADOJA DE", font(120), WHITE, smooth(0.3, 1.1, t))
    text_c(d, 960, 520, "MONTY HALL", font(170), AMBER, smooth(0.5, 1.3, t))
    text_c(d, 960, 670, "El problema de probabilidad que enfureció a miles de lectores", font(40), SOFT, smooth(1.4, 2.2, t))
    for ti, x, y, ang in ENV:
        p = smooth(ti, ti + 0.8, t)
        if p > 0.01:
            envelope(d, x, y - (1 - p) * (y + 200), ang, p)

DOORX = [460, 960, 1460]
BASE = 820
CONTENT = ["goat", "car", "goat"]

def open3_at(t):
    if t < 58.6: return smooth(36.3, 37.6, t)
    if t < 70.8: return 1 - smooth(58.6, 59.8, t)
    return smooth(70.8, 72.0, t)

def scene_doors(fr, d, t):
    if t < 31.0: lab, la = "1 · EL JUEGO", pulse(t, 15.2, 31.0)
    elif t < 47.2: lab, la = "2 · EL PRESENTADOR", pulse(t, 31.0, 47.2)
    elif t < 58.7: lab, la = "3 · LA INTUICIÓN", pulse(t, 47.2, 58.7)
    else: lab, la = "4 · LA EXPLICACIÓN", pulse(t, 58.7, 94.9)
    text_c(d, 70, 58, lab, font(34), AMBER, la, anchor="lm", shadow=False)

    d.rectangle((110, BASE, 1810, BASE + 14), fill=(6, 8, 18, 170))
    op3 = open3_at(t)
    dim3 = 0.0
    if 47.6 <= t < 58.7: dim3 = 0.45 * pulse(t, 47.6, 58.7, 0.5, 0.5)
    if t >= 72: dim3 = max(dim3, 0.45 * smooth(77.3, 78.3, t))
    for i in range(3):
        base = BASE + 560 * (1 - smooth(15.0 + 0.25 * i, 16.6 + 0.25 * i, t))
        outline = None
        if i == 0 and 26.6 <= t < 58.7:
            outline = C(AMBER, smooth(26.6, 27.4, t) * (1 - smooth(58.0, 58.7, t)))
        door(d, DOORX[i], base, 1.0, str(i + 1), op3 if i == 2 else 0.0, CONTENT[i], outline=outline, dim=dim3 if i == 2 else 0.0)

    # legend (1 auto, 2 cabras)
    la = pulse(t, 20.0, 30.6)
    if la > 0.01:
        draw_content(d, 620, 262, 0.33, "car", la)
        text_c(d, 735, 226, "1 auto", font(44), WHITE, la, anchor="lm")
        draw_content(d, 1010, 262, 0.33, "goat", la)
        draw_content(d, 1085, 262, 0.33, "goat", la)
        text_c(d, 1180, 226, "2 cabras", font(44), WHITE, la, anchor="lm")
    pill(d, DOORX[0], 285, "TU ELECCIÓN", 34, AMBER, a=pulse(t, 26.6, 46.8))
    pill(d, DOORX[2], 285, "CABRA", 34, (240, 240, 236), a=pulse(t, 37.8, 46.8))
    pa = pulse(t, 31.0, 46.8)
    if pa > 0.01: presenter(d, 1790, pa)
    ba = pulse(t, 42.4, 47.0)
    if ba > 0.01:
        d.rounded_rectangle((380, 120, 900, 210), radius=44, fill=C(CORAL, ba * 0.95))
        d.text((640, 165), "QUEDARME · puerta 1", font=font(36), fill=C(DARK, ba), anchor="mm")
        d.rounded_rectangle((1020, 120, 1540, 210), radius=44, fill=C(TEAL, ba * 0.95))
        d.text((1280, 165), "CAMBIAR · puerta 2", font=font(36), fill=C(DARK, ba), anchor="mm")

    # 50/50 intuition
    a50 = pulse(t, 47.6, 58.2, 0.5, 0.5)
    pill(d, DOORX[0], 285, "50%", 44, AMBER, a=a50)
    pill(d, DOORX[1], 285, "50%", 44, AMBER, a=a50)
    xa = smooth(54.2, 55.0, t) * (1 - smooth(57.7, 58.4, t))
    if xa > 0.01:
        for cx in (DOORX[0], DOORX[1]):
            d.line([(cx - 52, 248), (cx + 52, 322)], fill=C(CORAL, xa), width=11)
            d.line([(cx - 52, 322), (cx + 52, 248)], fill=C(CORAL, xa), width=11)
        text_c(d, 960, 170, "¡INCORRECTO!", font(84), CORAL, xa)

    # explanation
    ea = smooth(59.6, 60.4, t) * (1 - smooth(94.0, 94.8, t))
    c1 = TEAL if t < 84.3 else CORAL
    pill(d, DOORX[0], 285, "1/3", 44, c1, a=ea)
    a23 = smooth(59.6, 60.4, t) * (1 - smooth(64.6, 65.2, t))
    pill(d, DOORX[1], 285, "1/3", 44, TEAL, a=a23)
    pill(d, DOORX[2], 285, "1/3", 44, TEAL, a=a23)
    ba2 = smooth(65.0, 65.8, t) * (1 - smooth(77.3, 78.3, t))
    if ba2 > 0.01:
        xl, xr = DOORX[1] - 150, DOORX[2] + 150
        d.line([(xl, 262), (xr, 262)], fill=C(TEAL, ba2), width=7)
        d.line([(xl, 262), (xl, 292)], fill=C(TEAL, ba2), width=7)
        d.line([(xr, 262), (xr, 292)], fill=C(TEAL, ba2), width=7)
        pill(d, (xl + xr) / 2, 205, "2/3 juntas", 40, TEAL, a=ba2)
    pill(d, DOORX[2], 285, "0", 44, CORAL, a=smooth(72.2, 73.0, t) * (1 - smooth(77.3, 78.0, t)))
    p = smooth(77.4, 79.6, t)
    aa = 1 - smooth(84.0, 85.0, t)
    if p > 0.01 and aa > 0.01:
        p0 = (DOORX[2], 258); pc = (1210, 130); p1 = (DOORX[1] + 20, 258)
        def bez(u):
            return ((1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * pc[0] + u * u * p1[0],
                    (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * pc[1] + u * u * p1[1])
        pts = [bez(p * i / 40.0) for i in range(41)]
        d.line(pts, fill=C(AMBER, aa), width=9, joint="curve")
        if p > 0.97:
            tip = pts[-1]
            dx = 2 * (1 - p) * (pc[0] - p0[0]) + 2 * p * (p1[0] - pc[0])
            dy = 2 * (1 - p) * (pc[1] - p0[1]) + 2 * p * (p1[1] - pc[1])
            n = math.hypot(dx, dy) or 1; dx, dy = dx / n, dy / n
            bx, by = tip[0] - 30 * dx, tip[1] - 30 * dy
            d.polygon([tip, (bx - 17 * dy, by + 17 * dx), (bx + 17 * dy, by - 17 * dx)], fill=C(AMBER, aa))
    big = smooth(79.4, 80.2, t) * (1 - smooth(94.0, 94.8, t))
    pill(d, DOORX[1], 285, "2/3", int(44 + 14 * smooth(79.4, 80.2, t)), TEAL, a=big)
    ta = pulse(t, 84.4, 94.4, 0.5, 0.5)
    pill(d, DOORX[0], 862, "QUEDARSE: 1/3", 34, CORAL, a=ta)
    pill(d, DOORX[1], 862, "CAMBIAR: 2/3", 34, TEAL, a=ta)
    text_c(d, 960, 175, "¡El doble!", font(84), AMBER, pulse(t, 89.8, 94.4, 0.4, 0.4))

def scene_F(fr, d, t):
    text_c(d, 960, 150, "Los tres casos posibles", font(66), WHITE, smooth(95.2, 96.0, t))
    text_c(d, 70, 58, "5 · LOS TRES CASOS", font(34), AMBER, smooth(95.2, 96.0, t), anchor="lm", shadow=False)
    cols = [360, 960, 1560]
    tags = ["CASO A", "CASO B", "CASO C"]
    hosts = ["Abre la 2 o la 3", "El presentador abre la 3", "El presentador abre la 2"]
    win = [False, True, True]
    rt = [(101.0, 107.0), (107.3, 113.5), (113.8, 120.0)]
    for k in range(3):
        a = smooth(96.0 + 0.3 * k, 97.0 + 0.3 * k, t)
        cx = cols[k]
        act = pulse(t, rt[k][0] - 0.4, rt[k][1] + 0.2, 0.4, 0.4) * a
        if act > 0.01:
            d.rounded_rectangle((cx - 250, 320, cx + 250, 790), radius=30, outline=C(AMBER, act * 0.7), width=4)
        text_c(d, cx, 365, tags[k], font(40), AMBER, a)
        for i in range(3):
            dx = cx + (i - 1) * 150
            content = "car" if i == k else "goat"
            door(d, dx, 640, 0.42, "", 1.0, content, outline=C(AMBER, a * 0.9) if i == 0 else None, a=a)
            text_c(d, dx, 664, str(i + 1), font(28), SOFT, a)
        text_c(d, cx, 700, hosts[k], font(28), SOFT, a)
        ra = smooth(rt[k][0], rt[k][0] + 0.5, t)
        if ra > 0.01:
            pill(d, cx, 764, "Si cambias: " + ("GANAS" if win[k] else "PIERDES"), 34, TEAL if win[k] else CORAL, a=ra)
    ta = smooth(120.3, 121.1, t)
    pill(d, 600, 845, "CAMBIAR: gana en 2 de 3", 36, TEAL, a=ta)
    pill(d, 1320, 845, "QUEDARSE: gana en 1 de 3", 36, CORAL, a=ta)

def scene_G(fr, d, t):
    a = smooth(127.6, 128.4, t)
    text_c(d, 70, 58, "6 · LA PRUEBA", font(34), AMBER, a, anchor="lm", shadow=False)
    text_c(d, 960, 130, "Simulación: 1.000 partidas", font(62), WHITE, a)
    g = int(round(1000 * smooth(133.5, 148.5, t)))
    X0, X1, Y0, Y1 = 170, 1200, 250, 760
    def Yp(p): return Y1 - (Y1 - Y0) * p
    def Xg(n): return X0 + (X1 - X0) * n / 1000.0
    for p, lab in ((0, "0%"), (1 / 3.0, "33%"), (2 / 3.0, "67%"), (1, "100%")):
        d.line([(X0, Yp(p)), (X1, Yp(p))], fill=(90, 106, 150, int(200 * a)), width=2)
        d.text((X0 - 16, Yp(p)), lab, font=font(28), fill=C(SOFT, a), anchor="rm")
    for n, lab in ((0, "0"), (500, "500"), (1000, "1.000 partidas")):
        d.text((Xg(n), 790), lab, font=font(26), fill=C(SOFT, a), anchor="mm" if n < 1000 else "rm")
    if g >= 2:
        ps = [(Xg(i), Yp(CS[i - 1] / float(i))) for i in range(1, g + 1)]
        pw = [(Xg(i), Yp(CW[i - 1] / float(i))) for i in range(1, g + 1)]
        d.line(ps, fill=C(CORAL, a), width=5, joint="curve")
        d.line(pw, fill=C(TEAL, a), width=5, joint="curve")
    st = CS[g - 1] if g > 0 else 0
    sw = CW[g - 1] if g > 0 else 0
    def pct(n): return ("%.1f" % (100.0 * n / g)).replace(".", ",") + "%" if g > 0 else "—"
    cards = [(230, 350, "PARTIDAS", WHITE, "%d / 1.000" % g if g < 1000 else "1.000 / 1.000"),
             (390, 540, "SE QUEDÓ", CORAL, "%d · %s" % (st, pct(st))),
             (580, 730, "CAMBIÓ", TEAL, "%d · %s" % (sw, pct(sw)))]
    for y0, y1, lab, col, val in cards:
        d.rounded_rectangle((1290, y0, 1800, y1), radius=24, fill=(30, 40, 74, int(235 * a)))
        d.text((1322, y0 + 34), lab, font=font(28), fill=C(col, a), anchor="lm")
        d.text((1322, y0 + 92), val, font=font(54), fill=C(WHITE, a), anchor="lm")
    text_c(d, 700, 215, "Porcentaje de partidas ganadas", font(30), SOFT, a)

def scene_H(fr, d, t):
    text_c(d, 70, 58, "7 · LA CLAVE", font(34), AMBER, smooth(153.8, 154.6, t), anchor="lm", shadow=False)
    cards = [
        (153.6, 160.0, ["El presentador sabe", "dónde está el auto"], "y nunca lo abre", TEAL),
        (160.3, 166.3, ["Si abriera al azar,", "sería 50% / 50%"], "", AMBER),
        (166.8, 172.8, ["La intuición ignora", "lo que sabe el presentador"], "", CORAL),
        (173.2, 179.2, ["Suscríbete para ver más", "ideas explicadas con animaciones"], "", TEAL),
    ]
    for t0, t1, lines, sub, col in cards:
        a = pulse(t, t0, t1, 0.5, 0.4)
        if a <= 0.01: continue
        text_c(d, 960, 380, lines[0], font(96), WHITE, a)
        text_c(d, 960, 510, lines[1], font(96 if len(lines[1]) < 26 else 72), col, a)
        if sub: text_c(d, 960, 640, sub, font(60), SOFT, a)

def scene_E(fr, d, t):
    a = smooth(180.0, 181.0, t)
    text_c(d, 960, 400, "¿CAMBIARÍAS", font(130), WHITE, a)
    text_c(d, 960, 550, "DE PUERTA?", font(130), AMBER, a)
    text_c(d, 960, 710, "Cuéntamelo en los comentarios", font(54), TEAL, smooth(181.4, 182.4, t))

SCENES = [("A", 0.0, 14.6, scene_A), ("DOORS", 14.6, 94.9, scene_doors), ("F", 94.9, 127.3, scene_F),
          ("G", 127.3, 153.3, scene_G), ("H", 153.3, 179.6, scene_H), ("E", 179.6, TOTAL, scene_E)]

def frame_at(t):
    fr = BG.copy()
    d = ImageDraw.Draw(fr, "RGBA")
    sc = SCENES[-1]
    for s in SCENES:
        if s[1] <= t < s[2]:
            sc = s; break
    sc[3](fr, d, t)
    a = 0.0
    if sc[1] > 0: a = max(a, 1 - smooth(sc[1], sc[1] + 0.5, t))
    if sc[2] < TOTAL: a = max(a, smooth(sc[2] - 0.5, sc[2], t))
    else: a = max(a, smooth(sc[2] - 0.7, sc[2], t))
    if a > 0.01:
        fr.paste(VEIL, (0, 0), Image.new("L", (W, H), int(255 * min(1.0, a))))
    captions(fr, t)
    return fr

# ---------------------------------------------------------------- outputs
def srt_time(x):
    ms = int(round(x * 1000)); h = ms // 3600000; ms %= 3600000
    m = ms // 60000; ms %= 60000; s = ms // 1000; ms %= 1000
    return "%02d:%02d:%02d,%03d" % (h, m, s, ms)

def write_texts():
    with open(os.path.join(OUT, "subtitulos-monty-hall.srt"), "w", encoding="utf-8") as f:
        for i, (a, b, txt) in enumerate(CAPS, 1):
            f.write("%d\n%s --> %s\n%s\n\n" % (i, srt_time(a), srt_time(b), txt))
    def mmss(x): return "%d:%02d" % (int(x) // 60, int(x) % 60)
    with open(os.path.join(OUT, "guion-monty-hall.md"), "w", encoding="utf-8") as f:
        f.write("# Guion: La paradoja de Monty Hall\n\n")
        f.write("Duración: unos 3 minutos. Cada línea tiene el minuto en que aparece en el video, para que la leas en voz alta a ese ritmo.\n\n")
        f.write("## Texto para leer en voz alta\n\n")
        for a, b, txt in CAPS:
            f.write("**[%s]** %s\n\n" % (mmss(a), txt))
        f.write("## Datos a verificar antes de publicar\n\n")
        f.write("- La columna de 1990 y las miles de cartas con respuestas en contra (el caso de Marilyn vos Savant en la revista Parade).\n")
        f.write("- La simulación del video es real: se hizo con 1.000 partidas (quedarse ganó %d, cambiar ganó %d).\n" % (STAY_N, SW_N))

def render_chunk(args):
    i, t0, t1 = args
    n = int(round((t1 - t0) * FPS))
    tmp = os.path.join(OUT, "c_%d.tmp.mp4" % i); fin = os.path.join(OUT, "c_%d.mp4" % i)
    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, H), "-r", str(FPS),
           "-i", "-", "-c:v", "libx264", "-crf", "19", "-preset", "veryfast", "-pix_fmt", "yuv420p", tmp]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for k in range(n):
        p.stdin.write(frame_at(t0 + k / float(FPS)).tobytes())
    p.stdin.close()
    rc = p.wait()
    if rc == 0: os.replace(tmp, fin)
    return i, rc


# =====================================================================
#  SINCRONIZAR EL VIDEO CON LA VOZ
#  Uso:  python3 monty_sync.py voz salida
#    voz/    -> 30 audios (linea_01 ... linea_30), a velocidad NATURAL, en el orden del .srt
#    salida/ -> aquí quedan los videos, los subtítulos y los capítulos nuevos
#  El video se adapta a la duración real de cada frase (la voz nunca se acelera).
# =====================================================================
import glob
import json

AUDIO_EXT = (".wav", ".mp3", ".m4a", ".ogg", ".flac", ".aac")
SR = 44100
LEAD = 0.10      # la voz empieza 0,1 s después de que aparece el texto
TAIL_PAD = 0.30  # el texto se queda 0,3 s después de terminar la frase

CHAPTERS = [
    (0.0, "El problema que enfureció a miles de lectores"),
    (15.0, "El juego: tres puertas"),
    (47.2, "La intuición: ¿50 y 50?"),
    (58.7, "La explicación: 1/3 contra 2/3"),
    (94.9, "Los tres casos posibles"),
    (127.3, "La prueba: simulación de 1.000 partidas"),
    (153.3, "La clave: el presentador sabe dónde está el auto"),
]


def probe(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                       capture_output=True, text=True)
    return float(r.stdout.strip())


def find_clips(voz_dir):
    files = sorted(f for f in glob.glob(os.path.join(voz_dir, "*")) if f.lower().endswith(AUDIO_EXT))
    if len(files) != len(CAPS):
        raise SystemExit("Hay %d audios en '%s' y deberían ser %d (uno por cada frase del .srt)." % (len(files), voz_dir, len(CAPS)))
    return files


def build_timings(durs):
    new, t = [], CAPS[0][0]
    for i, (o0, o1, _) in enumerate(CAPS):
        n0 = t
        n1 = n0 + LEAD + durs[i] + TAIL_PAD
        new.append((n0, n1))
        if i + 1 < len(CAPS):
            t = n1 + (CAPS[i + 1][0] - o1)   # se conservan las pausas originales entre escenas
    total = new[-1][1] + (TOTAL - CAPS[-1][1])
    return new, total


def make_warp(new, total):
    oldp, newp = [0.0], [0.0]
    for (o0, o1, _), (n0, n1) in zip(CAPS, new):
        oldp += [o0, o1]; newp += [n0, n1]
    oldp.append(TOTAL); newp.append(total)
    return oldp, newp


def render_chunk_sync(args):
    i, a, b, oldp, newp, outdir = args
    n = int(round((b - a) * FPS))
    tmp = os.path.join(outdir, "c_%d.tmp.mp4" % i); fin = os.path.join(outdir, "c_%d.mp4" % i)
    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, H), "-r", str(FPS),
           "-i", "-", "-c:v", "libx264", "-crf", "19", "-preset", "veryfast", "-pix_fmt", "yuv420p", tmp]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for k in range(n):
        t_new = a + k / float(FPS)
        t_old = float(np.interp(t_new, newp, oldp))
        p.stdin.write(frame_at(t_old).tobytes())
    p.stdin.close()
    rc = p.wait()
    if rc == 0:
        os.replace(tmp, fin)
    return i, rc


def decode_mono(path):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True)
    return np.frombuffer(r.stdout, dtype=np.float32)


def make_music(total):
    fc = ("[0]volume=0.5[a];[1]tremolo=f=0.2:d=0.5,volume=0.4[b];[2]tremolo=f=0.13:d=0.6,volume=0.35[c];"
          "[3]tremolo=f=0.17:d=0.5,volume=0.25[e];[a][b][c][e]amix=inputs=4:duration=longest,lowpass=f=900,volume=1.4,"
          "aformat=channel_layouts=stereo,afade=t=in:d=2,afade=t=out:st=%.2f:d=4[o]" % (total - 4))
    cmd = ["ffmpeg", "-v", "error"]
    for f in (110, 164.81, 220, 261.63):
        cmd += ["-f", "lavfi", "-i", "sine=f=%s:d=%.2f:r=%d" % (f, total, SR)]
    cmd += ["-filter_complex", fc, "-map", "[o]", "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"]
    r = subprocess.run(cmd, capture_output=True)
    return np.frombuffer(r.stdout, dtype=np.float32).reshape(-1, 2)


def mmss(x):
    x = int(x)
    return "%d:%02d" % (x // 60, x % 60)


def sync_main(voz_dir, outdir):
    os.makedirs(outdir, exist_ok=True)
    clips = find_clips(voz_dir)
    durs = [probe(c) for c in clips]
    new, total = build_timings(durs)
    oldp, newp = make_warp(new, total)
    print("Duración nueva del video: %.1f s (antes %.1f s)" % (total, TOTAL))
    print("Frase más larga: %.1f s | más corta: %.1f s" % (max(durs), min(durs)))

    # 1) video
    chunks, a, i = [], 0.0, 0
    while a < total - 1e-6:
        b = min(a + 20.0, total)
        chunks.append((i, a, b, oldp, newp, outdir)); a = b; i += 1
    from multiprocessing import Pool
    with Pool(max(1, min(4, os.cpu_count() or 2))) as pool:
        for ci, rc in pool.imap_unordered(render_chunk_sync, chunks):
            print("tramo", ci, "ok" if rc == 0 else "ERROR", flush=True)
            if rc != 0:
                raise SystemExit("Falló el render del tramo %d" % ci)
    lst = os.path.join(outdir, "lista.txt")
    with open(lst, "w") as f:
        for c in chunks:
            f.write("file '%s'\n" % os.path.abspath(os.path.join(outdir, "c_%d.mp4" % c[0])))

    # 2) audio: voz en su segundo exacto + música suave
    n = int((total + 1) * SR)
    voice = np.zeros(n, np.float32)
    for k, c in enumerate(clips):
        x = decode_mono(c)
        s = int((new[k][0] + LEAD) * SR)
        e = min(n, s + len(x))
        voice[s:e] += x[:e - s]
    pk = float(np.abs(voice).max()) or 1.0
    voice *= 0.85 / pk
    mus = make_music(total)
    m_arr = np.zeros((n, 2), np.float32)
    L = min(n, len(mus)); m_arr[:L] = mus[:L]
    for tag, arr in (("voz_musica", m_arr + voice[:, None]), ("solo_voz", np.repeat(voice[:, None], 2, axis=1))):
        arr = np.clip(arr, -0.98, 0.98).astype(np.float32)
        raw = os.path.join(outdir, tag + ".raw")
        arr.tofile(raw)
        aac = os.path.join(outdir, tag + ".m4a")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", raw, "-c:a", "aac", "-b:a", "160k", aac], check=True)
        os.remove(raw)
    for tag, name in (("voz_musica", "monty-hall-con-voz.mp4"), ("solo_voz", "monty-hall-solo-voz.mp4")):
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-i", os.path.join(outdir, tag + ".m4a"),
                        "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "copy", "-t", "%.2f" % total, "-movflags", "+faststart",
                        os.path.join(outdir, name)], check=True)

    # 3) subtítulos y capítulos con los tiempos nuevos
    with open(os.path.join(outdir, "subtitulos-con-voz.srt"), "w", encoding="utf-8") as f:
        for k, ((o0, o1, txt), (n0, n1)) in enumerate(zip(CAPS, new), 1):
            f.write("%d\n%s --> %s\n%s\n\n" % (k, srt_time(n0), srt_time(n1), txt))
    with open(os.path.join(outdir, "capitulos.txt"), "w", encoding="utf-8") as f:
        for old, title in CHAPTERS:
            f.write("%s %s\n" % (mmss(float(np.interp(old, oldp, newp))), title))
    with open(os.path.join(outdir, "tiempos.json"), "w") as f:
        json.dump({"duracion_total": total, "frases": [{"inicio": a, "fin": b, "audio": os.path.basename(c)} for (a, b), c in zip(new, clips)]}, f, indent=1)
    # limpieza de tramos
    for c in chunks:
        os.remove(os.path.join(outdir, "c_%d.mp4" % c[0]))
    os.remove(lst)
    print("Listo. Archivos en:", outdir)


if __name__ == "__main__":
    voz = sys.argv[1] if len(sys.argv) > 1 else "voz"
    salida = sys.argv[2] if len(sys.argv) > 2 else "salida"
    sync_main(voz, salida)
