package pryuan05.pysift.progression;

import net.minecraft.server.level.ServerPlayer;

/**
 * 靈魂剝奪的減免規則，由 {@link pryuan05.pysift.effect.SoulBurn#ignite} 查詢：
 * <ul>
 *   <li>{@link #isImmune}：完全不會被點燃（隙浮信標的光環 {@link SiftBeacon}，或穿滿靈髓套裝 {@link SouliteGear}）。</li>
 *   <li>{@link #drainRatio}：血量被抽到原本的幾倍；預設 0.2，穿滿隙浮金盔甲為 0.5。</li>
 * </ul>
 */
public final class SoulWard {
    public static final float DEFAULT_DRAIN = 0.2f;
    public static final float SIFTITE_SET_DRAIN = 0.5f;

    private SoulWard() {
    }

    public static boolean isImmune(ServerPlayer player) {
        return SiftBeacon.inAura(player) || SouliteGear.wearsFullSet(player)   // beacon aura, or a full Soulite set (self only)
                || player.hasEffect(SiftFarming.SOUL_WARD)                           // soul ward potion / soul berries
                || isWarded(player);                                                 // Soul Ward enchantment on the head or chest
    }

    /** 頭盔或胸甲帶著靈魂護佑附魔：不會被奪走靈魂（mixin/SoulWardEffectMixin 擋掉所有直接加上的靈魂剝奪）。 */
    public static boolean isWarded(net.minecraft.world.entity.LivingEntity entity) {
        var level = entity.level();
        return SiftEnchantments.level(level, entity.getItemBySlot(net.minecraft.world.entity.EquipmentSlot.HEAD), SiftEnchantments.SOUL_WARD) > 0
                || SiftEnchantments.level(level, entity.getItemBySlot(net.minecraft.world.entity.EquipmentSlot.CHEST), SiftEnchantments.SOUL_WARD) > 0;
    }

    public static float drainRatio(ServerPlayer player) {
        return SiftiteGear.wearsFullSet(player) ? SIFTITE_SET_DRAIN : DEFAULT_DRAIN;
    }
}
