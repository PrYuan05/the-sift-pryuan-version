package pryuan05.pysift.soulpower;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.RandomSource;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.LevelReader;
import net.minecraft.world.level.ScheduledTickAccess;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.PipeBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.block.state.properties.BooleanProperty;
import net.minecraft.world.level.block.state.properties.IntegerProperty;
import net.minecraft.world.level.redstone.Orientation;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.Shapes;
import net.minecraft.world.phys.shapes.VoxelShape;
import pryuan05.pysift.block.AutoConnect;

/**
 * 靈魂導線：一段活的赤紅幽匿脈，把歌聲（靈魂訊號）傳到遠處；也是原版紅石線的進階版。六個方向都能接（可以垂直、懸空、貼牆），訊號每 2 格才少 1 級，
 * 而且能帶著引擎的靈壓去推動靈魂機器（{@link SoulCircuit}）。
 * <ul>
 *   <li>POWER：對外的紅石強度。對原版元件來說它就是訊號源：紅石粉會接上來，紅石燈、活塞、中繼器都吃得到。</li>
 *   <li>CHARGED：這段導線上有沒有靈魂訊號。有：赤紅發光（活的幽匿脈，歌聲在裡面流）；
 *       只有原版訊號：深藍微亮（沒有靈魂，和主世界枯死的幽匿同色）；沒有訊號：暗灰。</li>
 * </ul>
 * 原版元件（拉桿、中繼器、比較器、紅石火把、紅石塊…）貼著導線就能把訊號送進來；紅石粉不行（見 SoulCircuit）。
 */
public class SoulConduitBlock extends Block implements SoulConductor, AutoConnect.Connecting {
    public static final IntegerProperty POWER = BlockStateProperties.POWER;
    public static final BooleanProperty CHARGED = BooleanProperty.create("charged");
    private static final VoxelShape CORE = Block.box(6, 6, 6, 10, 10, 10);
    private static final VoxelShape[] ARMS = new VoxelShape[6];
    private final VoxelShape[] shapes = new VoxelShape[64];

    static {
        for (Direction d : Direction.values()) {
            ARMS[d.ordinal()] = switch (d) {
                case DOWN -> Block.box(6, 0, 6, 10, 6, 10);
                case UP -> Block.box(6, 10, 6, 10, 16, 10);
                case NORTH -> Block.box(6, 6, 0, 10, 10, 6);
                case SOUTH -> Block.box(6, 6, 10, 10, 10, 16);
                case WEST -> Block.box(0, 6, 6, 6, 10, 10);
                case EAST -> Block.box(10, 6, 6, 16, 10, 10);
            };
        }
    }

    public SoulConduitBlock(Properties properties) {
        super(properties);
        BlockState s = stateDefinition.any().setValue(POWER, 0).setValue(CHARGED, false);
        for (BooleanProperty p : PipeBlock.PROPERTY_BY_DIRECTION.values()) {
            s = s.setValue(p, false);
        }
        registerDefaultState(s);
        for (int mask = 0; mask < 64; mask++) {
            VoxelShape shape = CORE;
            for (Direction d : Direction.values()) {
                if ((mask & 1 << d.ordinal()) != 0) {
                    shape = Shapes.or(shape, ARMS[d.ordinal()]);
                }
            }
            shapes[mask] = shape;
        }
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        builder.add(PipeBlock.NORTH, PipeBlock.EAST, PipeBlock.SOUTH, PipeBlock.WEST, PipeBlock.UP, PipeBlock.DOWN, POWER, CHARGED);
    }

    /** 接得上：相鄰的靈魂元件（在那一面導通），或原版的紅石訊號源（紅石粉、拉桿、中繼器…）。 */
    private static boolean joins(BlockGetter level, BlockPos neighbor, Direction towards) {
        BlockState ns = level.getBlockState(neighbor);
        if (ns.getBlock() instanceof SoulConductor other) {
            return other.conducts(ns, towards.getOpposite());
        }
        return ns.isSignalSource();
    }

    @Override
    public BlockState getStateForPlacement(BlockPlaceContext context) {
        BlockState state = defaultBlockState();
        for (Direction d : Direction.values()) {
            state = state.setValue(PipeBlock.PROPERTY_BY_DIRECTION.get(d), joins(context.getLevel(), context.getClickedPos().relative(d), d));
        }
        return state;
    }

    @Override
    protected BlockState updateShape(BlockState state, LevelReader level, ScheduledTickAccess ticks, BlockPos pos, Direction dir,
                                     BlockPos neighborPos, BlockState neighbor, RandomSource random) {
        return state.setValue(PipeBlock.PROPERTY_BY_DIRECTION.get(dir), joins(level, neighborPos, dir));
    }

    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        int mask = 0;
        for (Direction d : Direction.values()) {
            if (state.getValue(PipeBlock.PROPERTY_BY_DIRECTION.get(d))) {
                mask |= 1 << d.ordinal();
            }
        }
        return shapes[mask];
    }

    // ---------------------------------------------------------------- 原版紅石：這是一個訊號源
    @Override
    protected boolean isSignalSource(BlockState state) {
        return true;
    }

    @Override
    protected int getSignal(BlockState state, BlockGetter level, BlockPos pos, Direction direction) {
        return state.getValue(POWER);
    }

    // ---------------------------------------------------------------- 迴路
    @Override
    protected void onPlace(BlockState state, Level level, BlockPos pos, BlockState oldState, boolean movedByPiston) {
        super.onPlace(state, level, pos, oldState, movedByPiston);
        if (level instanceof ServerLevel server && !oldState.is(this)) {
            SoulSignal.update(server, pos);
        }
    }

    @Override
    protected void affectNeighborsAfterRemoval(BlockState state, ServerLevel level, BlockPos pos, boolean movedByPiston) {
        super.affectNeighborsAfterRemoval(state, level, pos, movedByPiston);
        if (!level.getBlockState(pos).is(this)) {
            level.updateNeighborsAt(pos, this, null);
            SoulSignal.updateAround(level, pos);
        }
    }

    /** 旁邊的原版元件變了（拉桿扳動、中繼器輸出改變）：下一個 tick 重算，同一個 tick 的多次通知只算一次。 */
    @Override
    protected void neighborChanged(BlockState state, Level level, BlockPos pos, Block block, Orientation orientation, boolean movedByPiston) {
        if (level instanceof ServerLevel server) {
            for (Direction d : Direction.values()) {
                BlockState ns = level.getBlockState(pos.relative(d));
                if (ns.is(Blocks.SCULK_CATALYST) && ns.getValue(BlockStateProperties.BLOOM)) {
                    SoulCircuit.charge(server, pos);    // 生物死在催化體旁：放出來的靈魂流進導線
                }
            }
            if (!level.getBlockTicks().hasScheduledTick(pos, this)) {
                level.scheduleTick(pos, this, 1);
            }
        }
    }

    @Override
    protected void tick(BlockState state, ServerLevel level, BlockPos pos, RandomSource random) {
        SoulSignal.poll(level, pos);
        if (SoulCircuit.charged(level, pos)) {
            level.scheduleTick(pos, this, SoulSignal.INTERVAL);     // 催化體的靈魂用完之前定期重算，時間到就熄掉
        } else if (state.getValue(CHARGED) && level.getBlockState(pos).is(this)) {
            SoulSignal.update(level, pos);
        }
    }
}
