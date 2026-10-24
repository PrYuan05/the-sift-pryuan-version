package pryuan05.pysift.block;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.RandomSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.LevelReader;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.EntityBlock;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;
import pryuan05.pysift.block.entity.ResonantJukeboxBlockEntity;

/**
 * 共鳴唱片盒：由歌者召喚的迴音傀儡擺在傳送門框架前（不能合成）。
 * 手持儀式唱片（{@link RitualDiscs}）右鍵放入：由左到右第 i 個只收第 i 張（紅橙黃綠藍靛紫粉）；放滿 8 張就開門（{@link SiftPortalRitual}）。
 * 還沒放唱片時，會射出一道很淡、很細的光柱，提示這裡要哪個顏色。
 * 方塊本身不畫模型，交給 ResonantJukeboxRenderer 畫（才能做「從地面升起」、唱片旋轉與彩色光柱）。
 * 打破時只掉出唱片，不掉唱片盒；同時關閉這組儀式開的傳送門。
 */
public class ResonantJukeboxBlock extends Block implements EntityBlock {
    public ResonantJukeboxBlock(Properties properties) {
        super(properties);
    }

    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new ResonantJukeboxBlockEntity(pos, state);
    }

    @Override
    protected RenderShape getRenderShape(BlockState state) {
        return RenderShape.INVISIBLE;
    }

    @Override
    protected ItemStack getCloneItemStack(LevelReader level, BlockPos pos, BlockState state, boolean includeData) {
        return ItemStack.EMPTY;
    }

    @Override
    protected InteractionResult useItemOn(ItemStack stack, BlockState state, Level level, BlockPos pos, Player player,
                                          InteractionHand hand, BlockHitResult hit) {
        if (!(level.getBlockEntity(pos) instanceof ResonantJukeboxBlockEntity box)) {
            return InteractionResult.TRY_WITH_EMPTY_HAND;
        }
        RitualDiscs.Disc disc = RitualDiscs.of(stack);
        if (!box.getDisc().isEmpty()) {
            return InteractionResult.TRY_WITH_EMPTY_HAND;
        }
        RitualDiscs.Disc wanted = box.expectedDisc();
        if (disc == null || (wanted != null && disc != wanted)) {
            if (stack.has(net.minecraft.core.component.DataComponents.JUKEBOX_PLAYABLE) && !level.isClientSide()) {
                player.sendOverlayMessage(wanted == null
                        ? Component.translatable("message.pysift.ritual.wrong_disc").withStyle(ChatFormatting.LIGHT_PURPLE)
                        : Component.translatable("message.pysift.ritual.wants", Component.translatable(RitualDiscs.songKey(wanted)))
                                .withStyle(net.minecraft.network.chat.Style.EMPTY.withColor(wanted.color() & 0xFFFFFF)));
            }
            return InteractionResult.TRY_WITH_EMPTY_HAND;
        }
        if (!(level instanceof ServerLevel server)) {
            return InteractionResult.SUCCESS;
        }
        if (SiftPortalRitual.discUsed(server, box, disc)) {
            player.sendOverlayMessage(Component.translatable("message.pysift.ritual.disc_used").withStyle(ChatFormatting.LIGHT_PURPLE));
            return InteractionResult.FAIL;
        }
        box.setDisc(stack);
        stack.consume(1, player);
        server.playSound(null, pos, SoundEvents.NOTE_BLOCK_CHIME.value(), SoundSource.RECORDS, 2.0f, disc.pitch());
        server.playSound(null, pos, SoundEvents.NOTE_BLOCK_BELL.value(), SoundSource.RECORDS, 1.5f, disc.pitch());
        server.playSound(null, pos, SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.RECORDS, 1.0f, disc.pitch());
        server.sendParticles(ParticleTypes.NOTE, pos.getX() + 0.5, pos.getY() + 1.3, pos.getZ() + 0.5, 6, 0.3, 0.2, 0.3, disc.semitone() / 24.0);
        server.sendParticles(new DustParticleOptions(disc.color() & 0xFFFFFF, 1.5f), pos.getX() + 0.5, pos.getY() + 1.2, pos.getZ() + 0.5,
                20, 0.3, 0.5, 0.3, 0.0);
        SiftPortalRitual.onDiscInserted(server, box, player);
        return InteractionResult.SUCCESS_SERVER;
    }

    @Override
    public void animateTick(BlockState state, Level level, BlockPos pos, RandomSource random) {
        if (random.nextInt(4) == 0 && level.getBlockEntity(pos) instanceof ResonantJukeboxBlockEntity box && box.getRitualDisc() != null) {
            level.addParticle(ParticleTypes.NOTE, pos.getX() + 0.5, pos.getY() + 1.2, pos.getZ() + 0.5,
                    box.getRitualDisc().semitone() / 24.0, 0.0, 0.0);
        }
    }
}
