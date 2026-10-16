import re
from pathlib import Path

mobs_dir = Path("src/main/java/pryuan05/pysift/entity/mob")
for jf in sorted(mobs_dir.glob("*.java")):
    txt = jf.read_text(encoding="utf-8")
    skills = re.findall(r"skillAnimations\(\)\s*\{\s*return\s+List\.of\((.*?)\);", txt)
    has_death = "hasDeathAnimation()" in txt
    melee = re.findall(r"meleeAnimation\(\)\s*\{\s*return\s+(.*?);", txt)
    sk = skills[0] if skills else "[]"
    mel = melee[0] if melee else "None"
    print(f"{jf.stem}: skills={sk}, death={has_death}, melee={mel}")
