package pryuan05.pysift.entity.mob;

import java.util.Optional;
import java.util.UUID;
import net.minecraft.ChatFormatting;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.UUIDUtil;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.util.Unit;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.ai.memory.MemoryModuleType;
import net.minecraft.world.entity.ai.memory.WalkTarget;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.monster.warden.Warden;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;

/**
 * 隙浮守衛（MODDING_ROADMAP §4.7 第六幕）：治癒後的監守者，長回了赤紅的毛，不再挨餓、不再暴怒。
 * <ul>
 *   <li>沿用原版監守者的模型、動作與大腦，只是永遠不會生氣、不會鎖定目標、不會放黑暗（{@link pryuan05.pysift.entity.WardenSoothing}
 *       與 WardenMixin），也不會鑽回地底（一直刷新 DIG_COOLDOWN）。</li>
 *   <li>餵它迴音碎片：開始跟著你走；再餵一次就留在原地等。</li>
 *   <li>來源：監守者泡在靈液裡或待在隙浮夠久（{@link pryuan05.pysift.entity.WardenCure}）。</li>
 * </ul>
 * 貼圖：tools/models/build_sift_warden.py；用戶端 SiftWardenRenderer。
 */
public class SiftWardenEntity extends Warden {
    private static final double FOLLOW_FAR = 6.0;
    private UUID owner;
    private boolean following;

    public SiftWardenEntity(EntityType<? extends Monster> type, Level level) {
        super(type, level);
    }

    @Override
    public void tick() {
        super.tick();
        if (!(this.level() instanceof ServerLevel level)) {
            return;
        }
        // 不鑽回地底：監守者沒事做 1200 tick 後會挖地消失
        this.getBrain().setMemoryWithExpiry(MemoryModuleType.DIG_COOLDOWN, Unit.INSTANCE, 1200L);
        if (following && owner != null && this.tickCount % 10 == 0) {
            Player p = level.getPlayerByUUID(owner);
            if (p != null && p.level() == level && !p.isSpectator() && this.distanceTo(p) > FOLLOW_FAR) {
                this.getBrain().setMemory(MemoryModuleType.WALK_TARGET, new WalkTarget(p, 1.0f, 3));
            }
        }
        if (this.tickCount % 60 == 0 && this.random.nextInt(2) == 0) {
            level.sendParticles(ParticleTypes.GLOW, this.getX(), this.getY() + 2.2, this.getZ(), 2, 0.5, 0.4, 0.5, 0.01);
        }
    }

    @Override
    protected InteractionResult mobInteract(Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (!stack.is(Items.ECHO_SHARD)) {
            return super.mobInteract(player, hand);
        }
        if (this.level() instanceof ServerLevel level) {
            stack.consume(1, player);
            if (following && player.getUUID().equals(owner)) {
                following = false;
                this.getBrain().eraseMemory(MemoryModuleType.WALK_TARGET);
                player.sendOverlayMessage(Component.translatable("message.pysift.sift_warden.stay").withStyle(ChatFormatting.LIGHT_PURPLE));
            } else {
                owner = player.getUUID();
                following = true;
                player.sendOverlayMessage(Component.translatable("message.pysift.sift_warden.follow").withStyle(ChatFormatting.LIGHT_PURPLE));
            }
            this.playSound(SoundEvents.AMETHYST_BLOCK_CHIME, 1.5f, 0.6f);
            level.sendParticles(ParticleTypes.HEART, this.getX(), this.getY() + this.getBbHeight() + 0.3, this.getZ(), 3, 0.5, 0.2, 0.5, 0);
        }
        return InteractionResult.SUCCESS;
    }

    @Override
    protected SoundEvent getAmbientSound() {
        return SoundEvents.WARDEN_LISTENING;   // 只會低聲咕嚕，不會哀嚎
    }

    @Override
    public float getVoicePitch() {
        return super.getVoicePitch() * 1.25f;
    }

    @Override
    public void checkDespawn() {
        // 不會因為和平難度或距離而消失
    }

    @Override
    public boolean removeWhenFarAway(double distance) {
        return false;
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        output.putBoolean("Following", following);
        if (owner != null) {
            output.store("Owner", UUIDUtil.CODEC, owner);
        }
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        following = input.getBooleanOr("Following", false);
        Optional<UUID> o = input.read("Owner", UUIDUtil.CODEC);
        owner = o.orElse(null);
    }
}
