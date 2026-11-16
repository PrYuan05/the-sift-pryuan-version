"""Check that every pysift sound is wired up end to end.

Usage: python -I tools/audio/verify_sounds.py <project>      (exit 1 = problems)

1. every sound event in sounds.json is registered in Java (ModSounds constants, the biome loop, or the creature
   voices loaded from sounds.json), and every Java registration has an entry in sounds.json;
2. every pysift:<file> in sounds.json exists as .ogg;
3. every subtitle has en_us and zh_tw text;
4. every skill animation of a voiced creature has a sound (attack*, *_left fall back to attack);
5. every sound event a biome / data file references (pysift:...) exists.
"""
import json
import re
import sys
from pathlib import Path

P = Path(sys.argv[1]).resolve()
RES = P / "src/main/resources"
JAVA = P / "src/main/java/pryuan05/pysift"
sounds = json.loads((RES / "assets/pysift/sounds.json").read_text(encoding="utf-8"))
lang = {c: json.loads((RES / f"assets/pysift/lang/{c}.json").read_text(encoding="utf-8")) for c in ("en_us", "zh_tw")}
problems = []

ms = (JAVA / "sound/ModSounds.java").read_text(encoding="utf-8")
registered = set(re.findall(r'register\("([a-z0-9_.]+)"\)', ms))
biomes = re.search(r"SIFT_BIOMES = List\.of\(([^)]*)\)", ms, re.S).group(1)
for b in re.findall(r'"([a-z_]+)"', biomes):
    registered.add(f"music.the_sift.{b}")
    registered.update(f"ambient.the_sift.{b}.{p}" for p in ("loop", "mood", "additions"))
voiced = set(re.findall(r'"([a-z_]+)"', re.search(r"VOICED_MOBS = Set\.of\(([^)]*)\)", ms, re.S).group(1)))
for ev in sounds:
    parts = ev.split(".")
    if len(parts) == 3 and parts[0] == "entity" and parts[1] in voiced:
        registered.add(ev)

for ev in sorted(set(sounds) - registered):
    problems.append(f"sounds.json event not registered in Java: {ev}")
for ev in sorted(registered - set(sounds)):
    problems.append(f"Java registers {ev} but sounds.json has no entry")

for ev, data in sounds.items():
    for snd in data.get("sounds", []):
        name = snd["name"] if isinstance(snd, dict) else snd
        kind = snd.get("type", "file") if isinstance(snd, dict) else "file"
        if kind == "file" and name.startswith("pysift:"):
            f = RES / "assets/pysift/sounds" / (name.split(":", 1)[1] + ".ogg")
            if not f.exists():
                problems.append(f"{ev}: missing file {f.relative_to(P)}")
    sub = data.get("subtitle")
    if sub:
        for c in lang:
            if sub not in lang[c]:
                problems.append(f"{ev}: subtitle {sub} missing in {c}")

# 4. skill animations of voiced creatures
for mob in sorted(voiced):
    cls = "".join(w.capitalize() for w in mob.split("_")) + "Entity.java"
    src = (JAVA / "entity/mob" / cls).read_text(encoding="utf-8")
    m = re.search(r"skillAnimations\(\)\s*\{\s*return List\.of\(([^)]*)\)", src, re.S)
    anims = re.findall(r'"([a-z_0-9]+)"', m.group(1)) if m else []
    if "PysiftSwarmEntity" in src:
        anims = ["attack"]
    for kind in ["ambient", "hurt", "death"] + anims:
        if mob == "bloombud" and kind == "ambient":
            continue   # disguised as a flower: silent on purpose
        if f"entity.{mob}.{kind}" in sounds:
            continue
        if kind.startswith("attack") and f"entity.{mob}.attack" in sounds:
            continue
        problems.append(f"{mob}: no sound for '{kind}'")
    for kind in re.findall(r'voice\("([a-z_]+)"', src):
        if f"entity.{mob}.{kind}" not in sounds:
            problems.append(f"{mob}: code calls voice(\"{kind}\") but there is no entity.{mob}.{kind}")
swarm = (JAVA / "entity/mob/PysiftSwarmEntity.java").read_text(encoding="utf-8")
for kind in re.findall(r'voice\("([a-z_]+)"', swarm):
    for mob in ("seedling", "sprout"):
        if f"entity.{mob}.{kind}" not in sounds:
            problems.append(f"{mob}: swarm code calls voice(\"{kind}\") but there is no entity.{mob}.{kind}")

# 5. references from data / biome files
for f in list((RES / "data").rglob("*.json")):
    text = f.read_text(encoding="utf-8", errors="ignore")
    for ev in re.findall(r'"pysift:((?:music|ambient|entity|block|item)\.[a-z0-9_.]+)"', text):
        if ev not in sounds:
            problems.append(f"{f.relative_to(P)} references missing sound pysift:{ev}")

total = len(sounds)
files = sum(1 for _ in (RES / "assets/pysift/sounds").rglob("*.ogg"))
print(f"{total} sound events, {files} .ogg files, {len(voiced)} voiced creatures")
for p in problems:
    print("  !", p)
print("OK" if not problems else f"{len(problems)} problems")
sys.exit(1 if problems else 0)
