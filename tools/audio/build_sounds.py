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

P = Path(sys.argv[1]).resolve()
ARGS = sys.argv[2:]
ONLY = next((a.split("=", 1)[1] if "=" in a else ARGS[ARGS.index(a) + 1] for a in ARGS if a.startswith("--only")), None)
INSTALL = "--install" in ARGS
PREVIEW = P / "build/audio_preview"
ASSETS = P / "src/main/resources/assets/pysift/sounds"
SOURCES = P / "sound_sources"

A3 = 220.0
# 唱歌用的單音：遊戲裡用音符盒的音高倍率（0.5~2.0，1.0 = 第 12 個半音）播放，所以錄在 F#4，唱出來是 F#3~F#5
VOICE_BASE = 369.99
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


# ================================================================ Singer: sung vowels and crystal overtones
# 參考（Dungeons 2 歌者，只量特徵、不取用聲音）：音高很穩、幾乎沒有顫音、換音不滑音，音色圓潤偏暗（泛音少），
# 常常好幾個聲部一起唱、起音柔和、殘響長。所以歌者的聲音是：暗的「嗚／嗯」母音、3 人齊唱、極淺的顫音、一點和聲。
# 使用者指定（參考影片 0:00~0:20）：用「吶喊」的方式唱，帶一點風琴感；不要和聲。
# 吶喊 = 張口的「啊／欸」、泛音亮、帶氣聲；風琴 = 一層音高完全不動的管風琴泛音疊在底下，起音像慢慢灌氣。
def soft_voice(f0, rng, vowels=("ah", "eh")):
    def render(f):
        shout = S.voice(f, vowels, breath=0.09, rng=rng, rolloff=0.95)
        return S.lowpass(shout, 7000)
    v = S.chorus(render, f0, voices=3, detune_cents=6.0, spread=0.01, rng=rng)
    v /= np.max(np.abs(v)) + 1e-9
    pipe = S.organ(np.convolve(f0, np.ones(400) / 400, "same"))   # organ ignores the voice's tiny wobble
    pipe /= np.max(np.abs(pipe)) + 1e-9
    S.place(v, 0.38 * pipe, 0.0)
    return v[: len(f0)]   # same length as the pitch curve, so envelopes line up


def singer_phrase(rng, steps, base=A3, vowels=("ah", "eh"), harmony=0):
    notes = [(note(base, SCALE[s]), rng.uniform(0.42, 0.7)) for s in steps]
    notes[-1] = (notes[-1][0], notes[-1][1] + 0.5)
    f0 = S.vibrato(S.glide_curve(notes, rng, glide=0.025), rate=4.8, depth=0.003, rng=rng, delay=0.3)
    v = soft_voice(f0, rng, vowels)
    if harmony:   # a quieter second part a fourth/fifth below
        v2 = soft_voice(f0 * 2 ** (harmony / 12), rng, ("mm", "oo"))
        S.place(v, 0.45 * v2[: len(v)], 0.0)
    v = v * S.adsr(len(v), attack=0.2, release=0.6, curve=1.5)
    t = 0.0   # crystal overtones: a soft bell on each note, two octaves up
    for f, d in notes:
        S.place(v, 0.02 * S.bell(f * 4, 1.4, rng) * np.max(np.abs(v)), t)
        t += d
    return S.reverb(S.normalise(v), wet=0.42, size=1.3)


def singer(rng):
    sounds = {}
    phrases = [[0, 2, 4], [4, 3, 1], [2, 4, 5, 4], [5, 4, 2, 0]]
    for i, steps in enumerate(phrases, 1):
        sounds[f"ambient{i}"] = S.normalise(singer_phrase(rng, steps), -4)
    for i in (1, 2):   # hurt: a short startled rise and fall
        f0 = S.glide_curve([(note(A3, 4 + i), 0.08), (note(A3, 11 + i), 0.12), (note(A3, 2), 0.18)], rng, glide=0.05)
        v = soft_voice(S.vibrato(f0, rate=9, depth=0.02, rng=rng, delay=0), rng, ("ah", "oh"))
        v = v * S.adsr(len(v), attack=0.01, release=0.15)
        S.place(v, 0.15 * S.bell(note(A3, 24 + i), 0.5, rng), 0.0)
        sounds[f"hurt{i}"] = S.normalise(S.reverb(S.normalise(v), wet=0.2, size=0.7), -3)
    # death: a long fall from the top of the scale, the vibrato widening, then the crystal shatters
    f0 = np.geomspace(note(A3, 12), note(A3, -12), int(1.9 * S.SR))
    f0 = S.vibrato(f0, rate=6.5, depth=0.03, rng=rng, delay=0.3)
    v = soft_voice(f0, rng, ("ah", "oh", "oo", "mm")) * S.adsr(len(f0), 0.04, 0.9)
    for k in range(7):
        S.place(v, 0.12 * S.bell(note(A3, 19 + rng.integers(0, 12)), 1.4, rng, bright=2.0), 1.1 + k * 0.05)
    sounds["death1"] = S.normalise(S.reverb(S.normalise(v), wet=0.4, size=1.2), -3)
    # 唱歌用的單音：和平常哼唱同一種圓潤的齊唱音色，音高很穩
    f0 = S.vibrato(np.full(int(1.1 * S.SR), VOICE_BASE), rate=4.8, depth=0.003, rng=rng, delay=0.3)
    v = soft_voice(f0, rng, ("ah", "eh"))
    v = v * S.adsr(len(v), attack=0.07, release=0.6, curve=1.5)
    S.place(v, 0.02 * S.bell(VOICE_BASE * 4, 1.0, rng) * np.max(np.abs(v)), 0.0)
    sounds["voice"] = S.normalise(S.reverb(S.normalise(v), wet=0.35, size=1.1), -2)
    sounds.update(singer_actions(rng))
    return sounds


def call(rng, notes, base=A3, vowels=("ah", "eh"), legato=True, attack=0.05, release=0.35, vib=0.003, vib_rate=4.8,
         breath_burst=0.0, wet=0.38, size=1.1, peak=-3, tremble=0.0):
    """A short vocal gesture. notes = [(semitones from base, seconds)]; legato = one breath, else separate syllables."""
    if legato:
        f0 = S.glide_curve([(note(base, s), d) for s, d in notes], rng, glide=0.03)
        f0 = S.vibrato(f0, rate=vib_rate, depth=vib, rng=rng, delay=0.1, jitter=tremble)
        v = soft_voice(f0, rng, vowels) * S.adsr(len(f0), attack, release, curve=1.5)
    else:
        total = sum(d for _, d in notes) + 0.5
        v = np.zeros(int(total * S.SR))
        t = 0.0
        for s, d in notes:
            f0 = S.vibrato(np.full(int(d * 0.8 * S.SR), note(base, s)), rate=vib_rate, depth=vib, rng=rng, delay=0.05, jitter=tremble)
            syl = soft_voice(f0, rng, vowels) * S.adsr(len(f0), min(attack, 0.02), min(release, d * 0.4), curve=1.5)
            S.place(v, syl / (np.max(np.abs(syl)) + 1e-9), t)
            t += d
    if breath_burst:   # a sharp intake of breath before the voice (gasp)
        n = int(0.18 * S.SR)
        b = S.noise_band(n, 1200, 6000, rng) * S.adsr(n, 0.02, 0.12) * breath_burst
        v = np.concatenate([b, np.zeros(int(0.03 * S.SR)), v / (np.max(np.abs(v)) + 1e-9)])
    return S.normalise(S.reverb(S.normalise(v), wet=wet, size=size), peak)


def singer_actions(rng):
    """歌者對世界與玩家的每個互動各有一段人聲（SingerEntity / SiftPortalRitual 裡播放）。"""
    s = {}
    s["greet1"] = call(rng, [(4, 0.22), (9, 0.5)])                                   # 從地底爬出、抖掉泥土：「啊—欸！」往上
    s["greet2"] = call(rng, [(2, 0.2), (7, 0.18), (12, 0.45)])
    s["beckon1"] = call(rng, [(7, 0.3), (4, 0.45)], release=0.3)                     # 招手等迴音碎片：「嘿～」兩個音往下
    s["beckon2"] = call(rng, [(9, 0.28), (7, 0.2), (4, 0.4)], release=0.3)
    s["call1"] = call(rng, [(0, 0.35), (4, 0.3), (7, 0.3), (12, 0.9)], wet=0.5, size=1.4)   # 回應山羊角：長長的呼喊
    s["call2"] = call(rng, [(-5, 0.35), (2, 0.3), (7, 0.35), (9, 0.9)], wet=0.5, size=1.4)
    f0_sweep = [(0, 0.15), (5, 0.15), (9, 0.15), (12, 0.2), (9, 0.15), (5, 0.15), (2, 0.35)]
    s["sweep1"] = call(rng, f0_sweep, vowels=("oo", "ah", "oo"), wet=0.45)            # 揮手打掃：上去又下來的長音
    s["summon1"] = call(rng, [(0, 0.4), (7, 0.4), (12, 0.4), (16, 1.3)], vib=0.006, wet=0.55, size=1.6, peak=-2)   # 召喚傀儡：最用力的吶喊
    s["gasp1"] = call(rng, [(9, 0.12), (5, 0.18), (0, 0.45)], vowels=("oh", "oo"), breath_burst=0.6, tremble=2.0)  # 儀式走調：倒抽一口氣
    s["cheer1"] = call(rng, [(0, 0.12), (4, 0.12), (7, 0.12), (12, 0.12), (16, 0.6)], legato=False, release=0.2)  # 開門慶祝
    s["cheer2"] = call(rng, [(7, 0.12), (12, 0.12), (7, 0.12), (12, 0.12), (19, 0.6)], legato=False, release=0.2)
    s["giggle1"] = call(rng, [(12, 0.09), (14, 0.09), (12, 0.09), (16, 0.09), (12, 0.09), (19, 0.25)],   # 抱小傀儡玩：咯咯笑
                        legato=False, vowels=("eh", "ah"), release=0.05, wet=0.3)
    s["giggle2"] = call(rng, [(16, 0.08), (14, 0.08), (12, 0.08), (14, 0.08), (16, 0.08), (21, 0.3)],
                        legato=False, vowels=("eh", "ah"), release=0.05, wet=0.3)
    s["thanks1"] = call(rng, [(0, 0.25), (5, 0.6)], vowels=("mm", "ah"), wet=0.45)     # 收到靈魂晶塊：溫暖的「嗯—啊」
    s["unease1"] = call(rng, [(2, 0.5), (1, 0.6)], base=A3 / 2, vowels=("oo", "mm"), vib=0.02, vib_rate=9, tremble=4.0, peak=-6)  # 看見監守者：發抖嗚咽
    s["starve1"] = call(rng, [(0, 0.6), (-2, 0.8)], base=A3 / 2, vowels=("oh", "mm"), vib=0.015, tremble=3.0, wet=0.5, peak=-8)   # 快要屍化：虛弱的嘆息
    f0 = S.vibrato(np.geomspace(note(A3, 7), note(A3, -10), int(2.4 * S.SR)), rate=7, depth=0.03, rng=rng, delay=0.2, jitter=4.0)
    v = soft_voice(f0, rng, ("ah", "oh", "oo", "mm")) * S.adsr(len(f0), 0.05, 1.2)   # 屍化成哀悼者：長長的哭喊，聲音越來越空
    v = v * np.linspace(1.0, 0.35, len(v)) + 0.25 * S.noise_band(len(v), 300, 2500, rng) * np.linspace(0, 1, len(v))
    s["hollow1"] = S.normalise(S.reverb(S.normalise(v), wet=0.55, size=1.5), -3)
    # 哀悼者被治好、長回毛：從低低的哭腔一路往上，變成明亮的歡呼
    s["reborn1"] = call(rng, [(-5, 0.35), (0, 0.3), (4, 0.3), (7, 0.3), (12, 1.0)], vib=0.004, wet=0.5, size=1.4, peak=-2)
    return s


def sung_note(rng, vowels, breath, vib, shift, chime, sob=False, seconds=1.0):
    """One sustained sung note at VOICE_BASE: the ritual songs play it at note-block pitches."""
    f0 = S.vibrato(np.full(int(seconds * S.SR), VOICE_BASE), rate=vib[0], depth=vib[1], rng=rng, delay=0.12,
                   jitter=3.0 if sob else 0.0)
    v = S.voice(f0, vowels, breath=breath, rng=rng, shift=shift)
    if sob:
        v *= 1 - 0.35 * (0.5 + 0.5 * np.sin(2 * np.pi * 2.6 * np.arange(len(v)) / S.SR)) ** 3
    v = v * S.adsr(len(v), attack=0.04, release=0.55)
    if chime:
        S.place(v, chime * S.bell(VOICE_BASE * 4, 1.0, rng) * np.max(np.abs(v)) * 8, 0.0)
    return S.normalise(S.reverb(S.normalise(v), wet=0.25, size=0.8), -2)


# ================================================================ Mourner: the Singer's voice, starved and weeping
# 同一副嗓子（吶喊＋風琴），只是餓壞了：低四度、氣聲多、音一直在抖、跟著抽泣斷斷續續，風琴層也走音。
M_BASE = A3 / 2 ** (5 / 12)


def sob(n, rng, rate=None, depth=0.5):
    rate = rate or rng.uniform(2.2, 3.2)
    return 1 - depth * (0.5 + 0.5 * np.sin(2 * np.pi * rate * np.arange(n) / S.SR)) ** 3


def mourner_voice(f0, rng, vowels=("oh", "oo")):
    def render(f):
        return S.lowpass(S.voice(f, vowels, breath=0.2, rng=rng, rolloff=1.1, shift=0.92), 5500)
    v = S.chorus(render, f0, voices=3, detune_cents=14.0, spread=0.014, rng=rng)
    v /= np.max(np.abs(v)) + 1e-9
    pipe = S.organ(np.convolve(f0, np.ones(400) / 400, "same") * 2 ** (-0.35 / 12))   # the organ has gone flat
    pipe /= np.max(np.abs(pipe)) + 1e-9
    S.place(v, 0.25 * pipe, 0.0)
    return v[: len(f0)]


def m_call(rng, notes, vowels=("oh", "oo"), attack=0.15, release=0.6, vib=0.025, sobbing=0.5, wet=0.5, size=1.4, peak=-4,
           base=M_BASE):
    f0 = S.glide_curve([(note(base, st) * 2 ** (-rng.uniform(0, 0.4) / 12), d) for st, d in notes], rng, glide=0.15)
    f0 = S.vibrato(f0, rate=7.0, depth=vib, rng=rng, delay=0.05, jitter=3.5)
    v = mourner_voice(f0, rng, vowels) * S.adsr(len(f0), attack, release, curve=1.5)
    if sobbing:
        v *= sob(len(v), rng, depth=sobbing)
    return S.normalise(S.reverb(S.normalise(v), wet=wet, size=size), peak)


def mourner(rng):
    sounds = {}
    samples = load_samples("mourner", "ambient")
    phrases = [[(9, 0.7), (7, 0.6), (4, 0.9)], [(7, 0.6), (4, 0.5), (2, 0.5), (0, 0.9)], [(12, 0.6), (9, 0.6), (5, 0.9)], [(4, 0.6), (2, 0.6), (0, 1.0)]]
    for i, notes in enumerate(phrases, 1):   # 啜泣：倒著往下走的旋律
        v = m_call(rng, notes, ("oh", "oo", "mm"), peak=-5)
        if samples:   # a free moan underneath, lowered and darkened
            smp = pitch_shift(samples[(i - 1) % len(samples)], -rng.uniform(3, 6))[: len(v)]
            smp = S.bandpass(smp, 500, 0.8) * S.adsr(len(smp), 0.2, 0.6)
            S.place(v, 0.5 * smp * np.max(np.abs(v)) / (np.max(np.abs(smp)) + 1e-9), 0.0)
            v = S.normalise(v, -5)
        sounds[f"ambient{i}"] = v
    for i in (1, 2):   # 受傷：短促的一聲哭叫
        sounds[f"hurt{i}"] = m_call(rng, [(7 + i, 0.1), (3, 0.35)], ("ah", "oh"), attack=0.02, release=0.2, sobbing=0, wet=0.3, size=0.9, peak=-3)
    f0 = S.vibrato(np.geomspace(note(M_BASE, 7), note(M_BASE, -14), int(2.6 * S.SR)), 6, 0.04, rng, 0.2, 4.0)
    v = mourner_voice(f0, rng, ("oh", "oo", "mm")) * S.adsr(len(f0), 0.1, 1.4) * sob(len(f0), rng, 1.8, 0.4)
    sounds["death1"] = S.normalise(S.reverb(S.normalise(v), 0.55, 1.5), -3)
    # 唱歌用的單音（倒著唱八音時用）：F#4、抖著、帶抽泣
    f0 = S.vibrato(np.full(int(1.2 * S.SR), VOICE_BASE * 2 ** (-0.3 / 12)), 7.0, 0.022, rng, 0.08, 3.0)
    v = mourner_voice(f0, rng, ("oh", "oo")) * S.adsr(len(f0), 0.06, 0.6, curve=1.5) * sob(len(f0), rng, 2.6, 0.3)
    sounds["voice"] = S.normalise(S.reverb(S.normalise(v), 0.4, 1.2), -2)
    # 互動
    sounds["wail1"] = m_call(rng, [(0, 0.5), (5, 0.5), (9, 1.4)], ("oo", "oh", "ah"), attack=0.4, release=0.9, sobbing=0.25, peak=-3)   # 看到玩家、開始哭著唱：一聲往上拉的哀號
    sounds["wail2"] = m_call(rng, [(2, 0.5), (7, 0.6), (11, 1.3)], ("oo", "oh", "ah"), attack=0.4, release=0.9, sobbing=0.25, peak=-3)
    sounds["soothe1"] = m_call(rng, [(4, 0.5), (7, 0.9)], ("mm", "ah"), vib=0.01, sobbing=0.1, peak=-6)   # 泡靈液／聽香爐：被安慰、鬆一口氣
    sounds["soothe2"] = m_call(rng, [(2, 0.5), (9, 0.9)], ("mm", "ah"), vib=0.01, sobbing=0.1, peak=-6)
    sounds["hush1"] = m_call(rng, [(5, 0.3), (4, 0.4), (2, 0.8)], ("oh", "mm"), vib=0.015, sobbing=0.3, release=0.8, peak=-7)   # 被號角安撫：哭聲漸漸收住
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


BIOME_RECIPES = {
    "crimson_strata_canyon": (crimson_strata_canyon, 41), "violet_slate_abyss": (violet_slate_abyss, 42),
    "amber_dunes": (amber_dunes, 43), "red_zone_caves": (red_zone_caves, 44),
    "lullaby_hills": (lullaby_hills, 45), "soul_caldera": (soul_caldera, 46),
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
EVENTS.update(MU.EVENTS)


def main():
    names = ONLY.split(",") if ONLY else list(RECIPES)
    for name in names:
        recipe, folder, seed = RECIPES[name]
        sounds = recipe(np.random.default_rng(seed))
        gap = np.zeros(int(0.7 * S.SR))
        reel = []
        for key, x in sounds.items():
            x = S.fade(x, 0.003, 0.03) if not key.startswith("loop") else x
            S.write_ogg(PREVIEW / name / f"{key}.ogg", x)
            if INSTALL:
                S.write_ogg(ASSETS / folder / f"{key}.ogg", x)
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
