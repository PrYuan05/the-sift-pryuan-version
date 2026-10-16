package pryuan05.pysift.entity.mob;

import java.util.List;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import pryuan05.pysift.entity.PysiftMonsterEntity;

/**
 * 花苞潛伏怪（地面陷阱）。平時閉合偽裝、完全不動（idle 就是閉合的花苞）；
 * 玩家踏入 2 格內時瞬間張嘴咬合（動畫 bite）：6 點傷害並施加 3 秒緩速 IV（束縛），冷卻 2 秒。
 */
public class BloombudEntity extends PysiftMonsterEntity {
    private static final double BITE_RANGE = 2.0;
    private int biteCooldown;

    public BloombudEntity(EntityType<? extends PysiftMonsterEntity> entityType, Level level) {
        super(entityType, level);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return PysiftMonsterEntity.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 20.0)
                .add(Attributes.MOVEMENT_SPEED, 0.0)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.ATTACK_DAMAGE, 6.0)
                .add(Attributes.SCALE, 0.5); // 模型約 2.38 格高，縮小後約 1.2 格高
    }

    @Override
    protected void registerGoals() {
        // 不移動、不追擊：只有轉頭看玩家
        this.goalSelector.addGoal(8, new LookAtPlayerGoal(this, Player.class, 6.0f));
    }

    @Override
    protected List<String> skillAnimations() {
        return List.of("bite");
    }

    @Override
    public boolean isPushable() {
        return false;
    }

    @Override
    protected void customServerAiStep(ServerLevel level) {
        super.customServerAiStep(level);
        if (biteCooldown > 0) {
            biteCooldown--;
            return;
        }
        Player victim = level.getNearestPlayer(this.getX(), this.getY(), this.getZ(), BITE_RANGE + this.getBbWidth() / 2,
                p -> p.isAlive() && !((Player) p).isCreative() && !p.isSpectator());
        if (victim == null) {
            return;
        }
        biteCooldown = 40;
        this.getLookControl().setLookAt(victim, 90.0f, 90.0f);
        this.triggerAnim("skill", "bite");
        this.playSound(SoundEvents.PHANTOM_BITE, 1.2f, 0.8f);
        if (victim.hurtServer(level, this.damageSources().mobAttack(this), (float) this.getAttributeValue(Attributes.ATTACK_DAMAGE))) {
            victim.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 60, 3), this);
        }
    }
}
