package pryuan05.pysift.block;

import net.fabricmc.fabric.api.object.builder.v1.block.entity.FabricBlockEntityTypeBuilder;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import pryuan05.pysift.PySift;
import pryuan05.pysift.block.entity.ResonantJukeboxBlockEntity;

/** 開門儀式用的方塊：共鳴唱片盒（沒有物品形式，只由迴音傀儡放置）。 */
public final class RitualBlocks {
    private static final ResourceKey<Block> RESONANT_JUKEBOX_KEY = ResourceKey.create(Registries.BLOCK, PySift.id("resonant_jukebox"));
    public static final Block RESONANT_JUKEBOX = Registry.register(BuiltInRegistries.BLOCK, RESONANT_JUKEBOX_KEY,
            new ResonantJukeboxBlock(BlockBehaviour.Properties.ofFullCopy(Blocks.JUKEBOX).lightLevel(state -> 10).noOcclusion()
                    .setId(RESONANT_JUKEBOX_KEY)));
    public static final BlockEntityType<ResonantJukeboxBlockEntity> RESONANT_JUKEBOX_ENTITY = Registry.register(
            BuiltInRegistries.BLOCK_ENTITY_TYPE, PySift.id("resonant_jukebox"),
            FabricBlockEntityTypeBuilder.create(ResonantJukeboxBlockEntity::new, RESONANT_JUKEBOX).build());

    private RitualBlocks() {
    }

    static void load() {
    }
}
