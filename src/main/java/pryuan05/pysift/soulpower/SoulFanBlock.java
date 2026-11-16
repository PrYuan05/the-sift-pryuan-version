package pryuan05.pysift.soulpower;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityTicker;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockState;

/**
 * 靈魂風扇（Create 的 encased fan）：背面接傳動，正面吹出氣流；轉向反過來就變成吸。氣流穿過靈魂火（或靈魂營火）時，
 * 後面的掉落物會被「靈魂薰染」（pysift:soul_haunting：沙 → 靈魂沙、泥土 → 靈魂土、火把 → 靈魂火把…）。
 */
public class SoulFanBlock extends SoulMachineBlock {
    public SoulFanBlock(Properties properties) {
        super(true, properties);
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
    public float impact(BlockState state) {
        return 1f;
    }

    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new SoulFanBlockEntity(pos, state);
    }

    @Override
    public <T extends BlockEntity> BlockEntityTicker<T> getTicker(Level level, BlockState state, BlockEntityType<T> type) {
        return level.isClientSide() ? null : createTickerHelper(type, SoulPower.SOUL_FAN_ENTITY, SoulFanBlockEntity::serverTick);
    }
}
