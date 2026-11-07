package pryuan05.pysift.soulpower;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BooleanProperty;
import net.minecraft.world.level.redstone.Orientation;

/**
 * 靈魂離合器／靈魂換向器（Create 的 clutch / gearshift）：外殼裡是兩段傳動軸。收到紅石訊號（SHIFTED）時：
 * <ul>
 *   <li>離合器：分開，正方向那一頭不再被帶動（{@link #connects} 只接負方向那一頭）；</li>
 *   <li>換向器：正方向那一頭反轉（{@link #transfer} = -1）。</li>
 * </ul>
 * 頂上的指示燈亮起表示通電。
 */
public class SoulShiftBlock extends SoulShaftBlock {
    public static final BooleanProperty SHIFTED = BooleanProperty.create("shifted");
    public final boolean gearshift;

    public SoulShiftBlock(boolean gearshift, Properties properties) {
        super(properties);
        this.gearshift = gearshift;
        registerDefaultState(defaultBlockState().setValue(SHIFTED, false));
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        super.createBlockStateDefinition(builder);
        builder.add(SHIFTED);
    }

    @Override
    public BlockState getStateForPlacement(BlockPlaceContext context) {
        BlockState s = super.getStateForPlacement(context);
        return s == null ? null : s.setValue(SHIFTED, context.getLevel().hasNeighborSignal(context.getClickedPos()));
    }

    @Override
    public boolean connects(BlockState state, Direction side) {
        if (side.getAxis() != state.getValue(AXIS)) {
            return false;
        }
        return gearshift || !state.getValue(SHIFTED) || side.getAxisDirection() == Direction.AxisDirection.NEGATIVE;
    }

    @Override
    public float transfer(BlockState state, Direction side) {
        return gearshift && state.getValue(SHIFTED) && side.getAxisDirection() == Direction.AxisDirection.POSITIVE ? -1f : 1f;
    }

    @Override
    protected void neighborChanged(BlockState state, Level level, BlockPos pos, Block block, Orientation orientation, boolean movedByPiston) {
        boolean signal = level.hasNeighborSignal(pos);
        if (signal != state.getValue(SHIFTED) && level instanceof ServerLevel server) {
            server.setBlock(pos, state.setValue(SHIFTED, signal), Block.UPDATE_ALL);
            SoulNetwork.updateAround(server, pos);
            SoulNetwork.update(server, pos);
        }
    }
}
