package pryuan05.pysift.fluid;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.FluidTags;
import net.minecraft.world.level.LevelAccessor;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.Property;
import net.minecraft.world.level.material.FluidState;
import pryuan05.pysift.PySift;
import pryuan05.pysift.block.SoulCrystal;
import pryuan05.pysift.particle.ModParticles;

/**
 * 靈液與其他液體相遇（由 LiquidBlockMixin / LavaFluidMixin 呼叫，取代原版把靈液當水的結果）：
 * <ul>
 *   <li>岩漿源頭碰到靈液 → 虛空黑曜石；流動岩漿碰到靈液、或岩漿往下流進靈液 → 虛空石（暗色）。</li>
 *   <li>靈液碰到水 → 靈液變成靈魂晶塊（冒出靈魂與嘶聲）。</li>
 * </ul>
 */
public final class SpiritInteractions {
    private SpiritInteractions() {
    }

    public static boolean isSpirit(FluidState state) {
        return state.is(ModFluids.SPIRIT_LIQUID) || state.is(ModFluids.FLOWING_SPIRIT_LIQUID);
    }

    /** 真正的水（#water 但不是靈液）。 */
    public static boolean isRealWater(FluidState state) {
        return state.is(FluidTags.WATER) && !isSpirit(state);
    }

    private static Block block(String name) {
        return BuiltInRegistries.BLOCK.getValue(PySift.id(name));
    }

    /** 虛空石，tone=dark（和世界生成的地底石頭同一種）。 */
    @SuppressWarnings({"unchecked", "rawtypes"})
    private static BlockState voidStone() {
        BlockState state = block("void_stone").defaultBlockState();
        Property tone = state.getBlock().getStateDefinition().getProperty("tone");
        if (tone != null) {
            java.util.Optional value = tone.getValue("dark");
            if (value.isPresent()) {
                state = state.setValue(tone, (Comparable) value.get());
            }
        }
        return state;
    }

    /**
     * 岩漿方塊（pos）旁邊（上方或四周）有靈液時，岩漿凝固。回傳 true 表示已處理，原版不要再判斷。
     * 方向和原版一樣用 LiquidBlock.POSSIBLE_FLOW_DIRECTIONS 的反方向（下、南、北、東、西 → 上與四周）。
     */
    public static boolean solidifyLava(LevelAccessor level, BlockPos pos, Iterable<Direction> flowDirections) {
        for (Direction direction : flowDirections) {
            if (isSpirit(level.getFluidState(pos.relative(direction.getOpposite())))) {
                BlockState result = level.getFluidState(pos).isSource() ? block("void_obsidian").defaultBlockState() : voidStone();
                level.setBlock(pos, result, Block.UPDATE_ALL);
                level.levelEvent(1501, pos, 0);   // 原版岩漿凝固的嘶聲與煙
                return true;
            }
        }
        return false;
    }

    /** 岩漿往下流進靈液：靈液那格變成虛空石（原版是變石頭）。 */
    public static boolean lavaFlowsDownIntoSpirit(LevelAccessor level, BlockPos pos) {
        if (!isSpirit(level.getFluidState(pos))) {
            return false;
        }
        level.setBlock(pos, voidStone(), Block.UPDATE_ALL);
        level.levelEvent(1501, pos, 0);
        return true;
    }

    /** 靈液方塊（pos）的六個面任一碰到水：靈液凝成靈魂晶塊。回傳 true 表示已處理。 */
    public static boolean crystallizeSpirit(LevelAccessor level, BlockPos pos) {
        for (Direction direction : Direction.values()) {
            if (isRealWater(level.getFluidState(pos.relative(direction)))) {
                level.setBlock(pos, SoulCrystal.SOUL_CRYSTAL_BLOCK.defaultBlockState(), Block.UPDATE_ALL);
                level.playSound(null, pos, SoundEvents.SOUL_ESCAPE.value(), SoundSource.BLOCKS, 1.0f, 0.8f);
                level.playSound(null, pos, SoundEvents.FIRE_EXTINGUISH, SoundSource.BLOCKS, 0.5f, 1.6f);
                if (level instanceof ServerLevel server) {
                    releaseSouls(server, pos, 4);
                }
                return true;
            }
        }
        return false;
    }

    /** 從方塊中心放出 count 個往上飄的 soul_wisp（count=0 模式：每個粒子用 (dx,dy,dz) 當速度）。 */
    public static void releaseSouls(ServerLevel level, BlockPos pos, int count) {
        for (int i = 0; i < count; i++) {
            double vx = (level.getRandom().nextDouble() - 0.5) * 0.08;
            double vz = (level.getRandom().nextDouble() - 0.5) * 0.08;
            double vy = 0.03 + level.getRandom().nextDouble() * 0.05;
            level.sendParticles(ModParticles.SOUL_WISP, pos.getX() + 0.2 + level.getRandom().nextDouble() * 0.6,
                    pos.getY() + 0.3 + level.getRandom().nextDouble() * 0.5, pos.getZ() + 0.2 + level.getRandom().nextDouble() * 0.6,
                    0, vx, vy, vz, 1.0);
        }
    }
}
