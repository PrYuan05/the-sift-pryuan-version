"""Post effect pysift:sculk_vision for the Soul Deprivation vision (shaders/post/sculk_vision.fsh).
Usage: python -I tools/shaders/make_sculk_vision.py <project>

One effect: sculk pass (colour + depth of minecraft:main) -> swap, then blit swap -> main (vanilla invert.json shape).
The SculkCamera values here are only placeholders that size the uniform buffer: PostPassMixin rewrites them every frame
with the real camera (inverse view-projection, position, strength, depth convention). Removes the old
sculk_vision_1..N files from the screen-space version."""
import sys, json
from pathlib import Path

P = Path(sys.argv[1]).resolve()
OUT = P / "src/main/resources/assets/pysift/post_effect"
ZERO4 = [0.0, 0.0, 0.0, 0.0]
CAMERA = ["InvViewProj0", "InvViewProj1", "InvViewProj2", "InvViewProj3", "CameraStrength", "Params"]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    effect = {
        "targets": {"swap": {}},
        "passes": [
            {"vertex_shader": "minecraft:core/screenquad", "fragment_shader": "pysift:post/sculk_vision",
             "inputs": [{"sampler_name": "In", "target": "minecraft:main"},
                        {"sampler_name": "Depth", "target": "minecraft:main", "use_depth_buffer": True}],
             "output": "swap",
             "uniforms": {"SculkCamera": [{"name": n, "type": "vec4", "value": ZERO4} for n in CAMERA]}},
            {"vertex_shader": "minecraft:core/screenquad", "fragment_shader": "minecraft:post/blit",
             "inputs": [{"sampler_name": "In", "target": "swap"}], "output": "minecraft:main",
             "uniforms": {"BlitConfig": [{"name": "ColorModulate", "type": "vec4", "value": [1.0, 1.0, 1.0, 1.0]}]}},
        ],
    }
    (OUT / "sculk_vision.json").write_text(json.dumps(effect, indent=2) + "\n", encoding="utf-8")
    for old in OUT.glob("sculk_vision_*.json"):
        old.unlink()
    print("wrote", (OUT / "sculk_vision.json").relative_to(P))


if __name__ == "__main__":
    main()
