package pryuan05.pysift.entity.mob;

import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import pryuan05.pysift.entity.PysiftMonsterEntity;

/**
 * 食腐獸（嗜血掠食者）。
 * <ul>
 *   <li>優先鎖定血量低於 50% 的玩家或生物（不含敵對生物），其次才是一般玩家。</li>
 *   <li>撕裂流血：命中後 5 秒內每秒 1 點傷害（動畫 attack、紅色碎屑粒子）。流血由這隻食腐獸維持，牠死亡時流血停止。</li>
 * </ul>
 */
public class ScavengerEntity extends PysiftMonsterEntity {
    private static final int BLEED_TICKS = 100;
    private final Map<LivingEntity, Integer> bleeding = new HashMap<>();

    public ScavengerEntity(EntityType<? extends PysiftMonsterEntity> entityType, Level level) {
        super(entityType, level);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return PysiftMonsterEntity.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 22.0)
                .add(Attributes.MOVEMENT_SPEED, 0.27)
                .add(Attributes.ATTACK_DAMAGE, 4.0);
    }

    @Override
    protected void registerGoals() {
        super.registerGoals();
        this.targetSelector.removeAllGoals(g -> true);
        this.targetSelector.addGoal(1, new HurtByTargetGoal(this));
        this.targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, LivingEntity.class, 10, true, false,
                (target, level) -> target.getHealth() < target.getMaxHealth() * 0.5f && !(target instanceof Enemy)
                        && !(target instanceof Player p && (p.isCreative() || p.isSpectator()))));
        this.targetSelector.addGoal(3, new NearestAttackableTargetGoal<>(this, Player.class, true));
    }

    @Override
    protected List<String> skillAnimations() {
        return List.of("attack");
    }

    @Override
    protected String meleeAnimation() {
        return "attack";
    }

    @Override
    public boolean doHurtTarget(ServerLevel level, Entity target) {
        boolean hit = super.doHurtTarget(level, target);
        if (hit && target instanceof LivingEntity living) {
            bleeding.put(living, BLEED_TICKS);
        }
        return hit;
    }

    @Override
    protected void customServerAiStep(ServerLevel level) {
        super.customServerAiStep(level);
        Iterator<Map.Entry<LivingEntity, Integer>> it = bleeding.entrySet().iterator();
        while (it.hasNext()) {
            Map.Entry<LivingEntity, Integer> e = it.next();
            LivingEntity victim = e.getKey();
            int left = e.getValue() - 1;
            if (left <= 0 || !victim.isAlive() || victim.level() != level) {
                it.remove();
                continue;
            }
            e.setValue(left);
            if (left % 20 == 0) {
                victim.hurtServer(level, this.damageSources().generic(), 1.0f);
                level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, Blocks.REDSTONE_BLOCK.defaultBlockState()),
                        victim.getX(), victim.getY(0.5), victim.getZ(), 8, 0.2, 0.3, 0.2, 0.05);
            }
        }
    }
}
