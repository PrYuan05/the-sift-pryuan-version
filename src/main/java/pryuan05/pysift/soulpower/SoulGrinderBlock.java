package pryuan05.pysift.soulpower;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityTicker;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;

/** 靈魂研磨機：每一面都接得上傳動，滿載 64 SP。 */
public class SoulGrinderBlock extends SoulMachineBlock {
    public SoulGrinderBlock(Properties properties) {
        super(false, properties);
    }

    @Override
    public boolean connects(BlockState state, Direction side) {
        return true;
    }

    /** 石磨繞垂直軸轉。 */
    @Override
    public Direction.Axis axis(BlockState state) {
        return Direction.Axis.Y;
    }

    /** 每 1 RPM 吃 2 SP（32 RPM = 64 SP，一台引擎帶得動 4 台）。 */
    @Override
    public float impact(BlockState state) {
        return 2f;
    }

    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new SoulGrinderBlockEntity(pos, state);
    }

    @Override
    public <T extends BlockEntity> BlockEntityTicker<T> getTicker(Level level, BlockState state, BlockEntityType<T> type) {
        return level.isClientSide() ? null : createTickerHelper(type, SoulPower.SOUL_GRINDER_ENTITY, SoulGrinderBlockEntity::serverTick);
    }

    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
        if (!level.isClientSide()) {
            player.openMenu(state.getMenuProvider(level, pos));
        }
        return InteractionResult.SUCCESS;
    }
}
