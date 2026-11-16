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

/**
 * 靈魂淨化篩（故事：「用隙浮的工藝把腐爛的幽匿篩回赤紅幽匿」）：側面的曲柄輪轉動，帶著篩網前後搖晃。
 * 轉動時慢慢把 {@link SoulSifterBlockEntity#RANGE} 格內的藍色幽匿變回赤紅幽匿；篩網上也能放東西篩
 * （pysift:soul_sifting：幽匿 → 赤紅幽匿、礫石 → 燧石…）。每 1 RPM 吃 3 SP。
 */
public class SoulSifterBlock extends SoulMachineBlock {
    public SoulSifterBlock(Properties properties) {
        super(false, properties);
    }

    @Override
    public boolean connects(BlockState state, Direction side) {
        return side.getAxis() == axis(state);
    }

    /** 曲柄輪的軸：正面的右手邊（和引擎的飛輪一樣）。 */
    @Override
    public Direction.Axis axis(BlockState state) {
        return state.getValue(FACING).getClockWise().getAxis();
    }

    @Override
    public float impact(BlockState state) {
        return 3f;
    }

    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new SoulSifterBlockEntity(pos, state);
    }

    @Override
    public <T extends BlockEntity> BlockEntityTicker<T> getTicker(Level level, BlockState state, BlockEntityType<T> type) {
        return level.isClientSide() ? null : createTickerHelper(type, SoulPower.SOUL_SIFTER_ENTITY, SoulGrinderBlockEntity::serverTick);
    }

    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
        if (!level.isClientSide()) {
            player.openMenu(state.getMenuProvider(level, pos));
        }
        return InteractionResult.SUCCESS;
    }
}
