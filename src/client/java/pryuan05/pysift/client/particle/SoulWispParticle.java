package pryuan05.pysift.client.particle;

import net.minecraft.client.Camera;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.particle.SingleQuadParticle;
import net.minecraft.client.particle.SpriteSet;
import net.minecraft.client.renderer.state.level.QuadParticleRenderState;
import net.minecraft.client.renderer.texture.TextureAtlasSprite;
import net.minecraft.util.ARGB;
import net.minecraft.util.Mth;
import net.minecraft.world.phys.Vec3;
import org.joml.Quaternionf;

/**
 * 靈魂出竅：藍白發光的小鬼臉從靈液冒出，慢慢擺動、加速往上飄，身後拖一條長方形的光帶。
 * <ul>
 *   <li>光帶像 Enchantment Glows 的附魔光（使用者）：半透明的白藍本體，兩側一道清楚的亮框（soul_trail_band）。</li>
 *   <li>每一段光帶上端是圓頭、下端是互補的凹口（使用者的點子），段與段重疊 1/4、圓頭嵌進下一段的凹口；
 *       轉彎時圓頭跟著轉，補上彎道外側的縫，直的時候兩邊互補不會疊亮。頭部（soul_wisp）的底部也是同樣的凹口，
 *       所以從有臉的頭到尾巴是一條連續的帶子。</li>
 *   <li>光帶每一幀重新排：靈魂每 tick 記下頭部底部的位置（路徑），畫的時候從頭部的凹口開始沿路徑往後，每隔
 *       3/4 段放一段，排到光尾長度為止。頭和第一段永遠剛好嵌合；亮度依「離頭部多遠」漸變，不會一段一段跳。</li>
 *   <li>頭部和每一段都面向鏡頭、繞視線轉到「路徑在螢幕上的走向」（SoulTrailParticle.alongPath，含透視）。</li>
 *   <li>光尾長度每個靈魂隨機（TRAIL_MIN～TRAIL_MAX 格，偏短、偶爾很長）。頭部那端不染色，往尾端漸成深藍再淡出。</li>
 *   <li>前 8 tick 淡入；最後 FADE_OUT tick 頭部淡出，之後光帶再用 TRAIL_FADE tick 淡掉；全亮度渲染。</li>
 * </ul>
 */
public class SoulWispParticle extends SingleQuadParticle {
    /** 光尾長度（格）：TRAIL_MIN + (TRAIL_MAX - TRAIL_MIN) × r²，r 均勻，所以多數短、少數拖到約 18 格（使用者：5～18 格）。 */
    private static final float TRAIL_MIN = 5.0F, TRAIL_MAX = 18.0F;
    /** 頭部淡入、淡出（使用者：頭也消失慢一點，原本 20）；頭部消失後光帶再淡掉的 tick 數。 */
    private static final int FADE_IN = 8, FADE_OUT = 40, TRAIL_FADE = 30;
    /** 段落重疊比例 = 圓頭高度（貼圖 16 列裡的 4 列）。 */
    private static final double OVERLAP = 4.0 / 16.0;
    private static final int MAX_PATH = 600;

    private final SpriteSet trailSprites;
    private final float trailLength;
    private float angle;
    private final float angleSpeed;
    private final float swirl;
    private final float driftX, driftZ;
    private final float maxRise;
    private final int headLife;
    private double dirX, dirY = 1, dirZ;
    private float headAlpha;
    private float trailFade = 1;
    /** 頭部底部的歷史位置，path[0] 最新。 */
    private final double[] pathX = new double[MAX_PATH], pathY = new double[MAX_PATH], pathZ = new double[MAX_PATH];
    private int pathLen;

    public SoulWispParticle(ClientLevel level, double x, double y, double z, double xd, double yd, double zd,
                            TextureAtlasSprite sprite, SpriteSet trailSprites) {
        super(level, x, y, z, sprite);
        this.trailSprites = trailSprites;
        this.headLife = 90 + random.nextInt(70);                // 光尾消失太快（使用者）— 活久一點，長光尾才拉得出來
        this.lifetime = headLife + TRAIL_FADE;
        this.quadSize = (0.16F + random.nextFloat() * 0.09F) * 16F / 12F;   // 貼圖 16×16（身體 8 格寬＋外框光暈），放大到和原本 12×12 時一樣大
        this.hasPhysics = false;
        this.gravity = 0;
        this.friction = 1;
        this.angle = random.nextFloat() * Mth.TWO_PI;
        // 使用者：少繞一點 — 光帶是一段段拼成的，轉得急段與段之間就看得到折角；慢而小的擺動讓光帶接近直線
        this.angleSpeed = (0.04F + random.nextFloat() * 0.04F) * (random.nextBoolean() ? 1 : -1);
        this.swirl = 0.008F + random.nextFloat() * 0.012F;    // 螺旋的水平速度（原本 0.03～0.09）
        float driftAngle = random.nextFloat() * Mth.TWO_PI;    // 整體往某個方向斜飄
        float drift = random.nextFloat() * 0.03F;
        this.driftX = Mth.cos(driftAngle) * drift;
        this.driftZ = Mth.sin(driftAngle) * drift;
        this.maxRise = 0.09F + random.nextFloat() * 0.08F;
        float r = random.nextFloat();
        this.trailLength = TRAIL_MIN + (TRAIL_MAX - TRAIL_MIN) * r * r;
        this.xd = xd;
        this.yd = Math.max(yd, 0.02);
        this.zd = zd;
        setColor(1, 1, 1);
        setAlpha(0);
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
        if (age > headLife) {                                    // 頭已經消失：停住，光帶淡掉
            trailFade = 1 - (float) (age - headLife) / TRAIL_FADE;
            headAlpha = 0;
            setAlpha(0);
            return;
        }
        angle += angleSpeed;
        xd = Mth.cos(angle) * swirl + driftX;
        zd = Mth.sin(angle) * swirl + driftZ;
        yd = Math.min(yd + 0.0035, maxRise);                    // 越飄越快
        move(xd, yd, zd);

        headAlpha = Math.min(1, (float) age / FADE_IN) * Math.min(1, (float) (headLife - age) / FADE_OUT);
        setAlpha(headAlpha);
        double dx = x - xo, dy = y - yo, dz = z - zo;
        double dist = Math.sqrt(dx * dx + dy * dy + dz * dz);
        if (dist > 1.0E-4) {
            dirX = dx / dist;
            dirY = dy / dist;
            dirZ = dz / dist;
        }
        // 記下頭部底部（中心往後 quadSize）
        System.arraycopy(pathX, 0, pathX, 1, MAX_PATH - 1);
        System.arraycopy(pathY, 0, pathY, 1, MAX_PATH - 1);
        System.arraycopy(pathZ, 0, pathZ, 1, MAX_PATH - 1);
        pathX[0] = x - dirX * quadSize;
        pathY[0] = y - dirY * quadSize;
        pathZ[0] = z - dirZ * quadSize;
        pathLen = Math.min(MAX_PATH, pathLen + 1);
        // 頭部原本每 2 tick 放一顆大柔光點當光暈（使用者：頭部特效破圖）；頭部貼圖自己就有亮框與光暈，
        // 而那顆光點停在原地、頭往上飛就落在後面，所以拿掉。
    }

    @Override
    public void extract(QuadParticleRenderState state, Camera camera, float partialTick) {
        Vec3 cam = camera.position();
        float half = quadSize;
        double hx = Mth.lerp(partialTick, xo, x), hy = Mth.lerp(partialTick, yo, y), hz = Mth.lerp(partialTick, zo, z);
        boolean moving = age <= headLife;
        if (trailSprites != null && pathLen > 0) {
            extractTrail(state, camera, partialTick, cam, half,
                    moving ? hx - dirX * quadSize : pathX[0], moving ? hy - dirY * quadSize : pathY[0],
                    moving ? hz - dirZ * quadSize : pathZ[0]);
        }
        if (moving && headAlpha > 0) {                           // 頭部：和光帶同樣轉到路徑方向，底部凹口接住第一段的圓頭
            Quaternionf q = SoulTrailParticle.alongPath(getFacingCameraMode(), camera, partialTick, (float) (hx - cam.x()),
                    (float) (hy - cam.y()), (float) (hz - cam.z()), (float) dirX, (float) dirY, (float) dirZ);
            extractRotatedQuad(state, camera, q, partialTick);
        }
    }

    /**
     * 從頭部底部 (ax, ay, az) 開始沿路徑往後排光帶：第 k 段涵蓋弧長 [k·s − overlap, k·s − overlap + 段長]
     * （s = 段長 × 3/4、overlap = 圓頭高度），所以第 0 段的圓頭剛好伸進頭部的凹口，之後每段的圓頭伸進靠頭那段的凹口。
     */
    private void extractTrail(QuadParticleRenderState state, Camera camera, float partialTick, Vec3 cam, float half,
                              double ax, double ay, double az) {
        double seg = 2 * half, step = seg * (1 - OVERLAP);
        double length = Math.max(0, trailLength);
        TextureAtlasSprite band = trailSprites.get(1, 1);
        // 路徑折線：頭部底部（內插）→ path[0] → path[1] …；沿弧長取點
        double px = ax, py = ay, pz = az;
        int idx = 1;                                             // path[0] 是這個 tick 結束時的位置，在內插的頭部前面
        double walked = 0;                                       // 已走過的弧長（到 px,py,pz）
        double segLen = 0, sx = 0, sy = 0, sz = 0;               // 目前這一小段折線的方向與長度
        for (int k = 0; ; k++) {
            double centre = k * step - seg * OVERLAP + half;     // 第 k 段中心的弧長
            if (centre - half > length) {
                break;
            }
            // 走到弧長 centre
            while (walked + segLen < centre) {
                walked += segLen;
                if (segLen > 0) {
                    px += sx * segLen;
                    py += sy * segLen;
                    pz += sz * segLen;
                }
                if (idx >= pathLen) {
                    return;                                      // 路徑還不夠長（剛冒出來）
                }
                double nx = pathX[idx], ny = pathY[idx], nz = pathZ[idx];
                idx++;
                double vx = px - nx, vy = py - ny, vz = pz - nz;   // 往後（遠離頭部）的方向
                segLen = Math.sqrt(vx * vx + vy * vy + vz * vz);
                if (segLen > 1.0E-6) {
                    sx = -vx / segLen;
                    sy = -vy / segLen;
                    sz = -vz / segLen;
                }
            }
            double t = centre - walked;
            double cx = px + sx * t, cy = py + sy * t, cz = pz + sz * t;
            // 段落的「上方」朝向頭部 = 路徑往後方向的反方向
            float ux = (float) -sx, uy = (float) -sy, uz = (float) -sz;
            if (centre < 0) {                                    // 第 0 段的中心還在頭部底部之前：用頭部的方向
                cx = ax + dirX * -centre;
                cy = ay + dirY * -centre;
                cz = az + dirZ * -centre;
                ux = (float) dirX;
                uy = (float) dirY;
                uz = (float) dirZ;
            }
            float f = (float) Math.min(1, Math.max(0, centre / length));
            float alpha = trailFade * Math.max(headAlphaForTrail(), 0) * (1 - f * f);
            if (alpha <= 0.01F) {
                continue;
            }
            float c = f * (float) Math.sqrt(f);                  // 前段保持亮白，後段才轉深藍
            int colour = ARGB.colorFromFloat(alpha, Mth.lerp(c, 1, SoulTrailParticle.END_R), Mth.lerp(c, 1, SoulTrailParticle.END_G),
                    Mth.lerp(c, 1, SoulTrailParticle.END_B));
            float rx = (float) (cx - cam.x()), ry = (float) (cy - cam.y()), rz = (float) (cz - cam.z());
            Quaternionf q = SoulTrailParticle.alongPath(getFacingCameraMode(), camera, partialTick, rx, ry, rz, ux, uy, uz);
            state.add(Layer.TRANSLUCENT, rx, ry, rz, q.x, q.y, q.z, q.w, half,
                    band.getU0(), band.getU1(), band.getV0(), band.getV1(), colour, SoulTrailParticle.FULL_BRIGHT);
        }
    }

    /** 光帶跟著頭部淡入，但頭部淡出時光帶保持亮度（之後由 trailFade 收尾）。 */
    private float headAlphaForTrail() {
        return age <= headLife ? Math.min(1, (float) age / FADE_IN) : 1;
    }

    @Override
    protected Layer getLayer() {
        return Layer.TRANSLUCENT;
    }

    @Override
    protected int getLightCoords(float partialTick) {
        return SoulTrailParticle.FULL_BRIGHT;
    }
}
