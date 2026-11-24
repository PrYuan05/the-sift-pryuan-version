package pryuan05.pysift.client.particle;

import net.minecraft.client.Camera;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.particle.SingleQuadParticle;
import net.minecraft.client.renderer.state.level.QuadParticleRenderState;
import net.minecraft.client.renderer.texture.TextureAtlasSprite;
import net.minecraft.util.Mth;
import pryuan05.pysift.particle.ModParticles;

/**
 * 升級版靈魂粒子（仿 Bedrock Actions &amp; Stuff 動態靈魂效果）：
 * <ul>
 *   <li>保留在原版 ParticleEngine 內負責生命週期、物理軌跡記錄與微光星點生成；實際的「5×8 像素鬼臉＋連續 Catmull-Rom
 *       流暢光帶＋柔和外緣光暈」由 {@link SoulWispRenderer} 在世界渲染階段以共享頂點絲帶網格繪製，徹底消除分段粒子感。</li>
 *   <li>動態模擬影片中的大弧線與流暢 S 型滑翔：爆發放出時（如破壞靈魂晶塊、靈液互動）會先朝四面八方大幅度散射滑出，
 *       接著流暢折彎拉起並加速升空；淡出期間持續滑行不凍結，尾部自然消散。</li>
 *   <li>沿途稀疏飄落微小發光青色方形像素點（{@link ModParticles#SOUL_TRAIL}）。</li>
 * </ul>
 */
public class SoulWispParticle extends SingleQuadParticle {
    static final int MAX_HISTORY = 128;
    private static final float FADE_IN_TICKS = 6.0f;
    private static final float FADE_OUT_TICKS = 24.0f;

    private final float halfWidth;
    private final float headLength;
    private final float trailLength;
    private float horizDir;
    private float horizSpeed;
    private final float cruiseHoriz;
    private final float targetRise;
    private final float turnRate;
    private final float waveFreq;
    private final float wavePhase;
    private int sparkCooldown;

    /** 歷史軌跡點，index 0 為最新位置（本 tick 結束），依序往回推。 */
    private final double[] histX = new double[MAX_HISTORY];
    private final double[] histY = new double[MAX_HISTORY];
    private final double[] histZ = new double[MAX_HISTORY];
    private int histCount;

    public SoulWispParticle(ClientLevel level, double x, double y, double z, double xd, double yd, double zd,
                            TextureAtlasSprite sprite) {
        super(level, x, y, z, sprite);
        // 比例對齊參考影片：寬度 ~0.23..0.32 格，頭部嚴格 5:8 比例（高度 = 寬度 × 1.6）
        this.halfWidth = 0.115f + random.nextFloat() * 0.045f;
        this.headLength = this.halfWidth * 3.2f;
        float r = random.nextFloat();
        this.trailLength = 3.8f + 5.2f * r * r;
        this.lifetime = 68 + random.nextInt(44);
        this.quadSize = halfWidth;
        this.hasPhysics = false;
        this.gravity = 0;
        this.friction = 1;

        // 依初速度區分「放射狀爆發」與「環境悠然升起」，兩者皆平滑轉入寬弧線上升
        double hSpeed = Math.hypot(xd, zd);
        if (hSpeed > 0.015) {
            this.horizDir = (float) Math.atan2(zd, xd);
            this.horizSpeed = (float) Math.min(0.22, hSpeed * 2.4 + 0.045);
            // 爆發時允許部分靈魂先橫向甚至微俯衝再流暢拉起，重現影片的大弧線爆發感
            this.yd = Math.max(-0.025, yd * 1.1 + (random.nextDouble() - 0.35) * 0.065);
        } else {
            this.horizDir = random.nextFloat() * Mth.TWO_PI;
            this.horizSpeed = 0.045f + random.nextFloat() * 0.055f;
            this.yd = Math.max(yd, 0.035 + random.nextDouble() * 0.045);
        }
        this.cruiseHoriz = 0.040f + random.nextFloat() * 0.042f;
        this.targetRise = 0.115f + random.nextFloat() * 0.065f;
        this.turnRate = (0.030f + random.nextFloat() * 0.038f) * (random.nextBoolean() ? 1.0f : -1.0f);
        this.waveFreq = 0.055f + random.nextFloat() * 0.038f;
        this.wavePhase = random.nextFloat() * Mth.TWO_PI;
        this.sparkCooldown = 3 + random.nextInt(4);

        this.xd = Mth.cos(horizDir) * horizSpeed;
        this.zd = Mth.sin(horizDir) * horizSpeed;

        this.histX[0] = x;
        this.histY[0] = y;
        this.histZ[0] = z;
        this.histCount = 1;

        SoulWispRenderer.track(this);
    }

    @Override
    public void tick() {
        xo = x;
        yo = y;
        zo = z;
        if (age++ >= lifetime) {
            remove();
            return;
        }

        // 流暢的大弧度轉向與低頻 S 曲線，讓絲帶拖出自然柔順的曲線
        float wave = Mth.sin(age * waveFreq + wavePhase);
        horizDir += turnRate * (0.45f + 0.85f * wave);
        horizSpeed = Mth.lerp(0.065f, horizSpeed, cruiseHoriz);
        xd = Mth.cos(horizDir) * horizSpeed;
        zd = Mth.sin(horizDir) * horizSpeed;
        yd = Mth.lerp(0.055, yd, targetRise) + 0.004 * Mth.cos(age * waveFreq * 0.8f + wavePhase);
        move(xd, yd, zd);

        int shift = Math.min(histCount, MAX_HISTORY - 1);
        System.arraycopy(histX, 0, histX, 1, shift);
        System.arraycopy(histY, 0, histY, 1, shift);
        System.arraycopy(histZ, 0, histZ, 1, shift);
        histX[0] = x;
        histY[0] = y;
        histZ[0] = z;
        histCount = Math.min(MAX_HISTORY, histCount + 1);

        // 稀疏飄落青白小方塊像素星點
        if (age > 3 && age < lifetime - 14 && --sparkCooldown <= 0) {
            sparkCooldown = 4 + random.nextInt(5);
            int back = Math.min(histCount - 1, 2 + random.nextInt(7));
            double sx = histX[back] + (random.nextDouble() - 0.5) * 0.28;
            double sy = histY[back] + (random.nextDouble() - 0.5) * 0.24;
            double sz = histZ[back] + (random.nextDouble() - 0.5) * 0.28;
            double svx = (random.nextDouble() - 0.5) * 0.018;
            double svy = 0.006 + random.nextDouble() * 0.016;
            double svz = (random.nextDouble() - 0.5) * 0.018;
            level.addParticle(ModParticles.SOUL_TRAIL, sx, sy, sz, svx, svy, svz);
        }
    }

    @Override
    public void remove() {
        SoulWispRenderer.untrack(this);
        super.remove();
    }

    /** 實際幾何已交由 SoulWispRenderer 以連續絲帶網格繪製，這裡不再發出方形粒子避免重影。 */
    @Override
    public void extract(QuadParticleRenderState state, Camera camera, float partialTick) {
    }

    @Override
    protected Layer getLayer() {
        return Layer.TRANSLUCENT;
    }

    // ---- 供 SoulWispRenderer 讀取的狀態 ----

    ClientLevel clientLevel() {
        return level;
    }

    float halfWidth() {
        return halfWidth;
    }

    float headLength() {
        return headLength;
    }

    float overallAlpha(float partialTick) {
        float tAge = age + partialTick;
        float in = Mth.clamp(tAge / FADE_IN_TICKS, 0.0f, 1.0f);
        float out = Mth.clamp((lifetime - tAge) / FADE_OUT_TICKS, 0.0f, 1.0f);
        // 平滑曲線（smoothstep）淡入淡出，徹底消除突兀出現或消失
        in = in * in * (3.0f - 2.0f * in);
        out = out * out * (3.0f - 2.0f * out);
        return in * out;
    }

    /** 尾段在生命最後 28 tick 稍微隨滑行自然收斂，讓消散更輕盈流暢。 */
    float effectiveTrailLength(float partialTick) {
        float rem = lifetime - (age + partialTick);
        float shrink = Mth.clamp(rem / 28.0f, 0.0f, 1.0f);
        return trailLength * (0.45f + 0.55f * shrink);
    }

    double distanceSqTo(double camX, double camY, double camZ) {
        double dx = x - camX, dy = y - camY, dz = z - camZ;
        return dx * dx + dy * dy + dz * dz;
    }

    int historyCount() {
        return histCount;
    }

    double[] histX() {
        return histX;
    }

    double[] histY() {
        return histY;
    }

    double[] histZ() {
        return histZ;
    }

    double prevX() {
        return xo;
    }

    double prevY() {
        return yo;
    }

    double prevZ() {
        return zo;
    }
}
