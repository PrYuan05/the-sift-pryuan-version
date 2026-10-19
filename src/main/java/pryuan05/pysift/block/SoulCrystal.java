package pryuan05.pysift.block;

import net.fabricmc.fabric.api.creativetab.v1.CreativeModeTabEvents;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Registry;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.level.block.state.BlockState;
import pryuan05.pysift.fluid.SpiritInteractions;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockBehaviour;
import pryuan05.pysift.PySift;
import pryuan05.pysift.item.ModItems;

/**
 * 靈魂晶塊：迴音傀儡頭頂慢慢凝結的淡藍色發光方塊（貼圖取自傀儡模型頭頂那顆方塊）。
 * 傀儡會把它送給歌者，玩家也能右鍵傀儡取下；泥板厚甲怪用它繁殖。資源由 tools/worldgen/build_soul_crystal.py 產生。
 * 靈液碰到水也會凝成靈魂晶塊（SpiritInteractions）。放在世界裡的晶塊挖得掉但不掉落（掉落表是空的），
 * 消失時（挖掉、炸掉、被取代）會放出一群自訂的靈魂粒子 soul_wisp。
 */
public final class SoulCrystal {
    public static final Block SOUL_CRYSTAL_BLOCK;
    public static final Item SOUL_CRYSTAL_BLOCK_ITEM;

    static {
        ResourceKey<Block> blockKey = ResourceKey.create(Registries.BLOCK, PySift.id("soul_crystal_block"));
        ResourceKey<Item> itemKey = ResourceKey.create(Registries.ITEM, PySift.id("soul_crystal_block"));
        SOUL_CRYSTAL_BLOCK = Registry.register(BuiltInRegistries.BLOCK, blockKey, new SoulCrystalBlock(
                BlockBehaviour.Properties.ofFullCopy(Blocks.AMETHYST_BLOCK).lightLevel(state -> 10).setId(blockKey)));
        SOUL_CRYSTAL_BLOCK_ITEM = Registry.register(BuiltInRegistries.ITEM, itemKey,
                new BlockItem(SOUL_CRYSTAL_BLOCK, new Item.Properties().setId(itemKey)));
    }

    private SoulCrystal() {
    }

    /** 方塊消失時，晶塊裡的靈魂飄出來。 */
    public static class SoulCrystalBlock extends Block {
        public SoulCrystalBlock(BlockBehaviour.Properties properties) {
            super(properties);
        }

        @Override
        protected void affectNeighborsAfterRemoval(BlockState state, ServerLevel level, BlockPos pos, boolean movedByPiston) {
            super.affectNeighborsAfterRemoval(state, level, pos, movedByPiston);
            if (!movedByPiston) {
                SpiritInteractions.releaseSouls(level, pos, 8);
                level.playSound(null, pos, SoundEvents.SOUL_ESCAPE.value(), SoundSource.BLOCKS, 1.2f, 1.0f);
            }
        }
    }

    public static void register() {
        CreativeModeTabEvents.modifyOutputEvent(ModItems.BLOCKS_TAB_KEY).register(output -> output.accept(SOUL_CRYSTAL_BLOCK_ITEM));
        PySift.LOGGER.info("Registered soul crystal block");
    }
}
