package pryuan05.pysift.soulpower;

import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.util.StringRepresentable;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.EnumProperty;
import pryuan05.pysift.PySift;

/**
 * 靈魂動力機器會動的部件（Create 的 partial model）：這個方塊永遠不會被放進世界，只拿來掛部件模型
 * （blockstates/soul_power_part.json → models/block/soul_power_parts/&lt;部件&gt;.json），讓用戶端的渲染器
 * 依轉速旋轉、平移後畫出來。部件都以方塊中心為原點、繞 Y 軸建模。
 */
public final class SoulParts {
    public enum Part implements StringRepresentable {
        SHAFT, COG, LARGE_COG, FLYWHEEL, PISTON, MILLSTONE, EMITTER_DISH, RECEIVER_DISH, WAVE_RING, WAVE_CORE, DIAL, NEEDLE,
        SIEVE, LENS, CRANK, HALF_SHAFT, FAN, DRILL;

        @Override
        public String getSerializedName() {
            return name().toLowerCase(java.util.Locale.ROOT);
        }
    }

    public static final EnumProperty<Part> PART = EnumProperty.create("part", Part.class);
    private static final ResourceKey<Block> KEY = ResourceKey.create(Registries.BLOCK, PySift.id("soul_power_part"));
    public static final Block BLOCK = Registry.register(BuiltInRegistries.BLOCK, KEY,
            new Block(BlockBehaviour.Properties.of().noLootTable().noOcclusion().setId(KEY)) {
                @Override
                protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
                    builder.add(PART);
                }
            });

    private SoulParts() {
    }

    public static BlockState of(Part part) {
        return BLOCK.defaultBlockState().setValue(PART, part);
    }

    static void init() {
    }
}
