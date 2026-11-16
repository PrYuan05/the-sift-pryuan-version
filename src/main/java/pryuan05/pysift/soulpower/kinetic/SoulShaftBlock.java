package pryuan05.pysift.soulpower.kinetic;

import pryuan05.pysift.soulpower.*;

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
 * 靈魂傳動軸：沿著自己的軸向（AXIS）兩端傳動。方塊模型是空的，整根軸由用戶端的渲染器依轉速轉動著畫出來
 * （client/soulpower/SoulPowerRenderer，部件模型 models/block/soul_power_parts/）。
 * 齒輪（{@link SoulCogBlock}）與靈壓計（{@link SoulGaugeBlock}）也從這裡延伸。
 */
public class SoulShaftBlock extends RotatedPillarBlock implements SoulKinetic, EntityBlock {

    public SoulShaftBlock(Properties properties) {
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
        return side.getAxis() == state.getValue(AXIS);
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
