package pryuan05.pysift.entity.mob;

import java.util.List;
import java.util.ArrayList;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.phys.Vec3;
import pryuan05.pysift.entity.ai.SkillGoal;
import pryuan05.pysift.entity.ai.VortexGoal;
import java.util.UUID;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerBossEvent;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.BossEvent;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import pryuan05.pysift.entity.BossMechanics;
import pryuan05.pysift.entity.ModEntities;
import pryuan05.pysift.entity.PysiftMonsterEntity;
import pryuan05.pysift.entity.ai.GroundSlamGoal;
import pryuan05.pysift.entity.ai.KeepRangeGoal;
import pryuan05.pysift.entity.ai.ResonanceRingGoal;
import pryuan05.pysift.entity.ai.SonicConeGoal;

/**
 * 調和者（Boss，250 HP，水母型）：遠程為主，和目標保持 11~17 格。
 * <ul>
 *   <li>體型：原版 SCALE 屬性 2.35 倍（模型與碰撞箱一起放大，約 9 格高）；以下距離與半徑都是基礎值，半徑／貼身類距離實際乘上 SCALE，遠程最大距離乘上 RANGE_SCALE（1.75）。</li>
 *   <li>音波錐：目標在 8 格內且有視線，前搖 0.6 秒，前方 60° 扇形 8 點無視護甲傷害並擊退，冷卻 6 秒（動畫 sonic_cone）。</li>
 *   <li>共鳴環：目標在 7 格內，前搖 0.4 秒，音波環在 1 秒內從 2 格擴散到 7 格，經過的目標受 6 點傷害（可跳過或躲在內側），
 *       冷卻 12 秒（動畫 resonance）。</li>
 *   <li>近身砸地：被逼到 3.5 格內時，半徑 4 格 10 點傷害並往上擊飛，冷卻 7 秒（動畫 slam）。</li>
 *   <li>沒有一般近戰；死亡時播放 death。</li>
 *   <li>威脅機制（BossMechanics）：二階段攻擊 +30%、移速 +15%、冷卻 ×0.65，並召喚 3 隻引信飛蟲；脫戰回血、守在競技場。</li>
 *   <li>咆哮召喚：自己的援軍少於 3 隻時，咆哮放出半徑 5×SCALE 格的衝擊波（6 點）並召喚 5 隻隙浮怪物（哨兵、母巢怪、潛伏獵手、傳粉蜂怪、幼苗怪），冷卻 30 秒（動畫 roar）。</li>
 *   <li>光束增益：用光束連著每隻還活著的援軍，每 2 秒給力量 I 與抗性 I；援軍死了光束就斷。</li>
 *   <li>觸手抓取：目標在 2~6×SCALE 格且有視線，舉起觸手抓住目標拉到身邊，7 點傷害並緩速，冷卻 8 秒（動畫 tentacle_grab）。</li>
 *   <li>紫色漩渦球＋砸地：前方召出漩渦球，3.5 秒內把站在地上的人往球心吸（一直跳就不會被吸走），接著整個身體砸在球的位置，半徑 2.5×SCALE 格 16 點傷害，冷卻 15 秒（動畫 vortex）。</li>
 *   <li>死亡狂暴：死亡時 16 格內的敵對怪物獲得速度 II、生命提升 II 與再生 30 秒。</li>
 * </ul>
 */
public class HarmonizerEntity extends PysiftMonsterEntity {
    private final ServerBossEvent bossEvent = (ServerBossEvent) new ServerBossEvent(
            UUID.randomUUID(),
            Component.literal("Harmonizer"),
            BossEvent.BossBarColor.PURPLE,
            BossEvent.BossBarOverlay.PROGRESS
    ).setDarkenScreen(true);

    /** 體型倍率（原版 SCALE 屬性）；貼身／範圍類距離乘上它。 */
    private static final double SCALE = 2.35;
    /** 遠程最大距離的倍率（比體型小，避免射程過遠）。 */
    private static final double RANGE_SCALE = 1.75;

    public HarmonizerEntity(EntityType<? extends PysiftMonsterEntity> entityType, Level level) {
        super(entityType, level);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return PysiftMonsterEntity.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 350.0)
                .add(Attributes.MOVEMENT_SPEED, 0.28)
                .add(Attributes.ATTACK_DAMAGE, 12.0)
                .add(Attributes.KNOCKBACK_RESISTANCE, 0.7)
                .add(Attributes.SCALE, SCALE)
                .add(Attributes.STEP_HEIGHT, 2.5)
                .add(Attributes.FOLLOW_RANGE, 48.0);
    }

    @Override
    protected void registerGoals() {
        this.goalSelector.addGoal(0, new FloatGoal(this));
        this.goalSelector.addGoal(1, new GroundSlamGoal(this, "slam", 12, 20, 140, 3.5 * SCALE, 4.0 * SCALE, 10.0f, 0.6));
        this.goalSelector.addGoal(1, new SonicConeGoal(this, "sonic_cone", 12, 24, 120, 8.0 * SCALE, 30.0, 8.0f, 1.2));
        this.goalSelector.addGoal(1, new ResonanceRingGoal(this, "resonance", 8, 240, 7.0 * SCALE, 2.0 * SCALE, 7.0 * SCALE, 20, 6.0f));
        // 咆哮召喚：環狀衝擊波＋召喚 5 隻隙浮怪物（場上自己的援軍少於 3 隻時才會用）
        this.goalSelector.addGoal(1, new SkillGoal(this, "roar", 20, 40, 600, 0.0, 30.0, false, this::roarSummon) {
            @Override
            public boolean canUse() {
                return livingAllies() < 3 && super.canUse();
            }
        });
        // 觸手抓取：舉起觸手抓住目標，拉到身邊並造成傷害
        this.goalSelector.addGoal(1, new SkillGoal(this, "tentacle_grab", 14, 30, 160, 2.0 * SCALE, 6.0 * SCALE, true, this::tentacleGrab));
        // 紫色漩渦球＋砸地：前方召出漩渦球把人吸過去（一直跳可掙脫），3.5 秒後整個身體砸下
        this.goalSelector.addGoal(1, new VortexGoal(this, "vortex", 70, 84, 300, 12.0 * RANGE_SCALE, 2.5 * SCALE, 4.0 * SCALE,
                2.5 * SCALE, 16.0f));
        this.goalSelector.addGoal(3, new KeepRangeGoal(this, 11.0, 17.0, 1.0));   // 讓音波錐（8×SCALE）與共鳴環（7×SCALE）打得到
        this.goalSelector.addGoal(7, new WaterAvoidingRandomStrollGoal(this, 0.8));
        this.goalSelector.addGoal(8, new LookAtPlayerGoal(this, Player.class, (float) (12.0 * RANGE_SCALE)));
        this.goalSelector.addGoal(8, new RandomLookAroundGoal(this));

        this.targetSelector.addGoal(1, new HurtByTargetGoal(this));
        this.targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
    }

    // ------------------------------------------------------------------ allies, beams, skills
    private static final List<EntityType<? extends Mob>> SUMMONS = List.of(ModEntities.SENTINEL, ModEntities.NESTER,
            ModEntities.STALKER, ModEntities.POLLINATOR, ModEntities.SEEDLING);
    private final List<UUID> allies = new ArrayList<>();

    private List<LivingEntity> allyEntities(ServerLevel level) {
        List<LivingEntity> out = new ArrayList<>();
        allies.removeIf(id -> {
            Entity e = level.getEntity(id);
            if (e instanceof LivingEntity l && l.isAlive()) {
                out.add(l);
                return false;
            }
            return true;
        });
        return out;
    }

    private int livingAllies() {
        return this.level() instanceof ServerLevel level ? allyEntities(level).size() : 0;
    }

    private void roarSummon(ServerLevel level, LivingEntity target) {
        this.playSound(SoundEvents.WARDEN_ROAR, 2.5f, 1.3f);
        GroundSlamGoal.slamAt(level, this, this.position(), 5.0 * SCALE, 6.0f, 0.4, e -> !(e instanceof Enemy));
        for (int i = 0; i < 5; i++) {
            Mob minion = SUMMONS.get(this.random.nextInt(SUMMONS.size())).create(level, EntitySpawnReason.MOB_SUMMONED);
            if (minion == null) {
                continue;
            }
            double a = Math.PI * 2 * i / 5 + this.random.nextDouble() * 0.4;
            double r = this.getBbWidth() * 0.5 + 3.0;
            minion.snapTo(this.getX() + Math.cos(a) * r, this.getY() + 0.5, this.getZ() + Math.sin(a) * r, this.getYRot(), 0);
            level.addFreshEntity(minion);
            minion.setTarget(target);
            allies.add(minion.getUUID());
            level.sendParticles(ParticleTypes.SCULK_SOUL, minion.getX(), minion.getY() + 0.5, minion.getZ(), 10, 0.3, 0.5, 0.3, 0.02);
        }
    }

    /** 光束增益：連到每隻還活著的援軍，每 2 秒給力量 I 與抗性 I；援軍死掉光束就斷。 */
    private void tickBeams(ServerLevel level) {
        if (this.tickCount % 4 != 0 || allies.isEmpty()) {
            return;
        }
        Vec3 from = this.position().add(0, this.getBbHeight() * 0.75, 0);
        for (LivingEntity ally : allyEntities(level)) {
            if (ally.distanceTo(this) > 32) {
                continue;
            }
            Vec3 to = ally.position().add(0, ally.getBbHeight() * 0.6, 0).subtract(from);
            int n = Math.max(4, (int) (to.length() * 1.5));
            for (int i = 1; i < n; i++) {
                Vec3 pt = from.add(to.scale(i / (double) n));
                level.sendParticles(ParticleTypes.END_ROD, pt.x, pt.y, pt.z, 1, 0, 0, 0, 0);
            }
            if (this.tickCount % 40 == 0) {
                ally.addEffect(new MobEffectInstance(MobEffects.STRENGTH, 60, 0), this);
                ally.addEffect(new MobEffectInstance(MobEffects.RESISTANCE, 60, 0), this);
            }
        }
    }

    private void tentacleGrab(ServerLevel level, LivingEntity target) {
        if (target == null || !target.isAlive() || this.distanceTo(target) > 7.0 * SCALE) {
            return;
        }
        this.playSound(SoundEvents.SLIME_SQUISH, 2.0f, 0.5f);
        Vec3 to = this.position().subtract(target.position()).multiply(1, 0, 1);
        double d = to.length() - this.getBbWidth() * 0.5 - 1.0;
        if (target.hurtServer(level, this.damageSources().mobAttack(this), 7.0f) && d > 0) {
            Vec3 pull = to.normalize().scale(Math.min(2.2, d * 0.2));
            target.setDeltaMovement(pull.x, 0.35, pull.z);
            target.needsSync = true;
            target.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 40, 1), this);
        }
        level.sendParticles(ParticleTypes.SQUID_INK, target.getX(), target.getY(0.5), target.getZ(), 10, 0.3, 0.4, 0.3, 0.02);
    }

    /** 死亡狂暴：附近 16 格的隙浮怪物獲得速度、生命提升與再生 30 秒。 */
    @Override
    public void die(DamageSource source) {
        super.die(source);
        if (!(this.level() instanceof ServerLevel level)) {
            return;
        }
        this.playSound(SoundEvents.WARDEN_SONIC_BOOM, 2.0f, 0.8f);
        level.sendParticles(ParticleTypes.SONIC_BOOM, this.getX(), this.getY(0.5), this.getZ(), 1, 0, 0, 0, 0);
        for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, this.getBoundingBox().inflate(16.0),
                e -> e != this && e.isAlive() && e instanceof Enemy)) {
            e.addEffect(new MobEffectInstance(MobEffects.SPEED, 600, 1), this);
            e.addEffect(new MobEffectInstance(MobEffects.HEALTH_BOOST, 600, 1), this);
            e.addEffect(new MobEffectInstance(MobEffects.REGENERATION, 600, 0), this);
            level.sendParticles(ParticleTypes.ANGRY_VILLAGER, e.getX(), e.getY() + e.getBbHeight() + 0.3, e.getZ(), 2, 0.2, 0.1, 0.2, 0);
        }
    }

    @Override
    protected List<String> skillAnimations() {
        return List.of("sonic_cone", "resonance", "slam", "roar", "tentacle_grab", "vortex");
    }

    @Override
    protected boolean hasDeathAnimation() {
        return true;
    }

    /** 3 秒死亡演出：顫抖、觸手亂甩，緩緩沉到地上（2.6 秒落地）。 */
    @Override
    public int deathDuration() {
        return BossMechanics.DEATH_TICKS;
    }

    @Override
    protected void onDeathTick(ServerLevel level) {
        if (deathDuration() > 20) {
            BossMechanics.deathTick(this, level, this.deathTime, 52);
        }
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
        BossMechanics.tick(this, serverLevel, this.bossEvent, List.of(ModEntities.FUSEFLY, ModEntities.FUSEFLY, ModEntities.FUSEFLY));
        tickBeams(serverLevel);
    }
}
