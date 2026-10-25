package pryuan05.pysift.effect;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentSyncPredicate;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;
import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.fabricmc.fabric.api.entity.event.v1.ServerPlayerEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import pryuan05.pysift.PySift;
import pryuan05.pysift.progression.SoulWard;

/**
 * 靈魂剝奪（碰到靈液時的懲罰，原「靈魂火灼燒」已併入）與靈魂解藥的規則。只作用在玩家身上。
 * <ul>
 *   <li><b>點燃</b>（{@link #ignite}）：沒有靈魂剝奪時才觸發：給 {@link ModEffects#SOUL_DEPRIVATION} {@value #DURATION} tick；
 *       生存／冒險模式再記下目前血量，並把血量抽到原本的 0.2 倍（至少 1）。創造模式只有外觀效果。</li>
 *   <li><b>靈魂碎裂</b>：抽離期間（還沒喝解藥）再受到任何傷害，被抽走的 80% 血量徹底消散，
 *       最大生命值以 −0.8（ADD_MULTIPLIED_TOTAL）鎖成 0.2 倍，血量補滿到這個新上限後才承受這次傷害。</li>
 *   <li><b>抽離期間</b>：飢餓值的自然回血被擋下（FoodDataMixin）。</li>
 *   <li><b>喝下靈魂解藥</b>（{@link #cure}）：移除灼燒與上限鎖定；沒有碎裂就把血量還回點燃前的數值，碎裂則拿不回來。</li>
 *   <li><b>灼燒自然結束</b>（沒喝解藥）：被抽走的血不會還；上限鎖定（若已碎裂）一直保留到喝解藥或死亡。</li>
 *   <li>水、雨都澆不熄，只能等時間結束或喝解藥。</li>
 * </ul>
 * 身上的靈魂火外觀由用戶端依同步的 {@link #FIRE} 附件繪製（EntityRendererMixin、FlameFeatureRendererMixin、
 * ScreenEffectRendererMixin），所以其他玩家也看得到。
 */
public final class SoulBurn {
    public static final int DURATION = 400;
    private static final Identifier SHATTER_MODIFIER = PySift.id("soul_shatter");

    /** 伺服器端紀錄：點燃前的血量、是否正處於抽離、是否已碎裂。存進存檔，死亡後重置。 */
    public record State(float preHealth, boolean drained, boolean shattered) {
        public static final State NONE = new State(0, false, false);
        public static final Codec<State> CODEC = RecordCodecBuilder.create(i -> i.group(
                Codec.FLOAT.fieldOf("pre_health").forGetter(State::preHealth),
                Codec.BOOL.fieldOf("drained").forGetter(State::drained),
                Codec.BOOL.fieldOf("shattered").forGetter(State::shattered)
        ).apply(i, State::new));
    }

    public static final AttachmentType<State> STATE = AttachmentRegistry.create(PySift.id("soul_burn_state"),
            builder -> builder.persistent(State.CODEC).initializer(() -> State.NONE));
    /** 身上是否在燒靈魂火：同步給所有看得到這個玩家的用戶端（用來畫火焰）。 */
    public static final AttachmentType<Boolean> FIRE = AttachmentRegistry.create(PySift.id("soul_fire"),
            builder -> builder.persistent(Codec.BOOL).initializer(() -> false)
                    .syncWith(ByteBufCodecs.BOOL, AttachmentSyncPredicate.all()));

    private SoulBurn() {
    }

    public static State state(ServerPlayer player) {
        return player.getAttachedOrElse(STATE, State.NONE);
    }

    /** 碰到靈液。 */
    public static void ignite(ServerPlayer player) {
        if (player.hasEffect(ModEffects.SOUL_DEPRIVATION) || player.isSpectator() || SoulWard.isImmune(player)) {
            return;
        }
        player.addEffect(new MobEffectInstance(ModEffects.SOUL_DEPRIVATION, DURATION, 0));
        player.setAttached(FIRE, true);
        State s = state(player);
        if (!s.drained() && !player.isCreative()) {
            float pre = player.getHealth();
            player.setHealth(Math.max(1.0f, pre * SoulWard.drainRatio(player)));   // 0.2，隙浮金套裝 0.5
            player.setAttached(STATE, new State(pre, true, false));
            play(player, SoundEvents.SOUL_ESCAPE.value(), 1.0f);
            play(player, SoundEvents.GENERIC_BURN, 0.8f);
        }
    }

    /** 抽離期間再受傷：靈魂碎裂。在傷害套用之前呼叫（ALLOW_DAMAGE）。 */
    private static void shatter(ServerPlayer player, State s) {
        player.setAttached(STATE, new State(s.preHealth(), true, true));
        AttributeInstance maxHealth = player.getAttribute(Attributes.MAX_HEALTH);
        if (maxHealth != null && !maxHealth.hasModifier(SHATTER_MODIFIER)) {
            maxHealth.addPermanentModifier(new AttributeModifier(SHATTER_MODIFIER, -0.8, AttributeModifier.Operation.ADD_MULTIPLIED_TOTAL));
        }
        player.setHealth(player.getMaxHealth());          // 以鎖定後的完整上限承受這次傷害
        play(player, SoundEvents.RESPAWN_ANCHOR_DEPLETE.value(), 1.0f);
    }

    /** 喝下靈魂解藥。 */
    public static void cure(ServerPlayer player) {
        State s = state(player);
        player.removeEffect(ModEffects.SOUL_DEPRIVATION);
        removeShatterLock(player);
        if (s.drained() && !s.shattered()) {
            player.setHealth(Math.min(player.getMaxHealth(), s.preHealth()));
        }
        player.setAttached(STATE, State.NONE);
        player.setAttached(FIRE, false);
        play(player, SoundEvents.BEACON_POWER_SELECT, 1.0f);
        if (player.level() instanceof ServerLevel level) {
            level.sendParticles(ParticleTypes.TOTEM_OF_UNDYING, player.getX(), player.getY() + 1.0, player.getZ(), 40, 0.4, 0.6, 0.4, 0.4);
        }
    }

    /** 自然回血是否被擋下（FoodDataMixin）。 */
    public static boolean regenBlocked(ServerPlayer player) {
        return state(player).drained() && player.hasEffect(ModEffects.SOUL_DEPRIVATION);
    }

    private static void removeShatterLock(ServerPlayer player) {
        AttributeInstance maxHealth = player.getAttribute(Attributes.MAX_HEALTH);
        if (maxHealth != null) {
            maxHealth.removeModifier(SHATTER_MODIFIER);
        }
        if (player.getHealth() > player.getMaxHealth()) {
            player.setHealth(player.getMaxHealth());
        }
    }

    private static void play(ServerPlayer player, SoundEvent sound, float volume) {
        player.level().playSound(null, player.getX(), player.getY(), player.getZ(), sound, SoundSource.PLAYERS, volume, 1.0f);
    }

    public static void register() {
        ServerLivingEntityEvents.ALLOW_DAMAGE.register((entity, source, amount) -> {
            if (entity instanceof ServerPlayer player && player.hasEffect(ModEffects.SOUL_DEPRIVATION)) {
                State s = state(player);
                if (s.drained() && !s.shattered()) {
                    shatter(player, s);
                }
            }
            return true;
        });
        // 同步火焰外觀；灼燒自然結束時結束抽離（血不還，碎裂的上限鎖定保留到喝解藥）
        ServerTickEvents.END_SERVER_TICK.register(server -> {
            for (ServerPlayer player : server.getPlayerList().getPlayers()) {
                boolean burning = player.hasEffect(ModEffects.SOUL_DEPRIVATION);
                if (player.getAttachedOrElse(FIRE, false) != burning) {
                    player.setAttached(FIRE, burning);
                }
                State s = state(player);
                if (!burning && s.drained() && !s.shattered()) {
                    player.setAttached(STATE, State.NONE);
                }
            }
        });
        // 死亡重生：狀態與上限鎖定都清掉
        ServerPlayerEvents.AFTER_RESPAWN.register((oldPlayer, newPlayer, alive) -> {
            removeShatterLock(newPlayer);
            newPlayer.setAttached(STATE, State.NONE);
            newPlayer.setAttached(FIRE, false);
        });
        PySift.LOGGER.info("Registered soul burn rules");
    }
}
