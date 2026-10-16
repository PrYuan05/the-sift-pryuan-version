package pryuan05.pysift.entity.mob;

import java.util.List;
import java.util.UUID;
import net.minecraft.network.chat.Component;
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
import pryuan05.pysift.entity.ai.ChargeGoal;
import pryuan05.pysift.entity.ai.GroundSlamGoal;
import pryuan05.pysift.entity.ai.SonicBeamGoal;

/**
 * 幽匿巨怪（Boss，400 HP）。
 * <ul>
 *   <li>體型：原版 SCALE 屬性 1.8 倍（模型含肩上靈魂火約 9 格高，碰撞箱 5.8 × 7.7 格）；以下距離與半徑都是基礎值，半徑／貼身類距離實際乘上 SCALE，遠程最大距離乘上 RANGE_SCALE（1.75）。</li>
 *   <li>目標：玩家優先，其次鐵魔像；被攻擊會反擊。</li>
 *   <li>近戰：揮臂（動畫 attack）。</li>
 *   <li>砸地：目標在 6 格內，前搖 1 秒，半徑 5 格 12 點傷害並往上擊飛，冷卻 8 秒（動畫 slam）。</li>
 *   <li>音波：目標在 6~20 格且有視線，蓄力 1.7 秒，無視護甲 10 點傷害並擊退，冷卻 10 秒
 *       （動畫 sonic_charge → sonic_release）。</li>
 *   <li>衝撞：目標在 8~24 格時蓄力 1 秒（動畫 charge），直線衝刺最多 1.2 秒，撞到 18 點傷害並大幅撞飛；
 *       撞牆會停下並露出 1.25 秒破綻，冷卻 11 秒。</li>
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
        // 衝撞：目標在 8~24 格時蓄力 1 秒後直線衝刺（最多 1.2 秒），撞到 18 點傷害並大幅撞飛，冷卻 11 秒
        this.goalSelector.addGoal(1, new ChargeGoal(this, "charge", 20, 24, 25, 220, 8.0, 24.0, 0.9, 18.0f, 2.2));
        this.targetSelector.addGoal(3, new NearestAttackableTargetGoal<>(this, IronGolem.class, true));
    }

    @Override
    protected List<String> skillAnimations() {
        return List.of("attack", "slam", "sonic_charge", "sonic_release", "roar", "charge");
    }

    @Override
    protected boolean hasDeathAnimation() {
        return true;
    }

    public boolean isPhaseTwo() {
        return BossMechanics.isPhaseTwo(this);
    }


    @Override
    public boolean doHurtTarget(ServerLevel level, Entity target) {
        boolean hit = super.doHurtTarget(level, target);
        if (hit) {
            this.triggerAnim("skill", "attack");
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
