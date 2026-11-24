"""Studio-clean Dungeons 2 Singer & Mourner vocal engine (v3 — pitch & clarity matched to video).

Matched directly to the Dungeons 2 Singer reference (170-334 Hz / A3 center, 1100-1450 Hz centroid):
- Zero mic noise, zero TD-PSOLA comb-filtering: 100% clean band-limited studio synthesis.
- Pitch register restored to full musical range:
  * Speech/actions centered at A3 = 220 Hz (video's exact 170-334 Hz sweet spot).
  * Songs match exact MC note-block octave (F#3..F#5):
    - Low register:  B3  (246.94 Hz, notes 0..8)
    - Mid register:  F#4 (369.99 Hz, notes 9..16)
    - High register: C#5 (554.37 Hz, notes 17..24)
- Clear, musical throat resonance: cascaded pharyngeal-oral cavity (635 Hz hollow throat +
  1200-1450 Hz clear singing formant) + controlled organic false-vocal-fold warmth.
"""
import numpy as np
from scipy.signal import butter, lfilter, sosfilt

import synth as S

SR = S.SR

# Cascaded vocal-tract formants (F1, Q1, F2, Q2, F3, Q3) — clear, resonant, non-muffled
CASCADED_VOWELS = {
    "aw": (635.0, 6.5, 1160.0, 8.0, 2450.0, 10.5),   # Signature Dungeons 2 resonant hollow "AAAW"
    "ah": (710.0, 6.5, 1280.0, 8.0, 2550.0, 10.5),   # Clear open resonant call "AAAH"
    "oh": (520.0, 6.2,  940.0, 7.8, 2320.0, 10.5),   # Warm solemn "OOOH"
    "oo": (380.0, 6.0,  820.0, 7.5, 2220.0, 10.5),   # Deep round "UUUU"
    "eh": (580.0, 6.5, 1580.0, 8.5, 2580.0, 10.5),   # Bright expressive "EEEH"
    "mm": (290.0, 5.5, 1020.0, 8.0, 2200.0, 11.0),   # Warm hum "MMMM"
}


def _smooth_noise(n, cutoff_hz, rng):
    x = rng.normal(0.0, 1.0, n)
    sos = butter(2, min(cutoff_hz, SR * 0.45), btype="low", fs=SR, output="sos")
    y = sosfilt(sos, x)
    return y / (np.std(y) + 1e-9)


def _resonator(x, freq, q):
    w0 = 2.0 * np.pi * min(freq, SR * 0.45) / SR
    r = np.exp(-np.pi * (freq / max(0.5, q)) / SR)
    a1 = -2.0 * r * np.cos(w0)
    a2 = r * r
    b0 = 1.0 - r
    return lfilter([b0], [1.0, a1, a2], x)


def _peak_eq(x, freq, q, gain_db):
    w0 = 2.0 * np.pi * min(freq, SR * 0.45) / SR
    A = 10.0 ** (gain_db / 40.0)
    alpha = np.sin(w0) / (2.0 * q)
    b0 = 1.0 + alpha * A
    b1 = -2.0 * np.cos(w0)
    b2 = 1.0 - alpha * A
    a0 = 1.0 + alpha / A
    a1 = -2.0 * np.cos(w0)
    a2 = 1.0 - alpha / A
    return lfilter([b0 / a0, b1 / a0, b2 / a0], [1.0, a1 / a0, a2 / a0], x)


def glottal_clean_throat(f0, rng, brightness=1.0, throat_depth=0.28, drift=0.004):
    """Band-limited studio-clean glottal harmonic source + musical false-vocal-fold throat warmth."""
    n = len(f0)
    t = np.arange(n) / SR
    if drift > 0 and rng is not None:
        f_inst = f0 * (1.0 + drift * _smooth_noise(n, 5.2, rng))
    else:
        f_inst = f0.copy()

    phase = 2.0 * np.pi * np.cumsum(f_inst) / SR
    out = np.zeros(n, dtype=np.float64)

    # Alias-free harmonic series (matches the video's strong 1st-6th harmonics + clean top end)
    max_hz = min(6500.0, 5200.0 * brightness)
    for h in range(1, 28):
        fh = h * f_inst
        mask = fh < max_hz
        if not mask.any():
            break
        if h <= 5:
            amp = (1.0 / (h ** (0.52 / max(0.55, brightness)))) * (1.0 + 0.10 * (h % 2))
        else:
            amp = (1.0 / (5 ** (0.52 / max(0.55, brightness)))) * ((5.0 / h) ** (1.70 / max(0.55, brightness)))
        out += mask * amp * np.sin(h * phase + 0.38 * (h - 1))

    # Musical throat-resonance layer: subtle ventricular period-doubling (0.5x & 1.5x) without harsh static
    if throat_depth > 0 and rng is not None:
        onset_eng = 1.0 + 0.40 * np.exp(-t / 0.14)
        eng = np.clip(0.80 + 0.20 * _smooth_noise(n, 4.0, rng), 0.45, 1.15) * onset_eng
        # Smooth subharmonic + 1.5x throat overtone locked cleanly to glottal phase
        sub = 0.68 * np.sin(0.5 * phase) + 0.32 * np.sin(1.5 * phase)
        # Gentle alternate-cycle amplitude contour for organic throat resonance
        alt = 1.0 + (throat_depth * 0.32) * eng * np.cos(0.5 * phase)
        out = out * alt + (throat_depth * 0.38) * eng * sub

    out = out / (np.std(out) + 1e-9)
    return np.tanh(out * 0.72)


def cascaded_throat_tract(src, vowels, shift=1.0, resonance_boost=1.0):
    """Cascaded pharyngeal-oral vocal tract with clear 635 Hz hollow throat + 1250 Hz presence."""
    n = len(src)

    def _render_vowel(vname):
        f1, q1, f2, q2, f3, q3 = CASCADED_VOWELS[vname]
        y = _resonator(src, f1 * shift, q1 * resonance_boost)
        y = _resonator(y, f2 * shift, q2 * resonance_boost)
        y = _resonator(y, f3 * shift, q3)
        # Clear hollow pharyngeal ring + warm fundamental body
        pharynx = S.bandpass(src, f1 * shift, q1 * 1.25) * 0.45
        presence = S.bandpass(src, f2 * shift, q2 * 1.25) * 0.28
        chest = S.lowpass(src, 320.0 * shift, order=2) * 0.24
        return y + pharynx + presence + chest

    if len(vowels) == 1:
        out = _render_vowel(vowels[0])
    else:
        layers = [_render_vowel(v) for v in vowels]
        pos = np.linspace(0.0, len(layers) - 1, n)
        out = np.zeros(n, dtype=np.float64)
        for i, layer in enumerate(layers):
            w = np.clip(1.0 - np.abs(pos - i), 0.0, 1.0)
            out += w * layer

    # Sculpt to match the video's 635 Hz hollow throat peak + 1100-1450 Hz clear centroid
    out = _peak_eq(out, 635.0 * shift, 2.2, 4.5)
    out = _peak_eq(out, 1280.0 * shift, 2.4, 3.0)
    out = _peak_eq(out, 340.0 * shift, 2.0, -2.0)
    return out


def dark_cavern_reverb(x, wet=0.30, size=1.08, damp=0.76, cutoff=3800.0):
    """Clean, airy cathedral/cavern reverb (3800 Hz tail keeps audio crisp and hi-fi)."""
    tail_len = int(SR * 2.0 * size)
    xx = np.concatenate([x, np.zeros(tail_len)])
    er = np.zeros(len(xx), dtype=np.float64)
    for delay_ms, gain in ((19, 0.24), (39, 0.18), (63, 0.12)):
        d = int(delay_ms * 0.001 * SR)
        if d < len(xx):
            er[d:] += gain * xx[:-d]
    combs = [1429, 1553, 1667, 1789, 1913, 2053]
    acc = np.zeros(len(xx), dtype=np.float64)
    for idx, d in enumerate(combs):
        dl = max(32, int(d * size))
        a = np.zeros(dl + 1)
        a[0], a[-1] = 1.0, -(damp - 0.015 * (idx % 3))
        acc += lfilter([1.0], a, xx)
    acc /= len(combs)
    for d, g in ((211, 0.50), (389, 0.46), (617, 0.42)):
        b = np.zeros(d + 1)
        a = np.zeros(d + 1)
        b[0], b[-1] = -g, 1.0
        a[0], a[-1] = 1.0, -g
        acc = lfilter(b, a, acc)
    sos = butter(2, min(cutoff, SR * 0.45), btype="low", fs=SR, output="sos")
    acc = sosfilt(sos, acc + 0.45 * er)
    out = (1.0 - wet) * xx + wet * acc
    return S.trim_tail(out, floor=2e-4)


def singer_tone(f0, rng, vowels=("aw", "oh"), brightness=1.0, grit=0.28, breath=0.08,
                reed_mix=0.0, shift=1.0, voices=2, detune_cents=5.0, lowpass_hz=5200.0):
    """Render studio-clean Dungeons 2 Singer voice: clear, resonant, hollow-throated, hi-fi."""
    n = len(f0)
    t = np.arange(n) / SR
    # Map legacy grit values smoothly into clean musical throat_depth [0.18..0.40]
    td = float(np.clip(grit * 0.62, 0.16, 0.42))

    def render_one(f_curve, depth):
        src = glottal_clean_throat(f_curve, rng, brightness=brightness, throat_depth=depth)
        if breath > 0 and rng is not None:
            air = S.noise_band(len(f_curve), 600, 3400, rng, colour="white")
            air_env = 0.7 + 1.2 * np.exp(-t / 0.10)
            src = src + breath * air * air_env * 0.95
        v = cascaded_throat_tract(src, vowels, shift=shift, resonance_boost=1.02)
        return S.lowpass(v, lowpass_hz, order=2)

    v = render_one(f0, td)
    v /= np.max(np.abs(v)) + 1e-9

    if voices > 1 and detune_cents > 0:
        s2 = render_one(f0 * 2.0 ** (-detune_cents / 1200.0), td * 0.75)
        s2 /= np.max(np.abs(s2)) + 1e-9
        S.place(v, 0.30 * s2, 0.009)

    return v[:n] / (np.max(np.abs(v[:n])) + 1e-9)


def mourner_tone(f0, rng, vowels=("oh", "oo"), brightness=0.82, grit=0.40, breath=0.16,
                 reed_mix=0.0, shift=0.92, voices=2, detune_cents=12.0, lowpass_hz=3600.0):
    """Render Mourner: same clean vocal tract, darker, hollow, trembling, starved & weeping."""
    n = len(f0)
    t = np.arange(n) / SR
    td = float(np.clip(grit * 0.68, 0.25, 0.50))

    def render_one(f_curve, depth):
        src = glottal_clean_throat(f_curve, rng, brightness=brightness, throat_depth=depth, drift=0.009)
        if breath > 0 and rng is not None:
            air = S.noise_band(len(f_curve), 450, 2600, rng, colour="white")
            src = src + breath * air * (0.85 + 0.9 * np.exp(-t / 0.15)) * 1.25
        v = cascaded_throat_tract(src, vowels, shift=shift, resonance_boost=1.08)
        return S.lowpass(v, lowpass_hz, order=2)

    v = render_one(f0, td)
    v /= np.max(np.abs(v)) + 1e-9
    s2 = render_one(f0 * 2.0 ** (-detune_cents / 1200.0), td * 0.8)
    s2 /= np.max(np.abs(s2)) + 1e-9
    S.place(v, 0.32 * s2, 0.015)
    return v[:n] / (np.max(np.abs(v[:n])) + 1e-9)


def register_profile(register="mid", variant=0):
    """Multi-register presets for F#3..F#5 note-block songs (Low B3 / Mid F#4 / High C#5)."""
    if register == "low":
        # B3 (246.94 Hz): rich hollow throat-chant (matches video's 170-290 Hz sweet spot!)
        vowels = ("aw", "oh") if variant == 0 else ("oh", "aw")
        return dict(vowels=vowels, brightness=0.96, grit=0.48, breath=0.08,
                    shift=0.98, lowpass_hz=4400.0, bell_mix=0.008)
    if register == "high":
        # C#5 (554.37 Hz): clear, soaring, radiant resonant singing (zero harshness)
        vowels = ("ah", "eh") if variant == 0 else ("ah", "aw")
        return dict(vowels=vowels, brightness=1.12, grit=0.26, breath=0.09,
                    shift=1.06, lowpass_hz=5800.0, bell_mix=0.018)
    # Mid F#4 (369.99 Hz): clear melodic Dungeons 2 singing voice
    vowels = ("aw", "ah") if variant == 0 else ("ah", "oh")
    return dict(vowels=vowels, brightness=1.04, grit=0.38, breath=0.08,
                shift=1.02, lowpass_hz=5200.0, bell_mix=0.012)


def render_singer_note(base_hz, rng, register="mid", variant=0, seconds=1.10):
    """Render one sustained studio-clean Singer song note."""
    prof = register_profile(register, variant)
    n = int(seconds * SR)
    t = np.arange(n) / SR
    scoop = 1.0 - 0.016 * np.exp(-t / 0.024)
    f0 = np.full(n, base_hz, dtype=np.float64) * scoop
    f0 = S.vibrato(f0, rate=4.8, depth=0.0032, rng=rng, delay=0.32)
    bell_mix = prof.pop("bell_mix")
    v = singer_tone(f0, rng, **prof)
    v = v * S.adsr(len(v), attack=0.055, release=0.55, curve=1.4)
    if bell_mix > 0:
        S.place(v, bell_mix * S.bell(base_hz * 2.0, 0.9, rng) * np.max(np.abs(v)), 0.0)
    return S.normalise(dark_cavern_reverb(S.normalise(v), wet=0.28, size=1.05), -2.0)


def render_mourner_note(base_hz, rng, register="mid", variant=0, seconds=1.20):
    """Render one sustained studio-clean Mourner weeping note."""
    prof = register_profile(register, variant)
    prof.pop("bell_mix", None)
    prof["brightness"] *= 0.82
    prof["grit"] = min(0.60, prof["grit"] + 0.14)
    prof["breath"] = 0.16
    prof["shift"] *= 0.92
    prof["lowpass_hz"] *= 0.78
    prof["vowels"] = ("oh", "oo") if variant == 0 else ("aw", "oo")

    n = int(seconds * SR)
    t = np.arange(n) / SR
    sag = 2.0 ** ((-0.22 - 0.12 * (t / seconds)) / 12.0)
    f0 = S.vibrato(np.full(n, base_hz, dtype=np.float64) * sag, rate=6.8, depth=0.020, rng=rng, delay=0.08, jitter=2.8)
    v = mourner_tone(f0, rng, **prof)
    sob_rate = 2.5 if variant == 0 else 2.9
    sob_env = 1.0 - 0.28 * (0.5 + 0.5 * np.sin(2.0 * np.pi * sob_rate * t)) ** 3
    v = v * sob_env * S.adsr(len(v), attack=0.07, release=0.58, curve=1.45)
    return S.normalise(dark_cavern_reverb(S.normalise(v), wet=0.35, size=1.18, cutoff=3000.0), -2.0)
