"""Video: Las 7 maravillas del mundo moderno.
Uso: python3 maravillas.py <voz.onnx> <carpeta_salida>
Genera la narración con Piper, arma la línea de tiempo según la duración real de cada frase,
renderiza los cuadros con PIL y une todo con ffmpeg."""
import os, sys, math, subprocess, wave, random
from multiprocessing import Pool
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import maravillas_ilustraciones as ilus

W, H, FPS = 1920, 1080, 30
SR = 22050
FB = "/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf"
FR = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"
_fc = {}
def font(sz, f=FB):
    k = (int(sz), f)
    if k not in _fc:
        _fc[k] = ImageFont.truetype(f, int(sz))
    return _fc[k]

GOLD = (255, 200, 90); WHITE = (255, 255, 255); SOFT = (210, 220, 240)

# (clave, número, nombre, lugar, [(subtítulo, texto hablado o None)])
ESCENAS = [
    ("intro", None, "Las 7 maravillas", "del mundo moderno", [
        ("En 2007, según sus organizadores, más de 100 millones de personas votaron para elegir las nuevas siete maravillas del mundo.",
         "En dos mil siete, según sus organizadores, más de cien millones de personas votaron para elegir las nuevas siete maravillas del mundo."),
        ("No hay un ranking: las siete comparten el título. Vamos a recorrerlas una por una.", None),
    ]),
    ("muralla", 1, "Gran Muralla China", "China", [
        ("La Gran Muralla China.", None),
        ("No es un solo muro, sino una red de murallas construidas a lo largo de más de dos mil años.", None),
        ("Sumando todos sus tramos, supera los 20.000 kilómetros.", "Sumando todos sus tramos, supera los veinte mil kilómetros."),
        ("La parte más conocida, con sus torres de vigilancia, se levantó durante la dinastía Ming.", None),
    ]),
    ("petra", 2, "Petra", "Jordania", [
        ("Petra, en Jordania.", None),
        ("Fue la capital de los nabateos, un pueblo de comerciantes del desierto.", None),
        ("Sus edificios no se construyeron: se tallaron directamente en la roca rosada de las montañas.", None),
        ("Su fachada más famosa es El Tesoro, de casi 40 metros de altura.", "Su fachada más famosa es El Tesoro, de casi cuarenta metros de altura."),
    ]),
    ("cristo", 3, "Cristo Redentor", "Río de Janeiro, Brasil", [
        ("El Cristo Redentor, en Río de Janeiro, Brasil.", None),
        ("Se inauguró en 1931, en la cima del cerro del Corcovado.", "Se inauguró en mil novecientos treinta y uno, en la cima del cerro del Corcovado."),
        ("Mide 30 metros de alto sin contar el pedestal, y sus brazos abiertos se extienden 28 metros.",
         "Mide treinta metros de alto sin contar el pedestal, y sus brazos abiertos se extienden veintiocho metros."),
    ]),
    ("machu", 4, "Machu Picchu", "Perú", [
        ("Machu Picchu, en Perú.", None),
        ("Esta ciudadela inca se construyó en el siglo XV, a más de 2.400 metros de altura.",
         "Esta ciudadela inca se construyó en el siglo quince, a más de dos mil cuatrocientos metros de altura."),
        ("Sus muros encajan con tanta precisión que muchas piedras se sostienen sin mortero.", None),
        ("En 1911, el explorador Hiram Bingham la dio a conocer al mundo.", "En mil novecientos once, el explorador Jáiram Bíngam la dio a conocer al mundo."),
    ]),
    ("chichen", 5, "Chichén Itzá", "Yucatán, México", [
        ("Chichén Itzá, en México.", None),
        ("Fue una de las grandes ciudades mayas de la península de Yucatán.", None),
        ("Su pirámide, El Castillo, tiene 365 escalones: uno por cada día del año.",
         "Su pirámide, El Castillo, tiene trescientos sesenta y cinco escalones: uno por cada día del año."),
        ("En los equinoccios, la sombra forma una serpiente que parece bajar por la escalinata.", None),
    ]),
    ("coliseo", 6, "Coliseo", "Roma, Italia", [
        ("El Coliseo, en Roma, Italia.", None),
        ("Se inauguró en el año 80 después de Cristo y podía recibir a unos 50.000 espectadores.",
         "Se inauguró en el año ochenta después de Cristo y podía recibir a unos cincuenta mil espectadores."),
        ("Allí se celebraban combates de gladiadores y espectáculos con animales.", None),
    ]),
    ("taj", 7, "Taj Mahal", "Agra, India", [
        ("El Taj Mahal, en Agra, India.", None),
        ("El emperador Shah Jahan lo mandó construir en memoria de su esposa, Mumtaz Mahal.",
         "El emperador Sha Yahán lo mandó construir en memoria de su esposa, Mumtaz Majal."),
        ("Es un mausoleo de mármol blanco que cambia de color según la luz del día.", None),
    ]),
    ("piramides", None, "Gran Pirámide de Guiza", "Egipto · lugar de honor", [
        ("Y hay una más: la Gran Pirámide de Guiza, en Egipto.", None),
        ("Es la única de las siete maravillas del mundo antiguo que sigue en pie, y recibió un lugar de honor.", None),
    ]),
    ("outro", None, "¿Cuál te gustaría visitar?", "Déjalo en los comentarios", [
        ("¿Cuál de estas maravillas te gustaría visitar? Déjalo en los comentarios.", None),
    ]),
]

PAD_IN, GAP, PAD_OUT = 0.9, 0.45, 0.9
FADE = 0.45


def tts(model, text, path):
    if os.path.exists(path):
        return
    subprocess.run(["piper", "-m", model, "--output_file", path], input=text.encode("utf-8"),
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def read_wav(path):
    with wave.open(path) as w:
        assert w.getframerate() == SR
        return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768.0


def build_timeline(model, vdir):
    os.makedirs(vdir, exist_ok=True)
    t = 0.0
    scenes, caps, clips = [], [], []
    n = 0
    for key, num, name, place, lines in ESCENAS:
        start = t
        t += PAD_IN
        for cap, spoken in lines:
            p = os.path.join(vdir, "%02d.wav" % n); n += 1
            tts(model, spoken or cap, p)
            a = read_wav(p)
            dur = len(a) / SR
            caps.append((t, t + dur, cap))
            clips.append((t, a))
            t += dur + GAP
        t += PAD_OUT - GAP
        scenes.append(dict(key=key, num=num, name=name, place=place, start=start, end=t))
    return scenes, caps, clips, t


# ------------------------------------------------------------------ dibujo
def smooth(a, b, t):
    if t <= a: return 0.0
    if t >= b: return 1.0
    u = (t - a) / (b - a)
    return u * u * (3 - 2 * u)


def wrap(txt, f, maxw):
    words, lines, cur = txt.split(), [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if f.getlength(test) <= maxw:
            cur = test
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    return lines


IMGS = {}
THUMBS = {}
STARS = None


def load_images():
    global STARS
    for k, fn in ilus.ALL.items():
        IMGS[k] = fn()
        THUMBS[k] = IMGS[k].resize((480, 270), Image.LANCZOS)
    STARS = make_stars()


def make_stars():
    ys = np.linspace(0, 1, H)[:, None, None]
    arr = np.array([14, 18, 40], np.float32) + (np.array([40, 30, 70], np.float32) - [14, 18, 40]) * ys
    img = Image.fromarray(np.broadcast_to(arr, (H, W, 3)).astype(np.uint8))
    d = ImageDraw.Draw(img)
    rnd = random.Random(1)
    for _ in range(260):
        x, y, r = rnd.uniform(0, W), rnd.uniform(0, H), rnd.uniform(0.6, 2.0)
        c = int(rnd.uniform(140, 255))
        d.ellipse([x - r, y - r, x + r, y + r], fill=(c, c, min(255, c + 20)))
    return img


def kenburns(img, p, idx):
    iw, ih = img.size
    z0, z1 = (1.0, 0.86) if idx % 2 == 0 else (0.86, 1.0)
    z = z0 + (z1 - z0) * p
    cw = iw * z * 0.999
    ch = cw * 9 / 16
    dx = (iw - cw) / 2
    ox = dx + (dx * 0.6 if idx % 3 == 0 else -dx * 0.6) * (p - 0.5)
    oy = (ih - ch) / 2
    return img.resize((W, H), Image.BILINEAR, box=(ox, oy, ox + cw, oy + ch))


ORDER = ["muralla", "petra", "cristo", "machu", "chichen", "coliseo", "taj"]


def grid_scene(t, sc, intro):
    fr = STARS.copy()
    lt = t - sc["start"]
    d = ImageDraw.Draw(fr, "RGBA")
    cols = 4
    tw, th, gap = 380, 214, 26
    tot_w = cols * tw + (cols - 1) * gap
    x0 = (W - tot_w) / 2
    y0 = 300
    keys = ORDER + ["piramides"]
    for i, k in enumerate(keys):
        a = smooth(0.6 + i * 0.35, 1.1 + i * 0.35, lt) if intro else 1.0
        if a <= 0:
            continue
        r, c = divmod(i, cols)
        x = x0 + c * (tw + gap); y = y0 + r * (th + gap) + (1 - a) * 40
        th_img = THUMBS[k].resize((tw, th), Image.BILINEAR)
        if a < 1:
            th_img = Image.blend(Image.new("RGB", th_img.size, (20, 24, 50)), th_img, a)
        fr.paste(th_img, (int(x), int(y)))
        lab = str(i + 1) if i < 7 else "★"
        d.ellipse([x + 12, y + 12, x + 64, y + 64], fill=(20, 24, 40, int(200 * a)))
        d.text((x + 38, y + 39), lab, font=font(30), fill=GOLD + (int(255 * a),), anchor="mm")
    a = smooth(0.2, 0.9, lt)
    d.text((W / 2, 135), sc["name"], font=font(108), fill=WHITE + (int(255 * a),), anchor="mm")
    d.text((W / 2, 232), sc["place"], font=font(52, FR), fill=GOLD + (int(255 * a),), anchor="mm")
    return fr


def overlay_title(fr, sc, lt):
    a = smooth(0.25, 0.85, lt)
    if a <= 0:
        return
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    off = (1 - a) * -120
    nf, pf = font(70), font(40, FR)
    nw = max(nf.getlength(sc["name"]), pf.getlength(sc["place"]))
    has_num = sc["num"] is not None
    x0 = 60 + off
    bx1 = x0 + 175 + nw + 50
    d.rounded_rectangle([x0, 50, bx1, 220], 28, fill=(10, 14, 30, int(170 * a)))
    tx = x0 + 40
    if has_num:
        d.ellipse([x0 + 28, 72, x0 + 148, 192], fill=GOLD + (int(255 * a),))
        d.text((x0 + 88, 134), str(sc["num"]), font=font(76), fill=(20, 22, 36, int(255 * a)), anchor="mm")
        tx = x0 + 175
    else:
        d.text((x0 + 88, 134), "★", font=font(80, "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"), fill=GOLD + (int(255 * a),), anchor="mm")
        tx = x0 + 175
    d.text((tx, 112), sc["name"], font=nf, fill=WHITE + (int(255 * a),), anchor="lm")
    d.text((tx, 175), sc["place"], font=pf, fill=GOLD + (int(240 * a),), anchor="lm")
    # progreso
    if has_num:
        for i in range(7):
            cx = W - 70 - (6 - i) * 34
            on = i + 1 <= sc["num"]
            col = GOLD if i + 1 == sc["num"] else ((255, 255, 255) if on else (255, 255, 255))
            al = 255 if i + 1 == sc["num"] else (170 if on else 70)
            r = 11 if i + 1 == sc["num"] else 8
            d.ellipse([cx - r, 80 - r, cx + r, 80 + r], fill=col + (int(al * a),))
    fr.alpha_composite(lay)


def overlay_caption(fr, t, caps):
    cur = None
    for s, e, txt in caps:
        if s - 0.15 <= t <= e + 0.25:
            cur = (s, e, txt)
    if not cur:
        return
    s, e, txt = cur
    a = smooth(s - 0.15, s + 0.1, t) * (1 - smooth(e + 0.05, e + 0.25, t))
    if a <= 0:
        return
    f = font(46, FR)
    lines = wrap(txt, f, 1500)
    lh = 60
    bh = lh * len(lines) + 40
    bw = max(f.getlength(l) for l in lines) + 80
    y0 = H - 70 - bh
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.rounded_rectangle([(W - bw) / 2, y0, (W + bw) / 2, y0 + bh], 22, fill=(8, 10, 22, int(185 * a)))
    for i, l in enumerate(lines):
        d.text((W / 2, y0 + 20 + lh * i + lh / 2), l, font=f, fill=WHITE + (int(255 * a),), anchor="mm")
    fr.alpha_composite(lay)


def frame_at(t, scenes, caps, total):
    idx = 0
    for i, sc in enumerate(scenes):
        if sc["start"] <= t < sc["end"]:
            idx = i
    sc = scenes[idx]
    lt = t - sc["start"]
    dur = sc["end"] - sc["start"]
    if sc["key"] in ("intro", "outro"):
        fr = grid_scene(t, sc, sc["key"] == "intro").convert("RGBA")
    else:
        p = smooth(0, dur, lt) * 0.5 + (lt / dur) * 0.5
        fr = kenburns(IMGS[sc["key"]], p, idx).convert("RGBA")
        overlay_title(fr, sc, lt)
    overlay_caption(fr, t, caps)
    fr = fr.convert("RGB")
    fade = smooth(0, FADE, lt) * (1 - smooth(dur - FADE, dur, lt))
    if idx == 0:
        fade = smooth(0, 0.8, lt) * (1 - smooth(dur - FADE, dur, lt))
    if idx == len(scenes) - 1:
        fade = smooth(0, FADE, lt) * (1 - smooth(dur - 1.2, dur, lt))
    if fade < 1:
        fr = Image.blend(Image.new("RGB", (W, H), (6, 8, 16)), fr, fade)
    return fr


def render_chunk(args):
    i, f0, f1, scenes, caps, total, out = args
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, H),
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", out],
                         stdin=subprocess.PIPE)
    for f in range(f0, f1):
        p.stdin.write(frame_at(f / FPS, scenes, caps, total).tobytes())
    p.stdin.close(); p.wait()
    return out


# ------------------------------------------------------------------ audio
def make_music(total):
    n = int(total * SR)
    t = np.arange(n) / SR
    out = np.zeros(n, np.float32)
    # progresión suave: Am - F - C - G (4 s cada acorde)
    chords = [[220.0, 261.63, 329.63], [174.61, 220.0, 261.63], [196.0, 261.63, 329.63], [196.0, 246.94, 293.66]]
    seg = 4.0
    for k in range(int(total / seg) + 1):
        s0 = int(k * seg * SR); s1 = min(n, int((k + 1) * seg * SR + 1.5 * SR))
        if s0 >= n:
            break
        tt = t[s0:s1] - k * seg
        env = np.minimum(1, tt / 1.2) * np.exp(-np.maximum(0, tt - seg) / 0.6)
        for fq in chords[k % 4]:
            for h, g in ((1, 1.0), (2, 0.25), (0.5, 0.5)):
                out[s0:s1] += (g * np.sin(2 * np.pi * fq * h * tt + fq) * env).astype(np.float32)
        # arpegio suave
        for j, fq in enumerate(chords[k % 4] * 2):
            a0 = s0 + int(j * 0.5 * SR)
            a1 = min(n, a0 + int(1.2 * SR))
            if a0 >= n:
                break
            ta = t[a0:a1] - t[a0]
            out[a0:a1] += (0.35 * np.sin(2 * np.pi * fq * 2 * ta) * np.exp(-ta * 3.5)).astype(np.float32)
    out /= np.abs(out).max() + 1e-6
    fade = np.minimum(1, t / 2.0) * np.minimum(1, (total - t) / 3.0)
    return out * fade * 0.11


def mix_audio(clips, total, path):
    n = int(total * SR) + SR
    voice = np.zeros(n, np.float32)
    for s, a in clips:
        i = int(s * SR)
        voice[i:i + len(a)] += a
    music = make_music(n / SR)
    # bajar la música mientras hay voz
    env = (np.abs(voice) > 0.01).astype(np.float32)
    k = int(0.4 * SR)
    env = np.convolve(env, np.ones(k) / k, "same")
    duck = 1 - 0.55 * np.clip(env * 4, 0, 1)
    out = voice * 0.95 + music * duck
    out = np.clip(out, -1, 1)
    with wave.open(path, "w") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((out * 32767).astype(np.int16).tobytes())


def srt(caps, path):
    def ts(x):
        ms = int(round(x * 1000))
        return "%02d:%02d:%02d,%03d" % (ms // 3600000, ms // 60000 % 60, ms // 1000 % 60, ms % 1000)
    with open(path, "w") as f:
        for i, (s, e, txt) in enumerate(caps, 1):
            f.write("%d\n%s --> %s\n%s\n\n" % (i, ts(s), ts(e), txt))


def guion(scenes, caps, path):
    def mmss(x):
        return "%d:%02d" % (int(x) // 60, int(x) % 60)
    with open(path, "w") as f:
        f.write("# Guion: Las 7 maravillas del mundo moderno\n\n")
        f.write("Duración: %s. Narración generada con Piper (voz es_MX-claude-high).\n\n" % mmss(caps[-1][1] + 1))
        for sc in scenes:
            f.write("## %s%s\n\n" % ("%d. " % sc["num"] if sc["num"] else "", sc["name"]))
            for s, e, txt in caps:
                if sc["start"] <= s < sc["end"]:
                    f.write("**[%s]** %s\n\n" % (mmss(s), txt))


def main():
    model, outdir = sys.argv[1], sys.argv[2]
    work = os.path.join(outdir, "_trabajo")
    os.makedirs(work, exist_ok=True)
    scenes, caps, clips, total = build_timeline(model, os.path.join(work, "voz"))
    print("duración: %.1f s" % total)
    load_images()
    nfr = int(total * FPS)
    if len(sys.argv) > 3:   # vista previa de cuadros sueltos
        for x in sys.argv[3:]:
            frame_at(float(x), scenes, caps, total).save(os.path.join(work, "f_%s.png" % x))
        return
    audio = os.path.join(work, "audio.wav")
    mix_audio(clips, total, audio)
    nproc = os.cpu_count() or 4
    step = math.ceil(nfr / nproc)
    jobs = [(i, i * step, min(nfr, (i + 1) * step), scenes, caps, total, os.path.join(work, "parte%02d.mp4" % i)) for i in range(nproc)]
    with Pool(nproc) as pool:
        parts = pool.map(render_chunk, jobs)
    lst = os.path.join(work, "lista.txt")
    with open(lst, "w") as f:
        for p in parts:
            f.write("file '%s'\n" % os.path.abspath(p))
    final = os.path.join(outdir, "siete-maravillas.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-i", audio,
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", final], check=True)
    srt(caps, os.path.join(outdir, "subtitulos-siete-maravillas.srt"))
    guion(scenes, caps, os.path.join(outdir, "guion-siete-maravillas.md"))
    print("listo:", final)


if __name__ == "__main__":
    main()
