"""把食腐獸／潛伏獵手／Trapper／Hunter 共用的 128x128 合併貼圖拆成四張 64x64，並把現有兩個模型的 UV 換算到新圖。
Usage: python -I tools/models/split_scavenger_sheet.py
  左上 → scavenger.png，右上 → stalker.png（UV x 減 64），左下 → trapper.png，右下 → hunter.png。
  沒人用的 scavenger_stalker.png 移到備份。原檔先備份到 .texture_backups/<stamp>_split_sheet/。"""
import json, shutil, datetime
from pathlib import Path
from PIL import Image

P = Path(__file__).resolve().parents[2]
A = P / "src/main/resources/assets/pysift"
T = A / "textures/entity"
G = A / "geckolib/models/entity"
BK = P / ".texture_backups" / (datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + "_split_sheet")
QUAD = {"scavenger": (0, 0), "stalker": (64, 0), "trapper": (0, 64), "hunter": (64, 64)}


def backup(p):
    if p.exists():
        BK.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, BK / p.name)


def main():
    sheet = Image.open(T / "scavenger.png").convert("RGBA")
    assert sheet.size == (128, 128), "already split?"
    for name, (ox, oy) in QUAD.items():
        p = T / f"{name}.png"
        backup(p)
        sheet.crop((ox, oy, ox + 64, oy + 64)).save(p)
    for name in ("scavenger", "stalker"):
        ox, oy = QUAD[name]
        p = G / f"{name}.geo.json"
        backup(p)
        doc = json.loads(p.read_text(encoding="utf-8"))
        geo = doc["minecraft:geometry"][0]
        geo["description"]["texture_width"] = geo["description"]["texture_height"] = 64
        for b in geo["bones"]:
            for c in b.get("cubes", []):
                for f in (c.get("uv") or {}).values():
                    f["uv"] = [f["uv"][0] - ox, f["uv"][1] - oy]
        p.write_text(json.dumps(doc, ensure_ascii=False, indent="\t") + "\n", encoding="utf-8")
    old = T / "scavenger_stalker.png"
    if old.exists():
        BK.mkdir(parents=True, exist_ok=True)
        shutil.move(str(old), BK / old.name)
    print("split; backups in", BK)


if __name__ == "__main__":
    main()
