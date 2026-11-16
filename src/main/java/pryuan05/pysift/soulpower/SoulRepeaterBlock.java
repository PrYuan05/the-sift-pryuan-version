package pryuan05.pysift.soulpower;

import net.minecraft.core.Direction;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Mirror;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.block.state.properties.BooleanProperty;
import net.minecraft.world.level.block.state.properties.EnumProperty;

/**
 * 靈魂中繼器：有方向。訊號從背面進來、從正面（FACING）出去，出去時補回強度 15（靈魂訊號與原版訊號都補）。
 * 傳靈魂訊號時吃 {@link #LOAD} SP。訊號不會倒著走，所以也能當二極體用。
 */
public class SoulRepeaterBlock extends SoulPartBlock {
    public static final EnumProperty<Direction> FACING = BlockStateProperties.FACING;
    public static final BooleanProperty POWERED = BlockStateProperties.POWERED;
    public static final float LOAD = 16f;

    public SoulRepeaterBlock(Properties properties) {
        super(properties);
        registerDefaultState(stateDefinition.any().setValue(FACING, Direction.NORTH).setValue(POWERED, false));
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        builder.add(FACING, POWERED);
    }

    /** 訊號往玩家看的方向走。 */
    @Override
    public BlockState getStateForPlacement(BlockPlaceContext context) {
        return defaultBlockState().setValue(FACING, context.getNearestLookingDirection());
    }

    @Override
    protected BlockState rotate(BlockState state, Rotation rotation) {
        return state.setValue(FACING, rotation.rotate(state.getValue(FACING)));
    }

    @Override
    protected BlockState mirror(BlockState state, Mirror mirror) {
        return state.rotate(mirror.getRotation(state.getValue(FACING)));
    }

    @Override
    public boolean conducts(BlockState state, Direction side) {
        return side.getAxis() == state.getValue(FACING).getAxis();
    }

    @Override
    public boolean accepts(BlockState state, Direction side) {
        return side == state.getValue(FACING).getOpposite();
    }

    @Override
    public boolean emits(BlockState state, Direction side) {
        return side == state.getValue(FACING);
    }

    @Override
    public boolean boosts(BlockState state) {
        return true;
    }

    @Override
    public float load(BlockState state) {
        return LOAD;
    }
}
