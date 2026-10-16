package pryuan05.pysift.entity.mob;

import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.PathfinderMob;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.AvoidEntityGoal;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.PanicGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import pryuan05.pysift.entity.PysiftAnimalEntity;

/**
 * 藏寶小鬼（逃跑地精）：極快、極膽小，12 格內看到玩家就逃。
 * 掉落物見 data/pysift/loot_table/entities/lootkin.json（必掉礦物，稀有掉落 mod 材料與靈液桶）。
 */
public class LootkinEntity extends PysiftAnimalEntity {
    public LootkinEntity(EntityType<? extends PathfinderMob> entityType, Level level) {
        super(entityType, level);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return PysiftAnimalEntity.createAnimalAttributes()
                .add(Attributes.MAX_HEALTH, 20.0)
                .add(Attributes.MOVEMENT_SPEED, 0.38);
    }

    @Override
    protected void registerGoals() {
        this.goalSelector.addGoal(0, new FloatGoal(this));
        this.goalSelector.addGoal(1, new AvoidEntityGoal<>(this, Player.class, 12.0f, 1.1, 1.4,
                p -> !((Player) p).isSpectator() && !((Player) p).isCreative()));
        this.goalSelector.addGoal(2, new PanicGoal(this, 1.4));
        this.goalSelector.addGoal(6, new WaterAvoidingRandomStrollGoal(this, 1.0));
        this.goalSelector.addGoal(8, new RandomLookAroundGoal(this));
    }
}
