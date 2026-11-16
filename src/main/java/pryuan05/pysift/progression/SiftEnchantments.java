package pryuan05.pysift.progression;

import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.enchantment.Enchantment;
import net.minecraft.world.item.enchantment.EnchantmentHelper;
import net.minecraft.world.level.Level;
import pryuan05.pysift.PySift;

/**
 * 隙浮武器自己的附魔（資料在 data/pysift/enchantment/，由 tools/progression/build_progression.py 維護標籤與語系）。
 * 附魔本身沒有資料驅動的效果，由各武器的程式讀等級：
 * <ul>
 *   <li>{@link #AFTERSHOCK} 餘震（重錘，I–III）：蓄力砸地的震波半徑每級 +0.75 格、多 1 條幽匿藤蔓。</li>
 *   <li>{@link #RESONANCE} 共振（音波法杖，I–III）：音爆射程每級 +3 格、傷害每級 +1。</li>
 * </ul>
 * 重錘另外吃原版重錘的附魔（密度、破甲、風爆），因為它就是一把 {@link net.minecraft.world.item.MaceItem}
 * 並列在 #minecraft:enchantable/mace 裡。
 */
public final class SiftEnchantments {
    public static final ResourceKey<Enchantment> AFTERSHOCK = ResourceKey.create(Registries.ENCHANTMENT, PySift.id("aftershock"));
    public static final ResourceKey<Enchantment> RESONANCE = ResourceKey.create(Registries.ENCHANTMENT, PySift.id("resonance"));

    private SiftEnchantments() {
    }

    /** stack 上這個附魔的等級；沒有（或註冊表裡找不到）是 0。 */
    public static int level(Level level, ItemStack stack, ResourceKey<Enchantment> key) {
        return level.registryAccess().lookup(Registries.ENCHANTMENT)
                .flatMap(registry -> registry.get(key))
                .map(holder -> EnchantmentHelper.getItemEnchantmentLevel(holder, stack))
                .orElse(0);
    }
}
