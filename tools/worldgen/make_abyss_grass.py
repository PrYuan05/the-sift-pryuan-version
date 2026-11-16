"""Grayscale blade texture for abyss_grass, in the style of the user's ember_grass (same 4 grey levels, vertical
blades) but thinner, taller, with leaning wispy tips. Coloured in game by FloorTint (tintindex 0).
Usage: python -I tools/worldgen/make_abyss_grass.py <project> [seed]
       python -I tools/worldgen/make_abyss_grass.py <project> [seed] --tall-ember
--tall-ember draws the same kind of blades two blocks high (16x32) and splits them into tall_ember_grass_bottom.png /
tall_ember_grass_top.png, so the blades run on across the two blocks (also FloorTint-coloured, tinted_cross).
Existing PNGs are backed up to .texture_backups/<stamp>_grass_blades/ before they are replaced."""
import sys, random, shutil, datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import art_guard   # 臨時圖保護：使用者用同檔名覆蓋過的貼圖不會被重跑蓋掉
from PIL import Image

P = Path(sys.argv[1]).resolve()
ARGS = [a for a in sys.argv[2:] if not a.startswith("--")]
SEED = int(ARGS[0]) if ARGS else 7
TALL = "--tall-ember" in sys.argv
VEG = P / "src/main/resources/assets/pysift/textures/block/vegetation"
OUT = VEG / "abyss_grass.png"
W, H = 20, 21                                   # same size as ember_grass.png (the model's UVs expect it)
SHADES = [(192, 192, 192), (202, 202, 202), (226, 226, 226), (244, 244, 244)]   # dark -> light; light greys so the FloorTint colour stays pastel


def blades(w, h, rnd, min_height):
    """Grey vertical blades on a w x h canvas, growing up from the bottom row."""
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = img.load()
    x = 0.0
    blade = 0
    while x < w - 0.5:
        base = (0, 2, 1, 3)[blade % 4] if rnd.random() < 0.8 else rnd.randint(0, 3)   # neighbours alternate dark / light
        blade += 1
        height = rnd.randint(min_height, h)
        width = 2 if rnd.random() < 0.45 else 1
        lean = rnd.choice((-1, 0, 0, 1))
        bend_at = rnd.randint(height // 2, height - 2)
        for i in range(height):                       # i = 0 at the ground (bottom row)
            y = h - 1 - i
            off = lean * max(0, i - bend_at) // 2
            t = i / max(1, height - 1)
            shade = SHADES[min(3, base + (1 if t > 0.7 else 0))]          # one step lighter near the tip
            bw = 1 if i > height - 3 else width       # 1 px tips
            for dx in range(bw):
                cx = int(x) + off + dx
                if 0 <= cx < w:
                    px[cx, y] = shade + (255,)
        x += width + (1 if rnd.random() < 0.3 else 0)      # mostly touching, sometimes a 1 px gap
    return img


def save(img, path):
    if path.exists():
        bk = P / ".texture_backups" / f"{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}_grass_blades" / path.relative_to(P)
        bk.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, bk)
    path.parent.mkdir(parents=True, exist_ok=True)
    art_guard.save(img, path)
    print("wrote", path.relative_to(P))


def main():
    rnd = random.Random(SEED)
    if TALL:   # two blocks high: blades from 14 px up to the full 32 px, split at the block boundary
        img = blades(16, 32, rnd, 14)
        save(img.crop((0, 16, 16, 32)), VEG / "tall_ember_grass_bottom.png")
        save(img.crop((0, 0, 16, 16)), VEG / "tall_ember_grass_top.png")
        img.resize((16 * 12, 32 * 12), Image.Resampling.NEAREST).save(P / "build/vegwork/tall_ember_grass_tex_big.png")
        return
    img = blades(W, H, rnd, 9)
    save(img, OUT)
    img.resize((W * 12, H * 12), Image.Resampling.NEAREST).save(P / "build/vegwork/abyss_grass_tex_big.png")


if __name__ == "__main__":
    main()
