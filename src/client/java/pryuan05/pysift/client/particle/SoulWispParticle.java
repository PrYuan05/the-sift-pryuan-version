package pryuan05.pysift.client.particle;

import net.minecraft.client.Minecraft;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.particle.SingleQuadParticle;
import net.minecraft.client.particle.SpriteSet;
import net.minecraft.client.renderer.texture.TextureAtlasSprite;
import net.minecraft.util.Mth;

/**
 * 靈魂出竅：藍白發光的小鬼臉從靈液冒出，邊旋轉邊加速往上飄，身後拖一條淡藍→深藍的光尾，頭部帶一圈白藍光暈。
 * <ul>
 *   <li>每 tick 在上一格位置與目前位置之間補 TRAIL_PER_TICK 個光尾點，所以快速移動時光尾也是連續的。</li>
 *   <li>前 8 tick 淡入、最後 20 tick 淡出；全亮度渲染。</li>
 * </ul>
 */
public class SoulWispParticle extends SingleQuadParticle {
    private static final int TRAIL_PER_TICK = 3;
    /** 光尾每個點停留的 tick 數（越大光尾越長）。 */
    private static final int TRAIL_LIFE_MIN = 14, TRAIL_LIFE_RANGE = 10;
    private static final int FADE_IN = 8, FADE_OUT = 20;

    private final SpriteSet trailSprites;
    private float angle;
    private final float angleSpeed;
    private final float swirl;
    private final float driftX, driftZ;
    private final float maxRise;

    public SoulWispParticle(ClientLevel level, double x, double y, double z, double xd, double yd, double zd,
                            TextureAtlasSprite sprite, SpriteSet trailSprites) {
        super(level, x, y, z, sprite);
        this.trailSprites = trailSprites;
        this.lifetime = 60 + random.nextInt(60);
        this.quadSize = 0.16F + random.nextFloat() * 0.09F;   // 貼圖是 12×12、臉只佔中間 8 格寬，所以整體放大
        this.hasPhysics = false;
        this.gravity = 0;
        this.friction = 1;
        this.angle = random.nextFloat() * Mth.TWO_PI;
        this.angleSpeed = (0.12F + random.nextFloat() * 0.18F) * (random.nextBoolean() ? 1 : -1);
        this.swirl = 0.03F + random.nextFloat() * 0.06F;      // 螺旋的水平速度
        float driftAngle = random.nextFloat() * Mth.TWO_PI;    // 整體往某個方向斜飄
        float drift = random.nextFloat() * 0.03F;
        this.driftX = Mth.cos(driftAngle) * drift;
        this.driftZ = Mth.sin(driftAngle) * drift;
        this.maxRise = 0.09F + random.nextFloat() * 0.08F;
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
        angle += angleSpeed;
        xd = Mth.cos(angle) * swirl + driftX;
        zd = Mth.sin(angle) * swirl + driftZ;
        yd = Math.min(yd + 0.0035, maxRise);                    // 越飄越快
        move(xd, yd, zd);

        float alpha = Math.min(1, (float) age / FADE_IN) * Math.min(1, (float) (lifetime - age) / FADE_OUT);
        setAlpha(alpha);
        var engine = Minecraft.getInstance().particleEngine;
        for (int i = 0; i < TRAIL_PER_TICK; i++) {             // 光尾：頭部附近偏白，往後漸成深藍（SoulTrailParticle）
            double t = (i + 0.5) / TRAIL_PER_TICK;
            float white = random.nextFloat() * 0.4F;
            engine.add(new SoulTrailParticle(level, Mth.lerp(t, xo, x), Mth.lerp(t, yo, y), Mth.lerp(t, zo, z),
                    trailSprites.first(), quadSize * (0.5F + random.nextFloat() * 0.2F),
                    0.45F + white, 0.85F + white * 0.35F, 1.0F, 0.85F * alpha, TRAIL_LIFE_MIN + random.nextInt(TRAIL_LIFE_RANGE)));
        }
        if (age % 2 == 0) {                                      // 頭部光暈：大而淡、很快消失
            engine.add(new SoulTrailParticle(level, x, y, z, trailSprites.first(), quadSize * 2.2F,
                    0.75F, 0.95F, 1.0F, 0.22F * alpha, 3));
        }
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
