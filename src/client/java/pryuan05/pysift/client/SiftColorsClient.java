package pryuan05.pysift.client;

import net.fabricmc.fabric.api.client.rendering.v1.BlockColorRegistry;
import net.fabricmc.fabric.api.client.rendering.v1.EntityRendererRegistry;
import net.minecraft.client.color.block.BlockTintSources;
import pryuan05.pysift.block.SiftColors;

import java.util.List;

/**
 * 9 種新顏色的方塊著色：模型沿用原版白色貼圖（面上有 tintindex 0），這裡把各自的顏色乘上去。
 * 物品的著色寫在 items/*.json 的 "tints"（tools/progression/build_sift_colors.py）。
 * 另外：旗幟底色（{@link SiftBannerTint}）與坐墊實體的貼圖（{@link SiftCushionRenderer}）。
 */
public final class SiftColorsClient {
    private SiftColorsClient() {
    }

    public static void register() {
        SiftColors.TINTS.forEach((block, rgb) ->
                BlockColorRegistry.register(List.of(BlockTintSources.constant(0xFF000000 | rgb)), block));
        SiftBannerTint.register();
        EntityRendererRegistry.register(SiftColors.CUSHION_TYPE, SiftCushionRenderer::new);
    }
}
