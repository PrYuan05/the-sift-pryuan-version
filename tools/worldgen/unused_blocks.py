"""List the pysift blocks that world generation never places, and write them to the block tag pysift:not_in_worldgen.
Usage: python -I tools/worldgen/unused_blocks.py <project>      (rerun after changing build_the_sift.py)

"Used" = referenced by any The Sift worldgen / dimension JSON (surface rules, noise settings, features such as the mesas,
trees and plant patches) or placed by a structure template (data/pysift/structure/**/*.nbt), plus anything those blocks drop (e.g. the sapling from the leaves' loot table).
Building-set members (bricks, slabs, stairs, walls) follow their base stone in Java (ModBlocks.SET_BASE), so only base
blocks and the vegetation blocks are listed. Blocks without an item (the fluid) are skipped.
The creative tab pysift_unused_blocks shows the tagged blocks; the main block tab hides them (ModItems).
Also writes the item tag pysift:in_worldgen (used blocks + spawn eggs of naturally spawning mobs): CreativeLayout puts
those first within each creative tab category."""
import gzip, json, re, sys
from pathlib import Path

P = Path(sys.argv[1])
RES = P / "src/main/resources"
A, D = RES / "assets/pysift", RES / "data/pysift"
REF = re.compile(r'"pysift:([a-z0-9_]+)')

blocks = {p.stem for p in (A / "blockstates").glob("*.json") if (A / "items" / p.name).exists()}
java = (P / "src/main/java/pryuan05/pysift/block/ModBlocks.java").read_text(encoding="utf-8")
set_bases = re.search(r'BUILDING_SETS = List\.of\((.*?)\);', java, re.S)[1]
set_bases = re.findall(r'"([a-z0-9_]+)"', set_bases)
SET_SUFFIXES = ("_bricks", "_slab", "_stairs", "_wall", "_brick_slab", "_brick_stairs", "_brick_wall")
members = {b for b in blocks for base in set_bases
           if b != base and (b.startswith(base + "_") and b.endswith(SET_SUFFIXES) or b == f"chiseled_{base}_bricks")}

used = set()
for folder in (D / "worldgen", D / "dimension"):
    for f in folder.rglob("*.json"):
        used |= set(REF.findall(f.read_text(encoding="utf-8"))) & blocks
# structure templates (shrines, huts, fossils...): gzip NBT whose palette strings are plain UTF-8
for f in (D / "structure").rglob("*.nbt"):
    raw = gzip.decompress(f.read_bytes())
    used |= {m.decode() for m in re.findall(rb"pysift:([a-z0-9_]+)", raw)} & blocks
# anything the used blocks drop (sapling from leaves, ...), until nothing new turns up
todo = list(used)
while todo:
    b = todo.pop()
    loot = D / "loot_table/blocks" / f"{b}.json"
    if loot.exists():
        for name in set(REF.findall(loot.read_text(encoding="utf-8"))) & blocks - used:
            used.add(name)
            todo.append(name)

# item tag pysift:in_worldgen (creative tab ordering, CreativeLayout): the used blocks, plus the spawn eggs of the mobs
# that spawn naturally in a The Sift biome
spawned = set()
for f in (D / "worldgen/biome").glob("*.json"):
    for cat in json.loads(f.read_text(encoding="utf-8")).get("attributes", {}).get(
            "minecraft:gameplay/natural_mob_spawns", {}).get("argument", {}).get("spawns_by_category", {}).values():
        spawned |= {e["type"].split(":", 1)[1] for e in cat if e["type"].startswith("pysift:")}
eggs = sorted(f"{m}_spawn_egg" for m in spawned if (A / "items" / f"{m}_spawn_egg.json").exists())
item_tag = D / "tags/item/in_worldgen.json"
item_tag.parent.mkdir(parents=True, exist_ok=True)
item_tag.write_text(json.dumps({"replace": False, "values": [f"pysift:{i}" for i in sorted(used) + eggs]}, indent=2) + "\n",
                    encoding="utf-8")

unused = sorted(blocks - used - members)
tag = D / "tags/block/not_in_worldgen.json"
tag.parent.mkdir(parents=True, exist_ok=True)
tag.write_text(json.dumps({"replace": False, "values": [f"pysift:{b}" for b in unused]}, indent=2) + "\n", encoding="utf-8")
print(f"{len(blocks - members)} base blocks: {len(used - members)} used by worldgen, {len(unused)} not -> {tag.relative_to(P)}")
print("used:", ", ".join(sorted(used - members)))
print("not used:", ", ".join(unused))
print(f"item tag {item_tag.relative_to(P)}: {len(used)} blocks + {len(eggs)} spawn eggs ({', '.join(eggs)})")
