# Cognitivo Gym · ESTRELLAS EN ASCENSO (Rising Stars) · Lección 1: LA ZONA 2-1-2 (5 a 6 años)
#
#   VOZ_MX=/path/to/es_MX-claude-high.onnx python3 herramientas/leccion1.py salida.mp4    the voice in use (Latin American; pip install piper-tts onnxruntime)
#   KOKORO=/path/to/kokoro-multi-lang-v1_0 python3 herramientas/leccion1.py salida.mp4    another Latin American voice
#   PIPER=/path/to/piper VOZ=/path/to/es-carlfm-x-low.onnx python3 herramientas/leccion1.py salida.mp4   the first voice (Spain)
#   MUESTRA=5,12 ... python3 herramientas/leccion1.py x          sample frames only
#
# The online-lesson version of the zone drill: it talks to the child (a
# male coach's voice), with few words on screen, and ends by sending the
# child to play the game and then to practise at home with mom or dad.
# Plain color pieces, no animals. The timing follows the voice: every
# line is synthesized first, measured, and the picture is laid out on it.
import os, sys, json, math, wave, subprocess, tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__)); RAIZ = HERE
sys.path.insert(0, HERE)
import sigue as G
from sigue import W, H, FPS, bebas, outfit, grad_text, wordmark, text_c, ease, paste_c, CG_GOLD, CG_ORANGE, CG_DARK, CG_MUTED
import zona212 as Z
A = Z.AMIGOS

# ── what the coach says, in order; each line can trigger what we see ──
GUION = [
    ('titulo', '¡Hola, campeón! Hoy vamos a aprender la zona dos, uno, dos.'),
    ('casas',  'Cada amigo tiene su casa. Un color para cada uno.'),
    ('frente', 'Dos al frente.'),
    ('medio',  'Uno en el medio.'),
    ('atras',  'Y dos atrás.'),
    ('regla1', 'Regla número uno: ¡cuida tu casa!'),
    ('regla2', 'Regla número dos: ¡muévete hacia la bola!'),
    ('mira',   '¡Mira! La bola se mueve. El que está más cerca, va.'),
    ('rep1',   '¡El azul va!'),
    ('paso',   'Y los demás dan un pasito hacia la bola.'),
    ('rep2',   '¡El anaranjado va!'),
    ('rep3',   '¡El verde va!'),
    ('rep4',   '¡El amarillo va!'),
    ('rep5',   '¡El gris va!'),
    ('tu',     '¡Ahora te toca a ti!'),
    ('juega',  'Juega en la tableta. Y después, en casa, con mamá o con papá.'),
    ('fin',    '¡Muy bien, campeón! Nos vemos en la próxima lección.'),
]
REP_DE = {'rep1': 1, 'rep2': 3, 'rep3': 2, 'rep4': 0, 'rep5': 4}     # which friend goes on each rep
GAP = 0.35

def sintetizar(tmp):
    piper = os.environ.get('PIPER'); voz = os.environ.get('VOZ')
    plan = []; t = 0.6
    for k, (clave, texto) in enumerate(GUION):
        f = os.path.join(tmp, 'l%02d.wav' % k)
        if os.environ.get('VOZ_MX'):                    # the voice in use: Piper es_MX-claude-high (Latin American)
            subprocess.run([sys.executable, '-m', 'piper', '-m', os.environ['VOZ_MX'], '-f', f, '--sentence-silence', '0.1'], input=texto.encode('utf-8'), check=True, capture_output=True)
        elif os.environ.get('KOKORO'):                  # another Latin American voice (see voz_kokoro.py)
            import voz_kokoro; voz_kokoro.decir(texto, f)
        else:
            subprocess.run([piper, '-m', voz, '-f', f, '--length_scale', '1.0', '--sentence_silence', '0.1'], input=texto.encode('utf-8'), check=True, capture_output=True)
        w = wave.open(f); d = w.getnframes() / w.getframerate(); w.close()
        pre = 1.0 if clave in REP_DE else 0.0          # each rep: the ball flies first, then the coach calls who goes
        plan.append(dict(clave=clave, texto=texto, wav=f, t=t + pre, dur=d))
        t += pre + d + (1.6 if clave in REP_DE else GAP)
        if clave == 'titulo': t += 0.6
        if clave == 'casas': t += 1.2                  # let them finish walking in
        if clave == 'juega': t += 1.2
    return plan, t + 2.2

def plan_sin_voz():
    """for MUESTRA without the engine: rough timings from word counts"""
    plan = []; t = 0.6
    for clave, texto in GUION:
        d = 0.32 * len(texto.split()) + 0.4; pre = 1.0 if clave in REP_DE else 0.0
        plan.append(dict(clave=clave, texto=texto, wav=None, t=t + pre, dur=d))
        t += pre + d + (1.6 if clave in REP_DE else GAP) + (0.6 if clave == 'titulo' else 0) + (1.2 if clave in ('casas', 'juega') else 0)
    return plan, t + 2.2

# ── ESTRELLAS EN ASCENSO: gold stars rising up the screen ──────────
def estrella_spr(r, col=CG_GOLD):
    s = int(r * 4); im = Image.new('RGBA', (s, s), (0, 0, 0, 0)); c = s / 2
    pts = [(c + (r if k % 2 == 0 else r * 0.45) * math.cos(-math.pi / 2 + k * math.pi / 5), c + (r if k % 2 == 0 else r * 0.45) * math.sin(-math.pi / 2 + k * math.pi / 5)) for k in range(10)]
    gl = Image.new('RGBA', (s, s), (0, 0, 0, 0)); ImageDraw.Draw(gl).polygon(pts, fill=col + (230,))
    im.alpha_composite(gl.filter(ImageFilter.GaussianBlur(r * 0.35)))
    ImageDraw.Draw(im).polygon(pts, fill=col + (255,), outline=(255, 245, 200, 255))
    return im
STAR = {r: estrella_spr(r) for r in (14, 22, 34)}
_rs = __import__('random').Random(11)
SUBIDA = [dict(x=_rs.uniform(60, 1020), r=_rs.choice((14, 14, 22, 22, 34)), v=_rs.uniform(260, 520), f=_rs.uniform(0, 1), w=_rs.uniform(-1, 1)) for _ in range(26)]

def estrellas(img, t, a):
    """stars drifting up from the bottom, each fading out near the top and coming back from below"""
    if a <= 0: return
    for e in SUBIDA:
        span = H + 200; y = H + 100 - ((t * e['v'] + e['f'] * span) % span)
        x = e['x'] + 30 * math.sin(t * 1.3 + e['w'] * 6)
        fade = min(1, (H + 100 - y) / 300) * min(1, max(0, (y - 80) / 400))
        paste_c(img, STAR[e['r']], x, y, a * fade * 0.9, 1.0)

def sello(img, y, a, t):
    """the program's name: ★ ESTRELLAS EN ASCENSO ★, with the two stars rising a little in turn"""
    if a <= 0: return
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); al = int(255 * a)
    f = bebas(78); s = 'ESTRELLAS EN ASCENSO'; w = d.textlength(s, font=f)
    d.rounded_rectangle((540 - w / 2 - 110, y - 58, 540 + w / 2 + 110, y + 58), radius=58, fill=(26, 20, 10, int(220 * a)), outline=CG_GOLD + (al,), width=4)
    img.alpha_composite(lay)
    grad_text(img, (540, y + 2), s, f, a, spacing=2)
    for k, sx in enumerate((540 - w / 2 - 62, 540 + w / 2 + 62)):
        lift = 10 * math.sin(t * 3 + k * math.pi)
        paste_c(img, STAR[22], sx, y + lift, a, 1.0)

def make(plan, DUR):
    T = {p['clave']: p['t'] for p in plan}; D = {p['clave']: p['dur'] for p in plan}
    reps = [(T[c] - 1.0, REP_DE[c]) for c in ['rep1', 'rep2', 'rep3', 'rep4', 'rep5']]
    t_juego0 = T['regla2']; t_tu = T['tu']; t_fin = T['fin']

    def posiciones(t):
        pos = [a['casa'] for a in A]; bola = Z.COACH; va = None; ea = 0
        cur = None
        for k, (t0, i) in enumerate(reps):
            if t >= t0: cur = k
        if cur is None: return pos, bola, None, 0
        t0, i = reps[cur]; u = t - t0
        nxt = reps[cur + 1][0] if cur + 1 < len(reps) else t_tu
        prev = Z.COACH if cur == 0 else A[reps[cur - 1][1]]['bola']; spot = A[i]['bola']
        if u < 0.8:
            f = ease(u / 0.8); bola = Z.lerp(prev, spot, f); bola = (bola[0], bola[1] - 120 * math.sin(math.pi * f))
            return pos, bola, None, 0
        bola = spot; va = i
        back = nxt - t0 - 1.0                          # go home just before the next ball
        run = ease((u - 0.8) / 0.7) if u < back else 1 - ease((u - back) / 0.8)
        for j, a in enumerate(A):
            pos[j] = Z.lerp(a['casa'], Z.lerp(a['casa'], spot, 0.72 if j == i else 0.22), run)
        ea = ease((u - 0.9) / 0.3) * (1 - ease((u - back + 0.2) / 0.3))
        return pos, bola, va, ea

    def caption(img, s, a, col=(255, 255, 255), size=110, y=330):
        if a <= 0: return
        lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); al = int(255 * a)
        text_c(d, (540, y + 20 * (1 - a)), s, bebas(size), col + (al,), stroke=4, sf=(0, 0, 0, al)); img.alpha_composite(lay)

    def ventana(t, a, b): return ease((t - a) / 0.35) * (1 - ease((t - b + 0.35) / 0.35))

    def frame(t):
        tit = 1 - ease((t - (T['casas'] - 0.6)) / 0.5)
        img = (Z.BG_T if tit >= 1 else Image.blend(Z.BG_T, Z.BG, 1 - tit) if tit > 0 else Z.BG).copy()
        if tit > 0:
            img.alpha_composite(Image.new('RGBA', (W, H), CG_DARK + (int(170 * tit),)))
            estrellas(img, t, tit)
            wordmark(img, 280, ease(t / 0.5) * tit)
            sello(img, 420, ease((t - 0.15) / 0.5) * tit, t)
            lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); al = int(255 * ease((t - 0.8) / 0.5) * tit)
            text_c(d, (540, 1090), 'LECCIÓN 1', outfit(50, 800), (240, 240, 245, al)); img.alpha_composite(lay)
            grad_text(img, (540, 700), 'LA ZONA', bebas(210), ease((t - 0.4) / 0.5) * tit, spacing=8)
            grad_text(img, (540, 900), '2-1-2', bebas(260), ease((t - 0.6) / 0.5) * tit, spacing=8)
            if tit >= 1: return img.convert('RGB')
        wordmark(img, 70, 1 - tit)
        for k, a in enumerate(A):
            ca = ease((t - T['casas'] - 0.1 * k) / 0.35)
            if ca > 0: paste_c(img, Z.CONO[k], a['casa'][0], a['casa'][1] + 40, ca, 0.7 + 0.3 * ca)
        if t >= t_juego0: paste_c(img, Z.COACH_SPR, Z.COACH[0], Z.COACH[1] - 40, ease((t - t_juego0) / 0.4) * (1 - ease((t - t_tu) / 0.4)))
        pos, bola, va, ea = posiciones(t)
        if va is not None: Z.flecha(img, A[va]['casa'], Z.lerp(A[va]['casa'], A[va]['bola'], 0.72), (255, 255, 255), ea)
        # which ones the coach is pointing at: front, middle, back
        grupo = {'frente': [0, 1], 'medio': [2], 'atras': [3, 4]}
        luz = set()
        for g, ids in grupo.items():
            if T[g] <= t < T[g] + D[g] + 0.6: luz.update(ids)
        for k, a in enumerate(A):
            wa = (t - T['casas'] - 0.3 - 0.35 * k) / 1.0
            if wa <= 0: continue
            p = Z.lerp((a['casa'][0], 720), a['casa'], ease(wa)) if wa < 1 else pos[k]
            sc = 1.0 + (0.18 * (0.5 + 0.5 * math.sin((t - T['frente']) * 8)) if k in luz else 0)
            paste_c(img, Z.FICHA_HOT[k] if (k == va or k in luz) else Z.FICHA[k], p[0], p[1], min(1, wa * 2), sc)
        if t_juego0 + 0.5 <= t < t_tu + 0.3:
            paste_c(img, G.BALL, bola[0], bola[1] - (30 if bola == Z.COACH else 0), 1.0 - ease((t - t_tu) / 0.3), 0.75)
        # big words, only a few
        caption(img, '¡CADA UNO A SU CASA!', ventana(t, T['casas'], T['frente']), size=96)
        caption(img, 'DOS AL FRENTE', ventana(t, T['frente'], T['medio']), CG_GOLD)
        caption(img, 'UNO EN EL MEDIO', ventana(t, T['medio'], T['atras']), CG_GOLD)
        caption(img, 'DOS ATRÁS', ventana(t, T['atras'], T['regla1']), CG_GOLD)
        caption(img, 'CUIDA TU CASA', ventana(t, T['regla1'], T['regla2']))
        caption(img, '¡MUÉVETE HACIA LA BOLA!', ventana(t, T['regla2'], T['rep1'] - 1.0), size=92)
        if T['rep1'] - 1.0 <= t < t_tu:
            caption(img, 'EL MÁS CERCA VA', ventana(t, T['rep1'] - 1.0, t_tu), CG_GOLD, 96, 250)
            if va is not None and ea > 0:
                lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); al = int(255 * ea); s = '¡' + A[va]['es'] + ' VA!'
                f = bebas(84); w = d.textlength(s, font=f)
                d.rounded_rectangle((540 - w / 2 - 40, 380, 540 + w / 2 + 40, 490), radius=55, fill=A[va]['c'] + (al,)); text_c(d, (540, 437), s, f, (20, 16, 16, al))
                img.alpha_composite(lay)
        # "now it's your turn": two steps, play and at home
        if t >= t_tu:
            e = ease((t - t_tu) / 0.5) * (1 - ease((t - t_fin) / 0.4))
            img.alpha_composite(Image.new('RGBA', (W, H), CG_DARK + (int(210 * e),)))
            grad_text(img, (540, 520), '¡AHORA TÚ!', bebas(170), e, spacing=6)
            lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
            for k, (s, sub) in enumerate([('1 · JUEGA', 'el juego Zona 2-1-2 en la tableta'), ('2 · EN CASA', 'con mamá o papá: 5 vasitos y una bola')]):
                ak = e * ease((t - T['juega'] - 1.2 * k) / 0.4); y = 820 + k * 250
                d.rounded_rectangle((120, y - 95, 960, y + 95), radius=34, fill=(28, 28, 39, int(240 * ak)), outline=CG_GOLD + (int(255 * ak),), width=5)
                text_c(d, (540, y - 26), s, bebas(96), CG_GOLD + (int(255 * ak),))
                text_c(d, (540, y + 48), sub, outfit(38, 700), (230, 232, 238, int(255 * ak)))
            img.alpha_composite(lay)
        if t >= t_fin:
            u = ease((t - t_fin) / 0.6)
            img.alpha_composite(Image.new('RGBA', (W, H), CG_DARK + (int(225 * u),)))
            gl = Image.new('L', (W, H), 0); ImageDraw.Draw(gl).ellipse((140, 520, 940, 1120), fill=int(110 * u)); gl = gl.filter(ImageFilter.GaussianBlur(110))
            img.alpha_composite(Image.merge('RGBA', (*Image.new('RGB', (W, H), (255, 170, 40)).split(), gl)))
            estrellas(img, t, u)
            caption(img, '¡MUY BIEN, CAMPEÓN!', u, (255, 255, 255), 104, 470)
            grad_text(img, (540, 720), 'COGNITIVO', bebas(180), u, spacing=16)
            grad_text(img, (540, 875), 'GYM', bebas(180), u, spacing=16)
            lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); al = int(255 * u)
            text_c(d, (540, 1180), 'Lección 1 · La Zona 2-1-2', outfit(38, 700), CG_MUTED + (al,))
            img.alpha_composite(lay)
            sello(img, 1060, u, t)
            fo = min(1, max(0, (t - (DUR - 0.4)) / 0.4))
            if fo > 0: img.alpha_composite(Image.new('RGBA', (W, H), (0, 0, 0, int(255 * fo))))
        return img.convert('RGB')
    return frame

def mezcla(plan, DUR, musica, salida_wav):
    """the voice on top, the music low underneath (and dipping a little more while he talks)"""
    sr = 44100; n = int(DUR * sr)
    w = wave.open(musica); msr = w.getframerate(); ch = w.getnchannels(); m = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32)
    if ch == 2: m = m.reshape(-1, 2).mean(1)
    if msr != sr: m = np.interp(np.arange(int(len(m) * sr / msr)) * msr / sr, np.arange(len(m)), m)
    m = np.pad(m, (0, max(0, n - len(m))))[:n] * 0.22
    v = np.zeros(n, np.float32); duck = np.ones(n, np.float32)
    for p in plan:
        w = wave.open(p['wav']); vsr = w.getframerate(); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32)
        x = np.interp(np.arange(int(len(x) * sr / vsr)) * vsr / sr, np.arange(len(x)), x)
        a = int(p['t'] * sr); b = min(n, a + len(x)); v[a:b] += x[:b - a] * 1.15
        duck[max(0, a - 4000):min(n, b + 6000)] = 0.6
    duck = np.convolve(duck, np.ones(4000) / 4000, 'same')
    mix = v + m * duck; mix *= min(1.0, 27000 / max(1.0, np.abs(mix).max()))   # loud, never clipped
    out = mix.astype(np.int16)
    o = wave.open(salida_wav, 'wb'); o.setnchannels(1); o.setsampwidth(2); o.setframerate(sr); o.writeframes(out.tobytes()); o.close()

def main(salida):
    Z.frame(0)                                       # builds the court backgrounds Z.BG and Z.BG_T
    if os.environ.get('MUESTRA'):
        plan, DUR = plan_sin_voz() if not (os.environ.get('PIPER') or os.environ.get('KOKORO') or os.environ.get('VOZ_MX')) else sintetizar(tempfile.mkdtemp())
        fr = make(plan, DUR)
        for p in plan: print('%5.1f  %s' % (p['t'], p['texto']))
        for t in map(float, os.environ['MUESTRA'].split(',')): fr(t).save('muestra-%04.1f.jpg' % t, quality=88)
        return
    tmp = tempfile.mkdtemp(); plan, DUR = sintetizar(tmp); fr = make(plan, DUR)
    for p in plan: print('%5.1f  %s' % (p['t'], p['texto']))
    T = {p['clave']: p['t'] for p in plan}
    info = {'duration': DUR, 't_show': T['casas'], 't_hide': T['rep1'], 't_stop': T['tu'], 't_ask': T['tu'], 'roll': False,
            'swap_times': [[T[c] - 1.1, T[c] - 0.2] for c in ['rep1', 'rep2', 'rep3', 'rep4', 'rep5']], 't_brand': T['fin']}
    json.dump(info, open(os.path.join(tmp, 'info.json'), 'w'))
    subprocess.run([sys.executable, os.path.join(RAIZ, 'musica.py'), os.path.join(tmp, 'info.json'), os.path.join(tmp, 'm.wav')], check=True, cwd=tmp)
    mezcla(plan, DUR, os.path.join(tmp, 'm.wav'), os.path.join(tmp, 'audio.wav'))
    vid = os.path.join(tmp, 'v.mp4')
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '%dx%d' % (W, H), '-r', str(FPS), '-i', '-',
                           '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p', vid], stdin=subprocess.PIPE)
    for i in range(int(DUR * FPS)): ff.stdin.write(fr(i / FPS).tobytes())
    ff.stdin.close(); assert ff.wait() == 0
    part = salida[:-4] + '.part.mp4'
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', vid, '-i', os.path.join(tmp, 'audio.wav'), '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '160k', '-shortest', '-movflags', '+faststart', part], check=True)
    os.replace(part, salida)

if __name__ == '__main__':
    main(sys.argv[1])
