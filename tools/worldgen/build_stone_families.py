"""Extra building forms for the upgraded stones (StoneFamilies.java), resources rewritten from vanilla templates.
Usage: python -I tools/worldgen/build_stone_families.py <project>

FORMS: our block -> (base stone, texture, display names). Each form gets the block + slab / stairs / wall (skill rule:
every block has its derived blocks), all four from vanilla polished_deepslate's resources with the ids and the texture
swapped (one texture on every face - a frameless smooth face, smooth_basalt style). Recipes: the vanilla
polished_deepslate slab / stairs / wall crafting and stonecutting recipes rewritten, plus smelting the base stone into
the smooth block (like vanilla smooth stone). Loot, tags (wherever vanilla lists polished_deepslate*) and lang too;
the full block also goes into #minecraft:blocks_motion_no_leaves (CLAUDE.md).
"""
import json, re, sys, zipfile
from pathlib import Path

P = Path(sys.argv[1]).resolve()
RES = P / "src/main/resources"
A, D = RES / "assets/pysift", RES / "data"
CACHE = P / ".gradle/loom-cache/minecraftMaven/net/minecraft"
CLIENT = zipfile.ZipFile(next(CACHE.glob("minecraft-clientOnly-*/26.3/minecraft-clientOnly-*-26.3.jar")))
COMMON = zipfile.ZipFile(next(CACHE.glob("minecraft-common-*/26.3/minecraft-common-*-26.3.jar")))
TEMPLATE = "polished_deepslate"

FORMS = {
    "smooth_ash_marble": ("ash_marble", "pysift:block/ash_marble/smooth_ash_marble", ("Smooth Ash Marble", "平滑灰大理石")),
    # v2.1.0 user: Graystone (gray_strata, renamed from 灰色地層岩) gets a smooth version and a pillar
    "smooth_gray_strata": ("gray_strata", "pysift:block/gray_strata/smooth_gray_strata", ("Smooth Graystone", "平滑灰石")),
}
# pillars: our block -> (base stone, side texture, top texture, names); from vanilla quartz_pillar (axis blockstate,
# vertical + horizontal cube_column models, crafted from two base blocks, stonecut from one). No slab / stairs / wall
# (skill rule: pillars and chiseled bricks have no derived blocks).
PILLARS = {
    "gray_strata_pillar": ("gray_strata", "pysift:block/gray_strata/gray_strata_pillar_side",
                           "pysift:block/gray_strata/gray_strata_pillar_top", ("Graystone Pillar", "灰石柱")),
}
PILLAR_TEMPLATE = "quartz_pillar"
SUFFIX = {"": ("", ""), "_slab": (" Slab", "半磚"), "_stairs": (" Stairs", "階梯"), "_wall": (" Wall", "牆")}


def lj(p): return json.loads(Path(p).read_text(encoding="utf-8-sig"))


def wj(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def jar(z, name): return json.loads(z.read(name))


def main():
    made = []
    for ours, (base, tex, (en, zh)) in FORMS.items():
        def sub(obj, key=None):
            if isinstance(obj, dict):
                return {k: sub(v, k) for k, v in obj.items()}
            if isinstance(obj, list):
                return [sub(v, key) for v in obj]
            if isinstance(obj, str):
                if obj == f"minecraft:block/{TEMPLATE}":
                    return tex if key not in ("model", "parent") else f"pysift:block/{ours}"
                if obj.startswith(f"minecraft:block/{TEMPLATE}_"):
                    return f"pysift:block/{ours}" + obj[len(f"minecraft:block/{TEMPLATE}"):]
                if obj.startswith(f"minecraft:{TEMPLATE}"):
                    return f"pysift:{ours}" + obj[len(f"minecraft:{TEMPLATE}"):]
                if obj.startswith(f"minecraft:blocks/{TEMPLATE}"):
                    return f"pysift:blocks/{ours}" + obj[len(f"minecraft:blocks/{TEMPLATE}"):]
            return obj
        for suf in SUFFIX:
            part, bid = TEMPLATE + suf, ours + suf
            made.append(bid)
            for kind in ("blockstates", "items"):
                wj(A / f"{kind}/{bid}.json", sub(jar(CLIENT, f"assets/minecraft/{kind}/{part}.json")))
            for n in CLIENT.namelist():
                m = re.fullmatch(rf"assets/minecraft/models/block/({part}(_[a-z_]+)?)\.json", n)
                if m and (suf or not re.match(r"_(slab|stairs|wall)", m[2] or "")):
                    wj(A / f"models/block/{ours}{m[1][len(TEMPLATE):]}.json", sub(jar(CLIENT, n)))
            table = sub(jar(COMMON, f"data/minecraft/loot_table/blocks/{part}.json"))
            for d in ("loot_table", "loot_tables"):
                wj(D / f"pysift/{d}/blocks/{bid}.json", table)
            if suf:
                wj(D / f"pysift/recipe/{bid}.json", sub(jar(COMMON, f"data/minecraft/recipe/{part}.json")))
                wj(D / f"pysift/recipe/{bid}_from_{ours}_stonecutting.json",
                   sub(jar(COMMON, f"data/minecraft/recipe/{part}_from_{TEMPLATE}_stonecutting.json")))
            for n in COMMON.namelist():
                if n.startswith("data/minecraft/tags/") and n.endswith(".json") and "/worldgen/" not in n \
                        and f"minecraft:{part}" in jar(COMMON, n)["values"]:
                    path = D / "minecraft/tags" / n[len("data/minecraft/tags/"):]
                    data = lj(path) if path.exists() else {"replace": False, "values": []}
                    if f"pysift:{bid}" not in data["values"]:
                        data["values"].append(f"pysift:{bid}")
                    wj(path, data)
        smelt = jar(COMMON, "data/minecraft/recipe/smooth_stone.json")
        smelt["ingredient"] = f"pysift:{base}"
        smelt["result"] = {"id": f"pysift:{ours}"}
        wj(D / f"pysift/recipe/{ours}.json", smelt)
        motion = D / "minecraft/tags/block/blocks_motion_no_leaves.json"
        data = lj(motion)
        if f"pysift:{ours}" not in data["values"]:
            data["values"].append(f"pysift:{ours}")
        wj(motion, data)
        for code in ("en_us", "zh_tw"):
            lang = lj(A / f"lang/{code}.json")
            for suf, (es, zs) in SUFFIX.items():
                lang[f"block.pysift.{ours}{suf}"] = en + es if code == "en_us" else zh + zs
                lang[f"item.pysift.{ours}{suf}"] = lang[f"block.pysift.{ours}{suf}"]   # block items read item.* in 26.3
            wj(A / f"lang/{code}.json", lang)
    for ours, (base, side, top, (en, zh)) in PILLARS.items():
        def sub(obj, key=None):
            if isinstance(obj, dict):
                return {k: sub(v, k) for k, v in obj.items()}
            if isinstance(obj, list):
                return [sub(v, key) for v in obj]
            if isinstance(obj, str):
                if obj == f"minecraft:block/{PILLAR_TEMPLATE}_top":
                    return top
                if obj == f"minecraft:block/{PILLAR_TEMPLATE}":
                    return side if key not in ("model", "parent") else f"pysift:block/{ours}"
                if obj.startswith(f"minecraft:block/{PILLAR_TEMPLATE}_"):
                    return f"pysift:block/{ours}" + obj[len(f"minecraft:block/{PILLAR_TEMPLATE}"):]
                if obj == "minecraft:quartz_block":
                    return f"pysift:{base}"
                if obj.startswith(f"minecraft:{PILLAR_TEMPLATE}"):
                    return f"pysift:{ours}" + obj[len(f"minecraft:{PILLAR_TEMPLATE}"):]
                if obj.startswith(f"minecraft:blocks/{PILLAR_TEMPLATE}"):
                    return f"pysift:blocks/{ours}" + obj[len(f"minecraft:blocks/{PILLAR_TEMPLATE}"):]
            return obj
        made.append(ours)
        for kind in ("blockstates", "items"):
            wj(A / f"{kind}/{ours}.json", sub(jar(CLIENT, f"assets/minecraft/{kind}/{PILLAR_TEMPLATE}.json")))
        for n in CLIENT.namelist():
            m = re.fullmatch(rf"assets/minecraft/models/block/({PILLAR_TEMPLATE}(_horizontal)?)\.json", n)
            if m:
                wj(A / f"models/block/{ours}{m[1][len(PILLAR_TEMPLATE):]}.json", sub(jar(CLIENT, n)))
        table = sub(jar(COMMON, f"data/minecraft/loot_table/blocks/{PILLAR_TEMPLATE}.json"))
        for d in ("loot_table", "loot_tables"):
            wj(D / f"pysift/{d}/blocks/{ours}.json", table)
        wj(D / f"pysift/recipe/{ours}.json", sub(jar(COMMON, f"data/minecraft/recipe/{PILLAR_TEMPLATE}.json")))
        wj(D / f"pysift/recipe/{ours}_from_{base}_stonecutting.json",
           sub(jar(COMMON, f"data/minecraft/recipe/{PILLAR_TEMPLATE}_from_quartz_block_stonecutting.json")))
        for tag in ("minecraft/tags/block/mineable/pickaxe.json", "minecraft/tags/block/blocks_motion_no_leaves.json"):
            path = D / tag
            data = lj(path)
            if f"pysift:{ours}" not in data["values"]:
                data["values"].append(f"pysift:{ours}")
            wj(path, data)
        for code in ("en_us", "zh_tw"):
            lang = lj(A / f"lang/{code}.json")
            lang[f"block.pysift.{ours}"] = lang[f"item.pysift.{ours}"] = en if code == "en_us" else zh
            wj(A / f"lang/{code}.json", lang)
    print("made:", made)
    import subprocess, sys as _sys                          # keep models grouped per block (tools/texture_pipeline/group_models.py)
    subprocess.run([_sys.executable, "-I", str(Path(__file__).resolve().parents[1] / "texture_pipeline/group_models.py"), str(P)], check=True)


if __name__ == "__main__":
    main()
