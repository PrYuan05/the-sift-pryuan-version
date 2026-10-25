"""The Sift 各生態域的背景音樂與環境音 → assets/pysift/sounds.json（只改 music.the_sift.* / ambient.the_sift.* 這些鍵）。
Usage: python -I tools/worldgen/build_sift_audio.py <project>

生態域 JSON 引用的是模組自己的音效 ID（ModSounds.java 註冊；build_the_sift.py 的 AUDIO 寫進生態域 attributes），
這裡先讓它們指向原版的音樂與環境音當暫用。之後有可以合法使用的音檔（自己作的曲子、授權音樂）：
把 .ogg 放進 assets/pysift/sounds/music/ 或 sounds/ambient/，再把下面 MUSIC / AMBIENT 對應的項目改成
"pysift:music/<檔名>"（音樂記得 stream）即可，Java 和生態域都不用改。
原版的檔名與事件從 Loom 快取的 26.3 資產索引檢查，打錯字會直接報錯。
"""
import json, os, sys
from pathlib import Path

P = Path(sys.argv[1]).resolve()
SOUNDS = P / "src/main/resources/assets/pysift/sounds.json"
BIOMES = ["willow_grove", "crimson_strata_canyon", "violet_slate_abyss", "amber_dunes", "red_zone_caves", "lullaby_hills"]

# 背景音樂（原版曲目暫用）：柳絮林地柔和、峽谷乾燥遼闊、深淵幽暗、沙丘溫暖、紅區洞穴低沉
MUSIC = {
    "willow_grove": ["below_and_above", "bromeliad", "echo_in_the_wind", "featherfall", "left_to_bloom", "comforting_memories"],
    "crimson_strata_canyon": ["crescent_dunes", "echo_in_the_wind", "dry_hands", "nether/crimson_forest/chrysopoeia"],
    "violet_slate_abyss": ["ancestry", "deeper", "nether/soulsand_valley/so_below", "nether/concrete_halls"],
    "amber_dunes": ["crescent_dunes", "fireflies", "haggstrom", "danny"],
    "red_zone_caves": ["deeper", "an_ordinary_day", "ebb", "nether/crimson_forest/chrysopoeia"],
    "lullaby_hills": ["echo_in_the_wind", "left_to_bloom", "featherfall", "comforting_memories"],   # gentle: the echo golems' lullaby
}
# 環境音：loop（持續的底噪）、mood（偶爾一聲低鳴）、additions（零星的小聲音）。值 = [(原版事件, 音量, 音高)]
# 遠處的「歌聲」用悅靈的哼唱和紫水晶的叮噹聲代替（The Sift 是歌者的家）
AMBIENT = {
    "willow_grove": {
        "loop": [("ambient.warped_forest.loop", 0.55, 1.1)],
        "mood": [("ambient.soul_sand_valley.mood", 0.6, 1.2)],
        "additions": [("entity.allay.ambient_without_item", 0.35, 0.8), ("block.amethyst_block.chime", 0.6, 0.7),
                      ("ambient.warped_forest.additions", 0.6, 1.0)],
    },
    "crimson_strata_canyon": {
        "loop": [("ambient.crimson_forest.loop", 0.6, 1.0)],
        "mood": [("ambient.crimson_forest.mood", 0.7, 1.0)],
        "additions": [("ambient.crimson_forest.additions", 0.7, 1.0), ("block.amethyst_block.chime", 0.5, 0.6)],
    },
    "violet_slate_abyss": {
        "loop": [("ambient.soul_sand_valley.loop", 0.7, 0.9)],
        "mood": [("ambient.soul_sand_valley.mood", 0.8, 0.9)],
        "additions": [("ambient.soul_sand_valley.additions", 0.7, 1.0), ("block.amethyst_block.resonate", 0.4, 0.6),
                      ("entity.allay.ambient_without_item", 0.25, 0.6)],
    },
    "amber_dunes": {
        "loop": [("ambient.nether_wastes.loop", 0.35, 1.3)],
        "mood": [("ambient.basalt_deltas.mood", 0.5, 1.2)],
        "additions": [("block.amethyst_block.chime", 0.5, 0.9), ("ambient.basalt_deltas.additions", 0.3, 1.4)],
    },
    "lullaby_hills": {   # wind through the canyon, distant humming and chimes (the echo golems singing)
        "loop": [("ambient.crimson_forest.loop", 0.45, 1.15)],
        "mood": [("ambient.soul_sand_valley.mood", 0.5, 1.3)],
        "additions": [("block.amethyst_block.chime", 0.6, 0.8), ("entity.allay.ambient_without_item", 0.3, 0.7),
                      ("block.amethyst_block.resonate", 0.35, 0.9)],
    },
    "red_zone_caves": {
        "loop": [("ambient.crimson_forest.loop", 0.5, 0.8)],
        "mood": [("ambient.cave", 0.8, 0.9)],
        "additions": [("ambient.crimson_forest.additions", 0.6, 0.8), ("block.amethyst_block.resonate", 0.4, 0.5)],
    },
}


def vanilla():
    """26.3 的原版 sounds.json 與資產索引（Loom 快取）。"""
    root = Path(os.path.expanduser("~/.gradle/caches/fabric-loom/assets"))
    idx = json.loads(sorted((root / "indexes").glob("26.3*.json"))[-1].read_text())["objects"]
    h = idx["minecraft/sounds.json"]["hash"]
    return json.loads((root / "objects" / h[:2] / h).read_text(encoding="utf-8")), idx


def main():
    events, idx = vanilla()
    out = json.loads(SOUNDS.read_text(encoding="utf-8")) if SOUNDS.exists() else {}
    for k in [k for k in out if k.startswith(("music.the_sift.", "ambient.the_sift."))]:
        del out[k]
    for b in BIOMES:
        tracks = []
        for t in MUSIC[b]:
            assert f"minecraft/sounds/music/game/{t}.ogg" in idx, f"no vanilla track {t}"
            tracks.append({"name": f"minecraft:music/game/{t}", "stream": True})
        out[f"music.the_sift.{b}"] = {"category": "music", "sounds": tracks}
        for part, entries in AMBIENT[b].items():
            sounds = []
            for ev, vol, pitch in entries:
                assert ev in events, f"no vanilla sound event {ev}"
                sounds.append({"name": f"minecraft:{ev}", "type": "event", "volume": vol, "pitch": pitch})
            out[f"ambient.the_sift.{b}.{part}"] = {"category": "ambient", "sounds": sounds}
    SOUNDS.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(BIOMES) * 4} sound events to {SOUNDS.relative_to(P)}")


if __name__ == "__main__":
    main()
