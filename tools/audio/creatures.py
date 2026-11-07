"""Sounds for the remaining creatures, made from free Pixabay recordings in sound_sources/<mob>/ (see CREDITS.md).

Imported by build_sounds.py, which supplies the shared helpers (load_samples, slices, pitch_shift, glide_shift, mix,
finish, rumble, choir). Every recording is cut, pitch-shifted, filtered and layered; none is shipped unmodified.
Sound names: ambient / hurt / death, plus one per skill animation (the name of the GeckoLib animation, so
PysiftGeoEntity plays it automatically when that animation starts).
"""
import numpy as np

import synth as S

B = None   # build_sounds module, set by build_sounds.py


def _x(x):
    return x / (np.max(np.abs(x)) + 1e-9)


def cut(x, rng, lo=0.25, hi=1.6, th=0.25, n=1):
    c = B.slices(x, n, rng, min_len=lo, max_len=hi, thresh=th)
    return c if n > 1 else c[0]


def whoosh(seconds, rng, lo=300, hi=2500, up=True):
    n = int(seconds * S.SR)
    x = S.noise_band(n, lo, hi, rng)
    env = np.sin(np.linspace(0, np.pi, n)) ** 2
    sweep = np.linspace(0.6, 1.4, n) if up else np.linspace(1.4, 0.6, n)
    return x * env * sweep


def snap(rng, seconds=0.08, lo=1500, hi=7000):
    n = int(seconds * S.SR)
    return S.noise_band(n, lo, hi, rng) * S.adsr(n, 0.001, seconds * 0.8)


def heartbeat(rng, beats=2, gap=0.32, hz=48):
    out = np.zeros(int((beats * gap + 0.6) * S.SR))
    for k in range(beats):
        n = int(0.35 * S.SR)
        t = np.arange(n) / S.SR
        thump = np.sin(2 * np.pi * hz * t) * np.exp(-t / 0.09)
        S.place(out, thump * (1.0 if k % 2 == 0 else 0.7), k * gap)
    return out


def coins(rng, count=5, seconds=0.9):
    out = np.zeros(int(seconds * S.SR))
    for _ in range(count):
        S.place(out, 0.4 * S.bell(rng.uniform(2600, 4200), 0.35, rng, bright=2.5), rng.uniform(0, seconds - 0.35))
    return out


def sh(x, semis):
    return B.pitch_shift(x, semis) if semis else x


# ---------------------------------------------------------------- 授粉者：會螫人的蟲
def pollinator(rng):
    s = {}
    buzz = B.load_samples("pollinator", "ambient")
    mosq = B.load_samples("pollinator", "attack")[0]
    for i in range(1, 4):
        c = sh(cut(buzz[(i - 1) % len(buzz)], rng, 1.0, 1.8, 0.15), rng.uniform(1, 3))
        s[f"ambient{i}"] = B.finish(c * S.adsr(len(c), 0.15, 0.4), wet=0.1, peak=-9)
    for i in (1, 2):
        c = cut(buzz[i % len(buzz)], rng, 0.4, 0.5, 0.2)
        s[f"hurt{i}"] = B.finish(B.glide_shift(c, 0, 6 + i), wet=0.1, peak=-4)
    s["death1"] = B.finish(B.glide_shift(cut(buzz[0], rng, 0.8, 1.0, 0.2), 3, -10), wet=0.2, peak=-4)
    for i in (1, 2):   # 螫：高頻的一下＋尖刺
        c = sh(cut(mosq, rng, 0.25, 0.35, 0.3), 2 + i)
        s[f"sting{i}"] = B.finish(B.mix((c, 1.0), (snap(rng, 0.06, 3000, 9000), 0.6)), wet=0.05, peak=-4)
    c = cut(buzz[-1], rng, 1.2, 1.5, 0.15)   # 授粉：嗡聲加上幾聲柔和的叮
    out = B.mix((c, 0.6))
    for k in range(3):
        S.place(out, 0.2 * S.bell(B.note(B.A3, 19 + 3 * k), 0.9, rng), 0.2 + 0.25 * k)
    s["pollinate1"] = B.finish(out, wet=0.3, peak=-7)
    c = cut(buzz[0], rng, 0.9, 1.1, 0.15)   # 被打：整群被激怒，嗡聲猛地拉高
    s["alarm1"] = B.finish(B.mix((B.glide_shift(c, 0, 9), 1.0), (B.glide_shift(sh(c, 4), 0, 7), 0.6)), wet=0.15, peak=-3)
    return s


# ---------------------------------------------------------------- 漫遊根：緩慢的植物巨人
def roamroot(rng):
    s = {}
    creak = B.load_samples("roamroot", "ambient")[0]
    creak2 = B.load_samples("roamroot", "special")[0]
    groan = B.load_samples("roamroot", "hurt")[0]
    groans = B.load_samples("roamroot", "death")[0]
    for i in range(1, 4):
        c = sh(cut(creak, rng, 1.0, 2.5, 0.3), -3)
        s[f"ambient{i}"] = B.finish(B.mix((c, 1.0), (B.rumble(len(c) / S.SR, rng), 0.15)), wet=0.25, lp=4000, peak=-6)
    for i in (1, 2):
        g = sh(cut(groan, rng, 0.6, 1.0, 0.2), -1 - i)
        s[f"hurt{i}"] = B.finish(B.mix((g, 1.0), (snap(rng, 0.15, 800, 4000), 0.4)), wet=0.15, lp=5000, peak=-3)
    g = B.glide_shift(cut(groans, rng, 2.0, 3.5, 0.25), -2, -8)
    s["death1"] = B.finish(B.mix((g, 1.0), (sh(cut(creak2, rng, 2.0, 3.0, 0.2), -4), 0.6)), wet=0.35, size=1.2, lp=4000, peak=-3)
    for i in (1, 2):   # 跺地
        g = sh(cut(groan, rng, 0.4, 0.6, 0.3), -6)
        s[f"stomp{i}"] = B.finish(B.mix((g, 0.6), (B.rumble(0.9, rng, 120), 1.0), (B.thud(rng, 0.9), 0.8)), wet=0.2, peak=-2)
    for i in (1, 2):
        c = sh(cut(creak2, rng, 0.5, 0.7, 0.3), -2)
        s[f"attack{i}"] = B.finish(B.mix((c, 1.0), (whoosh(0.5, rng, 200, 1500), 0.5)), wet=0.1, peak=-4)
    return s


# ---------------------------------------------------------------- 盛開花苞：偽裝成花苞，會咬合（不發平時的聲音）
def bloombud(rng):
    s = {}
    sq = B.load_samples("bloombud", "special")
    celery = B.load_samples("bloombud", "attack")[0]
    snaps = cut(celery, rng, 0.2, 0.35, 0.3, n=3)
    for i in range(1, 4):
        out = B.mix((sh(snaps[i - 1], -2), 1.0))
        S.place(out, 0.7 * _x(sh(cut(sq[i % 2], rng, 0.3, 0.5, 0.3), -3)), 0.04)
        s[f"bite{i}"] = B.finish(out, wet=0.1, peak=-3)
    for i in (1, 2):
        s[f"hurt{i}"] = B.finish(sh(cut(sq[i - 1], rng, 0.3, 0.45, 0.3), 2), wet=0.1, peak=-4)
    out = B.glide_shift(cut(sq[0], rng, 0.8, 1.6, 0.15), 0, -7)
    s["death1"] = B.finish(B.mix((out, 1.0), (sh(snaps[0], -5), 0.5)), wet=0.25, peak=-3)
    return s


# ---------------------------------------------------------------- 哨兵：拿重劍的遺跡戰士
def sentinel(rng):
    s = {}
    slash = B.load_samples("sentinel", "attack")
    hit = B.load_samples("sentinel", "hurt")[0]
    fall = B.load_samples("sentinel", "death")[0]
    for i in (1, 2):   # 平時：盔甲輕響＋低沉的金屬嗡鳴
        out = B.mix((S.bell(B.note(B.A3 / 2, i * 2), 1.6, rng, bright=0.6), 0.5))
        S.place(out, 0.6 * _x(sh(cut(hit, rng, 0.15, 0.25, 0.4), 9)), 0.05)
        S.place(out, 0.4 * _x(sh(cut(hit, rng, 0.15, 0.25, 0.4), 11)), 0.32)
        s[f"ambient{i}"] = B.finish(out, wet=0.3, peak=-11)
    for i in (1, 2):   # 蓄力劈砍：沉重的揮劍＋劍身的鳴響
        out = B.mix((sh(slash[i - 1], -2), 1.0))
        S.place(out, 0.25 * S.bell(B.note(B.A3, 3 + i), 1.2, rng, bright=1.5), 0.15)
        s[f"slash{i}"] = B.finish(out, wet=0.2, peak=-2)
    for i in (1, 2):
        s[f"attack{i}"] = B.finish(sh(cut(slash[i - 1], rng, 0.3, 0.6, 0.3), 1), wet=0.1, peak=-4)
    for i in (1, 2):
        s[f"hurt{i}"] = B.finish(sh(cut(hit, rng, 0.4, 0.6, 0.3), 2 * (i - 1)), wet=0.15, peak=-4)
    s["death1"] = B.finish(B.mix((B.glide_shift(fall, 0, -5), 1.0), (B.rumble(len(fall) / S.SR, rng), 0.3)), wet=0.3, size=1.1, peak=-3)
    out = B.mix((sh(cut(hit, rng, 0.4, 0.6, 0.3), -3), 1.0), (snap(rng, 0.3, 500, 4000), 0.7))   # 劈碎玩家的盾牌
    S.place(out, 0.3 * S.bell(B.note(B.A3, 1), 1.0, rng, bright=2.0), 0.0)
    s["guard_break1"] = B.finish(out, wet=0.2, peak=-2)
    return s


# ---------------------------------------------------------------- 追蹤者：黑暗中隱形、繞背（平時很小聲）
def stalker(rng):
    s = {}
    breath = B.load_samples("stalker", "ambient")[0]
    hiss = B.load_samples("stalker", "attack")[0]
    dying = B.load_samples("stalker", "death")[0]
    for i in range(1, 4):
        s[f"ambient{i}"] = B.finish(sh(cut(breath, rng, 1.0, 2.0, 0.2), -2), wet=0.2, lp=3000, peak=-14)
    for i in (1, 2):
        s[f"attack{i}"] = B.finish(sh(cut(hiss, rng, 0.6, 1.0, 0.25), -1), wet=0.1, peak=-3)
    for i in (1, 2):
        s[f"hurt{i}"] = B.finish(sh(cut(hiss, rng, 0.3, 0.4, 0.3), 3), wet=0.1, peak=-4)
    s["death1"] = B.finish(B.glide_shift(dying, 0, -4), wet=0.3, lp=5000, peak=-3)
    out = B.glide_shift(cut(breath, rng, 0.8, 1.2, 0.2), 0, -6)   # 在黑暗中隱形：一口氣被吸回去
    s["vanish1"] = B.finish(B.mix((out[::-1].copy(), 1.0), (whoosh(1.0, rng, 1500, 6000, up=False), 0.3)), wet=0.4, lp=6000, peak=-10)
    out = B.mix((sh(cut(hiss, rng, 0.4, 0.6, 0.3), -3), 1.0), (snap(rng, 0.1, 1000, 6000), 0.8))   # 背刺
    s["backstab1"] = B.finish(out, wet=0.1, peak=-2)
    return s


# ---------------------------------------------------------------- 獵人：君王的士兵；陷阱師用同樣的素材換音色
def _hunter_like(rng, up, lp, kinds):
    s = {}
    grunts = B.load_samples("hunter", "ambient")[0]
    shout = B.load_samples("hunter", "attack")[0]
    hurt = B.load_samples("hunter", "hurt")[0]
    growl = B.load_samples("hunter", "death")[0]
    for i, c in enumerate(cut(grunts, rng, 0.5, 1.4, 0.3, n=4), 1):
        s[f"ambient{i}"] = B.finish(sh(c, up + rng.uniform(-1, 1)), wet=0.15, lp=lp, peak=-6)
    for i in (1, 2):
        s[f"hurt{i}"] = B.finish(sh(cut(hurt, rng, 0.3, 0.6, 0.3), up + i - 1), wet=0.1, lp=lp, peak=-3)
    s["death1"] = B.finish(B.glide_shift(cut(growl, rng, 1.5, 2.5, 0.2), up, up - 5), wet=0.3, lp=lp, peak=-3)
    for i in (1, 2):
        s[f"attack{i}"] = B.finish(sh(cut(grunts, rng, 0.25, 0.45, 0.35), up - 1), wet=0.1, lp=lp, peak=-4)
    if "throw" in kinds:
        for i in (1, 2):
            s[f"throw{i}"] = B.finish(B.mix((sh(shout, up + 2 * i - 3), 1.0), (whoosh(0.5, rng), 0.5)), wet=0.1, lp=lp, peak=-3)
    if "mark" in kinds:   # 標記獵物：拉高的喊聲＋一聲響亮的叮
        out = B.mix((B.glide_shift(cut(grunts, rng, 0.6, 0.9, 0.3), up, up + 3), 1.0))
        S.place(out, 0.35 * S.bell(B.note(B.A3, 19), 1.4, rng, bright=1.6), 0.2)
        s["mark1"] = B.finish(out, wet=0.35, lp=lp, peak=-3)
    if "leap" in kinds:
        s["leap1"] = B.finish(B.mix((sh(shout, up + 3), 1.0), (whoosh(0.6, rng, 400, 3000), 0.4)), wet=0.1, lp=lp, peak=-4)
    if "set_trap" in kinds:   # 佈置陷阱：哼一聲＋繩子與藤蔓的沙沙聲
        out = B.mix((sh(cut(grunts, rng, 0.4, 0.6, 0.3), up), 0.8), (np.zeros(int(1.0 * S.SR)), 0.0))
        for k in range(4):
            S.place(out, 0.4 * snap(rng, 0.12, 600, 3500), 0.3 + 0.12 * k)
        s["set_trap1"] = B.finish(out, wet=0.1, lp=lp, peak=-5)
    if "throw_net" in kinds:
        out = B.mix((sh(shout, up), 1.0), (whoosh(0.8, rng, 200, 2000), 0.6))
        s["throw_net1"] = B.finish(out, wet=0.1, lp=lp, peak=-3)
    return s


def hunter(rng):
    return _hunter_like(rng, -1, 6000, ("throw", "mark", "leap"))


def trapper(rng):
    return _hunter_like(rng, 4, 3500, ("set_trap", "throw_net"))


# ---------------------------------------------------------------- 飛鏢背：有殼、射刺、衝撞
def dartback(rng):
    s = {}
    click = B.load_samples("dartback", "ambient")[0]
    hiss = B.load_samples("dartback", "attack")[0]
    for i in range(1, 4):
        c = sh(cut(click, rng, 0.3, 0.8, 0.3), -3)
        s[f"ambient{i}"] = B.finish(B.mix((c, 1.0), (sh(cut(hiss, rng, 0.3, 0.5, 0.3), -4), 0.2)), wet=0.1, peak=-7)
    for i in (1, 2):
        out = B.mix((sh(cut(hiss, rng, 0.25, 0.35, 0.3), 1), 1.0), (snap(rng, 0.05, 2000, 8000), 0.7))
        s[f"shoot{i}"] = B.finish(out, wet=0.05, peak=-3)
    out = B.mix((B.glide_shift(cut(hiss, rng, 1.0, 1.3, 0.2), -3, 2), 1.0), (B.rumble(1.2, rng), 0.5))
    s["charge1"] = B.finish(out, wet=0.1, peak=-3)
    for i in (1, 2):
        out = B.mix((sh(cut(click, rng, 0.2, 0.4, 0.3), 2), 1.0), (snap(rng, 0.15, 900, 5000), 0.5))
        s[f"hurt{i}"] = B.finish(out, wet=0.1, peak=-4)
    out = B.mix((sh(cut(click, rng, 0.15, 0.3, 0.4), -6), 1.0), (snap(rng, 0.12, 400, 2500), 0.8))   # 背甲擋下攻擊
    s["block1"] = B.finish(out, wet=0.1, peak=-3)
    out = B.mix((B.glide_shift(cut(hiss, rng, 1.0, 1.5, 0.2), 0, -7), 1.0), (sh(click, -5)[: int(1.4 * S.SR)], 0.5))
    s["death1"] = B.finish(out, wet=0.25, peak=-3)
    return s


# ---------------------------------------------------------------- 刺球：帶刺、會反傷
def prickle(rng):
    s = {}
    hog = B.load_samples("prickle", "ambient")[0]
    rattle = B.load_samples("prickle", "attack")[0]
    shake = B.load_samples("prickle", "special")[0]
    for i, c in enumerate(cut(hog, rng, 0.5, 1.5, 0.3, n=3), 1):
        s[f"ambient{i}"] = B.finish(sh(c, 1), wet=0.1, peak=-7)
    for i in (1, 2):   # 豎刺射出
        out = B.mix((cut(rattle, rng, 0.5, 0.7, 0.2), 1.0), (sh(cut(shake, rng, 0.3, 0.5, 0.3), 3), 0.5))
        s[f"bristle{i}"] = B.finish(out, wet=0.1, peak=-3)
    for i in (1, 2):
        out = B.mix((sh(cut(hog, rng, 0.25, 0.4, 0.4), 4), 1.0), (sh(cut(shake, rng, 0.2, 0.3, 0.3), 5), 0.3))
        s[f"hurt{i}"] = B.finish(out, wet=0.1, peak=-4)
    s["death1"] = B.finish(B.glide_shift(cut(hog, rng, 0.8, 1.2, 0.3), 2, -6), wet=0.25, peak=-3)
    return s


# ---------------------------------------------------------------- 築巢者與幼體（幼苗、萌芽用同樣的素材變高音）
def nester(rng):
    s = {}
    call = B.load_samples("nester", "ambient")[0]
    ptero = B.load_samples("nester", "special")[0]
    scream = B.load_samples("nester", "hurt")[0]
    for i, st in enumerate((-5, -7, -4), 1):
        s[f"ambient{i}"] = B.finish(sh(call, st), wet=0.3, size=1.1, lp=4000, peak=-6)
    s["summon1"] = B.finish(B.mix((sh(ptero, -4), 1.0), (sh(call, -9), 0.5)), wet=0.4, size=1.3, peak=-3)
    s["attack1"] = B.finish(sh(cut(ptero, rng, 0.4, 0.6, 0.3), -2), wet=0.1, peak=-4)
    for i in (1, 2):
        s[f"hurt{i}"] = B.finish(sh(cut(scream, rng, 0.4, 0.6, 0.3), -3 + i), wet=0.1, peak=-3)
    s["death1"] = B.finish(B.glide_shift(cut(scream, rng, 1.0, 1.6, 0.2), -2, -9), wet=0.3, peak=-3)
    out = B.mix((sh(ptero, -6), 1.0), (B.rumble(2.0, rng, 140), 0.6), (snap(rng, 0.5, 200, 3000), 0.5))   # 死前一聲爆鳴，激怒幼體
    s["rally1"] = B.finish(out, wet=0.4, size=1.3, peak=-2)
    return s


def _brood(rng, up):
    s = {}
    call = B.load_samples("nester", "ambient")[0]
    scream = B.load_samples("nester", "hurt")[0]
    for i in (1, 2):
        s[f"ambient{i}"] = B.finish(sh(call, up + 2 * i), wet=0.15, peak=-8)
    for i in (1, 2):
        s[f"hurt{i}"] = B.finish(sh(cut(scream, rng, 0.2, 0.3, 0.4), up + i), wet=0.05, peak=-5)
    s["death1"] = B.finish(B.glide_shift(cut(scream, rng, 0.4, 0.6, 0.3), up, up - 6), wet=0.15, peak=-5)
    s["attack1"] = B.finish(B.mix((sh(cut(scream, rng, 0.2, 0.25, 0.4), up - 2), 1.0), (snap(rng, 0.05), 0.5)), wet=0.05, peak=-5)
    s["alert1"] = B.finish(B.glide_shift(sh(call, up), 0, 4), wet=0.2, peak=-5)   # 發現獵物，叫同伴一起上
    return s


def seedling(rng):
    return _brood(rng, 7)


def sprout(rng):
    return _brood(rng, 4)


# ---------------------------------------------------------------- 清道夫：腐食獵手、咬人流血
def scavenger(rng):
    s = {}
    laughs = B.load_samples("scavenger", "ambient")
    vulture = B.load_samples("scavenger", "hurt")[0]
    for i in range(1, 4):
        c = cut(laughs[(i - 1) % 2], rng, 0.8, 1.8, 0.2)
        s[f"ambient{i}"] = B.finish(sh(c, -1 - 2 * (i - 1) / 2), wet=0.15, peak=-6)
    for i in (1, 2):   # 咬：短促的笑聲＋咬合
        out = B.mix((sh(cut(laughs[i - 1], rng, 0.3, 0.4, 0.3), -2), 1.0), (snap(rng, 0.07, 800, 5000), 0.7))
        s[f"attack{i}"] = B.finish(out, wet=0.05, peak=-3)
    for i in (1, 2):
        s[f"hurt{i}"] = B.finish(sh(cut(vulture, rng, 0.3, 0.5, 0.3), -2 + i), wet=0.1, peak=-3)
    s["death1"] = B.finish(B.glide_shift(laughs[1], 0, -8), wet=0.3, peak=-3)
    tear = B.mix((snap(rng, 0.25, 300, 2500), 1.0), (sh(cut(laughs[0], rng, 0.25, 0.35, 0.3), -6), 0.4))   # 咬出流血
    s["bleed1"] = B.finish(tear, wet=0.1, lp=4000, peak=-5)
    return s


# ---------------------------------------------------------------- 投擲者：從地上挖石頭丟人
def hurler(rng):
    s = {}
    chitter = B.load_samples("hurler", "ambient")[0]
    grunt = B.load_samples("hurler", "attack")[0]
    roar = B.load_samples("hurler", "special")[0]
    for i, st in enumerate((-4, -6, -5), 1):
        out = B.mix((sh(chitter, st), 1.0))
        if i == 3:
            S.place(out, 0.6 * _x(sh(cut(grunt, rng, 0.3, 0.5, 0.3), -5)), 0.5)
        s[f"ambient{i}"] = B.finish(out, wet=0.15, lp=5000, peak=-6)
    for i in (1, 2):
        s[f"throw{i}"] = B.finish(B.mix((sh(grunt, -3 - i), 1.0), (whoosh(0.6, rng, 200, 1800), 0.5)), wet=0.1, peak=-3)
    s["attack1"] = B.finish(sh(cut(grunt, rng, 0.3, 0.6, 0.3), -5), wet=0.1, peak=-4)
    for i in (1, 2):
        s[f"hurt{i}"] = B.finish(sh(cut(chitter, rng, 0.25, 0.4, 0.3), -1 + i), wet=0.1, peak=-3)
    s["death1"] = B.finish(B.glide_shift(cut(roar, rng, 1.5, 2.5, 0.2), -2, -8), wet=0.3, peak=-3)
    return s


# ---------------------------------------------------------------- 搖晃怪：傻乎乎的果凍
def wobble(rng):
    s = {}
    jelly = B.load_samples("wobble", "ambient")[0]
    boing = B.load_samples("wobble", "special")[0]
    whoop = B.load_samples("wobble", "hurt")[0]
    for i, st in enumerate((0, -3, 3), 1):
        out = B.mix((sh(jelly, st), 1.0))
        S.place(out, 0.3 * _x(sh(cut(boing, rng, 0.3, 0.5, 0.3), st - 5)), 0.25)
        s[f"ambient{i}"] = B.finish(out, wet=0.1, peak=-7)
    for i in (1, 2):
        s[f"attack{i}"] = B.finish(sh(cut(boing, rng, 0.5, 0.7, 0.25), -2 * i), wet=0.1, peak=-4)
    for i in (1, 2):
        s[f"hurt{i}"] = B.finish(sh(cut(whoop, rng, 0.5, 0.8, 0.25), i - 1), wet=0.1, peak=-4)
    out = B.mix((B.glide_shift(cut(whoop, rng, 1.0, 1.5, 0.2), 0, -9), 1.0), (sh(jelly, -6), 0.5))
    s["death1"] = B.finish(out, wet=0.25, peak=-3)
    pop = B.mix((sh(boing, -7)[: int(0.8 * S.SR)], 0.7), (snap(rng, 0.2, 100, 1500), 1.0), (sh(jelly, -9), 0.8))   # 死後炸開成噁心的雲
    s["burst1"] = B.finish(pop, wet=0.3, peak=-2)
    return s


# ---------------------------------------------------------------- 掠奪精：很快、會逃跑，身上叮叮噹噹
def lootkin(rng):
    s = {}
    laugh = B.load_samples("lootkin", "ambient")[0]
    giggle = B.load_samples("lootkin", "special")[0]
    for i in range(1, 4):
        out = coins(rng, 4 + i)
        if i != 2:
            S.place(out, 0.8 * _x(sh(giggle if i == 1 else cut(laugh, rng, 0.4, 0.7, 0.3), 3)), 0.15)
        s[f"ambient{i}"] = B.finish(out, wet=0.15, peak=-7)
    for i in (1, 2):
        out = B.mix((sh(giggle, 6 + i)[: int(0.35 * S.SR)], 1.0), (coins(rng, 3, 0.5), 0.5))
        s[f"hurt{i}"] = B.finish(out, wet=0.1, peak=-4)
    for i in (1, 2):   # 看到玩家就逃：一陣叮噹亂響＋竊笑
        out = coins(rng, 9, 1.2)
        S.place(out, 0.8 * _x(sh(giggle, 4 + i)), 0.05)
        s[f"flee{i}"] = B.finish(out, wet=0.1, peak=-5)
    out = B.mix((B.glide_shift(laugh, 3, -6), 1.0), (coins(rng, 12, 1.6), 0.7))
    s["death1"] = B.finish(out, wet=0.25, peak=-3)
    return s


# ---------------------------------------------------------------- 君王（Boss）：大型猛禽叫聲＋王者的回音與合唱
def monarch(rng):
    s = {}
    eagle = B.load_samples("monarch", "ambient")[0]
    cry = B.load_samples("monarch", "hurt")[0]
    hawk = B.load_samples("monarch", "special")[0]

    def royal(x, wet=0.5, peak=-3):
        drone = S.organ(np.full(len(x) + int(0.8 * S.SR), B.A3 / 4), ((1, 1.0), (2, 0.5), (3, 0.3))) * S.adsr(len(x) + int(0.8 * S.SR), 0.2, 0.6)
        return B.finish(B.mix((x, 1.0), (drone, 0.18)), wet=wet, size=1.6, peak=peak)

    for i, st in enumerate((-5, -7), 1):
        s[f"ambient{i}"] = royal(sh(eagle, st), peak=-5)
    for i in (1, 2):
        s[f"attack{i}"] = B.finish(sh(cut(hawk, rng, 0.3, 0.5, 0.3), -3 - i), wet=0.2, peak=-3)
    s["leap1"] = royal(B.mix((sh(hawk, -2), 1.0), (whoosh(1.0, rng), 0.5)), wet=0.3)
    s["shockwave1"] = royal(B.mix((sh(eagle, -7), 0.8), (B.rumble(1.4, rng, 140), 1.0), (B.thud(rng, 1.4), 0.8)), wet=0.35, peak=-1)
    s["dash_strike1"] = B.finish(B.mix((hawk, 1.0), (whoosh(0.8, rng, 500, 4000), 0.6)), wet=0.2, peak=-2)
    flaps = np.zeros(int(1.8 * S.SR))
    for k in range(5):
        S.place(flaps, whoosh(0.25, rng, 150, 1200), 0.1 + 0.32 * k)
    s["hover_loop1"] = royal(B.mix((sh(eagle, -4), 0.8), (flaps, 0.7)), wet=0.45)
    s["calamity1"] = royal(B.mix((sh(hawk, -8), 1.0), (sh(cry, -10), 0.8), (B.rumble(2.2, rng, 160), 0.8)), wet=0.55, peak=-1)
    s["heel_stomp1"] = B.finish(B.mix((B.thud(rng, 1.0), 1.0), (sh(eagle, -9), 0.5)), wet=0.2, peak=-2)
    out = B.mix((sh(cry, -4), 1.0), (B.choir(rng, [-12, -5, 0, 7], 2.4, attack=0.2, release=0.9), 0.6))
    s["summon1"] = B.finish(out, wet=0.5, size=1.6, peak=-2)   # 召喚近衛：王者的呼喊＋合唱
    for i in (1, 2):
        s[f"hurt{i}"] = B.finish(sh(cut(cry, rng, 0.4, 0.7, 0.3), -3 - i), wet=0.25, peak=-3)
    echo = sh(eagle, -6)   # 分出鏡像分身：倒放的叫聲接正放的回音
    out = B.mix((echo[::-1].copy(), 0.8), (np.zeros(int(2.0 * S.SR)), 0.0))
    S.place(out, 0.8 * _x(echo), len(echo) / S.SR)
    s["echo1"] = B.finish(out, wet=0.65, size=1.8, peak=-3)
    out = B.mix((B.glide_shift(cry, -2, -12), 1.0), (B.choir(rng, [-12, -5, 0], 3.0, attack=0.1, release=1.5, bend=(0, -10)), 0.5))
    s["death1"] = B.finish(out, wet=0.55, size=1.8, peak=-2)
    return s


# ---------------------------------------------------------------- 幽匿巨怪（Boss）：巨獸咆哮＋低頻心跳與轟鳴
def sculk_monstrosity(rng):
    s = {}
    low = B.load_samples("sculk_monstrosity", "ambient")[0]
    big = B.load_samples("sculk_monstrosity", "special")
    sea = max(big, key=len)
    lion = min(big, key=len)
    for i in (1, 2):
        out = B.mix((sh(cut(low, rng, 1.2, 2.0, 0.2), -4 - i), 0.8), (heartbeat(rng, 4), 0.9))
        s[f"ambient{i}"] = B.finish(out, wet=0.3, size=1.3, lp=3000, peak=-4)
    s["roar1"] = B.finish(B.mix((sh(sea, -3), 1.0), (sh(lion, -5), 0.6), (B.rumble(4.0, rng, 120), 0.5)), wet=0.45, size=1.6, peak=-1)
    s["slam1"] = B.finish(B.mix((sh(cut(lion, rng, 0.5, 0.8, 0.3), -7), 0.7), (B.thud(rng, 1.4), 1.0), (B.rumble(1.2, rng), 0.8)), wet=0.3, peak=-1)
    out = B.mix((B.glide_shift(cut(sea, rng, 1.5, 2.0, 0.2), -8, 2), 1.0), (whoosh(1.8, rng, 200, 3000), 0.4))
    s["sonic_charge1"] = B.finish(out, wet=0.4, size=1.4, peak=-2)
    s["sonic_release1"] = B.finish(B.mix((sh(cut(lion, rng, 0.6, 1.0, 0.3), -2), 1.0), (snap(rng, 0.4, 300, 6000), 0.8)), wet=0.4, peak=-1)
    s["charge1"] = B.finish(B.mix((sh(cut(sea, rng, 1.0, 1.5, 0.2), -5), 1.0), (B.rumble(1.5, rng), 0.8)), wet=0.3, peak=-2)
    s["mega_punch1"] = B.finish(B.mix((sh(cut(low, rng, 0.4, 0.6, 0.3), -6), 0.8), (B.thud(rng, 1.0), 1.0)), wet=0.25, peak=-1)
    s["swipe1"] = B.finish(B.mix((sh(cut(lion, rng, 0.4, 0.6, 0.3), -4), 1.0), (whoosh(0.6, rng, 300, 2500), 0.6)), wet=0.2, peak=-2)
    out = B.mix((B.glide_shift(cut(sea, rng, 1.2, 1.8, 0.2), -6, -2), 0.8))
    for k in range(4):
        S.place(out, 0.4 * B.thud(rng, 0.5), 0.2 + 0.3 * k)
    s["cube_barrage1"] = B.finish(out, wet=0.3, peak=-2)
    out = B.mix((sh(cut(low, rng, 1.0, 1.6, 0.2), -8), 1.0))
    for k in range(4):
        S.place(out, 0.25 * S.bell(B.note(B.A3, -5 + 3 * k), 1.4, rng, bright=0.7), 0.3 + 0.2 * k)
    s["catalyst1"] = B.finish(out, wet=0.45, size=1.4, peak=-3)
    for i in (1, 2):
        s[f"attack{i}"] = B.finish(sh(cut(low, rng, 0.3, 0.5, 0.3), -5 + i), wet=0.2, peak=-3)
    for i in (1, 2):
        s[f"hurt{i}"] = B.finish(sh(cut(lion, rng, 0.3, 0.5, 0.3), -3 - i), wet=0.2, peak=-3)
    out = B.mix((B.glide_shift(sh(sea, -6), -4, 0), 1.0), (heartbeat(rng, 6, 0.24, 40), 1.0), (B.rumble(5.0, rng, 100), 0.6))
    s["phase1"] = B.finish(out, wet=0.5, size=1.8, peak=-1)   # 進入第二階段：心跳加速、咆哮、四周變暗
    out = B.mix((B.glide_shift(sea, -2, -12), 1.0), (B.rumble(len(sea) / S.SR, rng, 120), 0.6), (heartbeat(rng, 2, 0.6), 0.6))
    s["death1"] = B.finish(out, wet=0.5, size=1.8, peak=-2)
    return s


# ---------------------------------------------------------------- recipe table + subtitles
NAMES = {   # mob: (English, 中文)
    "pollinator": ("Pollinator", "授粉者"), "roamroot": ("Roamroot", "漫遊根"), "bloombud": ("Bloombud", "盛開花苞"),
    "sentinel": ("Sentinel", "哨兵"), "stalker": ("Stalker", "追蹤者"), "hunter": ("Hunter", "獵人"),
    "trapper": ("Trapper", "陷阱師"), "dartback": ("Dartback", "飛鏢背"), "prickle": ("Prickle", "刺球"),
    "nester": ("Nester", "築巢者"), "seedling": ("Seedling", "幼苗"), "sprout": ("Sprout", "萌芽"),
    "scavenger": ("Scavenger", "清道夫"), "hurler": ("Hurler", "投擲者"), "wobble": ("Wobble", "搖晃怪"),
    "lootkin": ("Lootkin", "掠奪精"), "monarch": ("Monarch", "君王"), "sculk_monstrosity": ("Sculk Monstrosity", "幽匿巨怪"),
}
VERBS = {   # sound kind: (English verb phrase, 中文)
    "ambient": ("calls", "叫聲"), "hurt": ("hurts", "受傷"), "death": ("dies", "死亡"), "attack": ("attacks", "攻擊"),
    "sting": ("stings", "螫人"), "pollinate": ("pollinates", "授粉"), "stomp": ("stomps", "跺地"), "bite": ("bites", "咬合"),
    "slash": ("slashes", "劈砍"), "throw": ("throws", "投擲"), "mark": ("marks its prey", "標記獵物"),
    "leap": ("leaps", "跳躍"), "set_trap": ("sets a trap", "佈置陷阱"), "throw_net": ("throws a net", "丟網"),
    "shoot": ("shoots", "射刺"), "charge": ("charges", "衝撞"), "bristle": ("bristles", "豎刺"),
    "summon": ("summons", "召喚"), "shockwave": ("sends a shockwave", "震波"), "dash_strike": ("dashes", "突進"),
    "hover_loop": ("hovers", "盤旋"), "calamity": ("calls down calamity", "天災"), "heel_stomp": ("stomps", "踏地"),
    "roar": ("roars", "咆哮"), "slam": ("slams", "重擊"), "sonic_charge": ("gathers sound", "聚集聲波"),
    "sonic_release": ("unleashes sound", "釋放聲波"), "mega_punch": ("punches", "重拳"), "swipe": ("swipes", "橫掃"),
    "cube_barrage": ("hurls blocks", "投擲方塊"), "catalyst": ("grows catalysts", "生出觸媒"),
    "alarm": ("swarm is angered", "群起激怒"), "vanish": ("fades into darkness", "隱入黑暗"), "backstab": ("backstabs", "背刺"),
    "block": ("blocks with its shell", "背甲格擋"), "bleed": ("draws blood", "咬出血"), "alert": ("alerts its kin", "呼叫同伴"),
    "burst": ("bursts", "炸開"), "rally": ("rallies its brood", "激怒幼體"), "flee": ("flees", "逃跑"),
    "echo": ("splits off an echo", "分出鏡像"), "phase": ("awakens", "狂暴"), "guard_break": ("breaks a shield", "劈碎盾牌"),
}
RECIPES = {   # name -> (recipe, asset folder, seed)
    m: (globals()[m], f"mob/{m}", 41 + i) for i, m in enumerate(NAMES)
}


def events(name, sounds):
    en, zh = NAMES[name]
    kinds = []
    for k in sounds:
        kind = k.rstrip("0123456789")
        if kind not in kinds:
            kinds.append(kind)
    return [(f"entity.{name}.{k}", k, f"{en} {VERBS[k][0]}", f"{zh}{VERBS[k][1]}", {}) for k in kinds]
