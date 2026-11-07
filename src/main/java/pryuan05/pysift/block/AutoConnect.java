package pryuan05.pysift.block;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.CrossCollisionBlock;
import net.minecraft.world.level.block.StairBlock;
import net.minecraft.world.level.block.WallBlock;
import net.minecraft.world.level.block.state.BlockState;
import pryuan05.pysift.PySift;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Automatic neighbour detection for pysift blocks whose state stores what they connect to: walls, fences, glass panes
 * and bars (CrossCollisionBlock), stairs (inner / outer corners) and spirit pipes ({@link Connecting}).
 * <p>
 * Vanilla only sets those connections when a player places the block (getStateForPlacement) or when a neighbour's
 * shape changes (updateShape); blocks put down by /setblock, /fill, structures, WorldEdit or Axiom stay unconnected.
 * mixin/AutoConnectMixin calls {@link #placed} after BlockState.onPlace and {@link #changed} after
 * handleNeighborChanged, which recompute every direction through the block's own updateShape (vanilla's
 * Block.updateFromNeighbourShapes), for the block and for the connecting blocks around it.
 */
public final class AutoConnect {
    /** Marks a pysift block with its own connection logic (in updateShape) as connecting. */
    public interface Connecting {
    }

    private static final Map<Block, Boolean> CONNECTING = new ConcurrentHashMap<>();

    private AutoConnect() {
    }

    public static boolean isConnecting(Block block) {
        return CONNECTING.computeIfAbsent(block, b -> {
            if (!(b instanceof Connecting || b instanceof WallBlock || b instanceof CrossCollisionBlock || b instanceof StairBlock)) {
                return false;
            }
            return PySift.MOD_ID.equals(BuiltInRegistries.BLOCK.getKey(b).getNamespace());
        });
    }

    /** The block was put into the world, by any means: connect it and the connecting blocks around it. */
    public static void placed(Level level, BlockPos pos) {
        if (level instanceof ServerLevel server) {
            refresh(server, pos);
            for (Direction d : Direction.values()) {
                BlockPos n = pos.relative(d);
                if (isConnecting(server.getBlockState(n).getBlock())) {
                    refresh(server, n);
                }
            }
        }
    }

    /** A neighbour changed (this also fires for /setblock and structures): recheck this block's connections. */
    public static void changed(Level level, BlockPos pos) {
        if (level instanceof ServerLevel server) {
            refresh(server, pos);
        }
    }

    private static void refresh(ServerLevel level, BlockPos pos) {
        BlockState state = level.getBlockState(pos);
        BlockState connected = Block.updateFromNeighbourShapes(state, level, pos);
        if (connected != state) {
            level.setBlock(pos, connected, Block.UPDATE_CLIENTS);
        }
    }
}
