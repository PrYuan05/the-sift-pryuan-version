"""Background music for the three underground layers of The Sift (imported by build_sounds.py, which sets B).

Two ways to make a layer's music (the second is the one installed):
  * sourced (RECIPES): CC0 tracks found on OpenGameArt, kept in sound_sources/music/<layer>/track_* (not in git; the
    download list is sources.txt beside them, credited in sounds/CREDITS.md). Cut, faded and levelled here, never shipped
    unmodified. The tracks were picked by analysing what each place should sound like (see each recipe).
  * synthesised (SYNTH_RECIPES, folder music_synth/, not wired into the game): original pieces made like the Singers' voices

The synthesised pieces are original music, fully synthesised, in the way the Singers' voices were made (see the Singer notes in build_sounds.py:
a very steady pitch with almost no vibrato, soft attack, several voices at once, a long reverb, and a layer of pipe organ
that never moves under the "shout" vowels). Nothing is sampled. Each layer is a different place the same choir sings in:

  withered_hollows  a lone voice in a cracked, dry stone: one note at a time with long silences, a thin organ breath,
                    dust and a dry drip; low minor pentatonic; short dry-ish reverb (the cracks are small)
  resonant_vaults   the choir in its great hall: four voices on slowly turning chords (major pentatonic), crystal bells
                    walking up the chord, an organ pedal, a very long reverb
  spirit_deeps      deep and slow: a low minor choir sinking in pitch, a heavy organ pedal, liquid pulses and bubbles,
                    a rare high tuning-fork ring

Two tracks per layer. The game streams them through the biome's background_music (tools/worldgen/build_sift_audio.py).
"""
import numpy as np

import synth as S

B = None
SR = S.SR


def _out(seconds):
    return np.zeros((int(seconds * SR), 2))


def put(dst, src, at, gain=1.0, pan=0.0):
    """Mix a mono clip into a stereo bed at `at` seconds, equal-power pan (-1 left .. +1 right)."""
    i = int(at * SR)
    j = min(len(dst), i + len(src))
    if j <= i:
        return
    angle = (pan + 1) * np.pi / 4
    dst[i:j, 0] += gain * np.cos(angle) * src[: j - i]
    dst[i:j, 1] += gain * np.sin(angle) * src[: j - i]


def reverb2(x, wet, size):
    """Stereo reverb: the two channels get slightly different room sizes so the tail is wide, not a mono blob."""
    left = S.reverb(x[:, 0], wet=wet, size=size)
    right = S.reverb(x[:, 1], wet=wet, size=size * 1.13)
    n = max(len(left), len(right))
    out = np.zeros((n, 2))
    out[: len(left), 0] = left
    out[: len(right), 1] = right
    return out


def pad(rng, chord, seconds, base, vowels, attack=2.2, release=3.0, detune=0.0):
    """A choir chord (mono, normalised)."""
    x = B.choir(rng, chord, seconds, base=base, vowels=vowels, attack=attack, release=release, detune=detune)
    return x / (np.max(np.abs(x)) + 1e-9)


def drone(freq, seconds, swell=0.5):
    """A pipe-organ pedal that breathes slowly in and out."""
    n = int(seconds * SR)
    t = np.arange(n) / SR
    x = S.organ(np.full(n, freq))
    breath = 0.65 + 0.35 * np.sin(2 * np.pi * swell / seconds * t * 2 + 1.0)
    return x * breath * S.adsr(n, attack=seconds * 0.15, release=seconds * 0.2, curve=1.5) / (np.max(np.abs(x)) + 1e-9)


def bell_note(rng, freq, seconds=3.2, bright=0.8):
    b = S.bell(freq, seconds, rng, bright=bright)
    return b / (np.max(np.abs(b)) + 1e-9)


def finish(x, rms_db, fade_in=3.0, fade_out=5.0):
    """Level to a target RMS, a gentle limiter, and fades so the restart is clean."""
    n_in, n_out = int(fade_in * SR), int(fade_out * SR)
    x = x.copy()
    x[:n_in] *= np.linspace(0, 1, n_in)[:, None]
    x[-n_out:] *= np.linspace(1, 0, n_out)[:, None] ** 2
    x *= 10 ** (rms_db / 20) / (np.sqrt(np.mean(x ** 2)) + 1e-12)
    peak = np.max(np.abs(x))
    if peak > 0.9:
        x = np.tanh(x / 0.9) * 0.9
    return x


def pick(rng, scale, base, octave=0):
    return B.note(base, scale[rng.integers(0, len(scale))] + 12 * octave)


# ----------------------------------------------------------------------------------------------- withered hollows
MINOR_PENT = [0, 3, 5, 7, 10]


def withered(rng, steps, total=78.0, whisper=True):
    """A lone voice: one note at a time. `steps` = [(start s, semitones above A2, length s)]."""
    bed = _out(total + 6)
    base = B.A3 / 2
    put(bed, drone(base, total, 0.4), 0.0, gain=0.12, pan=0.0)            # a thin organ breath, hardly there
    for at, st, length in steps:
        v = pad(rng, [st], length, base * 2, ("oo", "oh"), attack=length * 0.4, release=length * 0.45)
        put(bed, v, at, gain=0.55, pan=rng.uniform(-0.5, 0.5))
        if rng.random() < 0.45:                                           # a second, hollow voice a fifth below, late
            w = pad(rng, [st - 5], length * 0.7, base * 2, ("mm", "oo"), attack=length * 0.3, release=length * 0.35)
            put(bed, w, at + length * 0.35, gain=0.3, pan=rng.uniform(-0.8, 0.8))
    for k in range(int(total // 11)):                                     # dust, a lonely drip, wind in the cracks
        at = 4 + k * 11 + rng.uniform(0, 5)
        put(bed, B.drips(rng, 1, 1100, 2300, 0.5, 1.8), at, gain=0.35, pan=rng.uniform(-1, 1))
        if whisper and k % 2 == 0:
            put(bed, B.whistle(rng, 4.5, (rng.uniform(450, 650), rng.uniform(380, 520)), gain=0.4), at + 3.0, gain=0.22, pan=rng.uniform(-1, 1))
    for k in range(3):                                                    # a very rare high crystal, far away
        put(bed, bell_note(rng, pick(rng, MINOR_PENT, B.A3 * 2, 1), 3.5, 0.6), 18 + k * 21 + rng.uniform(0, 6), gain=0.16, pan=rng.uniform(-1, 1))
    return finish(reverb2(bed, 0.42, 1.2), -23.0)


def withered_hollows_hollow(rng):
    notes = [(2.0, 7, 9.0), (13.0, 5, 8.0), (24.0, 3, 10.0), (37.0, 0, 9.0), (49.0, 3, 8.0), (59.0, 5, 7.0), (68.0, 0, 9.0)]
    return {"track1": withered(rng, notes)}


def withered_hollows_dust(rng):
    notes = [(4.0, 10, 8.0), (15.0, 7, 9.0), (28.0, 10, 7.0), (38.0, 5, 10.0), (51.0, 3, 9.0), (63.0, 7, 8.0), (72.0, 0, 7.0)]
    return {"track1": withered(rng, notes, total=80.0, whisper=False)}


# ----------------------------------------------------------------------------------------------- resonant vaults
def vault(rng, chords, seconds_per, cycles=2, base=None, vowels=("oo", "ah", "oo"), bell_every=1.3):
    """The choir in its hall: voices on slowly turning chords, a pedal, bells walking up each chord."""
    base = base or B.A3
    total = len(chords) * seconds_per * cycles
    bed = _out(total + 8)
    t0 = 0.0
    for c in range(cycles):
        for chord in chords:
            v = pad(rng, chord, seconds_per + 3.0, base, vowels, attack=2.4, release=3.2, detune=0.02)
            put(bed, v, t0, gain=0.75, pan=rng.uniform(-0.35, 0.35))
            for side, st in ((-0.7, chord[1]), (0.7, chord[2])):          # two of the voices again, wide, a little late
                w = pad(rng, [st], seconds_per + 2.0, base, ("oo", "mm"), attack=2.8, release=3.0)
                put(bed, w, t0 + 0.4, gain=0.3, pan=side)
            put(bed, drone(base / 2 * 2 ** (chord[0] / 12), seconds_per + 3.0, 0.5), t0, gain=0.18, pan=0.0)
            ts = t0 + 1.2
            tones = [chord[0] + 12, chord[1] + 12, chord[2] + 12, chord[-1] + 12, chord[2] + 24, chord[1] + 24]
            for k in range(int((seconds_per - 1.5) / bell_every)):        # bells climb, then thin out
                st = tones[k % len(tones)]
                put(bed, bell_note(rng, B.note(base, st), 3.6, 0.95), ts + k * bell_every * rng.uniform(0.85, 1.15),
                    gain=0.20 * (0.55 + 0.45 * rng.random()), pan=rng.uniform(-0.9, 0.9))
            t0 += seconds_per
    return finish(reverb2(bed, 0.55, 2.0), -19.0)


def resonant_vaults_hall(rng):
    return {"track1": vault(rng, [[0, 4, 7, 14], [-3, 4, 9, 12], [-7, 0, 5, 9], [-5, 2, 7, 11]], 9.0)}


def resonant_vaults_echo(rng):
    return {"track1": vault(rng, [[0, 5, 9, 12], [-2, 5, 10, 14], [-5, 2, 7, 12], [-7, 0, 5, 10]], 10.0, bell_every=1.8,
                            vowels=("mm", "oo", "ah"))}


# ----------------------------------------------------------------------------------------------- spirit deeps
def deeps(rng, chords, seconds_per, cycles=2, sink=-2.0, swoosh=True):
    """Deep and slow: a low minor choir that sinks, a heavy pedal, liquid pulses and bubbles, a rare high fork."""
    base = B.A3 / 4
    total = len(chords) * seconds_per * cycles
    bed = _out(total + 8)
    t0 = 0.0
    for c in range(cycles):
        for chord in chords:
            n = seconds_per + 4.0
            x = B.choir(rng, chord, n, base=base * 2, vowels=("oo", "oh", "mm"), attack=3.2, release=4.0, bend=(0.0, sink * 0.35))
            put(bed, x / (np.max(np.abs(x)) + 1e-9), t0, gain=0.7, pan=rng.uniform(-0.3, 0.3))
            put(bed, drone(base * 2 ** (chord[0] / 12), n, 0.3), t0, gain=0.35, pan=0.0)
            t0 += seconds_per
    for k in range(int(total // 5)):                                      # liquid pulses: low gulps coming up out of the deep
        put(bed, B.bubbles(rng, 2, 1.2, 70, 170), 2 + k * 5 + rng.uniform(0, 3), gain=0.28, pan=rng.uniform(-1, 1))
    for k in range(int(total // 14)):
        put(bed, B.trickle(rng, 2.6), 6 + k * 14 + rng.uniform(0, 5), gain=0.18, pan=rng.uniform(-1, 1))
    for k in range(3):                                                    # a tuning fork ringing far above
        put(bed, B.fork(B.note(B.A3 * 2, B.SCALE[rng.integers(0, 7)]), 3.6, rng, beat=rng.uniform(1.0, 2.5)),
            14 + k * 24 + rng.uniform(0, 8), gain=0.10, pan=rng.uniform(-1, 1))
    if swoosh:                                                            # a soul rising through the liquid, once
        s = S.noise_band(int(2.4 * SR), 200, 1800, rng) * S.adsr(int(2.4 * SR), 1.0, 1.2)
        put(bed, B.glide_shift(s, -7, 6), total * 0.55, gain=0.16, pan=rng.uniform(-0.6, 0.6))
    return finish(reverb2(bed, 0.55, 1.6), -20.0)


def spirit_deeps_depth(rng):
    return {"track1": deeps(rng, [[0, 7, 12, 15], [-2, 5, 10, 14], [-4, 3, 7, 12], [-7, 0, 5, 10]], 10.0)}


def spirit_deeps_current(rng):
    return {"track1": deeps(rng, [[0, 3, 7, 12], [-5, 2, 7, 10], [-2, 5, 9, 12], [-7, 0, 3, 7]], 11.0, sink=-3.0)}


def withered_hollows_music(rng):
    return {"track1": withered_hollows_hollow(rng)["track1"], "track2": withered_hollows_dust(rng)["track1"]}


def resonant_vaults_music(rng):
    return {"track1": resonant_vaults_hall(rng)["track1"], "track2": resonant_vaults_echo(rng)["track1"]}


def spirit_deeps_music(rng):
    return {"track1": spirit_deeps_depth(rng)["track1"], "track2": spirit_deeps_current(rng)["track1"]}


SYNTH_RECIPES = {
    "music_withered_hollows_synth": (withered_hollows_music, "music_synth/withered_hollows", 81),
    "music_resonant_vaults_synth": (resonant_vaults_music, "music_synth/resonant_vaults", 82),
    "music_spirit_deeps_synth": (spirit_deeps_music, "music_synth/spirit_deeps", 83),
}


# ----------------------------------------------------------------------------------------------- sourced (CC0) tracks
def load_sources(layer):
    """sound_sources/music/<layer>/track_* as stereo float arrays at SR, in file-name order."""
    import soundfile as sf
    from scipy.signal import resample_poly
    out = []
    for f in sorted((B.SOURCES / "music" / layer).glob("track_*")):
        x, sr = sf.read(str(f), always_2d=True)
        x = np.repeat(x[:, :1], 2, axis=1) if x.shape[1] == 1 else x[:, :2]
        if sr != SR:
            x = np.stack([resample_poly(x[:, c], SR, sr) for c in range(2)], axis=1)
        out.append(x.astype(np.float64))
    assert out, f"no tracks in sound_sources/music/{layer}"
    return out


def trim_silence(x, floor_db=-60.0):
    level = np.abs(x).max(axis=1)
    loud = np.nonzero(level > 10 ** (floor_db / 20) * level.max())[0]
    return x[loud[0]: loud[-1] + 1]


def sourced(layer, rms_db, fade_in=3.0, fade_out=5.0, max_seconds=150.0):
    """Cut (trim silence, at most max_seconds), fade, level and limit each downloaded track of a layer."""
    def make(rng):
        tracks = {}
        for i, x in enumerate(load_sources(layer), 1):
            x = trim_silence(x)[: int(max_seconds * SR)]
            tracks[f"track{i}"] = finish(x, rms_db, fade_in, fade_out)
        return tracks
    return make


# Picked by analysing the places (measured, not guessed: centroid = spectral brightness, rms = loudness):
#  withered hollows (dry, cut off, wind in the cracks and a drip): IgnasD "Loopable Dungeon Ambience" (low wind and drips) and
#                    Creomoto "Dungeon Ambience" (a steady, quiet, empty bed) - ambience, almost no melody, leave room for the cave sounds
#  resonant vaults (the choir's hall, crystals): dgrannum22 "Cathedral" (choir and organ, slow) and messersm "Crystal Cave (song18)"
#                    (stone, bells and arpeggios)
#  spirit deeps (deep, slow, liquid): "Dark Cavern Ambient" 1 and 2 (very low, rumbling: spectral centroid ~270 Hz)
RECIPES = {
    "music_withered_hollows": (sourced("withered_hollows", -26.0), "music/withered_hollows", 81),
    "music_resonant_vaults": (sourced("resonant_vaults", -21.0), "music/resonant_vaults", 82),
    "music_spirit_deeps": (sourced("spirit_deeps", -22.0), "music/spirit_deeps", 83),
}
