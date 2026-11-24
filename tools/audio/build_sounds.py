"""The Sift's own sounds: synthesised voices, chimes and ambience, optionally mixed with free samples from sound_sources/.

Usage:
  python -I tools/audio/build_sounds.py <project> [--only singer,mourner,willow_grove] [--install]

Without --install only previews are written: build/audio_preview/<name>/<sound>.ogg plus one <name>_preview.wav that
plays every variant in a row (easy to listen to). With --install the .ogg files go to assets/pysift/sounds/... as well.
Each recipe is seeded, so re-running gives the same sounds. Samples: sound_sources/<name>/<use>_*.{mp3,wav,ogg}
(see sound_sources/README.md); a recipe that can use samples still works without them.
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import synth as S  # noqa: E402
import singer_voice as SV  # noqa: E402

P = Path(sys.argv[1]).resolve()
ARGS = sys.argv[2:]
ONLY = next((a.split("=", 1)[1] if "=" in a else ARGS[ARGS.index(a) + 1] for a in ARGS if a.startswith("--only")), None)
INSTALL = "--install" in ARGS
PREVIEW = P / "build/audio_preview"
ASSETS = P / "src/main/resources/assets/pysift/sounds"
SOURCES = P / "sound_sources"

# 歌者音域：對齊影片 Dungeons 2 歌者的清晰音高（170~334 Hz，A3 = 220 Hz 為中心），
# 唱歌三段音區完全對齊原版音符盒八度（F#3~F#5）：低音區 B3 (note 5)、中音區 F#4 (note 12)、高音區 C#5 (note 19)
A3 = 220.00
VOICE_LOW = 246.94    # B3  (note 5,  覆蓋 0..8:  F#3..D4)
VOICE_BASE = 369.99   # F#4 (note 12, 覆蓋 9..16: D#4..A#4)
VOICE_HIGH = 554.37   # C#5 (note 19, 覆蓋 17..24: B4..F#5)
SCALE = [0, 2, 4, 7, 9, 12, 14]   # major pentatonic - the Singers' lullaby


def note(base, step):
    return base * 2 ** (step / 12)


def load_samples(name, use):
    """All sound_sources/<name>/<use>_* files as mono float arrays at SR."""
    import soundfile as sf
    from scipy.signal import resample_poly
    out = []
    folder = SOURCES / name
    if not folder.is_dir():
        return out
    for f in sorted(folder.iterdir()):
        if f.suffix.lower() in (".mp3", ".wav", ".ogg", ".flac") and f.name.startswith(use + "_"):
            data, sr = sf.read(str(f), always_2d=True)
            mono = data.mean(axis=1)
            if sr != S.SR:
                mono = resample_poly(mono, S.SR, sr)
            out.append(mono / (np.max(np.abs(mono)) + 1e-9))
    return out


def pitch_shift(x, semitones):
    """Resampling shift (changes length too - fine for moans and growls)."""
    from scipy.signal import resample
    factor = 2 ** (-semitones / 12)
    return resample(x, max(1, int(len(x) * factor)))


# ================================================================ Singer: Dungeons 2 resonant hollow baritone-tenor
# 參考 Minecraft Dungeons 2 歌者（baritone-tenor 115~310 Hz）：空靈渾厚的胸腔喉音「啊喔／嗚」、
# 635 Hz 共鳴峰、自然氣聲與微粗糙聲帶質感、低亮度深洞穴殘響，並分為低／中／高三段音區音色供歌曲使用。
def soft_voice(f0, rng, vowels=("aw", "oh"), brightness=1.0, grit=0.48, breath=0.14, reed_mix=0.0, shift=1.0):
    return SV.singer_tone(f0, rng, vowels=vowels, brightness=brightness, grit=grit,
                          breath=breath, reed_mix=reed_mix, shift=shift)


def singer_phrase(rng, steps, base=A3, vowels=("aw", "oh"), harmony=0):
    notes = [(note(base, SCALE[s]), rng.uniform(0.45, 0.72)) for s in steps]
    notes[-1] = (notes[-1][0], notes[-1][1] + 0.55)
    f0 = S.vibrato(S.glide_curve(notes, rng, glide=0.04), rate=4.6, depth=0.0038, rng=rng, delay=0.32)
    v = soft_voice(f0, rng, vowels)
    if harmony:
        v2 = soft_voice(f0 * 2 ** (harmony / 12), rng, ("oh", "oo"), brightness=0.85)
        S.place(v, 0.42 * v2[: len(v)], 0.0)
    v = v * S.adsr(len(v), attack=0.14, release=0.60, curve=1.40)
    t = 0.0
    for f, d in notes:
        S.place(v, 0.009 * S.bell(f * 4, 1.1, rng) * np.max(np.abs(v)), t)
        t += d
    return SV.dark_cavern_reverb(S.normalise(v), wet=0.28, size=1.08)


def singer(rng):
    sounds = {}
    phrases = [[0, 2, 4], [4, 3, 1], [2, 4, 5, 4], [5, 4, 2, 0]]
    vowel_sets = [("aw", "oh"), ("oh", "aw", "oo"), ("aw", "ah", "oh"), ("ah", "aw", "oh")]
    for i, (steps, vs) in enumerate(zip(phrases, vowel_sets), 1):
        sounds[f"ambient{i}"] = S.normalise(singer_phrase(rng, steps, vowels=vs), -4)
    for i in (1, 2):   # hurt: startled husky cry
        f0 = S.glide_curve([(note(A3, 4 + i), 0.08), (note(A3, 11 + i), 0.12), (note(A3, 1), 0.20)], rng, glide=0.045)
        v = soft_voice(S.vibrato(f0, rate=8.5, depth=0.018, rng=rng, delay=0), rng, ("ah", "aw", "oh"),
                       brightness=1.12, grit=0.56, breath=0.18)
        v = v * S.adsr(len(v), attack=0.012, release=0.16)
        S.place(v, 0.07 * S.bell(note(A3, 24 + i), 0.45, rng), 0.0)
        sounds[f"hurt{i}"] = S.normalise(SV.dark_cavern_reverb(S.normalise(v), wet=0.20, size=0.75), -3)
    # death: long hollow fall from high to deep chest + crystal shatter
    f0 = np.geomspace(note(A3, 10), note(A3, -12), int(2.0 * S.SR))
    f0 = S.vibrato(f0, rate=6.0, depth=0.028, rng=rng, delay=0.25)
    v = soft_voice(f0, rng, ("aw", "oh", "oo", "mm"), brightness=0.88, grit=0.60, breath=0.20) * S.adsr(len(f0), 0.05, 0.95)
    for k in range(7):
        S.place(v, 0.07 * S.bell(note(A3, 19 + rng.integers(0, 12)), 1.3, rng, bright=1.8), 1.15 + k * 0.05)
    sounds["death1"] = S.normalise(SV.dark_cavern_reverb(S.normalise(v), wet=0.34, size=1.18), -3)
    # 唱歌用的三段音區與音色變體（低 B2 / 中 F#3 / 高 C#4），供歌曲套用不失真
    sounds["voice_low1"] = SV.render_singer_note(VOICE_LOW, rng, "low", 0, 1.2)
    sounds["voice_low2"] = SV.render_singer_note(VOICE_LOW, rng, "low", 1, 1.2)
    sounds["voice"] = SV.render_singer_note(VOICE_BASE, rng, "mid", 0, 1.15)
    sounds["voice2"] = SV.render_singer_note(VOICE_BASE, rng, "mid", 1, 1.15)
    sounds["voice_high1"] = SV.render_singer_note(VOICE_HIGH, rng, "high", 0, 1.1)
    sounds["voice_high2"] = SV.render_singer_note(VOICE_HIGH, rng, "high", 1, 1.1)
    sounds.update(singer_actions(rng))
    return sounds


def call(rng, notes, base=A3, vowels=("aw", "oh"), legato=True, attack=0.055, release=0.36, vib=0.0038, vib_rate=4.6,
         breath_burst=0.0, wet=0.28, size=1.05, peak=-3, tremble=0.0, brightness=1.0, grit=0.48, breath=0.14):
    """A short vocal gesture. notes = [(semitones from base, seconds)]; legato = one breath, else separate syllables."""
    if legato:
        f0 = S.glide_curve([(note(base, s), d) for s, d in notes], rng, glide=0.038)
        f0 = S.vibrato(f0, rate=vib_rate, depth=vib, rng=rng, delay=0.12, jitter=tremble)
        v = soft_voice(f0, rng, vowels, brightness=brightness, grit=grit, breath=breath) * S.adsr(len(f0), attack, release, curve=1.45)
    else:
        total = sum(d for _, d in notes) + 0.5
        v = np.zeros(int(total * S.SR))
        t = 0.0
        for s, d in notes:
            f0 = S.vibrato(np.full(int(d * 0.82 * S.SR), note(base, s)), rate=vib_rate, depth=vib, rng=rng, delay=0.05, jitter=tremble)
            syl = soft_voice(f0, rng, vowels, brightness=brightness, grit=grit, breath=breath) * S.adsr(len(f0), min(attack, 0.025), min(release, d * 0.42), curve=1.45)
            S.place(v, syl / (np.max(np.abs(syl)) + 1e-9), t)
            t += d
    if breath_burst:   # a sharp intake of breath before the voice (gasp)
        n = int(0.18 * S.SR)
        b = S.noise_band(n, 700, 3800, rng) * S.adsr(n, 0.02, 0.12) * breath_burst
        v = np.concatenate([b, np.zeros(int(0.03 * S.SR)), v / (np.max(np.abs(v)) + 1e-9)])
    return S.normalise(SV.dark_cavern_reverb(S.normalise(v), wet=wet, size=size), peak)


def singer_actions(rng):
    """歌者對世界與玩家的每個互動各有一段人聲（SingerEntity / SiftPortalRitual 裡播放）。"""
    s = {}
    s["greet1"] = call(rng, [(4, 0.24), (9, 0.52)], vowels=("oh", "aw", "ah"), brightness=1.06)          # 從地底爬出：「喔—啊！」往上
    s["greet2"] = call(rng, [(2, 0.22), (7, 0.20), (12, 0.48)], vowels=("oh", "aw", "ah"), brightness=1.08)
    s["beckon1"] = call(rng, [(7, 0.32), (4, 0.46)], vowels=("aw", "oh"), release=0.32)                  # 招手等迴音碎片
    s["beckon2"] = call(rng, [(9, 0.28), (7, 0.22), (4, 0.42)], vowels=("aw", "oh"), release=0.32)
    s["call1"] = call(rng, [(0, 0.36), (4, 0.32), (7, 0.32), (12, 0.95)], vowels=("oh", "aw", "ah"), brightness=1.10, wet=0.48, size=1.35)   # 回應山羊角
    s["call2"] = call(rng, [(-5, 0.36), (2, 0.32), (7, 0.36), (9, 0.92)], vowels=("oo", "aw", "ah"), brightness=1.08, wet=0.48, size=1.35)
    f0_sweep = [(0, 0.16), (5, 0.16), (9, 0.16), (12, 0.22), (9, 0.16), (5, 0.16), (2, 0.36)]
    s["sweep1"] = call(rng, f0_sweep, vowels=("oo", "aw", "oo"), wet=0.42)                               # 揮手打掃
    s["summon1"] = call(rng, [(0, 0.42), (7, 0.42), (12, 0.42), (16, 1.3)], vowels=("aw", "ah", "aw"), brightness=1.16, grit=0.58, vib=0.006, wet=0.36, size=1.35, peak=-2)   # 召喚傀儡
    s["gasp1"] = call(rng, [(9, 0.12), (5, 0.18), (0, 0.46)], vowels=("oh", "oo"), breath_burst=0.65, grit=0.56, tremble=2.0)  # 儀式走調
    s["cheer1"] = call(rng, [(0, 0.13), (4, 0.13), (7, 0.13), (12, 0.13), (16, 0.62)], vowels=("aw", "ah"), brightness=1.14, grit=0.45, legato=False, release=0.22)  # 開門慶祝
    s["cheer2"] = call(rng, [(7, 0.13), (12, 0.13), (7, 0.13), (12, 0.13), (17, 0.62)], vowels=("aw", "ah"), brightness=1.14, grit=0.45, legato=False, release=0.22)
    s["giggle1"] = call(rng, [(10, 0.09), (12, 0.09), (10, 0.09), (14, 0.09), (10, 0.09), (17, 0.26)],   # 抱小傀儡玩：咯咯笑
                        legato=False, vowels=("ah", "eh"), brightness=1.12, grit=0.36, release=0.06, wet=0.24)
    s["giggle2"] = call(rng, [(14, 0.09), (12, 0.09), (10, 0.09), (12, 0.09), (14, 0.09), (19, 0.28)],
                        legato=False, vowels=("ah", "eh"), brightness=1.14, grit=0.36, release=0.06, wet=0.24)
    s["thanks1"] = call(rng, [(0, 0.26), (5, 0.62)], vowels=("mm", "aw", "oh"), brightness=0.96, grit=0.46, wet=0.30)     # 收到靈魂晶塊
    s["unease1"] = call(rng, [(2, 0.52), (1, 0.62)], base=A3 * 0.75, vowels=("oo", "mm"), brightness=0.82, grit=0.60, breath=0.20, vib=0.018, vib_rate=8.5, tremble=3.5, peak=-5)  # 看見監守者
    s["starve1"] = call(rng, [(0, 0.62), (-2, 0.82)], base=A3 * 0.75, vowels=("oh", "oo", "mm"), brightness=0.78, grit=0.62, breath=0.22, vib=0.016, tremble=3.0, wet=0.34, peak=-6)   # 快要屍化
    f0 = S.vibrato(np.geomspace(note(A3, 7), note(A3, -10), int(2.4 * S.SR)), rate=6.8, depth=0.028, rng=rng, delay=0.2, jitter=3.8)
    v = soft_voice(f0, rng, ("aw", "oh", "oo", "mm"), brightness=0.82, grit=0.64, breath=0.24) * S.adsr(len(f0), 0.06, 1.2)   # 屍化成哀悼者
    v = v * np.linspace(1.0, 0.35, len(v)) + 0.22 * S.noise_band(len(v), 280, 2000, rng) * np.linspace(0, 1, len(v))
    s["hollow1"] = S.normalise(SV.dark_cavern_reverb(S.normalise(v), wet=0.38, size=1.35, cutoff=2300.0), -3)
    # 哀悼者被治好、長回毛：從低低的哭腔一路往上，變成明亮的歡呼
    s["reborn1"] = call(rng, [(-5, 0.36), (0, 0.32), (4, 0.32), (7, 0.32), (12, 1.05)], vowels=("oo", "oh", "aw", "ah"), brightness=1.12, grit=0.50, vib=0.004, wet=0.34, size=1.25, peak=-2)
    return s


def sung_note(rng, vowels, breath, vib, shift, chime, sob=False, seconds=1.0):
    """One sustained sung note at VOICE_BASE: the ritual songs play it at note-block pitches."""
    f0 = S.vibrato(np.full(int(seconds * S.SR), VOICE_BASE), rate=vib[0], depth=vib[1], rng=rng, delay=0.12,
                   jitter=3.0 if sob else 0.0)
    v = SV.singer_tone(f0, rng, vowels=vowels, breath=max(0.08, breath), shift=shift)
    if sob:
        v *= 1 - 0.35 * (0.5 + 0.5 * np.sin(2 * np.pi * 2.6 * np.arange(len(v)) / S.SR)) ** 3
    v = v * S.adsr(len(v), attack=0.05, release=0.55)
    if chime:
        S.place(v, chime * S.bell(VOICE_BASE * 4, 1.0, rng) * np.max(np.abs(v)) * 8, 0.0)
    return S.normalise(SV.dark_cavern_reverb(S.normalise(v), wet=0.28, size=0.9), -2)


# ================================================================ Mourner: the Singer's voice, starved and weeping
# 同一副 Dungeons 2 歌者嗓子，只是餓壞了：低四度、聲帶沙啞粗糙、氣聲重、顫抖抽泣、空洞殘響。
M_BASE = A3 / 2 ** (5 / 12)


def sob(n, rng, rate=None, depth=0.45):
    rate = rate or rng.uniform(2.2, 3.1)
    return 1 - depth * (0.5 + 0.5 * np.sin(2 * np.pi * rate * np.arange(n) / S.SR)) ** 3


def mourner_voice(f0, rng, vowels=("oh", "oo"), brightness=0.80, grit=0.62, breath=0.22):
    return SV.mourner_tone(f0, rng, vowels=vowels, brightness=brightness, grit=grit, breath=breath)


def m_call(rng, notes, vowels=("oh", "oo"), attack=0.14, release=0.60, vib=0.022, sobbing=0.42, wet=0.36, size=1.25, peak=-4,
           base=M_BASE, brightness=0.80, grit=0.62):
    f0 = S.glide_curve([(note(base, st) * 2 ** (-rng.uniform(0, 0.38) / 12), d) for st, d in notes], rng, glide=0.14)
    f0 = S.vibrato(f0, rate=6.8, depth=vib, rng=rng, delay=0.06, jitter=3.2)
    v = mourner_voice(f0, rng, vowels, brightness=brightness, grit=grit) * S.adsr(len(f0), attack, release, curve=1.5)
    if sobbing:
        v *= sob(len(v), rng, depth=sobbing)
    return S.normalise(SV.dark_cavern_reverb(S.normalise(v), wet=wet, size=size, cutoff=2300.0), peak)


def mourner(rng):
    sounds = {}
    samples = load_samples("mourner", "ambient")
    phrases = [[(9, 0.7), (7, 0.6), (4, 0.9)], [(7, 0.6), (4, 0.5), (2, 0.5), (0, 0.9)], [(12, 0.6), (9, 0.6), (5, 0.9)], [(4, 0.6), (2, 0.6), (0, 1.0)]]
    for i, notes in enumerate(phrases, 1):   # 啜泣：倒著往下走的旋律
        v = m_call(rng, notes, ("oh", "oo", "mm"), peak=-5)
        if samples:   # a free moan underneath, lowered and darkened
            smp = pitch_shift(samples[(i - 1) % len(samples)], -rng.uniform(3, 6))[: len(v)]
            smp = S.bandpass(smp, 480, 0.8) * S.adsr(len(smp), 0.2, 0.6)
            S.place(v, 0.42 * smp * np.max(np.abs(v)) / (np.max(np.abs(smp)) + 1e-9), 0.0)
            v = S.normalise(v, -5)
        sounds[f"ambient{i}"] = v
    for i in (1, 2):   # 受傷：短促沙啞的一聲哭叫
        sounds[f"hurt{i}"] = m_call(rng, [(7 + i, 0.11), (3, 0.36)], ("aw", "oh"), attack=0.02, release=0.22, sobbing=0, wet=0.26, size=0.88, peak=-3, brightness=0.92, grit=0.68)
    f0 = S.vibrato(np.geomspace(note(M_BASE, 7), note(M_BASE, -13), int(2.6 * S.SR)), 6, 0.036, rng, 0.2, 3.8)
    v = mourner_voice(f0, rng, ("oh", "oo", "mm"), grit=0.68) * S.adsr(len(f0), 0.1, 1.4) * sob(len(f0), rng, 1.8, 0.38)
    sounds["death1"] = S.normalise(SV.dark_cavern_reverb(S.normalise(v), 0.40, 1.35, cutoff=2200.0), -3)
    # 唱歌用的三段音區哀悼單音（倒唱哀悼之歌時自動依音高切換音色）
    sounds["voice_low1"] = SV.render_mourner_note(VOICE_LOW, rng, "low", 0, 1.3)
    sounds["voice_low2"] = SV.render_mourner_note(VOICE_LOW, rng, "low", 1, 1.3)
    sounds["voice"] = SV.render_mourner_note(VOICE_BASE, rng, "mid", 0, 1.25)
    sounds["voice2"] = SV.render_mourner_note(VOICE_BASE, rng, "mid", 1, 1.25)
    sounds["voice_high1"] = SV.render_mourner_note(VOICE_HIGH, rng, "high", 0, 1.2)
    sounds["voice_high2"] = SV.render_mourner_note(VOICE_HIGH, rng, "high", 1, 1.2)
    # 互動
    sounds["wail1"] = m_call(rng, [(0, 0.5), (5, 0.5), (9, 1.4)], ("oo", "oh", "aw"), attack=0.38, release=0.9, sobbing=0.25, peak=-3, brightness=0.90, grit=0.66)   # 看到玩家、開始哭著唱
    sounds["wail2"] = m_call(rng, [(2, 0.5), (7, 0.6), (11, 1.3)], ("oo", "oh", "aw"), attack=0.38, release=0.9, sobbing=0.25, peak=-3, brightness=0.90, grit=0.66)
    sounds["soothe1"] = m_call(rng, [(4, 0.5), (7, 0.9)], ("mm", "aw", "oh"), vib=0.01, sobbing=0.1, peak=-5, brightness=0.90, grit=0.52)   # 泡靈液／聽香爐
    sounds["soothe2"] = m_call(rng, [(2, 0.5), (9, 0.9)], ("mm", "aw", "oh"), vib=0.01, sobbing=0.1, peak=-5, brightness=0.90, grit=0.52)
    sounds["hush1"] = m_call(rng, [(5, 0.3), (4, 0.4), (2, 0.8)], ("oh", "oo", "mm"), vib=0.015, sobbing=0.28, release=0.82, peak=-6, grit=0.58)   # 被號角安撫
    return sounds


# ================================================================ Willow Grove ambience
def willow_grove(rng):
    sounds = {}
    # loop: 24 s of soft wind through the willows (three bands, each breathing at its own pace) + a faint low drone
    n = int(26 * S.SR)
    t = np.arange(n) / S.SR
    wind = np.zeros(n)
    for lo, hi, rate, g in ((120, 420, 0.07, 1.0), (380, 1100, 0.11, 0.55), (1500, 4200, 0.17, 0.18)):
        lfo = 0.55 + 0.45 * np.sin(2 * np.pi * rate * t + rng.uniform(0, 6.28)) * np.sin(2 * np.pi * rate * 0.37 * t + 1)
        wind += g * S.noise_band(n, lo, hi, rng, "brown" if lo < 200 else "white") * lfo
    drone = sum(0.06 / (k + 1) * np.sin(2 * np.pi * f * t) for k, f in enumerate((55.0, 82.4, 110.0)))
    loop = S.make_loop(S.normalise(wind) * 0.9 + drone, cross=2.0)
    sounds["loop"] = S.normalise(loop, -8)
    # mood: a distant choir chord swelling and fading (Singers far away)
    for i, chord in enumerate(([0, 4, 7, 12], [-3, 2, 7, 9]), 1):
        dur = 6.5
        m = np.zeros(int(dur * S.SR))
        for k, st in enumerate(chord):
            f0 = S.vibrato(np.full(len(m), note(A3 / 2, st)), rate=4.5 + k * 0.3, depth=0.008, rng=rng, delay=0)
            m += S.voice(f0, ("mm", "oo", "mm"), breath=0.02, rng=rng) * (0.8 if k else 1.0)
        m *= S.adsr(len(m), attack=2.2, release=2.8, curve=1.5)
        m = S.bandpass(m, 600, 0.6)   # far away: thin and muffled
        sounds[f"mood{i}"] = S.normalise(S.reverb(S.normalise(m), wet=0.6, size=1.6), -6)
    # additions: a few crystal chimes in the willows and a spirit-liquid drip
    for i in range(1, 4):
        a = np.zeros(int(3.0 * S.SR))
        for k in range(rng.integers(2, 4)):
            S.place(a, (0.6 + 0.4 * rng.random()) * S.bell(note(A3 * 2, SCALE[rng.integers(0, 7)]), 2.2, rng, bright=0.8),
                    k * rng.uniform(0.18, 0.4))
        sounds[f"additions{i}"] = S.normalise(S.reverb(S.normalise(a), wet=0.45, size=1.2), -8)
    drip = np.zeros(int(1.2 * S.SR))
    tt = S.t_axis(0.25)
    plop = np.sin(2 * np.pi * np.cumsum(np.geomspace(900, 2100, len(tt))) / S.SR) * np.exp(-tt / 0.04)
    S.place(drip, plop, 0.02)
    sounds["additions4"] = S.normalise(S.reverb(drip, wet=0.5, size=0.8), -10)
    return sounds


# ================================================================ the other biomes: shared ambience pieces
def wind_loop(rng, bands, seconds=26, drone=(), drone_gain=0.06, pulse=None):
    """A seamless loop of breathing wind bands [(lo, hi, lfo_rate, gain)], an optional drone and an optional slow pulse."""
    n = int(seconds * S.SR)
    t = np.arange(n) / S.SR
    out = np.zeros(n)
    for lo, hi, rate, g in bands:
        lfo = 0.55 + 0.45 * np.sin(2 * np.pi * rate * t + rng.uniform(0, 6.28)) * np.sin(2 * np.pi * rate * 0.37 * t + 1)
        out += g * S.noise_band(n, lo, hi, rng, "brown" if lo < 200 else "white") * lfo
    out = S.normalise(out) * 0.9
    for k, f in enumerate(drone):
        out += drone_gain / (k + 1) * np.sin(2 * np.pi * f * t + rng.uniform(0, 6.28))
    if pulse:   # (rate Hz, depth): e.g. a slow heartbeat-like swell under red caves
        out *= 1 - pulse[1] * (0.5 + 0.5 * np.sin(2 * np.pi * pulse[0] * t)) ** 4
    return S.normalise(S.make_loop(out, cross=2.0), -8)


def far_choir(rng, chord, seconds=6.5, base=A3 / 2, vowels=("mm", "oo", "mm"), band=600, bend=(0, 0)):
    m = choir(rng, chord, seconds, base=base, vowels=vowels, attack=2.0, release=2.6, bend=bend)
    return S.normalise(S.reverb(S.normalise(S.bandpass(m, band, 0.6)), wet=0.6, size=1.6), -6)


def chimes(rng, base=A3 * 2, count=(2, 4), seconds=3.0, bright=0.8):
    a = np.zeros(int(seconds * S.SR))
    for k in range(rng.integers(*count)):
        S.place(a, (0.6 + 0.4 * rng.random()) * S.bell(note(base, SCALE[rng.integers(0, 7)]), 2.2, rng, bright=bright), k * rng.uniform(0.18, 0.4))
    return S.normalise(S.reverb(S.normalise(a), wet=0.45, size=1.2), -8)


def drips(rng, count=2, low=900, high=2100, wet=0.6, size=1.4):
    a = np.zeros(int(1.6 * S.SR))
    tt = S.t_axis(0.25)
    for k in range(count):
        f = rng.uniform(0.8, 1.2)
        plop = np.sin(2 * np.pi * np.cumsum(np.geomspace(low * f, high * f, len(tt))) / S.SR) * np.exp(-tt / 0.04)
        S.place(a, plop * rng.uniform(0.5, 1.0), 0.02 + k * rng.uniform(0.3, 0.6))
    return S.normalise(S.reverb(a, wet=wet, size=size), -10)


def pebbles(rng, count=6, seconds=1.4):
    a = np.zeros(int(seconds * S.SR))
    for k in range(count):
        n = int(0.03 * S.SR)
        click = S.bandpass(S.noise_band(n, 800, 6000, rng), rng.uniform(1500, 3500), 3) * np.exp(-np.arange(n) / (0.006 * S.SR))
        S.place(a, click * rng.uniform(0.3, 1.0), k * seconds / count * rng.uniform(0.6, 1.0))
    return S.normalise(S.reverb(a, wet=0.35, size=1.0), -11)


def bubbles(rng, count=5, seconds=1.6, low=180, high=500):
    a = np.zeros(int(seconds * S.SR))
    for k in range(count):
        tt = S.t_axis(rng.uniform(0.06, 0.14))
        f = rng.uniform(low, high)
        pop = np.sin(2 * np.pi * np.cumsum(np.linspace(f, f * 2.2, len(tt))) / S.SR) * np.exp(-tt / 0.03)
        S.place(a, pop * rng.uniform(0.4, 1.0), rng.uniform(0, seconds - 0.2))
    return S.normalise(S.reverb(a, wet=0.3, size=0.9), -10)


def crackle(rng, seconds=1.2, density=30):
    n = int(seconds * S.SR)
    a = np.zeros(n)
    for _ in range(int(seconds * density)):
        i = rng.integers(0, n - 120)
        a[i:i + 80] += rng.uniform(0.2, 1.0) * np.exp(-np.arange(80) / 10) * rng.choice([-1, 1])
    return S.normalise(S.reverb(S.lowpass(a, 6000) * S.adsr(n, 0.05, 0.3), wet=0.2, size=0.7), -12)


def thud(rng, seconds=1.8):
    n = int(seconds * S.SR)
    t = np.arange(n) / S.SR
    boom = np.sin(2 * np.pi * np.cumsum(np.geomspace(70, 35, n)) / S.SR) * np.exp(-t / 0.4)
    return S.normalise(S.reverb(boom + 0.3 * rumble(seconds, rng, 150), wet=0.6, size=1.6), -9)


def crimson_strata_canyon(rng):
    """赤紅沉積峽谷：乾燥遼闊。峽谷裡的風（帶一點口哨似的共鳴）、落石、遠處的水晶。"""
    s = {"loop": wind_loop(rng, ((90, 350, 0.05, 1.0), (500, 1300, 0.09, 0.5), (1700, 2300, 0.13, 0.25)), drone=(65.4, 98.0))}
    s["mood1"] = far_choir(rng, [0, 7, 12], band=500)
    s["mood2"] = far_choir(rng, [-5, 2, 7], band=500)
    s["additions1"], s["additions2"] = pebbles(rng), pebbles(rng, 9, 1.8)
    s["additions3"] = chimes(rng, base=A3, count=(1, 3))
    return s


def violet_slate_abyss(rng):
    """紫晶深板岩區：幽暗的深淵。極低的轟鳴、迴盪的滴水、深處的小調合唱。"""
    s = {"loop": wind_loop(rng, ((30, 120, 0.04, 1.0), (150, 400, 0.06, 0.35)), drone=(41.2, 61.7, 49.0), drone_gain=0.09)}
    s["mood1"] = far_choir(rng, [0, 3, 7], base=A3 / 4, band=350)
    s["mood2"] = far_choir(rng, [-2, 1, 5], base=A3 / 4, band=350)
    s["additions1"], s["additions2"] = drips(rng, 2, 700, 1500, 0.7, 1.8), drips(rng, 3, 600, 1300, 0.7, 1.8)
    s["additions3"] = chimes(rng, base=A3 / 2, count=(1, 2), bright=0.5)
    return s


def amber_dunes(rng):
    """琥珀沙丘：溫暖的沙。輕柔的沙沙風聲、溫暖的大調低鳴、沙子流下。"""
    s = {"loop": wind_loop(rng, ((150, 500, 0.06, 0.6), (2000, 6000, 0.1, 0.55), (700, 1500, 0.08, 0.3)), drone=(73.4, 110.0))}
    s["mood1"] = far_choir(rng, [0, 4, 7, 11], band=700)
    s["mood2"] = far_choir(rng, [-3, 0, 4, 9], band=700)
    sand = S.noise_band(int(1.6 * S.SR), 3000, 9000, rng) * S.adsr(int(1.6 * S.SR), 0.4, 0.8)
    s["additions1"] = S.normalise(S.reverb(sand, 0.2, 0.8), -13)
    s["additions2"] = chimes(rng, base=A3 * 2, count=(1, 3))
    return s


def red_zone_caves(rng):
    """紅區洞穴：低沉、壓迫。地底的轟鳴像心跳一樣起伏、遠處的悶響、滴水與碎裂聲。"""
    s = {"loop": wind_loop(rng, ((25, 110, 0.03, 1.0), (120, 300, 0.05, 0.3)), drone=(36.7, 38.9), drone_gain=0.1, pulse=(0.9, 0.35))}
    s["mood1"] = far_choir(rng, [0, 1, 6], base=A3 / 4, band=300, bend=(0, -2))
    s["mood2"] = S.normalise(thud(rng) + 0.0, -7)
    s["additions1"], s["additions2"] = drips(rng, 2, 500, 1100, 0.7, 1.6), crackle(rng)
    s["additions3"] = thud(rng, 1.4)
    return s


def lullaby_hills(rng):
    """搖籃曲山丘：溫柔。山谷的風、遠處歌者唱的搖籃曲、水晶叮噹。"""
    s = {"loop": wind_loop(rng, ((110, 400, 0.06, 1.0), (450, 1000, 0.09, 0.4)), drone=(55.0, 82.4))}
    for i, steps in enumerate(([4, 2, 0, 2, 4], [2, 4, 5, 4, 2]), 1):   # a far-off Singer humming the lullaby
        v = singer_phrase(rng, steps, base=A3, vowels=("mm", "oo"))
        v = S.bandpass(v, 700, 0.6)
        s[f"mood{i}"] = S.normalise(S.reverb(S.normalise(v), wet=0.65, size=1.8), -9)
    s["additions1"] = chimes(rng, base=A3 * 2, count=(2, 4))
    s["additions2"] = chimes(rng, base=A3 * 4, count=(1, 3), bright=0.6)
    return s


def soul_caldera(rng):
    """靈魂火山高原：噴的是靈魂不是岩漿。低沉的火山轟鳴、靈液冒泡、遠處的靈魂哀鳴、餘燼劈啪。"""
    s = {"loop": wind_loop(rng, ((25, 140, 0.04, 1.0), (180, 600, 0.07, 0.35)), drone=(43.7, 65.4), drone_gain=0.08, pulse=(0.25, 0.25))}
    s["mood1"] = far_choir(rng, [0, 5, 7], base=A3 / 2, band=450, bend=(2, -3), vowels=("oo", "oh", "mm"))
    s["mood2"] = far_choir(rng, [-3, 2, 4], base=A3 / 2, band=450, bend=(0, 3), vowels=("oo", "ah", "oo"))
    s["additions1"], s["additions2"] = bubbles(rng), bubbles(rng, 8, 2.0, 120, 380)
    s["additions3"] = crackle(rng, 1.4, 45)
    swoosh = S.noise_band(int(1.4 * S.SR), 300, 2500, rng) * S.adsr(int(1.4 * S.SR), 0.5, 0.8)   # a soul rushing up out of a vent
    swoosh = glide_shift(swoosh, -5, 7)
    s["additions4"] = S.normalise(S.reverb(swoosh, 0.5, 1.4), -11)
    return s


def whistle(rng, seconds=3.0, freq=(620, 520), gain=0.5):
    """Wind whistling through a crack: a narrow band of noise gliding in pitch, breathing in and out."""
    n = int(seconds * S.SR)
    x = S.noise_band(n, 200, 4000, rng)
    out = np.zeros(n)
    for k, f in enumerate(np.linspace(freq[0], freq[1], 3)):   # three slightly different resonances
        out += S.bandpass(x, f * (1 + 0.03 * k), 28) * (0.6 if k else 1.0)
    out = S.normalise(out) * S.adsr(n, attack=seconds * 0.35, release=seconds * 0.45, curve=1.6)
    return S.normalise(S.reverb(out, wet=0.5, size=1.3), -10) * gain / 0.5


def trickle(rng, seconds=2.4, lo=1400, hi=4200):
    """Liquid trickling over stone: band-passed noise fluttering fast, with a few small drops."""
    n = int(seconds * S.SR)
    t = np.arange(n) / S.SR
    flutter = 0.55 + 0.45 * np.sin(2 * np.pi * rng.uniform(7, 11) * t + rng.uniform(0, 6.28)) * np.sin(2 * np.pi * 2.3 * t + 1)
    x = S.noise_band(n, lo, hi, rng) * flutter * S.adsr(n, attack=0.5, release=0.9)
    return S.normalise(S.reverb(x, wet=0.35, size=1.0), -12)


def withered_hollows(rng):
    """枯竭窟：和靈液隔絕的淺層。乾燥、空洞：風從岩縫裡鑽過去的口哨聲、偶爾一滴乾脆的水、碎石滾落。幾乎沒有生命的聲音。"""
    s = {"loop": wind_loop(rng, ((90, 300, 0.05, 1.0), (500, 1400, 0.08, 0.14), (2400, 5200, 0.13, 0.02)), drone=(49.0,), drone_gain=0.03)}
    s["mood1"] = whistle(rng, 4.5, (610, 480), gain=0.62)
    s["mood2"] = whistle(rng, 5.5, (380, 430), gain=0.55)
    s["additions1"] = drips(rng, 1, 1100, 2300, 0.55, 2.0)      # one dry, lonely drip
    s["additions2"] = pebbles(rng, 5, 1.6)
    # a far, thin, hollowed-out wail: a Mourner weeping somewhere in the cracks (it sits at the edge of hearing)
    s["additions3"] = far_choir(rng, [0, 3], seconds=4.0, base=A3 / 2, band=520, bend=(1, -3), vowels=("oh", "oo"))
    return s


def resonant_vaults(rng):
    """共鳴穹窟：回音的大廳。極大的空間殘響、水晶共鳴的泛音、歌者在遠處合唱、滴水在大廳裡迴盪很久。"""
    n = int(28 * S.SR)
    t = np.arange(n) / S.SR
    hall = S.normalise(S.noise_band(n, 60, 500, rng, "brown")) * (0.55 + 0.45 * np.sin(2 * np.pi * 0.04 * t + 1))
    drone = sum(g * np.sin(2 * np.pi * f * t + rng.uniform(0, 6.28)) for f, g in
                ((55.0, 0.10), (82.5, 0.07), (110.2, 0.06), (165.0, 0.035), (220.4, 0.02)))   # a stack of slightly beating harmonics
    air = S.noise_band(n, 3000, 7000, rng) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.07 * t)) * 0.006   # faint shimmer
    s = {"loop": S.normalise(S.make_loop(0.5 * hall + drone + air, cross=2.5), -9)}
    s["mood1"] = far_choir(rng, [0, 4, 7, 11], seconds=7.5, base=A3 / 2, band=900, vowels=("oo", "ah", "oo"))   # the choir, clearer than anywhere else
    s["mood2"] = far_choir(rng, [-5, 0, 4, 9], seconds=7.5, base=A3 / 2, band=800, bend=(0, 2), vowels=("mm", "oo", "mm"))
    s["additions1"] = chimes(rng, base=A3 * 2, count=(2, 4), seconds=4.5, bright=1.0)
    s["additions2"] = drips(rng, 2, 900, 2100, 0.85, 2.6)       # a drip falling a long way, ringing for seconds
    s["additions3"] = S.normalise(S.reverb(fork(note(A3 * 2, SCALE[rng.integers(0, 7)]), 2.6, rng, beat=2.0), wet=0.7, size=2.2), -9)
    return s


def spirit_deeps(rng):
    """靈液深淵：靈液湧上來的地方。濕潤、低沉：深處液體流動的悶響與冒泡、緩慢像呼吸的起伏、遠處的靈魂低吟。"""
    s = {"loop": wind_loop(rng, ((30, 160, 0.04, 1.0), (180, 700, 0.07, 0.45), (900, 2400, 0.19, 0.08)),
                           drone=(41.2, 55.0, 61.7), drone_gain=0.09, pulse=(0.17, 0.3))}
    s["mood1"] = far_choir(rng, [0, 3, 7], seconds=7.0, base=A3 / 4, band=420, bend=(0, -2), vowels=("oo", "oh", "mm"))
    gurgle = np.zeros(int(4.0 * S.SR))
    for k in range(rng.integers(3, 6)):                          # slow gulps rising out of the deep
        S.place(gurgle, bubbles(rng, 2, 1.2, 70, 160) * rng.uniform(0.6, 1.0), k * rng.uniform(0.4, 0.9))
    s["mood2"] = S.normalise(S.reverb(S.lowpass(gurgle, 900), wet=0.5, size=1.8), -8)
    s["additions1"], s["additions2"] = bubbles(rng, 6, 2.0, 120, 380), trickle(rng)
    s["additions3"] = drips(rng, 2, 500, 1300, 0.7, 1.8)         # heavier drops falling into the liquid
    swoosh = S.noise_band(int(1.8 * S.SR), 200, 1800, rng) * S.adsr(int(1.8 * S.SR), 0.7, 1.0)   # a soul rising through the liquid
    s["additions4"] = S.normalise(S.reverb(glide_shift(swoosh, -7, 5), 0.55, 1.5), -11)
    return s


BIOME_RECIPES = {
    "crimson_strata_canyon": (crimson_strata_canyon, 41), "violet_slate_abyss": (violet_slate_abyss, 42),
    "amber_dunes": (amber_dunes, 43), "red_zone_caves": (red_zone_caves, 44),
    "lullaby_hills": (lullaby_hills, 45), "soul_caldera": (soul_caldera, 46),
    "withered_hollows": (withered_hollows, 47), "resonant_vaults": (resonant_vaults, 48), "spirit_deeps": (spirit_deeps, 49),
}


# sounds.json 事件（--install 時寫入）：event -> (資料夾, 檔名前綴, 字幕英文, 字幕中文, 額外屬性)
EVENTS = {
    "singer": [("entity.singer.ambient", "ambient", "Singer hums", "歌者哼唱", {}),
               ("entity.singer.hurt", "hurt", "Singer hurts", "歌者受傷", {}),
               ("entity.singer.death", "death", "Singer dies", "歌者死亡", {}),
               ("entity.singer.voice", "voice", "Singer sings", "歌者歌唱", {}),
               ("entity.singer.greet", "greet", "Singer greets", "歌者打招呼", {}),
               ("entity.singer.beckon", "beckon", "Singer beckons", "歌者呼喚", {}),
               ("entity.singer.call", "call", "Singer answers the horn", "歌者回應號角", {}),
               ("entity.singer.sweep", "sweep", "Singer sweeps the ground with song", "歌者以歌聲清掃", {}),
               ("entity.singer.summon", "summon", "Singer summons", "歌者召喚", {}),
               ("entity.singer.gasp", "gasp", "Singer gasps", "歌者倒抽一口氣", {}),
               ("entity.singer.cheer", "cheer", "Singer cheers", "歌者歡呼", {}),
               ("entity.singer.giggle", "giggle", "Singer giggles", "歌者咯咯笑", {}),
               ("entity.singer.thanks", "thanks", "Singer hums thanks", "歌者哼聲道謝", {}),
               ("entity.singer.unease", "unease", "Singer whimpers", "歌者發抖嗚咽", {}),
               ("entity.singer.starve", "starve", "Singer sighs weakly", "歌者虛弱地嘆息", {}),
               ("entity.singer.hollow", "hollow", "Singer hollows", "歌者屍化", {}),
               ("entity.singer.reborn", "reborn", "Singer is reborn", "歌者重生", {})],
    "mourner": [("entity.mourner.ambient", "ambient", "Mourner weeps", "哀悼者啜泣", {}),
                ("entity.mourner.hurt", "hurt", "Mourner hurts", "哀悼者受傷", {}),
                ("entity.mourner.death", "death", "Mourner dies", "哀悼者死亡", {}),
                ("entity.mourner.voice", "voice", "Mourner sings", "哀悼者哀唱", {}),
                ("entity.mourner.wail", "wail", "Mourner wails", "哀悼者哀號", {}),
                ("entity.mourner.soothe", "soothe", "Mourner sighs in relief", "哀悼者鬆了一口氣", {}),
                ("entity.mourner.hush", "hush", "Mourner falls quiet", "哀悼者漸漸安靜", {})],
}

# ================================================================ creatures made from free samples (sound_sources/)
def slices(x, count, rng, min_len=0.25, max_len=1.6, thresh=0.25, pre=0.02):
    """Cut `count` loud events out of a recording: from just before an onset until it decays (or max_len)."""
    n = int(S.SR * 0.05)
    env = np.convolve(np.abs(x), np.ones(n) / n, "same")
    top = env.max() + 1e-9
    onsets = np.flatnonzero((env[1:] > thresh * top) & (env[:-1] <= thresh * top))
    picked, last = [], -10 ** 9
    for o in onsets:
        if o - last < S.SR * min_len:
            continue
        start = max(0, o - int(pre * S.SR))
        end = start + int(S.SR * min_len)
        while end < min(len(x), start + int(S.SR * max_len)) and env[end] > 0.08 * top:
            end += int(S.SR * 0.01)
        picked.append(x[start:end])
        last = end
    if not picked:
        picked = [x[: int(S.SR * max_len)]]
    order = rng.permutation(len(picked))
    return [S.fade(picked[order[i % len(picked)]], 0.004, 0.08) for i in range(count)]


def glide_shift(x, start_semi, end_semi):
    """Pitch shift that slides from start to end semitones over the clip (variable-rate resampling)."""
    n = len(x)
    rates = 2 ** (np.linspace(start_semi, end_semi, n) / 12)
    pos = np.cumsum(rates)
    pos = pos[pos < n - 1]
    return np.interp(pos, np.arange(n), x)


def rumble(seconds, rng, hz=180):
    n = int(seconds * S.SR)
    return S.lowpass(S.noise_band(n, 30, hz, rng, "brown"), hz) * S.adsr(n, 0.1, 0.3)


def mix(*layers):
    n = max(len(l) for l, _ in layers)
    out = np.zeros(n)
    for layer, g in layers:
        out[: len(layer)] += g * layer / (np.max(np.abs(layer)) + 1e-9)
    return out


def finish(x, wet=0.2, size=0.8, peak=-3, lp=None):
    if lp:
        x = S.lowpass(x, lp)
    return S.normalise(S.reverb(S.normalise(x), wet=wet, size=size), peak)


def nuzzle(rng):
    """蹭蹭怪：溫和、會蹭人。貓的呼嚕與喵叫（Pixabay），音高往上、加一點晶亮的閃光。"""
    s = {}
    purr = load_samples("nuzzle", "ambient")
    purrs = [p for p in purr if len(p) > S.SR * 2] or purr
    meows = [p for p in purr if len(p) <= S.SR * 2] or purr
    for i, cut in enumerate(slices(purrs[0], 3, rng, min_len=0.9, max_len=1.8, thresh=0.15), 1):   # 平時：輕輕的呼嚕
        s[f"ambient{i}"] = finish(pitch_shift(cut, rng.uniform(2, 4)), wet=0.15, lp=5000, peak=-6)
    for i in (1, 2):   # 蹭人：呼嚕＋一聲撒嬌的「喵」，帶一點晶亮的閃光（給玩家回血與發光）
        p = pitch_shift(slices(purrs[0], 1, rng, 0.8, 1.4, 0.15)[0], 3)
        m = pitch_shift(meows[0], 4 + i)
        out = mix((p, 0.7))
        S.place(out, 0.8 * m / (np.max(np.abs(m)) + 1e-9), 0.35)
        S.place(out, 0.12 * S.bell(note(A3, 24 + 2 * i), 1.0, rng), 0.4)
        s[f"nuzzle{i}"] = finish(out, wet=0.25, peak=-4)
    for i in (1, 2):   # 被打：尖叫（喵叫拉高、加一點刺耳的氣音）
        m = pitch_shift(meows[0], 8 + 2 * i)[: int(0.45 * S.SR)]
        hiss = S.noise_band(len(m), 2500, 7000, rng) * S.adsr(len(m), 0.01, 0.2)
        s[f"hurt{i}"] = finish(mix((m, 1.0), (hiss, 0.25)), wet=0.1, peak=-3)
    s["death1"] = finish(glide_shift(meows[0], 4, -7), wet=0.35, size=1.0, peak=-3)   # 死亡：喵叫一路往下掉
    return s


def slabber(rng):
    """泥板獸：隙浮的牛，背上一塊土。牛叫（Pixabay）壓低、加一點泥土的悶響。"""
    s = {}
    moos = load_samples("slabber", "ambient")
    for i in range(1, 4):   # 平時：低沉的哞
        m = pitch_shift(moos[(i - 1) % len(moos)], -rng.uniform(3, 6))
        s[f"ambient{i}"] = finish(mix((m, 1.0), (rumble(len(m) / S.SR, rng), 0.12)), wet=0.15, lp=3000, peak=-4)
    for i in (1, 2):   # 受傷：短促的一聲
        m = pitch_shift(moos[(i - 1) % len(moos)][: int(0.45 * S.SR)], 1)
        s[f"hurt{i}"] = finish(m * S.adsr(len(m), 0.005, 0.15), wet=0.1, lp=4000, peak=-3)
    m = glide_shift(np.concatenate([moos[0], moos[-1]]), -3, -11)   # 死亡：拉長、一路往下沉
    s["death1"] = finish(mix((m, 1.0), (rumble(len(m) / S.SR, rng), 0.2)), wet=0.3, size=1.0, lp=2500, peak=-3)
    for i in (1, 2):   # 吃東西：滿足的小哞一聲＋咀嚼聲
        m = pitch_shift(moos[(i - 1) % len(moos)][: int(0.5 * S.SR)], -2)
        m = m * S.adsr(len(m), 0.05, 0.25)
        chew = np.zeros(int(0.9 * S.SR))
        for k in range(4):
            c = S.noise_band(int(0.07 * S.SR), 300, 2500, rng) * S.adsr(int(0.07 * S.SR), 0.005, 0.05)
            S.place(chew, c, 0.1 + k * 0.17)
        out = mix((chew, 0.6))
        S.place(out, 0.7 * m / (np.max(np.abs(m)) + 1e-9), 0.35)
        s[f"eat{i}"] = finish(out, wet=0.1, peak=-6)
    return s


def echo_golem(rng):
    """迴音傀儡：搬運靈魂的石像。石板敲擊與石臼研磨（Freesound 社群，經 Pixabay），加上低沉的水晶共鳴。"""
    s = {}
    src = load_samples("echo_golem", "ambient")
    clacks = next((x for x in src if len(x) > 20 * S.SR), src[0])      # marble boards: single stone knocks
    grind = next((x for x in src if len(x) <= 20 * S.SR), src[-1])     # mortar and pestle: grinding
    knocks = slices(clacks, 8, rng, min_len=0.12, max_len=0.5, thresh=0.3)

    def hum(seconds, root):
        f = np.full(int(seconds * S.SR), root)
        h = S.organ(f, ((1, 1.0), (2, 0.5), (3, 0.25), (5, 0.12))) * S.adsr(len(f), 0.4, 0.8, 1.5)
        for k, r in enumerate((4, 6)):
            S.place(h, 0.15 * S.bell(root * r, seconds, rng), 0.05 + 0.2 * k)
        return h

    for i in range(1, 4):   # 平時：低沉的水晶嗡鳴，偶爾石頭喀一聲
        out = mix((hum(2.2, note(A3 / 2, [0, 3, 7][i - 1])), 1.0))
        S.place(out, 0.5 * pitch_shift(knocks[i], -5) / (np.max(np.abs(knocks[i])) + 1e-9), 0.6)
        s[f"ambient{i}"] = finish(out, wet=0.35, size=1.2, peak=-6)
    for i in range(1, 5):   # 腳步：沉重的石頭落地
        k = pitch_shift(knocks[i + 3], -7)
        s[f"step{i}"] = finish(mix((k, 1.0), (rumble(0.25, rng, 120), 0.4)), wet=0.05, lp=3000, peak=-8)
    for i in (1, 2):   # 受傷：石頭裂開＋水晶叮一聲
        k = pitch_shift(knocks[i], -2)
        crack = S.noise_band(int(0.25 * S.SR), 1500, 6000, rng) * S.adsr(int(0.25 * S.SR), 0.002, 0.2)
        out = mix((k, 1.0), (crack, 0.35))
        S.place(out, 0.3 * S.bell(note(A3, 19 + i), 0.8, rng), 0.0)
        s[f"hurt{i}"] = finish(out, wet=0.2, peak=-3)
    g = slices(grind, 1, rng, min_len=1.2, max_len=2.0, thresh=0.15)[0]   # 死亡：碎裂、研磨、晶體散落
    out = mix((pitch_shift(g, -5), 0.8))
    for k in range(5):
        S.place(out, 0.5 * pitch_shift(knocks[k], -3 - k), 0.1 + k * 0.18)
    for k in range(6):
        S.place(out, 0.18 * S.bell(note(A3, 14 + rng.integers(0, 12)), 1.2, rng, bright=2.0), 0.6 + k * 0.07)
    s["death1"] = finish(out, wet=0.35, size=1.1, peak=-3)
    for i in (1, 2):   # 工作：挖地、放下唱片盒（石頭研磨一下）
        g = slices(grind, 1, rng, min_len=0.4, max_len=0.7, thresh=0.2)[0]
        s[f"work{i}"] = finish(mix((pitch_shift(g, -3 - 2 * i), 1.0), (rumble(0.5, rng), 0.3)), wet=0.1, lp=4000, peak=-5)
    for i in (1, 2):   # 送東西（吐出靈魂土、送晶塊、立約）：往上的水晶嗡鳴
        h = hum(1.4, note(A3 / 2, 5 + 2 * i))
        S.place(h, 0.4 * S.bell(note(A3, 12 + 5 * i), 1.2, rng), 0.5)
        s[f"gift{i}"] = finish(h, wet=0.4, size=1.2, peak=-4)
    return s


# ================================================================ fully synthesised creatures
def fork(freq, seconds, rng, beat=0.0, bright=0.4):
    """A struck tuning fork: almost pure sine, a faint octave, long decay; beat = Hz of detuned beating."""
    t = S.t_axis(seconds)
    env = np.exp(-t / (seconds * 0.35)) * np.clip(t / 0.004, 0, 1)
    x = np.sin(2 * np.pi * freq * t) + bright * 0.15 * np.sin(2 * np.pi * freq * 2.0 * t) * np.exp(-t / 0.15)
    if beat:
        x += 0.8 * np.sin(2 * np.pi * (freq + beat) * t + rng.uniform(0, 6.28))
    clank = S.noise_band(int(0.02 * S.SR), 2000, 8000, rng) * 0.3
    S.place(x, clank, 0.0)
    return x * env


def tuner(rng):
    """調音器：只會替別的怪物加持。音叉、拍頻、調頻和弦。"""
    s = {}
    for i, root in enumerate((note(A3, 12), note(A3, 7), note(A3, 16)), 1):   # 平時：輕輕敲一下音叉，帶一點拍頻
        s[f"ambient{i}"] = finish(fork(root, 2.4, rng, beat=rng.uniform(1.5, 3.0)), wet=0.35, size=1.1, peak=-7)
    for i in (1, 2):   # 加持：音叉由下往上一個一個敲響，最後合成一個和弦撐住
        out = np.zeros(int(2.6 * S.SR))
        for k, st in enumerate([0, 4, 7, 12] if i == 1 else [0, 5, 9, 14]):
            S.place(out, fork(note(A3, st + 7), 2.0, rng, bright=0.8), k * 0.12)
        swell = S.organ(np.full(int(1.8 * S.SR), note(A3, 7))) * S.adsr(int(1.8 * S.SR), 0.6, 0.8, 1.5)
        S.place(out, 0.4 * swell / np.max(np.abs(swell)) * np.max(np.abs(out)), 0.4)
        s[f"aura{i}"] = finish(out, wet=0.45, size=1.3, peak=-4)
    for i in (1, 2):   # 受傷：兩支走音的音叉一起被敲到（刺耳的拍頻）
        out = fork(note(A3, 12 + i), 0.7, rng, beat=23 + 7 * i, bright=1.0)
        s[f"hurt{i}"] = finish(out, wet=0.15, peak=-3)
    x = fork(note(A3, 12), 2.5, rng, beat=4.0, bright=1.0)   # 死亡：音叉越來越走音、往下彎
    s["death1"] = finish(glide_shift(x, 0, -9), wet=0.4, size=1.2, peak=-3)
    return s


def wings(seconds, rng, beat=42.0, buzz=170.0, bend=(0.0, 0.0)):
    """Insect wings: a buzzy saw tone amplitude-modulated at the wingbeat, band-passed."""
    n = int(seconds * S.SR)
    t = np.arange(n) / S.SR
    f = buzz * 2 ** (np.linspace(bend[0], bend[1], n) / 12) * (1 + 0.03 * np.sin(2 * np.pi * 0.7 * t + rng.uniform(0, 6)))
    saw = S.glottal(f, rolloff=0.8, max_hz=6000)
    am = 0.55 + 0.45 * np.sin(2 * np.pi * beat * t)
    x = S.bandpass(saw * am, 900, 0.7) + 0.4 * S.bandpass(saw * am, 2600, 1.5)
    return x * S.adsr(n, 0.08, 0.2)


def fuse(seconds, rng):
    """A burning fuse: crackling hiss rising in pitch."""
    n = int(seconds * S.SR)
    hiss = S.noise_band(n, 2500, 9000, rng) * np.linspace(0.5, 1.0, n)
    crack = np.zeros(n)
    for _ in range(int(seconds * 40)):
        i = rng.integers(0, n - 200)
        crack[i:i + 60] += rng.uniform(0.3, 1.0) * np.exp(-np.arange(60) / 12) * rng.choice([-1, 1])
    tone = np.sin(2 * np.pi * np.cumsum(np.geomspace(500, 1600, n)) / S.SR) * 0.25
    return (hiss * 0.6 + crack + tone) * S.adsr(n, 0.02, 0.05)


def fusefly(rng):
    """引信蠅：會飛、死後爆炸。翅膀嗡鳴、燃燒的引信。"""
    s = {}
    for i in (1, 2):   # 平時：一陣翅膀嗡嗡聲
        s[f"ambient{i}"] = finish(wings(1.3, rng, beat=rng.uniform(38, 48), buzz=rng.uniform(150, 190), bend=(0, rng.uniform(-1, 2))), wet=0.1, peak=-7)
    for i in (1, 2):   # 受傷：嗡聲猛地拉高、亂抖，冒出火花聲
        w = wings(0.5, rng, beat=60, buzz=240, bend=(0, 5))
        S.place(w, 0.5 * fuse(0.3, rng), 0.05)
        s[f"hurt{i}"] = finish(w, wet=0.1, peak=-3)
    s["death1"] = finish(wings(0.35, rng, beat=70, buzz=280, bend=(4, -3)), wet=0.1, peak=-4)   # 死掉的一瞬間：尖細的一聲
    s["fuse1"] = finish(fuse(0.95, rng), wet=0.1, peak=-3)   # 點燃引信（死亡後 0.9 秒爆炸）
    return s


def choir(rng, chord, seconds, base=A3, vowels=("ah", "eh"), attack=0.3, release=0.8, bend=(0.0, 0.0), detune=0.0):
    """Several Singer voices on a chord (semitones from base); bend = gliding the whole chord."""
    n = int(seconds * S.SR)
    out = np.zeros(n)
    for k, st in enumerate(chord):
        f0 = note(base, st + detune * rng.uniform(-1, 1)) * 2 ** (np.linspace(bend[0], bend[1], n) / 12)
        f0 = S.vibrato(f0, rate=4.5 + 0.4 * k, depth=0.006, rng=rng, delay=0.1)
        v = soft_voice(f0, rng, vowels)
        out += v[:n] / (np.max(np.abs(v)) + 1e-9)
    return out * S.adsr(n, attack, release, 1.5)


def harmonizer(rng):
    """調和者（柳絮林地的 Boss）：一整團歌者的聲音擠在一起。和聲、不和諧音與聲波。"""
    s = {}
    for i, ch in enumerate(([-12, -5, 0, 4], [-12, -7, -2, 3], [-10, -3, 2, 5]), 1):   # 平時：低沉的合唱和弦慢慢浮起
        s[f"ambient{i}"] = finish(choir(rng, ch, 3.2, vowels=("mm", "oo", "mm"), attack=1.0, release=1.4), wet=0.5, size=1.6, peak=-5)
    for i in (1, 2):   # 受傷：不和諧的一記合唱
        s[f"hurt{i}"] = finish(choir(rng, [0, 1, 6, 11] if i == 1 else [-1, 0, 5, 10], 0.6, attack=0.01, release=0.35), wet=0.3, peak=-3)
    out = choir(rng, [-12, -5, 0, 4, 7], 3.5, attack=0.05, release=2.0, bend=(0, -14), detune=0.8)   # 死亡：整團和聲崩塌往下
    s["death1"] = finish(out, wet=0.55, size=1.8, peak=-2)
    s["roar1"] = finish(choir(rng, [-12, 0, 7, 12, 16], 2.4, attack=0.08, release=0.9, bend=(-3, 0)), wet=0.5, size=1.6, peak=-1)   # 召喚援軍：整團吶喊
    s["cone1"] = finish(choir(rng, [0, 7, 12], 0.9, vowels=("eh", "ah"), attack=0.02, release=0.5), wet=0.35, peak=-2)              # 音波錐：尖銳的一聲「欸！」
    ring = choir(rng, [0, 0.4, 7, 7.3], 2.4, vowels=("oo", "ah"), attack=0.6, release=0.7)                                           # 共鳴環：拍頻越來越強的和弦
    s["resonance1"] = finish(ring * (0.7 + 0.3 * np.sin(2 * np.pi * np.linspace(2, 9, len(ring)) * np.arange(len(ring)) / S.SR)), wet=0.5, size=1.5, peak=-2)
    s["vortex1"] = finish(choir(rng, [0, 4, 7], 3.0, vowels=("oo", "ah", "oo"), attack=0.4, release=0.8, bend=(-7, 12)), wet=0.55, size=1.7, peak=-2)   # 漩渦：往上捲的滑音
    s["slam1"] = finish(mix((choir(rng, [-17, -12], 0.7, vowels=("oh",), attack=0.01, release=0.4), 1.0), (rumble(0.7, rng, 120), 0.8)), wet=0.3, peak=-2)  # 砸地：低吼
    s["grab1"] = finish(choir(rng, [-14, -13, -8], 1.2, vowels=("oo", "mm"), attack=0.05, release=0.6, bend=(2, -3)), wet=0.35, peak=-3)   # 觸手抓人：黏稠的低吟
    return s


RECIPES = {   # name -> (recipe, asset folder, seed)
    "tuner": (tuner, "mob/tuner", 31),
    "fusefly": (fusefly, "mob/fusefly", 32),
    "harmonizer": (harmonizer, "mob/harmonizer", 33),
    "singer": (singer, "mob/singer", 11),
    "mourner": (mourner, "mob/mourner", 12),
    "willow_grove": (willow_grove, "ambient/willow_grove", 13),
    "nuzzle": (nuzzle, "mob/nuzzle", 21),
    "slabber": (slabber, "mob/slabber", 22),
    "echo_golem": (echo_golem, "mob/echo_golem", 23),
}
RECIPES.update({b: (r, f"ambient/{b}", seed) for b, (r, seed) in BIOME_RECIPES.items()})

EVENTS.update({
    "tuner": [("entity.tuner.ambient", "ambient", "Tuner rings", "調音器鳴響", {}),
              ("entity.tuner.aura", "aura", "Tuner empowers monsters", "調音器替怪物加持", {}),
              ("entity.tuner.hurt", "hurt", "Tuner clangs", "調音器走音", {}),
              ("entity.tuner.death", "death", "Tuner dies", "調音器死亡", {})],
    "fusefly": [("entity.fusefly.ambient", "ambient", "Fusefly buzzes", "引信蠅嗡嗡作響", {}),
                ("entity.fusefly.hurt", "hurt", "Fusefly hurts", "引信蠅受傷", {}),
                ("entity.fusefly.death", "death", "Fusefly dies", "引信蠅死亡", {}),
                ("entity.fusefly.fuse", "fuse", "Fusefly's fuse burns", "引信蠅的引信燃燒", {})],
    "harmonizer": [("entity.harmonizer.ambient", "ambient", "Harmonizer hums", "調和者低吟", {}),
                   ("entity.harmonizer.hurt", "hurt", "Harmonizer hurts", "調和者受傷", {}),
                   ("entity.harmonizer.death", "death", "Harmonizer dies", "調和者死亡", {}),
                   ("entity.harmonizer.roar", "roar", "Harmonizer roars", "調和者吶喊", {}),
                   ("entity.harmonizer.cone", "cone", "Harmonizer shrieks", "調和者尖鳴", {}),
                   ("entity.harmonizer.resonance", "resonance", "Harmonizer resonates", "調和者共鳴", {}),
                   ("entity.harmonizer.vortex", "vortex", "Harmonizer swirls", "調和者漩渦", {}),
                   ("entity.harmonizer.slam", "slam", "Harmonizer slams", "調和者重擊", {}),
                   ("entity.harmonizer.grab", "grab", "Harmonizer grabs", "調和者抓取", {})],
    "nuzzle": [("entity.nuzzle.ambient", "ambient", "Nuzzle purrs", "蹭蹭怪呼嚕", {}),
               ("entity.nuzzle.nuzzle", "nuzzle", "Nuzzle nuzzles you", "蹭蹭怪蹭了蹭你", {}),
               ("entity.nuzzle.hurt", "hurt", "Nuzzle shrieks", "蹭蹭怪尖叫", {}),
               ("entity.nuzzle.death", "death", "Nuzzle dies", "蹭蹭怪死亡", {})],
    "slabber": [("entity.slabber.ambient", "ambient", "Slabber lows", "泥板獸低鳴", {}),
                ("entity.slabber.hurt", "hurt", "Slabber hurts", "泥板獸受傷", {}),
                ("entity.slabber.death", "death", "Slabber dies", "泥板獸死亡", {}),
                ("entity.slabber.eat", "eat", "Slabber eats", "泥板獸進食", {})],
    "echo_golem": [("entity.echo_golem.ambient", "ambient", "Echo Golem hums", "迴音傀儡嗡鳴", {}),
                   ("entity.echo_golem.step", "step", "Echo Golem steps", "迴音傀儡腳步聲", {}),
                   ("entity.echo_golem.hurt", "hurt", "Echo Golem cracks", "迴音傀儡碎裂", {}),
                   ("entity.echo_golem.death", "death", "Echo Golem crumbles", "迴音傀儡崩塌", {}),
                   ("entity.echo_golem.work", "work", "Echo Golem works", "迴音傀儡工作", {}),
                   ("entity.echo_golem.gift", "gift", "Echo Golem chimes", "迴音傀儡鳴響", {})],
})

import creatures as C  # noqa: E402  remaining creatures, made from Pixabay recordings (tools/audio/creatures.py)
C.B = sys.modules[__name__]
RECIPES.update(C.RECIPES)
import music as MU  # noqa: E402  boss-fight music (tools/audio/music.py)
MU.B = sys.modules[__name__]
RECIPES.update(MU.RECIPES)
import layer_music as LM  # noqa: E402  music of the underground layers (tools/audio/layer_music.py)
LM.B = sys.modules[__name__]
RECIPES.update(LM.RECIPES)
RECIPES.update(LM.SYNTH_RECIPES)
EVENTS.update(MU.EVENTS)
import machines as MA  # noqa: E402  soul power machines (tools/audio/machines.py)
MA.B = sys.modules[__name__]
RECIPES.update(MA.RECIPES)
EVENTS.update(MA.EVENTS)


def main():
    names = ONLY.split(",") if ONLY else list(RECIPES)
    for name in names:
        recipe, folder, seed = RECIPES[name]
        sounds = recipe(np.random.default_rng(seed))
        gap = np.zeros(int(0.7 * S.SR))
        reel = []
        for key, x in sounds.items():
            if x.ndim == 1 and not key.startswith("loop"):   # stereo music is faded by music.py
                x = S.fade(x, 0.003, 0.03)
            S.write_ogg(PREVIEW / name / f"{key}.ogg", x)
            if INSTALL:
                S.write_ogg(ASSETS / folder / f"{key}.ogg", x)
            if x.ndim == 2:   # music: preview the first 30 s in mono
                x = x.mean(axis=1)[: int(30 * S.SR)]
            reel += [x if not key.startswith("loop") else np.tile(x, 1)[: int(12 * S.SR)], gap]
        S.write_wav(PREVIEW / f"{name}_preview.wav", np.concatenate(reel))
        lengths = ", ".join(f"{k} {len(v) / S.SR:.1f}s" for k, v in sounds.items())
        print(f"{name}: {lengths}")
        events = EVENTS.get(name) or (C.events(name, sounds) if name in C.RECIPES else None)
        if INSTALL and events:
            register(events, folder, sounds)


def register(events, folder, sounds):
    """Write this recipe's events into sounds.json and their subtitles into the lang files."""
    import json
    path = P / "src/main/resources/assets/pysift/sounds.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    langs = {code: P / f"src/main/resources/assets/pysift/lang/{code}.json" for code in ("en_us", "zh_tw")}
    lang = {code: json.loads(p.read_text(encoding="utf-8")) for code, p in langs.items()}
    for event, prefix, en, zh, extra in events:
        files = [k for k in sounds if k.rstrip("0123456789") == prefix]
        sub = f"subtitles.pysift.{event}"
        entry = [{"name": f"pysift:{folder}/{k}", **extra} for k in files]
        if en is None:   # music: no subtitle
            data[event] = {"sounds": entry}
            continue
        data[event] = {"subtitle": sub, "sounds": entry}
        lang["en_us"][sub] = en
        lang["zh_tw"][sub] = zh
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for code, p in langs.items():
        p.write_text(json.dumps(lang[code], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
