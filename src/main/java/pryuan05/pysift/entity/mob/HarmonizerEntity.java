package pryuan05.pysift.entity.mob;

import java.util.List;
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
        this.goalSelector.addGoal(3, new KeepRangeGoal(this, 11.0, 17.0, 1.0));   // 讓音波錐（8×SCALE）與共鳴環（7×SCALE）打得到
        this.goalSelector.addGoal(7, new WaterAvoidingRandomStrollGoal(this, 0.8));
        this.goalSelector.addGoal(8, new LookAtPlayerGoal(this, Player.class, (float) (12.0 * RANGE_SCALE)));
        this.goalSelector.addGoal(8, new RandomLookAroundGoal(this));

        this.targetSelector.addGoal(1, new HurtByTargetGoal(this));
        this.targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
    }

    @Override
    protected List<String> skillAnimations() {
        return List.of("sonic_cone", "resonance", "slam");
    }

    @Override
    protected boolean hasDeathAnimation() {
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
        BossMechanics.tick(this, serverLevel, this.bossEvent, List.of(ModEntities.FUSEFLY, ModEntities.FUSEFLY, ModEntities.FUSEFLY));
    }
}
