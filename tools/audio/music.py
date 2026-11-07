"""Boss-fight music for The Sift, fully synthesised (imported by build_sounds.py, which sets B).

Each track is a loop of about 70 seconds built on a small sequencer: drums, bass, a sustained pad, a lead melody
and the boss's own colour (the Harmonizer's choir, the Monarch's brass and timpani, the Sculk Monstrosity's
heartbeat and sculk chimes). The game plays it while a boss is near (client/BossMusic.java).
"""
import numpy as np

import synth as S

B = None


def kick(rng, seconds=0.45, hi=110, lo=42):
    n = int(seconds * S.SR)
    t = np.arange(n) / S.SR
    f = lo + (hi - lo) * np.exp(-t / 0.04)
    return np.sin(2 * np.pi * np.cumsum(f) / S.SR) * np.exp(-t / 0.16)


def snare(rng, seconds=0.25):
    n = int(seconds * S.SR)
    t = np.arange(n) / S.SR
    return (0.8 * S.noise_band(n, 1200, 7000, rng) + 0.4 * np.sin(2 * np.pi * 190 * t)) * np.exp(-t / 0.07)


def timpani(freq, rng, seconds=1.4):
    n = int(seconds * S.SR)
    t = np.arange(n) / S.SR
    f = freq * (1 + 0.04 * np.exp(-t / 0.05))
    x = np.sin(2 * np.pi * np.cumsum(f) / S.SR) + 0.3 * np.sin(2 * np.pi * np.cumsum(f * 1.5) / S.SR)
    return (x + 0.25 * S.noise_band(n, 60, 600, rng) * np.exp(-t / 0.05)) * np.exp(-t / 0.5)


def brass(freq, seconds, bright=2600):
    n = int(seconds * S.SR)
    f0 = np.full(n, freq) * (1 + 0.004 * np.sin(2 * np.pi * 5.2 * np.arange(n) / S.SR))
    x = S.glottal(f0, rolloff=0.7, max_hz=8000)
    return S.lowpass(x, bright) * S.adsr(n, 0.06, 0.15, 1.2)


def bass(freq, seconds):
    n = int(seconds * S.SR)
    f0 = np.full(n, freq)
    return S.lowpass(S.glottal(f0, rolloff=1.0, max_hz=3000), 600) * S.adsr(n, 0.01, 0.12, 1.5)


def pad(freqs, seconds):
    n = int(seconds * S.SR)
    out = np.zeros(n)
    for f in freqs:
        out += S.organ(np.full(n, f), ((1, 1.0), (2, 0.4), (3, 0.2), (4, 0.1)))
    return out * S.adsr(n, 0.5, 0.6, 1.5) / max(1, len(freqs))


def hz(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


class Track:
    def __init__(self, bpm, bars, beats=4):
        self.beat = 60.0 / bpm
        self.bar = self.beat * beats
        self.n = int(bars * self.bar * S.SR) + int(3 * S.SR)
        self.layers = {}
        self.length = bars * self.bar

    def add(self, layer, x, at):
        buf = self.layers.setdefault(layer, np.zeros(self.n))
        S.place(buf, x, at)

    def render(self, gains, wet=0.25, size=1.3):
        out = np.zeros(self.n)
        for name, buf in self.layers.items():
            out += gains.get(name, 1.0) * buf / (np.max(np.abs(buf)) + 1e-9)
        out = S.reverb(out, wet=wet, size=size)
        n = int(self.length * S.SR)
        tail = out[n:n + int(2.5 * S.SR)]   # fold the reverb tail back onto the start so the loop is seamless
        out = out[:n].copy()
        out[: len(tail)] += tail * np.linspace(1, 0, len(tail))
        return S.normalise(out, -2)


def progression(track, chords, rng, root_oct=36, drums="march", lead=None, lead_layer="lead", lead_voice=None,
                chord_layer="pad", choir_layer=False, intensity=None):
    """chords: list of (root midi offset, [chord tones]) one per bar; lead: list of (bar, beat, midi, beats)."""
    bars = len(chords)
    for b, (root, tones) in enumerate(chords):
        t0 = b * track.bar
        hot = intensity[b] if intensity else 1.0
        freqs = [hz(root_oct + 24 + root + x) for x in tones]
        track.add(chord_layer, pad(freqs, track.bar + 0.4), t0)
        if choir_layer:
            c = B.choir(rng, [root + x - 12 for x in tones], track.bar + 0.3, base=hz(57), vowels=("ah", "oh"), attack=0.4, release=0.5)
            track.add("choir", c, t0)
        for k in range(int(track.bar / track.beat)):
            at = t0 + k * track.beat
            note_len = track.beat * (0.9 if k % 2 == 0 else 0.45)
            track.add("bass", bass(hz(root_oct + root + (12 if k == 3 else 0)), note_len), at)
            if drums == "march":
                track.add("kick", kick(rng), at) if k % 2 == 0 else track.add("snare", snare(rng), at)
                if hot > 1.0:
                    track.add("snare", 0.5 * snare(rng, 0.15), at + track.beat / 2)
            elif drums == "heart":
                track.add("kick", kick(rng, 0.5, 80, 32), at)
                track.add("kick", 0.7 * kick(rng, 0.5, 80, 32), at + track.beat * 0.28)
            elif drums == "drive":
                track.add("kick", kick(rng), at)
                track.add("snare", 0.6 * snare(rng, 0.12), at + track.beat / 2)
                if k % 2 == 1:
                    track.add("snare", snare(rng), at)
    for bar, beat, midi, length in lead or ():
        x = (lead_voice or brass)(hz(midi), length * track.beat)
        track.add(lead_layer, x, bar * track.bar + beat * track.beat)
    return track


def motif(bars, notes, start=0):
    """notes: per-bar list of (beat, midi, beats); repeated over `bars` starting at bar `start`."""
    out = []
    for i, bar in enumerate(bars):
        for beat, midi, length in notes[i % len(notes)]:
            out.append((start + bar, beat, midi, length))
    return out


# ---------------------------------------------------------------- 調和者：柳絮林地，一整團歌者
def boss_harmonizer(rng):
    tr = Track(bpm=96, bars=28)
    i, iv, vi, v, iii = (0, [0, 3, 7]), (5, [0, 3, 7]), (-4, [0, 4, 7]), (7, [0, 4, 7]), (3, [0, 4, 7])
    chords = [i, i, vi, vi, iv, iv, v, v] * 3 + [i, vi, v, i]
    heat = [0.8] * 8 + [1.0] * 8 + [1.2] * 8 + [1.0] * 4
    def sung(freq, seconds):
        return B.soft_voice(S.vibrato(np.full(int(seconds * S.SR), freq), rate=5.0, depth=0.006, rng=rng), rng)[: int(seconds * S.SR)] \
            * S.adsr(int(seconds * S.SR), 0.08, 0.25)
    phrase = [[(0, 69, 1.5), (1.5, 72, 0.5), (2, 71, 1), (3, 69, 1)], [(0, 67, 3), (3, 64, 1)],
              [(0, 65, 1.5), (1.5, 69, 0.5), (2, 72, 2)], [(0, 71, 4)]]
    lead = motif(range(8, 24), phrase)
    progression(tr, chords, rng, root_oct=33, drums="drive", lead=lead, lead_voice=sung, choir_layer=True, intensity=heat)
    return {"track1": tr.render({"pad": 0.35, "choir": 0.55, "bass": 0.55, "kick": 0.7, "snare": 0.35, "lead": 0.6}, wet=0.35, size=1.6)}


# ---------------------------------------------------------------- 君王：琥珀沙丘的王，銅管與定音鼓的進行曲
def boss_monarch(rng):
    tr = Track(bpm=112, bars=32)
    i, vi, vii, iv, v = (0, [0, 3, 7]), (-4, [0, 4, 7]), (-2, [0, 4, 7]), (5, [0, 3, 7]), (7, [0, 4, 7, 10])
    chords = [i, i, vi, vii] * 2 + [iv, iv, v, v, i, vi, iv, v] + [i, vii, vi, v] * 2 + [iv, v, i, i]
    heat = [1.0] * 16 + [1.3] * 16
    fanfare = [[(0, 62, 0.75), (0.75, 62, 0.25), (1, 67, 1), (2, 70, 1.5), (3.5, 69, 0.5)],
               [(0, 67, 2), (2, 65, 1), (3, 62, 1)], [(0, 63, 1.5), (1.5, 65, 0.5), (2, 67, 2)], [(0, 66, 3), (3, 62, 1)]]
    lead = motif(range(4, 32), fanfare)
    progression(tr, chords, rng, root_oct=31, drums="march", lead=lead, intensity=heat)
    for b, (root, _) in enumerate(chords):   # 定音鼓：每小節開頭兩下
        tr.add("timp", timpani(hz(31 + root + 12), rng), b * tr.bar)
        tr.add("timp", 0.7 * timpani(hz(31 + root + 19), rng), b * tr.bar + 2.5 * tr.beat)
    return {"track1": tr.render({"pad": 0.35, "bass": 0.5, "kick": 0.5, "snare": 0.4, "lead": 0.75, "timp": 0.8}, wet=0.3, size=1.5)}


# ---------------------------------------------------------------- 幽匿巨怪：深處的心跳、轟鳴與幽匿的叮噹
def boss_sculk_monstrosity(rng):
    tr = Track(bpm=84, bars=24)
    i, ii, vi, v = (0, [0, 3, 7]), (1, [0, 4, 7]), (-4, [0, 3, 7]), (-5, [0, 3, 6])
    chords = [i, i, ii, i, vi, vi, v, v] * 3
    progression(tr, chords, rng, root_oct=26, drums="heart")
    for b in range(len(chords)):   # 低頻轟鳴與遠處的幽匿叮噹（和聲小調的走音）
        tr.add("rumble", B.rumble(tr.bar + 0.5, rng, 90), b * tr.bar)
        if b % 2 == 1:
            for k, st in enumerate(rng.choice([0, 1, 3, 7, 8, 11], 3)):
                tr.add("chime", S.bell(hz(74 + st), 2.2, rng, bright=0.8), b * tr.bar + (0.5 + 1.2 * k) * tr.beat)
    groan = [[(0, 50, 3), (3, 49, 1)], [(0, 46, 4)], [(0, 50, 2), (2, 53, 2)], [(0, 52, 4)]]
    for bar, beat, midi, length in motif(range(8, 24), groan):
        tr.add("lead", brass(hz(midi), length * tr.beat, bright=900), bar * tr.bar + beat * tr.beat)
    return {"track1": tr.render({"pad": 0.3, "bass": 0.6, "kick": 0.9, "rumble": 0.4, "chime": 0.35, "lead": 0.5}, wet=0.45, size=1.8)}


RECIPES = {
    "boss_harmonizer": (boss_harmonizer, "music/boss_harmonizer", 71),
    "boss_monarch": (boss_monarch, "music/boss_monarch", 72),
    "boss_sculk_monstrosity": (boss_sculk_monstrosity, "music/boss_sculk_monstrosity", 73),
}
# music: no subtitle (en None), streamed
EVENTS = {name: [(f"music.{name.replace('_', '.', 1)}", "track", None, None, {"stream": True})] for name in RECIPES}
