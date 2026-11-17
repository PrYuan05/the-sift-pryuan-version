package pryuan05.pysift.progression;

import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.enchantment.Enchantment;
import net.minecraft.world.item.enchantment.EnchantmentHelper;
import net.minecraft.world.level.Level;
import pryuan05.pysift.PySift;

/**
 * 隙浮的附魔（資料在 data/pysift/enchantment/，連同標籤與語系由 tools/progression/build_enchantments.py 產生）。
 * 放血、纏縛、隙步、靈魂收割、靈魂撕裂完全由資料驅動；下面這些沒有資料效果，由各物品的程式讀等級：
 * <ul>
 *   <li>{@link #AFTERSHOCK} 餘震（重錘，I–III）：蓄力砸地的震波半徑每級 +0.75 格、多 1 條幽匿藤蔓。</li>
 *   <li>{@link #RESONANCE} 共振（音波法杖，I–III）：音爆射程每級 +3 格、傷害每級 +1。</li>
 *   <li>{@link #SOUL_WARD} 靈魂護佑（胸甲、頭盔）：免疫靈魂剝奪（{@link SoulWard#isWarded}）。</li>
 *   <li>{@link #AFTERIMAGE} 殘影（衝刺護符，I–III）：衝更遠、分身更久、冷卻更短。</li>
 *   <li>{@link #HARMONY} 和聲（調音叉，I–III）：共鳴範圍與再生時間。</li>
 *   <li>{@link #LAMENT} 哀歌（哀悼號角，I–III）：安撫範圍。</li>
 *   <li>{@link #HOMECOMING} 歸魂（靈魂標槍，I–III）：像三叉戟的忠誠一樣飛回來（回程速度在附魔資料裡）。</li>
 * </ul>
 * 重錘另外吃原版重錘的附魔（密度、破甲、風爆），因為它就是一把 {@link net.minecraft.world.item.MaceItem}
 * 並列在 #minecraft:enchantable/mace 裡。
 */
public final class SiftEnchantments {
    public static final ResourceKey<Enchantment> AFTERSHOCK = ResourceKey.create(Registries.ENCHANTMENT, PySift.id("aftershock"));
    public static final ResourceKey<Enchantment> RESONANCE = ResourceKey.create(Registries.ENCHANTMENT, PySift.id("resonance"));
    public static final ResourceKey<Enchantment> SOUL_WARD = ResourceKey.create(Registries.ENCHANTMENT, PySift.id("soul_ward"));
    public static final ResourceKey<Enchantment> AFTERIMAGE = ResourceKey.create(Registries.ENCHANTMENT, PySift.id("afterimage"));
    public static final ResourceKey<Enchantment> HARMONY = ResourceKey.create(Registries.ENCHANTMENT, PySift.id("harmony"));
    public static final ResourceKey<Enchantment> LAMENT = ResourceKey.create(Registries.ENCHANTMENT, PySift.id("lament"));
    public static final ResourceKey<Enchantment> HOMECOMING = ResourceKey.create(Registries.ENCHANTMENT, PySift.id("homecoming"));

    private SiftEnchantments() {
    }

    /** 創造模式分頁：每個隙浮附魔一本最高等級的附魔書，依名稱排序（資料包新增的 pysift 附魔也會出現）。 */
    public static void acceptBooks(net.minecraft.core.HolderLookup.Provider holders, net.minecraft.world.item.CreativeModeTab.Output output) {
        holders.lookup(Registries.ENCHANTMENT).ifPresent(registry -> registry.listElements()
                .filter(holder -> holder.key().identifier().getNamespace().equals(PySift.MOD_ID))
                .sorted(java.util.Comparator.comparing(holder -> holder.key().identifier().getPath()))
                .forEach(holder -> output.accept(net.minecraft.world.item.enchantment.EnchantmentHelper.createBook(
                        new net.minecraft.world.item.enchantment.EnchantmentInstance(holder, holder.value().getMaxLevel())))));
    }

    /** stack 上這個附魔的等級；沒有（或註冊表裡找不到）是 0。 */
    public static int level(Level level, ItemStack stack, ResourceKey<Enchantment> key) {
        return level.registryAccess().lookup(Registries.ENCHANTMENT)
                .flatMap(registry -> registry.get(key))
                .map(holder -> EnchantmentHelper.getItemEnchantmentLevel(holder, stack))
                .orElse(0);
    }
}
