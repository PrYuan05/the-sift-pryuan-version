"""Building sets for every eligible stone: bricks, chiseled bricks, and slab / stairs / wall for both the stone
and its bricks, plus crafting and stonecutting recipes (vanilla stone-brick family as the template).

  python -I tools/texture_pipeline/building_sets.py <project> preview   -> candidate list + brick textures preview
  python -I tools/texture_pipeline/building_sets.py <project> apply     -> write textures, models, blockstates,
                                                                          items, loot, recipes, tags, lang
Rules: building_rules.json. New PNGs (bricks, chiseled) are generated from the stone's default texture palette
and logged in recolor_manifest.json (mode "generated"). Java registration lives in ModBlocks.BUILDING_SETS."""
import sys, re, json, datetime
from pathlib import Path
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from palette_lib import project_paths, lj, wj, entries, res_path, sha1, lab, lum

P, RES, A, D = project_paths(sys.argv[1])
ASSETS = RES / "assets"
HERE = Path(__file__).resolve().parent
OUT = P / "build/texture_pipeline/out/building"
RULES = lj(HERE / "building_rules.json")
CMD = sys.argv[2] if len(sys.argv) > 2 else "preview"
JAVA = P / "src/main/java/pryuan05/pysift/block/ModBlocks.java"


# ---------------- candidates ----------------
def parse_defs():
    java = JAVA.read_text(encoding="utf-8")
    return re.findall(r'^\s+(block|pillar|facing)\("([a-z0-9_]+)", Mat\.(\w+)\)((?:\.\w+\([^)]*\))*)', java, re.M)


def candidates():
    out = []
    for kind, bid, mat, chain in parse_defs():
        if bid in RULES["include"] or (kind == "block" and mat in ("STONE", "DEEPSLATE") and "_capped_" not in bid
                                       and bid not in RULES["exclude"]):
            out.append({"base": bid, "mat": mat, "chain": chain})
    return out


def default_key(chain):
    parts = [f"{n}={lo}" for n, lo, hi in re.findall(r'\.intProp\("(\w+)", (\d+), (\d+)\)', chain)]
    m = re.search(r'\.tones\("(\w+)"', chain)
    if m:
        parts.append(f"tone={m[1]}")
    return parts


def default_textures(base, chain):
    """cube_all textures of the default-state pool (random variants kept, in pool order)."""
    var = lj(A / "blockstates" / f"{base}.json")["variants"]
    want = set(default_key(chain))
    key = next(k for k in var if set(x for x in k.split(",") if x) >= want)
    refs = []
    for e in entries(var[key]):
        t = lj(res_path(ASSETS, e["model"], "models", ".json")).get("textures", {})
        if "all" in t and t["all"] not in refs:
            refs.append(t["all"])
    return refs


# ---------------- brick / chiseled textures ----------------
def lab_to_rgb(L, a, b):
    fy = (L + 16) / 116
    fx, fz = fy + a / 500, fy - b / 200
    inv = lambda t: t ** 3 if t ** 3 > 0.008856 else (t - 16 / 116) / 7.787
    x, y, z = inv(fx) * 0.95047, inv(fy), inv(fz) * 1.08883
    r = 3.2406 * x - 1.5372 * y - 0.4986 * z
    g = -0.9689 * x + 1.8758 * y + 0.0415 * z
    bl = 0.0557 * x - 0.2040 * y + 1.0570 * z
    gam = lambda c: 1.055 * c ** (1 / 2.4) - 0.055 if c > 0.0031308 else 12.92 * c
    return tuple(max(0, min(255, round(gam(max(0.0, c)) * 255))) for c in (r, g, bl))


MIN_SPREAD = 22.0   # CIELAB L between the darkest (mortar) and lightest level


def levels(img, n=5):
    """n colours ordered dark -> light: median colour of each brightness quantile of the stone. Flat stones
    (L spread < MIN_SPREAD) get synthetic levels around their main colour, so mortar lines stay visible
    (darker and slightly cooler, highlights lighter and slightly warmer)."""
    px = sorted((c[:3] for c in img.convert("RGBA").getdata() if c[3] > 0), key=lum)
    out = []
    for i in range(n):
        chunk = px[i * len(px) // n:(i + 1) * len(px) // n] or px[-1:]
        out.append(chunk[len(chunk) // 2])
    if lab(out[-1])[0] - lab(out[0])[0] < MIN_SPREAD:
        L, a, b = lab(px[len(px) // 2])
        offsets = [(-16, -1.5), (-7, -0.5), (0, 0), (5, 0.8), (10, 1.5)]
        out = [lab_to_rgb(max(4, min(96, L + dl)), a, b + db) for dl, db in offsets]
    return out


def level_of(c, pal):
    return min(range(len(pal)), key=lambda i: abs(lum(pal[i]) - lum(c)))


def bricks(img):
    """Vanilla stone-brick layout: 4 courses of 8x4 bricks, alternate courses offset by 4, 1px mortar
    (darkest colour) along the bottom and right of every brick; brick faces keep the stone's own grain mapped
    onto the lighter four colours, with a lighter top edge and a darker bottom edge."""
    pal = levels(img)
    src = img.convert("RGB")
    out = Image.new("RGB", (16, 16))
    for y in range(16):
        course, ry = divmod(y, 4)
        offset = 4 if course % 2 else 0
        for x in range(16):
            rx = (x + offset) % 8
            if ry == 3 or rx == 7:
                c = pal[0]
            else:
                lv = max(1, level_of(src.getpixel((x, y)), pal))
                if ry == 0:
                    lv = min(4, lv + 1)
                elif ry == 2:
                    lv = max(1, lv - 1)
                c = pal[lv]
            out.putpixel((x, y), c)
    return out


def chiseled(img):
    """Chiseled bricks: two stacked 16x8 panels (like vanilla chiseled stone bricks) each with a bevelled
    frame and a carved centre motif, mortar line between the panels."""
    pal = levels(img)
    out = Image.new("RGB", (16, 16))
    for y in range(16):
        py = y % 8
        for x in range(16):
            if py == 7:
                c = pal[0]                                     # mortar between panels / tiles
            elif x in (0, 15) or py == 0:
                c = pal[4] if (py == 0 or x == 0) else pal[1]  # bevel: light top/left, dark right
            elif py == 6:
                c = pal[1]                                     # bottom bevel
            else:
                dx, dy = abs(x - 7.5), abs(py - 3)
                if dx <= 1.5 and dy <= 1:
                    c = pal[2]                                 # carved centre recess
                elif (dx <= 3.5 and dy == 2) or (dx in (2.5, 3.5) and dy <= 2):
                    c = pal[1]                                 # carved groove around the centre
                else:
                    c = pal[3]
            out.putpixel((x, y), c)
    return out


# ---------------- preview ----------------
def preview():
    cands = candidates()
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for c in cands:
        refs = default_textures(c["base"], c["chain"])
        base_img = Image.open(res_path(ASSETS, refs[0], "textures", ".png")).convert("RGBA")
        bi, ci = bricks(base_img), chiseled(base_img)
        (OUT / "textures").mkdir(exist_ok=True)
        bi.save(OUT / "textures" / f"{c['base']}_bricks.png")
        ci.save(OUT / "textures" / f"chiseled_{c['base']}_bricks.png")
        rows.append((c, refs, base_img, bi, ci))
    tile, PAD, cols = 64, 6, 3
    per_row = 3
    W = per_row * (3 * (tile + PAD) + 200)
    H = 30 + ((len(rows) + per_row - 1) // per_row) * (tile + 24)
    img = Image.new("RGB", (W, H), (28, 28, 32))
    dr = ImageDraw.Draw(img)
    dr.text((6, 6), "stone | bricks | chiseled bricks   (slab / stairs / wall reuse these textures)", fill=(235, 235, 235))
    for n, (c, refs, b, bi, ci) in enumerate(rows):
        x0 = 6 + (n % per_row) * (3 * (tile + PAD) + 200)
        y0 = 28 + (n // per_row) * (tile + 24)
        x = x0
        for im in (b, bi, ci):
            img.paste(im.convert("RGB").resize((tile, tile), Image.Resampling.NEAREST), (x, y0))
            x += tile + PAD
        dr.text((x + 4, y0 + tile // 2 - 6), c["base"][:28] + ("" if len(refs) == 1 else f" ({len(refs)} var)"), fill=(250, 210, 90))
    img.save(OUT / "building_preview.png")
    wj(OUT / "building_candidates.json", [{"base": c["base"], "mat": c["mat"], "default_textures": refs} for c, refs, *_ in rows])
    print(f"{len(rows)} stones -> {len(rows) * 8} new blocks")
    for c, refs, *_ in rows:
        print(f"  {c['base']:24s} {c['mat']:9s} default={default_key(c['chain']) or '-'} variants={len(refs)}")


# ---------------- apply ----------------
VANILLA = P / "build/texture_pipeline/vanilla/assets/minecraft/blockstates"


def set_ids(base):
    return {"bricks": f"{base}_bricks", "chiseled": f"chiseled_{base}_bricks",
            "slab": f"{base}_slab", "stairs": f"{base}_stairs", "wall": f"{base}_wall",
            "brick_slab": f"{base}_brick_slab", "brick_stairs": f"{base}_brick_stairs", "brick_wall": f"{base}_brick_wall"}


def model(path_id, parent, textures):
    folder, name = path_id.split("/")
    wj(A / "models/block" / folder / f"{name}.json", {"parent": parent, "textures": textures})
    return f"pysift:block/{path_id}"


def vanilla_states(name, mapping):
    """Copy a vanilla stone-brick blockstate; every vanilla model ref becomes a weighted pool of our models."""
    bs = lj(VANILLA / f"{name}.json")

    def conv(entry):
        rest = {k: v for k, v in entry.items() if k != "model"}
        return [{"model": m, "weight": 1, **rest} for m in mapping[entry["model"]]]
    if "variants" in bs:
        return {"variants": {k: conv(v) for k, v in bs["variants"].items()}}
    return {"multipart": [{**part, "apply": conv(part["apply"])} for part in bs["multipart"]]}


def shape_family(fid, textures, full_models):
    """slab / stairs / wall models for one texture pool. Returns {block id: item model}."""
    slab, slab_top, st, st_in, st_out, post, side, tall = ([] for _ in range(8))
    inv = None
    for i, t in enumerate(textures, 1):
        tx = {"bottom": t, "top": t, "side": t}
        slab.append(model(f"{fid['slab']}/{fid['slab']}_{i}", "minecraft:block/slab", tx))
        slab_top.append(model(f"{fid['slab']}/{fid['slab']}_top_{i}", "minecraft:block/slab_top", tx))
        st.append(model(f"{fid['stairs']}/{fid['stairs']}_{i}", "minecraft:block/stairs", tx))
        st_in.append(model(f"{fid['stairs']}/{fid['stairs']}_inner_{i}", "minecraft:block/inner_stairs", tx))
        st_out.append(model(f"{fid['stairs']}/{fid['stairs']}_outer_{i}", "minecraft:block/outer_stairs", tx))
        post.append(model(f"{fid['wall']}/{fid['wall']}_post_{i}", "minecraft:block/template_wall_post", {"wall": t}))
        side.append(model(f"{fid['wall']}/{fid['wall']}_side_{i}", "minecraft:block/template_wall_side", {"wall": t}))
        tall.append(model(f"{fid['wall']}/{fid['wall']}_side_tall_{i}", "minecraft:block/template_wall_side_tall", {"wall": t}))
        if inv is None:
            inv = model(f"{fid['wall']}/{fid['wall']}_inventory", "minecraft:block/wall_inventory", {"wall": t})
    v = "minecraft:block/stone_brick"
    wj(A / "blockstates" / f"{fid['slab']}.json", vanilla_states("stone_brick_slab", {
        f"{v}_slab": slab, f"{v}_slab_top": slab_top, "minecraft:block/stone_bricks": full_models}))
    wj(A / "blockstates" / f"{fid['stairs']}.json", vanilla_states("stone_brick_stairs", {
        f"{v}_stairs": st, f"{v}_stairs_inner": st_in, f"{v}_stairs_outer": st_out}))
    wj(A / "blockstates" / f"{fid['wall']}.json", vanilla_states("stone_brick_wall", {
        f"{v}_wall_post": post, f"{v}_wall_side": side, f"{v}_wall_side_tall": tall}))
    return {fid["slab"]: slab[0], fid["stairs"]: st[0], fid["wall"]: inv}


def write_loot(bid, slab=False):
    entry = {"type": "minecraft:item", "name": f"pysift:{bid}"}
    if slab:   # vanilla slab loot: 2 items from a double slab
        entry["modifier"] = [{"type": "minecraft:set_count", "count": 2,
                              "condition": {"type": "minecraft:match_block", "blocks": f"pysift:{bid}", "state": {"type": "double"}}},
                             {"type": "minecraft:explosion_decay"}]
        pool = {"entries": [entry], "rolls": 1}
    else:
        pool = {"condition": {"type": "minecraft:survives_explosion"}, "entries": [entry], "rolls": 1}
    table = {"type": "minecraft:block", "pools": [pool], "random_sequence": f"pysift:blocks/{bid}"}
    for d in ("loot_table", "loot_tables"):
        wj(D / "pysift" / d / "blocks" / f"{bid}.json", table)


def result(out, n): return {"count": n, "id": f"pysift:{out}"} if n > 1 else {"id": f"pysift:{out}"}


def write_recipes(base, ids):
    R = D / "pysift/recipe"

    def shaped(src, pattern, out, n):
        return {"type": "minecraft:crafting_shaped", "category": "building", "key": {"#": f"pysift:{src}"},
                "pattern": pattern, "result": result(out, n)}

    def cut(src, out, n=1):
        return {"type": "minecraft:stonecutting", "ingredient": f"pysift:{src}", "result": result(out, n)}
    wj(R / f"{ids['bricks']}.json", shaped(base, ["##", "##"], ids["bricks"], 4))
    wj(R / f"{ids['chiseled']}.json", shaped(ids["brick_slab"], ["#", "#"], ids["chiseled"], 1))
    for src, sl, stv, wl in ((base, "slab", "stairs", "wall"), (ids["bricks"], "brick_slab", "brick_stairs", "brick_wall")):
        wj(R / f"{ids[sl]}.json", shaped(src, ["###"], ids[sl], 6))
        wj(R / f"{ids[stv]}.json", shaped(src, ["#  ", "## ", "###"], ids[stv], 4))
        wj(R / f"{ids[wl]}.json", shaped(src, ["###", "###"], ids[wl], 6))
    outs = [("bricks", 1), ("chiseled", 1), ("slab", 2), ("stairs", 1), ("wall", 1),
            ("brick_slab", 2), ("brick_stairs", 1), ("brick_wall", 1)]
    for k, n in outs:
        wj(R / f"{ids[k]}_from_{base}_stonecutting.json", cut(base, ids[k], n))
    for k, n in [outs[1]] + outs[5:]:
        wj(R / f"{ids[k]}_from_{ids['bricks']}_stonecutting.json", cut(ids["bricks"], ids[k], n))


def add_tag(path, values):
    tag = lj(path) if path.exists() else {"replace": False, "values": []}
    tag["values"] += [v for v in values if v not in tag["values"]]
    wj(path, tag)


def apply():
    cands = candidates()
    existing = {p.stem for p in (A / "blockstates").glob("*.json")}
    lang = {l: lj(A / f"lang/{l}.json") for l in ("en_us", "zh_tw")}
    man_path = HERE / "recolor_manifest.json"
    man = lj(man_path) if man_path.exists() else {"entries": []}
    by_file = {e["file"]: e for e in man["entries"]}
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    tool_of = {}
    for tf in (D / "minecraft/tags/block/mineable").glob("*.json"):
        for v in lj(tf)["values"]:
            tool_of[v.split(":", 1)[1]] = tf.stem
    tags, mineable, java = {"slabs": [], "stairs": [], "walls": []}, {}, []
    chains = {b: ch for _, b, _, ch in parse_defs()}
    reused = []
    for c in cands:
        base, ids = c["base"], set_ids(c["base"])
        # an existing <base>_bricks block (e.g. corrupted_slate_bricks) is reused as this stone's bricks
        reuse_bricks = ids["bricks"] in chains
        clash = [i for k, i in ids.items() if i in existing and not (k == "bricks" and reuse_bricks)]
        assert not clash, f"{base}: ids already exist {clash}"
        refs = default_textures(base, c["chain"])
        base_img = Image.open(res_path(ASSETS, refs[0], "textures", ".png")).convert("RGBA")
        tex = {}
        todo = (("chiseled", chiseled(base_img)),) if reuse_bricks else (("bricks", bricks(base_img)), ("chiseled", chiseled(base_img)))
        for k, img in todo:
            path = A / "textures/block" / ids["bricks"] / f"{ids[k]}.png"
            path.parent.mkdir(parents=True, exist_ok=True)
            img.save(path)
            rel = path.relative_to(A).as_posix()
            by_file[rel] = {"file": rel, "pool": f"{base}:{k}", "reference": refs[0], "source": refs[0], "mode": "generated",
                            "method": "building_set", "sha1_before": None, "sha1_after": sha1(path), "backup": None, "date": stamp}
            tex[k] = f"pysift:block/{ids['bricks']}/{ids[k]}"
        def default_models(block, chain):
            var = lj(A / "blockstates" / f"{block}.json")["variants"]
            want = set(default_key(chain))
            key = next(k for k in var if set(x for x in k.split(",") if x) >= want)
            return [e["model"] for e in entries(var[key])]
        chis_model = model(f"{ids['bricks']}/{ids['chiseled']}", "minecraft:block/cube_all", {"all": tex["chiseled"]})
        wj(A / "blockstates" / f"{ids['chiseled']}.json", {"variants": {"": {"model": chis_model}}})
        item_models = {ids["chiseled"]: chis_model}
        if reuse_bricks:
            brick_textures = default_textures(ids["bricks"], chains[ids["bricks"]])
            brick_full = default_models(ids["bricks"], chains[ids["bricks"]])
            reused.append(ids["bricks"])
        else:
            brick_model = model(f"{ids['bricks']}/{ids['bricks']}", "minecraft:block/cube_all", {"all": tex["bricks"]})
            wj(A / "blockstates" / f"{ids['bricks']}.json", {"variants": {"": {"model": brick_model}}})
            item_models[ids["bricks"]] = brick_model
            brick_textures, brick_full = [tex["bricks"]], [brick_model]
        item_models |= shape_family({"slab": ids["slab"], "stairs": ids["stairs"], "wall": ids["wall"]}, refs,
                                    default_models(base, c["chain"]))
        item_models |= shape_family({"slab": ids["brick_slab"], "stairs": ids["brick_stairs"], "wall": ids["brick_wall"]},
                                    brick_textures, brick_full)
        for bid, m in item_models.items():
            wj(A / "models/item" / f"{bid}.json", {"parent": m})
            wj(A / "items" / f"{bid}.json", {"model": {"type": "minecraft:model", "model": f"pysift:item/{bid}"}})
            write_loot(bid, slab=bid.endswith("_slab"))
        write_recipes(base, ids)
        tags["slabs"] += [f"pysift:{ids['slab']}", f"pysift:{ids['brick_slab']}"]
        tags["stairs"] += [f"pysift:{ids['stairs']}", f"pysift:{ids['brick_stairs']}"]
        tags["walls"] += [f"pysift:{ids['wall']}", f"pysift:{ids['brick_wall']}"]
        mineable.setdefault(tool_of.get(base, "pickaxe"), []).extend(f"pysift:{i}" for i in ids.values())
        zh_base = lang["zh_tw"].get(f"block.pysift.{base}", base)
        en_base = lang["en_us"].get(f"block.pysift.{base}", base.replace("_", " ").title())
        names = {"bricks": (f"{en_base} Bricks", f"{zh_base}磚"), "chiseled": (f"Chiseled {en_base} Bricks", f"浮雕{zh_base}磚"),
                 "slab": (f"{en_base} Slab", f"{zh_base}半磚"), "stairs": (f"{en_base} Stairs", f"{zh_base}階梯"),
                 "wall": (f"{en_base} Wall", f"{zh_base}牆"), "brick_slab": (f"{en_base} Brick Slab", f"{zh_base}磚半磚"),
                 "brick_stairs": (f"{en_base} Brick Stairs", f"{zh_base}磚階梯"), "brick_wall": (f"{en_base} Brick Wall", f"{zh_base}磚牆")}
        if reuse_bricks:
            names.pop("bricks")          # keep the existing block's names
        for k, (en, zh) in names.items():
            for pre in ("block", "item"):
                lang["en_us"][f"{pre}.pysift.{ids[k]}"] = en
                lang["zh_tw"][f"{pre}.pysift.{ids[k]}"] = zh
        java.append(f'"{base}"')
    for name, vals in tags.items():
        add_tag(D / f"minecraft/tags/block/{name}.json", vals)
        add_tag(D / f"minecraft/tags/item/{name}.json", vals)
    for tool, vals in mineable.items():
        add_tag(D / f"minecraft/tags/block/mineable/{tool}.json", vals)
    for l, d in lang.items():
        wj(A / f"lang/{l}.json", d)
    man["entries"] = sorted(by_file.values(), key=lambda e: e["file"])
    wj(man_path, man)
    (OUT / "building_sets_java.txt").write_text(",\n".join(java) + "\n", encoding="utf-8")
    print(f"wrote {len(cands)} building sets ({len(cands) * 8 - len(reused)} new blocks); reused bricks: {reused}")


if CMD == "preview":
    preview()
elif CMD == "apply":
    apply()
else:
    sys.exit(__doc__)
