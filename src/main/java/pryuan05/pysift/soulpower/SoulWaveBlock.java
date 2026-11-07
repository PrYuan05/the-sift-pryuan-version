package pryuan05.pysift.soulpower;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityTicker;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;
import pryuan05.pysift.block.RitualDiscs;

/**
 * 靈魂振波發送器／接收器：背面接傳動；放一張共鳴唱片（{@link RitualDiscs} 的 8 張之一）當頻率，
 * 同頻率、{@link SoulWaveBlockEntity#RANGE} 格內、中間沒有隔絕振動的方塊（羊毛類）就無線連通。
 * 拿唱片右鍵放入（換掉舊的），空手右鍵取出。
 */
public class SoulWaveBlock extends SoulMachineBlock {
    public final boolean emitter;

    public SoulWaveBlock(boolean emitter, Properties properties) {
        super(true, properties);
        this.emitter = emitter;
    }

    @Override
    public boolean connects(BlockState state, Direction side) {
        return side == state.getValue(FACING).getOpposite();
    }

    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new SoulWaveBlockEntity(pos, state);
    }

    @Override
    public <T extends BlockEntity> BlockEntityTicker<T> getTicker(Level level, BlockState state, BlockEntityType<T> type) {
        return level.isClientSide() ? null : createTickerHelper(type, SoulPower.SOUL_WAVE_ENTITY, SoulWaveBlockEntity::serverTick);
    }

    @Override
    protected InteractionResult useItemOn(ItemStack stack, BlockState state, Level level, BlockPos pos, Player player,
                                          InteractionHand hand, BlockHitResult hit) {
        if (RitualDiscs.of(stack) == null) {
            return InteractionResult.TRY_WITH_EMPTY_HAND;
        }
        if (level instanceof ServerLevel server && level.getBlockEntity(pos) instanceof SoulWaveBlockEntity wave) {
            ItemStack old = wave.getDisc();
            wave.setDisc(stack.copyWithCount(1));
            if (!player.getAbilities().instabuild) {
                stack.shrink(1);
            }
            if (!old.isEmpty() && !player.addItem(old)) {
                net.minecraft.world.Containers.dropItemStack(level, pos.getX() + 0.5, pos.getY() + 1.0, pos.getZ() + 0.5, old);
            }
            level.playSound(null, pos, SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.BLOCKS, 1.0f, RitualDiscs.of(wave.getDisc()).pitch());
            player.sendOverlayMessage(Component.translatable("message.pysift.soul_wave.frequency", Component.translatable(RitualDiscs.songKey(RitualDiscs.of(wave.getDisc())))));
            SoulNetwork.update(server, pos);
        }
        return InteractionResult.SUCCESS;
    }

    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
        if (level instanceof ServerLevel server && level.getBlockEntity(pos) instanceof SoulWaveBlockEntity wave) {
            ItemStack old = wave.getDisc();
            if (old.isEmpty()) {
                player.sendOverlayMessage(Component.translatable("message.pysift.soul_wave.empty"));
                return InteractionResult.SUCCESS;
            }
            wave.setDisc(ItemStack.EMPTY);
            if (!player.addItem(old)) {
                net.minecraft.world.Containers.dropItemStack(level, pos.getX() + 0.5, pos.getY() + 1.0, pos.getZ() + 0.5, old);
            }
            SoulNetwork.update(server, pos);
        }
        return InteractionResult.SUCCESS;
    }
}
