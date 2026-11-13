package pryuan05.pysift.soulpower;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.Level;
import pryuan05.pysift.fluid.ModFluids;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityTicker;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockState;

/**
 * 靈液泵：正面伸進靈液池（吸走正前方的靈液源頭），背面把靈液送進靈液管；側面的曲柄輪接動力，每 1 RPM 吃 2 SP。
 * 轉越快抽越快（32 RPM 時每 2 秒一桶）。
 */
public class SpiritPumpBlock extends SoulMachineBlock {
    public SpiritPumpBlock(Properties properties) {
        super(true, properties);
    }

    /**
     * 吸口（FACING）對著靈液：旁邊有靈液源頭就對著它（先看玩家面對的方向），沒有的話對著玩家看的方向。
     * 其他機器是正面朝玩家；泵照那樣放的話吸口會背對靈液池，轉了也抽不到。
     */
    @Override
    public BlockState getStateForPlacement(BlockPlaceContext context) {
        for (Direction d : context.getNearestLookingDirections()) {
            if (context.getLevel().getFluidState(context.getClickedPos().relative(d)).isSourceOfType(ModFluids.SPIRIT_LIQUID)) {
                return defaultBlockState().setValue(FACING, d);
            }
        }
        return defaultBlockState().setValue(FACING, context.getNearestLookingDirection());
    }

    @Override
    public boolean connects(BlockState state, Direction side) {
        return side.getAxis() == axis(state);
    }

    /** 曲柄輪的軸：和朝向垂直（朝上下時用 X 軸，朝水平方向時用它的右手邊）。 */
    @Override
    public Direction.Axis axis(BlockState state) {
        Direction f = state.getValue(FACING);
        return f.getAxis() == Direction.Axis.Y ? Direction.Axis.X : f.getClockWise().getAxis();
    }

    @Override
    public float impact(BlockState state) {
        return 2f;
    }

    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new SpiritPumpBlockEntity(pos, state);
    }

    @Override
    public <T extends BlockEntity> BlockEntityTicker<T> getTicker(Level level, BlockState state, BlockEntityType<T> type) {
        return level.isClientSide() ? null : createTickerHelper(type, SoulPower.SPIRIT_PUMP_ENTITY, SpiritPumpBlockEntity::serverTick);
    }
}
