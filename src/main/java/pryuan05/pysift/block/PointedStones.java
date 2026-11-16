package pryuan05.pysift.block;

import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.SpeleothemBlock;
import net.minecraft.world.level.block.state.BlockBehaviour;
import pryuan05.pysift.PySift;

import java.util.LinkedHashMap;
import java.util.Map;

/**
 * 尖石（v2.1.0 地底裝飾）：每一種洞穴各有自己的「滴水石」，用該層的石材長成，和原版鋒利滴水石一樣
 * 有尖端／錐台／中段／底座、上下兩個方向，會自己算粗細、懸空的鐘乳石會掉下來砸人、站在石筍上摔落會加傷害。
 * 26.3 的原版 {@link SpeleothemBlock} 已經把這些行為做成通用的（鋒利滴水石、硫磺尖刺都繼承它），這裡只給石材與聲音。
 * <ul>
 *   <li>pointed_dark_slate：枯竭窟（暗板岩）</li>
 *   <li>pointed_crimson_vein_stone：紅區洞穴（赤紅脈石）</li>
 *   <li>pointed_void_stone：共鳴穹窟（虛空石）</li>
 *   <li>pointed_violet_strata：靈液深淵（紫地層）</li>
 * </ul>
 * 原版的 #minecraft:speleothems 標籤收了它們，原版的 minecraft:speleothem／speleothem_cluster 特徵直接拿來生成
 * （tools/worldgen/build_the_sift.py）。方塊資源由 tools/worldgen/build_pointed_stones.py 產生，貼圖在 textures/block/pointed/。
 */
public final class PointedStones {
    /** 尖石 id → 它長在上面的石材 id。 */
    public static final Map<String, String> STONES = new LinkedHashMap<>();
    public static final Map<String, Block> BLOCKS = new LinkedHashMap<>();

    static {
        STONES.put("pointed_dark_slate", "dark_slate");
        STONES.put("pointed_crimson_vein_stone", "crimson_vein_stone");
        STONES.put("pointed_void_stone", "void_stone");
        STONES.put("pointed_violet_strata", "violet_strata");
    }

    private PointedStones() {
    }

    /** 鋒利滴水石掉下來的音效事件（LevelEvent 1045），尖石沿用。 */
    private static final int LANDING_SOUND = 1045;

    public static class PointedStoneBlock extends SpeleothemBlock {
        public PointedStoneBlock(Block growOn, BlockBehaviour.Properties properties) {
            super(growOn.defaultBlockState(), properties);
        }

        @Override
        protected int getStalactiteLandingSound() {
            return LANDING_SOUND;
        }
    }

    public static void register() {
        for (Map.Entry<String, String> e : STONES.entrySet()) {
            Block stone = BuiltInRegistries.BLOCK.getValue(PySift.id(e.getValue()));
            ResourceKey<Block> blockKey = ResourceKey.create(Registries.BLOCK, PySift.id(e.getKey()));
            ResourceKey<Item> itemKey = ResourceKey.create(Registries.ITEM, PySift.id(e.getKey()));
            Block block = new PointedStoneBlock(stone, BlockBehaviour.Properties.ofFullCopy(Blocks.POINTED_DRIPSTONE)
                    .mapColor(stone.defaultMapColor()).setId(blockKey));
            Registry.register(BuiltInRegistries.BLOCK, blockKey, block);
            Registry.register(BuiltInRegistries.ITEM, itemKey, new BlockItem(block, new Item.Properties().setId(itemKey)));
            ModBlocks.ALL_BLOCKS.add(block);
            BLOCKS.put(e.getKey(), block);
        }
        PySift.LOGGER.debug("Registered {} pointed stones", BLOCKS.size());
    }
}
