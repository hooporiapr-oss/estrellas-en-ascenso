# Cognitivo Gym · ESTRELLAS EN ASCENSO (Rising Stars) · Drill 1: LA ZONA 2-1-2 (5 a 6 años)
#
#   python3 herramientas/zona212.py salida.mp4            the video (1080x1920, 30 fps, ~51 s)
#   MUESTRA=5,12,22 python3 herramientas/zona212.py x     sample frames only
#
# An animated drill for coaches and parents, no real kids on screen. It
# teaches the same thing, with the same five colors and animals and the
# same two rules as the Zona 2-1-2 game (plain color pieces, no animals): "Cuida tu casa" and
# "Muévete hacia la bola" — the closest friend goes to the ball, the
# others take one step toward it.
#
#   0.0  title
#   3.5  1 · five cones in the 2-1-2 shape
#   8.0  2 · each kid to their house
#   13   rule 1 · CUIDA TU CASA
#   16   rule 2 · MUÉVETE HACIA LA BOLA, the coach takes the ball
#   19   five reps: the ball goes to a spot, the closest goes, the rest step
#   42   what it trains
#   47   closing card
import os, sys, json, math, subprocess, tempfile
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); RAIZ = HERE; sys.path.insert(0, HERE)
import sigue as G
from sigue import W, H, FPS, bebas, outfit, grad_text, wordmark, text_c, ease, paste_c, CG_GOLD, CG_ORANGE, CG_DARK, CG_MUTED

DUR = 51.0

# the five friends, in the game's colors, each with a house (cone) and the ball spot it owns
AMIGOS = [
    dict(c=(240, 180, 41),  casa=(395, 1290), bola=(150, 1225), es='EL AMARILLO'),   # front left  · left wing
    dict(c=(79, 168, 224),  casa=(685, 1290), bola=(930, 1225), es='EL AZUL'),       # front right · right wing
    dict(c=(94, 168, 98),   casa=(540, 1455), bola=(540, 1085), es='EL VERDE'),      # middle      · top of the key
    dict(c=(242, 138, 60),  casa=(330, 1630), bola=(95, 1730),  es='EL ANARANJADO'), # back left   · left corner
    dict(c=(150, 160, 172), casa=(750, 1630), bola=(985, 1730), es='EL GRIS'),       # back right  · right corner
]
COACH = (540, 905)
T_CONOS, T_CASAS, T_R1, T_R2, T_REPS, T_ENTRENA, T_FIN = 3.5, 8.0, 13.0, 16.0, 19.0, 42.0, 47.0
ORDEN = [1, 3, 2, 0, 4]          # right wing, left corner, top, left wing, right corner
REP = 4.6                        # seconds per rep: ball flies 0.8, runs 0.7, hold 1.9, back home 0.9, rest 0.3

def ficha(a, hot=False):
    """a kid: a solid disc in their cone's color, with a glow; a white ring when they are the one going"""
    s = 200; im = Image.new('RGBA', (s, s), (0, 0, 0, 0)); c = s / 2; r = 58
    gl = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    ImageDraw.Draw(gl).ellipse((c - r - 12, c - r - 12, c + r + 12, c + r + 12), fill=(a['c'] if not hot else (255, 255, 255)) + (200,))
    im.alpha_composite(gl.filter(ImageFilter.GaussianBlur(14)))
    d = ImageDraw.Draw(im)
    d.ellipse((c - r, c - r, c + r, c + r), fill=a['c'] + (255,), outline=(255, 255, 255, 255) if hot else (20, 20, 26, 255), width=8)
    hi = Image.new('RGBA', (s, s), (0, 0, 0, 0))                                     # a soft highlight so it reads as a round piece
    ImageDraw.Draw(hi).ellipse((c - r + 18, c - r + 12, c + 6, c - 8), fill=(255, 255, 255, 70))
    im.alpha_composite(hi.filter(ImageFilter.GaussianBlur(6)))
    return im

def cono(col):
    s = 120; im = Image.new('RGBA', (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse((14, 78, 106, 104), fill=(0, 0, 0, 110))                                  # shadow
    d.polygon([(60, 18), (96, 92), (24, 92)], fill=col + (255,), outline=(255, 255, 255, 230))
    d.rectangle((30, 64, 90, 72), fill=(255, 255, 255, 200))                            # the white band
    d.rounded_rectangle((18, 88, 102, 100), radius=5, fill=col + (255,))
    return im

FICHA = [ficha(a) for a in AMIGOS]; FICHA_HOT = [ficha(a, True) for a in AMIGOS]; CONO = [cono(a['c']) for a in AMIGOS]

def coach_sprite():
    s = 200; im = Image.new('RGBA', (s, s), (0, 0, 0, 0)); c = s / 2; r = 58
    d = ImageDraw.Draw(im); d.ellipse((c - r, c - r, c + r, c + r), fill=(22, 20, 28, 255), outline=CG_GOLD + (255,), width=7)
    text_c(d, (c, c + 3), 'COACH', bebas(44), (255, 255, 255, 255))
    return im
COACH_SPR = coach_sprite()

def lerp(p, q, u): return (p[0] + (q[0] - p[0]) * u, p[1] + (q[1] - p[1]) * u)

def posiciones(t):
    """where each kid stands and where the ball is at time t; also who is going"""
    pos = [a['casa'] for a in AMIGOS]; bola = COACH; va = None; etiqueta = None; ea = 0
    if t < T_REPS: return pos, bola, va, etiqueta, ea
    k = int((t - T_REPS) // REP)
    if k >= len(ORDEN): return pos, COACH, None, None, 0
    u = (t - T_REPS) - k * REP
    i = ORDEN[k]; spot = AMIGOS[i]['bola']; prev = COACH if k == 0 else AMIGOS[ORDEN[k - 1]]['bola']
    # the ball flies from where it was to the new spot (a small arc)
    if u < 0.8:
        f = ease(u / 0.8); bola = lerp(prev, spot, f); bola = (bola[0], bola[1] - 120 * math.sin(math.pi * f))
        return pos, bola, None, None, 0
    bola = spot; va = i
    run = ease((u - 0.8) / 0.7) if u < 3.4 else 1 - ease((u - 3.4) / 0.9)
    for j, a in enumerate(AMIGOS):
        meta = lerp(a['casa'], spot, 0.72 if j == i else 0.22)       # the closest goes most of the way; the rest take one step
        pos[j] = lerp(a['casa'], meta, run)
    ea = ease((u - 1.1) / 0.3) * (1 - ease((u - 3.3) / 0.3))
    return pos, bola, va, '¡' + AMIGOS[i]['es'] + ' VA!', ea

def banda(img, y, s1, s2=None, a=1.0, num=None):
    """the instruction at the top: an optional step number, a big line, a small line"""
    if a <= 0: return
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); al = int(255 * a)
    if num:
        d.ellipse((540 - 44, y - 132, 540 + 44, y - 44), fill=CG_GOLD + (al,)); text_c(d, (540, y - 86), num, bebas(66), (26, 15, 15, al))
    text_c(d, (540, y), s1, bebas(104), (255, 255, 255, al), stroke=3, sf=(0, 0, 0, al))
    if s2: text_c(d, (540, y + 82), s2, outfit(40, 700), (220, 224, 232, al))
    img.alpha_composite(lay)

def flecha(img, p, q, col, a):
    if a <= 0: return
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    x0, y0 = p; x1, y1 = q; L = math.hypot(x1 - x0, y1 - y0)
    if L < 40: return
    ux, uy = (x1 - x0) / L, (y1 - y0) / L; x0 += ux * 70; y0 += uy * 70; x1 -= ux * 70; y1 -= uy * 70
    n = int(L / 34)
    for k in range(n):
        if k % 2: continue
        s0, s1 = k / n, min(1, (k + 1) / n)
        d.line((x0 + (x1 - x0) * s0, y0 + (y1 - y0) * s0, x0 + (x1 - x0) * s1, y0 + (y1 - y0) * s1), fill=col + (int(235 * a),), width=9)
    hx, hy = x1, y1; px, py = -uy, ux
    d.polygon([(hx + ux * 22, hy + uy * 22), (hx - ux * 18 + px * 20, hy - uy * 18 + py * 20), (hx - ux * 18 - px * 20, hy - uy * 18 - py * 20)], fill=col + (int(235 * a),))
    img.alpha_composite(lay)

BG = None; BG_T = None
def frame(t):
    global BG, BG_T
    if BG is None: BG = G.background().convert('RGBA'); BG_T = G.background(piso='').convert('RGBA')
    # title: the court is dimmed until the first step (no floor words behind the title)
    tit = 1 - ease((t - 3.0) / 0.5)
    img = (BG_T if tit >= 1 else Image.blend(BG_T, BG, 1 - tit) if tit > 0 else BG).copy()
    if tit > 0:
        img.alpha_composite(Image.new('RGBA', (W, H), CG_DARK + (int(170 * tit),)))
        wordmark(img, 300, ease(t / 0.5) * tit)
        lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); al = int(255 * ease((t - 0.2) / 0.5) * tit)
        text_c(d, (540, 470), 'ESTRELLAS EN ASCENSO', outfit(42, 800), CG_MUTED + (al,))
        img.alpha_composite(lay)
        grad_text(img, (540, 700), 'LA ZONA', bebas(210), ease((t - 0.4) / 0.5) * tit, spacing=8)
        grad_text(img, (540, 900), '2-1-2', bebas(260), ease((t - 0.6) / 0.5) * tit, spacing=8)
        lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); al = int(255 * ease((t - 1.0) / 0.5) * tit)
        text_c(d, (540, 1110), '5 a 6 años · 5 nenes · 1 coach', outfit(44, 700), (240, 240, 245, al))
        img.alpha_composite(lay)
        return img.convert('RGB')
    wordmark(img, 70)
    # cones
    for k, a in enumerate(AMIGOS):
        ca = ease((t - T_CONOS - 0.3 - 0.25 * k) / 0.35)
        if ca > 0: paste_c(img, CONO[k], a['casa'][0], a['casa'][1] + 40, ca, 0.7 + 0.3 * ca)
    # the coach and the ball, from rule 2
    if t >= T_R2:
        paste_c(img, COACH_SPR, COACH[0], COACH[1] - 40, ease((t - T_R2) / 0.4))
    pos, bola, va, etiqueta, ea = posiciones(t)
    # arrows: where the one who goes is headed
    if va is not None:
        flecha(img, AMIGOS[va]['casa'], lerp(AMIGOS[va]['casa'], AMIGOS[va]['bola'], 0.72), (255, 255, 255), ea)
    # kids walk in from the top to their cones
    for k, a in enumerate(AMIGOS):
        wa = (t - T_CASAS - 0.2 - 0.45 * k) / 1.2
        if wa <= 0: continue
        start = (a['casa'][0], 720)
        p = lerp(start, a['casa'], ease(wa)) if wa < 1 else pos[k]
        paste_c(img, FICHA_HOT[k] if k == va else FICHA[k], p[0], p[1], min(1, wa * 2))
    if t >= T_R2 + 0.6:
        paste_c(img, G.BALL, bola[0], bola[1] - (30 if bola == COACH else 0), 1.0, 0.75)
    # the instructions on top
    def ventana(a, b): return ease((t - a) / 0.4) * (1 - ease((t - b + 0.4) / 0.4))
    banda(img, 330, 'PON 5 CONOS', 'en forma 2-1-2: dos, uno y dos', ventana(T_CONOS, T_CASAS), '1')
    banda(img, 330, 'CADA NENE A SU CASA', 'cada uno con su color', ventana(T_CASAS, T_R1), '2')
    banda(img, 330, 'CUIDA TU CASA', 'regla 1 · tu cono es tu lugar', ventana(T_R1, T_R2), '3')
    banda(img, 330, 'MUÉVETE HACIA LA BOLA', 'regla 2 · el coach mueve la bola', ventana(T_R2, T_REPS + 0.6), '4')
    if T_REPS + 0.2 < t < T_ENTRENA:
        a = ventana(T_REPS + 0.2, T_ENTRENA)
        lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); al = int(255 * a)
        text_c(d, (540, 250), 'EL MÁS CERCA VA', bebas(92), CG_GOLD + (al,), stroke=3, sf=(0, 0, 0, al))
        text_c(d, (540, 340), 'los demás dan un paso hacia la bola', outfit(40, 700), (230, 232, 238, al))
        img.alpha_composite(lay)
        if etiqueta and ea > 0:
            lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); al = int(255 * ea); col = AMIGOS[va]['c']
            f = bebas(84); w = d.textlength(etiqueta, font=f)
            d.rounded_rectangle((540 - w / 2 - 40, 470, 540 + w / 2 + 40, 580), radius=55, fill=col + (al,))
            text_c(d, (540, 527), etiqueta, f, (20, 16, 16, al))
            img.alpha_composite(lay)
    # what it trains
    if t >= T_ENTRENA:
        e = ease((t - T_ENTRENA) / 0.5) * (1 - ease((t - T_FIN) / 0.4))
        img.alpha_composite(Image.new('RGBA', (W, H), CG_DARK + (int(205 * e),)))
        lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        text_c(d, (540, 560), '¿QUÉ ENTRENA?', bebas(120), (255, 255, 255, int(255 * e)))
        for k, (s, sub) in enumerate([('ATENCIÓN', 'mirar la bola todo el tiempo'), ('REACCIÓN', 'moverse rápido cuando cambia'), ('EQUIPO', 'cada uno sabe su lugar')]):
            ak = e * ease((t - T_ENTRENA - 0.4 - 0.5 * k) / 0.4); y = 780 + k * 220
            d.rounded_rectangle((150, y - 80, 930, y + 80), radius=30, fill=(28, 28, 39, int(235 * ak)), outline=CG_GOLD + (int(255 * ak),), width=4)
            text_c(d, (540, y - 22), s, bebas(88), CG_GOLD + (int(255 * ak),))
            text_c(d, (540, y + 42), sub, outfit(36, 700), (225, 228, 235, int(255 * ak)))
        img.alpha_composite(lay)
    # closing card
    if t >= T_FIN:
        u = ease((t - T_FIN) / 0.6)
        img.alpha_composite(Image.new('RGBA', (W, H), CG_DARK + (int(225 * u),)))
        gl = Image.new('L', (W, H), 0); ImageDraw.Draw(gl).ellipse((140, 520, 940, 1120), fill=int(110 * u)); gl = gl.filter(ImageFilter.GaussianBlur(110))
        img.alpha_composite(Image.merge('RGBA', (*Image.new('RGB', (W, H), (255, 170, 40)).split(), gl)))
        grad_text(img, (540, 700), 'COGNITIVO', bebas(190), u, spacing=16)
        grad_text(img, (540, 860), 'GYM', bebas(190), u, spacing=16)
        lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); al = int(255 * u)
        text_c(d, (540, 1000), 'ESTRELLAS EN ASCENSO', outfit(44, 800), (255, 255, 255, al))
        text_c(d, (540, 1110), 'Drill 1 · La Zona 2-1-2', outfit(38, 700), CG_MUTED + (al,))
        m = Image.new('L', (W, H), 0); ImageDraw.Draw(m).rounded_rectangle((150, 1200, 930, 1340), radius=26, fill=al)
        u2 = np.clip((np.arange(W) - 150) / 780, 0, 1)[None, :, None]
        col = np.array(CG_GOLD, np.float32) * (1 - u2) + np.array(CG_ORANGE, np.float32) * u2
        img.alpha_composite(lay)
        img.alpha_composite(Image.merge('RGBA', (*Image.fromarray(np.repeat(col, H, 0).astype(np.uint8)).split(), m)))
        lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        text_c(d, (540, 1273), 'COGNOGYM.COM', bebas(84), (26, 15, 15, al))
        img.alpha_composite(lay)
        fo = min(1, max(0, (t - (DUR - 0.4)) / 0.4))
        if fo > 0: img.alpha_composite(Image.new('RGBA', (W, H), (0, 0, 0, int(255 * fo))))
    return img.convert('RGB')

def main(salida):
    if os.environ.get('MUESTRA'):
        for t in map(float, os.environ['MUESTRA'].split(',')): frame(t).save('muestra-%04.1f.jpg' % t, quality=88)
        return
    tmp = tempfile.mkdtemp()
    swaps = [[T_REPS + k * REP - 0.1, T_REPS + k * REP + 0.8] for k in range(len(ORDEN))]
    info = {'duration': DUR, 't_show': T_CONOS, 't_hide': T_REPS, 't_stop': T_ENTRENA, 't_ask': T_ENTRENA, 'roll': False, 'swap_times': swaps, 't_brand': T_FIN}
    json.dump(info, open(os.path.join(tmp, 'info.json'), 'w'))
    subprocess.run([sys.executable, os.path.join(RAIZ, 'musica.py'), os.path.join(tmp, 'info.json'), os.path.join(tmp, 'm.wav')], check=True, cwd=tmp)
    vid = os.path.join(tmp, 'v.mp4')
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '%dx%d' % (W, H), '-r', str(FPS), '-i', '-',
                           '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p', vid], stdin=subprocess.PIPE)
    for i in range(int(DUR * FPS)): ff.stdin.write(frame(i / FPS).tobytes())
    ff.stdin.close(); assert ff.wait() == 0
    part = salida[:-4] + '.part.mp4'
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', vid, '-i', os.path.join(tmp, 'm.wav'), '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '160k', '-shortest', '-movflags', '+faststart', part], check=True)
    os.replace(part, salida)

if __name__ == '__main__':
    main(sys.argv[1])
