package pryuan05.pysift.entity;

import java.util.Map;
import java.util.WeakHashMap;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.memory.MemoryModuleType;
import net.minecraft.world.entity.monster.warden.Warden;

/**
 * 被歌者倒唱的旋律安撫的監守者（MODDING_ROADMAP §4.7「歌者與監守者的呼應」）：一段時間內不會生氣、不會鎖定目標。
 * 只記在記憶體裡（30 秒的效果，存檔重開就算結束），由 WardenMixin 擋掉增加憤怒值與選目標。
 */
public final class WardenSoothing {
    private static final Map<Warden, Long> UNTIL = new WeakHashMap<>();

    private WardenSoothing() {
    }

    /** 清掉監守者對附近所有生物的憤怒、忘掉攻擊目標，之後 ticks 內不再生氣。 */
    public static void soothe(ServerLevel level, Warden warden, int ticks) {
        UNTIL.put(warden, level.getGameTime() + ticks);
        for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, warden.getBoundingBox().inflate(48.0), e -> e != warden)) {
            warden.clearAnger(e);
        }
        warden.getBrain().eraseMemory(MemoryModuleType.ATTACK_TARGET);
        warden.getBrain().eraseMemory(MemoryModuleType.ROAR_TARGET);
        warden.getBrain().eraseMemory(MemoryModuleType.DISTURBANCE_LOCATION);
        warden.setTarget(null);
        warden.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, ticks, 1));
    }

    public static boolean isSoothed(Warden warden) {
        if (warden instanceof pryuan05.pysift.entity.mob.SiftWardenEntity) {   // 治癒後的隙浮守衛永遠平靜
            return true;
        }
        Long until = UNTIL.get(warden);
        if (until == null) {
            return false;
        }
        if (warden.level().getGameTime() >= until) {
            UNTIL.remove(warden);
            return false;
        }
        return true;
    }
}
