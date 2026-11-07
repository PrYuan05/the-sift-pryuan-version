"""Check the soul power network on the running test server (./gradlew.bat runSiftTestServer) over RCON.
Usage: python -I tools/progression/test_soul_power.py <project> [part]   part: gears | conflict | overload | wave | all

Builds machines in the Overworld at x 200.., y 120 (in the air, forceloaded), lets the network settle and reads every
block entity's synced Speed / Load back. Prints PASS / FAIL per check; exit 1 when something fails."""
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


def clear():
    r(f"forceload add 190 190 230 230")
    r(f"fill 190 {Y - 2} 190 230 {Y + 8} 230 minecraft:air")


def settle(seconds=2.0):
    time.sleep(seconds)


def gears():
    clear()
    r(f"setblock 200 {Y} 200 pysift:spirit_engine[facing=north]{FUEL}")
    r(f"setblock 201 {Y} 200 pysift:soul_shaft[axis=x]")
    r(f"setblock 202 {Y} 200 pysift:soul_cogwheel[axis=x]")
    r(f"setblock 202 {Y + 1} 200 pysift:soul_cogwheel[axis=x]")          # meshes with the cog below: reversed
    r(f"setblock 202 {Y + 2} 201 pysift:large_soul_cogwheel[axis=x]")    # diagonal to it: half speed
    r(f"setblock 202 {Y + 3} 202 pysift:soul_cogwheel[axis=x]")          # diagonal to the large one: twice that
    r(f"setblock 203 {Y} 200 pysift:soul_gauge[axis=x]")
    r(f"setblock 204 {Y} 200 pysift:soul_grinder[facing=north]")
    settle()
    check("engine speed", num(200, Y, 200, "Speed"), 32)
    check("shaft speed", num(201, Y, 200, "Speed"), 32)
    check("cog speed", num(202, Y, 200, "Speed"), 32)
    check("meshed cog reversed", num(202, Y + 1, 200, "Speed"), -32)
    check("large cog half", num(202, Y + 2, 201, "Speed"), 16)
    check("small after large, reversed x2", num(202, Y + 3, 202, "Speed"), -32)
    check("gauge speed", num(203, Y, 200, "Speed"), 32)
    check("grinder speed", num(204, Y, 200, "Speed"), 32)
    check("gauge load 64/256", num(203, Y, 200, "Load"), 0.25)
    print("  gauge says:", r(f"data get block 203 {Y} 200"))


def conflict():
    gears()
    # a second engine on the reversed cog's axis: it wants +32 where the network turns at -32
    r(f"setblock 203 {Y + 1} 200 pysift:soul_shaft[axis=x]")
    r(f"setblock 204 {Y + 1} 200 pysift:spirit_engine[facing=north]{FUEL}")
    settle()
    check("conflict stops the shaft", num(201, Y, 200, "Speed"), 0)
    out = r(f"data get block 203 {Y} 200 Conflict")
    print(("PASS" if "1b" in out else "FAIL"), "conflict flag:", out)
    if "1b" not in out:
        fails.append("conflict flag")


def overload():
    gears()
    for x in range(205, 209):   # 5 grinders x 64 SP = 320 > 256
        r(f"setblock {x} {Y} 200 pysift:soul_grinder[facing=north]")
    settle()
    check("overload stops the shaft", num(201, Y, 200, "Speed"), 0)
    check("gauge load 320/256", num(203, Y, 200, "Load"), 1.25)
    r(f"summon minecraft:armor_stand 206 {Y + 1} 201")
    r(f"setblock 206 {Y} 201 minecraft:glass")
    time.sleep(6)
    out = r(f"data get entity @e[type=minecraft:armor_stand,x=206,y={Y + 1},z=201,distance=..2,limit=1] active_effects")
    print(("PASS" if "soul_deprivation" in out else "FAIL"), "soul deprivation near the overload:", out[:160])
    if "soul_deprivation" not in out:
        fails.append("soul deprivation")
    r("kill @e[type=minecraft:armor_stand]")
    # breaking a grinder relieves it
    r(f"setblock 208 {Y} 200 minecraft:air")
    settle()
    check("4 grinders run again", num(201, Y, 200, "Speed"), 32)


def wave():
    clear()
    disc = '{Disc:{id:"minecraft:music_disc_pigstep",count:1}}'
    r(f"setblock 200 {Y} 210 pysift:spirit_engine[facing=north]{FUEL}")
    r(f"setblock 201 {Y} 210 pysift:soul_wave_emitter[facing=east]{disc}")   # back (west) takes the engine
    r(f"setblock 210 {Y} 210 pysift:soul_wave_receiver[facing=west]{disc}")
    r(f"setblock 211 {Y} 210 pysift:soul_grinder[facing=north]")
    settle(3)
    check("receiver turns", abs(num(210, Y, 210, "Speed") or 0), 32)
    check("grinder behind the receiver", abs(num(211, Y, 210, "Speed") or 0), 32)
    r(f"fill 205 {Y - 1} 209 205 {Y + 1} 211 minecraft:white_wool")
    settle(3)
    check("wool cuts the wave", num(211, Y, 210, "Speed"), 0)


parts = {"gears": gears, "conflict": conflict, "overload": overload, "wave": wave}
which = sys.argv[2] if len(sys.argv) > 2 else "all"
for name, f in parts.items():
    if which in ("all", name):
        print(f"--- {name}")
        f()
print("FAILED: " + ", ".join(fails) if fails else "ALL PASS")
sys.exit(1 if fails else 0)
