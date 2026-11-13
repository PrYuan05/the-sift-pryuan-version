"""Check soul redstone (soulpower/SoulCircuit) on the running test server (./gradlew.bat runSiftTestServer) over RCON.
Usage: python -I tools/progression/test_soul_redstone.py <project> [part]
    part: wire | vanilla | plain | control | overload | gauge | beam | cover | repeater | filter | note | singer | catalyst | sensor | pump | machines | addon | all

Run it with the mechanical add-on off (run-server/config/pysift.properties: kinetic_addon=auto or off, no Create):
the base system must work without any shaft or cogwheel. The add-on's own checks are tools/progression/test_soul_power.py
(kinetic_addon=on).

Builds in the Overworld at x 200.., y 120 (in the air, forceloaded), lets the circuit settle and reads block states and
block entity data back. Prints PASS / FAIL per check; exit 1 when something fails.

Signal strength: 15 at the engine, one level less every 2 blocks (cost 1 per block, strength = 15 - cost // 2);
a machine's speed is 32 x strength / 15, its load is its full load x strength / 15."""
import re, sys, time
from pathlib import Path

P = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(P / "tools/worldgen"))
import devserver as d  # noqa: E402

OW = "execute in minecraft:overworld run "
Y = 120
FUEL = '{Fuel:{id:"pysift:spirit_liquid_bucket",count:1}}'
fails = []


def r(cmd):
    out = d.rcon(OW + cmd)
    return out if isinstance(out, str) else " | ".join(map(str, out))


def num(x, y, z, path):
    out = r(f"data get block {x} {y} {z} {path}")
    m = re.search(r"has the following block data: (-?[0-9.]+)", out)
    return float(m.group(1)) if m else None


def check(name, got, want, tol=0.01):
    ok = got is not None and abs(got - want) <= tol * max(1, abs(want))
    print(("PASS" if ok else "FAIL"), f"{name}: {got} (want {want})")
    if not ok:
        fails.append(name)


def is_block(x, y, z, spec):
    return "passed" in r(f"execute if block {x} {y} {z} {spec}")


def expect(name, ok, detail=""):
    print(("PASS" if ok else "FAIL"), name + (f": {detail}" if detail else ""))
    if not ok:
        fails.append(name)


def conduit(name, x, y, z, power, charged):
    """The conduit's state: outward redstone power and whether a soul signal runs through it."""
    look = "off" if power == 0 else "soul" if charged else "plain"
    got = num(x, y, z, "Power")
    ok = got == power and is_block(x, y, z, f"pysift:soul_conduit[look={look}]")
    if not ok:
        name += f" (power is {got}, look {next((k for k in ('off', 'plain', 'soul') if is_block(x, y, z, f'pysift:soul_conduit[look={k}]')), None)})"
    expect(f"{name}: power {power}, {'soul' if charged else 'no soul'}", ok)


def speed_at(strength):
    return 32 * strength / 15


def clear():
    r("forceload add 190 190 230 260")
    r("kill @e[type=!minecraft:player,x=190,y=100,z=190,dx=40,dy=40,dz=70]")
    r(f"fill 190 {Y - 2} 190 230 {Y + 8} 260 minecraft:air")   # 41 x 11 x 71 < the 32768-block fill limit


def settle(seconds=1.5):
    time.sleep(seconds)


def wire():
    """Range, decay and vertical runs: 15 next to the engine, one level less every 2 blocks, ~30 blocks."""
    clear()
    r(f"setblock 200 {Y} 200 pysift:spirit_engine[facing=north]{FUEL}")
    r(f"fill 200 {Y} 201 200 {Y} 231 pysift:soul_conduit")
    r(f"fill 200 {Y + 1} 202 200 {Y + 3} 202 pysift:soul_conduit")     # straight up from the 2nd conduit
    settle()
    check("engine runs", num(200, Y, 200, "Speed"), 32)
    for dist, power in ((1, 15), (2, 14), (3, 14), (10, 10), (29, 1)):
        conduit(f"conduit {dist} from the engine", 200, Y, 200 + dist, power, True)
    conduit("conduit 30 from the engine (out of range)", 200, Y, 230, 0, False)
    conduit("vertical run, 2 up (cost 4)", 200, Y + 2, 202, 13, True)
    expect("conduit arms join their neighbours", is_block(200, Y, 205, "pysift:soul_conduit[north=wire,south=wire,up=none]"))
    expect("the T-junction grows an arm up", is_block(200, Y, 202, "pysift:soul_conduit[up=wire]"))
    r(f"setblock 200 {Y} 203 minecraft:air")                           # cut the wire
    settle()
    conduit("after the cut: the far side goes dark", 200, Y, 204, 0, False)
    conduit("after the cut: the near side stays", 200, Y, 202, 14, True)


def vanilla():
    """Soul -> vanilla: a conduit is a redstone source for lamps and dust."""
    clear()
    # consumers first: a block placed with /setblock does not look at its neighbours until one of them changes
    r(f"setblock 201 {Y} 204 minecraft:redstone_lamp")
    r(f"setblock 199 {Y - 1} 204 minecraft:stone")
    r(f"setblock 199 {Y} 204 minecraft:redstone_wire")
    r(f"setblock 200 {Y - 1} 207 minecraft:stone")
    r(f"setblock 200 {Y} 207 minecraft:repeater[facing=north]")        # reads the conduit behind it (to its north)
    r(f"fill 200 {Y} 201 200 {Y} 206 pysift:soul_conduit")
    r(f"setblock 200 {Y} 200 pysift:spirit_engine[facing=north]{FUEL}")
    settle()
    conduit("conduit 4 from the engine", 200, Y, 204, 13, True)
    expect("a lamp next to the conduit lights", is_block(201, Y, 204, "minecraft:redstone_lamp[lit=true]"))
    expect("redstone dust next to it takes the signal (13)", is_block(199, Y, 204, "minecraft:redstone_wire[power=13]"))
    expect("a repeater reads the conduit", is_block(200, Y, 207, "minecraft:repeater[powered=true]"))
    expect("the conduit plugs into the lamp", is_block(200, Y, 204, "pysift:soul_conduit[east=plug]"))
    expect("it bends down to the dust", is_block(200, Y, 204, "pysift:soul_conduit[west=low]"))
    expect("and to the repeater's input", is_block(200, Y, 206, "pysift:soul_conduit[south=low]"))


def plain():
    """Vanilla -> soul: a lever feeds the conduit like better redstone wire, but machines do not run on it; dust is
    not an input, and the wire never latches."""
    clear()
    r(f"setblock 210 {Y - 1} 200 minecraft:stone")
    r(f"setblock 210 {Y} 200 minecraft:lever[face=floor,powered=false]")
    r(f"fill 211 {Y} 200 216 {Y} 200 pysift:soul_conduit")
    r(f"setblock 217 {Y} 200 minecraft:redstone_lamp")
    r(f"setblock 214 {Y} 201 pysift:soul_grinder[facing=north]")
    r(f"setblock 212 {Y - 1} 199 minecraft:stone")
    r(f"setblock 212 {Y} 199 minecraft:redstone_wire")                 # dust that takes the signal back out
    r(f"setblock 210 {Y} 200 minecraft:lever[face=floor,powered=true]")
    settle()
    conduit("conduit next to the lever", 211, Y, 200, 15, False)
    conduit("3rd conduit (cost 2)", 213, Y, 200, 14, False)
    expect("the lamp at the far end lights", is_block(217, Y, 200, "minecraft:redstone_lamp[lit=true]"))
    check("a grinder on that wire does not run", num(214, Y, 201, "Speed"), 0)
    r(f"setblock 210 {Y} 200 minecraft:lever[face=floor,powered=false]")
    settle()
    conduit("lever off: the wire goes dark (no latch through the dust)", 211, Y, 200, 0, False)
    expect("the lamp goes out", is_block(217, Y, 200, "minecraft:redstone_lamp[lit=false]"))
    # dust alone is not an input
    r(f"setblock 220 {Y} 200 minecraft:redstone_block")
    r(f"setblock 221 {Y - 1} 200 minecraft:stone")
    r(f"setblock 221 {Y} 200 minecraft:redstone_wire")
    r(f"setblock 222 {Y} 200 pysift:soul_conduit")
    settle()
    expect("the dust is powered", is_block(221, Y, 200, "minecraft:redstone_wire[power=15]"))
    conduit("dust cannot feed a conduit", 222, Y, 200, 0, False)


def control():
    """A vanilla signal on a machine pauses it; on the engine it switches the engine off."""
    clear()
    r(f"setblock 200 {Y} 200 pysift:spirit_engine[facing=north]{FUEL}")
    r(f"fill 200 {Y} 201 200 {Y} 203 pysift:soul_conduit")
    r(f"setblock 200 {Y} 204 pysift:soul_grinder[facing=north]")
    settle()
    check("grinder runs (cost 4: strength 13)", num(200, Y, 204, "Speed"), speed_at(13))
    r(f"setblock 200 {Y} 205 minecraft:redstone_block")                # on the grinder only
    settle()
    check("redstone on the grinder pauses it", num(200, Y, 204, "Speed"), 0)
    conduit("the wire keeps its soul signal", 200, Y, 203, 14, True)
    check("a paused machine takes no load", num(200, Y, 200, "Load"), 0)
    r(f"setblock 200 {Y} 205 minecraft:air")
    settle()
    check("signal gone: the grinder runs again", num(200, Y, 204, "Speed"), speed_at(13))
    r(f"setblock 199 {Y} 200 minecraft:redstone_block")                # on the engine
    settle()
    check("redstone on the engine switches it off", num(200, Y, 200, "Speed"), 0)
    conduit("the wire goes dark", 200, Y, 201, 0, False)
    r(f"setblock 199 {Y} 200 minecraft:air")
    settle()
    conduit("signal gone: the engine is back", 200, Y, 201, 15, True)


def overload():
    """Load, overload (everything stops), the shrieker alarm, soul deprivation after 5 s, recovery."""
    clear()
    Z = 240
    r(f"setblock 200 {Y} {Z} pysift:spirit_engine[facing=north]{FUEL}")
    r(f"fill 200 {Y} {Z + 1} 200 {Y} {Z + 5} pysift:soul_conduit")
    r(f"fill 201 {Y} {Z + 1} 201 {Y} {Z + 4} pysift:soul_grinder[facing=north]")   # strengths 14 14 13 13
    settle()
    check("4 grinders: load 230 / 256", num(200, Y, Z, "Load"), 230 / 256, tol=0.01)
    check("first grinder (strength 14)", num(201, Y, Z + 1, "Speed"), speed_at(14))
    check("fourth grinder (strength 13)", num(201, Y, Z + 4, "Speed"), speed_at(13))
    r(f"setblock 199 {Y - 1} {Z + 3} minecraft:stone")
    r(f"setblock 199 {Y} {Z + 3} minecraft:sculk_shrieker")
    r(f"setblock 201 {Y} {Z + 5} pysift:soul_grinder[facing=north]")               # the fifth: 282 > 256
    r(f"setblock 202 {Y} {Z + 3} minecraft:glass")
    r(f"summon minecraft:armor_stand 202 {Y + 1} {Z + 3}")
    shrieked = False
    for _ in range(12):
        time.sleep(0.25)
        shrieked = shrieked or is_block(199, Y, Z + 3, "minecraft:sculk_shrieker[shrieking=true]")
    check("overload stops the grinders", num(201, Y, Z + 1, "Speed"), 0)
    check("load 282 / 256", num(200, Y, Z, "Load"), 282 / 256, tol=0.01)
    conduit("overloaded wire carries no soul signal", 200, Y, Z + 1, 0, False)
    expect("the shrieker on the wire shrieks", shrieked)
    time.sleep(6)
    out = r(f"data get entity @e[type=minecraft:armor_stand,x=202,y={Y + 1},z={Z + 3},distance=..2,limit=1] active_effects")
    expect("soul deprivation near the overload", "soul_deprivation" in out, out[:120])
    expect("the alarm summons no warden", "passed" not in r("execute if entity @e[type=minecraft:warden]"))
    r("kill @e[type=minecraft:armor_stand]")
    r(f"setblock 201 {Y} {Z + 5} minecraft:air")
    settle()
    check("4 grinders run again", num(201, Y, Z + 1, "Speed"), speed_at(14))


def gauge():
    """The soul gauge sits in the wire and reads the circuit's load."""
    clear()
    r(f"setblock 200 {Y} 200 pysift:spirit_engine[facing=north]{FUEL}")
    r(f"setblock 200 {Y} 201 pysift:soul_conduit")
    r(f"setblock 200 {Y} 202 pysift:soul_gauge[axis=z]")
    r(f"setblock 200 {Y} 203 pysift:soul_conduit")
    r(f"setblock 200 {Y} 204 pysift:soul_grinder[facing=north]")       # cost 4: strength 13, load 64 x 13 / 15 = 55
    settle()
    check("signal passes through the gauge", num(200, Y, 204, "Speed"), speed_at(13))
    check("gauge load 55 / 256", num(200, Y, 202, "Load"), 55 / 256, tol=0.02)


def beam():
    clear()
    Z = 215
    r(f"setblock 200 {Y} {Z} pysift:spirit_engine[facing=north]{FUEL}")
    r(f"setblock 201 {Y} {Z} pysift:charoite_beam_emitter[facing=east]")
    r(f"setblock 207 {Y} {Z} pysift:charoite_prism[facing=north]")            # turns the beam north
    r(f"setblock 207 {Y} {Z - 5} pysift:charoite_beam_receiver[facing=south]")
    r(f"setblock 207 {Y} {Z - 6} pysift:soul_grinder[facing=north]")
    settle(3)
    check("the beam loses nothing (strength 14)", num(207, Y, Z - 6, "Speed"), speed_at(14))
    r(f"setblock 205 {Y} {Z} minecraft:stone")
    settle(3)
    check("stone blocks the beam", num(207, Y, Z - 6, "Speed"), 0)
    r(f"setblock 205 {Y} {Z} minecraft:glass")
    settle(3)
    check("glass lets it through", num(207, Y, Z - 6, "Speed"), speed_at(14))


def cover():
    """A conduit wrapped in a full block: it still carries the signal, keeps the block in its data and is a full cube."""
    clear()
    r(f"setblock 201 {Y} 203 minecraft:redstone_lamp")
    r(f"fill 200 {Y} 201 200 {Y} 205 pysift:soul_conduit")
    r(f"setblock 200 {Y} 200 pysift:spirit_engine[facing=north]{FUEL}")
    r(f'data merge block 200 {Y} 203 {{Cover:"minecraft:polished_deepslate"}}')
    settle()
    out = r(f"data get block 200 {Y} 203 Cover")
    expect("the cover is kept in the conduit's data", "polished_deepslate" in out, out[:100])
    check("a covered conduit carries the signal (power 14)", num(200, Y, 203, "Power"), 14)
    expect("and gives off no light (look off)", is_block(200, Y, 203, "pysift:soul_conduit[look=off]"))
    conduit("and passes it on", 200, Y, 205, 13, True)
    expect("the lamp next to the covered conduit lights", is_block(201, Y, 203, "minecraft:redstone_lamp[lit=true]"))
    r(f"summon minecraft:armor_stand 200.5 {Y + 3} 203.5")
    time.sleep(2)
    out = r(f"data get entity @e[type=minecraft:armor_stand,limit=1,sort=nearest,x=200,y={Y},z=203] Pos[1]")
    m = re.search(r"(-?[0-9.]+)d", out)
    check("a mob stands on the cover (full cube)", float(m.group(1)) if m else None, Y + 1, tol=0.0002)
    r("kill @e[type=minecraft:armor_stand]")


def repeater():
    """A soul repeater brings the signal back to 15, costs 16 SP, and passes nothing backwards."""
    clear()
    r(f"fill 200 {Y} 201 200 {Y} 212 pysift:soul_conduit")
    r(f"setblock 200 {Y} 213 pysift:soul_repeater[facing=south]")
    r(f"fill 200 {Y} 214 200 {Y} 216 pysift:soul_conduit")
    r(f"setblock 200 {Y} 200 pysift:spirit_engine[facing=north]{FUEL}")
    settle()
    conduit("12 conduits out: strength 9", 200, Y, 212, 9, True)
    conduit("past the repeater: back to 15", 200, Y, 214, 15, True)
    expect("the repeater lights up", is_block(200, Y, 213, "pysift:soul_repeater[powered=true]"))
    check("it costs 16 SP", num(200, Y, 200, "Load"), 16 / 256, tol=0.02)
    r(f"setblock 200 {Y} 213 pysift:soul_repeater[facing=north]")      # turned round: nothing passes
    settle()
    conduit("a repeater turned the other way passes nothing", 200, Y, 214, 0, False)
    conduit("and the near side is untouched", 200, Y, 212, 9, True)


def filter_():
    """A soul filter passes one kind of signal: soul only, or plain redstone only."""
    clear()
    # soul signal against a filter
    r(f"fill 200 {Y} 201 200 {Y} 202 pysift:soul_conduit")
    r(f"setblock 200 {Y} 203 pysift:soul_filter[soul=false]")
    r(f"fill 200 {Y} 204 200 {Y} 205 pysift:soul_conduit")
    r(f"setblock 200 {Y} 200 pysift:spirit_engine[facing=north]{FUEL}")
    # plain signal against a filter
    r(f"setblock 210 {Y - 1} 200 minecraft:stone")
    r(f"setblock 210 {Y} 200 minecraft:lever[face=floor,powered=false]")
    r(f"fill 211 {Y} 200 212 {Y} 200 pysift:soul_conduit")
    r(f"setblock 213 {Y} 200 pysift:soul_filter[soul=true]")
    r(f"fill 214 {Y} 200 215 {Y} 200 pysift:soul_conduit")
    r(f"setblock 210 {Y} 200 minecraft:lever[face=floor,powered=true]")
    settle()
    conduit("plain-only filter stops the soul signal", 200, Y, 204, 0, False)
    conduit("soul-only filter stops the plain signal", 214, Y, 200, 0, False)
    r(f"setblock 200 {Y} 203 pysift:soul_filter[soul=true]")
    r(f"setblock 213 {Y} 200 pysift:soul_filter[soul=false]")
    settle()
    conduit("soul-only filter passes the soul signal", 200, Y, 204, 13, True)
    conduit("plain-only filter passes the plain signal", 214, Y, 200, 14, False)


def note():
    """A soul note block is triggered like a vanilla one: it is powered while the conduit next to it carries a signal."""
    clear()
    r(f"setblock 201 {Y} 202 pysift:soul_note_block[note=3]")
    r(f"fill 200 {Y} 201 200 {Y} 203 pysift:soul_conduit")
    settle(0.5)
    expect("the conduit plugs into the note block", is_block(200, Y, 202, "pysift:soul_conduit[east=plug]"))
    expect("silent without a signal", is_block(201, Y, 202, "pysift:soul_note_block[powered=false]"))
    r(f"setblock 200 {Y} 200 pysift:spirit_engine[facing=north]{FUEL}")
    settle()
    expect("triggered by the soul signal", is_block(201, Y, 202, "pysift:soul_note_block[note=3,powered=true]"))


def singer():
    """A Singer within 3 blocks of a conduit sings into it: strength 15, 64 SP, enough for one grinder."""
    clear()
    r(f"fill 197 {Y - 1} 197 204 {Y - 1} 204 minecraft:stone")
    r(f"fill 200 {Y} 200 200 {Y} 201 pysift:soul_conduit")
    r(f"setblock 200 {Y} 202 pysift:soul_grinder[facing=north]")
    r(f"summon pysift:singer 202.5 {Y} 200.5 {{NoAI:1b,PersistenceRequired:1b}}")
    sung = False
    for _ in range(20):
        time.sleep(0.5)
        if is_block(200, Y, 200, "pysift:soul_conduit[look=soul]"):
            sung = True
            break
    expect("the conduit next to a Singer carries a soul signal", sung)
    settle(1)
    check("the grinder runs on the song (strength 14)", num(200, Y, 202, "Speed"), speed_at(14))
    check("load 60 / 64", num(200, Y, 202, "Load"), 60 / 64, tol=0.02)
    r("kill @e[type=pysift:singer]")
    time.sleep(3)
    conduit("the Singer gone: the song stops", 200, Y, 200, 0, False)
    r("kill @e[type=minecraft:item]")


def catalyst():
    """A mob dying at a sculk catalyst: the conduit on the catalyst carries a soul signal for 10 s (32 SP: one fan)."""
    clear()
    Z = 250
    r(f"fill 198 {Y - 1} {Z - 2} 204 {Y - 1} {Z + 2} minecraft:stone")
    r(f"setblock 200 {Y} {Z} minecraft:sculk_catalyst")
    r(f"setblock 201 {Y} {Z} pysift:soul_conduit")
    r(f"setblock 202 {Y} {Z} pysift:soul_fan[facing=east]")                  # its back (west) takes the conduit
    settle()
    conduit("before: no signal", 201, Y, Z, 0, False)
    r(f"summon minecraft:pig 200 {Y} {Z + 2} {{NoAI:1b}}")
    time.sleep(0.5)
    r(f"kill @e[type=minecraft:pig,x=200,y={Y},z={Z + 2},distance=..3]")
    time.sleep(1.0)
    conduit("a death at the catalyst charges the conduit", 201, Y, Z, 15, True)
    check("the fan runs on it", num(202, Y, Z, "Speed"), 32)
    time.sleep(11)
    conduit("10 s later the soul is spent", 201, Y, Z, 0, False)
    check("the fan stops", num(202, Y, Z, "Speed"), 0)
    r("kill @e[type=minecraft:item]")
    r("kill @e[type=minecraft:experience_orb]")


def sensor():
    """A sculk sensor's output is a vanilla signal: it travels along the conduit, but runs no machine."""
    clear()
    Z = 256
    r(f"fill 208 {Y - 1} {Z - 2} 222 {Y - 1} {Z + 2} minecraft:stone")
    r(f"setblock 210 {Y} {Z} minecraft:sculk_sensor")
    r(f"fill 211 {Y} {Z} 216 {Y} {Z} pysift:soul_conduit")
    r(f"setblock 217 {Y} {Z} minecraft:redstone_lamp")
    r(f"setblock 214 {Y} {Z + 1} pysift:soul_grinder[facing=north]")
    settle(3)                                                             # the sensor's own placement cooldown
    lit = ran = False
    r(f"setblock 210 {Y + 2} {Z} minecraft:stone")
    r(f"setblock 210 {Y + 2} {Z} minecraft:air destroy")                  # breaking a block is a vibration
    for _ in range(16):
        time.sleep(0.15)
        lit = lit or is_block(217, Y, Z, "minecraft:redstone_lamp[lit=true]")
        ran = ran or (num(214, Y, Z + 1, "Speed") or 0) != 0
    expect("a sensor's signal lights the lamp at the end of the conduit", lit)
    expect("but the grinder on that conduit never runs", not ran)
    r("kill @e[type=minecraft:item]")


def pump():
    """The self-feeding loop: one engine drives the pump over a conduit, the pump pipes spirit liquid back to it.
    The conduit comes in at the pump's back and the pipe leaves from its side: every face but the intake takes both."""
    clear()
    Z = 235
    r(f"fill 194 {Y - 1} {Z - 3} 204 {Y - 1} {Z + 3} minecraft:smooth_stone")
    r(f"fill 194 {Y} {Z - 3} 199 {Y} {Z + 3} minecraft:smooth_stone")
    r(f"fill 195 {Y} {Z - 2} 199 {Y} {Z + 2} pysift:spirit_liquid")              # the pool
    r(f"setblock 200 {Y} {Z} pysift:spirit_pump[facing=west]")                    # intake in the pool
    r(f"setblock 201 {Y} {Z} pysift:soul_conduit")                                # signal into the pump's back
    r(f"fill 200 {Y} {Z - 1} 202 {Y} {Z - 1} pysift:spirit_pipe")                 # pipe from the pump's side to the engine
    r(f'setblock 202 {Y} {Z} pysift:spirit_engine[facing=east]{{Fuel:{{id:"minecraft:soul_sand",count:1}}}}')   # 10 s of fuel
    settle(2)
    check("pump turns on the conduit at its back (strength 14)", num(200, Y, Z, "Speed"), speed_at(14))
    expect("the pipe joins the pump's side and the engine",
           is_block(200, Y, Z - 1, "pysift:spirit_pipe[south=true,east=true]") and is_block(202, Y, Z - 1, "pysift:spirit_pipe[south=true,west=true]"))
    expect("no pipe arm on the intake side", not is_block(199, Y, Z, "pysift:spirit_pipe"))
    time.sleep(7)
    liquid = num(202, Y, Z, "Liquid") or 0
    expect("the engine takes in piped spirit liquid", liquid > 0, f"{liquid:.0f} mB")
    time.sleep(6)                                                                 # the soul sand is gone by now
    check("the engine now burns the piped liquid", num(202, Y, Z, "BurnMax"), 3200)
    check("and the pump keeps turning", num(200, Y, Z, "Speed"), speed_at(14))
    # the intake takes neither signal nor pipe
    r(f"setblock 201 {Y} {Z} minecraft:air")
    settle()
    check("without the conduit the pump stops", num(200, Y, Z, "Speed"), 0)
    r(f"setblock 201 {Y} {Z} pysift:soul_conduit")
    settle()


def machines():
    """Grinding and drilling on soul signal alone."""
    clear()
    r(f"setblock 200 {Y} 200 pysift:spirit_engine[facing=north]{FUEL}")
    r(f"fill 200 {Y} 201 200 {Y} 202 pysift:soul_conduit")
    r(f"setblock 200 {Y} 203 pysift:soul_grinder[facing=north]")
    r(f'data modify block 200 {Y} 203 Slot0 set value {{id:"minecraft:cobblestone",count:1}}')
    r(f"setblock 201 {Y} 202 pysift:soul_drill[facing=east]")               # its back (west) takes the conduit
    r(f"setblock 202 {Y} 202 minecraft:stone")
    settle(1)
    check("grinder runs (strength 14)", num(200, Y, 203, "Speed"), speed_at(14))
    check("drill runs (strength 14)", num(201, Y, 202, "Speed"), speed_at(14))
    time.sleep(9)
    expect("the drill bores the stone in front of it", is_block(202, Y, 202, "minecraft:air"))
    out = r(f"data get block 200 {Y} 203 Slot1")
    expect("the grinder grinds cobblestone to gravel", "minecraft:gravel" in out, out[:160])
    r("kill @e[type=minecraft:item]")


def addon():
    """With the add-on off the mechanical blocks do not exist, and nothing in the data fails to load."""
    out = r(f"setblock 228 {Y + 6} 258 pysift:soul_shaft")
    expect("soul_shaft is not registered", "nknown block" in out, out[:80])
    log = (P / "run-server/logs/latest.log").read_text(encoding="utf-8", errors="replace")
    bad = [line for line in log.splitlines() if "pysift" in line and
           re.search(r"Couldn't parse|Parsing error|Couldn't load tag|Unknown registry key|missing following references", line)]
    expect("no pysift data errors in the server log", not bad, "; ".join(b[:160] for b in bad[:3]))


parts = {"wire": wire, "vanilla": vanilla, "plain": plain, "control": control, "overload": overload, "gauge": gauge,
         "beam": beam, "cover": cover, "repeater": repeater, "filter": filter_, "note": note, "singer": singer, "catalyst": catalyst, "sensor": sensor, "pump": pump, "machines": machines, "addon": addon}
which = sys.argv[2] if len(sys.argv) > 2 else "all"
for name, f in parts.items():
    if which in ("all", name):
        print(f"--- {name}")
        f()
print("FAILED: " + ", ".join(fails) if fails else "ALL PASS")
sys.exit(1 if fails else 0)
