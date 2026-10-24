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
 * 篩靈界傳送門完整方塊渲染器。
 * <ol>
 *   <li>亮白珠光大畫布：對所有未被同類方塊遮擋的暴露面（前後左右上下），
 *       以世界座標連續對齊取樣並疊加兩層反向正弦流光；法線統一頂向天頂，消除水平漫反射陰暗。</li>
 *   <li>內側破曉金白光環：沿暴露面外圍邊緣向內漸層發光。</li>
 *   <li>外溢聖光束：向傳送門外側空域輻射，不遮擋門面本體。</li>
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

    private static void texVertex(VertexConsumer vc, PoseStack.Pose pose, float[] p, int argb, float u, float v, float[] n) {
        vc.addVertex(pose, p[0], p[1], p[2]).setColor(argb).setUv(u, v).setOverlay(OverlayTexture.NO_OVERLAY)
                .setLight(FULL_BRIGHT).setNormal(pose, n[0], n[1], n[2]);
    }

    private static void colVertex(VertexConsumer vc, PoseStack.Pose pose, float[] p, int r, int g, int b, int a) {
        vc.addVertex(pose, p[0], p[1], p[2]).setColor(r, g, b, a);
    }

    // ------------------------------------------------------------------ layer 1: world-space pearlescent canvas
    private static void canvas(SiftPortalRenderState s, PoseStack.Pose pose, VertexConsumer vc) {
        float du = 1.0f / 16.0f, dv = 1.0f / 8.0f;
        float t = s.time;
        float[][] layers = {
                {t * 0.6f + 0.012f * (float) Math.sin(t * 9.0), t * 0.25f + 0.010f * (float) Math.sin(t * 7.0 + 1.3), 255},
                {-t * 0.45f + 0.015f * (float) Math.sin(t * 6.0 + 2.1), -t * 0.2f + 0.012f * (float) Math.cos(t * 8.0), 120},
        };
        float[] fullNormal = {0, 1, 0};

        for (int li = 0; li < layers.length; li++) {
            float uo = layers[li][0], vo = layers[li][1];
            int alpha = (int) Math.min(255, layers[li][2] * (1.0f + 0.35f * s.night));
            int g = (int) (255 - 70 * s.night), b = (int) (255 - 35 * s.night);
            int argb = (alpha << 24) | (255 << 16) | (g << 8) | b;
            float d = li * 0.002f;

            // 1. 南面 (South, Z = 1)
            if (s.faceSouth) {
                float uBase = Math.floorMod(s.worldX, 16) / 16.0f;
                float vBase = Math.floorMod(-s.worldY - 1, 8) / 8.0f;
                float u0 = uBase + uo, u1 = u0 + du, v0 = vBase + vo, v1 = v0 + dv;
                float z = 1.0f - d;
                quad(vc, pose, new float[][]{{0, 1, z}, {1, 1, z}, {1, 0, z}, {0, 0, z}}, argb, u0, u1, v0, v1, fullNormal);
            }
            // 2. 北面 (North, Z = 0)
            if (s.faceNorth) {
                float uBase = Math.floorMod(-s.worldX - 1, 16) / 16.0f;
                float vBase = Math.floorMod(-s.worldY - 1, 8) / 8.0f;
                float u0 = uBase + uo, u1 = u0 + du, v0 = vBase + vo, v1 = v0 + dv;
                float z = d;
                quad(vc, pose, new float[][]{{1, 1, z}, {0, 1, z}, {0, 0, z}, {1, 0, z}}, argb, u0, u1, v0, v1, fullNormal);
            }
            // 3. 東面 (East, X = 1)
            if (s.faceEast) {
                float uBase = Math.floorMod(-s.worldZ - 1, 16) / 16.0f;
                float vBase = Math.floorMod(-s.worldY - 1, 8) / 8.0f;
                float u0 = uBase + uo, u1 = u0 + du, v0 = vBase + vo, v1 = v0 + dv;
                float x = 1.0f - d;
                quad(vc, pose, new float[][]{{x, 1, 1}, {x, 1, 0}, {x, 0, 0}, {x, 0, 1}}, argb, u0, u1, v0, v1, fullNormal);
            }
            // 4. 西面 (West, X = 0)
            if (s.faceWest) {
                float uBase = Math.floorMod(s.worldZ, 16) / 16.0f;
                float vBase = Math.floorMod(-s.worldY - 1, 8) / 8.0f;
                float u0 = uBase + uo, u1 = u0 + du, v0 = vBase + vo, v1 = v0 + dv;
                float x = d;
                quad(vc, pose, new float[][]{{x, 1, 0}, {x, 1, 1}, {x, 0, 1}, {x, 0, 0}}, argb, u0, u1, v0, v1, fullNormal);
            }
            // 5. 頂面 (Up, Y = 1)
            if (s.faceUp) {
                float uBase = Math.floorMod(s.worldX, 16) / 16.0f;
                float vBase = Math.floorMod(s.worldZ, 8) / 8.0f;
                float u0 = uBase + uo, u1 = u0 + du, v0 = vBase + vo, v1 = v0 + dv;
                float y = 1.0f - d;
                quad(vc, pose, new float[][]{{0, y, 0}, {1, y, 0}, {1, y, 1}, {0, y, 1}}, argb, u0, u1, v0, v1, fullNormal);
            }
            // 6. 底面 (Down, Y = 0)
            if (s.faceDown) {
                float uBase = Math.floorMod(s.worldX, 16) / 16.0f;
                float vBase = Math.floorMod(-s.worldZ - 1, 8) / 8.0f;
                float u0 = uBase + uo, u1 = u0 + du, v0 = vBase + vo, v1 = v0 + dv;
                float y = d;
                quad(vc, pose, new float[][]{{0, y, 1}, {1, y, 1}, {1, y, 0}, {0, y, 0}}, argb, u0, u1, v0, v1, fullNormal);
            }
        }
    }

    private static void quad(VertexConsumer vc, PoseStack.Pose pose, float[][] p, int argb, float u0, float u1, float v0, float v1, float[] n) {
        float[][] uv = {{u0, v0}, {u1, v0}, {u1, v1}, {u0, v1}};
        for (int i = 0; i < 4; i++) {
            texVertex(vc, pose, p[i], argb, uv[i][0], uv[i][1], n);
        }
    }

    // ------------------------------------------------------------------ layer 2: inner dawn halo along borders
    private static void edgeHalo(SiftPortalRenderState s, PoseStack.Pose pose, VertexConsumer vc) {
        haloNight = s.night;
        float w = EDGE_WIDTH + 0.15f * s.night;
        if (s.faceSouth) {
            float z = 1.001f;
            if (s.faceUp) halo(vc, pose, new float[]{0, 1, z}, new float[]{1, 1, z}, new float[]{1, 1 - w, z}, new float[]{0, 1 - w, z});
            if (s.faceDown) halo(vc, pose, new float[]{1, 0, z}, new float[]{0, 0, z}, new float[]{0, w, z}, new float[]{1, w, z});
            if (s.faceWest) halo(vc, pose, new float[]{0, 0, z}, new float[]{0, 1, z}, new float[]{w, 1, z}, new float[]{w, 0, z});
            if (s.faceEast) halo(vc, pose, new float[]{1, 1, z}, new float[]{1, 0, z}, new float[]{1 - w, 0, z}, new float[]{1 - w, 1, z});
        }
        if (s.faceNorth) {
            float z = -0.001f;
            if (s.faceUp) halo(vc, pose, new float[]{1, 1, z}, new float[]{0, 1, z}, new float[]{0, 1 - w, z}, new float[]{1, 1 - w, z});
            if (s.faceDown) halo(vc, pose, new float[]{0, 0, z}, new float[]{1, 0, z}, new float[]{1, w, z}, new float[]{0, w, z});
            if (s.faceEast) halo(vc, pose, new float[]{1, 0, z}, new float[]{1, 1, z}, new float[]{1 - w, 1, z}, new float[]{1 - w, 0, z});
            if (s.faceWest) halo(vc, pose, new float[]{0, 1, z}, new float[]{0, 0, z}, new float[]{w, 0, z}, new float[]{w, 1, z});
        }
    }

    private static float haloNight;

    private static void halo(VertexConsumer vc, PoseStack.Pose pose, float[] edgeA, float[] edgeB, float[] innerB, float[] innerA) {
        float[][] p = {edgeA, edgeB, innerB, innerA};
        float n = haloNight;   // 夜晚：邊緣變成粉紅色，內側透出金黃（影片中夜裡浮現的門）
        for (int i = 0; i < 4; i++) {
            boolean edge = i < 2;
            int g = edge ? (int) (246 - 116 * n) : (int) (230 - 10 * n);
            int b = edge ? (int) (215 - 15 * n) : (int) (245 - 165 * n);
            colVertex(vc, pose, p[i], 255, g, b, edge ? (int) Math.min(255, 220 + 35 * n) : (int) (90 * n));
        }
    }

    // ------------------------------------------------------------------ layer 3: god rays spilling out of the rim
    private static void godRays(SiftPortalRenderState s, PoseStack.Pose pose, VertexConsumer vc) {
        float breathe = (float) Math.sin(s.time * 1.5f * 60.0f + (s.seed % 1000));
        float len = (0.85f + 0.20f * breathe) * (1.0f + 0.8f * s.night);   // 夜晚光芒更長

        if (s.faceSouth) {
            float z = 1.0f;
            if (s.faceUp) ray(vc, pose, new float[]{0, 1, z}, new float[]{1, 1, z}, new float[]{1, 1 + len, z + 0.15f}, new float[]{0, 1 + len, z + 0.15f});
            if (s.faceDown) ray(vc, pose, new float[]{1, 0, z}, new float[]{0, 0, z}, new float[]{0, -len, z + 0.15f}, new float[]{1, -len, z + 0.15f});
            if (s.faceWest) ray(vc, pose, new float[]{0, 0, z}, new float[]{0, 1, z}, new float[]{-len, 1, z + 0.15f}, new float[]{-len, 0, z + 0.15f});
            if (s.faceEast) ray(vc, pose, new float[]{1, 1, z}, new float[]{1, 0, z}, new float[]{1 + len, 0, z + 0.15f}, new float[]{1 + len, 1, z + 0.15f});
        }
        if (s.faceNorth) {
            float z = 0.0f;
            if (s.faceUp) ray(vc, pose, new float[]{1, 1, z}, new float[]{0, 1, z}, new float[]{0, 1 + len, z - 0.15f}, new float[]{1, 1 + len, z - 0.15f});
            if (s.faceDown) ray(vc, pose, new float[]{0, 0, z}, new float[]{1, 0, z}, new float[]{1, -len, z - 0.15f}, new float[]{0, -len, z - 0.15f});
            if (s.faceEast) ray(vc, pose, new float[]{1, 0, z}, new float[]{1, 1, z}, new float[]{1 + len, 1, z - 0.15f}, new float[]{1 + len, 0, z - 0.15f});
            if (s.faceWest) ray(vc, pose, new float[]{0, 1, z}, new float[]{0, 0, z}, new float[]{-len, 0, z - 0.15f}, new float[]{-len, 1, z - 0.15f});
        }
    }

    private static void ray(VertexConsumer vc, PoseStack.Pose pose, float[] rootA, float[] rootB, float[] tipB, float[] tipA) {
        float[][] p = {rootA, rootB, tipB, tipA};
        for (int i = 0; i < 4; i++) {
            boolean root = i < 2;
            colVertex(vc, pose, p[i], 255, root ? 250 : 240, root ? 225 : 200, root ? 110 : 0);
        }
    }
}
