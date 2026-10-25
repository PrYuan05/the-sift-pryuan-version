package pryuan05.pysift.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import net.fabricmc.fabric.api.client.rendering.v1.level.LevelRenderEvents;
import net.minecraft.client.Minecraft;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import pryuan05.pysift.block.SiftDayPhase;
import pryuan05.pysift.block.SiftPortalBlock;

/**
 * 隙浮的夜晚極光：入夜（{@link SiftDayPhase}）後，高空出現七條會飄動、閃爍的極光帶（翠綠轉粉紫、青藍轉洋紅、金綠轉玫瑰），
 * 遠的低、近的高，頭頂也有兩條橫過天頂。
 * 每條是一片垂直的光幕，沿著一條彎曲的弧線掛在鏡頭周圍（跟著鏡頭移動，所以永遠走不到），用 lightning 渲染（疊加發光）。
 */
public final class SiftAurora {
    private static final int SEGMENTS = 96;
    /** 每條極光：{起始角度（度）, 角度跨度, 距離, 高度, 光幕高度, 飄動速度, 相位, 配色}。 */
    private static final float[][] RIBBONS = {
            {-40, 150, 82, 58, 34, 0.6f, 0.0f, 0},
            {70, 120, 96, 66, 28, 0.45f, 2.1f, 1},
            {175, 140, 74, 52, 38, 0.75f, 4.3f, 0},
            {250, 110, 110, 74, 30, 0.5f, 1.2f, 2},
            {10, 100, 120, 80, 24, 0.4f, 3.4f, 1},
            // 頭頂：近、高，橫過天頂
            {-70, 140, 40, 88, 20, 0.55f, 5.1f, 2},
            {110, 140, 46, 92, 22, 0.65f, 0.7f, 0}};
    /** 配色：{底部, 中段, 頂部}。 */
    private static final int[][][] PALETTES = {
            {{80, 255, 170}, {120, 255, 190}, {215, 120, 255}},   // 翠綠 -> 粉紫
            {{70, 220, 255}, {110, 200, 255}, {255, 110, 210}},   // 青藍 -> 洋紅
            {{190, 255, 120}, {255, 230, 140}, {255, 120, 170}}}; // 金綠 -> 玫瑰

    private SiftAurora() {
    }

    public static void register() {
        LevelRenderEvents.COLLECT_SUBMITS.register(context -> {
            ClientLevel level = Minecraft.getInstance().level;
            if (level == null || !level.dimension().equals(SiftPortalBlock.SIFT_DIM)) {
                return;
            }
            float night = SiftDayPhase.night(level);
            if (night <= 0.01f) {
                return;
            }
            float time = (level.getGameTime() + Minecraft.getInstance().getDeltaTracker().getGameTimeDeltaPartialTick(false)) / 20.0f;
            PoseStack pose = context.poseStack();
            context.submitNodeCollector().submitCustomGeometry(pose, RenderTypes.lightning(), (p, vc) -> {
                for (float[] r : RIBBONS) {
                    ribbon(p, vc, r, time, night);
                }
            });
        });
    }

    private static void ribbon(PoseStack.Pose pose, VertexConsumer vc, float[] r, float time, float night) {
        float start = r[0], span = r[1], dist = r[2], height = r[3], curtain = r[4], speed = r[5], phase = r[6];
        int[][] pal = PALETTES[(int) r[7]];
        float[] px = new float[SEGMENTS + 1], pz = new float[SEGMENTS + 1], py = new float[SEGMENTS + 1], a = new float[SEGMENTS + 1];
        for (int i = 0; i <= SEGMENTS; i++) {
            float s = i / (float) SEGMENTS;
            double ang = Math.toRadians(start + span * s + 6.0 * Math.sin(time * 0.15 * speed + s * 5.0 + phase));
            float d = dist + 10.0f * (float) Math.sin(s * 7.0 + time * 0.3 * speed + phase);
            px[i] = (float) (Math.cos(ang) * d);
            pz[i] = (float) (Math.sin(ang) * d);
            py[i] = height + 5.0f * (float) Math.sin(s * 4.0 + time * 0.25 * speed + phase * 1.7);
            // 兩端淡出，中間有一段一段的亮暗（極光的皺褶）
            float edge = (float) Math.sin(Math.PI * s);
            float folds = 0.55f + 0.45f * (float) Math.sin(s * 23.0 + time * 1.3 * speed + phase);
            // 整條慢慢地一陣亮一陣暗
            float pulse = 0.75f + 0.25f * (float) Math.sin(time * 0.2 * speed + phase * 2.3);
            a[i] = night * edge * edge * folds * pulse;
        }
        for (int i = 0; i < SEGMENTS; i++) {
            // 下半段：翠綠，從底部透明到中間最亮
            band(pose, vc, px, pz, py, a, i, 0.0f, 0.4f, curtain, pal[0], pal[1], 0.0f, 1.0f);
            // 上半段：轉成頂部的顏色，往上淡出
            band(pose, vc, px, pz, py, a, i, 0.4f, 1.0f, curtain, pal[1], pal[2], 1.0f, 0.0f);
        }
    }

    /** 光幕在第 i 段、從高度比例 f0 到 f1 的一塊（正反兩面）。 */
    private static void band(PoseStack.Pose pose, VertexConsumer vc, float[] px, float[] pz, float[] py, float[] a, int i,
                             float f0, float f1, float curtain, int[] c0, int[] c1, float k0, float k1) {
        int j = i + 1;
        float y0i = py[i] + curtain * f0, y1i = py[i] + curtain * f1, y0j = py[j] + curtain * f0, y1j = py[j] + curtain * f1;
        int a0i = (int) (240 * a[i] * k0), a1i = (int) (240 * a[i] * k1), a0j = (int) (240 * a[j] * k0), a1j = (int) (240 * a[j] * k1);
        float[][] q = {{px[i], y0i, pz[i]}, {px[j], y0j, pz[j]}, {px[j], y1j, pz[j]}, {px[i], y1i, pz[i]}};
        int[][] col = {c0, c0, c1, c1};
        int[] al = {a0i, a0j, a1j, a1i};
        for (int n = 0; n < 4; n++) {
            vc.addVertex(pose, q[n][0], q[n][1], q[n][2]).setColor(col[n][0], col[n][1], col[n][2], Math.min(255, al[n]));
        }
        for (int n = 3; n >= 0; n--) {
            vc.addVertex(pose, q[n][0], q[n][1], q[n][2]).setColor(col[n][0], col[n][1], col[n][2], Math.min(255, al[n]));
        }
    }
}
