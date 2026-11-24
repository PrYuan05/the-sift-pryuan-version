package pryuan05.pysift.client.particle;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import net.fabricmc.fabric.api.client.rendering.v1.level.LevelRenderEvents;
import net.minecraft.client.Minecraft;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.resources.Identifier;
import net.minecraft.util.ARGB;
import net.minecraft.util.Mth;
import net.minecraft.world.phys.Vec3;
import pryuan05.pysift.PySift;

import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Set;

/**
 * 靈魂粒子連續光帶渲染器（仿 Bedrock Actions &amp; Stuff 升級靈魂粒子效果）：
 * <ul>
 *   <li>透過 {@link LevelRenderEvents#COLLECT_SUBMITS} 繪製真正「共享頂點、零分段」的 3D 面向鏡頭曲線絲帶。</li>
 *   <li>將每個 {@link SoulWispParticle} 的歷史軌跡以 Catmull-Rom 三次樣條曲線細分（每 tick 4 次細分），
 *       再依精確弧長取樣：前端 5:8 比例像素鬼臉（透明鏤空方形雙眼＋縱向長口）與後方光帶頂點完全焊死，
 *       連轉彎時頭部與光帶都能一體流暢彎曲，完全消除舊版方形粒子分段的鋸齒與折角。</li>
 *   <li>第二層以極柔和的 {@link RenderTypes#lightning()} 外緣光暈裙帶沿兩側外擴，讓暗處有真實的靈魂眩光，
 *       同時不覆蓋臉部，確保透明鏤空的眼睛與嘴巴保持銳利清晰。</li>
 * </ul>
 */
public final class SoulWispRenderer {
    private static final Identifier RIBBON_TEX = PySift.id("textures/entity/soul_wisp_ribbon.png");
    private static final int FULL_BRIGHT = 0xF000F0;
    /** 貼圖 32×64 中實際 5×8 靈魂寬度為 20 texel → u ∈ [0, 20/32]。 */
    private static final float U0 = 0.0f;
    private static final float U1 = 20.0f / 32.0f;
    /** 頭部佔貼圖上半部 v ∈ [0, 0.5]；皇冠第 0 列佔前 1/8 頭高（v ∈ [0, 0.0625]）；絲帶主體佔下半部 v ∈ [0.5, 1.0]。 */
    private static final float V_HEAD_START = 0.001f;   // 避開 v=0 處 GL_REPEAT 捲繞取到貼圖底邊 y=63 的白邊
    private static final float V_CROWN_END = 0.5f / 8.0f;
    private static final float V_HEAD_END = 0.5f;
    private static final float V_RIBBON_STEADY = 0.68f;
    private static final float V_RIBBON_END = 0.96f;
    /** 每 tick 細分次數（Catmull-Rom）與每個光帶取樣間隔（格）。 */
    private static final int SPLINE_SUBDIV = 4;
    private static final int HEAD_SEGMENTS = 4;
    private static final float TRAIL_STEP_BLOCKS = 0.14f;
    private static final int MAX_SAMPLES = 96;

    private static final Set<SoulWispParticle> ACTIVE = Collections.newSetFromMap(new IdentityHashMap<>());
    private static final List<SoulWispParticle> SORTED = new ArrayList<>();

    // 重複使用的暫存緩衝，避免每幀 GC 分配
    private static final double[] SP_X = new double[SoulWispParticle.MAX_HISTORY * SPLINE_SUBDIV + 8];
    private static final double[] SP_Y = new double[SP_X.length];
    private static final double[] SP_Z = new double[SP_X.length];
    private static final float[] SP_ARC = new float[SP_X.length];

    private static final float[] RX = new float[MAX_SAMPLES];
    private static final float[] RY = new float[MAX_SAMPLES];
    private static final float[] RZ = new float[MAX_SAMPLES];
    private static final float[] SX = new float[MAX_SAMPLES];
    private static final float[] SY = new float[MAX_SAMPLES];
    private static final float[] SZ = new float[MAX_SAMPLES];
    private static final float[] HW = new float[MAX_SAMPLES];
    private static final float[] VV = new float[MAX_SAMPLES];
    private static final float[] CR = new float[MAX_SAMPLES];
    private static final float[] CG = new float[MAX_SAMPLES];
    private static final float[] CB = new float[MAX_SAMPLES];
    private static final float[] CA = new float[MAX_SAMPLES];
    private static final float[] GLOW = new float[MAX_SAMPLES];

    private SoulWispRenderer() {
    }

    static void track(SoulWispParticle particle) {
        ACTIVE.add(particle);
    }

    static void untrack(SoulWispParticle particle) {
        ACTIVE.remove(particle);
    }

    public static void register() {
        LevelRenderEvents.COLLECT_SUBMITS.register(context -> {
            ClientLevel level = Minecraft.getInstance().level;
            if (level == null || ACTIVE.isEmpty()) {
                ACTIVE.clear();
                return;
            }
            ACTIVE.removeIf(p -> !p.isAlive() || p.clientLevel() != level);
            if (ACTIVE.isEmpty()) {
                return;
            }

            Vec3 cam = context.levelState().cameraRenderState.pos;
            float partialTick = context.levelState().worldPartialTicks;
            double camX = cam.x(), camY = cam.y(), camZ = cam.z();

            SORTED.clear();
            SORTED.addAll(ACTIVE);
            // 由遠到近排序，讓多條半透明靈魂光帶交錯時層次自然
            SORTED.sort(Comparator.comparingDouble((SoulWispParticle p) -> -p.distanceSqTo(camX, camY, camZ)));

            // 拍下當幀清單快照，避免回呼執行期間受變動影響
            List<SoulWispParticle> frameList = List.copyOf(SORTED);
            PoseStack pose = context.poseStack();

            // Pass 1：銳利像素鬼臉＋無縫連續漸層光帶（透明鏤空眼睛與嘴巴）
            context.submitNodeCollector().submitCustomGeometry(pose, RenderTypes.entityTranslucentEmissive(RIBBON_TEX),
                    (p, vc) -> {
                        for (int i = 0; i < frameList.size(); i++) {
                            renderRibbon(frameList.get(i), p, vc, null, camX, camY, camZ, partialTick);
                        }
                    });

            // Pass 2：柔和外緣青白疊加光暈（僅畫在光帶兩側外部，絕不糊掉臉上的眼睛與嘴巴）
            context.submitNodeCollector().submitCustomGeometry(pose, RenderTypes.lightning(),
                    (p, vc) -> {
                        for (int i = 0; i < frameList.size(); i++) {
                            renderRibbon(frameList.get(i), p, null, vc, camX, camY, camZ, partialTick);
                        }
                    });
        });
    }

    private static void renderRibbon(SoulWispParticle wisp, PoseStack.Pose pose,
                                     VertexConsumer bodyVc, VertexConsumer glowVc,
                                     double camX, double camY, double camZ, float partialTick) {
        float overallAlpha = wisp.overallAlpha(partialTick);
        if (overallAlpha <= 0.008f) {
            return;
        }
        int histCount = wisp.historyCount();
        if (histCount < 1) {
            return;
        }

        // 1. 以 Catmull-Rom 樣條曲線細分歷史路徑（含 partialTick 即時內插頭部位置）
        float headLen = wisp.headLength();
        float maxTrailLen = wisp.effectiveTrailLength(partialTick);
        float targetTotal = headLen + maxTrailLen;

        int spCount = buildCatmullRomPolyline(wisp, partialTick, targetTotal + 0.35f);
        if (spCount < 2) {
            return;
        }
        float availArc = SP_ARC[spCount - 1];
        if (availArc < 0.025f) {
            return;
        }

        // 2. 依弧長重新取樣成連續橫截面（頭部 0..shownHead + 絲帶 shownHead..endArc）
        float shownHead = Math.min(headLen, availArc);
        float endArc = Math.min(availArc, targetTotal);
        float halfW = wisp.halfWidth();

        int count = 0;
        // 頭部橫截面（0 .. shownHead，等分 HEAD_SEGMENTS 段，讓頭部能順著大弧度自然彎曲）
        for (int i = 0; i <= HEAD_SEGMENTS && count < MAX_SAMPLES; i++) {
            float frac = i / (float) HEAD_SEGMENTS;
            float s = frac * shownHead;
            samplePointOnSpline(spCount, s, camX, camY, camZ, count);
            HW[count] = halfW;
            VV[count] = i == 0 ? V_HEAD_START : Math.max(V_HEAD_START, V_HEAD_END * (s / headLen));
            CR[count] = 0.96f;
            CG[count] = 1.00f;
            CB[count] = 1.00f;
            CA[count] = overallAlpha;
            GLOW[count] = overallAlpha * (0.95f - 0.15f * frac);
            count++;
        }

        // 絲帶橫截面（shownHead .. endArc，第 0 點與頭部下巴最後一點完全共享，確保零接縫）
        if (endArc > shownHead + 0.005f && maxTrailLen > 0.01f) {
            float trailAvail = endArc - shownHead;
            int trailSegs = Math.max(2, Math.min(MAX_SAMPLES - count - 1, (int) Math.ceil(trailAvail / TRAIL_STEP_BLOCKS)));
            for (int i = 1; i <= trailSegs && count < MAX_SAMPLES; i++) {
                float u = i / (float) trailSegs;
                float s = shownHead + u * trailAvail;
                float t = Mth.clamp((s - shownHead) / maxTrailLen, 0.0f, 1.0f);
                samplePointOnSpline(spCount, s, camX, camY, camZ, count);

                // 寬度從 100% 輕柔收窄至 ~62%（不會尖成細針，與 Actions & Stuff 影片一致）
                HW[count] = halfW * (1.0f - 0.38f * t);

                // UV：緊接下巴處從 0.50 平滑銜接到 0.68..0.96 穩定光帶區
                VV[count] = t < 0.12f
                        ? Mth.lerp(t / 0.12f, V_HEAD_END, V_RIBBON_STEADY)
                        : Mth.lerp((t - 0.12f) / 0.88f, V_RIBBON_STEADY, V_RIBBON_END);

                // 色彩漸層：冰白 -> 亮電青 -> 靈魂青藍 -> 深幽藍（平滑連續，無段差）
                float r, g, b, a;
                if (t < 0.08f) {
                    float k = t / 0.08f;
                    r = Mth.lerp(k, 0.96f, 0.82f);
                    g = 1.00f;
                    b = 1.00f;
                    a = Mth.lerp(k, 0.98f, 0.93f);
                } else if (t < 0.28f) {
                    float k = (t - 0.08f) / 0.20f;
                    r = Mth.lerp(k, 0.82f, 0.28f);
                    g = Mth.lerp(k, 1.00f, 0.91f);
                    b = 1.00f;
                    a = Mth.lerp(k, 0.93f, 0.78f);
                } else if (t < 0.62f) {
                    float k = (t - 0.28f) / 0.34f;
                    r = Mth.lerp(k, 0.28f, 0.09f);
                    g = Mth.lerp(k, 0.91f, 0.66f);
                    b = Mth.lerp(k, 1.00f, 0.92f);
                    a = Mth.lerp(k, 0.78f, 0.38f);
                } else {
                    float k = (t - 0.62f) / 0.38f;
                    float ease = 1.0f - k;
                    r = Mth.lerp(k, 0.09f, 0.04f);
                    g = Mth.lerp(k, 0.66f, 0.32f);
                    b = Mth.lerp(k, 0.92f, 0.62f);
                    a = 0.38f * ease * ease;
                }

                // 若粒子剛冒出不久、拖尾還沒長滿，在出生點那一端做平滑淡入避免尾端生硬截斷
                if (availArc < targetTotal) {
                    float distFromSpawn = endArc - s;
                    float spawnFade = Mth.clamp(distFromSpawn / 0.45f, 0.0f, 1.0f);
                    a *= spawnFade;
                }

                CR[count] = r;
                CG[count] = g;
                CB[count] = b;
                CA[count] = a * overallAlpha;
                GLOW[count] = overallAlpha * Math.max(0.0f, 0.80f * (1.0f - t) * (1.0f - t));
                count++;
            }
        }

        if (count < 2) {
            return;
        }

        // 3. 計算每個橫截面的面向鏡頭側向量 side = normalize(cross(tangent, toCamera))
        float prevSx = 1.0f, prevSy = 0.0f, prevSz = 0.0f;
        boolean hasPrev = false;
        for (int i = 0; i < count; i++) {
            float tx, ty, tz;
            if (i == 0) {
                tx = RX[0] - RX[1];
                ty = RY[0] - RY[1];
                tz = RZ[0] - RZ[1];
            } else if (i == count - 1) {
                tx = RX[i - 1] - RX[i];
                ty = RY[i - 1] - RY[i];
                tz = RZ[i - 1] - RZ[i];
            } else {
                tx = RX[i - 1] - RX[i + 1];
                ty = RY[i - 1] - RY[i + 1];
                tz = RZ[i - 1] - RZ[i + 1];
            }
            float tLen = Mth.sqrt(tx * tx + ty * ty + tz * tz);
            if (tLen > 1.0e-5f) {
                tx /= tLen;
                ty /= tLen;
                tz /= tLen;
            } else {
                tx = 0.0f;
                ty = 1.0f;
                tz = 0.0f;
            }

            // 指向鏡頭的向量 = -R（因為 R 已是相對鏡頭座標）
            float vx = -RX[i], vy = -RY[i], vz = -RZ[i];
            float vLen = Mth.sqrt(vx * vx + vy * vy + vz * vz);
            if (vLen > 1.0e-5f) {
                vx /= vLen;
                vy /= vLen;
                vz /= vLen;
            } else {
                vx = 0.0f;
                vy = 0.0f;
                vz = 1.0f;
            }

            // side = tangent × toCamera（螢幕上指向光帶右側）
            float sx = ty * vz - tz * vy;
            float sy = tz * vx - tx * vz;
            float sz = tx * vy - ty * vx;
            float sLen = Mth.sqrt(sx * sx + sy * sy + sz * sz);

            if (sLen < 0.06f) {
                // 光帶幾乎正對／背對鏡頭時沿用上一段側向量，避免瞬間打結或縮成一條線
                if (hasPrev) {
                    sx = prevSx;
                    sy = prevSy;
                    sz = prevSz;
                } else {
                    sx = Math.abs(ty) < 0.9f ? 0.0f : 1.0f;
                    sy = Math.abs(ty) < 0.9f ? 1.0f : 0.0f;
                    sz = 0.0f;
                    float cx = ty * sz - tz * sy;
                    float cy = tz * sx - tx * sz;
                    float cz = tx * sy - ty * sx;
                    float cLen = Mth.sqrt(cx * cx + cy * cy + cz * cz);
                    sx = cLen > 1.0e-5f ? cx / cLen : 1.0f;
                    sy = cLen > 1.0e-5f ? cy / cLen : 0.0f;
                    sz = cLen > 1.0e-5f ? cz / cLen : 0.0f;
                }
            } else {
                sx /= sLen;
                sy /= sLen;
                sz /= sLen;
                if (hasPrev && (sx * prevSx + sy * prevSy + sz * prevSz) < 0.0f) {
                    // 防止穿越視線極點時翻轉成蝴蝶結
                    sx = -sx;
                    sy = -sy;
                    sz = -sz;
                }
            }

            SX[i] = sx;
            SY[i] = sy;
            SZ[i] = sz;
            prevSx = sx;
            prevSy = sy;
            prevSz = sz;
            hasPrev = true;
        }

        // 4A. Pass 1：寫入連續共享頂點的貼圖光帶四邊形
        if (bodyVc != null) {
            for (int i = 0; i < count - 1; i++) {
                int j = i + 1;
                if (CA[i] <= 0.005f && CA[j] <= 0.005f) {
                    continue;
                }
                int colI = ARGB.colorFromFloat(CA[i], CR[i], CG[i], CB[i]);
                int colJ = ARGB.colorFromFloat(CA[j], CR[j], CG[j], CB[j]);

                float wI = HW[i], wJ = HW[j];
                float lix = RX[i] - SX[i] * wI, liy = RY[i] - SY[i] * wI, liz = RZ[i] - SZ[i] * wI;
                float rix = RX[i] + SX[i] * wI, riy = RY[i] + SY[i] * wI, riz = RZ[i] + SZ[i] * wI;
                float ljx = RX[j] - SX[j] * wJ, ljy = RY[j] - SY[j] * wJ, ljz = RZ[j] - SZ[j] * wJ;
                float rjx = RX[j] + SX[j] * wJ, rjy = RY[j] + SY[j] * wJ, rjz = RZ[j] + SZ[j] * wJ;

                // 逆時針面向鏡頭（TL -> BL -> BR -> TR），與 entityTranslucentEmissive 的 NO_CULL 一致且不重複疊畫
                texVertex(bodyVc, pose, lix, liy, liz, colI, U0, VV[i]);
                texVertex(bodyVc, pose, ljx, ljy, ljz, colJ, U0, VV[j]);
                texVertex(bodyVc, pose, rjx, rjy, rjz, colJ, U1, VV[j]);
                texVertex(bodyVc, pose, rix, riy, riz, colI, U1, VV[i]);
            }
        }

        // 4B. Pass 2：兩側柔和外緣疊加光暈裙帶（L_outer..L_inner 與 R_inner..R_outer），讓靈魂發光但不糊掉臉部鏤空
        // 注意：第 0 列（v < V_CROWN_END = 1/8 頭高）是內縮的 3×1 皇冠，左右各 1 格為透明缺角；
        // 因此左右裙帶從肩膀線（V_CROWN_END）才開始平滑淡入，頭頂帽寬度亦對齊皇冠 0.6×halfW，完全避免左上／右上多出方格光條。
        if (glowVc != null) {
            int outerZero = ARGB.colorFromFloat(0.0f, 0.12f, 0.72f, 1.00f);
            for (int i = 0; i < count - 1; i++) {
                int j = i + 1;
                if (VV[j] <= V_CROWN_END) {
                    continue;   // 仍在透明缺角的皇冠高度內，不畫滿寬側裙
                }
                float gI = GLOW[i], gJ = GLOW[j];
                if (gI <= 0.01f && gJ <= 0.01f) {
                    continue;
                }

                // 若此段跨過肩膀線 V_CROWN_END，將起點內插至肩膀處並由 alpha=0 平滑起筆（無斷層、無懸空光條）
                float rIx, rIy, rIz, sIx, sIy, sIz, wI;
                int innerI;
                if (VV[i] < V_CROWN_END) {
                    float f = (V_CROWN_END - VV[i]) / (VV[j] - VV[i]);
                    rIx = Mth.lerp(f, RX[i], RX[j]);
                    rIy = Mth.lerp(f, RY[i], RY[j]);
                    rIz = Mth.lerp(f, RZ[i], RZ[j]);
                    sIx = Mth.lerp(f, SX[i], SX[j]);
                    sIy = Mth.lerp(f, SY[i], SY[j]);
                    sIz = Mth.lerp(f, SZ[i], SZ[j]);
                    float sLen = Mth.sqrt(sIx * sIx + sIy * sIy + sIz * sIz);
                    if (sLen > 1.0e-5f) {
                        sIx /= sLen;
                        sIy /= sLen;
                        sIz /= sLen;
                    }
                    wI = Mth.lerp(f, HW[i], HW[j]);
                    innerI = outerZero;
                } else {
                    rIx = RX[i];
                    rIy = RY[i];
                    rIz = RZ[i];
                    sIx = SX[i];
                    sIy = SY[i];
                    sIz = SZ[i];
                    wI = HW[i];
                    innerI = ARGB.colorFromFloat(0.24f * gI, 0.36f, 0.94f, 1.00f);
                }

                int innerJ = ARGB.colorFromFloat(0.24f * gJ, 0.24f, 0.86f, 1.00f);
                float wJ = HW[j];
                float owI = wI * 1.70f, owJ = wJ * 1.70f;

                float liX = rIx - sIx * wI,  liY = rIy - sIy * wI,  liZ = rIz - sIz * wI;
                float loX = rIx - sIx * owI, loY = rIy - sIy * owI, loZ = rIz - sIz * owI;
                float ljX = RX[j] - SX[j] * wJ,  ljY = RY[j] - SY[j] * wJ,  ljZ = RZ[j] - SZ[j] * wJ;
                float lojX = RX[j] - SX[j] * owJ, lojY = RY[j] - SY[j] * owJ, lojZ = RZ[j] - SZ[j] * owJ;

                // 左側外暈裙帶
                glowQuad(glowVc, pose, loX, loY, loZ, lojX, lojY, lojZ, ljX, ljY, ljZ, liX, liY, liZ,
                        outerZero, outerZero, innerJ, innerI);

                float riX = rIx + sIx * wI,  riY = rIy + sIy * wI,  riZ = rIz + sIz * wI;
                float roX = rIx + sIx * owI, roY = rIy + sIy * owI, roZ = rIz + sIz * owI;
                float rjX = RX[j] + SX[j] * wJ,  rjY = RY[j] + SY[j] * wJ,  rjZ = RZ[j] + SZ[j] * wJ;
                float rojX = RX[j] + SX[j] * owJ, rojY = RY[j] + SY[j] * owJ, rojZ = RZ[j] + SZ[j] * owJ;

                // 右側外暈裙帶
                glowQuad(glowVc, pose, riX, riY, riZ, rjX, rjY, rjZ, rojX, rojY, rojZ, roX, roY, roZ,
                        innerI, innerJ, outerZero, outerZero);
            }

            // 頭頂上方柔和光暈帽：嚴格對齊 3×1 皇冠寬度（0.60 × HW[0]），不跨出左右透明缺角
            float g0 = GLOW[0];
            if (g0 > 0.01f) {
                float tx = RX[0] - RX[1], ty = RY[0] - RY[1], tz = RZ[0] - RZ[1];
                float tLen = Mth.sqrt(tx * tx + ty * ty + tz * tz);
                if (tLen > 1.0e-5f) {
                    float ext = HW[0] * 0.52f / tLen;
                    tx *= ext;
                    ty *= ext;
                    tz *= ext;
                    float crownW = HW[0] * 0.60f;
                    float outerCrownW = HW[0] * 0.88f;
                    int inner0 = ARGB.colorFromFloat(0.20f * g0, 0.45f, 0.96f, 1.00f);
                    int outer0 = ARGB.colorFromFloat(0.0f, 0.16f, 0.78f, 1.00f);
                    float liX = RX[0] - SX[0] * crownW,  liY = RY[0] - SY[0] * crownW,  liZ = RZ[0] - SZ[0] * crownW;
                    float riX = RX[0] + SX[0] * crownW,  riY = RY[0] + SY[0] * crownW,  riZ = RZ[0] + SZ[0] * crownW;
                    float ltX = RX[0] - SX[0] * outerCrownW + tx, ltY = RY[0] - SY[0] * outerCrownW + ty, ltZ = RZ[0] - SZ[0] * outerCrownW + tz;
                    float rtX = RX[0] + SX[0] * outerCrownW + tx, rtY = RY[0] + SY[0] * outerCrownW + ty, rtZ = RZ[0] + SZ[0] * outerCrownW + tz;
                    glowQuad(glowVc, pose, ltX, ltY, ltZ, liX, liY, liZ, riX, riY, riZ, rtX, rtY, rtZ,
                            outer0, inner0, inner0, outer0);
                }
            }
        }
    }

    /**
     * 將粒子歷史節點 hist[0..n-1]（hist[0] 為本 tick 結束點、hist[1] 為上一 tick）
     * 以 Catmull-Rom 樣條曲線細分成密集平滑折線，存入 SP_X/Y/Z 與累積弧長 SP_ARC。
     */
    private static int buildCatmullRomPolyline(SoulWispParticle wisp, float pt, float stopArc) {
        int n = wisp.historyCount();
        double[] hx = wisp.histX(), hy = wisp.histY(), hz = wisp.histZ();
        if (n == 1) {
            // 剛生成的第一幀：由 xo -> x 內插
            double lx = Mth.lerp(pt, wisp.prevX(), hx[0]);
            double ly = Mth.lerp(pt, wisp.prevY(), hy[0]);
            double lz = Mth.lerp(pt, wisp.prevZ(), hz[0]);
            SP_X[0] = lx;
            SP_Y[0] = ly;
            SP_Z[0] = lz;
            SP_ARC[0] = 0.0f;
            SP_X[1] = wisp.prevX();
            SP_Y[1] = wisp.prevY();
            SP_Z[1] = wisp.prevZ();
            SP_ARC[1] = (float) Math.sqrt((lx - SP_X[1]) * (lx - SP_X[1])
                    + (ly - SP_Y[1]) * (ly - SP_Y[1]) + (lz - SP_Z[1]) * (lz - SP_Z[1]));
            return 2;
        }

        // 虛擬前方控制點（沿當前速度外推 1 tick），讓頭部在 tick 之間保持 C1 平滑連續
        double futX = hx[0] + (hx[0] - hx[1]);
        double futY = hy[0] + (hy[0] - hy[1]);
        double futZ = hz[0] + (hz[0] - hz[1]);

        int out = 0;
        float arc = 0.0f;

        // 第 0 段：從當前即時頭部位置（t = pt，介於 hist[1] 到 hist[0]）往回走到 hist[1]（t = 0）
        double p0x = n >= 3 ? hx[2] : (2.0 * hx[1] - hx[0]);
        double p0y = n >= 3 ? hy[2] : (2.0 * hy[1] - hy[0]);
        double p0z = n >= 3 ? hz[2] : (2.0 * hz[1] - hz[0]);
        int firstSteps = Math.max(1, (int) Math.ceil(pt * SPLINE_SUBDIV));
        for (int s = 0; s <= firstSteps && out < SP_X.length; s++) {
            float t = pt * (1.0f - s / (float) firstSteps);
            double x = catmullRom(p0x, hx[1], hx[0], futX, t);
            double y = catmullRom(p0y, hy[1], hy[0], futY, t);
            double z = catmullRom(p0z, hz[1], hz[0], futZ, t);
            if (out > 0) {
                double dx = x - SP_X[out - 1], dy = y - SP_Y[out - 1], dz = z - SP_Z[out - 1];
                float d = (float) Math.sqrt(dx * dx + dy * dy + dz * dz);
                if (d < 1.0e-5f) {
                    continue;
                }
                arc += d;
            }
            SP_X[out] = x;
            SP_Y[out] = y;
            SP_Z[out] = z;
            SP_ARC[out] = arc;
            out++;
        }

        // 後續歷史段：hist[k] -> hist[k+1]，每段細分 SPLINE_SUBDIV 次
        for (int k = 1; k < n - 1 && arc < stopArc && out < SP_X.length - SPLINE_SUBDIV; k++) {
            double ax = hx[k - 1], ay = hy[k - 1], az = hz[k - 1];
            double bx = hx[k],     by = hy[k],     bz = hz[k];
            double cx = hx[k + 1], cy = hy[k + 1], cz = hz[k + 1];
            double dx = (k + 2 < n) ? hx[k + 2] : (2.0 * cx - bx);
            double dy = (k + 2 < n) ? hy[k + 2] : (2.0 * cy - by);
            double dz = (k + 2 < n) ? hz[k + 2] : (2.0 * cz - bz);
            for (int s = 1; s <= SPLINE_SUBDIV && out < SP_X.length; s++) {
                float t = s / (float) SPLINE_SUBDIV;
                double x = catmullRom(ax, bx, cx, dx, t);
                double y = catmullRom(ay, by, cy, dy, t);
                double z = catmullRom(az, bz, cz, dz, t);
                double ddx = x - SP_X[out - 1], ddy = y - SP_Y[out - 1], ddz = z - SP_Z[out - 1];
                float d = (float) Math.sqrt(ddx * ddx + ddy * ddy + ddz * ddz);
                if (d < 1.0e-5f) {
                    continue;
                }
                arc += d;
                SP_X[out] = x;
                SP_Y[out] = y;
                SP_Z[out] = z;
                SP_ARC[out] = arc;
                out++;
                if (arc >= stopArc) {
                    break;
                }
            }
        }
        return out;
    }

    /** 標準均勻 Catmull-Rom 樣條插值（t ∈ [0, 1] 介於 p1 與 p2 之間）。 */
    private static double catmullRom(double p0, double p1, double p2, double p3, float t) {
        double t2 = t * t;
        double t3 = t2 * t;
        return 0.5 * ((2.0 * p1)
                + (-p0 + p2) * t
                + (2.0 * p0 - 5.0 * p1 + 4.0 * p2 - p3) * t2
                + (-p0 + 3.0 * p1 - 3.0 * p2 + p3) * t3);
    }

    /** 二分搜尋弧長 s 並寫入相機相對座標 RX/RY/RZ[dst]。 */
    private static void samplePointOnSpline(int spCount, float s, double camX, double camY, double camZ, int dst) {
        if (s <= 0.0f) {
            RX[dst] = (float) (SP_X[0] - camX);
            RY[dst] = (float) (SP_Y[0] - camY);
            RZ[dst] = (float) (SP_Z[0] - camZ);
            return;
        }
        int last = spCount - 1;
        if (s >= SP_ARC[last]) {
            RX[dst] = (float) (SP_X[last] - camX);
            RY[dst] = (float) (SP_Y[last] - camY);
            RZ[dst] = (float) (SP_Z[last] - camZ);
            return;
        }
        int lo = 0, hi = last;
        while (lo + 1 < hi) {
            int mid = (lo + hi) >>> 1;
            if (SP_ARC[mid] <= s) {
                lo = mid;
            } else {
                hi = mid;
            }
        }
        float seg = SP_ARC[hi] - SP_ARC[lo];
        float f = seg > 1.0e-5f ? (s - SP_ARC[lo]) / seg : 0.0f;
        RX[dst] = (float) (Mth.lerp(f, SP_X[lo], SP_X[hi]) - camX);
        RY[dst] = (float) (Mth.lerp(f, SP_Y[lo], SP_Y[hi]) - camY);
        RZ[dst] = (float) (Mth.lerp(f, SP_Z[lo], SP_Z[hi]) - camZ);
    }

    private static void texVertex(VertexConsumer vc, PoseStack.Pose pose, float x, float y, float z,
                                  int color, float u, float v) {
        vc.addVertex(pose, x, y, z)
                .setColor(color)
                .setUv(u, v)
                .setOverlay(OverlayTexture.NO_OVERLAY)
                .setLight(FULL_BRIGHT)
                .setNormal(pose, 0.0f, 1.0f, 0.0f);
    }

    private static void glowQuad(VertexConsumer vc, PoseStack.Pose pose,
                                 float x0, float y0, float z0, float x1, float y1, float z1,
                                 float x2, float y2, float z2, float x3, float y3, float z3,
                                 int c0, int c1, int c2, int c3) {
        vc.addVertex(pose, x0, y0, z0).setColor(c0);
        vc.addVertex(pose, x1, y1, z1).setColor(c1);
        vc.addVertex(pose, x2, y2, z2).setColor(c2);
        vc.addVertex(pose, x3, y3, z3).setColor(c3);
    }
}
