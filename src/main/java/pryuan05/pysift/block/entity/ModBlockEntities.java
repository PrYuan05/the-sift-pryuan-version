package pryuan05.pysift.block.entity;

import net.fabricmc.fabric.api.object.builder.v1.block.entity.FabricBlockEntityTypeBuilder;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.world.level.block.entity.BlockEntityType;
import pryuan05.pysift.PySift;
import pryuan05.pysift.block.ModBlocks;

public final class ModBlockEntities {
    public static final BlockEntityType<SiftPortalBlockEntity> SIFT_PORTAL = Registry.register(
            BuiltInRegistries.BLOCK_ENTITY_TYPE, PySift.id("sift_portal"),
            FabricBlockEntityTypeBuilder.create(SiftPortalBlockEntity::new, ModBlocks.SIFT_PORTAL).build());

    private ModBlockEntities() {
    }

    public static void registerModBlockEntities() {
        PySift.LOGGER.info("Registering Block Entities for {}", PySift.MOD_ID);
    }
}
