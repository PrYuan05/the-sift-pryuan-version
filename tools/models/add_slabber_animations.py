"""Only tongue licking effect for slabber (no head or body bobbing).
"""
import json, shutil, datetime
from pathlib import Path

P = Path(".")
STAMP = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
BK = P / ".texture_backups" / f"{STAMP}_slabber_anims"
BK.mkdir(parents=True, exist_ok=True)

anim_path = P / "src/main/resources/assets/pysift/geckolib/animations/entity/slabber.animation.json"
shutil.copy2(anim_path, BK / anim_path.name)

data = json.loads(anim_path.read_text(encoding="utf-8"))
anims = data.setdefault("animations", {})

# Licking effect: purely tongue bone, head stays completely steady
lick_animation = {
    "animation_length": 1.4,
    "bones": {
        "tongue": {
            "rotation": {
                "0.0": [0, 0, 0],
                "0.2": [-35, 0, 0],
                "0.45": [-45, 0, 0],
                "0.7": [-12, 0, 0],
                "0.9": [-42, 0, 0],
                "1.1": [-20, 0, 0],
                "1.4": [0, 0, 0]
            }
        }
    }
}

anims["animation.slabber.eat"] = lick_animation
anims["animation.slabber.sniff"] = {
    "animation_length": 0.8,
    "bones": {
        "tongue": {
            "rotation": {
                "0.0": [0, 0, 0],
                "0.25": [-30, 0, 0],
                "0.5": [-15, 0, 0],
                "0.8": [0, 0, 0]
            }
        }
    }
}
anims.pop("animation.slabber.shake", None)

anim_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"Updated {anim_path}: tongue-only lick animation, removed head/body wobbling.")
