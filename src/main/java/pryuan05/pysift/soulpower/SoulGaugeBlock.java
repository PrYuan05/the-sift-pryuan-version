package pryuan05.pysift.soulpower;

import pryuan05.pysift.soulpower.kinetic.SoulShaftBlock;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.network.chat.Component;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;

/**
 * 靈壓計（Create 的應力計＋轉速計）：一段傳動軸外面包著錶盒，軸四周的四面錶盤上，指針平滑擺到負載比例
 * （超過 100% 進紅區、指針發抖）。右鍵在動作列顯示轉速、容量與負載；比較器輸出負載比例（0～15）。
 */
public class SoulGaugeBlock extends SoulShaftBlock implements SoulConductor {
    @Override
    public boolean conducts(BlockState state, Direction side) {
        return connects(state, side);
    }


    public SoulGaugeBlock(Properties properties) {
        super(properties);
    }

    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new Entity(pos, state);
    }

    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
        if (!level.isClientSide() && level.getBlockEntity(pos) instanceof KineticBlockEntity gauge) {
            SoulSignal.Result n = gauge.network();
            Component status;
            if (n.conflict()) {
                status = Component.translatable("message.pysift.soul_gauge.conflict").withStyle(ChatFormatting.RED);
            } else if (n.overloaded()) {
                status = Component.translatable("message.pysift.soul_gauge.overloaded", n.stress(), n.capacity()).withStyle(ChatFormatting.RED);
            } else {
                status = Component.translatable("message.pysift.soul_gauge.status", gauge.strength(),
                        n.stress(), n.capacity(), Math.round(n.load() * 100));
            }
            player.sendOverlayMessage(status);
        }
        return InteractionResult.SUCCESS;
    }

    @Override
    protected boolean hasAnalogOutputSignal(BlockState state) {
        return true;
    }

    @Override
    protected int getAnalogOutputSignal(BlockState state, Level level, BlockPos pos, Direction direction) {
        if (level.getBlockEntity(pos) instanceof KineticBlockEntity gauge && gauge.network().capacity() > 0) {
            return Math.min(15, Math.round(gauge.network().load() * 15));
        }
        return 0;
    }

    /** 和傳動軸一樣，只是負載改變時通知比較器。 */
    public static class Entity extends KineticBlockEntity {
        private int signal = -1;

        public Entity(BlockPos pos, BlockState state) {
            super(SoulPower.SOUL_GAUGE_ENTITY, pos, state);
        }

        @Override
        protected void onState(SoulSignal.Result result, float speed) {
            int s = result.capacity() > 0 ? Math.min(15, Math.round(result.load() * 15)) : 0;
            if (s != signal && level != null) {
                signal = s;
                level.updateNeighbourForOutputSignal(worldPosition, getBlockState().getBlock());
            }
        }
    }
}
