"""Boss-fight music for The Sift (imported by build_sounds.py, which sets B).

Each boss plays one royalty-free track from Pixabay Music (sound_sources/music/<boss>/, credited in
sounds/CREDITS.md), chosen by the user from three candidates each. The track is kept in stereo, resampled to
44.1 kHz, trimmed of leading / trailing silence, given a short fade so the restart is clean, and levelled to the
same loudness as the rest. The game plays it while a boss is near (client/BossMusic.java) and starts it again
when it ends.
"""
import numpy as np

import synth as S

B = None

TARGET_RMS_DB = -18.0   # roughly the loudness of the vanilla music discs


def load_stereo(boss, prefix):
    import soundfile as sf
    from scipy.signal import resample_poly
    files = [f for f in sorted((B.SOURCES / "music" / boss).glob("*.mp3")) if f.name.startswith(prefix)]
    assert len(files) == 1, (boss, prefix, files)
    x, sr = sf.read(str(files[0]), always_2d=True)
    if x.shape[1] == 1:
        x = np.repeat(x, 2, axis=1)
    x = x[:, :2]
    if sr != S.SR:
        x = np.stack([resample_poly(x[:, c], S.SR, sr) for c in range(2)], axis=1)
    return x


def trim_silence(x, floor_db=-50.0):
    level = np.abs(x).max(axis=1)
    loud = np.nonzero(level > 10 ** (floor_db / 20))[0]
    return x[loud[0]: loud[-1] + 1]


def prepare(x, fade_in=0.05, fade_out=1.5):
    x = trim_silence(x)
    n_in, n_out = int(fade_in * S.SR), int(fade_out * S.SR)
    x = x.copy()
    x[:n_in] *= np.linspace(0, 1, n_in)[:, None]
    x[-n_out:] *= np.linspace(1, 0, n_out)[:, None] ** 2
    rms = np.sqrt(np.mean(x ** 2))
    x *= 10 ** (TARGET_RMS_DB / 20) / (rms + 1e-12)
    peak = np.max(np.abs(x))
    if peak > 0.95:   # gentle limiter on the few peaks that would clip
        x = np.tanh(x / 0.95) * 0.95
    return x


# 調和者：柳絮林地，一整團歌者 -> 合唱管弦循環（sonican, Epic Choir Orchestral Music Loop），本來就做成循環
def boss_harmonizer(rng):
    return {"track1": prepare(load_stereo("boss_harmonizer", "sonican-epic-choir-orchestral-music-loop"), fade_out=0.3)}


# 君王：琥珀沙丘的王 -> 堅毅進行曲（studiokolomna, March of Resolve）
def boss_monarch(rng):
    return {"track1": prepare(load_stereo("boss_monarch", "studiokolomna-march-of-resolve"))}


# 幽匿巨怪：深處的最終 Boss -> 帝國的殞落（nickpanek, The Fall of Empires）
def boss_sculk_monstrosity(rng):
    return {"track1": prepare(load_stereo("boss_sculk_monstrosity", "nickpanek-the-fall-of-empires"))}


RECIPES = {
    "boss_harmonizer": (boss_harmonizer, "music/boss_harmonizer", 71),
    "boss_monarch": (boss_monarch, "music/boss_monarch", 72),
    "boss_sculk_monstrosity": (boss_sculk_monstrosity, "music/boss_sculk_monstrosity", 73),
}
# music: no subtitle (en None), streamed
EVENTS = {name: [(f"music.{name.replace('_', '.', 1)}", "track", None, None, {"stream": True})] for name in RECIPES}
