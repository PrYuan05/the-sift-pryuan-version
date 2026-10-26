package pryuan05.pysift.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.serialization.Codec;
import com.mojang.serialization.DataResult;
import com.mojang.serialization.MapCodec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.blockentity.BannerRenderer;
import net.minecraft.client.renderer.special.SpecialModelRenderer;
import net.minecraft.core.component.DataComponents;
import net.minecraft.util.ARGB;
import net.minecraft.world.item.DyeColor;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.BannerBlock;
import net.minecraft.world.level.block.entity.BannerPatternLayers;
import org.joml.Vector3fc;
import pryuan05.pysift.PySift;
import pryuan05.pysift.block.SiftColors;
import pryuan05.pysift.client.mixin.SpecialModelRenderersAccessor;

import java.util.Arrays;
import java.util.Objects;
import java.util.function.Consumer;

/**
 * 篩靈界顏色的旗幟底色。原版旗幟只認 DyeColor（16 色），所以方塊上是白色旗幟，畫的時候把「底色那一層」換成篩靈界的顏色：
 * BannerRendererMixin 在畫旗幟時呼叫 {@link #begin}，畫底層（BANNER_PATTERN_BASE）時用 {@link #baseColor} 取代白色；
 * 圖案層照舊用原版染料顏色。物品欄裡的旗幟用自己的特殊模型 pysift:sift_banner（{@link Unbaked}）。
 */
public final class SiftBannerTint {
    /** 0xRRGGBB of the banner being drawn, -1 = a vanilla banner. Rendering happens on the render thread only. */
    private static int current = -1;
    /** The layer being drawn is the base cloth (not a pattern). */
    private static boolean baseLayer;

    private SiftBannerTint() {
    }

    public static void register() {
        SpecialModelRenderersAccessor.pysift$idMapper().put(PySift.id("sift_banner"), Unbaked.MAP_CODEC);
    }

    public static void begin(int rgb) {
        current = rgb;
    }

    public static void end() {
        current = -1;
    }

    public static void layer(boolean base) {
        baseLayer = base;
    }

    public static int baseColor(DyeColor color) {
        return baseLayer && current >= 0 ? ARGB.opaque(current) : color.getTextureDiffuseColor();
    }

    /** Duck interface on BannerRenderState (BannerRenderStateMixin). */
    public interface State {
        int pysift$siftTint();

        void pysift$setSiftTint(int rgb);
    }

    private static final Codec<SiftColors.SiftColor> COLOR = Codec.STRING.comapFlatMap(
            id -> Arrays.stream(SiftColors.SiftColor.values()).filter(c -> c.id.equals(id)).findFirst()
                    .map(DataResult::success).orElseGet(() -> DataResult.error(() -> "Unknown Sift colour: " + id)),
            c -> c.id);

    /** Item model {"type": "pysift:sift_banner", "color": "teal"} - vanilla's minecraft:banner with a Sift colour. */
    public record Unbaked(SiftColors.SiftColor color, BannerBlock.AttachmentType attachment)
            implements SpecialModelRenderer.Unbaked<BannerPatternLayers> {
        public static final MapCodec<Unbaked> MAP_CODEC = RecordCodecBuilder.mapCodec(i -> i.group(
                COLOR.fieldOf("color").forGetter(Unbaked::color),
                BannerBlock.AttachmentType.CODEC.optionalFieldOf("attachment", BannerBlock.AttachmentType.GROUND).forGetter(Unbaked::attachment)
        ).apply(i, Unbaked::new));

        @Override
        public MapCodec<Unbaked> type() {
            return MAP_CODEC;
        }

        @Override
        public SpecialModelRenderer<BannerPatternLayers> bake(SpecialModelRenderer.BakingContext context) {
            return new Baked(color.rgb, new BannerRenderer(context), attachment);
        }
    }

    private record Baked(int rgb, BannerRenderer renderer, BannerBlock.AttachmentType attachment)
            implements SpecialModelRenderer<BannerPatternLayers> {
        @Override
        public BannerPatternLayers extractArgument(ItemStack stack) {
            return stack.get(DataComponents.BANNER_PATTERNS);
        }

        @Override
        public void submit(BannerPatternLayers patterns, PoseStack pose, SubmitNodeCollector collector, int light, int overlay,
                           boolean foil, int outline) {
            begin(rgb);
            try {
                renderer.submitSpecial(attachment, pose, collector, light, overlay, DyeColor.WHITE,
                        Objects.requireNonNullElse(patterns, BannerPatternLayers.EMPTY), outline);
            } finally {
                end();
            }
        }

        @Override
        public void getExtents(Consumer<Vector3fc> output) {
            renderer.getExtents(output);
        }
    }
}
