package pryuan05.pysift.client;

import java.util.Set;
import net.fabricmc.fabric.api.client.item.v1.ItemTooltipCallback;
import net.minecraft.ChatFormatting;
import net.minecraft.client.Minecraft;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.contents.TranslatableContents;
import pryuan05.pysift.PySift;

/**
 * 物品說明太長：本模組物品的說明文字（翻譯鍵 tooltip.pysift.*）預設收起來，只顯示一行「按住 Shift 查看說明」，
 * 按住 Shift 才展開。狀態類的短行（已覺醒、羅盤目前的目標）與遠古殘頁的標題一直顯示。
 * <p>
 * 另外替兩個原版物品加一行世界觀（4.7）：強化深板岩裡砌著遠古人的骨頭、回響碎片還記得那首歌。
 */
public final class PysiftTooltips {
    /** 一直顯示的短行（狀態，不是說明）。 */
    private static final Set<String> ALWAYS_SHOWN = Set.of("tooltip.pysift.awakened");
    private static final java.util.Map<net.minecraft.world.item.Item, String> LORE = java.util.Map.ofEntries(
            java.util.Map.entry(net.minecraft.world.item.Items.REINFORCED_DEEPSLATE, "tooltip.pysift.reinforced_deepslate"),
            java.util.Map.entry(net.minecraft.world.item.Items.ECHO_SHARD, "tooltip.pysift.echo_shard"),
            java.util.Map.entry(pryuan05.pysift.block.SoulshaleFamily.CHISELED_SOULSHALE.asItem(), "tooltip.pysift.chiseled_soulshale"),
            // 故事物品（StoryItems）：用途一直顯示
            java.util.Map.entry(pryuan05.pysift.progression.StoryItems.MOURNING_HORN, "tooltip.pysift.mourning_horn"),
            java.util.Map.entry(pryuan05.pysift.progression.StoryItems.RIFT_SEAL, "tooltip.pysift.rift_seal"),
            java.util.Map.entry(pryuan05.pysift.progression.StoryItems.SIFT_HEART, "tooltip.pysift.sift_heart"),
            java.util.Map.entry(pryuan05.pysift.progression.StoryItems.LULLABY_CENSER.asItem(), "tooltip.pysift.lullaby_censer"),
            java.util.Map.entry(pryuan05.pysift.progression.AncientPages.SHERDS.get(3), "tooltip.pysift.octave_pottery_sherd"),
            java.util.Map.entry(pryuan05.pysift.progression.BossRewards.SCULK_MONSTROSITY_HEART, "tooltip.pysift.sculk_monstrosity_heart.purify"));

    private PysiftTooltips() {
    }

    public static void register() {
        ItemTooltipCallback.EVENT.register((stack, context, flag, lines) -> {
            String lore = LORE.get(stack.getItem());
            if (lore != null) {
                lines.add(Math.min(1, lines.size()), Component.translatable(lore).withStyle(ChatFormatting.DARK_AQUA, ChatFormatting.ITALIC));
                return;
            }
            if (!PySift.MOD_ID.equals(BuiltInRegistries.ITEM.getKey(stack.getItem()).getNamespace())) {
                return;
            }
            if (Minecraft.getInstance().hasShiftDown()) {
                return;
            }
            int first = -1;
            for (int i = lines.size() - 1; i >= 1; i--) {   // 第 0 行是物品名稱
                if (isDescription(lines.get(i))) {
                    lines.remove(i);
                    first = i;
                }
            }
            if (first >= 0) {
                lines.add(Math.min(first, lines.size()), Component.translatable("tooltip.pysift.hold_shift").withStyle(ChatFormatting.DARK_GRAY));
            }
        });
    }

    private static boolean isDescription(Component line) {
        return line.getContents() instanceof TranslatableContents tc
                && tc.getKey().startsWith("tooltip.pysift.")
                && !ALWAYS_SHOWN.contains(tc.getKey())
                && !tc.getKey().startsWith("tooltip.pysift.ancient_page_");
    }
}
