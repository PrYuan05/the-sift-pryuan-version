package pryuan05.pysift.soulpower;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.LevelReader;
import net.minecraft.world.level.ScheduledTickAccess;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.PipeBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BooleanProperty;
import net.minecraft.util.RandomSource;

/**
 * 靈液管：自動接上相鄰的靈液管、靈液泵（背面）與靈液引擎。靈液泵把靈液沿著管子送到引擎；
 * 只接了一頭、另一頭空著的管子是<b>漏口</b>：送不出去的靈液會從那裡漏出來，弄髒地面（{@link SpiritPumpBlockEntity}）。
 */
public class SpiritPipeBlock extends Block {

    public SpiritPipeBlock(Properties properties) {
        super(properties);
        BlockState s = stateDefinition.any();
        for (BooleanProperty p : PipeBlock.PROPERTY_BY_DIRECTION.values()) {
            s = s.setValue(p, false);
        }
        registerDefaultState(s);
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        builder.add(PipeBlock.NORTH, PipeBlock.EAST, PipeBlock.SOUTH, PipeBlock.WEST, PipeBlock.UP, PipeBlock.DOWN);
    }

    /** 這一面接得上什麼：管子、泵的背面、引擎（任何一面）。 */
    public static boolean accepts(BlockGetter level, BlockPos pos, Direction from) {
        BlockState state = level.getBlockState(pos);
        if (state.getBlock() instanceof SpiritPipeBlock || state.getBlock() instanceof SpiritEngineBlock) {
            return true;
        }
        return state.getBlock() instanceof SpiritPumpBlock && state.getValue(SoulMachineBlock.FACING).getOpposite() == from.getOpposite();
    }

    private BlockState connect(BlockGetter level, BlockPos pos, BlockState state) {
        for (Direction d : Direction.values()) {
            state = state.setValue(PipeBlock.PROPERTY_BY_DIRECTION.get(d), accepts(level, pos.relative(d), d));
        }
        return state;
    }

    @Override
    public BlockState getStateForPlacement(BlockPlaceContext context) {
        return connect(context.getLevel(), context.getClickedPos(), defaultBlockState());
    }

    @Override
    protected BlockState updateShape(BlockState state, LevelReader level, ScheduledTickAccess ticks, BlockPos pos, Direction dir,
                                     BlockPos neighborPos, BlockState neighbor, RandomSource random) {
        return state.setValue(PipeBlock.PROPERTY_BY_DIRECTION.get(dir), accepts(level, neighborPos, dir));
    }

}
