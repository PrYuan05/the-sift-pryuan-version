package pryuan05.pysift.entity.mob;

import java.util.List;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import pryuan05.pysift.entity.PysiftMonsterEntity;
import pryuan05.pysift.entity.projectile.DartEntity;

/**
 * 針刺獸（反傷刺蝟）。被玩家近戰（非投射物）打中時，反彈 30% 傷害給攻擊者（荊棘），
 * 並向四周水平射出一圈 8 根尖刺（動畫 bristle，2 點基礎傷害；尖刺環冷卻 1 秒）。
 */
public class PrickleEntity extends PysiftMonsterEntity {
    private int spikeCooldown;

    public PrickleEntity(EntityType<? extends PysiftMonsterEntity> entityType, Level level) {
        super(entityType, level);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return PysiftMonsterEntity.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 26.0)
                .add(Attributes.MOVEMENT_SPEED, 0.22)
                .add(Attributes.ATTACK_DAMAGE, 3.0);
    }

    @Override
    protected List<String> skillAnimations() {
        return List.of("bristle");
    }

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        boolean hurt = super.hurtServer(level, source, amount);
        if (hurt && source.getEntity() instanceof Player attacker && source.getDirectEntity() == attacker) {
            attacker.hurtServer(level, this.damageSources().thorns(this), amount * 0.3f);
            if (spikeCooldown <= 0) {
                spikeCooldown = 20;
                spikeRing(level);
            }
        }
        return hurt;
    }

    private void spikeRing(ServerLevel level) {
        this.triggerAnim("skill", "bristle");
        this.playSound(SoundEvents.ARROW_SHOOT, 1.0f, 0.6f);
        double y = this.getY() + this.getBbHeight() * 0.5;
        for (int i = 0; i < 8; i++) {
            double a = i * Math.PI / 4;
            double dx = Math.cos(a), dz = Math.sin(a);
            DartEntity spike = DartEntity.create(level, this, this.getX() + dx * (this.getBbWidth() * 0.6 + 0.3), y,
                    this.getZ() + dz * (this.getBbWidth() * 0.6 + 0.3), 2.0);
            spike.shoot(dx, 0.05, dz, 1.0f, 0.0f);
            level.addFreshEntity(spike);
        }
    }

    @Override
    protected void customServerAiStep(ServerLevel level) {
        super.customServerAiStep(level);
        if (spikeCooldown > 0) {
            spikeCooldown--;
        }
    }
}
