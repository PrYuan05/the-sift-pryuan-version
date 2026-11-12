package pryuan05.pysift.soulpower.kinetic;

import pryuan05.pysift.soulpower.*;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.sounds.SoundSource;
import pryuan05.pysift.effect.ModEffects;
import pryuan05.pysift.sound.ModSounds;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 靈魂動力網路（Create 式）：從一個方塊出發找出整個網路，替每個方塊算出「相對轉速」（傳動比，有正負號）：
 * <ul>
 *   <li>同軸相接（傳動軸、機器的接口）：×1；</li>
 *   <li>同軸向、同平面上相鄰的兩個小齒輪：×-1（互相帶動，方向相反）；</li>
 *   <li>同軸向、同平面上斜向的大齒輪與小齒輪：大 → 小 ×-2，小 → 大 ×-1/2；</li>
 *   <li>靈魂振波等無線連結：×1（容量打 {@link #WAVE_EFFICIENCY} 折）。</li>
 * </ul>
 * 同一個方塊從兩條路得到不同的傳動比，或兩台引擎要求的轉速不一樣，就是<b>轉速衝突</b>：整個網路停下來冒煙。
 * 容量 = Σ 引擎的 capacityPerRpm × |RPM|；需求 = Σ 機器的 impact × |RPM|。需求超過容量就<b>過載</b>：全部停轉，
 * 持續 {@link #OVERLOAD_HAZARD_TICKS} 之後，網路裡的機器周圍 {@link #HAZARD_RADIUS} 格的生物得到靈魂剝奪。
 * <p>
 * 什麼時候算：引擎每 {@link #INTERVAL} tick 算一次（同一個 tick 已經算過的網路不重算），
 * 以及方塊放下或拆掉的時候（拆掉時從相鄰方塊各算一次，網路可能斷成兩半）。
 */
public final class SoulNetwork {
    public static final int INTERVAL = 10;
    public static final int SPEED = 32;                 // 引擎的轉速（RPM）
    public static final float MAX_SPEED = 256;
    public static final float WAVE_EFFICIENCY = 0.9f;
    public static final float BEAM_EFFICIENCY = 0.95f;
    public static final float VEIN_EFFICIENCY = 0.85f;
    public static final int OVERLOAD_HAZARD_TICKS = 100;
    public static final int HAZARD_RADIUS = 6;
    private static final int MAX_NODES = 1024;

    private SoulNetwork() {
    }

    /** 從 start 找出整個網路、算出狀態並寫回每個成員。回傳這個網路的引擎（呼叫者用來判斷是否已算過）。 */
    public static List<SpiritEngineBlockEntity> update(ServerLevel level, BlockPos start) {
        long now = level.getGameTime();
        List<SpiritEngineBlockEntity> engines = new ArrayList<>();
        if (!(level.getBlockState(start).getBlock() instanceof SoulKinetic)) {
            return engines;
        }
        Map<BlockPos, Float> ratio = new HashMap<>();
        ArrayDeque<BlockPos> queue = new ArrayDeque<>();
        List<BlockPos> members = new ArrayList<>();
        boolean wireless = false;
        boolean beamed = false;
        boolean veined = false;
        boolean conflict = false;
        ratio.put(start.immutable(), 1f);
        queue.add(start.immutable());
        while (!queue.isEmpty() && members.size() < MAX_NODES) {
            BlockPos pos = queue.poll();
            BlockState state = level.getBlockState(pos);
            if (!(state.getBlock() instanceof SoulKinetic kinetic)) {
                continue;
            }
            members.add(pos);
            float r = ratio.get(pos);
            List<BlockPos> next = new ArrayList<>();
            List<Float> nextRatio = new ArrayList<>();
            // 同軸相接
            for (Direction dir : Direction.values()) {
                if (!kinetic.connects(state, dir)) {
                    continue;
                }
                BlockPos n = pos.relative(dir);
                BlockState ns = level.getBlockState(n);
                if (ns.getBlock() instanceof SoulKinetic other && other.connects(ns, dir.getOpposite())) {
                    next.add(n);
                    nextRatio.add(r * kinetic.transfer(state, dir) * other.transfer(ns, dir.getOpposite()));
                }
            }
            // 齒輪咬合
            SoulKinetic.Cog cog = kinetic.cog(state);
            Direction.Axis axis = kinetic.axis(state);
            if (cog != SoulKinetic.Cog.NONE && axis != null) {
                for (Direction d : Direction.values()) {
                    if (d.getAxis() == axis) {
                        continue;
                    }
                    if (cog == SoulKinetic.Cog.SMALL && meshes(level, pos.relative(d), axis, SoulKinetic.Cog.SMALL)) {
                        next.add(pos.relative(d));
                        nextRatio.add(-r);
                    }
                    for (Direction e : Direction.values()) {
                        if (e.getAxis() == axis || e.getAxis() == d.getAxis() || e.ordinal() < d.ordinal()) {
                            continue;
                        }
                        BlockPos diag = pos.relative(d).relative(e);
                        SoulKinetic.Cog want = cog == SoulKinetic.Cog.SMALL ? SoulKinetic.Cog.LARGE : SoulKinetic.Cog.SMALL;
                        if (meshes(level, diag, axis, want)) {
                            next.add(diag);
                            nextRatio.add(cog == SoulKinetic.Cog.LARGE ? -2f * r : -0.5f * r);
                        }
                    }
                }
            }
            // 無線（靈脈：穿過岩石）
            if (level.getBlockEntity(pos) instanceof SoulVeinNodeBlockEntity node) {
                for (BlockPos link : node.findLinks(level)) {
                    veined = true;
                    next.add(link);
                    nextRatio.add(r);
                }
            }
            // 無線（紫龍晶光束）
            if (level.getBlockEntity(pos) instanceof CharoiteBeamBlockEntity beam) {
                for (BlockPos link : beam.findLinks(level)) {
                    beamed = true;
                    next.add(link);
                    nextRatio.add(r);
                }
            }
            // 無線（靈魂振波）
            if (level.getBlockEntity(pos) instanceof SoulWaveBlockEntity wave) {
                for (BlockPos link : wave.findLinks(level)) {
                    wireless = true;
                    next.add(link);
                    nextRatio.add(r);
                }
            }
            for (int i = 0; i < next.size(); i++) {
                BlockPos n = next.get(i).immutable();
                float nr = nextRatio.get(i);
                Float old = ratio.get(n);
                if (old == null) {
                    ratio.put(n, nr);
                    queue.add(n);
                } else if (Math.abs(old - nr) > 1e-3f * Math.max(1f, Math.abs(nr))) {
                    conflict = true;
                }
            }
        }
        // 引擎：每台都要求自己的轉速；換算回起點的「基準轉速」要一致
        float base = 0;
        int capacity = 0;
        for (BlockPos pos : members) {
            if (level.getBlockEntity(pos) instanceof SpiritEngineBlockEntity engine) {
                engines.add(engine);
            }
            if (level.getBlockEntity(pos) instanceof SoulKinetic.Source source && source.sourceSpeed() != 0) {
                float b = source.sourceSpeed() / ratio.get(pos);
                if (base == 0) {
                    base = b;
                } else if (Math.abs(base - b) > 1e-3f * Math.abs(b)) {
                    conflict = true;
                }
                capacity += Math.round(source.capacityPerRpm() * Math.abs(source.sourceSpeed()));
            }
        }
        // 無線連結的損耗：用到哪幾種就取最差的那一種（靈脈 15%、振波 10%、光束 5%）
        float efficiency = veined ? VEIN_EFFICIENCY : wireless ? WAVE_EFFICIENCY : beamed ? BEAM_EFFICIENCY : 1f;
        capacity = Math.round(capacity * efficiency);
        float stress = 0;
        float fastest = 0;
        for (BlockPos pos : members) {
            BlockState state = level.getBlockState(pos);
            if (state.getBlock() instanceof SoulKinetic kinetic) {
                float rpm = Math.abs(base * ratio.get(pos));
                stress += kinetic.impact(state) * rpm;
                fastest = Math.max(fastest, rpm);
            }
        }
        if (fastest > MAX_SPEED) {
            conflict = true;    // 齒輪加速太多：當成衝突，網路停下來
        }
        boolean overloaded = capacity > 0 && stress > capacity;
        boolean running = capacity > 0 && !overloaded && !conflict;
        SoulSignal.Result result = new SoulSignal.Result(running ? Math.round(Math.abs(base)) : 0, capacity, Math.round(stress), overloaded, conflict, now);
        for (BlockPos pos : members) {
            BlockState state = level.getBlockState(pos);
            if (state.getBlock() instanceof SoulKinetic kinetic) {
                kinetic.onNetwork(level, pos, state, result, running ? base * ratio.get(pos) : 0f);
            }
        }
        // 過載：引擎記錄持續多久；太久了，機器就燒掉周圍生物的靈魂。轉速衝突：冒煙
        boolean hazard = false;
        for (SpiritEngineBlockEntity engine : engines) {
            hazard |= engine.countOverload(overloaded, INTERVAL) >= OVERLOAD_HAZARD_TICKS;
        }
        if ((overloaded || conflict) && capacity > 0) {
            if (now % 40 == 0 && !members.isEmpty()) {
                level.playSound(null, members.get(0), conflict ? ModSounds.SOUL_POWER_CONFLICT : ModSounds.SOUL_POWER_OVERLOAD,
                        SoundSource.BLOCKS, 0.8f, 1.0f);
            }
            for (BlockPos pos : members) {
                level.sendParticles(conflict ? ParticleTypes.LARGE_SMOKE : ParticleTypes.SOUL_FIRE_FLAME,
                        pos.getX() + 0.5, pos.getY() + 0.8, pos.getZ() + 0.5, 2, 0.3, 0.1, 0.3, 0.01);
                if (hazard && overloaded) {
                    for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, new AABB(pos).inflate(HAZARD_RADIUS))) {
                        e.addEffect(new MobEffectInstance(ModEffects.SOUL_DEPRIVATION, 200));
                    }
                }
            }
        }
        return engines;
    }

    private static boolean meshes(ServerLevel level, BlockPos pos, Direction.Axis axis, SoulKinetic.Cog want) {
        BlockState state = level.getBlockState(pos);
        return state.getBlock() instanceof SoulKinetic k && k.cog(state) == want && k.axis(state) == axis;
    }

    /** 拆掉 pos 的方塊之後：附近還接著的方塊各自重算（網路可能斷開；齒輪可能斜向相接，所以連斜角一起）。 */
    public static void updateAround(ServerLevel level, BlockPos pos) {
        for (BlockPos p : BlockPos.betweenClosed(pos.offset(-1, -1, -1), pos.offset(1, 1, 1))) {
            if (!p.equals(pos)) {
                update(level, p.immutable());
            }
        }
    }
}
