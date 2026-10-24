"""Arrival portals of The Sift, one design per biome palette (built by the user in-game, see art/portal_designs.json).
Usage: python -I tools/worldgen/build_portal_designs.py <project>
Writes data/pysift/structure/portal/<design>.nbt. SiftPortalBlock.buildArrivalPortal() places the design that matches
the biome (SiftPortalBlock.PORTAL_DESIGNS), rotated to the portal axis.

| design | palette                                         | biomes                               |
| ember  | ember stone + capped crimson strata             | crimson_strata_canyon                |
| dune   | bleached sandstone bricks + cracked sandstone   | amber_dunes (derived from ember)     |
| slate  | dark slate + violet-capped dark slate           | violet_slate_abyss                   |
| silted | silted strata + crimson-capped crimson strata 2 | willow_grove (and anything else)     |"""
import gzip, io, json, struct, sys
from pathlib import Path

P = Path(sys.argv[1])
DATA_VERSION = 5023          # Minecraft 26.3 (same as build_structures.py)


def _s(text):
    b = text.encode("utf-8")
    return struct.pack(">H", len(b)) + b


def _payload(tag, value):                       # same tiny NBT writer as build_structures.py
    if tag == 3:
        return struct.pack(">i", value)
    if tag == 8:
        return _s(value)
    if tag == 10:
        return b"".join(bytes([t]) + _s(k) + _payload(t, v) for k, (t, v) in value.items()) + bytes([0])
    if tag == 9:
        elem, items = value
        return bytes([elem]) + struct.pack(">i", len(items)) + b"".join(_payload(elem, i) for i in items)
    raise ValueError(tag)


def nbt_file(root):
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode="wb", mtime=0) as gz:
        gz.write(bytes([10]) + _s("") + _payload(10, root))
    return buf.getvalue()

D = P / "src/main/resources/data/pysift"
A = P / "src/main/resources/assets/pysift"
src = json.loads((Path(__file__).parent / "art/portal_designs.json").read_text(encoding="utf-8"))


# designs derived from a built one by swapping blocks (properties are kept; None = leave the block out)
DERIVED = {
    "dune": ("ember", {   # desert version for amber_dunes: pale sandstone body, warm cracked-sandstone bands, no willow vines
        "pysift:ember_stone": "pysift:bleached_sandstone_bricks",
        "pysift:ember_stone_slab": "pysift:bleached_sandstone_brick_slab",
        "pysift:ember_stone_wall": "pysift:bleached_sandstone_brick_wall",
        "pysift:capped_crimson_strata": "pysift:cracked_sandstone[crack=0]",
        "pysift:soul_willow_vine": None,
    }),
}
for name, (base, swap) in DERIVED.items():
    blocks = []
    for x, y, z, state in src["designs"][base]:
        block, _, props = state.partition("[")
        if block in swap:
            if swap[block] is None:
                continue
            new = swap[block]
            state = new if "[" in new else new + ("[" + props if props else "")
        blocks.append([x, y, z, state])
    src["designs"][name] = blocks


def parse(state):
    name, _, rest = state.partition("[")
    props = dict(kv.split("=") for kv in rest.rstrip("]").split(",")) if rest else {}
    return name, props


for design, blocks in src["designs"].items():
    palette, index, out = [], {}, []
    for x, y, z, state in blocks:
        name, props = parse(state)
        if name.startswith("pysift:"):
            assert (A / "blockstates" / f"{name.split(':')[1]}.json").exists(), name
        key = (name, tuple(sorted(props.items())))
        if key not in index:
            index[key] = len(palette)
            entry = {"id": (8, name)}
            if props:
                entry["properties"] = (10, {k: (8, v) for k, v in props.items()})
            palette.append(entry)
        out.append({"pos": (9, (3, [x, y, z])), "state": (3, index[key])})
    path = D / f"structure/portal/{design}.nbt"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(nbt_file({"DataVersion": (3, DATA_VERSION), "size": (9, (3, src["size"])),
                               "palette": (9, (10, palette)), "blocks": (9, (10, out)), "entities": (9, (10, []))}))
    print(f"portal/{design}.nbt: {len(out)} blocks, {len(palette)} states")
