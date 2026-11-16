package pryuan05.pysift.soulpower;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.tags.BlockTags;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.block.state.BlockState;

import java.util.ArrayList;
import java.util.List;

/**
 * 紫龍晶光束（第二種無線傳動）：從發射器正面射出，最遠 {@link #RANGE} 格；穿過空氣與不擋光的方塊（玻璃、花草…），
 * 碰到紫龍晶稜鏡就轉向稜鏡指的方向，打中接收器的正面就連通。光束的路徑在伺服器（網路、傷害）與
 * 用戶端（渲染）用同一個函式算，所以看到的就是實際的路徑。
 */
public final class CharoiteBeam {
    public static final int RANGE = 32;

    /** 一段直線光束：從 from 的中心朝 dir 走 length 格。 */
    public record Segment(BlockPos from, Direction dir, float length) {
    }

    /** 追蹤的結果：每一段光束，以及打中的接收器（null = 沒打中）。 */
    public record Trace(List<Segment> segments, BlockPos receiver) {
    }

    private CharoiteBeam() {
    }

    public static Trace trace(BlockGetter level, BlockPos emitter, Direction dir) {
        List<Segment> segments = new ArrayList<>();
        BlockPos start = emitter;
        BlockPos pos = emitter;
        int run = 0;
        int turns = 0;
        for (int steps = 0; steps < RANGE; steps++) {
            pos = pos.relative(dir);
            run++;
            BlockState state = level.getBlockState(pos);
            if (state.getBlock() instanceof CharoitePrismBlock && turns < 16) {
                Direction out = state.getValue(CharoitePrismBlock.FACING);
                segments.add(new Segment(start, dir, run));
                if (out == dir.getOpposite()) {
                    return new Trace(segments, null);   // pointing back: the beam ends in the prism
                }
                start = pos;
                run = 0;
                dir = out;
                turns++;
                continue;
            }
            if (state.getBlock() instanceof CharoiteBeamBlock beam && !beam.emitter
                    && state.getValue(SoulMachineBlock.FACING) == dir.getOpposite()) {
                segments.add(new Segment(start, dir, run - 0.3f));
                return new Trace(segments, pos.immutable());
            }
            if (!passes(state)) {
                segments.add(new Segment(start, dir, run - 0.5f));
                return new Trace(segments, null);
            }
        }
        segments.add(new Segment(start, dir, run));
        return new Trace(segments, null);
    }

    /** 光束穿得過：空氣、玻璃、不完整遮擋的方塊（草、花、鐵欄杆…）。 */
    static boolean passes(BlockState state) {
        return state.isAir() || !state.canOcclude() || state.is(BlockTags.IMPERMEABLE);
    }
}
