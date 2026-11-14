# The coach's voice: Kokoro v1.0 (Apache-2.0), Spanish male voice em_santa,
# spoken with Latin American pronunciation (espeak-ng "es-419": "zona" with
# an s, not the Spain "th").
#
#   KOKORO=/path/to/kokoro-multi-lang-v1_0   folder with model.onnx, voices.bin, tokens.txt
#   VOZ_ID=53                                 53 = em_santa (the default), 29 = em_alex
#
# Needs: pip install onnxruntime piper-tts   (piper-tts only for its espeak-ng phonemizer)
import os, wave, numpy as np

SR = 24000
_S = {}

def _carga():
    if _S: return _S
    import onnxruntime as ort
    from piper.phonemize_espeak import EspeakPhonemizer
    d = os.environ['KOKORO']
    tok = {}
    for line in open(os.path.join(d, 'tokens.txt'), encoding='utf-8'):
        line = line.rstrip('\n')
        if not line: continue
        s, i = line.rsplit(' ', 1); tok[s if s else ' '] = int(i)
    V = np.fromfile(os.path.join(d, 'voices.bin'), dtype=np.float32)
    _S.update(tok=tok, V=V.reshape(-1, 510, 256), sess=ort.InferenceSession(os.path.join(d, 'model.onnx')), E=EspeakPhonemizer())
    return _S

def decir(texto, salida, speed=1.0):
    """writes one line to a 24 kHz mono wav, without silence at either end; returns its length in seconds"""
    S = _carga(); sid = int(os.environ.get('VOZ_ID', '53')); partes = []
    for frase in S['E'].phonemize('es-419', texto):
        ids = [0] + [S['tok'][p] for p in frase if p in S['tok']][:508] + [0]
        a = S['sess'].run(None, {'tokens': np.array([ids], np.int64), 'style': S['V'][sid][len(ids) - 2][None, :],
                                 'speed': np.array([speed], np.float32)})[0].reshape(-1)
        partes += [a, np.zeros(int(SR * 0.12), np.float32)]
    a = np.concatenate(partes[:-1])
    on = np.where(np.abs(a) > 0.02 * np.abs(a).max())[0]
    a = a[max(0, on[0] - 600):on[-1] + 1800]                      # trim the edges, keep a short tail
    a = a / max(1e-6, np.abs(a).max()) * 0.9
    w = wave.open(salida, 'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((a * 32767).astype(np.int16).tobytes()); w.close()
    return len(a) / SR
