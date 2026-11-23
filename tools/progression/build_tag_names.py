"""Names for the pysift item tags that had none, so recipe viewers (JEI / EMI / REI) show a readable tag name and
Fabric's "Untranslated Item Tags" dev warning goes away. Key format: tag.item.<namespace>.<path with / as .>.
Merges into both lang files (LF line endings); safe to re-run.

Run from the project root:  python -I tools/progression/build_tag_names.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "src/main/resources/assets/pysift"
TAGS_DIR = ROOT / "src/main/resources/data/pysift/tags/item"

# tag path (under pysift:) -> (English, Traditional Chinese)
NAMES = {
    "arrow_spines": ("Arrow Spines", "箭矢尖刺"),
    "aurum_tool_materials": ("Aurum Tool Materials", "金銀合金工具材料"),
    "enchantable/dash_charm": ("Dash Charm", "衝刺護符"),
    "enchantable/hemorrhage": ("Hemorrhage Targets", "可附放血的武器"),
    "enchantable/javelin": ("Soul Javelins", "靈魂標槍"),
    "enchantable/mourning_horn": ("Mourning Horns", "哀悼號角"),
    "enchantable/ranged": ("Ranged Weapons", "遠程武器"),
    "enchantable/sculk_hammer": ("Sculk Hammers", "幽匿重錘"),
    "enchantable/sonic_staff": ("Sonic Staffs", "音波法杖"),
    "enchantable/soul_rend": ("Soul Rend Targets", "可附靈魂撕裂的武器"),
    "enchantable/soul_ward": ("Soul Ward Targets", "可附靈魂護佑的護甲"),
    "enchantable/tuning_fork": ("Tuning Forks", "調音叉"),
}

# every pysift item tag must be named: fail loudly when a new tag is added without a name
existing = {p.relative_to(TAGS_DIR).with_suffix("").as_posix() for p in TAGS_DIR.rglob("*.json")}
lang_have = json.loads((A / "lang/en_us.json").read_text(encoding="utf-8"))
missing = sorted(t for t in existing
                 if t not in NAMES and "tag.item.pysift." + t.replace("/", ".") not in lang_have)
if missing:
    raise SystemExit("item tags without a name (add them to NAMES): " + ", ".join(missing))

for lang, i in (("en_us", 0), ("zh_tw", 1)):
    f = A / f"lang/{lang}.json"
    data = json.loads(f.read_text(encoding="utf-8"))
    for tag, names in NAMES.items():
        data["tag.item.pysift." + tag.replace("/", ".")] = names[i]
    f.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")

print(f"{len(NAMES)} item tag names written; {len(existing)} pysift item tags all named")
