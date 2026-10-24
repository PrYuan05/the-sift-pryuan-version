package pryuan05.pysift.client.render;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.block.BlockModelRenderState;
import net.minecraft.client.renderer.block.BlockModelResolver;
import net.minecraft.client.renderer.block.model.BlockDisplayContext;
import net.minecraft.client.renderer.blockentity.BeaconRenderer;
import net.minecraft.client.renderer.blockentity.BlockEntityRenderer;
import net.minecraft.client.renderer.blockentity.BlockEntityRendererProvider;
import net.minecraft.client.renderer.feature.ModelFeatureRenderer;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.client.renderer.state.level.CameraRenderState;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.JukeboxBlock;
import net.minecraft.world.phys.Vec3;
import pryuan05.pysift.block.RitualDiscs;
import pryuan05.pysift.block.entity.ResonantJukeboxBlockEntity;

/**
 * 共鳴唱片盒：方塊本身不畫模型（RenderShape.INVISIBLE），由這裡畫原版唱片盒的模型，才能做動畫。
 * <ul>
 *   <li>出現：放下後 30 tick 內從地面下升起、由小變大並轉一圈。</li>
 *   <li>還沒放唱片：盒頂浮著這個位置要的唱片的半透明虛影（8 個唱片盒一起看，就是整套唱片的順序）。</li>
 *   <li>放入唱片後：虛影消失，射出該唱片顏色的信標光柱（終曲時閃亮變粗）。</li>
 * </ul>
 */
public class ResonantJukeboxRenderer implements BlockEntityRenderer<ResonantJukeboxBlockEntity, ResonantJukeboxRenderer.ResonantJukeboxRenderState> {
    private static final int RISE_TICKS = 30;
    private static final int FLASH_TICKS = 16;
    private final BlockModelResolver blockModels;

    public ResonantJukeboxRenderer(BlockEntityRendererProvider.Context context) {
        this.blockModels = context.blockModelResolver();
    }

    @Override
    public ResonantJukeboxRenderState createRenderState() {
        return new ResonantJukeboxRenderState();
    }

    @Override
    public void extractRenderState(ResonantJukeboxBlockEntity box, ResonantJukeboxRenderState state, float partialTick, Vec3 cameraPos,
                                   ModelFeatureRenderer.CrumblingOverlay breakProgress) {
        BlockEntityRenderer.super.extractRenderState(box, state, partialTick, cameraPos, breakProgress);
        Level level = box.getLevel();
        float now = level == null ? 0 : level.getGameTime() + partialTick;
        state.time = now;
        state.rise = Math.min(1.0f, Math.max(0.0f, (now - box.getPlacedAt()) / RISE_TICKS));
        state.flash = Math.max(0.0f, 1.0f - (now - box.getFlashAt()) / FLASH_TICKS);
        RitualDiscs.Disc disc = box.getRitualDisc();
        RitualDiscs.Disc wanted = box.expectedDisc();
        state.color = disc == null ? 0 : disc.color();
        state.hintColor = wanted == null ? 0 : wanted.color();
        if (wanted == null) {
            state.ghostTexture = null;
        } else {
            net.minecraft.resources.Identifier id = net.minecraft.core.registries.BuiltInRegistries.ITEM.getKey(wanted.item());
            state.ghostTexture = id.withPath("textures/item/" + id.getPath() + ".png");
        }
        state.hasDisc = disc != null;
        blockModels.update(state.block, Blocks.JUKEBOX.defaultBlockState().setValue(JukeboxBlock.HAS_RECORD, state.hasDisc),
                BlockDisplayContext.create());
    }

    @Override
    public void submit(ResonantJukeboxRenderState s, PoseStack poseStack, SubmitNodeCollector collector, CameraRenderState camera) {
        // 1. 唱片盒本體：升起 + 放大 + 轉一圈（ease-out）
        float t = 1.0f - (1.0f - s.rise) * (1.0f - s.rise);
        poseStack.pushPose();
        poseStack.translate(0.5f, -1.0f + t, 0.5f);
        poseStack.rotateDegrees(Axis.YP, (1.0f - t) * 360.0f);
        float scale = 0.2f + 0.8f * t;
        poseStack.scale(scale, scale, scale);
        poseStack.translate(-0.5f, 0.0f, -0.5f);
        s.block.submit(poseStack, collector, s.lightCoords, OverlayTexture.NO_OVERLAY, 0);
        poseStack.popPose();

        if (s.rise < 1.0f) {
            return;
        }
        if (!s.hasDisc) {   // 還沒放唱片：盒頂浮著這個位置要的唱片的半透明虛影
            if (s.ghostTexture != null) {
                poseStack.pushPose();
                poseStack.translate(0.5f, 1.35f + 0.06f * (float) Math.sin(s.time * 0.08f), 0.5f);
                poseStack.rotateDegrees(Axis.YP, s.time * 2.0f);
                collector.submitCustomGeometry(poseStack, RenderTypes.entityTranslucent(s.ghostTexture), (pose, vc) -> ghostDisc(pose, vc));
                poseStack.popPose();
            }
            return;
        }
        // 3. 彩色光柱（終曲時變粗變亮）
        float radius = 1.0f + 1.5f * s.flash;
        int color = s.flash > 0 ? brighten(s.color, s.flash) : s.color;
        BeaconRenderer.submitBeaconBeam(poseStack, collector, BeaconRenderer.BEAM_LOCATION, 1.0f, s.time, 1, BeaconRenderer.MAX_RENDER_Y,
                color, 0.2f * radius, 0.25f * radius);
    }

    /** 半透明的唱片圖（正反兩面），0.6 格寬。 */
    private static void ghostDisc(PoseStack.Pose pose, com.mojang.blaze3d.vertex.VertexConsumer vc) {
        float h = 0.3f;
        int argb = 0x90FFFFFF;
        float[][] front = {{-h, -h, 0}, {h, -h, 0}, {h, h, 0}, {-h, h, 0}};
        float[][] uv = {{0, 1}, {1, 1}, {1, 0}, {0, 0}};
        for (int i = 0; i < 4; i++) {
            vc.addVertex(pose, front[i][0], front[i][1], front[i][2]).setColor(argb).setUv(uv[i][0], uv[i][1])
                    .setOverlay(OverlayTexture.NO_OVERLAY).setLight(0xF000F0).setNormal(pose, 0, 0, 1);
        }
        for (int i = 3; i >= 0; i--) {
            vc.addVertex(pose, front[i][0], front[i][1], front[i][2]).setColor(argb).setUv(uv[i][0], uv[i][1])
                    .setOverlay(OverlayTexture.NO_OVERLAY).setLight(0xF000F0).setNormal(pose, 0, 0, -1);
        }
    }

    private static int dim(int argb) {
        int r = ((argb >> 16) & 0xFF) / 2, g = ((argb >> 8) & 0xFF) / 2, b = (argb & 0xFF) / 2;
        return 0xFF000000 | (r << 16) | (g << 8) | b;
    }

    private static int brighten(int argb, float k) {
        int r = (argb >> 16) & 0xFF, g = (argb >> 8) & 0xFF, b = argb & 0xFF;
        r += (int) ((255 - r) * k * 0.7f);
        g += (int) ((255 - g) * k * 0.7f);
        b += (int) ((255 - b) * k * 0.7f);
        return 0xFF000000 | (r << 16) | (g << 8) | b;
    }

    @Override
    public boolean shouldRenderOffScreen() {
        return true;
    }

    @Override
    public int getViewDistance() {
        return 256;
    }

    /** ResonantJukeboxRenderer 的渲染狀態。 */
    public static class ResonantJukeboxRenderState extends net.minecraft.client.renderer.blockentity.state.BlockEntityRenderState {
        public final BlockModelRenderState block = new BlockModelRenderState();
        public float time;
        public float rise;
        public float flash;
        public int color;
        public int hintColor;
        public net.minecraft.resources.Identifier ghostTexture;
        public boolean hasDisc;
    }
}
