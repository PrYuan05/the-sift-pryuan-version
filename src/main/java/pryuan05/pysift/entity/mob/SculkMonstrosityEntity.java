package pryuan05.pysift.entity.mob;

import java.util.List;
import java.util.UUID;
import net.minecraft.network.chat.Component;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.phys.Vec3;
import pryuan05.pysift.entity.ai.SkillGoal;
import pryuan05.pysift.entity.ai.SoulChargeGoal;
import pryuan05.pysift.entity.projectile.SculkCubeEntity;
import net.minecraft.server.level.ServerBossEvent;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.BossEvent;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.animal.golem.IronGolem;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.AABB;
import pryuan05.pysift.entity.BossMechanics;
import pryuan05.pysift.entity.ModEntities;
import pryuan05.pysift.entity.PysiftMonsterEntity;
import pryuan05.pysift.entity.ai.GroundSlamGoal;
import pryuan05.pysift.entity.ai.SonicBeamGoal;

/**
 * 幽匿巨怪（Boss，400 HP）。
 * <ul>
 *   <li>體型：原版 SCALE 屬性 1.8 倍（模型含肩上靈魂火約 9 格高，碰撞箱 5.8 × 7.7 格）；以下距離與半徑都是基礎值，半徑／貼身類距離實際乘上 SCALE，遠程最大距離乘上 RANGE_SCALE（1.75）。</li>
 *   <li>目標：玩家優先，其次鐵魔像；被攻擊會反擊。</li>
 *   <li>近戰：左右連擊，右手、左手輪流（動畫 attack / attack_left）。</li>
 *   <li>扭身橫掃：貼身（4.5×SCALE 格內）時扭身蓄力 0.8 秒，左臂橫掃前方約 200°，12 點傷害並甩飛，冷卻 6 秒（動畫 swipe）。</li>
 *   <li>幽匿方塊彈幕：目標在 6 格外且有視線，張臂咆哮 1.5 秒後彈出 5 個幽匿方塊，落地後滾向最近的玩家，撞到 7 點傷害，冷卻 13 秒（動畫 cube_barrage）。</li>
 *   <li>幽匿觸媒召喚：繃緊雙臂 1.2 秒，目標周圍冒出 3 個幽匿觸媒並長出脈絡；6 秒內沒被挖掉就爆開（半徑 4 格 10 點傷害，每個替 Boss 回 5% 生命）。場上有觸媒時不再召喚，冷卻 21 秒（動畫 catalyst）。</li>
 *   <li>砸地：目標在 6 格內，前搖 1 秒，半徑 5 格 12 點傷害並往上擊飛，冷卻 8 秒（動畫 slam）。</li>
 *   <li>音波：目標在 6~20 格且有視線，蓄力 1.7 秒，無視護甲 10 點傷害並擊退，冷卻 10 秒
 *       （動畫 sonic_charge → sonic_release）。</li>
 *   <li>靈魂火衝撞＋重拳：目標在 8~24 格時蓄力 1 秒（動畫 charge），全身靈魂火直線衝刺最多 1.2 秒，撞到 18 點傷害並大幅撞飛；
 *       停下後右拳點燃，0.7 秒後揮出重拳（動畫 mega_punch）：前方 4×SCALE 格 16 點傷害、擊飛、靈魂剝奪與 4 秒火焰。冷卻 11 秒。</li>
 *   <li>二階段（血量 &lt; 50%）：每 5 秒對 20 格內的玩家施加黑暗。</li>
 *   <li>出場時吼叫（動畫 roar），死亡時播放 death。</li>
 *   <li>威脅機制（BossMechanics）：二階段攻擊 +30%、移速 +15%、冷卻 ×0.65，並召喚 2 隻潛伏獵手；脫戰回血、守在競技場。</li>
 * </ul>
 */
public class SculkMonstrosityEntity extends PysiftMonsterEntity {
    /** 體型倍率（原版 SCALE 屬性）；貼身／範圍類距離乘上它。 */
    private static final double SCALE = 1.8;
    /** 遠程最大距離的倍率（比體型小，避免射程過遠）。 */
    private static final double RANGE_SCALE = 1.75;
    private final ServerBossEvent bossEvent = (ServerBossEvent) new ServerBossEvent(
            UUID.randomUUID(),
            Component.literal("Sculk Monstrosity"),
            BossEvent.BossBarColor.BLUE,
            BossEvent.BossBarOverlay.NOTCHED_10
    ).setDarkenScreen(true);
    private boolean roared;
    private int combo;
    private final SculkCatalystField catalysts = new SculkCatalystField(this);

    public SculkMonstrosityEntity(EntityType<? extends PysiftMonsterEntity> entityType, Level level) {
        super(entityType, level);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return PysiftMonsterEntity.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 520.0)
                .add(Attributes.MOVEMENT_SPEED, 0.25)
                .add(Attributes.ATTACK_DAMAGE, 18.0)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.ARMOR, 12.0)
                .add(Attributes.SCALE, SCALE)
                .add(Attributes.STEP_HEIGHT, 2.5)
                .add(Attributes.FOLLOW_RANGE, 48.0);
    }

    @Override
    protected void registerGoals() {
        super.registerGoals();
        // 技能優先於一般近戰（MeleeAttackGoal 為 2）；兩者都佔用 MOVE / LOOK，所以施放時會中斷追擊
        this.goalSelector.addGoal(1, new GroundSlamGoal(this, "slam", 19, 28, 160, 6.0 * SCALE, 5.0 * SCALE, 12.0f, 0.7));
        this.goalSelector.addGoal(1, new SonicBeamGoal(this, "sonic_charge", "sonic_release", 34, 46, 200, 6.0 * SCALE, 20.0 * RANGE_SCALE, 10.0f));
        // 靈魂火衝撞：目標在 8~24 格時蓄力 1 秒後直線衝刺（最多 1.2 秒，全身靈魂火），撞到 18 點傷害並大幅撞飛；
        // 停下後右拳點燃揮出重拳（動畫 mega_punch），前方 4×SCALE 格 16 點傷害＋靈魂剝奪＋火焰，冷卻 11 秒
        this.goalSelector.addGoal(1, new SoulChargeGoal(this, "charge", "mega_punch", 20, 24, 32, 220, 8.0, 24.0, 0.9, 18.0f, 2.2,
                4.0 * SCALE, 16.0f));
        // 扭身橫掃：貼身時扭身蓄力，左臂橫掃前方 200°，把人甩飛
        this.goalSelector.addGoal(1, new SkillGoal(this, "swipe", 16, 26, 120, 0.0, 4.5 * SCALE, false, this::swipe));
        // 幽匿方塊彈幕：張開雙臂咆哮，彈出 5 個會滾向玩家的幽匿方塊
        this.goalSelector.addGoal(1, new SkillGoal(this, "cube_barrage", 30, 50, 260, 6.0, 20.0 * RANGE_SCALE, true, this::cubeBarrage));
        // 幽匿觸媒召喚：繃緊雙臂，場上冒出 3 個觸媒（場上還有觸媒時不再召喚）
        this.goalSelector.addGoal(1, new SkillGoal(this, "catalyst", 24, 40, 420, 0.0, 30.0, false, this::summonCatalysts) {
            @Override
            public boolean canUse() {
                return !catalysts.isActive() && super.canUse();
            }
        });
        this.targetSelector.addGoal(3, new NearestAttackableTargetGoal<>(this, IronGolem.class, true));
    }

    @Override
    protected List<String> skillAnimations() {
        return List.of("attack", "attack_left", "slam", "sonic_charge", "sonic_release", "roar", "charge", "mega_punch",
                "swipe", "cube_barrage", "catalyst");
    }

    @Override
    protected boolean hasDeathAnimation() {
        return true;
    }

    /** 3 秒死亡演出：仰天怒吼、跪倒、撐地，最後側身倒下（2.2 秒落地），眼睛與肩上火焰熄滅。 */
    @Override
    public int deathDuration() {
        return BossMechanics.DEATH_TICKS;
    }

    @Override
    protected void onDeathTick(ServerLevel level) {
        if (deathDuration() > 20) {
            BossMechanics.deathTick(this, level, this.deathTime, 44);
        }
    }

    // ------------------------------------------------------------------ skills
    private void swipe(ServerLevel level, LivingEntity target) {
        Vec3 fwd = Vec3.directionFromRotation(0, this.getYRot());
        double r = 4.5 * SCALE;
        this.playSound(SoundEvents.PLAYER_ATTACK_SWEEP, 2.0f, 0.5f);
        level.sendParticles(ParticleTypes.SWEEP_ATTACK, this.getX() + fwd.x * r * 0.6, this.getY(0.4), this.getZ() + fwd.z * r * 0.6,
                3, r * 0.3, 0.2, r * 0.3, 0);
        for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, this.getBoundingBox().inflate(r),
                e -> e != this && e.isAlive() && !(e instanceof Enemy))) {
            Vec3 to = e.position().subtract(this.position()).multiply(1, 0, 1);
            if (to.lengthSqr() > 1.0E-4 && fwd.dot(to.normalize()) < -0.17) {
                continue;   // 正後方打不到（約 200° 扇形）
            }
            if (e.hurtServer(level, this.damageSources().mobAttack(this), 12.0f)) {
                Vec3 out = to.lengthSqr() < 1.0E-4 ? fwd : to.normalize();
                e.setDeltaMovement(e.getDeltaMovement().add(out.x * 1.4, 0.7, out.z * 1.4));
                e.needsSync = true;
            }
        }
    }

    private void cubeBarrage(ServerLevel level, LivingEntity target) {
        this.playSound(SoundEvents.WARDEN_ROAR, 2.5f, 1.1f);
        level.sendParticles(ParticleTypes.SCULK_SOUL, this.getX(), this.getY(0.7), this.getZ(), 30,
                this.getBbWidth() * 0.4, this.getBbHeight() * 0.3, this.getBbWidth() * 0.4, 0.05);
        int n = 5;
        for (int i = 0; i < n; i++) {
            double a = this.getYRot() * Math.PI / 180 + (i - (n - 1) / 2.0) * 0.6 + Math.PI / 2;
            SculkCubeEntity cube = new SculkCubeEntity(level, this);
            cube.setPos(this.getX() + Math.cos(a) * this.getBbWidth() * 0.5, this.getY(0.6), this.getZ() + Math.sin(a) * this.getBbWidth() * 0.5);
            cube.setDeltaMovement(Math.cos(a) * 0.45, 0.55, Math.sin(a) * 0.45);
            level.addFreshEntity(cube);
        }
    }

    private void summonCatalysts(ServerLevel level, LivingEntity target) {
        this.playSound(SoundEvents.SCULK_SHRIEKER_SHRIEK, 2.0f, 0.6f);
        Vec3 centre = target != null ? target.position() : this.position();
        catalysts.summon(level, centre, 3, 9.0);
    }

    @Override
    public void die(DamageSource source) {
        super.die(source);
        if (this.level() instanceof ServerLevel level) {
            catalysts.clear(level);
        }
    }

    @Override
    public void remove(Entity.RemovalReason reason) {
        if (this.level() instanceof ServerLevel level) {
            catalysts.clear(level);
        }
        super.remove(reason);
    }

    public boolean isPhaseTwo() {
        return BossMechanics.isPhaseTwo(this);
    }


    @Override
    public boolean doHurtTarget(ServerLevel level, Entity target) {
        boolean hit = super.doHurtTarget(level, target);
        if (hit) {
            // 左右連擊：右手、左手輪流
            this.triggerAnim("skill", (combo++ & 1) == 0 ? "attack" : "attack_left");
        }
        return hit;
    }

    @Override
    public double skillCooldownScale() {
        return BossMechanics.isPhaseTwo(this) ? BossMechanics.PHASE_TWO_COOLDOWN : 1.0;
    }

    /** Boss 不會因為玩家走遠而消失。 */
    @Override
    public boolean removeWhenFarAway(double distanceSqr) {
        return false;
    }

    @Override
    public void startSeenByPlayer(ServerPlayer player) {
        super.startSeenByPlayer(player);
        this.bossEvent.setName(this.getDisplayName());
        this.bossEvent.addPlayer(player);
    }

    @Override
    public void stopSeenByPlayer(ServerPlayer player) {
        super.stopSeenByPlayer(player);
        this.bossEvent.removePlayer(player);
    }

    @Override
    protected void customServerAiStep(ServerLevel serverLevel) {
        super.customServerAiStep(serverLevel);
        BossMechanics.tick(this, serverLevel, this.bossEvent, List.of(ModEntities.STALKER, ModEntities.STALKER));
        catalysts.tick(serverLevel);
        if (!roared && this.tickCount > 10) {
            roared = true;
            this.triggerAnim("skill", "roar");
            this.playSound(SoundEvents.WARDEN_ROAR, 3.0f, 0.8f);
        }
        if (isPhaseTwo() && this.tickCount % 100 == 0) {
            for (Player p : serverLevel.getEntitiesOfClass(Player.class, new AABB(this.blockPosition()).inflate(20.0 * RANGE_SCALE))) {
                p.addEffect(new MobEffectInstance(MobEffects.DARKNESS, 120, 0, false, false), this);
            }
        }
    }
}
