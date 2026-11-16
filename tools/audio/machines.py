"""Soul power machine sounds, fully synthesised (imported by build_sounds.py, which sets B).

  chug1-3      Spirit Engine: one piston stroke - a low thump, a soft valve puff and a metal tick
  grind1-3     Soul Grinder: stone grating on stone, with a few crunching grains
  pulse1-2     Soul Wave Emitter: a soft crystal ping wrapped in a breathy whoosh (each wave sent)
  overload1-2  any overloaded machine: a strained groan with a soul hiss rising over it
  conflict1    a speed conflict: two gears grinding against each other
Played by the block entities in src/main/java/pryuan05/pysift/soulpower/ (SoulPowerSounds)."""
import numpy as np

import synth as S

B = None


def env_exp(n, tau):
    return np.exp(-np.arange(n) / (tau * S.SR))


def thump(rng, freq=58, seconds=0.35):
    n = int(seconds * S.SR)
    t = np.arange(n) / S.SR
    f = freq * (1 + 0.6 * np.exp(-t / 0.03))
    return np.sin(2 * np.pi * np.cumsum(f) / S.SR) * env_exp(n, 0.09)


def chug(rng, pitch=1.0):
    n = int(0.55 * S.SR)
    out = np.zeros(n)
    S.place(out, thump(rng, 55 * pitch), 0.0)
    puff = S.noise_band(int(0.32 * S.SR), 300 * pitch, 2600, rng) * S.adsr(int(0.32 * S.SR), 0.02, 0.25)
    S.place(out, 0.45 * puff, 0.05)
    tick = S.bell(1900 * pitch, 0.12, rng, bright=1.5)
    S.place(out, 0.18 * tick, 0.02)
    return S.normalise(S.lowpass(out, 5000), -4)


def grind(rng):
    n = int(0.9 * S.SR)
    grate = S.noise_band(n, 120, 1400, rng, colour="brown")
    # the stone catches and slips: a slow wobble in the grating
    wob = 0.6 + 0.4 * np.sin(2 * np.pi * rng.uniform(5, 8) * np.arange(n) / S.SR + rng.uniform(0, 6))
    out = grate * wob * S.adsr(n, 0.08, 0.3)
    for _ in range(int(rng.integers(4, 8))):   # crunching grains
        g = S.noise_band(int(0.03 * S.SR), 1500, 6000, rng) * env_exp(int(0.03 * S.SR), 0.008)
        S.place(out, 0.35 * g, rng.uniform(0.05, 0.8))
    return S.normalise(out, -5)


def sift(rng):
    """Grains rattling on a shaking wooden sieve: bursts of sandy noise at the shake rate."""
    n = int(1.0 * S.SR)
    out = np.zeros(n)
    for k in range(4):
        burst = S.noise_band(int(0.18 * S.SR), 1800, 9000, rng) * S.adsr(int(0.18 * S.SR), 0.03, 0.12)
        S.place(out, (0.8 if k % 2 == 0 else 0.55) * burst, k * 0.24 + rng.uniform(0, 0.02))
        S.place(out, 0.3 * thump(rng, 140, 0.08), k * 0.24)
    return S.normalise(out, -6)


def pulse(rng):
    n = int(1.2 * S.SR)
    out = np.zeros(n)
    f = rng.choice([880, 988, 1175])
    S.place(out, 0.5 * S.bell(f, 1.1, rng, bright=0.7), 0.0)
    whoosh = S.noise_band(int(0.6 * S.SR), 400, 3000, rng) * S.adsr(int(0.6 * S.SR), 0.25, 0.3)
    S.place(out, 0.35 * whoosh, 0.0)
    return S.normalise(S.reverb(out, wet=0.35, size=1.2), -6)


def overload(rng):
    n = int(1.6 * S.SR)
    t = np.arange(n) / S.SR
    groan_f = 70 + 12 * np.sin(2 * np.pi * 1.3 * t) + rng.normal(0, 1, n).cumsum() * 0.002
    groan = S.lowpass(S.glottal(groan_f, rolloff=0.9, max_hz=3000), 900) * S.adsr(n, 0.2, 0.4)
    hiss = S.noise_band(n, 2500, 9000, rng) * np.linspace(0.1, 1.0, n) ** 2 * S.adsr(n, 0.3, 0.2)
    rattle = np.zeros(n)
    for k in range(int(rng.integers(10, 16))):
        S.place(rattle, S.bell(rng.uniform(1200, 2400), 0.06, rng, bright=2), rng.uniform(0, 1.4))
    return S.normalise(0.8 * groan + 0.35 * hiss + 0.25 * rattle, -4)


def conflict(rng):
    n = int(1.3 * S.SR)
    t = np.arange(n) / S.SR
    # two toothed wheels: a rasp at the tooth rate with a squeal on top
    teeth = np.sign(np.sin(2 * np.pi * 38 * t)) * S.noise_band(n, 200, 4000, rng)
    squeal = np.sin(2 * np.pi * np.cumsum(2400 + 300 * np.sin(2 * np.pi * 3 * t)) / S.SR)
    out = (0.7 * teeth + 0.25 * squeal) * S.adsr(n, 0.05, 0.4)
    return S.normalise(S.lowpass(out, 7000), -4)


def soul_power(rng):
    out = {}
    for i, p in enumerate((1.0, 0.94, 1.07), 1):
        out[f"chug{i}"] = chug(rng, p)
    for i in range(1, 4):
        out[f"grind{i}"] = grind(rng)
    for i in range(1, 3):
        out[f"pulse{i}"] = pulse(rng)
    for i in range(1, 3):
        out[f"sift{i}"] = sift(rng)
    for i in range(1, 3):
        out[f"overload{i}"] = overload(rng)
    out["conflict1"] = conflict(rng)
    return out


RECIPES = {"soul_power": (soul_power, "block/soul_power", 81)}
EVENTS = {"soul_power": [
    ("block.spirit_engine.chug", "chug", "Spirit Engine chugs", "靈液引擎運轉", {}),
    ("block.soul_grinder.grind", "grind", "Soul Grinder grinds", "靈魂研磨機研磨", {}),
    ("block.soul_sifter.sift", "sift", "Soul Sifter rattles", "靈魂淨化篩沙沙作響", {}),
    ("block.soul_wave.pulse", "pulse", "Soul wave sent", "靈魂振波發送", {}),
    ("block.soul_power.overload", "overload", "Soul machines strain", "靈魂機械過載", {}),
    ("block.soul_power.conflict", "conflict", "Gears grind", "齒輪互相卡住", {}),
]}
