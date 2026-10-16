package pryuan05.pysift.effect;

import net.minecraft.core.Holder;
import net.minecraft.core.Registry;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.effect.MobEffectCategory;
import pryuan05.pysift.PySift;

public final class ModEffects {
    /**
     * 靈魂剝奪：碰到靈液時獲得（原本的「靈魂火灼燒」已併入）。
     * <ul>
     *   <li>視野變成伏聆（SoulDeprivationVision），身上燒靈魂火（用戶端 mixin），血量愛心換成靈魂火愛心（HudMixin）。</li>
     *   <li>玩家：血量抽到 0.2 倍、抽離期間再受傷會靈魂碎裂、喝靈魂解藥解除，規則見 {@link SoulBurn}。</li>
     * </ul>
     */
    public static final Holder<MobEffect> SOUL_DEPRIVATION = Registry.registerForHolder(
            BuiltInRegistries.MOB_EFFECT, PySift.id("soul_deprivation"), new SoulDeprivationEffect());

    private ModEffects() {
    }

    /** 身體周圍持續冒出靈魂火焰與伏聆靈魂（伺服器端送出，所有人都看得到）。 */
    private static final class SoulDeprivationEffect extends MobEffect {
        private SoulDeprivationEffect() {
            super(MobEffectCategory.HARMFUL, 0x29DFEB);
        }

        @Override
        public boolean shouldApplyEffectTickThisTick(int duration, int amplifier) {
            return duration % 4 == 0;
        }

        @Override
        public boolean applyEffectTick(ServerLevel level, LivingEntity entity, int amplifier) {
            double w = entity.getBbWidth() * 0.6, h = entity.getBbHeight();
            level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, entity.getX(), entity.getY() + h * 0.5, entity.getZ(), 3, w, h * 0.35, w, 0.01);
            if (entity.getRandom().nextInt(3) == 0) {
                level.sendParticles(ParticleTypes.SCULK_SOUL, entity.getX(), entity.getY() + h * 0.7, entity.getZ(), 1, w, h * 0.2, w, 0.02);
            }
            return true;
        }
    }

    public static void registerModEffects() {
        PySift.LOGGER.info("Registering Mob Effects for {}", PySift.MOD_ID);
    }
}
