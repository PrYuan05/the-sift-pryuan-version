package pryuan05.pysift.soulpower;

import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.tags.BlockTags;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * 靈脈節點的資料：每個世界裡所有節點的位置。連線條件：{@link #RANGE} 格內，兩點之間的每一格都是岩石
 * （主世界與地獄的基岩石、深板岩、靈脈石）。運轉時每 {@link #GROW_INTERVAL} tick，連線路徑上的一格岩石長成靈脈石，
 * 並沿著路徑冒出靈魂粒子。
 */
public class SoulVeinNodeBlockEntity extends KineticBlockEntity {
    public static final int RANGE = 16;
    public static final int GROW_INTERVAL = 100;
    private static final Map<ResourceKey<Level>, Set<BlockPos>> NODES = new HashMap<>();
    private List<BlockPos> links = List.of();

    public SoulVeinNodeBlockEntity(BlockPos pos, BlockState state) {
        super(SoulPower.SOUL_VEIN_NODE_ENTITY, pos, state);
    }

    public static boolean isRock(BlockState state) {
        return state.is(BlockTags.BASE_STONE_OVERWORLD) || state.is(BlockTags.BASE_STONE_NETHER)
                || state.is(SoulPower.SOUL_VEINED_STONE);
    }

    public List<BlockPos> findLinks(ServerLevel level) {
        List<BlockPos> out = new ArrayList<>();
        for (BlockPos other : NODES.getOrDefault(level.dimension(), Set.of())) {
            if (!other.equals(worldPosition) && other.closerThan(worldPosition, RANGE + 0.5)
                    && level.getBlockEntity(other) instanceof SoulVeinNodeBlockEntity && path(level, worldPosition, other) != null) {
                out.add(other);
            }
        }
        links = out;
        return out;
    }

    /** 兩點之間的每一格（不含兩端）；有一格不是岩石就回傳 null。 */
    static List<BlockPos> path(Level level, BlockPos from, BlockPos to) {
        Vec3 a = Vec3.atCenterOf(from), b = Vec3.atCenterOf(to);
        int steps = (int) Math.ceil(a.distanceTo(b) * 2);
        List<BlockPos> cells = new ArrayList<>();
        for (int i = 1; i < steps; i++) {
            BlockPos p = BlockPos.containing(a.lerp(b, (double) i / steps));
            if (p.equals(from) || p.equals(to) || cells.contains(p)) {
                continue;
            }
            if (!isRock(level.getBlockState(p))) {
                return null;
            }
            cells.add(p);
        }
        return cells;
    }

    public static void serverTick(Level level, BlockPos pos, BlockState state, SoulVeinNodeBlockEntity node) {
        ServerLevel server = (ServerLevel) level;
        long now = level.getGameTime();
        if (now - node.network.time() > SoulNetwork.INTERVAL * 3L && now % SoulNetwork.INTERVAL == 5) {
            node.network = SoulNetwork.Result.IDLE;
            SoulNetwork.update(server, pos);
        }
        if (node.speed == 0 || node.links.isEmpty()) {
            return;
        }
        for (BlockPos link : node.links) {
            if (link.asLong() < pos.asLong()) {
                continue;   // each link is handled by one of its two ends
            }
            List<BlockPos> cells = path(level, pos, link);
            if (cells == null || cells.isEmpty()) {
                continue;
            }
            if ((now + pos.hashCode()) % 20 == 0) {
                BlockPos p = cells.get(level.getRandom().nextInt(cells.size()));
                server.sendParticles(ParticleTypes.SCULK_SOUL, p.getX() + 0.5, p.getY() + 0.5, p.getZ() + 0.5, 1, 0.4, 0.4, 0.4, 0.0);
            }
            if ((now + pos.hashCode()) % GROW_INTERVAL == 0) {
                for (BlockPos p : cells) {   // the vein grows from this end towards the other
                    if (!level.getBlockState(p).is(SoulPower.SOUL_VEINED_STONE)) {
                        level.setBlock(p, SoulPower.SOUL_VEINED_STONE.defaultBlockState(), Block.UPDATE_ALL);
                        server.sendParticles(ParticleTypes.SOUL, p.getX() + 0.5, p.getY() + 0.5, p.getZ() + 0.5, 4, 0.3, 0.3, 0.3, 0.01);
                        break;
                    }
                }
            }
        }
    }

    @Override
    public void setLevel(Level level) {
        super.setLevel(level);
        if (!level.isClientSide()) {
            NODES.computeIfAbsent(level.dimension(), k -> new HashSet<>()).add(worldPosition.immutable());
        }
    }

    @Override
    public void setRemoved() {
        super.setRemoved();
        if (level != null && !level.isClientSide()) {
            Set<BlockPos> set = NODES.get(level.dimension());
            if (set != null) {
                set.remove(worldPosition);
            }
        }
    }
}
