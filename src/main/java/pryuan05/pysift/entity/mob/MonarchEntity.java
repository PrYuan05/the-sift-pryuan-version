package pryuan05.pysift.entity.mob;

import java.util.List;
import java.util.ArrayList;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.Mob;
import pryuan05.pysift.entity.ai.GroundSlamGoal;
import pryuan05.pysift.entity.ai.MonarchSkills;
import pryuan05.pysift.entity.ai.SkillGoal;
import java.util.UUID;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerBossEvent;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.BossEvent;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;
import pryuan05.pysift.entity.BossMechanics;
import pryuan05.pysift.entity.ModEntities;
import pryuan05.pysift.entity.PysiftMonsterEntity;
import pryuan05.pysift.entity.ai.GroundShockwaveGoal;
import pryuan05.pysift.entity.ai.LeapSlamGoal;

/**
 * 君王（Boss，300 HP，披風國王）：近戰為主。
 * <ul>
 *   <li>體型：原版 SCALE 屬性 2.5 倍（模型與碰撞箱一起放大，約 9 格高）；以下距離與半徑都是基礎值，半徑／貼身類距離實際乘上 SCALE，遠程最大距離乘上 RANGE_SCALE（1.75）。</li>
 *   <li>連段：近戰第一下一般攻擊（動畫 attack），第二下橫掃（動畫 attack2）——對目標造成較強擊退，
 *       並對身邊 2.5 格內其他非敵對生物造成 6 點傷害。</li>
 *   <li>跳躍砸地：目標在 5~14 格且有視線，蹲低 0.4 秒後朝目標躍起，約 0.7 秒後落地，落點半徑 4 格 14 點傷害並擊飛，
 *       冷卻 9 秒（動畫 leap）。</li>
 *   <li>地面衝擊波：目標在 6~16 格且有視線，前搖 0.7 秒，沿地面朝目標送出 12 格長的音波（每 tick 1 格），
 *       波頭碰到的目標受 10 點無視護甲傷害並被掀起，可側閃或跳過，冷卻 11 秒（動畫 shockwave）。</li>
 *   <li>近戰吸血：近戰命中回復 3% 最大生命。</li>
 *   <li>衝刺迴旋斬：目標在 5~18 格，後拉 0.6 秒後迴旋衝刺 0.5 秒（碰到 14 點），路徑上留下羽毛，5 秒後射向玩家，冷卻 10 秒（動畫 dash_strike）。</li>
 *   <li>繞圈旋轉：目標在 3~14 格，高速旋轉撲向目標（碰到 10 點），落點周圍的圓上留下 8 根羽毛，5 秒後射向玩家，冷卻 13 秒（動畫 hover_loop）。</li>
 *   <li>三段災厄連擊：貼近時前方斬擊（12 點）→ 迴旋衝刺（8 點）→ 再斬一次，冷卻 12 秒（動畫 calamity）。</li>
 *   <li>迴旋踢：貼身時短短一轉，周圍一圈 9 點傷害，冷卻 4 秒（動畫 heel_stomp）。</li>
 *   <li>召喚：咆哮召來 2 隻潛伏獵手、2 隻食腐獸，牠們還活著時不重複召喚，冷卻 20 秒（動畫 summon）。</li>
 *   <li>Monarch 分身：血量剩 3/4 以下時召出半透明的分身（30% 生命、同樣的招式、沒有血條、不掉落、不存檔）；分身被打倒 10 秒後再召一隻，本體死亡時分身一起消失。</li>
 *   <li>死亡時播放 death。</li>
 *   <li>威脅機制（BossMechanics）：二階段攻擊 +30%、移速 +15%、冷卻 ×0.65，並召喚 2 隻冠羽哨兵護衛；脫戰回血、守在競技場。</li>
 * </ul>
 */
public class MonarchEntity extends PysiftMonsterEntity {
    private final ServerBossEvent bossEvent = (ServerBossEvent) new ServerBossEvent(
            UUID.randomUUID(),
            Component.literal("Monarch"),
            BossEvent.BossBarColor.PURPLE,
            BossEvent.BossBarOverlay.PROGRESS
    ).setDarkenScreen(true);
    private int combo;
    /** 體型倍率（原版 SCALE 屬性）；貼身／範圍類距離乘上它。 */
    private static final double SCALE = 2.5;
    /** 遠程最大距離的倍率（比體型小，避免射程過遠）。 */
    private static final double RANGE_SCALE = 1.75;

    public MonarchEntity(EntityType<? extends PysiftMonsterEntity> entityType, Level level) {
        super(entityType, level);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return PysiftMonsterEntity.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 420.0)
                .add(Attributes.MOVEMENT_SPEED, 0.3)
                .add(Attributes.ATTACK_DAMAGE, 15.0)
                .add(Attributes.KNOCKBACK_RESISTANCE, 0.8)
                .add(Attributes.ARMOR, 10.0)
                .add(Attributes.SCALE, SCALE)
                .add(Attributes.STEP_HEIGHT, 2.5)
                .add(Attributes.FOLLOW_RANGE, 48.0);
    }

    @Override
    protected void registerGoals() {
        super.registerGoals();   // float, melee (priority 2), stroll, look, targets
        this.goalSelector.addGoal(1, new LeapSlamGoal(this, "leap", 8, 14, 10, 180, 8.0, 16.0 * RANGE_SCALE, 4.0 * SCALE, 14.0f));
        this.goalSelector.addGoal(1, new GroundShockwaveGoal(this, "shockwave", 14, 220, 6.0 * RANGE_SCALE, 16.0 * RANGE_SCALE, 28.0, 2.3, 1.2 * SCALE, 10.0f));
        // 衝刺迴旋斬：後拉 0.6 秒後迴旋衝刺 0.5 秒（接觸 14 傷害），路徑上留下羽毛，5 秒後射向玩家
        this.goalSelector.addGoal(1, new MonarchSkills.DashStrike(this, "dash_strike", 12, 10, 12, 200, 5.0, 18.0, 1.1, 14.0f));
        // 繞圈旋轉：反方向後拉，高速旋轉撲向目標（接觸 10 傷害），落點周圍圓上留下 8 根羽毛
        this.goalSelector.addGoal(1, new MonarchSkills.HoverLoop(this, "hover_loop", 10, 14, 16, 260, 3.0, 14.0, 0.9, 10.0f, 3.0));
        // 三段災厄連擊：斬 → 迴旋衝刺 → 斬
        this.goalSelector.addGoal(1, new MonarchSkills.Calamity(this, "calamity", 14, 240, 3.0 * SCALE, 3.5 * SCALE, 12.0f, 8.0f, 0.9));
        // 迴旋踢：貼身時短短一轉，周圍一圈 9 點傷害
        this.goalSelector.addGoal(1, new SkillGoal(this, "heel_stomp", 8, 18, 80, 0.0, 2.0 * SCALE, false,
                (level, t) -> GroundSlamGoal.slamAt(level, this, this.position(), 2.5 * SCALE, 9.0f, 0.3, e -> !(e instanceof Enemy))));
        // 召喚：咆哮召來 2 隻潛伏獵手、2 隻食腐獸（還活著時不重複召喚；分身不召喚）
        this.goalSelector.addGoal(1, new SkillGoal(this, "summon", 20, 36, 400, 0.0, 30.0, false, this::summonGuards) {
            @Override
            public boolean canUse() {
                return !isEcho() && livingGuards() == 0 && super.canUse();
            }
        });
    }

    @Override
    protected List<String> skillAnimations() {
        return List.of("attack", "attack2", "leap", "shockwave", "dash_strike", "hover_loop", "calamity", "heel_stomp", "summon");
    }

    @Override
    protected boolean hasDeathAnimation() {
        return true;
    }

    /** 3 秒死亡演出：受創踉蹌、跪地、王冠滑落，最後向後倒下（2.5 秒落地）；分身照舊立刻消失。 */
    @Override
    public int deathDuration() {
        return isEcho() ? 20 : BossMechanics.DEATH_TICKS;
    }

    @Override
    protected void onDeathTick(ServerLevel level) {
        if (deathDuration() > 20) {
            BossMechanics.deathTick(this, level, this.deathTime, 50);
        }
    }

    @Override
    public boolean doHurtTarget(ServerLevel level, Entity target) {
        boolean hit = super.doHurtTarget(level, target);
        if (!hit) {
            return false;
        }
        this.heal(this.getMaxHealth() * 0.03f);   // 近戰吸血：每次命中回 3% 生命
        combo++;
        if (combo % 2 == 1) {
            this.triggerAnim("skill", "attack");
            return true;
        }
        // second hit of the combo: a wide sweep
        this.triggerAnim("skill", "attack2");
        this.playSound(SoundEvents.PLAYER_ATTACK_SWEEP, 1.5f, 0.7f);
        Vec3 c = this.position();
        if (target instanceof LivingEntity lt) {
            Vec3 out = lt.position().subtract(c).multiply(1, 0, 1).normalize();
            lt.setDeltaMovement(lt.getDeltaMovement().add(out.x * 1.2, 0.35, out.z * 1.2));
            lt.needsSync = true;
        }
        for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, this.getBoundingBox().inflate(2.5 * SCALE),
                e -> e != this && e != target && e.isAlive() && !(e instanceof Enemy))) {
            e.hurtServer(level, this.damageSources().mobAttack(this), 6.0f);
        }
        return true;
    }

    // ------------------------------------------------------------------ guards
    private final List<UUID> guards = new ArrayList<>();

    private int livingGuards() {
        if (!(this.level() instanceof ServerLevel level)) {
            return 0;
        }
        guards.removeIf(id -> !(level.getEntity(id) instanceof LivingEntity l) || !l.isAlive());
        return guards.size();
    }

    private void summonGuards(ServerLevel level, LivingEntity target) {
        this.playSound(SoundEvents.RAVAGER_ROAR, 2.5f, 0.8f);
        List<EntityType<? extends Mob>> kinds = List.of(ModEntities.STALKER, ModEntities.STALKER, ModEntities.SCAVENGER, ModEntities.SCAVENGER);
        for (int i = 0; i < kinds.size(); i++) {
            Mob guard = kinds.get(i).create(level, EntitySpawnReason.MOB_SUMMONED);
            if (guard == null) {
                continue;
            }
            double a = Math.PI * 2 * i / kinds.size() + Math.PI / 4;
            double r = this.getBbWidth() * 0.5 + 2.5;
            guard.snapTo(this.getX() + Math.cos(a) * r, this.getY() + 0.5, this.getZ() + Math.sin(a) * r, this.getYRot(), 0);
            level.addFreshEntity(guard);
            guard.setTarget(target);
            guards.add(guard.getUUID());
            level.sendParticles(ParticleTypes.SCULK_SOUL, guard.getX(), guard.getY() + 0.5, guard.getZ(), 10, 0.3, 0.5, 0.3, 0.02);
        }
    }

    // ------------------------------------------------------------------ Monarch Echo (spectral clone)
    private static final EntityDataAccessor<Boolean> DATA_ECHO = SynchedEntityData.defineId(MonarchEntity.class, EntityDataSerializers.BOOLEAN);
    private static final float ECHO_HEALTH_FRACTION = 0.3f;
    private static final int ECHO_RESPAWN_TICKS = 200;
    private UUID echoOf;          // 分身：本體的 UUID
    private UUID echoId;          // 本體：目前分身的 UUID
    private int echoReadyAt;

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(DATA_ECHO, false);
    }

    /** 這隻是 Monarch 分身（半透明、沒有血條、不掉落、不存檔，本體死亡時一起消失）。 */
    public boolean isEcho() {
        return this.entityData.get(DATA_ECHO);
    }

    /** 本體血量剩 3/4 以下時召出分身；分身被打倒後 10 秒再召一隻。 */
    private void tickEchoSpawning(ServerLevel level) {
        if (echoId != null) {
            if (level.getEntity(echoId) instanceof MonarchEntity echo && echo.isAlive()) {
                return;
            }
            echoId = null;
            echoReadyAt = this.tickCount + ECHO_RESPAWN_TICKS;
        }
        if (this.getHealth() > this.getMaxHealth() * 0.75f || this.tickCount < echoReadyAt || this.getTarget() == null) {
            return;
        }
        MonarchEntity echo = ModEntities.MONARCH.create(level, EntitySpawnReason.MOB_SUMMONED);
        if (echo == null) {
            return;
        }
        echo.entityData.set(DATA_ECHO, true);
        echo.echoOf = this.getUUID();
        float hp = this.getMaxHealth() * ECHO_HEALTH_FRACTION;
        echo.getAttribute(Attributes.MAX_HEALTH).setBaseValue(hp);
        echo.setHealth(hp);
        Vec3 side = Vec3.directionFromRotation(0, this.getYRot() + 90).scale(this.getBbWidth() + 1.5);
        echo.snapTo(this.getX() + side.x, this.getY(), this.getZ() + side.z, this.getYRot(), 0);
        level.addFreshEntity(echo);
        echo.setTarget(this.getTarget());
        echoId = echo.getUUID();
        this.playSound(SoundEvents.ILLUSIONER_MIRROR_MOVE, 2.0f, 0.7f);
        level.sendParticles(ParticleTypes.REVERSE_PORTAL, echo.getX(), echo.getY(0.5), echo.getZ(), 50,
                echo.getBbWidth() * 0.4, echo.getBbHeight() * 0.4, echo.getBbWidth() * 0.4, 0.05);
    }

    /** 分身：本體不在或已死亡時消散。 */
    private void tickAsEcho(ServerLevel level) {
        if (echoOf == null || !(level.getEntity(echoOf) instanceof MonarchEntity owner) || !owner.isAlive()) {
            level.sendParticles(ParticleTypes.REVERSE_PORTAL, this.getX(), this.getY(0.5), this.getZ(), 40,
                    this.getBbWidth() * 0.4, this.getBbHeight() * 0.4, this.getBbWidth() * 0.4, 0.05);
            this.discard();
        }
    }

    @Override
    public void die(DamageSource source) {
        super.die(source);
        if (!isEcho() && echoId != null && this.level() instanceof ServerLevel level
                && level.getEntity(echoId) instanceof MonarchEntity echo && echo.isAlive()) {
            echo.kill(level);
        }
    }

    @Override
    public boolean shouldBeSaved() {
        return !isEcho() && super.shouldBeSaved();
    }

    @Override
    protected boolean shouldDropLoot(ServerLevel level) {
        return !isEcho() && super.shouldDropLoot(level);
    }

    @Override
    public boolean shouldDropExperience() {
        return !isEcho() && super.shouldDropExperience();
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
        if (isEcho()) {
            return;   // 分身沒有血條
        }
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
        if (isEcho()) {
            tickAsEcho(serverLevel);
            return;
        }
        BossMechanics.tick(this, serverLevel, this.bossEvent, List.of(ModEntities.SENTINEL, ModEntities.SENTINEL));
        tickEchoSpawning(serverLevel);
    }
}
