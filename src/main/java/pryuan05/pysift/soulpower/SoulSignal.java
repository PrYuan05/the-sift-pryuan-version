package pryuan05.pysift.soulpower;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import pryuan05.pysift.soulpower.kinetic.KineticAddon;
import pryuan05.pysift.soulpower.kinetic.SoulNetwork;

/**
 * 靈魂紅石：靈魂訊號是「帶著靈壓的紅石訊號」，強度一樣是 0–15（{@link SoulCircuit}）。
 * 這裡放共用的常數、網路狀態，以及「重新計算」的入口：基礎的靈魂迴路一定會算；
 * 機械擴充（傳動軸、齒輪…，{@link KineticAddon}）啟用時，舊的轉速網路 {@link SoulNetwork} 也跟著算。
 */
public final class SoulSignal {
    /** 引擎每隔幾 tick 重算一次網路。 */
    public static final int INTERVAL = 10;
    /** 強度 15 時機器的速度（動畫與加工速度的基準；機械擴充裡是 RPM）。 */
    public static final int SPEED = 32;
    public static final int MAX_STRENGTH = 15;
    public static final int OVERLOAD_HAZARD_TICKS = 100;
    public static final int HAZARD_RADIUS = 6;

    /** 網路的狀態：是否運轉（speed，0 = 停）、容量、需求、是否過載或轉速衝突、算的時間。 */
    public record Result(int speed, int capacity, int stress, boolean overloaded, boolean conflict, long time) {
        public static final Result IDLE = new Result(0, 0, 0, false, false, 0);

        public float load() {
            return capacity <= 0 ? (stress > 0 ? 2f : 0f) : (float) stress / capacity;
        }
    }

    private SoulSignal() {
    }

    /** 強度 0–15 換算成機器的速度。 */
    public static float speed(int strength) {
        return (float) SPEED * strength / MAX_STRENGTH;
    }

    /** 機器的速度換算回強度（GUI 顯示用）。 */
    public static int strength(float speed) {
        return Math.round(Math.abs(speed) * MAX_STRENGTH / SPEED);
    }

    /** 方塊放下、拆掉或狀態改變之後：這個位置所在的網路馬上重算。 */
    public static void update(ServerLevel level, BlockPos pos) {
        SoulCircuit.invalidate();
        poll(level, pos);
    }

    /** 定期或排程的重算：同一個 tick 已經算過的靈魂迴路不重算。 */
    public static void poll(ServerLevel level, BlockPos pos) {
        SoulCircuit.update(level, pos);
        if (KineticAddon.enabled()) {
            SoulNetwork.update(level, pos);
        }
    }

    /** 拆掉 pos 的方塊之後：附近還接著的方塊各自重算（網路可能斷開）。 */
    public static void updateAround(ServerLevel level, BlockPos pos) {
        SoulCircuit.invalidate();
        for (Direction d : Direction.values()) {
            SoulCircuit.update(level, pos.relative(d));
        }
        if (KineticAddon.enabled()) {
            SoulNetwork.updateAround(level, pos);
        }
    }

    /**
     * 貼在這個方塊上的原版紅石訊號（不算靈魂導線等靈魂元件，它們給的是動力不是控制）。
     * 機器用它暫停，引擎用它關閉。
     */
    public static int externalRedstone(Level level, BlockPos pos) {
        int best = 0;
        for (Direction d : Direction.values()) {
            BlockPos n = pos.relative(d);
            BlockState ns = level.getBlockState(n);
            if (ns.getBlock() instanceof SoulConductor) {
                continue;
            }
            best = Math.max(best, level.getSignal(n, d));
        }
        return best;
    }
}
