"""Build a running soul power showcase next to the first online player on the test server (RCON), so every machine,
part and effect is in front of the camera. Usage: python -I tools/progression/showcase_soul_power.py <project>"""
import re, sys
from pathlib import Path

P = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(P / "tools/worldgen"))
import devserver as d  # noqa: E402

OW = "execute in minecraft:overworld run "
FUEL = '{Fuel:{id:"pysift:spirit_liquid_bucket",count:1}}'


def r(cmd):
    out = d.rcon(OW + cmd)
    return out if isinstance(out, str) else " | ".join(map(str, out))


who = d.rcon("list")
who = who if isinstance(who, str) else " ".join(who)
name = who.rsplit(":", 1)[-1].strip().split(",")[0].strip()
print("player:", name)
X, Y, Z = 300, 140, 300
r(f"forceload add {X - 10} {Z - 10} {X + 30} {Z + 30}")
r(f"fill {X - 6} {Y - 1} {Z - 6} {X + 26} {Y + 8} {Z + 20} minecraft:air")
r(f"fill {X - 6} {Y - 1} {Z - 6} {X + 26} {Y - 1} {Z + 20} minecraft:polished_deepslate")
r(f"time set noon")
r(f"gamerule doDaylightCycle false")
# row 1: engine -> shaft -> cog train -> gauge -> grinder (with cobblestone)
r(f"setblock {X} {Y} {Z} pysift:spirit_engine[facing=north]{FUEL}")
r(f"setblock {X + 1} {Y} {Z} pysift:soul_shaft[axis=x]")
r(f"setblock {X + 2} {Y} {Z} pysift:soul_cogwheel[axis=x]")
r(f"setblock {X + 2} {Y + 1} {Z} pysift:soul_cogwheel[axis=x]")
r(f"setblock {X + 2} {Y + 2} {Z + 1} pysift:large_soul_cogwheel[axis=x]")
r(f"setblock {X + 3} {Y} {Z} pysift:soul_gauge[axis=x]")
r(f"setblock {X + 4} {Y} {Z} pysift:soul_grinder[facing=north]" + '{Slot0:{id:"minecraft:cobblestone",count:64}}')
r(f"setblock {X + 5} {Y} {Z} pysift:soul_shaft[axis=x]")
r(f"setblock {X + 6} {Y} {Z} pysift:soul_gearshift[axis=x]")
r(f"setblock {X + 7} {Y} {Z} pysift:soul_shaft[axis=x]")
r(f"setblock {X + 8} {Y} {Z} pysift:soul_fan[facing=east]")
r(f"setblock {X + 11} {Y - 1} {Z} minecraft:soul_soil")
r(f"setblock {X + 11} {Y} {Z} minecraft:soul_fire")
# row 2: engine -> sifter on blue sculk; beam over a prism; wave pair
r(f"fill {X - 4} {Y - 1} {Z + 4} {X + 4} {Y - 1} {Z + 8} minecraft:sculk")
r(f"setblock {X} {Y} {Z + 6} pysift:soul_sifter[facing=north]" + '{Slot0:{id:"minecraft:sculk",count:16}}')
r(f"setblock {X + 1} {Y} {Z + 6} pysift:spirit_engine[facing=north]{FUEL}")
r(f"setblock {X + 6} {Y} {Z + 6} pysift:spirit_engine[facing=north]{FUEL}")
r(f"setblock {X + 7} {Y} {Z + 6} pysift:charoite_beam_emitter[facing=east]")
r(f"setblock {X + 13} {Y} {Z + 6} pysift:charoite_prism[facing=south]")
r(f"setblock {X + 13} {Y} {Z + 11} pysift:charoite_beam_receiver[facing=north]")
r(f"setblock {X + 13} {Y} {Z + 12} pysift:soul_grinder[facing=north]" + '{Slot0:{id:"minecraft:gravel",count:64}}')
disc = '{Disc:{id:"minecraft:music_disc_pigstep",count:1}}'
# resonance array
cx, cz = X + 20, Z + 12
r(f"setblock {cx} {Y - 1} {cz} pysift:spirit_engine[facing=north]{FUEL}")
r(f'setblock {cx} {Y} {cz} pysift:resonance_core{{Item:{{id:"minecraft:amethyst_shard",count:1}}}}')
items = ["minecraft:sculk"] * 4 + ["pysift:soul_essence"] * 4
for (dx, dz), it in zip([(3, 0), (-3, 0), (0, 3), (0, -3), (3, 3), (-3, -3), (3, -3), (-3, 3)], items):
    r(f'setblock {cx + dx} {Y} {cz + dz} pysift:resonance_pedestal{{Item:{{id:"{it}",count:1}}}}')
# vein node pair through stone, pump from a pool
r(f"fill {X - 4} {Y} {Z + 14} {X + 6} {Y + 2} {Z + 16} minecraft:stone")
r(f"setblock {X - 5} {Y + 1} {Z + 15} pysift:spirit_engine[facing=north]{FUEL}")
r(f"setblock {X - 4} {Y + 1} {Z + 15} pysift:soul_vein_node")
r(f"setblock {X + 6} {Y + 1} {Z + 15} pysift:soul_vein_node")
r(f"setblock {X + 7} {Y + 1} {Z + 15} pysift:soul_hand_crank[facing=east]")
# camera
r(f"tp {name} {X + 8} {Y + 6} {Z - 7} 25 30")
r(f"gamemode spectator {name}")
print("built")
