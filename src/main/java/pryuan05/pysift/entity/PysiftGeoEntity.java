package pryuan05.pysift.entity;

import com.geckolib.animatable.GeoEntity;
import com.geckolib.animatable.instance.AnimatableInstanceCache;
import com.geckolib.animatable.manager.AnimatableManager;
import com.geckolib.animation.AnimationController;
import com.geckolib.animation.RawAnimation;
import com.geckolib.animation.object.PlayState;
import com.geckolib.util.GeckoLibUtil;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.PathfinderMob;
import net.minecraft.world.level.Level;

import java.util.List;

public abstract class PysiftGeoEntity extends PathfinderMob implements GeoEntity {
    private final AnimatableInstanceCache cache = GeckoLibUtil.createInstanceCache(this);
    private boolean usingSkill;

    protected PysiftGeoEntity(EntityType<? extends PathfinderMob> entityType, Level level) {
        super(entityType, level);
        // 碰撞箱只在屬性變動時才依 SCALE 重算；預設屬性不會觸發，所以建構時手動刷新一次
        this.refreshDimensions();
    }

    /** 正在執行 TimedSkillGoal 時為 true；同時只會有一個技能。 */
    public boolean isUsingSkill() {
        return usingSkill;
    }

    public void setUsingSkill(boolean usingSkill) {
        this.usingSkill = usingSkill;
    }

    /** 技能冷卻倍率（例如二階段時縮短）。 */
    public double skillCooldownScale() {
        return 1.0;
    }

    public String getEntityIdName() {
        Identifier id = BuiltInRegistries.ENTITY_TYPE.getKey(this.getType());
        return id != null ? id.getPath() : "mob";
    }

    /** 這隻生物的可觸發動畫名稱（對應 animation.&lt;id&gt;.&lt;name&gt;），由伺服器端 triggerAnim("skill", name) 播放。 */
    protected List<String> skillAnimations() {
        return List.of();
    }

    /** 有 animation.&lt;id&gt;.death 動畫時回傳 true，死亡時播放並停在最後一格。 */
    protected boolean hasDeathAnimation() {
        return false;
    }

    /** 一般近戰命中時要播放的可觸發動畫（需同時列在 {@link #skillAnimations()}）；null 表示不播放。 */
    protected String meleeAnimation() {
        return null;
    }

    @Override
    public boolean doHurtTarget(ServerLevel level, Entity target) {
        boolean hit = super.doHurtTarget(level, target);
        String melee = meleeAnimation();
        if (hit && melee != null) {
            this.triggerAnim("skill", melee);
        }
        return hit;
    }

    protected String anim(String name) {
        return "animation." + getEntityIdName() + "." + name;
    }

    @Override
    public void registerControllers(AnimatableManager.ControllerRegistrar controllers) {
        controllers.add(new AnimationController<>("movement", 5, state -> {
            if (hasDeathAnimation() && isDeadOrDying()) {
                return state.setAndContinue(RawAnimation.begin().thenPlayAndHold(anim("death")));
            }
            if (state.isMoving()) {
                return state.setAndContinue(RawAnimation.begin().thenLoop(anim("walk")));
            } else {
                return state.setAndContinue(RawAnimation.begin().thenLoop(anim("idle")));
            }
        }));
        List<String> skills = skillAnimations();
        if (!skills.isEmpty()) {
            AnimationController<PysiftGeoEntity> skill = new AnimationController<>("skill", 2, state -> PlayState.STOP);
            for (String name : skills) {
                skill.triggerableAnim(name, RawAnimation.begin().thenPlay(anim(name)));
            }
            controllers.add(skill);
        }
    }

    @Override
    public AnimatableInstanceCache getAnimatableInstanceCache() {
        return this.cache;
    }
}
