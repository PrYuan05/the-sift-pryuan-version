"""Rename block ids everywhere: Java, resources, data, tools, file / folder names and structure NBT.
Usage: python -I tools/rename_block_ids.py <project> [--apply]

RENAMES: old id -> new id (numbered ids such as void_capped_crimson_01 get names that say what they are, from their zh
names). Without --apply it only checks (collisions, every file that would change). With --apply:
  - every text file under src/ and tools/ (.java .json .py .md .mcmeta .txt): the old id as a whole word is replaced,
    including "<id>_1" style model variant names; lines that point into .texture_backups/ are left alone
  - files and folders whose name contains an old id are renamed (deepest first)
  - structure .nbt files: string tags "pysift:<old>" are rewritten (NBT read / write from import_structures.py)
"""
import gzip, re, sys
from pathlib import Path

P = Path(sys.argv[1]).resolve()
APPLY = "--apply" in sys.argv
sys.path.insert(0, str(P / "tools/worldgen"))
from import_structures import read_nbt, write_nbt

RENAMES = {
    "amber_capped_stone_01": "mottled_amber_capped_stone",       # 斑駁琥珀覆蓋灰石岩
    "amber_capped_stone_02": "pale_amber_capped_stone",          # 淡沙琥珀覆蓋灰石岩
    "amber_capped_stone_03": "olive_amber_capped_stone",         # 橄欖琥珀覆蓋灰石岩
    "ash_capped_crimson_01": "ash_capped_crimson",
    "ash_capped_dark_slate_01": "plain_ash_capped_dark_slate",   # 平滑灰白覆蓋深板岩
    "ash_capped_dark_slate_02": "speckled_ash_capped_dark_slate",
    "ash_capped_violet_01": "ash_capped_violet",
    "crimson_capped_crimson_strata_2": "grove_capped_crimson_strata",    # 柳林赤紅覆蓋赤紅地層岩
    "crimson_capped_crimson_strata_3": "canyon_capped_crimson_strata",   # 峽谷赤紅覆蓋赤紅地層岩
    "crimson_capped_violet_strata_2": "streaked_crimson_capped_violet_strata",   # 垂紋
    "crimson_capped_void_01": "crimson_capped_void_stone",
    "dark_slate_capped_ash_01": "dark_slate_capped_ash",
    "dark_slate_capped_rose_01": "dark_slate_capped_rose",
    "rose_capped_dark_slate_01": "rose_capped_dark_slate",
    "rose_capped_stone_01": "rose_capped_stone",
    "stone_capped_amber_01": "mossy_stone_capped_amber",         # 苔斑灰石覆蓋琥珀岩
    "stone_capped_amber_02": "umber_stone_capped_amber",         # 褐土
    "stone_capped_amber_03": "pale_stone_capped_amber",          # 淡斑
    "stone_capped_rose_01": "stone_capped_rose",
    "stone_capped_violet_01": "stone_capped_violet",
    "teal_capped_gray_strata_2": "red_spotted_teal_capped_gray_strata",   # 赤斑
    "teal_capped_teal_strata_2": "bright_teal_capped_teal_strata",        # 亮青碧
    "void_capped_crimson_01": "capped_crimson_vein_stone",       # caps crimson_vein_stone on the Lullaby plateaus
}
PAT = re.compile(r"(?<![a-z0-9_])(" + "|".join(sorted(map(re.escape, RENAMES), key=len, reverse=True)) + r")(?![a-z0-9])")
TEXT = {".java", ".json", ".py", ".md", ".mcmeta", ".txt"}
ROOTS = [P / "src", P / "tools"]


def sub(text):
    return PAT.sub(lambda m: RENAMES[m[1]], text)


def main():
    existing = {f.stem for f in (P / "src/main/resources/assets/pysift/blockstates").glob("*.json")}
    clash = [n for n in RENAMES.values() if n in existing]
    assert not clash, f"new ids already exist: {clash}"
    assert len(set(RENAMES.values())) == len(RENAMES), "two old ids map to one new id"
    changed_files, renamed, nbt = [], [], []
    for root in ROOTS:
        for f in root.rglob("*"):
            if f.is_file() and f.suffix in TEXT and f != Path(__file__).resolve():
                t = f.read_text(encoding="utf-8", errors="strict")
                lines = t.split("\n")
                new = "\n".join(l if ".texture_backups" in l else sub(l) for l in lines)
                if new != t:
                    changed_files.append(f)
                    if APPLY:
                        f.write_text(new, encoding="utf-8")
    for f in (P / "src/main/resources/data").rglob("*.nbt"):
        raw = gzip.decompress(f.read_bytes())
        if not PAT.search(raw.decode("latin-1")):
            continue
        name, root = read_nbt(raw)

        def walk(t, v):
            if t == 8:
                return sub(v)
            if t == 9:
                et, items = v
                return (et, [walk(et, i) for i in items])
            if t == 10:
                return {k: (tt, walk(tt, vv)) for k, (tt, vv) in v.items()}
            return v
        nbt.append(f)
        if APPLY:
            f.write_bytes(write_nbt(name, walk(10, root)))
    paths = [p for root in ROOTS for p in root.rglob("*") if PAT.search(p.name)]
    for p in sorted(paths, key=lambda p: len(p.parts), reverse=True):   # deepest first
        target = p.with_name(sub(p.name))
        renamed.append((p, target))
        if APPLY:
            p.rename(target)
    print(f"text files: {len(changed_files)}, renamed paths: {len(renamed)}, structures: {len(nbt)}")
    for f in changed_files:
        if f.suffix == ".java" or "worldgen" in f.as_posix() and f.suffix == ".py":
            print("  ", f.relative_to(P))
    for f in nbt:
        print("   nbt", f.relative_to(P))


if __name__ == "__main__":
    main()
