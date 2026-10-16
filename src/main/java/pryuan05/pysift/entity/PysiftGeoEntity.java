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

    /**
     * 死亡動畫長度（tick）。原版 20 tick 就移除屍體；回傳更長的值時，屍體會留到動畫播完才消失，
     * 客戶端也不再套用原版的倒地翻轉與紅色受傷色（見 PysiftUniversalGeoRenderer），讓 death 動畫完整呈現。
     */
    public int deathDuration() {
        return 20;
    }

    /** 死亡期間每 tick 在伺服器端呼叫一次（deathTime 從 1 開始），用來放粒子與音效。 */
    protected void onDeathTick(ServerLevel level) {
    }

    @Override
    protected void tickDeath() {
        int duration = deathDuration();
        if (duration <= 20) {
            super.tickDeath();
            return;
        }
        this.deathTime++;
        if (this.level() instanceof ServerLevel level) {
            if (this.deathTime == 1 && !skillAnimations().isEmpty()) {
                this.stopTriggeredAnim("skill", null);   // 技能動畫別蓋過死亡動畫
            }
            onDeathTick(level);
            if (this.deathTime >= duration && !this.isRemoved()) {
                level.broadcastEntityEvent(this, (byte) 60);   // 原版的消失煙霧
                this.remove(RemovalReason.KILLED);
            }
        }
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

    /** 不為 null 時，移動動畫控制器改播這個動畫並停在最後一格（例如出生時從地底爬出）；兩端都會呼叫，要用同步資料判斷。 */
    protected String heldMovementAnimation() {
        return null;
    }

    protected String anim(String name) {
        return "animation." + getEntityIdName() + "." + name;
    }

    @Override
    public void registerControllers(AnimatableManager.ControllerRegistrar controllers) {
        controllers.add(new AnimationController<>("movement", 5, state -> {
            String held = heldMovementAnimation();
            if (held != null) {
                return state.setAndContinue(RawAnimation.begin().thenPlayAndHold(anim(held)));
            }
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
