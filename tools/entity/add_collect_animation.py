"""Add "animation.echo_golem.collect" (Echo Golem absorbing a soul crystal block, see EchoGolemEntity.CollectCrystalGoal).
Usage: python -I tools/entity/add_collect_animation.py <project>

Timeline (1.5 s, the goal absorbs the block at tick COLLECT_TICK = 20 = 1.0 s):
  0.0-0.5  bends forward, both arms reach down towards the block
  0.5-1.0  arms pull back up to the chest while the head tilts back
  0.9-1.2  the crystal bone pops out of the head (scale 0 -> 1.2 -> 1)
  1.2-1.5  back to neutral
Re-running replaces the animation."""
import json, sys
from pathlib import Path

P = Path(sys.argv[1])
path = P / "src/main/resources/assets/pysift/geckolib/animations/entity/echo_golem.animation.json"
anims = json.loads(path.read_text(encoding="utf-8"))
anims["animations"]["animation.echo_golem.collect"] = {
    "animation_length": 1.5,
    "bones": {
        "body": {"rotation": {"0.0": [0, 0, 0], "0.4": [25, 0, 0], "0.75": [-5, 0, 0], "1.1": [0, 0, 0], "1.5": [0, 0, 0]}},
        "head": {"rotation": {"0.0": [0, 0, 0], "0.4": [15, 0, 0], "0.85": [-20, 0, 0], "1.2": [0, 0, 0], "1.5": [0, 0, 0]}},
        "right_arm": {"rotation": {"0.0": [0, 0, 0], "0.45": [-70, 0, 15], "0.8": [-30, 0, -10], "1.2": [0, 0, 0],
                                   "1.5": [0, 0, 0]}},
        "left_arm": {"rotation": {"0.0": [0, 0, 0], "0.45": [-70, 0, -15], "0.8": [-30, 0, 10], "1.2": [0, 0, 0],
                                  "1.5": [0, 0, 0]}},
        "crystal": {"scale": {"0.0": [1, 1, 1], "0.85": [0, 0, 0], "0.9": [0, 0, 0], "1.05": [1.25, 1.25, 1.25],
                              "1.2": [1, 1, 1], "1.5": [1, 1, 1]},
                    "rotation": {"0.9": [0, 0, 0], "1.2": [0, 90, 0], "1.5": [0, 90, 0]}},
    },
}
path.write_text(json.dumps(anims, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("added animation.echo_golem.collect")
