package pryuan05.pysift.soulpower;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.SculkShriekerBlock;
import net.minecraft.world.level.gameevent.GameEvent;
import net.minecraft.world.level.block.RedstoneWireBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import pryuan05.pysift.effect.ModEffects;
import pryuan05.pysift.sound.ModSounds;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.PriorityQueue;
import java.util.Set;

/**
 * 靈魂迴路：原版紅石的進階版。從一個方塊出發找出整個迴路（相接的靈魂元件加上無線連結），然後算兩種訊號：
 * <ul>
 *   <li><b>靈魂訊號</b>（帶靈壓）：從運轉中的靈液引擎出發，強度 15，每經過 2 格少 1 級（原版紅石是每格少 1 級），
 *       無線每跳一次另外扣（光束 0、振波 1、靈脈 2 級）。機器靠它運轉，速度 = 強度 ÷ 15。</li>
 *   <li><b>原版訊號</b>（沒有靈壓）：中繼器、拉桿、紅石火把等元件貼著靈魂導線，就能把訊號送進來，
 *       一樣每 2 格少 1 級。只能驅動原版元件，機器不會動。</li>
 * </ul>
 * 靈魂導線對外的紅石強度取兩者較大的。紅石粉不能當輸入：它會從導線取得訊號，再送回來就會自己鎖住。
 * <p>
 * 容量 = 每台運轉中的引擎 256 SP；需求 = Σ 機器的滿載值 × 強度 ÷ 15（被原版紅石暫停的機器不算）。
 * 需求超過容量就<b>過載</b>：靈魂訊號全部歸零，持續 {@link SoulSignal#OVERLOAD_HAZARD_TICKS} 之後，
 * 迴路裡的方塊周圍 {@link SoulSignal#HAZARD_RADIUS} 格的生物得到靈魂剝奪。
 * <p>
 * 花費以「半格強度」計：相鄰一格 1，所以強度 = 15 − 花費 ÷ 2。
 */
public final class SoulCircuit {
    private static final int MAX_NODES = 1024;
    private static final int UNREACHED = Integer.MAX_VALUE;
    /** 這個 tick 已經算過的方塊（同一個迴路不必每個成員各算一次）。 */
    private static final Set<Long> SOLVED = new HashSet<>();
    private static long solvedTick = Long.MIN_VALUE;
    private static Object solvedLevel;

    /** 幽匿催化體綻放時，貼著它的導線得到一小段時間的靈魂（生物死掉放出來的）：強度 15、容量 {@link #CATALYST_CAPACITY}。 */
    public static final int CATALYST_TICKS = 200;
    public static final int CATALYST_CAPACITY = 32;
    private static final int SHRIEK_TICKS = 90;
    private static final Map<ResourceKey<Level>, Map<Long, Long>> CATALYST = new HashMap<>();

    private SoulCircuit() {
    }

    /** 貼著綻放的催化體的導線：從現在起 {@link #CATALYST_TICKS} tick 是靈魂訊號源。 */
    public static void charge(ServerLevel level, BlockPos conduit) {
        CATALYST.computeIfAbsent(level.dimension(), k -> new HashMap<>()).put(conduit.asLong(), level.getGameTime() + CATALYST_TICKS);
        invalidate();
    }

    public static boolean charged(ServerLevel level, BlockPos conduit) {
        Map<Long, Long> map = CATALYST.get(level.dimension());
        if (map == null) {
            return false;
        }
        Long until = map.get(conduit.asLong());
        if (until == null) {
            return false;
        }
        if (until <= level.getGameTime()) {
            map.remove(conduit.asLong());
            return false;
        }
        return true;
    }

    private record Edge(BlockPos to, int cost) {
    }

    /** 迴路有變動（放下、拆掉方塊）：下一次 update 一定重算。 */
    public static void invalidate() {
        SOLVED.clear();
    }

    public static void update(ServerLevel level, BlockPos start) {
        BlockState startState = level.getBlockState(start);
        if (!(startState.getBlock() instanceof SoulConductor)) {
            return;
        }
        long now = level.getGameTime();
        if (now != solvedTick || solvedLevel != level) {
            SOLVED.clear();
            solvedTick = now;
            solvedLevel = level;
        }
        if (SOLVED.contains(start.asLong())) {
            return;
        }
        // 1. 找出整個迴路，記下每一條可以走的邊
        List<BlockPos> members = new ArrayList<>();
        Map<BlockPos, List<Edge>> edges = new HashMap<>();
        Set<BlockPos> seen = new HashSet<>();
        ArrayDeque<BlockPos> queue = new ArrayDeque<>();
        seen.add(start.immutable());
        queue.add(start.immutable());
        while (!queue.isEmpty() && members.size() < MAX_NODES) {
            BlockPos pos = queue.poll();
            BlockState state = level.getBlockState(pos);
            if (!(state.getBlock() instanceof SoulConductor conductor)) {
                continue;
            }
            members.add(pos);
            List<Edge> out = edges.computeIfAbsent(pos, k -> new ArrayList<>());
            for (Direction dir : Direction.values()) {
                if (!conductor.conducts(state, dir)) {
                    continue;
                }
                BlockPos n = pos.relative(dir);
                BlockState ns = level.getBlockState(n);
                if (ns.getBlock() instanceof SoulConductor other && other.conducts(ns, dir.getOpposite())) {
                    out.add(new Edge(n, 1));
                    if (seen.add(n)) {
                        queue.add(n);
                    }
                }
            }
            if (level.getBlockEntity(pos) instanceof SoulConductor.Relay relay) {
                for (BlockPos link : relay.findLinks(level)) {
                    BlockPos to = link.immutable();
                    if (relay.sends() && level.getBlockEntity(to) instanceof SoulConductor.Relay other && other.receives()) {
                        out.add(new Edge(to, relay.hopCost()));
                    }
                    if (seen.add(to)) {
                        queue.add(to);
                    }
                }
            }
        }
        // 2. 靈魂訊號：從運轉中的引擎出發
        Map<BlockPos, Integer> soulCost = new HashMap<>();
        int capacity = 0;
        List<SpiritEngineBlockEntity> engines = new ArrayList<>();
        for (BlockPos pos : members) {
            if (level.getBlockEntity(pos) instanceof SpiritEngineBlockEntity engine) {
                engines.add(engine);
            }
            if (level.getBlockEntity(pos) instanceof SoulKinetic.Source source && source.sourceSpeed() != 0) {
                soulCost.put(pos, 0);
                capacity += Math.round(source.capacityPerRpm() * Math.abs(source.sourceSpeed()));
            }
        }
        for (BlockPos pos : members) {
            if (level.getBlockState(pos).getBlock() instanceof SoulConduitBlock && charged(level, pos)) {
                soulCost.put(pos, 0);
                capacity += CATALYST_CAPACITY;
            }
        }
        spread(soulCost, edges);
        // 3. 原版訊號：貼著靈魂導線的原版元件
        Map<BlockPos, Integer> plainCost = new HashMap<>();
        for (BlockPos pos : members) {
            if (level.getBlockState(pos).getBlock() instanceof SoulConduitBlock) {
                int ext = vanillaInput(level, pos);
                if (ext > 0) {
                    plainCost.put(pos, (SoulSignal.MAX_STRENGTH - ext) * 2);
                }
            }
        }
        spread(plainCost, edges);
        // 4. 需求
        Map<BlockPos, Integer> strength = new HashMap<>();
        float stress = 0;
        for (BlockPos pos : members) {
            int s = strengthOf(soulCost.getOrDefault(pos, UNREACHED));
            BlockState state = level.getBlockState(pos);
            float full = fullLoad(state);
            if (full > 0 && s > 0 && SoulSignal.externalRedstone(level, pos) > 0) {
                s = 0;      // 被原版紅石暫停（和漏斗被鎖住一樣）
            }
            strength.put(pos, s);
            stress += full * s / SoulSignal.MAX_STRENGTH;
        }
        boolean overloaded = capacity > 0 && stress > capacity;
        boolean running = capacity > 0 && !overloaded;
        SoulSignal.Result result = new SoulSignal.Result(running ? SoulSignal.SPEED : 0, capacity, Math.round(stress), overloaded, false, now);
        // 5. 寫回每個成員
        for (BlockPos pos : members) {
            SOLVED.add(pos.asLong());
            int soul = running ? strength.get(pos) : 0;
            BlockState state = level.getBlockState(pos);
            if (state.getBlock() instanceof SoulConduitBlock) {
                int power = Math.max(soul, strengthOf(plainCost.getOrDefault(pos, UNREACHED)));
                boolean charged = soul > 0;
                if (state.getValue(SoulConduitBlock.POWER) != power || state.getValue(SoulConduitBlock.CHARGED) != charged) {
                    level.setBlock(pos, state.setValue(SoulConduitBlock.POWER, power).setValue(SoulConduitBlock.CHARGED, charged), Block.UPDATE_ALL);
                }
            }
            if (level.getBlockEntity(pos) instanceof KineticBlockEntity member) {
                member.setCircuit(result, SoulSignal.speed(soul));
            }
        }
        // 6. 過載：引擎記錄持續多久；太久了，機器就燒掉周圍生物的靈魂
        boolean hazard = false;
        for (SpiritEngineBlockEntity engine : engines) {
            hazard |= engine.countOverload(overloaded, SoulSignal.INTERVAL) >= SoulSignal.OVERLOAD_HAZARD_TICKS;
        }
        if (overloaded) {
            if (now % 40 == 0) {
                level.playSound(null, members.get(0), ModSounds.SOUL_POWER_OVERLOAD, SoundSource.BLOCKS, 0.8f, 1.0f);
            }
            for (BlockPos pos : members) {
                if (level.getBlockEntity(pos) == null) {
                    shriek(level, pos);
                    continue;   // 導線不冒火，只有機器會
                }
                level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, pos.getX() + 0.5, pos.getY() + 0.8, pos.getZ() + 0.5, 2, 0.3, 0.1, 0.3, 0.01);
                if (hazard) {
                    for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, new AABB(pos).inflate(SoulSignal.HAZARD_RADIUS))) {
                        e.addEffect(new MobEffectInstance(ModEffects.SOUL_DEPRIVATION, 200));
                    }
                }
            }
        }
    }

    /**
     * 過載示警：貼著導線的幽匿尖嘯體尖叫（只有聲音與粒子；尖嘯體自己的警告等級是 0，所以不會召喚監守者）。
     */
    private static void shriek(ServerLevel level, BlockPos conduit) {
        if (!(level.getBlockState(conduit).getBlock() instanceof SoulConduitBlock)) {
            return;
        }
        for (Direction dir : Direction.values()) {
            BlockPos n = conduit.relative(dir);
            BlockState ns = level.getBlockState(n);
            if (ns.is(Blocks.SCULK_SHRIEKER) && !ns.getValue(SculkShriekerBlock.SHRIEKING)) {
                level.setBlock(n, ns.setValue(SculkShriekerBlock.SHRIEKING, true), Block.UPDATE_CLIENTS);
                level.scheduleTick(n, ns.getBlock(), SHRIEK_TICKS);
                level.levelEvent(3007, n, 0);      // LevelEvent.PARTICLES_SCULK_SHRIEK
                level.gameEvent(GameEvent.SHRIEK, n, GameEvent.Context.of(ns));
            }
        }
    }

    /** 多來源的最短花費（花費都是很小的非負整數）。 */
    private static void spread(Map<BlockPos, Integer> cost, Map<BlockPos, List<Edge>> edges) {
        PriorityQueue<Map.Entry<BlockPos, Integer>> open = new PriorityQueue<>(Map.Entry.comparingByValue());
        for (Map.Entry<BlockPos, Integer> e : cost.entrySet()) {
            open.add(Map.entry(e.getKey(), e.getValue()));
        }
        int limit = SoulSignal.MAX_STRENGTH * 2;
        while (!open.isEmpty()) {
            Map.Entry<BlockPos, Integer> cur = open.poll();
            if (cur.getValue() > cost.getOrDefault(cur.getKey(), UNREACHED)) {
                continue;
            }
            for (Edge edge : edges.getOrDefault(cur.getKey(), List.of())) {
                int c = cur.getValue() + edge.cost();
                if (c < limit && c < cost.getOrDefault(edge.to(), UNREACHED)) {
                    cost.put(edge.to(), c);
                    open.add(Map.entry(edge.to(), c));
                }
            }
        }
    }

    private static int strengthOf(int cost) {
        return cost == UNREACHED ? 0 : Math.max(0, SoulSignal.MAX_STRENGTH - cost / 2);
    }

    /** 機器在強度 15 時的需求（SP）。 */
    public static float fullLoad(BlockState state) {
        return state.getBlock() instanceof SoulKinetic kinetic ? kinetic.impact(state) * SoulSignal.SPEED : 0;
    }

    /**
     * 貼著這段導線的原版元件送進來的訊號：只收直接的訊號源（拉桿、中繼器、比較器、紅石火把、紅石塊…），
     * 不收紅石粉，也不收隔著方塊傳來的強充能，避免導線自己供給自己。
     */
    private static int vanillaInput(ServerLevel level, BlockPos pos) {
        int best = 0;
        for (Direction dir : Direction.values()) {
            BlockPos n = pos.relative(dir);
            BlockState ns = level.getBlockState(n);
            if (ns.getBlock() instanceof SoulConductor || ns.getBlock() instanceof RedstoneWireBlock || !ns.isSignalSource()) {
                continue;
            }
            best = Math.max(best, ns.getSignal(level, n, dir));
        }
        return Math.min(SoulSignal.MAX_STRENGTH, best);
    }
}
