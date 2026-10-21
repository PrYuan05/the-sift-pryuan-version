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
 * 按住 Shift 才展開。狀態類的短行（已覺醒、羅盤目前的目標）一直顯示。
 */
public final class PysiftTooltips {
    /** 一直顯示的短行（狀態，不是說明）。 */
    private static final Set<String> ALWAYS_SHOWN = Set.of("tooltip.pysift.awakened");

    private PysiftTooltips() {
    }

    public static void register() {
        ItemTooltipCallback.EVENT.register((stack, context, flag, lines) -> {
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
                && !ALWAYS_SHOWN.contains(tc.getKey());
    }
}
