package pryuan05.pysift.soulpower;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.EntityBlock;
import net.minecraft.world.level.block.RotatedPillarBlock;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;

/**
 * 靈魂齒輪箱（Create 的 gearbox）：四片傘齒輪裝在軸向（AXIS）四周的四個側面上，從任何一面輸入的轉動都傳到另外三面，
 * 所以動力可以轉 90°。四面的軸「由外往內看」都朝同一個方向轉：換成各自 +軸 的轉速，就是正方向那一面 ×1、
 * 負方向那一面 ×-1（{@link #transfer}）——對面的軸反轉，旁邊的軸轉 90°。
 * 會轉的傘齒輪與軸頭由 client/soulpower/SoulPowerRenderer 畫出來。
 */
public class SoulGearboxBlock extends RotatedPillarBlock implements SoulKinetic, EntityBlock {
    public SoulGearboxBlock(Properties properties) {
        super(properties);
        registerDefaultState(defaultBlockState().setValue(POWERED, false));
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        super.createBlockStateDefinition(builder);
        builder.add(POWERED);
    }

    @Override
    public boolean connects(BlockState state, Direction side) {
        return side.getAxis() != state.getValue(AXIS);
    }

    /** The box's own speed is "seen from outside, looking in" on every face; per face's +axis that is ±1. */
    @Override
    public float transfer(BlockState state, Direction side) {
        return side.getAxisDirection() == Direction.AxisDirection.POSITIVE ? 1f : -1f;
    }

    @Override
    public Direction.Axis axis(BlockState state) {
        return state.getValue(AXIS);
    }

    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new KineticBlockEntity(pos, state);
    }

    @Override
    protected void onPlace(BlockState state, Level level, BlockPos pos, BlockState oldState, boolean movedByPiston) {
        super.onPlace(state, level, pos, oldState, movedByPiston);
        if (level instanceof ServerLevel server && !oldState.is(this)) {
            SoulNetwork.update(server, pos);
        }
    }

    @Override
    protected void affectNeighborsAfterRemoval(BlockState state, ServerLevel level, BlockPos pos, boolean movedByPiston) {
        super.affectNeighborsAfterRemoval(state, level, pos, movedByPiston);
        if (!level.getBlockState(pos).is(this)) {
            SoulNetwork.updateAround(level, pos);
        }
    }
}
