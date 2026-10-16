package pryuan05.pysift.entity.mob;

import java.util.List;
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
    }

    @Override
    protected List<String> skillAnimations() {
        return List.of("attack", "attack2", "leap", "shockwave");
    }

    @Override
    protected boolean hasDeathAnimation() {
        return true;
    }

    @Override
    public boolean doHurtTarget(ServerLevel level, Entity target) {
        boolean hit = super.doHurtTarget(level, target);
        if (!hit) {
            return false;
        }
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
        BossMechanics.tick(this, serverLevel, this.bossEvent, List.of(ModEntities.SENTINEL, ModEntities.SENTINEL));
    }
}
