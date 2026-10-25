package pryuan05.pysift.block;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.LevelReader;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.SnowLayerBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.Property;
import net.minecraft.world.level.lighting.LightEngine;
import pryuan05.pysift.PySift;

import java.util.HashMap;
import java.util.Map;

/**
 * 自然生成的地表方塊被蓋住時退化成它下方的方塊，規則和原版草方塊變泥土一樣（SpreadingSnowyBlock#canStayAlive）：
 * 上方是一層雪就保持；上方是滿格液體，或上方方塊完全不透光（光線衰減 ≥ 15）時，下一次隨機刻就變成下方方塊。
 * <p>
 * 對照表和 tools/worldgen/build_the_sift.py 的地表規則一致（*_TOP → *_UNDER、桌山的 top → body）。
 * 複合面方塊只有頂面朝上（facing=up，世界生成放的方向）時才會退化，玩家側放或倒放的不受影響。
 */
public final class SurfaceDecay {
    /** 地表方塊 → 被蓋住後變成的方塊（id 與屬性）。 */
    private static final Map<String, Under> UNDER = Map.of(
            "crimson_capped_crimson_strata_3", new Under("silted_strata", Map.of("silt", "0")),       // 赤紅沉積峽谷、紅區洞穴
            "violet_capped_dark_slate", new Under("dark_slate", Map.of("fade", "0")),                 // 紫晶深板岩區
            "crimson_capped_crimson_strata_2", new Under("abyssal_strata", Map.of("depth", "0")),     // 柳絮林地
            "capped_crimson_strata", new Under("ember_stone", Map.of("heat", "0")),                    // 峽谷桌山頂
            "void_capped_crimson_01", new Under("crimson_vein_stone", Map.of("crimson_spread", "4"))  // 搖籃曲山丘
    );
    private static final Map<Block, BlockState> RESOLVED = new HashMap<>();

    private record Under(String id, Map<String, String> properties) {
    }

    private SurfaceDecay() {
    }

    public static boolean isSurfaceName(String name) {
        return UNDER.containsKey(name);
    }

    public static boolean isSurface(Block block) {
        return UNDER.containsKey(BuiltInRegistries.BLOCK.getKey(block).getPath());
    }

    /** 上方沒有蓋住（原版草方塊的存活條件）。 */
    public static boolean canStayUncovered(BlockState state, LevelReader level, BlockPos pos) {
        BlockState above = level.getBlockState(pos.above());
        if (above.is(Blocks.SNOW) && above.getValue(SnowLayerBlock.LAYERS) == 1) {
            return true;
        }
        if (above.getFluidState().isFull()) {
            return false;
        }
        return LightEngine.getLightDampeningInto(state, above, Direction.UP, above.getLightDampening()) < 15;
    }

    /** 隨機刻：被蓋住就換成下方方塊。 */
    public static void randomTick(BlockState state, ServerLevel level, BlockPos pos) {
        if (!canStayUncovered(state, level, pos)) {
            level.setBlockAndUpdate(pos, underOf(state.getBlock()));
        }
    }

    private static BlockState underOf(Block surface) {
        return RESOLVED.computeIfAbsent(surface, block -> {
            Under under = UNDER.get(BuiltInRegistries.BLOCK.getKey(block).getPath());
            BlockState result = BuiltInRegistries.BLOCK.getValue(PySift.id(under.id())).defaultBlockState();
            for (Map.Entry<String, String> e : under.properties().entrySet()) {
                result = withValue(result, e.getKey(), e.getValue());
            }
            return result;
        });
    }

    private static <T extends Comparable<T>> BlockState withValue(BlockState state, String name, String value) {
        @SuppressWarnings("unchecked")
        Property<T> property = (Property<T>) state.getBlock().getStateDefinition().getProperty(name);
        return property == null ? state : property.getValue(value).map(v -> state.setValue(property, v)).orElse(state);
    }
}
