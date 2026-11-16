"""Write textures edited in game (Live Texture Editor) back into the mod's resources.
Usage: python -I tools/texture_pipeline/import_texture_pack.py <project> [pack.zip | pack folder] [--apply] [--all-namespaces]

In game: look at a block and press R (Live Texture Editor), paint, then export the edits as a resource pack; the mod
writes it to run/resourcepacks/<name>.zip. Without a pack argument the newest pack in run/resourcepacks/ is used.

Only assets/pysift/textures/**.png (and their .png.mcmeta) are taken; other namespaces (vanilla / other mods) are
listed but skipped unless --all-namespaces (they would then go to src/main/resources/assets/<ns>/..., i.e. the mod
would override them - normally not wanted). Entry names are checked, so a pack cannot write outside the textures folder.
Without --apply it only prints what would change (new / changed / unchanged). With --apply every file it replaces is
backed up to .texture_backups/<stamp>_texture_pack_import/ first; run tools/texture_pipeline/verify.py afterwards
(it lists PNGs changed outside recolor.py as "external" - expected here)."""
import sys, re, shutil, zipfile, datetime, hashlib
from pathlib import Path, PurePosixPath

P = Path(sys.argv[1]).resolve()
ARGS = [a for a in sys.argv[2:] if not a.startswith("--")]
APPLY = "--apply" in sys.argv
ALL_NS = "--all-namespaces" in sys.argv
RES = P / "src/main/resources"
PACKS = P / "run/resourcepacks"
STAMP = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
BK = P / ".texture_backups" / f"{STAMP}_texture_pack_import"
ENTRY = re.compile(r"^assets/([a-z0-9_.-]+)/textures/([a-z0-9_./-]+\.png(?:\.mcmeta)?)$")


def newest_pack():
    packs = [p for p in PACKS.glob("*") if p.suffix == ".zip" or (p.is_dir() and (p / "pack.mcmeta").exists())]
    if not packs:
        sys.exit(f"no resource packs in {PACKS} - export one from the texture editor first")
    return max(packs, key=lambda p: p.stat().st_mtime)


def entries(pack):
    """(posix name, bytes) of every file in a zip or folder pack."""
    if pack.is_dir():
        for f in pack.rglob("*"):
            if f.is_file():
                yield f.relative_to(pack).as_posix(), f.read_bytes()
    else:
        with zipfile.ZipFile(pack) as z:
            for info in z.infolist():
                if not info.is_dir():
                    yield info.filename, z.read(info)


def main():
    pack = Path(ARGS[0]).resolve() if ARGS else newest_pack()
    print("pack:", pack)
    counts = {"new": 0, "changed": 0, "same": 0, "skipped": 0}
    for name, data in entries(pack):
        m = ENTRY.match(name)
        parts = PurePosixPath(name).parts
        if not m or ".." in parts:
            continue
        ns = m.group(1)
        if ns != "pysift" and not ALL_NS:
            print(f"  skip (namespace {ns}): {name}")
            counts["skipped"] += 1
            continue
        dst = RES / name
        if dst.exists() and hashlib.sha1(dst.read_bytes()).digest() == hashlib.sha1(data).digest():
            counts["same"] += 1
            continue
        kind = "changed" if dst.exists() else "new"
        counts[kind] += 1
        print(f"  {kind:7s} {dst.relative_to(P)}")
        if APPLY:
            if dst.exists():
                b = BK / dst.relative_to(P)
                b.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(dst, b)
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(data)
    print(", ".join(f"{k} {v}" for k, v in counts.items()))
    if not APPLY and (counts["new"] or counts["changed"]):
        print("dry run - add --apply to write these files")
    elif APPLY and counts["changed"]:
        print("backups:", BK.relative_to(P))


main()
