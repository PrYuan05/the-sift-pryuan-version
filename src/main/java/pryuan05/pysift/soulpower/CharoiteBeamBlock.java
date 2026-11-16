package pryuan05.pysift.soulpower;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityTicker;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockState;

/**
 * 紫龍晶光束發射器／接收器：背面接傳動。發射器運轉時從正面射出紫龍晶光束（{@link CharoiteBeam}），
 * 打中接收器的正面就無線連通（靈魂訊號不損耗，比振波好，但要瞄準）。
 * 光束會灼傷穿過它的生物。
 */
public class CharoiteBeamBlock extends SoulMachineBlock {
    public final boolean emitter;

    public CharoiteBeamBlock(boolean emitter, Properties properties) {
        super(true, properties);
        this.emitter = emitter;
    }

    @Override
    public boolean connects(BlockState state, Direction side) {
        return side == state.getValue(FACING).getOpposite();
    }

    @Override
    public Direction.Axis axis(BlockState state) {
        return state.getValue(FACING).getAxis();
    }

    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new CharoiteBeamBlockEntity(pos, state);
    }

    @Override
    public <T extends BlockEntity> BlockEntityTicker<T> getTicker(Level level, BlockState state, BlockEntityType<T> type) {
        return level.isClientSide() ? null : createTickerHelper(type, SoulPower.CHAROITE_BEAM_ENTITY, CharoiteBeamBlockEntity::serverTick);
    }
}
