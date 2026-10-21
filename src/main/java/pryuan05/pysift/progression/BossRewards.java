package pryuan05.pysift.progression;

import net.minecraft.world.item.Item;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;

/**
 * Boss 掉落與重新挑戰（第 1 階段第 3 段）：
 * <ul>
 *   <li>每次擊敗必掉 1 顆<b>核心</b>（調和者核心／君王王冠／幽匿巨怪之心）與 2–4 個<b>碎片</b>
 *       （共鳴音晶／君王羽刃（ModItems.MONARCH_FEATHER）／幽匿鱗片）、3–6 個靈魂精華。掉落表由 build_progression.py 產生。</li>
 *   <li>核心會被消耗：三把 Boss 武器各用一顆，篩靈信標寶石再用三種各一顆，所以每隻 Boss 至少要打兩次。</li>
 *   <li><b>篩靈祭壇</b>（{@link SiftAltarBlock}）：放在 Boss 競技場 48 格內，手持<b>召喚印記</b>右鍵即可重新召喚該競技場的 Boss。</li>
 * </ul>
 */
public final class BossRewards {
    private static Item.Properties epic() {
        return new Item.Properties().rarity(Rarity.EPIC).stacksTo(16).fireResistant();
    }

    // ===== 核心（每次擊敗 1 顆）=====
    public static final Item HARMONIZER_CORE = ModProgression.registerItem("harmonizer_core", Item::new, epic());
    public static final Item MONARCH_CROWN = ModProgression.registerItem("monarch_crown", Item::new, epic());
    public static final Item SCULK_MONSTROSITY_HEART = ModProgression.registerItem("sculk_monstrosity_heart", Item::new, epic());

    // ===== 碎片（君王的碎片沿用 ModItems.MONARCH_FEATHER）=====
    public static final Item RESONANT_CRYSTAL = ModProgression.registerItem("resonant_crystal", Item::new,
            new Item.Properties().rarity(Rarity.UNCOMMON));
    public static final Item SCULK_SCALE = ModProgression.registerItem("sculk_scale", Item::new,
            new Item.Properties().rarity(Rarity.UNCOMMON));

    // ===== 重新挑戰 =====
    public static final Item SUMMONING_SIGIL = ModProgression.registerItem("summoning_sigil",
            p -> new HintItem(p, "tooltip.pysift.summoning_sigil.0", "tooltip.pysift.summoning_sigil.1", "tooltip.pysift.summoning_sigil.2"),
            new Item.Properties().rarity(Rarity.RARE).stacksTo(16));
    public static final Block SIFT_ALTAR = ModProgression.registerBlock("sift_altar", SiftAltarBlock::new, Blocks.LODESTONE);

    private BossRewards() {
    }

    static void load() {
    }
}
