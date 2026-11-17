"""Treasure enchantment books in the Sift's structure chests (the Sift-only enchantments, #pysift:sift_treasure;
tools/progression/build_enchantments.py).

Used two ways:
  - imported by tools/worldgen/build_structures.py and build_landmarks.py, which add book_pool(name) to every chest
    table they write, so a regeneration keeps the books;
  - run on its own to add the pool to the chest tables already in the mod without regenerating any structure:
        python -I tools/worldgen/loot_books.py <project>
    It is idempotent: a table that already has the pool is left alone.

The pool gives one enchanted book (a random Sift treasure enchantment at a random level) in a quarter of the chests,
and always in the Echo Den vault. The loot function format follows vanilla 26.3 (chests/ancient_city.json):
an item entry with a "modifier" of type minecraft:enchant_randomly and "options"."""
import json
import sys
from pathlib import Path

TAG = "#pysift:sift_treasure"
GUARANTEED = {"echo_den_vault"}
BOOK = {"type": "minecraft:item", "name": "minecraft:book", "weight": 1,
        "modifier": [{"type": "minecraft:enchant_randomly", "options": TAG}]}


def book_pool(name):
    """The extra pool for the chest table `name` (chests/<name>.json)."""
    entries = [BOOK] if name in GUARANTEED else [BOOK, {"type": "minecraft:empty", "weight": 3}]
    return {"rolls": 1, "entries": entries}


def has_books(table):
    return any(e.get("name") == "minecraft:book" and TAG in json.dumps(e.get("modifier", ""))
               for pool in table.get("pools", []) for e in pool.get("entries", []))


if __name__ == "__main__":
    P = Path(sys.argv[1]).resolve()
    D = P / "src/main/resources/data/pysift"
    for folder in ("loot_table", "loot_tables"):
        for f in sorted((D / folder / "chests").glob("*.json")):
            raw = f.read_bytes()
            table = json.loads(raw.decode("utf-8"))
            if has_books(table):
                continue
            table["pools"].append(book_pool(f.stem))
            text = json.dumps(table, indent=2, ensure_ascii=False) + "\n"
            f.write_bytes((text.replace("\n", "\r\n") if b"\r\n" in raw else text).encode("utf-8"))
            print(f"{folder}/chests/{f.stem}: added the treasure book pool")
