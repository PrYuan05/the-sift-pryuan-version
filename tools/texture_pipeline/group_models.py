"""Put loose models/block/<name>.json files into the folder of their block (longest blockstate-id prefix), rewriting every
reference (uses move_assets.py). Generators call this when they finish, so a re-run never leaves models at the root.
Usage: python -I tools/texture_pipeline/group_models.py <project>   (nothing to do -> prints 0 and exits)"""
import json, subprocess, sys
from pathlib import Path

P = Path(sys.argv[1]).resolve()
A = P / "src/main/resources/assets/pysift"
ids = sorted({f.stem for f in (A / "blockstates").glob("*.json")}, key=len, reverse=True)
plan = []
for f in sorted((A / "models/block").glob("*.json")):
    base = next((i for i in ids if f.stem == i or f.stem.startswith(i + "_")), f.stem)
    dst = A / "models/block" / base / f.name
    if dst.exists():                      # a generator just rewrote this model: the fresh loose file wins
        dst.unlink()
    plan.append(("models", f"block/{f.stem}", f"block/{base}/{f.stem}"))
if not plan:
    print("0 loose block models")
    sys.exit(0)
out = P / "build/texture_pipeline/move_plan.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
subprocess.run([sys.executable, "-I", str(Path(__file__).with_name("move_assets.py")), str(P), "--apply"], check=True)
