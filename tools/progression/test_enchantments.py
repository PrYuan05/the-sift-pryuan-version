"""Check the Sift's enchantments on the running test server (./gradlew.bat runSiftTestServer) over RCON.
Usage: python -I tools/progression/test_enchantments.py <project> [part]
    part: load | items | hemorrhage | ward | rift | loot | all

What needs a real player (the javelin flying back, the dash, the fork, the horn) is checked by hand in game.
Builds at x 300.., y 120 in the Overworld and at the same spot in the Sift (forceloaded). PASS / FAIL per check;
exit 1 when something fails."""
import json
import re
import sys
import time
from pathlib import Path

P = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(P / "tools/worldgen"))
import devserver as d  # noqa: E402

OW = "execute in minecraft:overworld run "
SIFT = "execute in pysift:the_sift run "
X, Y, Z = 300, 120, 300
DATA = P / "src/main/resources/data"
fails = []


def r(cmd, where=OW):
    out = d.rcon(where + cmd)
    return out if isinstance(out, str) else " | ".join(map(str, out))


def expect(name, ok, detail=""):
    print(("PASS" if ok else "FAIL"), name + (f": {detail}" if detail else ""))
    if not ok:
        fails.append(name)


def tag(path):
    return json.loads((DATA / path).read_text(encoding="utf-8"))["values"]


EVERYDAY = ["pysift:hemorrhage", "pysift:ensnare", "pysift:rift_step", "pysift:soul_harvest", "pysift:aftershock", "pysift:resonance"]
TREASURE = ["pysift:soul_rend", "pysift:soul_ward", "pysift:afterimage", "pysift:harmony", "pysift:lament", "pysift:homecoming"]


def setup(where=OW):
    r(f"forceload add {X - 8} {Z - 8} {X + 8} {Z + 8}", where)
    r(f"kill @e[type=!minecraft:player,x={X - 8},y={Y - 4},z={Z - 8},dx=16,dy=12,dz=16]", where)
    r(f"fill {X - 6} {Y - 1} {Z - 6} {X + 6} {Y + 6} {Z + 6} minecraft:air", where)
    r(f"fill {X - 6} {Y - 1} {Z - 6} {X + 6} {Y - 1} {Z + 6} minecraft:stone", where)


def load():
    """No enchantment, enchantment tag or chest table failed to load."""
    log = (P / "run-server/logs/latest.log").read_text(encoding="utf-8", errors="replace")
    bad = [line for line in log.splitlines() if re.search(r"enchantment|pysift:chests|exclusive_set|enchantable", line)
           and re.search(r"(?i)error|couldn't|failed|unknown|missing", line)]
    expect("no enchantment or loot errors in the server log", not bad, "; ".join(b[:160] for b in bad[:3]))
    for e in EVERYDAY + TREASURE:
        out = r(f"enchant @e[tag=nobody_here] {e}")   # nobody matches: a real id gets "no entity", a wrong one a parse error
        expect(f"{e} is registered", "No entity was found" in out, out[:80])
    expect("treasure enchantments stay off the table, trades and random loot",
           not set(TREASURE) & set(tag("minecraft/tags/enchantment/in_enchanting_table.json") + tag("minecraft/tags/enchantment/tradeable.json")
                                   + tag("minecraft/tags/enchantment/on_random_loot.json")))
    expect("everyday enchantments are on the table", set(EVERYDAY) <= set(tag("minecraft/tags/enchantment/in_enchanting_table.json")))


def holder(item, name="holder"):
    r(f'summon minecraft:armor_stand {X} {Y} {Z} {{Tags:["{name}"],NoGravity:1b,ShowArms:1b}}')
    r(f"item replace entity @e[tag={name},limit=1] weapon.mainhand with {item}")


def items():
    """The enchant command follows supported_items: vanilla gear by kind, the Sift's items by name."""
    setup()
    cases = [("minecraft:diamond_sword", "pysift:hemorrhage", True), ("minecraft:bow", "pysift:ensnare", True),
             ("minecraft:diamond_pickaxe", "pysift:soul_harvest", True), ("minecraft:mace", "pysift:soul_rend", True),
             ("minecraft:trident", "pysift:ensnare", True), ("pysift:soul_javelin", "pysift:homecoming", True),
             ("pysift:soul_javelin", "pysift:hemorrhage", True), ("pysift:sculk_hammer", "pysift:soul_rend", True),
             ("pysift:dash_charm", "pysift:afterimage", True), ("pysift:tuning_fork", "pysift:harmony", True),
             ("pysift:mourning_horn", "pysift:lament", True), ("pysift:siftite_sword", "pysift:hemorrhage", True),
             ("minecraft:diamond_sword", "pysift:afterimage", False), ("minecraft:diamond_pickaxe", "pysift:hemorrhage", False),
             ("pysift:tuning_fork", "minecraft:unbreaking", True)]
    for item, ench, ok in cases:
        r("kill @e[tag=holder]")
        holder(item)
        out = r(f"enchant @e[tag=holder,limit=1] {ench}")
        took = "Applied enchantment" in out
        expect(f"{ench} on {item} {'accepted' if ok else 'refused'}", took == ok, out[:90])
    r("kill @e[tag=holder]")
    holder("pysift:diamond_sword" if False else "minecraft:diamond_sword")
    r("enchant @e[tag=holder,limit=1] pysift:soul_rend")
    out = r("enchant @e[tag=holder,limit=1] minecraft:fire_aspect")
    expect("Soul Rend and Fire Aspect do not go together", "Applied enchantment" not in out, out[:90])
    r("kill @e[tag=holder]")


def hemorrhage():
    """A Hemorrhage III sword makes a zombie bleed (45% a hit)."""
    setup()
    r("difficulty easy")
    # a zombie with the sword, shut in with a villager it wants to hit; the villager can take a lot of hits
    r(f'summon minecraft:villager {X + 1} {Y} {Z} {{Tags:["victim"],NoAI:1b,PersistenceRequired:1b,Health:500f,attributes:[{{id:"minecraft:max_health",base:500}}]}}')
    r(f'summon minecraft:vindicator {X - 1} {Y} {Z} {{Tags:["attacker"],PersistenceRequired:1b}}')
    r('item replace entity @e[tag=attacker,limit=1] weapon.mainhand with minecraft:diamond_sword[enchantments={"pysift:hemorrhage":3}]')
    bled = False
    for _ in range(40):
        time.sleep(0.5)
        if "pysift:bleeding" in r("data get entity @e[tag=victim,limit=1] active_effects"):
            bled = True
            break
    expect("Hemorrhage makes the target bleed", bled)
    r("kill @e[tag=attacker]")
    r("kill @e[tag=victim]")


def ward():
    """Soul Ward on a chestplate: Soul Deprivation cannot be applied (every direct source asks canBeAffected first)."""
    setup()
    r(f'summon minecraft:husk {X} {Y} {Z} {{Tags:["warded"],NoAI:1b,PersistenceRequired:1b}}')
    r('item replace entity @e[tag=warded,limit=1] armor.chest with minecraft:iron_chestplate[enchantments={"pysift:soul_ward":1}]')
    r(f'summon minecraft:husk {X + 2} {Y} {Z} {{Tags:["bare"],NoAI:1b,PersistenceRequired:1b}}')
    r("effect give @e[tag=warded] pysift:soul_deprivation 10")
    r("effect give @e[tag=bare] pysift:soul_deprivation 10")
    time.sleep(0.3)
    expect("Soul Ward blocks Soul Deprivation", "soul_deprivation" not in r("data get entity @e[tag=warded,limit=1] active_effects"))
    expect("without it Soul Deprivation still takes", "soul_deprivation" in r("data get entity @e[tag=bare,limit=1] active_effects"))
    r("kill @e[tag=warded]")
    r("kill @e[tag=bare]")


def rift():
    """Rift Step adds movement speed on the ground in the Sift and nowhere else.
    The game re-tests it when the wearer steps into a new block while on the ground, so an armor stand is dropped
    into a new block twice (a mob's own walking is not reliable: it may stand still for the whole test)."""
    found = {}
    for where, label in ((OW, "Overworld"), (SIFT, "Sift")):
        setup(where)
        r(f'summon minecraft:armor_stand {X}.5 {Y} {Z}.5 {{Tags:["walker"]}}', where)
        r('item replace entity @e[tag=walker,limit=1] armor.feet with minecraft:iron_boots[enchantments={"pysift:rift_step":3}]', where)
        for step in range(2):
            r(f"tp @e[tag=walker,limit=1] {X + step + 1}.5 {Y + 1.5} {Z}.5", where)
            time.sleep(1.0)
        now = re.search(r"is (-?[0-9.]+)", r("attribute @e[tag=walker,limit=1] minecraft:movement_speed get", where))
        base = re.search(r"is (-?[0-9.]+)", r("attribute @e[tag=walker,limit=1] minecraft:movement_speed base get", where))
        found[label] = (float(now.group(1)) - float(base.group(1))) if now and base else None
        r("kill @e[tag=walker]", where)
    expect("Rift Step III adds 0.03 speed in the Sift", found["Sift"] is not None and abs(found["Sift"] - 0.03) < 0.002, f"+{found['Sift']}")
    expect("Rift Step does nothing in the Overworld", found["Overworld"] is not None and abs(found["Overworld"]) < 1e-6, f"+{found['Overworld']}")


def loot():
    """Sift chests hold treasure books only, and the Echo Den vault always has one."""
    setup()
    seen, vault_books = set(), 0
    for i in range(20):
        r(f"setblock {X} {Y} {Z} minecraft:air")
        r(f"setblock {X} {Y} {Z} minecraft:chest")
        r(f"loot insert {X} {Y} {Z} loot pysift:chests/echo_den_vault")
        items = r(f"data get block {X} {Y} {Z} Items")
        books = re.findall(r'"minecraft:stored_enchantments": \{([^}]*)\}', items)
        vault_books += 1 if books else 0
        for b in books:
            seen |= set(re.findall(r'"([a-z_]+:[a-z_]+)"', b))
    expect("the Echo Den vault always holds a book", vault_books == 20, f"{vault_books}/20")
    expect("only Sift treasure enchantments come out of the chests", seen and seen <= set(TREASURE), ", ".join(sorted(seen)))
    r(f"setblock {X} {Y} {Z} minecraft:air")


parts = {"load": load, "items": items, "hemorrhage": hemorrhage, "ward": ward, "rift": rift, "loot": loot}
which = sys.argv[2] if len(sys.argv) > 2 else "all"
for name, f in parts.items():
    if which in ("all", name):
        print(f"--- {name}")
        f()
print("FAILED: " + ", ".join(fails) if fails else "ALL PASS")
sys.exit(1 if fails else 0)
