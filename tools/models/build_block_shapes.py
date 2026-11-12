"""VoxelShapes that follow the models: for every pysift block whose model has its own geometry (elements in a pysift
model file), write the boxes of each blockstate variant to assets/pysift/block_shapes.json. At runtime
block/ModelShapes.java turns them into VoxelShapes and mixin/ModelShapeMixin returns them from BlockState.getShape,
so the outline, the collision (when the block has collision) and the occlusion all match what is drawn.
Usage: python -I tools/models/build_block_shapes.py <project>      (run after the model generators)

Rules
  * the variant's x / y rotation is applied like vanilla (x first, then y, about the block centre);
  * random variant lists: the first entry; multipart: the parts whose "when" matches, combined per state;
  * elements thinner than 1 px (decals, needles, film) are left out; rotated elements count as unrotated boxes;
  * coordinates snap to 0.5 px and are clipped to the block (a large cogwheel's teeth stick out of it);
  * a model with more than MAX_BOXES elements, and every plant model (models/block/vegetation/, leaves included),
    becomes one bounding box, like vanilla plants;
  * a block whose every state comes out as the full cube is left alone;
  * soul power machines whose moving parts are drawn by SoulPowerRenderer take their shape from the item model
    (casing + parts at rest), which is modelled in the same orientation as the block model."""
import json, sys
from itertools import product
from pathlib import Path

P = Path(sys.argv[1]).resolve()
A = P / "src/main/resources/assets/pysift"
OUT = A / "block_shapes.json"
MAX_BOXES = 12
SKIP = {"soul_power_part",                # never placed: it only holds the moving-part models
        "soul_gearbox",                    # an encased box: the default full-cube shape, like Create's gearbox
        "soul_conduit"}                    # 2048 states: its shapes are built in SoulConduitBlock
FROM_ITEM = {"soul_shaft", "soul_cogwheel", "large_soul_cogwheel", "spirit_engine", "soul_grinder", "soul_sifter",
             "charoite_beam_emitter", "charoite_beam_receiver", "spirit_pump",
             "soul_hand_crank", "soul_fan", "soul_drill", "soul_clutch", "soul_gearshift", "soul_vein_node", "soul_gauge"}


def lj(p):
    return json.loads(Path(p).read_text(encoding="utf-8-sig"))


def elements(ref, depth=0):
    ns, path = ref.split(":") if ":" in ref else ("minecraft", ref)
    if ns != "pysift" or depth > 8:
        return None
    f = A / "models" / (path + ".json")
    if not f.exists():
        return None
    j = lj(f)
    if "elements" in j:
        return j["elements"]
    return elements(j["parent"], depth + 1) if "parent" in j else None


def rot_x(p, deg):                          # vanilla: +Y turns towards -Z for x = 90
    x, y, z = p[0] - 8, p[1] - 8, p[2] - 8
    for _ in range((deg // 90) % 4):
        y, z = z, -y
    return [x + 8, y + 8, z + 8]


def rot_y(p, deg):                          # vanilla: -Z (north) turns towards +X (east) for y = 90
    x, y, z = p[0] - 8, p[1] - 8, p[2] - 8
    for _ in range((deg // 90) % 4):
        x, z = -z, x
    return [x + 8, y + 8, z + 8]


def snap(v):
    return max(0.0, min(16.0, round(v * 2) / 2))


def boxes(els, x=0, y=0, plant=False):
    out = []
    for e in els:
        f, t = e["from"], e["to"]
        if min(abs(t[i] - f[i]) for i in range(3)) < 1 and not plant:
            continue
        a, b = rot_y(rot_x(f, x), y), rot_y(rot_x(t, x), y)
        lo = [snap(min(a[i], b[i])) for i in range(3)]
        hi = [snap(max(a[i], b[i])) for i in range(3)]
        if plant or all(hi[i] - lo[i] >= 0.5 for i in range(3)):
            out.append(lo + hi)
    if len(out) > MAX_BOXES or (plant and out):
        out = [[min(b[i] for b in out) for i in range(3)] + [max(b[i + 3] for b in out) for i in range(3)]]
    return sorted({tuple(b) for b in out})


def is_full(bs):
    return any(b == (0, 0, 0, 16, 16, 16) for b in bs)


# blocks drawn entirely by SoulPowerRenderer have unrotated blockstates; their shape turns with the axis property
BY_AXIS = {"soul_shaft", "soul_cogwheel", "large_soul_cogwheel"}
AXIS_ROT = {"y": {}, "x": {"x": 90, "y": 90}, "z": {"x": 90}}


def variant_boxes(block, v, key=""):
    v = v[0] if isinstance(v, list) else v
    if block in BY_AXIS:
        axis = dict(kv.split("=") for kv in key.split(",") if "=" in kv).get("axis", "y")
        v = {**v, **AXIS_ROT[axis]}
    ref = v["model"]
    els = None
    if block in FROM_ITEM:
        els = elements(f"pysift:item/{block}")
    if els is None:
        els = elements(ref)
    if els is None:
        return None
    return boxes(els, v.get("x", 0), v.get("y", 0), plant="/vegetation/" in ref)


def matches(when, state):
    if "OR" in when:
        return any(matches(w, state) for w in when["OR"])
    return all(state.get(k) in str(v).split("|") for k, v in when.items())


shapes = {}
for bs in sorted((A / "blockstates").glob("*.json")):
    block = bs.stem
    if block in SKIP or block.endswith("_vine"):
        continue                            # vines: their Java shape follows the faces they hang on
    j = lj(bs)
    states = {}
    if "variants" in j:
        for key, v in j["variants"].items():
            b = variant_boxes(block, v, key)
            if b is None:
                states = None
                break
            states[key] = b
    else:                                   # multipart: enumerate the property values the parts test
        props = {}
        for part in j["multipart"]:
            for w in ([part["when"]] if "when" in part else []):
                for cond in (w["OR"] if "OR" in w else [w]):
                    for k, v in cond.items():
                        props.setdefault(k, set()).update(str(v).split("|"))
        for k in props:
            props[k] |= {"true", "false"} if props[k] <= {"true", "false"} else set()
        names = sorted(props)
        for values in product(*[sorted(props[k]) for k in names]):
            state = dict(zip(names, values))
            bb = []
            for part in j["multipart"]:
                if "when" in part and not matches(part["when"], state):
                    continue
                b = variant_boxes(block, part["apply"])
                if b is None:
                    bb = None
                    break
                bb += b
            if bb is None:
                states = None
                break
            states[",".join(f"{k}={state[k]}" for k in names)] = sorted(set(bb))
    if not states or any(not b for b in states.values()) or all(is_full(b) for b in states.values()):
        continue
    shapes[block] = {k: [list(b) for b in v] for k, v in states.items()}

OUT.write_text(json.dumps(shapes, indent=1) + "\n", encoding="utf-8")
print(f"{len(shapes)} blocks with model shapes: {', '.join(sorted(shapes))}")
