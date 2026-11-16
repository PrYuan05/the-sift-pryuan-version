"""Soul crystal block: outer-deep to inner-light soul glare palette + 5-tile 4-quadrant CTM + 16-frame breathing/wisp animation.
Usage: python -I tools/worldgen/paint_soul_crystal.py <project> [--apply]

Material Brief (Step 0 of minecraft-texture-crafter):
  1. Identity & Lore Role:
     - Condensed soul crystal carried on the Echo Golem's head and formed when spirit liquid meets water (Lullaby Hills).
     - Emits strong soul light (light level 12) and releases soul_wisp particles when broken or exposed.
  2. Physical & Surface Properties:
     - Self-luminous energy core encased in a dense, bevelled teal crystal shell (80/20 rule: deep translucent cyan-teal
       outer frame and glass + high-luminance soul-fire cyan/white glowing core).
     - Strict "outer-deep -> inner-light" value gradient across the entire connected structure: both the inner soul glow
       and the outer crystal sheen connect seamlessly across adjacent blocks into a single unified crystal mass.
  3. Real-World Analogues:
     - Phantom Quartz (clear crystal shell grown around an inner crystal phantom) + Uranium/Fluorescent Glass under UV
       (deep absorption along thick outer edges, intense glowing core inside).
  4. Vanilla Structural Anchors:
     - block/soul_campfire_fire.png & block/soul_lantern.png: deep teal-slate outer framing (#0A2638..#158C94) contrasting
       against the saturated soul-fire ramp (#085E78 -> #0E8296 -> #1FAEB8 -> #3EC0C6 -> #62E0E2 -> #92F4EC -> #DCFFF4).
     - block/glass.png: diagonal specular sheen and animated glint that connect seamlessly across multi-block faces.

Files generated in textures/block/soul_crystal_block/:
  soul_crystal_block_shell_0..4.png (+ .mcmeta)  16 x 256 (16 frames, frametime 3): 4-quadrant CTM shell tiles
  soul_crystal_block_core_0..4.png  (+ .mcmeta)  16 x 256 (16 frames, frametime 3): 4-quadrant CTM core tiles
"""
import datetime, json, math, shutil, sys
from pathlib import Path
from PIL import Image

P = Path(sys.argv[1]).resolve()
APPLY = "--apply" in sys.argv
A = P / "src/main/resources/assets/pysift"
DIR = A / "textures/block/soul_crystal_block"
OLD_TEX = A / "textures/block/soul_crystal_block.png"
MODEL_DIR = A / "models/block/soul_crystal_block"
MODEL = MODEL_DIR / "soul_crystal_block.json"
BLOCKSTATE = A / "blockstates/soul_crystal_block.json"
GOLEM = A / "textures/entity/echo_golem.png"
GEO = A / "geckolib/models/entity/echo_golem.geo.json"
SHELL_UV, CORE_UV = (111, 48), (0, 64)
sys.path.insert(0, str(P / "tools"))
import art_guard

# --- Palette: Outer-Deep -> Inner-Light (No #000000, No #FFFFFF, Hue-shifted) ---
# Shell colours (deep navy-teal bevel frame -> translucent cyan glass + soul-white specular)
S0_D = (0x0A, 0x26, 0x38)   # H=203 S=73% V=22% - deepest outer shadow edge
S0_L = (0x0D, 0x38, 0x4E)   # H=200 S=83% V=31% - top-left lit outer edge
S1_D = (0x0E, 0x4C, 0x60)   # H=195 S=85% V=38% - inner bevel shadow
S1_L = (0x12, 0x62, 0x76)   # H=192 S=85% V=46% - inner bevel lit
S2   = (0x10, 0x76, 0x82)   # H=186 S=88% V=51% - frame-to-glass cushion
S3   = (0x15, 0x8C, 0x94)   # H=184 S=86% V=58% - tinted crystal glass body
S4   = (0x2B, 0xAE, 0xB4)   # H=183 S=76% V=71% - connected diagonal crystal refraction sheen

# Core colours (7-step two-tier block palette: cold-shifted shadows ~194 deg -> base 184 deg -> warm-shifted highlights ~161 deg)
C0  = (0x08, 0x5E, 0x78)    # H=194 S=89% V=47% - exposed core rim (deep cold ocean teal)
C1  = (0x0E, 0x82, 0x96)    # H=189 S=91% V=59% - outer core step
C2  = (0x1F, 0xAE, 0xB8)    # H=184 S=83% V=72% - mid-core base (soul fire anchor)
C2B = (0x3E, 0xC0, 0xC6)    # H=183 S=69% V=78% - micro-texture bridge (dV=6%, desaturated bridge)
C3  = (0x62, 0xE0, 0xE2)    # H=181 S=57% V=89% - inner bright cyan
C4  = (0x92, 0xF4, 0xEC)    # H=175 S=40% V=96% - soul aura highlight (warm-shifted +9 deg)
C5  = (0xDC, 0xFF, 0xF4)    # H=161 S=14% V=100% - blazing soul-white core (warm-shifted +23 deg, not #FFFFFF)

CORE_RAMP = (C0, C1, C2, C2B, C3, C4, C5)
FRAMES = 16
MCMETA = {"animation": {"frametime": 3, "interpolate": True}}


def _quad_conn(tile):
    """For tile index 0..4, return (H_connected, V_connected, D_connected)."""
    return ((False, False, False),
            (True,  False, False),
            (False, True,  False),
            (True,  True,  False),
            (True,  True,  True))[tile]


def _shell_edge_dist(x, y, H, V, D):
    """Distance in pixels from the nearest unconnected outer boundary on the shell (0, 1, 2 = frame, >=3 = interior glass)."""
    u = x if x < 8 else 15 - x
    v = y if y < 8 else 15 - y
    d_h = 99 if H else u
    d_v = 99 if V else v
    d = min(d_h, d_v)
    if H and V and not D:
        d = min(d, u + v)
    return d


def shell_frame_base(tile):
    """16x16 RGBA base frame for shell tile 0..4.
    Both the bevelled frame AND the diagonal specular glare rays connect seamlessly across adjacent blocks:
    a torus-continuous diagonal ray ((x + y) % 16 in (6, 7)) runs straight across connected boundaries and terminates
    cleanly at the outer bevel frame (d_edge <= 2)."""
    H, V, D = _quad_conn(tile)
    px = {}
    for y in range(16):
        for x in range(16):
            u = x if x < 8 else 15 - x
            v = y if y < 8 else 15 - y
            lit_x = x < 8
            lit_y = y < 8
            s0 = S0_L if (lit_x and lit_y) else S0_D if (not lit_x and not lit_y) else (S0_L if (x + y < 15) else S0_D)
            s1 = S1_L if (lit_x and lit_y) else S1_D if (not lit_x and not lit_y) else (S1_L if (x + y < 15) else S1_D)

            d_edge = _shell_edge_dist(x, y, H, V, D)
            if d_edge == 0:
                px[(x, y)] = (s0, 244)
            elif d_edge == 1:
                if not H and not V and u == 1 and v == 1:
                    px[(x, y)] = (s0, 234)
                else:
                    px[(x, y)] = (s1, 214)
            elif d_edge == 2:
                if not H and not V and u <= 2 and v <= 2 and (u + v <= 3):
                    px[(x, y)] = (s1, 185)
                else:
                    px[(x, y)] = (S2, 146)
            else:
                # Torus-continuous diagonal glare rays: (x + y) % 16 == 7 (main ray) and 6 (soft edge)
                # Because (15 + y) % 16 == (0 + y - 1) % 16, this ray connects seamlessly across every connected block edge!
                diag = (x + y) % 16
                if diag == 7:
                    px[(x, y)] = (C4, 132)
                elif diag == 6:
                    px[(x, y)] = (C3, 98)
                elif diag == 14 and ((x + y) >= 14):
                    px[(x, y)] = (S4, 84)
                else:
                    px[(x, y)] = (S3, 64)
    return px


def shell_animate(base_px, f, tile):
    """16-frame torus-connected diagonal soul-glint sweep + corner 4-point star flare on outer corners."""
    out = dict(base_px)
    H, V, D = _quad_conn(tile)
    breath = int(round(8 * math.sin(2 * math.pi * f / FRAMES)))
    for (x, y), (c, a) in out.items():
        if a < 140:
            out[(x, y)] = (c, max(50, min(145, a + breath)))

    # Torus-continuous diagonal glint sweep across the entire connected crystal (sweeps 2 modulo-16 cycles over 16 frames)
    # Because it uses (x + y) % 16 and extends all the way to x=0/15 and y=0/15 on connected sides,
    # the moving light beam flows seamlessly from block to block across the whole connected wall!
    if f >= 6:
        d = ((f - 6) * 2) % 16
        for (x, y), (c, a) in list(out.items()):
            d_edge = _shell_edge_dist(x, y, H, V, D)
            if d_edge <= 1:
                continue
            s = (x + y) % 16
            dist_diag = min((s - d) % 16, (d - s) % 16)
            if dist_diag == 0:
                out[(x, y)] = (C5, max(a, 215 if d_edge >= 3 else 185))
            elif dist_diag == 1:
                out[(x, y)] = (C4, max(a, 160))

    # Frames 10..12: 4-point soul star flare (✦) on true outer top-left corners (Tile 0)
    if tile == 0 and f in (10, 11, 12):
        peak = (f == 11)
        for cx, cy in (((4, 4), (11, 11)) if peak else ((4, 4),)):
            out[(cx, cy)] = (C5, 248 if peak else 210)
            for ox, oy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                q = (cx + ox, cy + oy)
                if 2 <= q[0] <= 13 and 2 <= q[1] <= 13:
                    out[q] = (C5 if peak else C4, 215 if peak else 170)
            if peak:
                for ox, oy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
                    q = (cx + ox, cy + oy)
                    if 2 <= q[0] <= 13 and 2 <= q[1] <= 13:
                        out[q] = (C3, max(out[q][1], 145))
    return out


def core_frame(tile, f):
    """16x16 RGBA core texture for tile 0..4 at animation frame f (0..15).
    Key property — CONNECTED GLOW:
      The brightness index (0..6 -> C0..C5) is strictly a function of the distance d_outer from the nearest
      UNCONNECTED boundary of the multi-block shape:
        - When H is True, d_H = 7 (no horizontal drop-off at all — the glow beam runs straight across the block seam!).
        - When V is True, d_V = 7 (no vertical drop-off at all — the glow beam runs straight across the block seam!).
        - When H, V, D are all True (Tile 4), the entire quadrant is deep inside the connected crystal (C4/C5),
          with torus-seamless rising soul-flame waves so a 1x3, L-shape, 2x2, or 3x3 has ONE unified glowing core!
    """
    H, V, D = _quad_conn(tile)
    breath = 0.35 * math.sin(2 * math.pi * f / FRAMES)

    grid = {}
    for y in range(16):
        for x in range(16):
            u = x if x < 8 else 15 - x       # 0 at block outer edge, 7 at block centre
            v = y if y < 8 else 15 - y

            # Distance from the nearest unconnected boundary (in pixels, 0..7)
            d_h = 7.0 if H else float(u)
            d_v = 7.0 if V else float(v)

            if not H and not V:
                # Tile 0 (outer corner): rounded crystal corner from rim (1 -> C0) to inner core (7 -> C5)
                m = min(d_h, d_v)
                M = max(d_h, d_v)
                d_outer = m - (0.35 if (m <= 5 and M <= 5 and m == d_h and m == d_v) else 0.0)
            elif H and V and not D:
                # Tile 3 (inner concave corner): concentric rings radiating from the missing diagonal (u=0, v=0)
                d_outer = min(7.0, math.hypot(u, v) * 0.95)
            else:
                # Tile 1 (H=True, V=False -> d_outer = v), Tile 2 (H=False, V=True -> d_outer = u), Tile 4 (-> 7.0)
                d_outer = min(d_h, d_v)

            # Map d_outer (0..7) strictly to ramp index (0..6):
            #   d <= 1 -> 0 (C0)
            #   d == 2 -> 1 (C1)
            #   d == 3 -> 2 (C2)
            #   d == 4 -> 3 (C2B)
            #   d == 5 -> 4 (C3)
            #   d == 6 -> 5 (C4)
            #   d >= 7 -> 6 (C5, blazing soul-white core!)
            base = max(0.0, d_outer - 1.0)

            # Torus-seamless rising soul wave (gentle +/- 0.45 ripple that only modulates the innermost C4/C5 core
            # and is completely locked to 0 on the outer C0..C3 rings so the connected beam never pinches!)
            wave = (0.32 * math.sin(2 * math.pi * (x / 16.0) + 2 * math.pi * ((y + f) / 16.0)) +
                    0.22 * math.cos(2 * math.pi * (x / 8.0) - 2 * math.pi * ((y + f) / 16.0)))

            if base >= 4.8:
                val = base + wave + breath
            else:
                val = base + 0.15 * wave

            idx = max(0, min(len(CORE_RAMP) - 1, int(round(val))))
            grid[(x, y)] = idx

    # Clean any single-pixel orphans while preserving the exact connected bands
    for _ in range(2):
        nxt = dict(grid)
        for y in range(16):
            for x in range(16):
                v = grid[(x, y)]
                ns = [grid[((x + dx) % 16, (y + dy) % 16)] for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1))]
                if v not in ns:
                    nxt[(x, y)] = min(ns, key=lambda n: abs(n - v))
        grid = nxt

    im = Image.new("RGBA", (16, 16))
    im.putdata([(*CORE_RAMP[grid[(x, y)]], 255) for y in range(16) for x in range(16)])
    return im


def render_shell_frame(px):
    im = Image.new("RGBA", (16, 16))
    im.putdata([(*px[(x, y)][0], px[(x, y)][1]) for y in range(16) for x in range(16)])
    return im


def make_strip(frames):
    strip = Image.new("RGBA", (16, 16 * len(frames)))
    for i, fr in enumerate(frames):
        strip.paste(fr, (0, 16 * i))
    return strip


def compose_quadrant_face(tiles, L, R, U, D, UL, UR, DL, DR):
    """Compose a 16x16 face from 5 CTM tiles (0..4) using the exact same 4-quadrant rules as SoulCrystalModel.java."""
    out = Image.new("RGBA", (16, 16))
    quads = (
        (0, 0, L, U, UL),   # TL
        (8, 0, R, U, UR),   # TR
        (0, 8, L, D, DL),   # BL
        (8, 8, R, D, DR),   # BR
    )
    for x0, y0, h, v, d in quads:
        t = 0 if (not h and not v) else 1 if (h and not v) else 2 if (not h and v) else 3 if not d else 4
        crop = tiles[t].crop((x0, y0, x0 + 8, y0 + 8))
        out.paste(crop, (x0, y0))
    return out


def connected_preview(shell_tiles, core_tiles):
    """Render a multi-shape connected preview (Single, 1x3 bar, 2x2 square, L-shape, 3x3 wall, T/plus shape)."""
    cells = {
        # Single crystal
        (0, 0),
        # 1x3 horizontal bar
        (2, 0), (3, 0), (4, 0),
        # 2x2 square (the exact case from the user's screenshot!)
        (6, 0), (7, 0),
        (6, 1), (7, 1),
        # L-shape (tests inner concave corner at (1, 4))
        (0, 3), (0, 4), (0, 5), (1, 5), (2, 5),
        # 3x3 solid wall (tests full interior Tile 4 at (5, 4))
        (4, 3), (5, 3), (6, 3),
        (4, 4), (5, 4), (6, 4),
        (4, 5), (5, 5), (6, 5),
        # 2x2 with an extra arm (tests mixed inner & outer corners)
        (8, 3), (9, 3), (10, 3),
        (8, 4), (9, 4),
    }
    W, H = 11 * 16 + 16, 6 * 16 + 16
    im = Image.new("RGBA", (W, H), (22, 34, 28, 255))
    for yy in range(0, H, 8):
        for xx in range(0, W, 8):
            if (xx // 8 + yy // 8) % 2:
                im.paste((18, 28, 23, 255), (xx, yy, xx + 8, yy + 8))

    for c, r in sorted(cells):
        L, R, U, D = (c - 1, r) in cells, (c + 1, r) in cells, (c, r - 1) in cells, (c, r + 1) in cells
        UL, UR, DL, DR = (c - 1, r - 1) in cells, (c + 1, r - 1) in cells, (c - 1, r + 1) in cells, (c + 1, r + 1) in cells
        x0, y0 = (c + 1) * 16 - 8, (r + 1) * 16 - 8

        core_face = compose_quadrant_face(core_tiles, L, R, U, D, UL, UR, DL, DR)
        shell_face = compose_quadrant_face(shell_tiles, L, R, U, D, UL, UR, DL, DR)

        # Sub-cube occupancy on the 2D face (inset I = 1 px)
        for y in range(16):
            sy = -1 if y < 1 else (1 if y >= 15 else 0)
            for x in range(16):
                sx = -1 if x < 1 else (1 if x >= 15 else 0)
                ok_x = True if sx == 0 else (L if sx == -1 else R)
                ok_y = True if sy == 0 else (U if sy == -1 else D)
                ok_d = True if (sx == 0 or sy == 0) else (
                    UL if (sx == -1 and sy == -1) else
                    UR if (sx == 1 and sy == -1) else
                    DL if (sx == -1 and sy == 1) else DR
                )
                if ok_x and ok_y and ok_d:
                    im.putpixel((x0 + x, y0 + y), core_face.getpixel((x, y)))

        im.alpha_composite(shell_face, (x0, y0))

    return im.resize((W * 5, H * 5), Image.NEAREST).convert("RGB")


def static_block_model():
    """Static block model used for the item, particles, and to register all 10 CTM sprites into the block atlas."""
    base = "pysift:block/soul_crystal_block/"
    tex = {"particle": base + "soul_crystal_block_core_0"}
    for i in range(5):
        tex[f"shell_{i}"] = {"sprite": base + f"soul_crystal_block_shell_{i}", "force_translucent": True}
        tex[f"core_{i}"] = base + f"soul_crystal_block_core_{i}"
    faces = ("down", "up", "north", "south", "west", "east")
    return {
        "parent": "minecraft:block/block",
        "textures": tex,
        "elements": [
            {
                "from": [1, 1, 1],
                "to": [15, 15, 15],
                "shade": False,
                "light_emission": 15,
                "faces": {d: {"uv": [1, 1, 15, 15], "texture": "#core_0"} for d in faces},
            },
            {
                "from": [0, 0, 0],
                "to": [16, 16, 16],
                "shade": False,
                "light_emission": 15,
                "faces": {d: {"uv": [0, 0, 16, 16], "texture": "#shell_0", "cullface": d} for d in faces},
            },
        ],
    }


def golem_geo(doc):
    """Echo golem crystal bone: 12^3 inner core first (drawn before the 16^3 translucent shell)."""
    d = doc["minecraft:geometry"][0]
    bone = next(b for b in d["bones"] if b["name"] == "crystal")
    shell_cube = next(c for c in bone["cubes"] if c.get("size") == [16, 16, 16])
    uv = {f: {"uv": list(CORE_UV), "uv_size": [12, 12]} for f in ("north", "east", "south", "west", "up", "down")}
    bone["cubes"] = [{"origin": [-6, 28, -6], "size": [12, 12, 12], "uv": uv}, shell_cube]
    return doc


def main():
    shell_strips, core_strips = [], []
    shell_f0, core_f0 = [], []
    shell_f11, core_f2 = [], []
    for t in range(5):
        sb = shell_frame_base(t)
        s_frames = [render_shell_frame(shell_animate(sb, f, t)) for f in range(FRAMES)]
        c_frames = [core_frame(t, f) for f in range(FRAMES)]
        shell_strips.append(make_strip(s_frames))
        core_strips.append(make_strip(c_frames))
        shell_f0.append(s_frames[0])
        core_f0.append(c_frames[0])
        shell_f11.append(s_frames[11])
        core_f2.append(c_frames[2])

    S = 112
    sheet = Image.new("RGBA", (5 * (S + 6) + 6, 3 * (S + 6) + 6), (12, 16, 22, 255))
    checker = Image.new("RGBA", (S, S), (28, 44, 34, 255))
    for yy in range(0, S, 14):
        for xx in range(0, S, 14):
            if (xx // 14 + yy // 14) % 2:
                checker.paste((22, 36, 28, 255), (xx, yy, xx + 14, yy + 14))

    for t in range(5):
        x = 6 + t * (S + 6)
        sheet.paste(checker, (x, 6))
        sh_im = shell_f11[0] if t == 0 else shell_f0[t]
        sheet.alpha_composite(sh_im.resize((S, S), Image.NEAREST), (x, 6))
        sheet.paste(core_f0[t].resize((S, S), Image.NEAREST), (x, 12 + S))
        comp = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
        comp.alpha_composite(core_f2[t])
        comp.alpha_composite(sh_im)
        sheet.paste(checker, (x, 18 + 2 * S))
        sheet.alpha_composite(comp.resize((S, S), Image.NEAREST), (x, 18 + 2 * S))

    (P / "build/previews").mkdir(parents=True, exist_ok=True)
    sheet.convert("RGB").save(P / "build/previews/soul_crystal_paint.png")
    connected_preview(shell_f0, core_f2).save(P / "build/previews/soul_crystal_connected.png")

    tmp = P / "build/previews/soul_crystal_paint"
    tmp.mkdir(parents=True, exist_ok=True)
    for t in range(5):
        core_f0[t].save(tmp / f"core_{t}.png")
        shell_f0[t].save(tmp / f"shell_{t}.png")
    print("preview written: build/previews/soul_crystal_paint.png & build/previews/soul_crystal_connected.png")

    if not APPLY:
        return

    bk = P / ".texture_backups" / (datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + "_soul_crystal_ctm")
    for f in [OLD_TEX, GOLEM, GEO, BLOCKSTATE, *DIR.glob("*"), *MODEL_DIR.glob("*.json")]:
        if f.exists() and f.is_file():
            dest = bk / f.relative_to(P)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, dest)

    for old_f in (OLD_TEX, OLD_TEX.with_name(OLD_TEX.name + ".mcmeta"),
                  DIR / "soul_crystal_block_outer.png", DIR / "soul_crystal_block_outer.png.mcmeta",
                  DIR / "soul_crystal_block_inner.png", DIR / "soul_crystal_block_frame.png"):
        if old_f.exists():
            old_f.unlink()
    for mf in MODEL_DIR.glob("*.json"):
        if mf.name != "soul_crystal_block.json":
            mf.unlink()

    DIR.mkdir(parents=True, exist_ok=True)
    for t in range(5):
        sp = DIR / f"soul_crystal_block_shell_{t}.png"
        cp = DIR / f"soul_crystal_block_core_{t}.png"
        art_guard.save(shell_strips[t], sp)
        art_guard.save(core_strips[t], cp)
        sp.with_name(sp.name + ".mcmeta").write_text(json.dumps(MCMETA, indent=2) + "\n", encoding="utf-8")
        cp.with_name(cp.name + ".mcmeta").write_text(json.dumps(MCMETA, indent=2) + "\n", encoding="utf-8")

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    MODEL.write_text(json.dumps(static_block_model(), indent=2) + "\n", encoding="utf-8")
    BLOCKSTATE.write_text(json.dumps({
        "variants": {"": {"model": "pysift:block/soul_crystal_block/soul_crystal_block"}}
    }, indent=2) + "\n", encoding="utf-8")

    g = Image.open(GOLEM).convert("RGBA")
    g.paste(shell_f0[0], SHELL_UV)
    core_12 = core_f0[0].crop((2, 2, 14, 14))
    g.paste(core_12, CORE_UV)
    g.save(GOLEM)
    GEO.write_text(json.dumps(golem_geo(json.loads(GEO.read_text(encoding="utf-8"))), indent=2) + "\n", encoding="utf-8")
    print("applied soul crystal textures, models, and golem head; backups in", bk.relative_to(P))


if __name__ == "__main__":
    main()
