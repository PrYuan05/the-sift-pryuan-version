package pryuan05.pysift.soulpower;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.core.particles.ParticleTypes;
import pryuan05.pysift.effect.ModEffects;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

/**
 * 靈魂動力網路：從一個方塊出發，沿著接得上的面（傳動軸、機器）與靈魂振波的無線連結找出整個網路，
 * 算出容量（運轉中的引擎各 {@link #ENGINE_CAPACITY} SP，經過振波時打 {@link #WAVE_EFFICIENCY} 折）與需求
 * （每台研磨機 {@link #GRINDER_STRESS} SP）。需求超過容量就過載：全部停轉，持續 {@link #OVERLOAD_HAZARD_TICKS}
 * 之後，網路裡的機器周圍 {@link #HAZARD_RADIUS} 格的生物得到靈魂剝奪。
 * <p>
 * 什麼時候算：引擎每 {@link #INTERVAL} tick 算一次（同一個 tick 已經算過的網路不重算），
 * 以及方塊放下或拆掉的時候（拆掉時從相鄰方塊各算一次，網路可能斷成兩半）。
 */
public final class SoulNetwork {
    public static final int INTERVAL = 10;
    public static final int SPEED = 32;                 // RPM
    public static final int ENGINE_CAPACITY = 256;      // SP
    public static final int GRINDER_STRESS = 64;        // SP
    public static final float WAVE_EFFICIENCY = 0.9f;
    public static final int OVERLOAD_HAZARD_TICKS = 100;
    public static final int HAZARD_RADIUS = 6;
    private static final int MAX_NODES = 1024;

    /** 網路的狀態：轉速（0 = 停）、容量、需求、是否過載、算的時間。 */
    public record Result(int speed, int capacity, int stress, boolean overloaded, long time) {
        public static final Result IDLE = new Result(0, 0, 0, false, 0);
    }

    private SoulNetwork() {
    }

    /** 從 start 找出整個網路、算出狀態並寫回每個成員。回傳這個網路的引擎（呼叫者用來判斷是否已算過）。 */
    public static List<SpiritEngineBlockEntity> update(ServerLevel level, BlockPos start) {
        long now = level.getGameTime();
        Set<BlockPos> seen = new HashSet<>();
        ArrayDeque<BlockPos> queue = new ArrayDeque<>();
        List<BlockPos> members = new ArrayList<>();
        List<SpiritEngineBlockEntity> engines = new ArrayList<>();
        int grinders = 0;
        boolean wireless = false;
        if (!(level.getBlockState(start).getBlock() instanceof SoulKinetic)) {
            return engines;
        }
        seen.add(start);
        queue.add(start);
        while (!queue.isEmpty() && members.size() < MAX_NODES) {
            BlockPos pos = queue.poll();
            BlockState state = level.getBlockState(pos);
            if (!(state.getBlock() instanceof SoulKinetic kinetic)) {
                continue;
            }
            members.add(pos);
            if (level.getBlockEntity(pos) instanceof SpiritEngineBlockEntity engine) {
                engines.add(engine);
            }
            if (state.getBlock() instanceof SoulGrinderBlock) {
                grinders++;
            }
            for (Direction dir : Direction.values()) {
                if (!kinetic.connects(state, dir)) {
                    continue;
                }
                BlockPos next = pos.relative(dir);
                BlockState ns = level.getBlockState(next);
                if (ns.getBlock() instanceof SoulKinetic other && other.connects(ns, dir.getOpposite()) && seen.add(next)) {
                    queue.add(next);
                }
            }
            if (level.getBlockEntity(pos) instanceof SoulWaveBlockEntity wave) {
                for (BlockPos link : wave.findLinks(level)) {
                    wireless = true;
                    if (seen.add(link)) {
                        queue.add(link);
                    }
                }
            }
        }
        int capacity = 0;
        for (SpiritEngineBlockEntity engine : engines) {
            if (engine.isBurning()) {
                capacity += ENGINE_CAPACITY;
            }
        }
        if (wireless) {
            capacity = Math.round(capacity * WAVE_EFFICIENCY);
        }
        int stress = grinders * GRINDER_STRESS;
        boolean overloaded = capacity > 0 && stress > capacity;
        Result result = new Result(capacity > 0 && !overloaded ? SPEED : 0, capacity, stress, overloaded, now);
        for (BlockPos pos : members) {
            BlockState state = level.getBlockState(pos);
            if (state.getBlock() instanceof SoulKinetic kinetic) {
                kinetic.onNetwork(level, pos, state, result);
            }
        }
        // overload: the engines count how long it lasts; after a while the machines burn the souls around them
        boolean hazard = false;
        for (SpiritEngineBlockEntity engine : engines) {
            hazard |= engine.countOverload(overloaded, INTERVAL) >= OVERLOAD_HAZARD_TICKS;
        }
        if (overloaded) {
            for (BlockPos pos : members) {
                if (level.getBlockEntity(pos) instanceof SoulKinetic.Member) {
                    level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, pos.getX() + 0.5, pos.getY() + 1.0, pos.getZ() + 0.5,
                            3, 0.3, 0.1, 0.3, 0.01);
                    if (hazard) {
                        for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, new AABB(pos).inflate(HAZARD_RADIUS))) {
                            e.addEffect(new MobEffectInstance(ModEffects.SOUL_DEPRIVATION, 200));
                        }
                    }
                }
            }
        }
        return engines;
    }

    /** 拆掉 pos 的方塊之後：相鄰還接著的方塊各自重算（網路可能斷開）。 */
    public static void updateAround(ServerLevel level, BlockPos pos) {
        for (Direction dir : Direction.values()) {
            update(level, pos.relative(dir));
        }
    }
}
