package pryuan05.pysift.soulpower;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.BaseEntityBlock;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityTicker;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;

/**
 * 靈脈節點（第三種無線傳動，地下傳導）：六面都能接傳動。兩個節點之間只要整條路都是岩石
 * （{@link SoulVeinNodeBlockEntity#isRock}），{@link SoulVeinNodeBlockEntity#RANGE} 格內就連通——振波要空氣、光束要瞄準，
 * 靈脈則穿過實心的岩層，適合埋在地底的機器。運轉時，路上的岩石會慢慢長出發光的靈脈（靈脈石）。
 */
public class SoulVeinNodeBlock extends BaseEntityBlock implements SoulKinetic, SoulConductor {
    @Override
    public boolean conducts(BlockState state, Direction side) {
        return connects(state, side);
    }

    public SoulVeinNodeBlock(Properties properties) {
        super(properties);
        registerDefaultState(stateDefinition.any().setValue(POWERED, false));
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        builder.add(POWERED);
    }

    @Override
    public boolean connects(BlockState state, Direction side) {
        return true;
    }

    @Override
    public Direction.Axis axis(BlockState state) {
        return Direction.Axis.Y;   // 只給渲染器轉晶核用
    }

    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new SoulVeinNodeBlockEntity(pos, state);
    }

    @Override
    public <T extends BlockEntity> BlockEntityTicker<T> getTicker(Level level, BlockState state, BlockEntityType<T> type) {
        return level.isClientSide() ? null : createTickerHelper(type, SoulPower.SOUL_VEIN_NODE_ENTITY, SoulVeinNodeBlockEntity::serverTick);
    }

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
            SoulSignal.updateAround(level, pos);
        }
    }
}
