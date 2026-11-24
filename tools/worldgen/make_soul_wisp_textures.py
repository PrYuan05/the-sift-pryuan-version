"""Generate the upgraded Actions & Stuff-style Soul Wisp textures (minecraft-texture-crafter skill).
Usage: python -I tools/worldgen/make_soul_wisp_textures.py <project>

Material Brief (Step 0):
  1. Identity & Lore Role:
     - Escaping soul wisps rising from Spirit Liquid, Soul Crystal Blocks, and soul interactions.
  2. Physical & Surface Properties:
     - Self-luminous pure-white pixel-art ghost head with sharp transparent cutouts for the stepped crown,
       two 1x1 square eyes, and a centered 1x3 vertical wailing mouth, welded seamlessly into a smooth
       translucent cyan-to-deep-blue curved energy ribbon with crisp luminous side edges.
  3. Real-World / Stylistic Reference:
     - Actions & Stuff Bedrock add-on soul particle (10:50-11:19 reference): 5x8 logical pixel grid head
       (.###. crown, ##### forehead, #.#.# square cutout eyes, ##### bridge, ##.## x3 mouth, ##### chin)
       merged seamlessly at 100% width into a fluid glowing ribbon, accompanied by tiny crisp cyan pixel sparks.
  4. Vanilla Structural Anchors:
     - block/soul_fire_0.png & particle/soul_0.png: luminous soul-white (#F6FFFF) to electric cyan (#5CEBFF)
       to deep soul blue (#0D6FB8) emissive ramp (no #000000).

Outputs:
  - textures/entity/soul_wisp_ribbon.png  (32x64 POT: top 20x32 = 5x8 head @ 4x4/unit; bottom 20x32 = ribbon cross-section)
  - textures/particle/soul_wisp.png       (16x16 POT: matching crisp 5x8 ghost face fallback)
  - textures/particle/soul_trail.png      (8x8 POT: crisp glowing square cyan-white pixel spark ember)
  - build/previews/soul_wisp_preview.png  (enlarged visual audit preview on dark Ancient City backdrop)
"""
import datetime, shutil, sys
from pathlib import Path
from PIL import Image

P = Path(sys.argv[1]).resolve()
A = P / "src/main/resources/assets/pysift"
PARTICLE_DIR = A / "textures/particle"
ENTITY_DIR = A / "textures/entity"
PARTICLE_DIR.mkdir(parents=True, exist_ok=True)
ENTITY_DIR.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(P / "tools"))
import art_guard

# Exact 5x8 logical pixel grid verified from reference screenshots (10:50-11:19):
#   '.' = fully transparent cutout (crown notches, 1x1 square eyes, 1x3 vertical mouth)
#   'W' = luminous soul-white body (vertex-tinted cleanly in SoulWispRenderer)
HEAD_5X8 = [
    ".WWW.",  # Row 0: stepped crown (3 wide, aligned directly above eyes & nose bridge)
    "WWWWW",  # Row 1: forehead (5 wide)
    "W.W.W",  # Row 2: two crisp 1x1 square transparent eye cutouts, 1 unit apart
    "WWWWW",  # Row 3: solid bridge between eyes and mouth
    "WW.WW",  # Row 4: wailing mouth top (1 wide, centered)
    "WW.WW",  # Row 5: wailing mouth mid
    "WW.WW",  # Row 6: wailing mouth bottom (1x3 vertical cutout)
    "WWWWW",  # Row 7: chin (welds seamlessly at 100% width into the ribbon!)
]

# Backup existing particle/entity soul wisp textures before overwriting
bk = P / ".texture_backups" / (datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + "_soul_wisp_upgrade")
for old_f in (PARTICLE_DIR / "soul_wisp.png", PARTICLE_DIR / "soul_trail.png",
              PARTICLE_DIR / "soul_trail_band.png", ENTITY_DIR / "soul_wisp_ribbon.png"):
    if old_f.exists():
        dest = bk / old_f.relative_to(P)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(old_f, dest)

# ------------------------------------------------------------------
# 1. textures/entity/soul_wisp_ribbon.png (32 x 64 power-of-two)
#    Active UV region: u in [0, 20/32 = 0.625], v in [0, 1]
#    - Top half    (y = 0..31,  v = 0.0..0.5): 5x8 head at 4x4 texels per logical pixel
#    - Bottom half (y = 32..63, v = 0.5..1.0): continuous ribbon cross-section
#      (white RGB so per-vertex color controls the exact white -> cyan -> deep-blue gradient;
#       outer 2 texels slightly higher alpha/brightness for crisp glowing ribbon edges,
#       smooth translucent interior so dark backgrounds show softly through the mid-tail!)
# ------------------------------------------------------------------
UNIT = 4
ACTIVE_W = 5 * UNIT   # 20 texels
ribbon_sheet = Image.new("RGBA", (32, 64), (0, 0, 0, 0))

# Draw 5x8 head into y = 0..31, x = 0..19
for row_i, row in enumerate(HEAD_5X8):
    for col_i, ch in enumerate(row):
        if ch == "W":
            # Crisp near-pure white (F7FFFF, no #FFFFFF per skill rule, full alpha 255)
            # Subtle 1-texel inner tint on outer vertical rim? Keep pure luminous white like reference!
            col = (247, 254, 255, 255)
            for dy in range(UNIT):
                for dx in range(UNIT):
                    ribbon_sheet.putpixel((col_i * UNIT + dx, row_i * UNIT + dy), col)

# Draw continuous ribbon cross-section into y = 32..63, x = 0..19
# Seamless weld at y=32 (matches chin rgb & alpha=255), gently transitioning over 16 texels
# into bright-rimmed translucent ribbon (edge=255, center=226)
for y in range(32, 64):
    t_neck = min(1.0, (y - 32) / 16.0)
    for x in range(ACTIVE_W):
        d_edge = min(x, ACTIVE_W - 1 - x)
        if d_edge <= 1:
            edge_alpha = 255
            rgb = (247, 254, 255)
        elif d_edge == 2:
            edge_alpha = int(round(255 - 14 * t_neck))
            rgb = (242, 253, 255)
        else:
            edge_alpha = int(round(255 - 30 * t_neck))
            rgb = (234, 252, 255)
        ribbon_sheet.putpixel((x, y), (*rgb, edge_alpha))

art_guard.save(ribbon_sheet, ENTITY_DIR / "soul_wisp_ribbon.png")

# ------------------------------------------------------------------
# 2. textures/particle/soul_wisp.png (16 x 16 power-of-two fallback)
#    Centered 10x16 crisp pixel-art version of the same 5x8 ghost face (2x2 per unit)
# ------------------------------------------------------------------
head_16 = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
for row_i, row in enumerate(HEAD_5X8):
    for col_i, ch in enumerate(row):
        if ch == "W":
            for dy in range(2):
                for dx in range(2):
                    head_16.putpixel((3 + col_i * 2 + dx, row_i * 2 + dy), (242, 253, 255, 255))
art_guard.save(head_16, PARTICLE_DIR / "soul_wisp.png")

# ------------------------------------------------------------------
# 3. textures/particle/soul_trail.png (8 x 8 power-of-two)
#    Crisp glowing square pixel spark ember (matching the tiny square cyan dots in reference video)
# ------------------------------------------------------------------
spark = Image.new("RGBA", (8, 8), (0, 0, 0, 0))
for y in range(8):
    for x in range(8):
        if 2 <= x <= 5 and 2 <= y <= 5:
            spark.putpixel((x, y), (245, 254, 255, 255))     # crisp 4x4 glowing square core
        elif 1 <= x <= 6 and 1 <= y <= 6:
            # Soft 1 px outer glow fringe (corners even softer)
            corner = (x in (1, 6)) and (y in (1, 6))
            spark.putpixel((x, y), (140, 245, 255, 42 if corner else 92))
art_guard.save(spark, PARTICLE_DIR / "soul_trail.png")

# ------------------------------------------------------------------
# 4. Preview sheet on dark Ancient City backdrop for visual verification
# ------------------------------------------------------------------
preview = Image.new("RGBA", (420, 320), (10, 16, 22, 255))
# Render simulated ribbon: head (20x32) + long gradient tail (20x120) scaled 2x
sim = Image.new("RGBA", (20, 152), (0, 0, 0, 0))
# Copy head
sim.paste(ribbon_sheet.crop((0, 0, 20, 32)), (0, 0))
# Sample ribbon with vertex color gradient matching SoulWispRenderer.java
def sample_grad(t):
    stops = [
        (0.00, (0.96, 1.00, 1.00, 0.98)),
        (0.16, (0.55, 0.96, 1.00, 0.90)),
        (0.45, (0.14, 0.78, 0.95, 0.58)),
        (0.80, (0.06, 0.48, 0.74, 0.20)),
        (1.00, (0.03, 0.30, 0.54, 0.00)),
    ]
    for i in range(len(stops) - 1):
        t0, c0 = stops[i]
        t1, c1 = stops[i + 1]
        if t <= t1:
            k = (t - t0) / (t1 - t0)
            return tuple(c0[j] + (c1[j] - c0[j]) * k for j in range(4))
    return stops[-1][1]

for dy in range(120):
    t = dy / 119.0
    gr, gg, gb, ga = sample_grad(t)
    sy = 32 + min(31, dy)
    for x in range(20):
        tr, tg, tb, ta = ribbon_sheet.getpixel((x, sy))
        sim.putpixel((x, 32 + dy), (int(tr * gr), int(tg * gg), int(tb * gb), int(ta * ga)))

preview.alpha_composite(sim.resize((40, 304), Image.NEAREST), (40, 8))
preview.alpha_composite(ribbon_sheet.crop((0, 0, 20, 32)).resize((100, 160), Image.NEAREST), (120, 20))
preview.alpha_composite(head_16.resize((96, 96), Image.NEAREST), (260, 20))
preview.alpha_composite(spark.resize((64, 64), Image.NEAREST), (276, 150))

(P / "build/previews").mkdir(parents=True, exist_ok=True)
preview.convert("RGB").save(P / "build/previews/soul_wisp_preview.png")
print("wrote soul_wisp_ribbon.png, soul_wisp.png, soul_trail.png and build/previews/soul_wisp_preview.png")
