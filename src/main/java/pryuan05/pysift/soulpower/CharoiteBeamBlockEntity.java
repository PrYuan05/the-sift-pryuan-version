package pryuan05.pysift.soulpower;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * 紫龍晶光束發射器／接收器的資料：每個世界裡所有光束方塊的位置（找連線用）。發射器運轉時每
 * {@link #BURN_INTERVAL} tick 灼傷光束上的生物 {@link #BURN_DAMAGE} 點，並在光束的終點冒出紫色火花。
 */
public class CharoiteBeamBlockEntity extends KineticBlockEntity implements SoulConductor.Relay {
    @Override
    public boolean sends() {
        return isEmitter();
    }

    @Override
    public boolean receives() {
        return !isEmitter();
    }

    /** 每跳一次扣的強度，以半級計（2 = 少 1 級）。 */
    @Override
    public int hopCost() {
        return 0;
    }

    public static final int BURN_INTERVAL = 20;
    public static final float BURN_DAMAGE = 2f;
    private static final Map<ResourceKey<Level>, Set<BlockPos>> BEAMS = new HashMap<>();

    public CharoiteBeamBlockEntity(BlockPos pos, BlockState state) {
        super(SoulPower.CHAROITE_BEAM_ENTITY, pos, state);
    }

    public boolean isEmitter() {
        return getBlockState().getBlock() instanceof CharoiteBeamBlock beam && beam.emitter;
    }

    public Direction facing() {
        return getBlockState().getValue(SoulMachineBlock.FACING);
    }

    /** 發射器：光束打中的接收器；接收器：光束打中自己的發射器。 */
    @Override
    public List<BlockPos> findLinks(ServerLevel level) {
        List<BlockPos> out = new ArrayList<>();
        if (isEmitter()) {
            BlockPos hit = CharoiteBeam.trace(level, worldPosition, facing()).receiver();
            if (hit != null) {
                out.add(hit);
            }
            return out;
        }
        for (BlockPos other : BEAMS.getOrDefault(level.dimension(), Set.of())) {
            if (other.closerThan(worldPosition, CharoiteBeam.RANGE + 1) && level.getBlockEntity(other) instanceof CharoiteBeamBlockEntity e
                    && e.isEmitter() && worldPosition.equals(CharoiteBeam.trace(level, other, e.facing()).receiver())) {
                out.add(other);
            }
        }
        return out;
    }

    /** 稜鏡或擋路的方塊變了：附近的光束各自重算網路。 */
    public static void refreshNear(ServerLevel level, BlockPos pos) {
        for (BlockPos p : List.copyOf(BEAMS.getOrDefault(level.dimension(), Set.of()))) {
            if (p.closerThan(pos, CharoiteBeam.RANGE + 1)) {
                SoulSignal.poll(level, p);
            }
        }
    }

    public static void serverTick(Level level, BlockPos pos, BlockState state, CharoiteBeamBlockEntity beam) {
        ServerLevel server = (ServerLevel) level;
        long now = level.getGameTime();
        if (now - beam.network.time() > SoulSignal.INTERVAL * 3L && now % SoulSignal.INTERVAL == 5) {
            beam.network = SoulSignal.Result.IDLE;
            SoulSignal.poll(server, pos);
        }
        if (!beam.isEmitter() || beam.speed == 0 || (now + pos.hashCode()) % BURN_INTERVAL != 0) {
            return;
        }
        CharoiteBeam.Trace trace = CharoiteBeam.trace(level, pos, beam.facing());
        for (CharoiteBeam.Segment seg : trace.segments()) {
            Vec3 a = Vec3.atCenterOf(seg.from());
            Vec3 b = a.add(Vec3.atLowerCornerOf(seg.dir().getUnitVec3i()).scale(seg.length()));
            for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, new AABB(a, b).inflate(0.2))) {
                e.hurtServer(server, server.damageSources().magic(), BURN_DAMAGE);
            }
            if (seg == trace.segments().getLast()) {
                server.sendParticles(ParticleTypes.WITCH, b.x, b.y, b.z, 3, 0.1, 0.1, 0.1, 0.02);
            }
        }
    }

    @Override
    public void setLevel(Level level) {
        super.setLevel(level);
        if (!level.isClientSide()) {
            BEAMS.computeIfAbsent(level.dimension(), k -> new HashSet<>()).add(worldPosition.immutable());
        }
    }

    @Override
    public void setRemoved() {
        super.setRemoved();
        if (level != null && !level.isClientSide()) {
            Set<BlockPos> set = BEAMS.get(level.dimension());
            if (set != null) {
                set.remove(worldPosition);
            }
        }
    }
}
