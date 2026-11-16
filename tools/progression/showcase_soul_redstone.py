"""Build a running soul redstone showcase next to the first online player on the test server (RCON), so every look
of the conduit, the vanilla hook-ups, the machines and the sculk hooks are in front of the camera.
Usage: python -I tools/progression/showcase_soul_redstone.py <project>      (mechanical add-on off)

Rows, from the camera (looking south), left to right along +x:
  z+0   engine -> 30 conduits: the red soul signal fading out; a lamp every 4 blocks; a riser up and over;
        on the north side a hopper, dust, a powered rail, a repeater, a piston, a comparator and a note block
  z+4   lever -> conduits -> lamp (dead blue: a vanilla signal, the grinder on it stays still); beside it an unpowered wire
  z+8   engine -> conduit -> gauge -> grinder, drill, fan through soul fire, sifter on blue sculk
  z+12  redstone block on a grinder (paused) and on an engine (off)
  z+16  beam over a prism into a grinder; a conduit line wrapped in blocks
  z+22  sculk catalyst -> conduit -> fan (kill the pig: /kill @e[type=pig]); overloaded circuit with a shrieker"""
import sys
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
r(f"forceload add {X - 10} {Z - 10} {X + 40} {Z + 44}")
r(f"kill @e[type=!minecraft:player,x={X - 6},y={Y - 2},z={Z - 6},dx=42,dy=12,dz=42]")
r(f"fill {X - 6} {Y - 1} {Z - 6} {X + 36} {Y + 6} {Z + 36} minecraft:air")
r(f"fill {X - 6} {Y - 1} {Z - 6} {X + 36} {Y - 1} {Z + 36} minecraft:polished_deepslate")
r("time set midnight")                       # the glow shows best in the dark
r("gamerule advance_time false")
r("gamerule spawn_monsters false")

# ---- row 0: range and decay
for x in range(4, 30, 4):                    # lamps first: a block placed by /setblock does not look at its neighbours
    r(f"setblock {X + x} {Y} {Z + 1} minecraft:redstone_lamp")
# vanilla parts on the north side: the conduit plugs into full blocks and bends down to floor-level parts
r(f"setblock {X + 6} {Y} {Z - 1} minecraft:hopper")
r(f"setblock {X + 8} {Y} {Z - 1} minecraft:redstone_wire")
r(f"setblock {X + 8} {Y} {Z - 2} minecraft:redstone_wire")
r(f"setblock {X + 10} {Y} {Z - 1} minecraft:powered_rail[shape=north_south]")
r(f"setblock {X + 10} {Y} {Z - 2} minecraft:powered_rail[shape=north_south]")
r(f"setblock {X + 12} {Y} {Z - 1} minecraft:repeater[facing=south]")
r(f"setblock {X + 12} {Y} {Z - 2} minecraft:redstone_lamp")
r(f"setblock {X + 14} {Y} {Z - 1} minecraft:sticky_piston[facing=north]")
r(f"setblock {X + 16} {Y} {Z - 1} minecraft:comparator[facing=south]")
r(f"setblock {X + 18} {Y} {Z - 1} minecraft:note_block")
r(f"fill {X + 1} {Y} {Z} {X + 31} {Y} {Z} pysift:soul_conduit")
r(f"fill {X + 2} {Y + 1} {Z} {X + 2} {Y + 4} {Z} pysift:soul_conduit")          # riser
r(f"fill {X + 2} {Y + 4} {Z - 1} {X + 2} {Y + 4} {Z - 3} pysift:soul_conduit")  # and across, through the air
r(f"setblock {X + 2} {Y + 4} {Z - 4} minecraft:redstone_lamp")
r(f"setblock {X} {Y} {Z} pysift:spirit_engine[facing=north]{FUEL}")

# ---- row 1: a vanilla signal on the wire (blue), and an unpowered wire (grey)
z = Z + 4
r(f"setblock {X} {Y} {z} minecraft:lever[face=floor,powered=false]")
r(f"fill {X + 1} {Y} {z} {X + 8} {Y} {z} pysift:soul_conduit")
r(f"setblock {X + 9} {Y} {z} minecraft:redstone_lamp")
r(f"setblock {X + 5} {Y} {z + 1} pysift:soul_grinder[facing=north]" + '{Slot0:{id:"minecraft:cobblestone",count:64}}')
r(f"setblock {X + 3} {Y} {z - 1} minecraft:redstone_wire")
r(f"setblock {X} {Y} {z} minecraft:lever[face=floor,powered=true]")
r(f"fill {X + 14} {Y} {z} {X + 20} {Y} {z} pysift:soul_conduit")                  # nothing feeds this one
r(f"setblock {X + 13} {Y} {z} minecraft:lever[face=floor,powered=false]")
# small parts that do not sit against the conduit: a tendril reaches them (client/soulpower/ConduitRenderer)
r(f"setblock {X + 15} {Y} {z - 1} minecraft:stone_button[face=floor,facing=north]")
r(f"setblock {X + 17} {Y} {z - 2} minecraft:polished_deepslate")
r(f"setblock {X + 17} {Y} {z - 1} minecraft:stone_button[face=wall,facing=south]")      # on the far wall of its cell
r(f"setblock {X + 19} {Y} {z - 1} minecraft:redstone_torch")
r(f"setblock {X + 15} {Y} {z + 1} minecraft:polished_deepslate")
r(f"setblock {X + 16} {Y} {z + 1} minecraft:lever[face=wall,facing=east]")              # on a side wall
r(f"setblock {X + 18} {Y + 1} {z + 1} minecraft:polished_deepslate")
r(f"setblock {X + 18} {Y} {z + 1} minecraft:lever[face=ceiling,facing=north]")
r(f"setblock {X + 20} {Y} {z + 1} minecraft:stone_pressure_plate")

# ---- row 2: machines on soul signal
z = Z + 8
r(f"fill {X - 4} {Y - 1} {z - 1} {X + 22} {Y - 1} {z + 2} minecraft:sculk")
r(f"setblock {X} {Y} {z} pysift:spirit_engine[facing=north]{FUEL}")
r(f"fill {X + 1} {Y} {z} {X + 14} {Y} {z} pysift:soul_conduit")
r(f"setblock {X + 3} {Y} {z} pysift:soul_gauge[axis=x]")
r(f"setblock {X + 5} {Y} {z + 1} pysift:soul_grinder[facing=north]" + '{Slot0:{id:"minecraft:cobblestone",count:64}}')
r(f"setblock {X + 8} {Y} {z + 1} pysift:soul_drill[facing=south]")
r(f"fill {X + 8} {Y} {z + 2} {X + 8} {Y} {z + 2} minecraft:deepslate")
r(f"setblock {X + 11} {Y} {z - 1} pysift:soul_fan[facing=north]")
r(f"setblock {X + 11} {Y - 1} {z - 3} minecraft:soul_soil")
r(f"setblock {X + 11} {Y} {z - 3} minecraft:soul_fire")
r(f"setblock {X + 15} {Y} {z} pysift:soul_sifter[facing=north]" + '{Slot0:{id:"minecraft:sculk",count:16}}')

# ---- row 3: redstone control
z = Z + 12
r(f"setblock {X} {Y} {z} pysift:spirit_engine[facing=north]{FUEL}")
r(f"fill {X + 1} {Y} {z} {X + 3} {Y} {z} pysift:soul_conduit")
r(f"setblock {X + 4} {Y} {z} pysift:soul_grinder[facing=north]" + '{Slot0:{id:"minecraft:cobblestone",count:64}}')
r(f"setblock {X + 5} {Y} {z} minecraft:redstone_block")                           # pauses the grinder
r(f"setblock {X + 10} {Y} {z} pysift:spirit_engine[facing=north]{FUEL}")
r(f"fill {X + 11} {Y} {z} {X + 14} {Y} {z} pysift:soul_conduit")
r(f"setblock {X + 9} {Y} {z} minecraft:redstone_block")                           # switches the engine off

# ---- row 4: wireless
z = Z + 16
disc = '{Disc:{id:"minecraft:music_disc_pigstep",count:1}}'
r(f"setblock {X + 13} {Y} {z} pysift:spirit_engine[facing=north]{FUEL}")
r(f"setblock {X + 14} {Y} {z} pysift:charoite_beam_emitter[facing=east]")
r(f"setblock {X + 20} {Y} {z} pysift:charoite_prism[facing=south]")
r(f"setblock {X + 20} {Y} {z + 4} pysift:charoite_beam_receiver[facing=north]")
r(f"setblock {X + 20} {Y} {z + 5} pysift:soul_grinder[facing=north]" + '{Slot0:{id:"minecraft:gravel",count:64}}')
# a conduit line wrapped in full blocks: engine -> 6 covered conduits -> lamp
r(f"setblock {X + 32} {Y} {z} minecraft:redstone_lamp")
r(f"fill {X + 25} {Y} {z} {X + 31} {Y} {z} pysift:soul_conduit")
for i, cover in enumerate(("polished_deepslate", "stone_bricks", "oak_planks", "glass", "amethyst_block", "copper_block")):
    r(f'data merge block {X + 26 + i} {Y} {z} {{Cover:"minecraft:{cover}"}}')
r(f"setblock {X + 24} {Y} {z} pysift:spirit_engine[facing=north]{FUEL}")

# ---- row 5: sculk
z = Z + 22
r(f"setblock {X} {Y} {z} minecraft:sculk_catalyst")
r(f"fill {X + 1} {Y} {z} {X + 3} {Y} {z} pysift:soul_conduit")
r(f"setblock {X + 4} {Y} {z} pysift:soul_fan[facing=east]")
r(f"fill {X - 2} {Y} {z + 2} {X + 1} {Y} {z + 4} minecraft:glass")
r(f"fill {X - 1} {Y} {z + 3} {X} {Y} {z + 3} minecraft:air")
for _ in range(4):
    r(f"summon minecraft:pig {X - 0.5} {Y} {z + 3.5}")
r(f"setblock {X + 12} {Y} {z} pysift:spirit_engine[facing=north]{FUEL}")
r(f"fill {X + 12} {Y} {z + 1} {X + 12} {Y} {z + 5} pysift:soul_conduit")
r(f"setblock {X + 11} {Y} {z + 3} minecraft:sculk_shrieker")
r(f"fill {X + 13} {Y} {z + 1} {X + 13} {Y} {z + 5} pysift:soul_grinder[facing=north]")      # five grinders: overloaded

# ---- row 6: stage two - a Singer on the line, repeater, filters, the eight note blocks
z = Z + 28
r(f"fill {X - 2} {Y} {z - 2} {X + 3} {Y} {z + 2} minecraft:glass")                # a pen for the Singer
r(f"fill {X - 1} {Y} {z - 1} {X + 2} {Y} {z + 1} minecraft:air")
r(f"setblock {X - 1} {Y} {z + 1} pysift:soul_crystal_block")                      # keeps it from starving
r(f"fill {X + 3} {Y} {z} {X + 6} {Y} {z} pysift:soul_conduit")
r(f"setblock {X + 7} {Y} {z} pysift:soul_grinder[facing=north]" + '{Slot0:{id:"minecraft:cobblestone",count:64}}')
r(f"summon pysift:singer {X + 1} {Y} {z + 0.5} {{PersistenceRequired:1b}}")
# engine -> 12 conduits -> repeater -> conduits; a soul-only and a plain-only filter on two branches
r(f"fill {X + 12} {Y} {z} {X + 23} {Y} {z} pysift:soul_conduit")
r(f"setblock {X + 24} {Y} {z} pysift:soul_repeater[facing=east]")
r(f"fill {X + 25} {Y} {z} {X + 28} {Y} {z} pysift:soul_conduit")
r(f"setblock {X + 26} {Y} {z - 1} pysift:soul_filter[soul=true]")
r(f"setblock {X + 26} {Y} {z - 2} pysift:soul_conduit")
r(f"setblock {X + 28} {Y} {z - 1} pysift:soul_filter[soul=false]")
r(f"setblock {X + 28} {Y} {z - 2} pysift:soul_conduit")
r(f"setblock {X + 11} {Y} {z} pysift:spirit_engine[facing=north]{FUEL}")
# the eight notes along a wire with a lever: flick it to hear the chord, right-click a box to retune it
z = Z + 32
r(f"setblock {X + 11} {Y} {z} minecraft:lever[face=floor,powered=false]")
r(f"fill {X + 12} {Y} {z} {X + 27} {Y} {z} pysift:soul_conduit")
for i in range(8):
    r(f"setblock {X + 13 + i * 2} {Y} {z + 1} pysift:soul_note_block[note={i + 1}]")

# camera
r(f"gamemode creative {name}")
r(f"tp {name} {X + 14} {Y + 9} {Z - 8} 0 35")
print("built at", X, Y, Z)
