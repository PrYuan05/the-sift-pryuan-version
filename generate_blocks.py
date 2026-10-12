import zipfile
import csv
import io
import json
import os
import shutil

zip_path = "sift_atlas_sorted.zip"
res_dir = "src/main/resources/assets/pysift"
data_dir = "src/main/resources/data/pysift"
mc_data_dir = "src/main/resources/data/minecraft"
java_dir = "src/main/java/pryuan05/pysift/block"

# --- 步驟 1：徹底清除舊方塊與舊資源 ---
print("清理舊方塊與資產...")

# 清空/重建 blockstates、models/block
for d in [f"{res_dir}/blockstates", f"{res_dir}/models/block"]:
    if os.path.exists(d):
        shutil.rmtree(d)
    os.makedirs(d, exist_ok=True)

# 確保目錄存在
os.makedirs(f"{res_dir}/textures/block", exist_ok=True)
os.makedirs(f"{res_dir}/models/item", exist_ok=True)
os.makedirs(f"{res_dir}/items", exist_ok=True)
os.makedirs(f"{res_dir}/lang", exist_ok=True)
os.makedirs(f"{data_dir}/loot_tables/blocks", exist_ok=True)
os.makedirs(f"{data_dir}/loot_table/blocks", exist_ok=True)
os.makedirs(f"{data_dir}/recipe", exist_ok=True)
os.makedirs(f"{data_dir}/recipes", exist_ok=True)
os.makedirs(f"{mc_data_dir}/tags/block/mineable", exist_ok=True)
os.makedirs(java_dir, exist_ok=True)

# 清理舊的 block 貼圖（保留目錄，清空舊貼圖以容納新 343 張）
for f in os.listdir(f"{res_dir}/textures/block"):
    os.remove(os.path.join(f"{res_dir}/textures/block", f))

# 清理舊的 loot tables 與 recipes
for lt_dir in [f"{data_dir}/loot_tables/blocks", f"{data_dir}/loot_table/blocks"]:
    for f in os.listdir(lt_dir):
        os.remove(os.path.join(lt_dir, f))

for rec_dir in [f"{data_dir}/recipe", f"{data_dir}/recipes"]:
    for f in os.listdir(rec_dir):
        os.remove(os.path.join(rec_dir, f))

# --- 步驟 2：讀取 sift_atlas_sorted.zip 並提取貼圖與 CSV ---
with zipfile.ZipFile(zip_path, 'r') as z:
    content = z.read('sift_atlas_sorted/blocks.csv').decode('utf-8-sig')
    rows = list(csv.DictReader(io.StringIO(content)))

    # 1. 搬移所有貼圖至 assets/pysift/textures/block/
    copied_tex = 0
    for f in z.namelist():
        if f.endswith('.png') and ('the_sift/' in f or 'vanilla_expansion/' in f):
            with open(f"{res_dir}/textures/block/{os.path.basename(f)}", "wb") as out_f:
                out_f.write(z.read(f))
            copied_tex += 1
    print(f"已解壓 {copied_tex} 張方塊貼圖至 {res_dir}/textures/block/")

# 讀取現有語系檔保留實體與物品翻譯
en_path = f"{res_dir}/lang/en_us.json"
zh_path = f"{res_dir}/lang/zh_tw.json"
lang_en = json.load(open(en_path, encoding='utf-8')) if os.path.exists(en_path) else {}
lang_zh = json.load(open(zh_path, encoding='utf-8')) if os.path.exists(zh_path) else {}

# 清除舊方塊的翻譯鍵
lang_en = {k: v for k, v in lang_en.items() if not k.startswith("block.pysift.") and not k.startswith("item.pysift.") or k.startswith("item.pysift.charoite") or k.startswith("item.pysift.siftite_ingot") or "_spawn_egg" in k}
lang_zh = {k: v for k, v in lang_zh.items() if not k.startswith("block.pysift.") and not k.startswith("item.pysift.") or k.startswith("item.pysift.charoite") or k.startswith("item.pysift.siftite_ingot") or "_spawn_egg" in k}

java_registrations = []
pickaxe_blocks = []
axe_blocks = []
shovel_blocks = []

for r in rows:
    raw_id = r['預擬命名 ID']
    block_name = raw_id.split(':')[1]  # 例如 amber_capped_stone_01, amber_log
    name_cn = r['中文方塊名稱']
    name_en = ' '.join(p.capitalize() for p in block_name.split('_'))

    lang_en[f"block.pysift.{block_name}"] = name_en
    lang_zh[f"block.pysift.{block_name}"] = name_cn
    lang_en[f"item.pysift.{block_name}"] = name_en
    lang_zh[f"item.pysift.{block_name}"] = name_cn

    files = [f.strip() for f in r['輸出檔名'].replace('<br>', '\n').replace('/', '\n').split('\n') if f.strip()]
    bases = [os.path.splitext(f)[0] for f in files]

    has_side = any(f.endswith('_side') for f in bases)
    has_top = any(f.endswith('_top') for f in bases)
    has_bottom = any(f.endswith('_bottom') for f in bases)

    side_tex = next((f for f in bases if f.endswith('_side')), bases[0])
    top_tex = next((f for f in bases if f.endswith('_top')), bases[0])
    bottom_tex = next((f for f in bases if f.endswith('_bottom')), bases[0])

    is_pillar = has_side and has_top and not has_bottom
    is_bottom_top = has_side and has_top and has_bottom

    # 設定材質特質、硬度與音效 (Mojang Mappings: SoundType)
    if 'log' in block_name or 'wood' in block_name or 'planks' in block_name:
        sound = "SoundType.WOOD"
        destroy_time = 2.0
        resistance = 3.0
        axe_blocks.append(f"pysift:{block_name}")
    elif 'grass' in block_name or 'foliage' in block_name:
        sound = "SoundType.GRASS"
        destroy_time = 0.6
        resistance = 0.6
        shovel_blocks.append(f"pysift:{block_name}")
    elif 'sand' in block_name:
        sound = "SoundType.SAND"
        destroy_time = 0.5
        resistance = 0.5
        shovel_blocks.append(f"pysift:{block_name}")
    elif 'dirt' in block_name or 'earth' in block_name or 'floor' in block_name:
        sound = "SoundType.GRAVEL"
        destroy_time = 0.5
        resistance = 0.5
        shovel_blocks.append(f"pysift:{block_name}")
    elif 'slate' in block_name:
        sound = "SoundType.DEEPSLATE"
        destroy_time = 3.0
        resistance = 6.0
        pickaxe_blocks.append(f"pysift:{block_name}")
    else:
        sound = "SoundType.STONE"
        destroy_time = 1.5
        resistance = 6.0
        pickaxe_blocks.append(f"pysift:{block_name}")

    field_name = block_name.upper()

    # 原木/柱狀特質 (RotatedPillarBlock)
    if is_pillar:
        java_registrations.append(f'    public static final Block {field_name} = registerPillar("{block_name}", BlockBehaviour.Properties.of().destroyTime({destroy_time}f).explosionResistance({resistance}f).sound({sound}));')
        bs = {
            "variants": {
                "axis=y": {"model": f"pysift:block/{block_name}"},
                "axis=z": {"model": f"pysift:block/{block_name}_horizontal", "x": 90},
                "axis=x": {"model": f"pysift:block/{block_name}_horizontal", "x": 90, "y": 90}
            }
        }
        m_y = {"parent": "minecraft:block/cube_column", "textures": {"end": f"pysift:block/{top_tex}", "side": f"pysift:block/{side_tex}"}}
        m_h = {"parent": "minecraft:block/cube_column_horizontal", "textures": {"end": f"pysift:block/{top_tex}", "side": f"pysift:block/{side_tex}"}}
        with open(f"{res_dir}/models/block/{block_name}_horizontal.json", "w", encoding="utf-8") as f_mh:
            json.dump(m_h, f_mh, indent=2)

    # 草地/覆蓋特質 (cube_bottom_top)
    elif is_bottom_top:
        java_registrations.append(f'    public static final Block {field_name} = register("{block_name}", BlockBehaviour.Properties.of().destroyTime({destroy_time}f).explosionResistance({resistance}f).sound({sound}));')
        bs = {"variants": {"": {"model": f"pysift:block/{block_name}"}}}
        m_y = {"parent": "minecraft:block/cube_bottom_top", "textures": {"top": f"pysift:block/{top_tex}", "bottom": f"pysift:block/{bottom_tex}", "side": f"pysift:block/{side_tex}"}}

    # 一般六面同材質 (cube_all)
    else:
        java_registrations.append(f'    public static final Block {field_name} = register("{block_name}", BlockBehaviour.Properties.of().destroyTime({destroy_time}f).explosionResistance({resistance}f).sound({sound}));')
        bs = {"variants": {"": {"model": f"pysift:block/{block_name}"}}}
        m_y = {"parent": "minecraft:block/cube_all", "textures": {"all": f"pysift:block/{bases[0]}"}}

    with open(f"{res_dir}/blockstates/{block_name}.json", "w", encoding="utf-8") as f_bs:
        json.dump(bs, f_bs, indent=2)
    with open(f"{res_dir}/models/block/{block_name}.json", "w", encoding="utf-8") as f_mb:
        json.dump(m_y, f_mb, indent=2)
    with open(f"{res_dir}/models/item/{block_name}.json", "w", encoding="utf-8") as f_mi:
        json.dump({"parent": f"pysift:block/{block_name}"}, f_mi, indent=2)

    # Minecraft 1.21.4 必備 items/<block_name>.json (避免物品欄紫黑破圖)
    item_def = {
        "model": {
            "type": "minecraft:model",
            "model": f"pysift:item/{block_name}"
        }
    }
    with open(f"{res_dir}/items/{block_name}.json", "w", encoding="utf-8") as f_item:
        json.dump(item_def, f_item, indent=2)

    # 掉落表
    lt = {"type": "minecraft:block", "pools": [{"rolls": 1.0, "bonus_rolls": 0.0, "entries": [{"type": "minecraft:item", "name": f"pysift:{block_name}"}], "conditions": [{"condition": "minecraft:survives_explosion"}]}]}
    with open(f"{data_dir}/loot_tables/blocks/{block_name}.json", "w", encoding="utf-8") as f_lt:
        json.dump(lt, f_lt, indent=2)
    with open(f"{data_dir}/loot_table/blocks/{block_name}.json", "w", encoding="utf-8") as f_lt:
        json.dump(lt, f_lt, indent=2)

# 寫入 Mineable Tags
with open(f"{mc_data_dir}/tags/block/mineable/pickaxe.json", "w", encoding="utf-8") as f:
    json.dump({"replace": False, "values": pickaxe_blocks}, f, indent=2)
with open(f"{mc_data_dir}/tags/block/mineable/axe.json", "w", encoding="utf-8") as f:
    json.dump({"replace": False, "values": axe_blocks}, f, indent=2)
with open(f"{mc_data_dir}/tags/block/mineable/shovel.json", "w", encoding="utf-8") as f:
    json.dump({"replace": False, "values": shovel_blocks}, f, indent=2)

# 寫入語系檔
json.dump(lang_en, open(en_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
json.dump(lang_zh, open(zh_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# 產生全新 ModBlocks.java
mod_blocks_code = f"""package pryuan05.pysift.block;

import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.RotatedPillarBlock;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import pryuan05.pysift.PySift;

import java.util.ArrayList;
import java.util.List;

public class ModBlocks {{
    public static final List<Block> ALL_BLOCKS = new ArrayList<>();

    public static Block register(String name, BlockBehaviour.Properties properties) {{
        ResourceKey<Block> blockKey = ResourceKey.create(Registries.BLOCK, PySift.id(name));
        ResourceKey<Item> itemKey = ResourceKey.create(Registries.ITEM, PySift.id(name));
        Block block = new Block(properties.setId(blockKey));
        Registry.register(BuiltInRegistries.BLOCK, blockKey, block);
        Registry.register(BuiltInRegistries.ITEM, itemKey, new BlockItem(block, new Item.Properties().setId(itemKey)));
        ALL_BLOCKS.add(block);
        return block;
    }}

    public static Block registerPillar(String name, BlockBehaviour.Properties properties) {{
        ResourceKey<Block> blockKey = ResourceKey.create(Registries.BLOCK, PySift.id(name));
        ResourceKey<Item> itemKey = ResourceKey.create(Registries.ITEM, PySift.id(name));
        Block block = new RotatedPillarBlock(properties.setId(blockKey));
        Registry.register(BuiltInRegistries.BLOCK, blockKey, block);
        Registry.register(BuiltInRegistries.ITEM, itemKey, new BlockItem(block, new Item.Properties().setId(itemKey)));
        ALL_BLOCKS.add(block);
        return block;
    }}

{chr(10).join(java_registrations)}

    public static void registerModBlocks() {{
        PySift.LOGGER.info("Successfully registered {{}} Sift Blocks for {{}}", ALL_BLOCKS.size(), PySift.MOD_ID);
    }}
}}
"""
with open(f"{java_dir}/ModBlocks.java", "w", encoding="utf-8") as f_java:
    f_java.write(mod_blocks_code)

print("295 款方塊代碼、JSON 及貼圖已全數成功建立！")
