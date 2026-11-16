package pryuan05.pysift.client;

import net.fabricmc.fabric.api.client.render.fluid.v1.FluidRenderingRegistry;
import net.fabricmc.fabric.api.client.rendering.v1.BlockColorRegistry;
import net.minecraft.client.color.block.BlockTintSource;
import net.minecraft.client.color.block.BlockTintSources;
import net.minecraft.client.renderer.block.FluidModel;
import net.minecraft.client.resources.model.sprite.Material;
import net.minecraft.world.level.block.state.BlockState;
import pryuan05.pysift.PySift;
import pryuan05.pysift.block.ModVegetation;
import pryuan05.pysift.fluid.ModFluids;

import java.util.List;

/**
 * 植被染色與靈液渲染（靈液使用 textures/block/fluid/ 下的專屬動畫貼圖）。
 * 26.3 的 render layer 由貼圖的透明度自動判斷（cutout），垂藤、葉子不需要另外設定；靈魂柳的貼圖本身已上色，不登記染色。
 */
public final class SiftClientVisuals {
    private SiftClientVisuals() {
    }

    public static void register() {
        ModVegetation.TINTS.forEach((block, argb) ->
                BlockColorRegistry.register(List.of(BlockTintSources.constant(argb)), block));
        // 餘燼草、深淵草、蓬鬆草團：顏色依腳下地板（FloorTints 色表）
        ModVegetation.FLOOR_TINTS.forEach((block, argb) ->
                BlockColorRegistry.register(List.of(new FloorTint(argb)), block));

        FluidRenderingRegistry.register(ModFluids.SPIRIT_LIQUID, ModFluids.FLOWING_SPIRIT_LIQUID, new FluidModel.Unbaked(
                new Material(PySift.id("block/fluid/spirit_liquid_still")),
                new Material(PySift.id("block/fluid/spirit_liquid_flow")),
                new Material(PySift.id("block/fluid/spirit_liquid_overlay")),
                new SpiritLiquidTint()));
    }

    /** 靈液：貼圖本身已是彩虹星雲，並由 FluidRendererMixin 以世界座標貼成 32×32 格的連續大圖，所以不再染色（白色 = 原色）。 */
    private static final class SpiritLiquidTint implements BlockTintSource {
        @Override
        public int color(BlockState state) {
            return 0xFFFFFFFF;
        }
    }
}
