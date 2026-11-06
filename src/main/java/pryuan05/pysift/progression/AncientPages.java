package pryuan05.pysift.progression;

import net.fabricmc.fabric.api.loot.v3.LootTableEvents;
import net.minecraft.ChatFormatting;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.server.network.Filterable;
import net.minecraft.stats.Stats;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.component.TooltipDisplay;
import net.minecraft.world.item.component.WrittenBookContent;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.storage.loot.LootPool;
import net.minecraft.world.level.storage.loot.entries.EmptyLootItem;
import net.minecraft.world.level.storage.loot.entries.LootItem;
import net.minecraft.world.level.storage.loot.providers.number.ints.ConstantValue;
import pryuan05.pysift.PySift;

import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.function.Consumer;

/**
 * 遠古殘頁（世界觀 4.7）：8 張，各寫著一段當年的故事。撿起來時隙浮手記（Modonomicon 書 pysift:sift_codex）
 * 對應的條目會解鎖，手持右鍵可以像書一樣直接讀。
 * <ul>
 *   <li>其一～其四：遠古人寫的，放在原版遠古城市的箱子（約一半的箱子有一張）。</li>
 *   <li>其五～其七：歌者的歌，放在隙浮遺跡的箱子（約一半）；迴音巢穴的寶庫一定有一張。</li>
 *   <li>其八：幽匿巨怪身上一定帶著。</li>
 * </ul>
 * 文字與手記的內容由 tools/progression/build_codex.py 產生（語系 book.pysift.ancient_page_N.pageM）。
 */
public final class AncientPages {
    /** 每張殘頁的頁數（和 build_codex.py 的 PAGES 一致）。 */
    private static final int[] PAGE_LENGTHS = {2, 1, 2, 2, 2, 2, 1, 2};
    public static final List<Item> PAGES = new ArrayList<>();

    static {
        for (int i = 1; i <= PAGE_LENGTHS.length; i++) {
            PAGES.add(ModProgression.registerItem("ancient_page_" + i, AncientPageItem::new, properties(i)));
        }
    }

    /**
     * 遠古陶片（§4.7）：遠古人把那場災難刻在陶器上。可以像原版陶片一樣拼成飾紋陶罐（圖案在 data/pysift/decorated_pot_pattern/）。
     * 門扉＝被撕開的門框、歌者、親族＝監守者、八音＝八根長條的高度就是正確的開門順序 1 3 7 6 5 2 4 8。
     * 貼圖與資料：tools/progression/build_story.py。
     */
    public static final List<String> SHERD_NAMES = List.of("gate", "singer", "kin", "octave");
    public static final List<Item> SHERDS = new ArrayList<>();

    static {
        for (String name : SHERD_NAMES) {
            net.minecraft.resources.ResourceKey<net.minecraft.world.level.block.entity.DecoratedPotPattern> pattern =
                    net.minecraft.resources.ResourceKey.create(net.minecraft.core.registries.Registries.DECORATED_POT_PATTERN, PySift.id(name));
            SHERDS.add(ModProgression.registerItem(name + "_pottery_sherd", Item::new,
                    new Item.Properties().rarity(Rarity.UNCOMMON).potPattern(pattern)));
        }
    }

    private static final Set<String> SIFT_RUINS = Set.of("lullaby_shrine", "willow_hut", "strata_shrine", "abyss_obelisk",
            "dune_tomb", "echo_den");

    private AncientPages() {
    }

    private static Item.Properties properties(int index) {
        List<Filterable<Component>> pages = new ArrayList<>();
        for (int n = 1; n <= PAGE_LENGTHS[index - 1]; n++) {
            pages.add(Filterable.passThrough(Component.translatable("book.pysift.ancient_page_" + index + ".page" + n)));
        }
        return new Item.Properties().stacksTo(16).rarity(Rarity.UNCOMMON)
                .component(DataComponents.WRITTEN_BOOK_CONTENT,
                        new WrittenBookContent(Filterable.passThrough("Ancient Page"), "?", 3, pages, true))
                .component(DataComponents.TOOLTIP_DISPLAY, TooltipDisplay.DEFAULT.withHidden(DataComponents.WRITTEN_BOOK_CONTENT, true));
    }

    static void load() {
        LootTableEvents.MODIFY.register((key, table, source, registries) -> {
            Identifier id = key.identifier();
            if (id.equals(Identifier.withDefaultNamespace("chests/ancient_city"))) {
                table.withPool(pool(PAGES.subList(0, 4), 4));
                table.withPool(pool(SHERDS, 8));
            } else if (id.getNamespace().equals("pysift") && id.getPath().startsWith("chests/")) {
                String chest = id.getPath().substring("chests/".length());
                if (chest.equals("echo_den_vault")) {
                    table.withPool(pool(PAGES.subList(4, 7), 0));
                } else if (SIFT_RUINS.contains(chest)) {
                    table.withPool(pool(PAGES.subList(4, 7), 3));
                    table.withPool(pool(SHERDS, 8));
                }
            } else if (id.equals(PySift.id("entities/sculk_monstrosity"))) {
                table.withPool(pool(PAGES.subList(7, 8), 0));
            }
        });
    }

    /** 一個抽一次的池子：每張殘頁權重 1，再加上 empty 權重的「什麼都沒有」。 */
    private static LootPool.Builder pool(List<Item> pages, int empty) {
        LootPool.Builder pool = LootPool.lootPool().setRolls(net.minecraft.core.Holder.direct(new ConstantValue(1)));
        for (Item page : pages) {
            pool.add(LootItem.lootTableItem(page).setWeight(1));
        }
        if (empty > 0) {
            pool.add(EmptyLootItem.emptyItem().setWeight(empty));
        }
        return pool;
    }

    /** 右鍵像成書一樣打開來讀（客戶端只看物品上的 WRITTEN_BOOK_CONTENT，不看物品種類）。 */
    public static class AncientPageItem extends Item {
        public AncientPageItem(Properties properties) {
            super(properties);
        }

        @Override
        public InteractionResult use(Level level, Player player, InteractionHand hand) {
            player.openItemGui(player.getItemInHand(hand), hand);
            player.awardStat(Stats.ITEM_USED.get(this));
            return InteractionResult.SUCCESS;
        }

        @Override
        public void appendHoverText(ItemStack stack, TooltipContext context, TooltipDisplay display, Consumer<Component> out, TooltipFlag flag) {
            out.accept(Component.translatable("tooltip.pysift." + BuiltInRegistries.ITEM.getKey(this).getPath()).withStyle(ChatFormatting.DARK_AQUA, ChatFormatting.ITALIC));
            out.accept(Component.translatable("tooltip.pysift.ancient_page.use").withStyle(ChatFormatting.GRAY));
        }
    }
}
