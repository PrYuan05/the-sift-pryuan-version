"""Bring structures the user edited in game back into the mod.
Usage: python -I tools/worldgen/import_structures.py <world folder> [name filter]
  e.g. python -I tools/worldgen/import_structures.py "run/saves/新的世界 (6)"

Workflow: /pysift_showcase lays every landmark template out with a structure block set to SAVE next to it; the user edits
the build and presses SAVE, which writes <world>/generated/pysift/structure/<name>.nbt. This script copies those files to
src/main/resources/data/pysift/structure/<name>.nbt and lists them in tools/worldgen/art/edited_structures.json, so
tools/worldgen/build_landmarks.py stops overwriting them. Showcase-only entity tags (NoAI, Silent) are removed on the way."""
import gzip, io, json, struct, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / "src/main/resources/data/pysift/structure"
EDITED = ROOT / "tools/worldgen/art/edited_structures.json"


# ---------------- NBT (read and write, keeping every tag type)
def read_nbt(data):
    pos = 0

    def take(n):
        nonlocal pos
        out = data[pos:pos + n]
        pos += n
        return out

    def string():
        return take(struct.unpack(">H", take(2))[0]).decode("utf-8")

    def payload(t):
        if t == 1: return struct.unpack(">b", take(1))[0]
        if t == 2: return struct.unpack(">h", take(2))[0]
        if t == 3: return struct.unpack(">i", take(4))[0]
        if t == 4: return struct.unpack(">q", take(8))[0]
        if t == 5: return struct.unpack(">f", take(4))[0]
        if t == 6: return struct.unpack(">d", take(8))[0]
        if t == 7: return take(struct.unpack(">i", take(4))[0])
        if t == 8: return string()
        if t == 9:
            et, n = take(1)[0], struct.unpack(">i", take(4))[0]
            return (et, [payload(et) for _ in range(n)])
        if t == 10:
            out = {}
            while True:
                tt = take(1)[0]
                if tt == 0:
                    return out
                k = string()
                out[k] = (tt, payload(tt))
        if t == 11: return _ints(4, "i")
        if t == 12: return _ints(8, "q")
        raise ValueError(t)

    def _ints(size, fmt):
        n = struct.unpack(">i", take(4))[0]
        return list(struct.unpack(f">{n}{fmt}", take(size * n)))

    t = take(1)[0]
    name = string()
    return name, payload(t)


def write_nbt(name, root):
    def s(text):
        b = text.encode("utf-8")
        return struct.pack(">H", len(b)) + b

    def payload(t, v):
        if t == 1: return struct.pack(">b", v)
        if t == 2: return struct.pack(">h", v)
        if t == 3: return struct.pack(">i", v)
        if t == 4: return struct.pack(">q", v)
        if t == 5: return struct.pack(">f", v)
        if t == 6: return struct.pack(">d", v)
        if t == 7: return struct.pack(">i", len(v)) + v
        if t == 8: return s(v)
        if t == 9:
            et, items = v
            return bytes([et]) + struct.pack(">i", len(items)) + b"".join(payload(et, i) for i in items)
        if t == 10: return b"".join(bytes([tt]) + s(k) + payload(tt, vv) for k, (tt, vv) in v.items()) + b"\x00"
        if t == 11: return struct.pack(f">i{len(v)}i", len(v), *v)
        if t == 12: return struct.pack(f">i{len(v)}q", len(v), *v)
        raise ValueError(t)

    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode="wb", mtime=0) as gz:
        gz.write(b"\x0a" + s(name) + payload(10, root))
    return buf.getvalue()


SHOWCASE_ONLY = ("NoAI", "Silent")


def clean(root):
    """Drop the showcase-only flags from saved entities."""
    entities = root.get("entities", (9, (10, [])))[1][1]
    for e in entities:
        nbt = e.get("nbt", (10, {}))[1]
        for k in SHOWCASE_ONLY:
            nbt.pop(k, None)
    return len(entities)


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    world = Path(sys.argv[1])
    flt = sys.argv[2] if len(sys.argv) > 2 else ""
    saved = sorted((world / "generated/pysift").glob("structure*/**/*.nbt"))
    if not saved:
        raise SystemExit(f"No saved structures under {world / 'generated/pysift'} (press SAVE on the structure blocks first)")
    edited = set(json.loads(EDITED.read_text(encoding="utf-8"))) if EDITED.exists() else set()
    for f in saved:
        base = next(p for p in f.parents if p.name.startswith("structure"))
        name = f.relative_to(base).with_suffix("").as_posix()
        if flt and flt not in name:
            continue
        tag_name, root = read_nbt(gzip.decompress(f.read_bytes()))
        mobs = clean(root)
        out = DEST / f"{name}.nbt"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(write_nbt(tag_name, root))
        edited.add(name)
        print(f"imported {name} ({len(root['blocks'][1][1])} blocks, {mobs} mobs) -> {out.relative_to(ROOT)}")
    EDITED.parent.mkdir(parents=True, exist_ok=True)
    EDITED.write_text(json.dumps(sorted(edited), indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
