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
import net.minecraft.resources.Identifier;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;
import pryuan05.pysift.block.ModBlocks;
import pryuan05.pysift.block.entity.SiftPortalBlockEntity;

/**
 * 隙浮傳送門完整方塊渲染器。
 * <ol>
 *   <li>亮白珠光大畫布：對所有未被同類方塊遮擋的暴露面（前後左右上下），
 *       以世界座標連續對齊取樣並疊加兩層反向正弦流光；法線統一頂向天頂，消除水平漫反射陰暗。</li>
 *   <li>內側破曉金白光環：沿暴露面外圍邊緣向內漸層發光。</li>
 *   <li>外溢聖光束：向傳送門外側空域輻射，不遮擋門面本體。</li>
 *   <li>夜晚：光芒拉長、邊框轉粉金，門前後浮出一層光霧，地上鋪一片光。</li>
 * </ol>
 */
public class SiftPortalBlockEntityRenderer implements BlockEntityRenderer<SiftPortalBlockEntity, SiftPortalRenderState> {
    private static final Identifier CANVAS = Identifier.fromNamespaceAndPath("pysift", "textures/block/sift_portal_large_canvas.png");
    private static final int FULL_BRIGHT = 15728880;
    private static final float EDGE_WIDTH = 0.40f;

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
        state.worldX = pos.getX();
        state.worldY = pos.getY();
        state.worldZ = pos.getZ();
        state.seed = pos.asLong();
        state.time = level == null ? 0 : (level.getGameTime() + partialTick) * 0.003f;
        state.night = pryuan05.pysift.block.SiftDayPhase.night(level);   // 夜晚：更亮、偏粉紅與金黃
        state.faceUp = !isPortal(level, pos.above());
        state.faceDown = !isPortal(level, pos.below());
        state.faceNorth = !isPortal(level, pos.north());
        state.faceSouth = !isPortal(level, pos.south());
        state.faceWest = !isPortal(level, pos.west());
        state.faceEast = !isPortal(level, pos.east());
        // 被門框（不透光的整塊）貼住的面看不到，畫布就不畫（邊框光仍然要知道哪裡是邊）
        state.covered = 0;
        net.minecraft.core.Direction[] dirs = net.minecraft.core.Direction.values();
        for (int i = 0; i < dirs.length; i++) {
            if (level != null && level.getBlockState(pos.relative(dirs[i])).canOcclude()) {
                state.covered |= 1 << dirs[i].ordinal();
            }
        }
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
            nightGlow(s, pose, vc);
        });
    }

    // 效能：這個渲染器每一格傳送門、每一幀都會跑，所以頂點直接寫進 VertexConsumer，不建立任何暫時陣列。

    private static int argb(int a, int r, int g, int b) {
        return Math.clamp(a, 0, 255) << 24 | r << 16 | g << 8 | b;
    }

    // ------------------------------------------------------------------ layer 1: world-space pearlescent canvas
    private static void canvas(SiftPortalRenderState s, PoseStack.Pose pose, VertexConsumer vc) {
        float t = s.time;
        int g = (int) (255 - 70 * s.night), b = (int) (255 - 35 * s.night);
        for (int li = 0; li < 2; li++) {
            float uo = li == 0 ? t * 0.6f + 0.012f * (float) Math.sin(t * 9.0) : -t * 0.45f + 0.015f * (float) Math.sin(t * 6.0 + 2.1);
            float vo = li == 0 ? t * 0.25f + 0.010f * (float) Math.sin(t * 7.0 + 1.3) : -t * 0.2f + 0.012f * (float) Math.cos(t * 8.0);
            int color = argb((int) ((li == 0 ? 255 : 120) * (1.0f + 0.35f * s.night)), 255, g, b);
            float d = li * 0.002f;
            float yV = Math.floorMod(-s.worldY - 1, 8) / 8.0f + vo;
            if (s.faceSouth && visible(s, net.minecraft.core.Direction.SOUTH)) {
                float u = Math.floorMod(s.worldX, 16) / 16.0f + uo, z = 1.0f - d;
                texQuad(vc, pose, color, u, yV, 0, 1, z, 1, 1, z, 1, 0, z, 0, 0, z);
            }
            if (s.faceNorth && visible(s, net.minecraft.core.Direction.NORTH)) {
                float u = Math.floorMod(-s.worldX - 1, 16) / 16.0f + uo;
                texQuad(vc, pose, color, u, yV, 1, 1, d, 0, 1, d, 0, 0, d, 1, 0, d);
            }
            if (s.faceEast && visible(s, net.minecraft.core.Direction.EAST)) {
                float u = Math.floorMod(-s.worldZ - 1, 16) / 16.0f + uo, x = 1.0f - d;
                texQuad(vc, pose, color, u, yV, x, 1, 1, x, 1, 0, x, 0, 0, x, 0, 1);
            }
            if (s.faceWest && visible(s, net.minecraft.core.Direction.WEST)) {
                float u = Math.floorMod(s.worldZ, 16) / 16.0f + uo;
                texQuad(vc, pose, color, u, yV, d, 1, 0, d, 1, 1, d, 0, 1, d, 0, 0);
            }
            if (s.faceUp && visible(s, net.minecraft.core.Direction.UP)) {
                float u = Math.floorMod(s.worldX, 16) / 16.0f + uo, v = Math.floorMod(s.worldZ, 8) / 8.0f + vo, y = 1.0f - d;
                texQuad(vc, pose, color, u, v, 0, y, 0, 1, y, 0, 1, y, 1, 0, y, 1);
            }
            if (s.faceDown && visible(s, net.minecraft.core.Direction.DOWN)) {
                float u = Math.floorMod(s.worldX, 16) / 16.0f + uo, v = Math.floorMod(-s.worldZ - 1, 8) / 8.0f + vo;
                texQuad(vc, pose, color, u, v, 0, d, 1, 1, d, 1, 1, d, 0, 0, d, 0);
            }
        }
    }

    private static boolean visible(SiftPortalRenderState s, net.minecraft.core.Direction face) {
        return (s.covered & 1 << face.ordinal()) == 0;
    }

    /** 貼圖四邊形：(u0, v0) 起算 1/16 × 1/8 的一格貼圖；法線統一朝上（消除水平漫反射陰暗）。 */
    private static void texQuad(VertexConsumer vc, PoseStack.Pose pose, int color, float u0, float v0,
                                float x0, float y0, float z0, float x1, float y1, float z1,
                                float x2, float y2, float z2, float x3, float y3, float z3) {
        float u1 = u0 + 1.0f / 16.0f, v1 = v0 + 1.0f / 8.0f;
        texVertex(vc, pose, x0, y0, z0, color, u0, v0);
        texVertex(vc, pose, x1, y1, z1, color, u1, v0);
        texVertex(vc, pose, x2, y2, z2, color, u1, v1);
        texVertex(vc, pose, x3, y3, z3, color, u0, v1);
    }

    private static void texVertex(VertexConsumer vc, PoseStack.Pose pose, float x, float y, float z, int color, float u, float v) {
        vc.addVertex(pose, x, y, z).setColor(color).setUv(u, v).setOverlay(OverlayTexture.NO_OVERLAY)
                .setLight(FULL_BRIGHT).setNormal(pose, 0, 1, 0);
    }

    // ------------------------------------------------------------------ shared: the portal's own frame of reference
    /** 門面沿 X 軸（南北兩面露出）還是沿 Z 軸（東西兩面露出）。 */
    private static boolean axisX(SiftPortalRenderState s) {
        return s.faceSouth || s.faceNorth;
    }

    /** 門面左（u = 0）、右（u = 1）兩側是否露出。 */
    private static boolean leftOpen(SiftPortalRenderState s) {
        return axisX(s) ? s.faceWest : s.faceNorth;
    }

    private static boolean rightOpen(SiftPortalRenderState s) {
        return axisX(s) ? s.faceEast : s.faceSouth;
    }

    /** 門面座標的一個頂點：u 沿門面、y 往上、w 沿法線（0 = 背面、1 = 正面）。 */
    private static void vertex(VertexConsumer vc, PoseStack.Pose pose, boolean axisX, float u, float y, float w, int color) {
        if (axisX) {
            vc.addVertex(pose, u, y, w).setColor(color);
        } else {
            vc.addVertex(pose, w, y, u).setColor(color);
        }
    }

    /**
     * 門面座標的四邊形，前兩個頂點用 inner、後兩個用outer（漸層）；正反兩面都畫，背面會被剔除，只多花頂點不多花填色。
     */
    private static void quad(VertexConsumer vc, PoseStack.Pose pose, boolean ax, int inner, int outer,
                             float u0, float y0, float w0, float u1, float y1, float w1,
                             float u2, float y2, float w2, float u3, float y3, float w3) {
        vertex(vc, pose, ax, u0, y0, w0, inner);
        vertex(vc, pose, ax, u1, y1, w1, inner);
        vertex(vc, pose, ax, u2, y2, w2, outer);
        vertex(vc, pose, ax, u3, y3, w3, outer);
        vertex(vc, pose, ax, u3, y3, w3, outer);
        vertex(vc, pose, ax, u2, y2, w2, outer);
        vertex(vc, pose, ax, u1, y1, w1, inner);
        vertex(vc, pose, ax, u0, y0, w0, inner);
    }

    // ------------------------------------------------------------------ layer 2: inner dawn halo along borders
    private static void edgeHalo(SiftPortalRenderState s, PoseStack.Pose pose, VertexConsumer vc) {
        boolean ax = axisX(s), left = leftOpen(s), right = rightOpen(s);
        if (!s.faceUp && !s.faceDown && !left && !right) {
            return;   // 門中間的格子沒有邊框光
        }
        float n = s.night;   // 夜晚：邊緣變成粉紅色，內側透出金黃（影片中夜裡浮現的門）
        float w = EDGE_WIDTH + 0.25f * n;
        int edge = argb((int) (220 + 35 * n), 255, (int) (246 - 116 * n), (int) (215 - 15 * n));
        int inner = argb((int) (140 * n), 255, (int) (230 - 10 * n), (int) (245 - 165 * n));
        for (int side = 0; side < 2; side++) {
            float d = side == 0 ? 1.001f : -0.001f;
            if (s.faceUp) quad(vc, pose, ax, edge, inner, 0, 1, d, 1, 1, d, 1, 1 - w, d, 0, 1 - w, d);
            if (s.faceDown) quad(vc, pose, ax, edge, inner, 1, 0, d, 0, 0, d, 0, w, d, 1, w, d);
            if (left) quad(vc, pose, ax, edge, inner, 0, 0, d, 0, 1, d, w, 1, d, w, 0, d);
            if (right) quad(vc, pose, ax, edge, inner, 1, 1, d, 1, 0, d, 1 - w, 0, d, 1 - w, 1, d);
        }
    }

    // ------------------------------------------------------------------ layer 3: god rays spilling out of the rim
    private static void godRays(SiftPortalRenderState s, PoseStack.Pose pose, VertexConsumer vc) {
        boolean ax = axisX(s), left = leftOpen(s), right = rightOpen(s);
        if (!s.faceUp && !s.faceDown && !left && !right) {
            return;
        }
        float n = s.night;
        float breathe = (float) Math.sin(s.time * 1.5f * 60.0f + (s.seed % 1000));
        float len = (0.85f + 0.20f * breathe) * (1.0f + 2.0f * n);   // 夜晚光芒長到快三倍
        int root = argb((int) (110 + 120 * n), 255, (int) (250 - 90 * n), (int) (225 + 10 * n));
        int tip = argb(0, 255, (int) (240 - 80 * n), (int) (200 + 30 * n));
        for (int side = 0; side < 2; side++) {
            float d = side == 0 ? 1.0f : 0.0f;
            float out = side == 0 ? d + 0.15f + 0.25f * n : d - 0.15f - 0.25f * n;
            if (s.faceUp) quad(vc, pose, ax, root, tip, 0, 1, d, 1, 1, d, 1, 1 + len, out, 0, 1 + len, out);
            if (s.faceDown) quad(vc, pose, ax, root, tip, 1, 0, d, 0, 0, d, 0, -len, out, 1, -len, out);
            if (left) quad(vc, pose, ax, root, tip, 0, 0, d, 0, 1, d, -len, 1, out, -len, 0, out);
            if (right) quad(vc, pose, ax, root, tip, 1, 1, d, 1, 0, d, 1 + len, 0, out, 1 + len, 1, out);
        }
    }

    // ------------------------------------------------------------------ layer 4 (night only): glow haze and ground light
    /**
     * 入夜後門前後各浮出一層粉金色的光霧，外緣往外淡出；最底下一排還會在地上鋪一片往外淡出的光（照亮門前的台階）。
     * 效能：光霧只有一層（整面半透明的層數越多，貼近門時要填的像素越多）。
     */
    private static void nightGlow(SiftPortalRenderState s, PoseStack.Pose pose, VertexConsumer vc) {
        float n = s.night;
        if (n <= 0.02f) {
            return;
        }
        boolean ax = axisX(s), left = leftOpen(s), right = rightOpen(s);
        float pulse = 0.8f + 0.2f * (float) Math.sin(s.time * 60.0f + (s.seed % 997) * 0.01f);
        float fade = 0.9f;   // 外緣淡出的寬度
        int in = argb((int) (95 * n * pulse), 255, 150, 220);
        int out = argb(0, 255, 190, 150);
        for (int side = 0; side < 2; side++) {
            float d = side == 0 ? 1.45f : -0.45f;
            quad(vc, pose, ax, in, in, 0, 0, d, 1, 0, d, 1, 1, d, 0, 1, d);
            if (s.faceUp) quad(vc, pose, ax, in, out, 0, 1, d, 1, 1, d, 1, 1 + fade, d, 0, 1 + fade, d);
            if (left) quad(vc, pose, ax, in, out, 0, 0, d, 0, 1, d, -fade, 1, d, -fade, 0, d);
            if (right) quad(vc, pose, ax, in, out, 1, 1, d, 1, 0, d, 1 + fade, 0, d, 1 + fade, 1, d);
        }
        if (s.faceDown) {
            int root = argb((int) (150 * n * pulse), 255, 170, 225);
            int tip = argb(0, 255, 210, 160);
            float y = 0.02f, reach = 3.0f;
            float l = left ? -0.6f : 0.0f, r = right ? 1.6f : 1.0f;
            quad(vc, pose, ax, root, tip, l, y, 1, r, y, 1, r, y, 1 + reach, l, y, 1 + reach);
            quad(vc, pose, ax, root, tip, l, y, 0, r, y, 0, r, y, -reach, l, y, -reach);
        }
    }
}
