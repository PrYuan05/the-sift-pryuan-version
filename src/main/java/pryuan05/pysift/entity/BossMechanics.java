package pryuan05.pysift.entity;

import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerBossEvent;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.BossEvent;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.phys.Vec3;
import pryuan05.pysift.PySift;

import java.util.List;

/**
 * 三隻 Boss 共用的威脅機制（每隻 Boss 在 customServerAiStep 呼叫 {@link #tick}）：
 * <ul>
 *   <li>二階段（血量 &lt; 50%，只觸發一次）：怒吼、血條轉紅、攻擊 +30%、移速 +15%，並在身邊召喚援軍；
 *       技能冷卻倍率由各 Boss 的 skillCooldownScale 依 {@link #isPhaseTwo} 縮短。
 *       是否已進入二階段記在屬性修飾器上（隨存檔保存），重新載入後不會重複召喚。</li>
 *   <li>脫戰回血：沒有目標時每秒回復 2% 最大生命，避免被遠程慢慢磨死後拉開距離回補。</li>
 *   <li>守場：有競技場中心（{@link #setArena}）時，沒有目標且離中心超過 ARENA_LEASH 格就走回去。</li>
 *   <li>死亡演出（{@link #deathTick}）：屍體留 {@link #DEATH_TICKS} tick 播完 3 秒的 death 動畫，
 *       期間靈魂從身上逸散、倒地時揚起塵土、最後化成一團靈魂火消失。</li>
 * </ul>
 */
public final class BossMechanics {
    private static final AttributeModifier ENRAGED_DAMAGE = new AttributeModifier(PySift.id("boss_enraged_damage"), 0.30,
            AttributeModifier.Operation.ADD_MULTIPLIED_BASE);
    private static final AttributeModifier ENRAGED_SPEED = new AttributeModifier(PySift.id("boss_enraged_speed"), 0.15,
            AttributeModifier.Operation.ADD_MULTIPLIED_BASE);
    private static final double PHASE_TWO_HEALTH = 0.5;
    private static final int ARENA_LEASH = 20;
    /** 二階段的技能冷卻倍率。 */
    public static final double PHASE_TWO_COOLDOWN = 0.65;
    /** Boss 死亡演出長度（tick），要和各 Boss 的 animation.&lt;id&gt;.death（3.0 秒）一致。 */
    public static final int DEATH_TICKS = 60;

    private BossMechanics() {
    }

    /** 已經進入二階段（看攻擊力修飾器，存檔後仍然成立）。 */
    public static boolean isPhaseTwo(Mob boss) {
        AttributeInstance damage = boss.getAttribute(Attributes.ATTACK_DAMAGE);
        return damage != null && damage.hasModifier(ENRAGED_DAMAGE.id());
    }

    /** 競技場生成時呼叫：Boss 不會消失，並記住競技場中心。 */
    public static void setArena(Mob boss, BlockPos center) {
        boss.setPersistenceRequired();
        boss.setHomeTo(center, ARENA_LEASH);
    }

    /**
     * @param reinforcements 二階段召喚的援軍種類（每種一隻，可重複列出）
     */
    public static void tick(Mob boss, ServerLevel level, ServerBossEvent bar, List<EntityType<? extends Mob>> reinforcements) {
        bar.setProgress(boss.getHealth() / boss.getMaxHealth());
        if (!isPhaseTwo(boss) && boss.getHealth() < boss.getMaxHealth() * PHASE_TWO_HEALTH) {
            enterPhaseTwo(boss, level, bar, reinforcements);
        }
        if (boss.getTarget() == null && boss.tickCount % 20 == 0 && boss.getHealth() < boss.getMaxHealth()) {
            boss.heal(boss.getMaxHealth() * 0.02f);
        }
        if (boss.getTarget() == null && boss.hasHome() && !boss.isWithinHome() && boss.getNavigation().isDone()) {
            BlockPos home = boss.getHomePosition();
            boss.getNavigation().moveTo(home.getX() + 0.5, home.getY(), home.getZ() + 0.5, 1.0);
        }
    }

    /**
     * 死亡演出，每 tick 呼叫一次（各 Boss 的 onDeathTick）。
     * @param impactTick death 動畫中身體砸到地面的那一刻（tick），在這裡揚起塵土並播放落地聲
     */
    public static void deathTick(Mob boss, ServerLevel level, int deathTime, int impactTick) {
        double w = boss.getBbWidth() * 0.5;
        double h = boss.getBbHeight();
        if (deathTime == 1) {
            boss.playSound(SoundEvents.WITHER_DEATH, 1.5f, 1.6f);
            level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, boss.getX(), boss.getY(0.5), boss.getZ(), 40, w, h * 0.4, w, 0.08);
        }
        // 靈魂逸散：越接近消失越多
        int souls = 1 + deathTime * 4 / DEATH_TICKS;
        level.sendParticles(ParticleTypes.SOUL, boss.getX(), boss.getY(0.4), boss.getZ(), souls, w, h * 0.3, w, 0.03);
        if (deathTime % 10 == 0 && deathTime < impactTick) {
            boss.playSound(SoundEvents.SOUL_ESCAPE.value(), 2.0f, 0.6f);
        }
        if (deathTime == impactTick) {
            boss.playSound(SoundEvents.GENERIC_BIG_FALL, 2.5f, 0.6f);
            boss.playSound(SoundEvents.RAVAGER_STUNNED, 1.5f, 0.6f);
            level.sendParticles(ParticleTypes.CAMPFIRE_COSY_SMOKE, boss.getX(), boss.getY() + 0.2, boss.getZ(), 30, w * 1.4, 0.2, w * 1.4, 0.02);
            level.sendParticles(ParticleTypes.POOF, boss.getX(), boss.getY() + 0.3, boss.getZ(), 40, w * 1.6, 0.2, w * 1.6, 0.08);
        }
        if (deathTime == DEATH_TICKS - 2) {
            boss.playSound(SoundEvents.SOUL_ESCAPE.value(), 3.0f, 0.4f);
            level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, boss.getX(), boss.getY(0.3), boss.getZ(), 80, w, h * 0.3, w, 0.15);
            level.sendParticles(ParticleTypes.SCULK_SOUL, boss.getX(), boss.getY(0.3), boss.getZ(), 30, w, h * 0.3, w, 0.1);
        }
    }

    private static void enterPhaseTwo(Mob boss, ServerLevel level, ServerBossEvent bar, List<EntityType<? extends Mob>> reinforcements) {
        boss.getAttribute(Attributes.ATTACK_DAMAGE).addPermanentModifier(ENRAGED_DAMAGE);
        boss.getAttribute(Attributes.MOVEMENT_SPEED).addPermanentModifier(ENRAGED_SPEED);
        bar.setColor(BossEvent.BossBarColor.RED);
        boss.addEffect(new MobEffectInstance(MobEffects.RESISTANCE, 60, 2, false, false));
        boss.playSound(SoundEvents.ENDER_DRAGON_GROWL, 3.0f, 0.7f);
        level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, boss.getX(), boss.getY(0.5), boss.getZ(), 60,
                boss.getBbWidth() * 0.6, boss.getBbHeight() * 0.4, boss.getBbWidth() * 0.6, 0.05);
        for (int i = 0; i < reinforcements.size(); i++) {
            Mob minion = reinforcements.get(i).create(level, EntitySpawnReason.MOB_SUMMONED);
            if (minion == null) {
                continue;
            }
            double angle = Math.PI * 2 * i / reinforcements.size();
            double r = boss.getBbWidth() * 0.5 + 2.5;
            Vec3 at = boss.position().add(Math.cos(angle) * r, 0.5, Math.sin(angle) * r);
            minion.snapTo(at, boss.getYRot(), 0);
            minion.setTarget(boss.getTarget());
            level.addFreshEntity(minion);
            level.sendParticles(ParticleTypes.SCULK_SOUL, at.x, at.y + 0.5, at.z, 12, 0.4, 0.6, 0.4, 0.02);
        }
    }
}
