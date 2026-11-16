"""Facial expressions for the Singer: one short `face_<name>` animation per voice line (tools/audio/build_sounds.py).

Only the `mouth` bone (scale: opens downward into an "O", see singer_mouth.py) and the two ears (z rotation) move, so
an expression can play on its own controller ("face", SingerEntity) on top of whatever the body is doing.
Ears: left ear z < 0 / right ear z > 0 = perked up (excited); the opposite sign = drooping (sad, scared).
Each animation is timed to its sound: the mouth opens on every syllable of the call.
Idempotent (rewrites every face_* animation); the animation file is backed up to .texture_backups/ first.
The Mourner (same model, see build_mourner.py) gets its own sadder set, MOURNER_FACES: ears always drooping, the mouth
trembling with sobs. build_mourner.py imports this file and writes them into mourner.animation.json.
Usage: python -I tools/models/singer_faces.py <project>
"""
import datetime
import json
import shutil
import sys
from pathlib import Path

P = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[2]
A = P / "src/main/resources/assets/pysift/geckolib/animations/entity/singer.animation.json"
BK = P / ".texture_backups" / (datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + "_singer_faces")

OPEN_X, OPEN_Y = 0.3, 1.6   # wide open = 1.3 x 2.6 (same as singer_mouth.py)


def fmt(t):
    return "0.0" if t == 0 else f"{t:.3f}".rstrip("0").rstrip(".")


def mouth(points, oo=False):
    """[(t, open 0..1)] -> mouth scale keys. oo = rounder, narrower mouth."""
    wx = 0.05 if oo else OPEN_X
    return {"scale": {fmt(t): [round(1 + wx * o, 3), round(1 + OPEN_Y * o, 3), 1] for t, o in points}}


def syllables(starts, length, wide=1.0, hold=0.35, trail=0.15):
    """Open on each syllable start, ease down, close at the end."""
    pts = [(0.0, 0.0)]
    for i, (s, d) in enumerate(starts):
        w = wide[i] if isinstance(wide, (list, tuple)) else wide
        pts += [(s + 0.06, w), (s + max(0.1, d * hold), w * 0.85), (s + max(0.14, d - 0.02), w * trail)]
    pts.append((length, 0.0))
    out, last = [], -1.0
    for t, o in sorted(pts):
        if t > last + 1e-3 and t <= length:
            out.append((round(t, 3), o))
            last = t
    return out


def ears(points):
    """[(t, angle)] angle > 0 = perked up, < 0 = drooping."""
    return ({"rotation": {fmt(t): [0, 0, -a] for t, a in points}},
            {"rotation": {fmt(t): [0, 0, a] for t, a in points}})


def tremble(start, end, base, amp, step=0.08):
    pts, t, sign = [], start, 1
    while t <= end:
        pts.append((round(t, 3), base + sign * amp))
        t += step
        sign = -sign
    return pts


def seq(notes, start=0.0):
    """[(semitones, seconds)] (as in build_sounds.call) -> [(start, seconds)]."""
    out, t = [], start
    for _, d in notes:
        out.append((t, d))
        t += d
    return out


def face(length, mouth_pts, ear_pts, oo=False):
    le, re = ears(ear_pts)
    return {"animation_length": length,
            "bones": {"mouth": mouth(mouth_pts, oo), "left_ear": le, "right_ear": re}}


FACES = {
    # 打招呼：兩聲往上，耳朵豎起來抖一下
    "greet": face(1.4, syllables(seq([(4, 0.22), (9, 0.5)]), 1.4, wide=[0.7, 1.0]),
                  [(0, 0), (0.15, 30), (0.3, 22), (0.45, 32), (0.9, 25), (1.4, 0)]),
    # 呼喚：兩聲往下，耳朵半豎、輕輕擺
    "beckon": face(1.4, syllables(seq([(7, 0.3), (4, 0.45)]), 1.4, wide=0.8),
                   [(0, 0), (0.2, 18), (0.5, 10), (0.8, 18), (1.4, 0)]),
    # 回應號角：長長的呼喊，嘴巴越張越大，最後一個音張到最大撐住；耳朵全豎
    "call": face(2.8, syllables(seq([(0, 0.35), (4, 0.3), (7, 0.3), (12, 0.9)]), 2.8, wide=[0.6, 0.7, 0.85, 1.0], hold=0.8),
                 [(0, 0), (0.3, 30), (1.0, 40), (2.0, 45), (2.8, 0)]),
    # 清掃：圓圓的「嗚」嘴，一口氣唱完；耳朵跟著上去又下來
    "sweep": face(1.8, [(0, 0), (0.1, 0.7), (0.8, 0.9), (1.4, 0.6), (1.8, 0)],
                  [(0, 0), (0.6, 25), (1.0, 10), (1.8, 0)], oo=True),
    # 召喚：最用力的吶喊，嘴張到最大很久，耳朵往上甩到底、還在抖
    "summon": face(3.6, [(0, 0), (0.1, 0.6), (0.45, 0.75), (0.85, 0.9), (1.25, 1.0), (2.7, 1.0), (3.2, 0.4), (3.6, 0)],
                   [(0, 0), (0.4, 40)] + tremble(1.2, 2.8, 50, 5) + [(3.6, 0)]),
    # 倒抽一口氣：嘴先張成小圓（吸氣），耳朵一下子垂下去貼住，發抖
    "gasp": face(1.9, [(0, 0), (0.05, 0.5), (0.2, 0.55), (0.25, 0.9), (0.5, 0.7), (1.0, 0.4), (1.9, 0)],
                 [(0, 0), (0.08, -35)] + tremble(0.2, 1.4, -38, 4) + [(1.9, 0)], oo=True),
    # 歡呼：五個跳音，嘴一開一合；耳朵跟著彈跳
    "cheer": face(1.8, syllables(seq([(0, 0.12), (4, 0.12), (7, 0.12), (12, 0.12), (16, 0.6)]), 1.8, wide=[0.7, 0.75, 0.8, 0.9, 1.0], hold=0.7),
                  [(0, 0), (0.12, 35), (0.24, 15), (0.36, 38), (0.48, 15), (0.6, 42), (1.2, 40), (1.8, 0)]),
    # 咯咯笑：很快的小開合，耳朵左右扭
    "giggle": face(1.5, syllables(seq([(12, 0.09), (14, 0.09), (12, 0.09), (16, 0.09), (12, 0.09), (19, 0.25)]), 1.5, wide=0.55, hold=0.5),
                   [(0, 0), (0.1, 20), (0.2, 5), (0.3, 25), (0.4, 5), (0.5, 28), (0.9, 18), (1.5, 0)]),
    # 道謝：先閉著嘴哼「嗯」，再張開「啊」；耳朵放鬆、微微垂
    "thanks": face(1.5, [(0, 0), (0.25, 0.08), (0.32, 0.6), (0.7, 0.7), (1.0, 0.3), (1.5, 0)],
                   [(0, 0), (0.3, -8), (0.8, 6), (1.5, 0)]),
    # 發抖嗚咽：嘴微張在抖，耳朵壓低、一直抖
    "unease": face(2.0, [(0, 0)] + [(round(0.1 + i * 0.1, 3), 0.25 + 0.1 * (i % 2)) for i in range(17)] + [(2.0, 0)],
                   [(0, 0), (0.15, -30)] + tremble(0.25, 1.7, -32, 5, 0.07) + [(2.0, 0)], oo=True),
    # 虛弱的嘆息：嘴鬆鬆地半開，耳朵垂到底
    "starve": face(2.2, [(0, 0), (0.3, 0.35), (1.2, 0.3), (2.2, 0)],
                   [(0, -15), (0.6, -45), (1.8, -45), (2.2, -15)], oo=True),
    # 受傷：嘴猛然張開，耳朵往下一縮又彈回來
    "hurt": face(0.8, [(0, 0), (0.05, 0.9), (0.25, 0.7), (0.6, 0.1), (0.8, 0)],
                 [(0, 0), (0.06, -30), (0.3, -20), (0.8, 0)]),
    # 平時的哼唱：三、四個音輕輕開合，耳朵跟著擺
    "ambient": face(3.0, syllables([(0.2, 0.55), (0.75, 0.55), (1.3, 0.55), (1.85, 1.0)], 3.0, wide=0.55, hold=0.8),
                    [(0, 0), (0.6, 12), (1.4, 4), (2.2, 12), (3.0, 0)]),
    # 歌裡的一個音（hum）：張一下再收
    "note": face(0.45, [(0, 0), (0.06, 0.85), (0.25, 0.65), (0.45, 0.05)], [(0, 0), (0.1, 8), (0.45, 0)]),
    # 從哀悼者變回歌者：嘴從小慢慢張到最大，耳朵從垂到底一路豎起來
    "reborn": face(3.2, syllables(seq([(-5, 0.35), (0, 0.3), (4, 0.3), (7, 0.3), (12, 1.0)]), 3.2, wide=[0.4, 0.55, 0.7, 0.85, 1.0], hold=0.8),
                   [(0, -40), (0.4, -30), (0.7, -10), (1.0, 10), (1.3, 30), (1.6, 45), (2.6, 40), (3.2, 0)]),
}


def sobbing(length, wide, start=0.1, rate=0.38):
    """Jerky little openings: a sob every `rate` s, each catching the breath."""
    pts, t = [(0.0, 0.0)], start
    while t + 0.2 < length:
        pts += [(round(t, 3), wide), (round(t + 0.12, 3), wide * 0.4), (round(t + 0.22, 3), wide * 0.75)]
        t += rate
    pts.append((length, 0.0))
    return pts


MOURNER_FACES = {
    # 啜泣：嘴一抽一抽地開合，耳朵垂著發抖
    "ambient": face(3.4, sobbing(3.4, 0.5), [(0, -25)] + tremble(0.1, 3.1, -32, 4, 0.1) + [(3.4, -25)], oo=True),
    # 看到玩家、開始哭著唱：嘴慢慢張到最大，耳朵垂到底
    "wail": face(3.0, [(0, 0), (0.5, 0.45), (1.0, 0.7), (1.6, 1.0), (2.5, 0.9), (3.0, 0)],
                 [(0, -25), (0.6, -45)] + tremble(1.0, 2.6, -48, 3) + [(3.0, -25)]),
    # 倒唱的一個音：抖著張一下
    "note": face(0.6, [(0, 0), (0.08, 0.7), (0.18, 0.45), (0.28, 0.65), (0.6, 0.05)], [(0, -25), (0.1, -32), (0.6, -25)], oo=True),
    # 受傷：猛然張開，耳朵更往下縮
    "hurt": face(0.9, [(0, 0), (0.05, 0.9), (0.3, 0.6), (0.9, 0)], [(0, -25), (0.06, -50), (0.4, -40), (0.9, -25)]),
    # 被安慰：嘴鬆開「嗯—啊」，耳朵慢慢抬起一點
    "soothe": face(2.2, [(0, 0), (0.4, 0.15), (0.6, 0.55), (1.4, 0.45), (2.2, 0)], [(0, -30), (0.8, -12), (1.6, -8), (2.2, -20)]),
    # 被號角安撫：哭聲收住，嘴慢慢閉上，耳朵放鬆
    "hush": face(2.4, [(0, 0.4), (0.4, 0.5), (1.0, 0.25), (1.8, 0.08), (2.4, 0)], [(0, -40), (1.0, -25), (2.4, -18)], oo=True),
}


def main():
    data = json.loads(A.read_text(encoding="utf-8"))
    BK.mkdir(parents=True, exist_ok=True)
    shutil.copy2(A, BK / A.name)
    anims = data["animations"]
    for k in [k for k in anims if k.startswith("animation.singer.face_")]:
        del anims[k]
    for name, anim in FACES.items():
        anims[f"animation.singer.face_{name}"] = anim
    A.write_text(json.dumps(data, ensure_ascii=False, indent="\t") + "\n", encoding="utf-8")
    print(f"wrote {len(FACES)} face animations to {A.relative_to(P)} (backup in {BK.relative_to(P)})")


if __name__ == "__main__":
    main()
