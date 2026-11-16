package pryuan05.pysift.client;

import net.minecraft.client.color.block.BlockTintSource;
import net.minecraft.client.renderer.block.BlockAndTintGetter;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.util.Mth;
import net.minecraft.world.level.block.DoublePlantBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.DoubleBlockHalf;

import java.util.Map;

/**
 * 依腳下地板染色：讀植物下方那格（兩格高植物的上半讀下半的下方）的方塊，查 {@link FloorTints} 色表；
 * 查不到（例如種在原版方塊上、或物品）就用預設色。模型的面要有 tintindex 0 才會被染色。
 * 色表給兩個顏色的地板（紫岩：紫＋淡黃）依座標分成一塊一塊的色區：平滑的格點雜訊（約 {@value #PATCH} 格一區）
 * 決定用哪個顏色，交界處 smoothstep 漸變，所以同一片草原會一部分紫、一部分黃。
 */
public final class FloorTint implements BlockTintSource {
    private static final int PATCH = 6;
    private final int fallback;
    private final Map<String, int[]> table;

    public FloorTint(int fallback) {
        this(fallback, FloorTints.COLORS);
    }

    /** 用另一張地面 → 顏色表。 */
    public FloorTint(int fallback, Map<String, int[]> table) {
        this.fallback = fallback;
        this.table = table;
    }

    @Override
    public int color(BlockState state) {
        return this.fallback;
    }

    @Override
    public int colorInWorld(BlockState state, BlockAndTintGetter level, BlockPos pos) {
        BlockPos floor = pos.below();
        if (state.hasProperty(DoublePlantBlock.HALF) && state.getValue(DoublePlantBlock.HALF) == DoubleBlockHalf.UPPER) {
            floor = floor.below();
        }
        int[] colors = table.get(BuiltInRegistries.BLOCK.getKey(level.getBlockState(floor).getBlock()).toString());
        if (colors == null) {
            return this.fallback;
        }
        if (colors.length == 1) {
            return colors[0];
        }
        float t = Mth.clamp((patchNoise(pos.getX(), pos.getZ()) - 0.38F) / 0.24F, 0.0F, 1.0F);   // soft edge, ~half each
        t = t * t * (3.0F - 2.0F * t);
        return lerpColor(colors[0], colors[1], t);
    }

    /** Smooth value noise in [0, 1): hashed lattice every PATCH blocks, bilinear with smoothstep. */
    private static float patchNoise(int x, int z) {
        float fx = (float) x / PATCH, fz = (float) z / PATCH;
        int x0 = Mth.floor(fx), z0 = Mth.floor(fz);
        float u = fx - x0, v = fz - z0;
        u = u * u * (3.0F - 2.0F * u);
        v = v * v * (3.0F - 2.0F * v);
        float a = Mth.lerp(u, hash(x0, z0), hash(x0 + 1, z0));
        float b = Mth.lerp(u, hash(x0, z0 + 1), hash(x0 + 1, z0 + 1));
        return Mth.lerp(v, a, b);
    }

    private static float hash(int x, int z) {
        long h = x * 0x9E3779B97F4A7C15L ^ z * 0xC2B2AE3D27D4EB4FL;
        h = (h ^ (h >>> 31)) * 0xBF58476D1CE4E5B9L;
        h ^= h >>> 29;
        return (h >>> 40) / (float) (1L << 24);
    }

    private static int lerpColor(int c0, int c1, float t) {
        int r = Math.round(Mth.lerp(t, (c0 >> 16) & 0xFF, (c1 >> 16) & 0xFF));
        int g = Math.round(Mth.lerp(t, (c0 >> 8) & 0xFF, (c1 >> 8) & 0xFF));
        int b = Math.round(Mth.lerp(t, c0 & 0xFF, c1 & 0xFF));
        return 0xFF000000 | r << 16 | g << 8 | b;
    }
}
