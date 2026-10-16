"""Generate dedicated top/bottom textures for composite faces that have no good match in the library.
Usage: python -I tools/texture_pipeline/generate_faces.py <project> [--dry-run]

Reads build/texture_pipeline/out/refit_faces_report.json (run refit_faces.py first). For every face whose best
score is above face_rules.json max_band_delta, the closest existing texture is recoloured onto the colours of
the side band it meets (rank mode: brightness order of the source kept, colour proportions of the band;
--regenerate rebuilds faces that were generated before) and saved as a NEW file
textures/block/<block>/<block>_<face>.png. Existing PNGs are never touched. Each file is logged in
recolor_manifest.json (mode "generated") and registered in face_rules.json "generated_faces"; run
refit_faces.py afterwards to wire it into the models. Undo with: recolor.py revert <block>:<face>"""
import sys, datetime
from pathlib import Path
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from palette_lib import project_paths, lj, wj, res_path, sha1, Tex, remap_rank

P, RES, A, D = project_paths(sys.argv[1])
ASSETS = RES / "assets"
HERE = Path(__file__).resolve().parent
OUT = P / "build/texture_pipeline/out"
DRY = "--dry-run" in sys.argv
RULES = lj(HERE / "face_rules.json")
T = Image.Transpose
ORIENT = {"none": None, "vflip": T.FLIP_TOP_BOTTOM, "rot90": T.ROTATE_270, "rot270": T.ROTATE_90}
TH = RULES["max_band_delta"]


class ImgTex(Tex):
    def __init__(self, image):
        from palette_lib import palette
        self.image = image.convert("RGB")
        px = self.image.load()
        self.grid = [[px[x, y] for x in range(16)] for y in range(16)]
        self.pal = palette([c for row in self.grid for c in row])


report = lj(OUT / "refit_faces_report.json")
man = lj(HERE / "recolor_manifest.json") if (HERE / "recolor_manifest.json").exists() else {"entries": []}
by_file = {e["file"]: e for e in man["entries"]}
gen = RULES.setdefault("generated_faces", {})
stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
made = []
for r in report:
    if r.get("kind") != "grass":
        continue
    side = Tex(r["sides"][0], ASSETS)
    o = side.image.transpose(ORIENT[r["transform"]]) if ORIENT[r["transform"]] else side.image
    ot = ImgTex(o)
    for face in ("top", "bottom"):
        regen = "--regenerate" in sys.argv and face in gen.get(r["block"], {})
        if not regen and (face in gen.get(r["block"], {}) or r[f"{face}_delta"][0] <= TH):
            continue
        if regen:  # rebuild from the library texture that was closest before the generated face existed
            r[face] = [by_file[f"textures/block/{r['block']}/{r['block']}_{face}.png"]["source"]]
        band = ot.band(face)
        source = r[face][0]
        new = remap_rank(Tex(source, ASSETS).image, band["band_px"])
        name = f"{r['block']}_{face}"
        path = A / "textures/block" / r["block"] / f"{name}.png"
        ref = f"pysift:block/{r['block']}/{name}"
        made.append((r["block"], face, source, r[f"{face}_delta"][0], ref))
        if DRY:
            continue
        assert not path.exists() or path.relative_to(A).as_posix() in by_file, f"refusing to overwrite {path}"
        path.parent.mkdir(parents=True, exist_ok=True)
        new.save(path)
        rel = path.relative_to(A).as_posix()
        by_file[rel] = {"file": rel, "pool": f"{r['block']}:{face}", "reference": f"{face} band of {r['sides'][0]} ({r['transform']})",
                        "source": source, "mode": "generated", "method": "rank", "sha1_before": None, "sha1_after": sha1(path),
                        "backup": None, "date": stamp}
        gen.setdefault(r["block"], {})[face] = ref

if not DRY:
    man["entries"] = sorted(by_file.values(), key=lambda e: e["file"])
    wj(HERE / "recolor_manifest.json", man)
    wj(HERE / "face_rules.json", RULES)
for b, f, src, d, ref in made:
    print(f"{b:34s} {f:6s} from {src.rsplit('/', 1)[1]:34s} (was {d}) -> {ref.rsplit('/', 1)[1]}")
print(f"{'would generate' if DRY else 'generated'} {len(made)} textures")
