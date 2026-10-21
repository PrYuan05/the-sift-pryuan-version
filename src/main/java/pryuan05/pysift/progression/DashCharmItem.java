package pryuan05.pysift.progression;

import net.minecraft.core.component.DataComponents;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ClientboundSetEntityMotionPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.decoration.Mannequin;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.component.ResolvableProfile;
import net.minecraft.world.item.component.TooltipDisplay;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import java.util.function.Consumer;

/**
 * 衝刺護符（君王王冠製成）：右鍵朝視線方向衝刺，連續可衝 2 次（覺醒 3 次，且衝刺路徑上的敵人受到 5 點傷害）。
 * 每一輪衝刺的起點會留下你的分身（{@link Mannequin}，顯示你的外觀）10 秒，附近正在追你的怪物會改追分身。
 * 一輪用完或 1.5 秒內沒有接著衝，進入 4 秒冷卻。
 */
public class DashCharmItem extends Item {
    private static final int CHAIN_WINDOW = 30;
    private static final int COOLDOWN = 80;
    private static final int DECOY_TICKS = 200;
    private static final double SPEED = 2.2;     // about 8-9 blocks on the ground
    private static final double LIFT = 0.35;

    private record Chain(int used, long lastDash) {
    }

    private static final Map<UUID, Chain> CHAINS = new HashMap<>();

    public DashCharmItem(Properties properties) {
        super(properties);
    }

    @Override
    public InteractionResult use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (player.getCooldowns().isOnCooldown(stack)) {
            return InteractionResult.PASS;
        }
        // The player's movement is client-side: apply the dash on BOTH sides (like riptide / wind charges),
        // and also send the motion from the server so nothing is lost if the client was out of sync.
        Vec3 look = player.getLookAngle();
        Vec3 flat = new Vec3(look.x, 0, look.z);
        flat = flat.lengthSqr() < 1.0E-4 ? Vec3.directionFromRotation(0, player.getYRot()) : flat.normalize();
        player.setDeltaMovement(flat.x * SPEED, LIFT, flat.z * SPEED);
        player.fallDistance = 0;
        if (!(level instanceof ServerLevel server)) {
            return InteractionResult.SUCCESS;
        }
        if (player instanceof ServerPlayer serverPlayer) {
            serverPlayer.connection.send(new ClientboundSetEntityMotionPacket(player));
        }
        boolean awakened = BossWeapons.isAwakened(stack);
        int max = awakened ? 3 : 2;
        long now = server.getGameTime();
        Chain chain = CHAINS.get(player.getUUID());
        if (chain == null || now - chain.lastDash() > CHAIN_WINDOW) {
            chain = new Chain(0, now);
            BossWeapons.spawnDecoy(server, player, DECOY_TICKS);   // a new chain leaves a decoy where it started
        }
        server.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, player.getX(), player.getY(0.5), player.getZ(), 15, 0.3, 0.5, 0.3, 0.05);
        server.playSound(null, player.blockPosition(), SoundEvents.BREEZE_JUMP, SoundSource.PLAYERS, 1.0f, 1.3f);
        if (awakened) {
            Vec3 ahead = player.position().add(flat.scale(3));
            for (LivingEntity e : server.getEntitiesOfClass(LivingEntity.class, player.getBoundingBox().expandTowards(flat.scale(5)).inflate(0.8),
                    e -> BossWeapons.isFoe(player, e))) {
                e.hurtServer(server, server.damageSources().playerAttack(player), 5.0f);
            }
            server.sendParticles(ParticleTypes.SWEEP_ATTACK, ahead.x, player.getY(0.5), ahead.z, 1, 0, 0, 0, 0);
        }
        int used = chain.used() + 1;
        if (used >= max) {
            CHAINS.remove(player.getUUID());
            player.getCooldowns().addCooldown(stack, COOLDOWN);
        } else {
            CHAINS.put(player.getUUID(), new Chain(used, now));
        }
        stack.hurtAndBreak(1, player, hand == InteractionHand.MAIN_HAND ? EquipmentSlot.MAINHAND : EquipmentSlot.OFFHAND);
        return InteractionResult.SUCCESS_SERVER;
    }

    @Override
    public boolean isFoil(ItemStack stack) {
        return BossWeapons.isAwakened(stack) || super.isFoil(stack);
    }

    @Override
    public void appendHoverText(ItemStack stack, TooltipContext context, TooltipDisplay display, Consumer<Component> out, TooltipFlag flag) {
        boolean awakened = BossWeapons.isAwakened(stack);
        out.accept(Component.translatable(awakened ? "tooltip.pysift.dash_charm.use_awakened" : "tooltip.pysift.dash_charm.use"));
        out.accept(Component.translatable("tooltip.pysift.dash_charm.decoy"));
        if (awakened) {
            out.accept(Component.translatable("tooltip.pysift.awakened"));
        } else {
            out.accept(Component.translatable("tooltip.pysift.dash_charm.how_to_awaken").withStyle(net.minecraft.ChatFormatting.DARK_GRAY));
        }
    }
}
