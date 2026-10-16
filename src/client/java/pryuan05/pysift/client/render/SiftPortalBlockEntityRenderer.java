package pryuan05.pysift.client.render;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.blockentity.BlockEntityRenderer;
import net.minecraft.client.renderer.feature.ModelFeatureRenderer;
import net.minecraft.client.renderer.rendertype.RenderType;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.client.renderer.state.level.CameraRenderState;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.resources.Identifier;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;
import pryuan05.pysift.block.ModBlocks;
import pryuan05.pysift.block.SiftPortalBlock;
import pryuan05.pysift.block.entity.SiftPortalBlockEntity;

/**
 * 篩靈界傳送門的三層外觀。座標系：方塊局部 0..1；門面在 X 軸門為 z = 0.5 的平面（水平沿 x），Z 軸門為 x = 0.5（水平沿 z）。
 * <ol>
 *   <li>珠光虹彩大畫布：sift_portal_large_canvas.png（256×128）視為 16×8 格的一整張圖，每格取世界座標對應的 1/16 × 1/8，
 *       再疊兩層反向微幅正弦流動（第二層半透明），整座巨口連成一片流動的靈液。全亮半透明（entityTranslucentEmissive）。</li>
 *   <li>內側破曉光帶：緊鄰邊框的方向，從邊緣往內 0.45 格畫加法混色的漸層（暖金白 → 透明）。</li>
 *   <li>外溢聖光束：邊緣處往門的前後兩側斜向伸出 0.7～1.2 格的半透明光片，長度與角度隨時間緩慢呼吸。</li>
 * </ol>
 */
public class SiftPortalBlockEntityRenderer implements BlockEntityRenderer<SiftPortalBlockEntity, SiftPortalRenderState> {
    private static final Identifier CANVAS = Identifier.fromNamespaceAndPath("pysift", "textures/block/sift_portal_large_canvas.png");
    private static final int FULL_BRIGHT = 15728880;
    private static final float EDGE_WIDTH = 0.45f;

    @Override
    public SiftPortalRenderState createRenderState() {
        return new SiftPortalRenderState();
    }

    @Override
    public void extractRenderState(SiftPortalBlockEntity portal, SiftPortalRenderState state, float partialTick, Vec3 cameraPos,
                                   ModelFeatureRenderer.CrumblingOverlay breakProgress) {
        BlockEntityRenderer.super.extractRenderState(portal, state, partialTick, cameraPos, breakProgress);
        BlockPos pos = portal.getBlockPos();
        Level level = portal.getLevel();
        state.axis = portal.getBlockState().hasProperty(SiftPortalBlock.AXIS)
                ? portal.getBlockState().getValue(SiftPortalBlock.AXIS) : Direction.Axis.X;
        boolean x = state.axis == Direction.Axis.X;
        state.horiz = x ? pos.getX() : pos.getZ();
        state.worldY = pos.getY();
        state.seed = pos.asLong();
        state.time = level == null ? 0 : (level.getGameTime() + partialTick) * 0.003f;
        Direction minus = x ? Direction.WEST : Direction.NORTH;
        state.edgeUp = !isPortal(level, pos.above());
        state.edgeDown = !isPortal(level, pos.below());
        state.edgeMinus = !isPortal(level, pos.relative(minus));
        state.edgePlus = !isPortal(level, pos.relative(minus.getOpposite()));
    }

    private static boolean isPortal(Level level, BlockPos pos) {
        return level != null && level.getBlockState(pos).is(ModBlocks.SIFT_PORTAL);
    }

    @Override
    public void submit(SiftPortalRenderState s, PoseStack poseStack, SubmitNodeCollector collector, CameraRenderState camera) {
        collector.submitCustomGeometry(poseStack, RenderTypes.entityTranslucentEmissive(CANVAS), (pose, vc) -> canvas(s, pose, vc));
        RenderType glow = RenderTypes.lightning();
        collector.submitCustomGeometry(poseStack, glow, (pose, vc) -> {
            edgeHalo(s, pose, vc);
            godRays(s, pose, vc);
        });
    }

    // ------------------------------------------------------------------ helpers
    /** 門面上的點：h = 沿門面水平（0..1），y = 高度，d = 離門面中心的法線方向偏移。 */
    private static float[] at(SiftPortalRenderState s, float h, float y, float d) {
        return s.axis == Direction.Axis.X ? new float[]{h, y, 0.5f + d} : new float[]{0.5f + d, y, h};
    }

    private static float[] normal(SiftPortalRenderState s, float sign) {
        return s.axis == Direction.Axis.X ? new float[]{0, 0, sign} : new float[]{sign, 0, 0};
    }

    private static void texVertex(VertexConsumer vc, PoseStack.Pose pose, float[] p, int argb, float u, float v, float[] n) {
        vc.addVertex(pose, p[0], p[1], p[2]).setColor(argb).setUv(u, v).setOverlay(OverlayTexture.NO_OVERLAY)
                .setLight(FULL_BRIGHT).setNormal(pose, n[0], n[1], n[2]);
    }

    private static void colVertex(VertexConsumer vc, PoseStack.Pose pose, float[] p, int r, int g, int b, int a) {
        vc.addVertex(pose, p[0], p[1], p[2]).setColor(r, g, b, a);
    }

    /** 雙面四邊形（兩種繞向各畫一次），頂點依 a→b→c→d 環繞。 */
    private interface Corner {
        void emit(int index);
    }

    private static void doubleSided(Corner c) {
        for (int i = 0; i < 4; i++) {
            c.emit(i);
        }
        for (int i = 3; i >= 0; i--) {
            c.emit(i);
        }
    }

    // ------------------------------------------------------------------ layer 1: world-space pearlescent canvas
    private static void canvas(SiftPortalRenderState s, PoseStack.Pose pose, VertexConsumer vc) {
        float uBase = Math.floorMod(s.horiz, 16) / 16.0f;
        float vBase = Math.floorMod(-s.worldY - 1, 8) / 8.0f;   // 往下遞增，上下相鄰格接得起來
        float du = 1.0f / 16.0f, dv = 1.0f / 8.0f;
        float t = s.time;
        // 兩層反向的緩慢漂移 + 微幅正弦擺動（貼圖四方連續，UV 超出 0..1 由取樣器重複）
        float[][] layers = {
                {t * 0.6f + 0.012f * (float) Math.sin(t * 9.0), t * 0.25f + 0.010f * (float) Math.sin(t * 7.0 + 1.3), 255},
                {-t * 0.45f + 0.015f * (float) Math.sin(t * 6.0 + 2.1), -t * 0.2f + 0.012f * (float) Math.cos(t * 8.0), 120},
        };
        for (int li = 0; li < layers.length; li++) {
            float uo = layers[li][0], vo = layers[li][1];
            int alpha = (int) layers[li][2];
            int argb = (alpha << 24) | 0xFFFFFF;
            float d = li * 0.002f;   // 第二層略微前移，避免和第一層打架
            float u0 = uBase + uo, u1 = uBase + du + uo, v0 = vBase + vo, v1 = vBase + dv + vo;
            float[][] front = {at(s, 0, 1, d), at(s, 1, 1, d), at(s, 1, 0, d), at(s, 0, 0, d)};
            float[][] back = {at(s, 0, 1, -d), at(s, 1, 1, -d), at(s, 1, 0, -d), at(s, 0, 0, -d)};
            float[][] uv = {{u0, v0}, {u1, v0}, {u1, v1}, {u0, v1}};
            float[] nf = normal(s, 1), nb = normal(s, -1);
            for (int i = 0; i < 4; i++) {
                texVertex(vc, pose, front[i], argb, uv[i][0], uv[i][1], nf);
            }
            for (int i = 3; i >= 0; i--) {
                texVertex(vc, pose, back[i], argb, uv[i][0], uv[i][1], nb);
            }
        }
    }

    // ------------------------------------------------------------------ layer 2: inner dawn halo along the frame
    private static void edgeHalo(SiftPortalRenderState s, PoseStack.Pose pose, VertexConsumer vc) {
        float w = EDGE_WIDTH;
        for (float side : new float[]{0.004f, -0.004f}) {
            // 每個緊鄰邊框的方向：邊緣兩點不透明暖金白，內側兩點透明
            if (s.edgeUp) halo(vc, pose, at(s, 0, 1, side), at(s, 1, 1, side), at(s, 1, 1 - w, side), at(s, 0, 1 - w, side));
            if (s.edgeDown) halo(vc, pose, at(s, 1, 0, side), at(s, 0, 0, side), at(s, 0, w, side), at(s, 1, w, side));
            if (s.edgeMinus) halo(vc, pose, at(s, 0, 0, side), at(s, 0, 1, side), at(s, w, 1, side), at(s, w, 0, side));
            if (s.edgePlus) halo(vc, pose, at(s, 1, 1, side), at(s, 1, 0, side), at(s, 1 - w, 0, side), at(s, 1 - w, 1, side));
        }
    }

    private static void halo(VertexConsumer vc, PoseStack.Pose pose, float[] edgeA, float[] edgeB, float[] innerB, float[] innerA) {
        float[][] p = {edgeA, edgeB, innerB, innerA};
        doubleSided(i -> {
            boolean edge = i < 2;
            colVertex(vc, pose, p[i], 255, edge ? 246 : 230, edge ? 215 : 245, edge ? 220 : 0);
        });
    }

    // ------------------------------------------------------------------ layer 3: god rays spilling out of the rim
    private static void godRays(SiftPortalRenderState s, PoseStack.Pose pose, VertexConsumer vc) {
        float breathe = (float) Math.sin(s.time * 1.5f * 60.0f + (s.seed % 1000)) ;   // time 已乘 0.003，這裡放大回秒級的呼吸
        float len = 0.95f + 0.25f * breathe;                 // 0.7 ~ 1.2 格
        float tilt = 0.45f + 0.12f * breathe;                // 往外斜的比例
        for (float sign : new float[]{1, -1}) {              // 門的前、後兩側
            float out = len * sign;
            if (s.edgeUp) ray(vc, pose, at(s, 0, 1, 0), at(s, 1, 1, 0), at(s, 1, 1 + len * tilt, out), at(s, 0, 1 + len * tilt, out));
            if (s.edgeDown) ray(vc, pose, at(s, 1, 0, 0), at(s, 0, 0, 0), at(s, 0, -len * tilt, out), at(s, 1, -len * tilt, out));
            if (s.edgeMinus) ray(vc, pose, at(s, 0, 0, 0), at(s, 0, 1, 0), at(s, -len * tilt, 1, out), at(s, -len * tilt, 0, out));
            if (s.edgePlus) ray(vc, pose, at(s, 1, 1, 0), at(s, 1, 0, 0), at(s, 1 + len * tilt, 0, out), at(s, 1 + len * tilt, 1, out));
        }
    }

    private static void ray(VertexConsumer vc, PoseStack.Pose pose, float[] rootA, float[] rootB, float[] tipB, float[] tipA) {
        float[][] p = {rootA, rootB, tipB, tipA};
        doubleSided(i -> {
            boolean root = i < 2;
            colVertex(vc, pose, p[i], 255, root ? 250 : 240, root ? 225 : 200, root ? 110 : 0);
        });
    }
}
