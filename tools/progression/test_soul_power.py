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
    r(f"forceload add 190 190 230 260")
    r(f"fill 190 {Y - 2} 190 230 {Y + 8} 260 minecraft:air")   # 41 x 11 x 71 < the 32768-block fill limit


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


def sifter():
    clear()
    r(f"fill 194 {Y - 1} 194 206 {Y - 1} 206 minecraft:sculk")       # rotten floor around the sifter
    r(f"setblock 200 {Y} 200 pysift:soul_sifter[facing=north]")
    r(f"setblock 201 {Y} 200 pysift:spirit_engine[facing=north]{FUEL}")   # on the crank side (east)
    r(f'data modify block 200 {Y} 200 Slot0 set value {{id:"minecraft:sculk",count:2}}')
    settle(1)
    check("sifter turns", abs(num(200, Y, 200, "Speed") or 0), 32)
    check("load 96/256", num(200, Y, 200, "Load"), 0.375)
    time.sleep(9)
    healed = r("data get block 200 %d 200 Slot1" % Y)
    print(("PASS" if "red_sculk" in healed else "FAIL"), "sifted sculk -> red sculk:", healed)
    if "red_sculk" not in healed:
        fails.append("sifting recipe")
    # count red sculk in the floor: clone the layer onto itself, keeping only red sculk
    cnt = r(f"clone 194 {Y - 1} 194 206 {Y - 1} 206 194 {Y - 1} 194 filtered pysift:red_sculk force")
    m = re.search(r"(\d+) block", cnt)
    ok = bool(m) and int(m.group(1)) >= 2
    print(("PASS" if ok else "FAIL"), "the floor around it is purified:", cnt)
    if not ok:
        fails.append("purify floor")


def beam():
    clear()
    Z = 215
    r(f"setblock 200 {Y} {Z} pysift:spirit_engine[facing=north]{FUEL}")
    r(f"setblock 201 {Y} {Z} pysift:charoite_beam_emitter[facing=east]")       # back (west) takes the engine
    r(f"setblock 207 {Y} {Z} pysift:charoite_prism[facing=north]")            # turns the beam north
    r(f"setblock 207 {Y} {Z - 5} pysift:charoite_beam_receiver[facing=south]")  # its front faces the beam
    r(f"setblock 207 {Y} {Z - 6} pysift:soul_grinder[facing=north]")
    r("kill @e[type=minecraft:pig]")
    r(f"summon minecraft:pig 204 {Y - 0.4} {Z} {{NoAI:1b,Health:10f}}")
    r(f"setblock 204 {Y - 1} {Z} minecraft:glass")
    settle(3)
    check("receiver turns through the prism", abs(num(207, Y, Z - 5, "Speed") or 0), 32)
    check("grinder behind the receiver", abs(num(207, Y, Z - 6, "Speed") or 0), 32)
    check("beam loses 5%", num(207, Y, Z - 6, "Load"), 64 / 243, tol=0.02)
    hp = r("data get entity @e[type=minecraft:pig,limit=1] Health")
    print(("PASS" if "10.0f" not in hp else "FAIL"), "the beam burns a pig in its way:", hp)
    if "10.0f" in hp:
        fails.append("beam damage")
    r(f"setblock 207 {Y} {Z} pysift:charoite_prism[facing=up]")               # turn the prism away
    settle(3)
    check("prism turned away: no link", num(207, Y, Z - 6, "Speed"), 0)
    r(f"setblock 207 {Y} {Z} pysift:charoite_prism[facing=north]")
    r(f"setblock 205 {Y} {Z} minecraft:stone")                                # block the beam
    settle(3)
    check("stone blocks the beam", num(207, Y, Z - 6, "Speed"), 0)
    r(f"setblock 205 {Y} {Z} minecraft:glass")                                # glass lets it through
    settle(3)
    check("glass lets it through", abs(num(207, Y, Z - 6, "Speed") or 0), 32)
    r("kill @e[type=minecraft:pig]")


def vein():
    clear()
    Z = 225
    r(f"fill 199 {Y - 2} {Z - 2} 212 {Y + 2} {Z + 2} minecraft:stone")       # solid rock
    r(f"setblock 199 {Y} {Z} pysift:spirit_engine[facing=north]{FUEL}")
    r(f"setblock 200 {Y} {Z} pysift:soul_vein_node")
    r(f"setblock 210 {Y} {Z} pysift:soul_vein_node")
    r(f"setblock 211 {Y} {Z} pysift:soul_grinder[facing=north]")
    settle(3)
    check("vein carries power through rock", abs(num(211, Y, Z, "Speed") or 0), 32)
    check("vein loses 15%", num(211, Y, Z, "Load"), 64 / 218, tol=0.02)
    time.sleep(6)
    cnt = r(f"clone 201 {Y} {Z} 209 {Y} {Z} 201 {Y} {Z} filtered pysift:soul_veined_stone force")
    print(("PASS" if re.search(r"[1-9]\d* block", cnt) else "FAIL"), "the vein grows into the rock:", cnt)
    if not re.search(r"[1-9]\d* block", cnt):
        fails.append("vein growth")
    r(f"setblock 205 {Y} {Z} minecraft:air")                                 # a cave cuts the vein
    settle(3)
    check("air breaks the vein", num(211, Y, Z, "Speed"), 0)


def pump():
    clear()
    Z = 235
    r(f"fill 195 {Y - 1} {Z - 2} 199 {Y - 1} {Z + 2} minecraft:glass")
    r(f"fill 195 {Y} {Z - 2} 199 {Y} {Z + 2} pysift:spirit_liquid")              # a pool in front of the pump
    r(f"setblock 200 {Y} {Z} pysift:spirit_pump[facing=west]")
    r(f"setblock 200 {Y} {Z - 1} pysift:spirit_engine[facing=north]{FUEL}")      # on the crank side
    r(f"setblock 201 {Y} {Z} pysift:spirit_pipe")
    r(f"setblock 202 {Y} {Z} pysift:spirit_pipe")
    r(f"setblock 203 {Y} {Z} pysift:spirit_engine[facing=north]")                 # no fuel: runs on piped liquid
    settle(2)
    check("pump turns", abs(num(200, Y, Z, "Speed") or 0), 32)
    time.sleep(8)
    liquid = num(203, Y, Z, "Liquid") or 0
    burn = num(203, Y, Z, "Burn") or 0
    ok = liquid > 0 or burn > 0
    print(("PASS" if ok else "FAIL"), f"the second engine gets piped spirit liquid (liquid {liquid}, burn {burn})")
    if not ok:
        fails.append("pump to engine")
    # a dead-end pipe over dirt leaks and pollutes it
    r(f"setblock 203 {Y} {Z} minecraft:air")
    r(f"setblock 203 {Y - 2} {Z} minecraft:dirt")
    time.sleep(6)
    soil = r(f"execute if block 203 {Y - 2} {Z} minecraft:soul_soil")
    print(("PASS" if "passed" in soil else "FAIL"), "a leaking pipe pollutes the dirt below:", soil)
    if "passed" not in soil:
        fails.append("leak pollution")


def shift():
    clear()
    Z = 245
    r(f"setblock 200 {Y} {Z} pysift:spirit_engine[facing=north]{FUEL}")
    r(f"setblock 201 {Y} {Z} pysift:soul_gearshift[axis=x]")
    r(f"setblock 202 {Y} {Z} pysift:soul_shaft[axis=x]")
    r(f"setblock 203 {Y} {Z} pysift:soul_clutch[axis=x]")
    r(f"setblock 204 {Y} {Z} pysift:soul_shaft[axis=x]")
    settle(2)
    check("through gearshift and clutch", num(204, Y, Z, "Speed"), 32)
    r(f"setblock 201 {Y + 1} {Z} minecraft:redstone_block")     # gearshift on: the far side turns the other way
    settle(2)
    check("gearshift reverses", num(202, Y, Z, "Speed"), -32)
    check("and everything after it", num(204, Y, Z, "Speed"), -32)
    r(f"setblock 203 {Y + 1} {Z} minecraft:redstone_block")     # clutch on: the far side stops
    settle(2)
    check("clutch disengages", num(204, Y, Z, "Speed"), 0)
    check("the near side still turns", num(202, Y, Z, "Speed"), -32)
    r(f"setblock 203 {Y + 1} {Z} minecraft:air")
    settle(2)
    check("clutch engages again", num(204, Y, Z, "Speed"), -32)


def fan():
    clear()
    Z = 255
    r(f"setblock 200 {Y} {Z} pysift:spirit_engine[facing=north]{FUEL}")
    r(f"setblock 201 {Y} {Z} pysift:soul_fan[facing=east]")             # back (west) takes the engine
    r(f"fill 202 {Y - 1} {Z} 210 {Y - 1} {Z} minecraft:glass")
    r(f"setblock 203 {Y - 1} {Z} minecraft:soul_soil")
    r(f"setblock 203 {Y} {Z} minecraft:soul_fire")
    r(f"setblock 208 {Y} {Z} minecraft:glass")                            # a wall: items rest in the stream against it
    settle(2)
    check("fan turns", abs(num(201, Y, Z, "Speed") or 0), 32)
    r(f'summon minecraft:item 205 {Y} {Z} {{Item:{{id:"minecraft:sand",count:4}},PickupDelay:32767}}')
    time.sleep(5)
    out = r(f"data get entity @e[type=minecraft:item,limit=1,sort=nearest,x=205,y={Y},z={Z}] Item")
    print(("PASS" if "soul_sand" in out else "FAIL"), "sand blown through soul fire becomes soul sand:", out)
    if "soul_sand" not in out:
        fails.append("haunting")
    pos = r(f"data get entity @e[type=minecraft:item,limit=1,sort=nearest,x=205,y={Y},z={Z}] Pos[0]")
    m = re.search(r"(-?[0-9.]+)d", pos)
    ok = m and float(m.group(1)) > 206.5
    print(("PASS" if ok else "FAIL"), "the stream pushes it away from the fan, against the wall:", pos)
    if not ok:
        fails.append("fan push")
    r("kill @e[type=minecraft:item]")


parts = {"shift": shift, "fan": fan, "pump": pump, "vein": vein, "beam": beam, "gears": gears, "conflict": conflict, "overload": overload, "wave": wave, "sifter": sifter}
which = sys.argv[2] if len(sys.argv) > 2 else "all"
for name, f in parts.items():
    if which in ("all", name):
        print(f"--- {name}")
        f()
print("FAILED: " + ", ".join(fails) if fails else "ALL PASS")
sys.exit(1 if fails else 0)
