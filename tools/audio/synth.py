"""Small DSP toolkit for The Sift's sounds (numpy + scipy). Everything is mono float32 at SR.

Building blocks:
- voice(...)       formant ("sung vowel") synthesis with a glottal-like harmonic source, vibrato and glides
- bell(...)        inharmonic struck-crystal partials
- noise_band(...)  band-passed noise (wind, breath)
- reverb(...)      Schroeder reverb (4 combs + 2 all-pass)
- envelope / fades / normalise / loop crossfade / write_ogg
"""
import numpy as np
from scipy.signal import lfilter, butter, sosfilt

SR = 44100


def t_axis(seconds):
    return np.arange(int(seconds * SR)) / SR


# ---------------------------------------------------------------- pitch curves
def glide_curve(notes, rng, glide=0.08):
    """notes = [(freq_hz, seconds)]; returns a per-sample f0 curve with short portamento between notes."""
    parts = [np.full(int(d * SR), f, dtype=np.float64) for f, d in notes]
    f0 = np.concatenate(parts)
    g = max(1, int(glide * SR))
    kernel = np.ones(g) / g                     # moving average = smooth glide
    padded = np.concatenate([np.full(g, f0[0]), f0, np.full(g, f0[-1])])
    return np.convolve(padded, kernel, mode="same")[g:-g]


def vibrato(f0, rate=5.5, depth=0.012, rng=None, delay=0.15, jitter=0.0):
    n = len(f0)
    t = np.arange(n) / SR
    ramp = np.clip((t - delay) / 0.25, 0, 1)    # vibrato fades in after the onset
    phase = 2 * np.pi * rate * t
    if jitter and rng is not None:              # irregular trembling (mourner)
        phase += np.cumsum(rng.normal(0, jitter, n)) / SR * 2 * np.pi
    return f0 * (1 + depth * ramp * np.sin(phase))


# ---------------------------------------------------------------- sources and filters
def glottal(f0, rolloff=1.4, max_hz=9000):
    """Band-limited harmonic sum (no aliasing): amplitude 1/n^rolloff, harmonics above max_hz muted."""
    phase = 2 * np.pi * np.cumsum(f0) / SR
    out = np.zeros(len(f0))
    for n in range(1, 60):
        mask = (n * f0) < max_hz
        if not mask.any():
            break
        out += mask * np.sin(n * phase) / n ** rolloff
    return out


def bandpass(x, freq, q):
    w0 = 2 * np.pi * freq / SR
    alpha = np.sin(w0) / (2 * q)
    b = np.array([alpha, 0.0, -alpha])
    a = np.array([1 + alpha, -2 * np.cos(w0), 1 - alpha])
    return lfilter(b / a[0], a / a[0], x)


def organ(f0, drawbars=((1, 1.0), (2, 0.7), (3, 0.45), (4, 0.4), (6, 0.22), (8, 0.18), (10, 0.08))):
    """Pipe-organ-like steady additive stack (no vibrato of its own; follows f0)."""
    phase = 2 * np.pi * np.cumsum(f0) / SR
    out = np.zeros(len(f0))
    for h, g in drawbars:
        out += g * (h * f0 < 12000) * np.sin(h * phase)
    return out


VOWELS = {   # formant (Hz, Q, gain)
    "ah": [(730, 8, 1.0), (1090, 10, 0.5), (2440, 14, 0.22)],
    "eh": [(560, 8, 1.0), (1800, 10, 0.55), (2550, 14, 0.3)],
    "oh": [(570, 8, 1.0), (840, 10, 0.45), (2410, 14, 0.15)],
    "oo": [(320, 7, 1.0), (870, 10, 0.28), (2240, 14, 0.08)],
    "mm": [(260, 5, 1.0), (1700, 12, 0.05), (2600, 14, 0.03)],
}


def formants(src, vowel, shift=1.0):
    return sum(g * bandpass(src, f * shift, q) for f, q, g in VOWELS[vowel])


def chorus(render, f0, voices=3, detune_cents=7.0, spread=0.012, rng=None):
    """Several singers on the same line: each copy slightly detuned and late (render(f0) -> signal)."""
    out = np.zeros(len(f0) + int(spread * SR * voices))
    for k in range(voices):
        cents = (k - (voices - 1) / 2) * detune_cents + (rng.normal(0, 1.5) if rng is not None else 0)
        y = render(f0 * 2 ** (cents / 1200))
        place(out, y / voices, k * spread * (0.6 + 0.4 * (rng.random() if rng is not None else 0.5)))
    return out


def lowpass(x, hz, order=2):
    return sosfilt(butter(order, hz, btype="low", fs=SR, output="sos"), x)


def voice(f0, vowels=("oo", "ah"), breath=0.03, rng=None, shift=1.0, rolloff=1.4):
    """Sung vowel: glottal source through formant filters; vowels crossfade over the phrase."""
    src = glottal(f0, rolloff=rolloff)
    if breath and rng is not None:
        src = src + breath * noise_band(len(f0), 400, 4000, rng) * 6
    n = len(f0)
    if len(vowels) == 1:
        out = formants(src, vowels[0], shift)
    else:
        layers = [formants(src, v, shift) for v in vowels]
        pos = np.linspace(0, len(layers) - 1, n)
        out = np.zeros(n)
        for i, layer in enumerate(layers):
            w = np.clip(1 - np.abs(pos - i), 0, 1)
            out += w * layer
    return out


def noise_band(n, lo, hi, rng, colour="white"):
    x = rng.normal(0, 1, n)
    if colour == "brown":
        x = np.cumsum(x)
        x -= np.convolve(x, np.ones(2048) / 2048, mode="same")
    sos = butter(2, [lo, hi], btype="band", fs=SR, output="sos")
    y = sosfilt(sos, x)
    return y / (np.max(np.abs(y)) + 1e-9)


def bell(freq, seconds, rng=None, ratios=(1.0, 2.0, 2.76, 4.07, 5.4, 8.93), bright=1.0):
    t = t_axis(seconds)
    out = np.zeros(len(t))
    gains = [1.0, 0.55, 0.5, 0.3, 0.22, 0.1]
    for k, (r, g) in enumerate(zip(ratios, gains)):
        f = freq * r
        if f > 16000:
            continue
        tau = seconds * 0.45 / (1 + k * 0.9 / bright)
        detune = 1 + (rng.normal(0, 0.0015) if rng is not None else 0)
        out += g * np.exp(-t / tau) * np.sin(2 * np.pi * f * detune * t + (rng.uniform(0, 6.28) if rng is not None else 0))
    attack = np.clip(t / 0.003, 0, 1)
    return out * attack


# ---------------------------------------------------------------- envelopes and effects
def adsr(n, attack=0.05, release=0.3, curve=2.0):
    env = np.ones(n)
    a, r = min(int(attack * SR), n // 2), min(int(release * SR), n // 2)   # short clips: never longer than the clip
    if a:
        env[:a] = np.linspace(0, 1, a) ** curve
    if r:
        env[-r:] *= np.linspace(1, 0, r) ** curve
    return env


def reverb(x, wet=0.3, size=1.0, damp=0.8):
    out = np.zeros(len(x) + int(SR * 2.5 * size))
    xx = np.concatenate([x, np.zeros(len(out) - len(x))])
    combs = [1557, 1617, 1491, 1422, 1277, 1356]
    acc = np.zeros(len(xx))
    for d in combs:
        d = int(d * size)
        a = np.zeros(d + 1)
        a[0], a[-1] = 1.0, -damp
        acc += lfilter([1.0], a, xx)
    acc /= len(combs)
    for d, g in ((225, 0.5), (556, 0.5)):
        b = np.zeros(d + 1)
        a = np.zeros(d + 1)
        b[0], b[-1] = -g, 1.0
        a[0], a[-1] = 1.0, -g
        acc = lfilter(b, a, acc)
    sos = butter(1, 5000, btype="low", fs=SR, output="sos")   # darker tail
    acc = sosfilt(sos, acc)
    out = (1 - wet) * xx + wet * acc
    return trim_tail(out)


def trim_tail(x, floor=1e-4):
    idx = np.nonzero(np.abs(x) > floor * np.max(np.abs(x)))[0]
    end = idx[-1] + 1 if len(idx) else len(x)
    return x[:end]


def normalise(x, peak_db=-3.0):
    x = x - np.mean(x)
    peak = np.max(np.abs(x)) + 1e-9
    return x * (10 ** (peak_db / 20) / peak)


def fade(x, fin=0.01, fout=0.05):
    x = x.copy()
    a, b = int(fin * SR), int(fout * SR)
    if a:
        x[:a] *= np.linspace(0, 1, a)
    if b:
        x[-b:] *= np.linspace(1, 0, b)
    return x


def make_loop(x, cross=2.0):
    """Seamless loop: the last `cross` seconds are crossfaded (equal power) into the start."""
    c = int(cross * SR)
    head, body, tail = x[:c], x[c:-c], x[-c:]
    w = np.linspace(0, np.pi / 2, c)
    mixed = tail * np.cos(w) + head * np.sin(w)
    return np.concatenate([mixed, body])


def place(dst, src, at):
    i = int(at * SR)
    j = min(len(dst), i + len(src))
    if j <= i:
        return
    dst[i:j] += src[: j - i]


def write_ogg(path, x):
    import soundfile as sf
    path.parent.mkdir(parents=True, exist_ok=True)
    data = np.clip(x, -1, 1).astype(np.float32)
    # libsndfile's Vorbis encoder overflows the stack on long single writes (Windows): write in blocks
    with sf.SoundFile(str(path), "w", SR, 1, format="OGG", subtype="VORBIS") as f:
        for i in range(0, len(data), 16384):
            f.write(data[i:i + 16384])


def write_wav(path, x):
    import soundfile as sf
    path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(path), np.clip(x, -1, 1).astype(np.float32), SR, subtype="PCM_16")
