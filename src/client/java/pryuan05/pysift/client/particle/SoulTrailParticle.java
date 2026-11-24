package pryuan05.pysift.client.particle;

import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.particle.SingleQuadParticle;
import net.minecraft.client.renderer.texture.TextureAtlasSprite;
import net.minecraft.util.Mth;

/**
 * 伴隨靈魂光帶飄散的青白微小方形星點粒子（對應 Actions &amp; Stuff 靈魂拖尾周圍的發光像素點）。
 * 全亮度渲染（不受環境光影響），緩緩漂移、微幅上浮並柔和縮小淡出，顏色從亮青白漸轉深靈魂藍。
 */
public class SoulTrailParticle extends SingleQuadParticle {
    static final float END_R = 0.06F, END_G = 0.45F, END_B = 0.92F;
    static final int FULL_BRIGHT = 0xF000F0;

    private final float startR, startG, startB, startAlpha, startSize;

    public SoulTrailParticle(ClientLevel level, double x, double y, double z,
                             double xd, double yd, double zd, TextureAtlasSprite sprite,
                             float size, float r, float g, float b, float alpha, int lifetime) {
        super(level, x, y, z, sprite);
        this.startR = r;
        this.startG = g;
        this.startB = b;
        this.startAlpha = alpha;
        this.startSize = size;
        this.quadSize = size;
        this.lifetime = lifetime;
        this.hasPhysics = false;
        this.gravity = 0;
        this.xd = xd;
        this.yd = yd == 0.0 ? 0.006 : yd;
        this.zd = zd;
        setColor(r, g, b);
        setAlpha(alpha);
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
        float t = (float) age / lifetime;
        xd *= 0.94;
        zd *= 0.94;
        yd = Mth.lerp(0.08, yd, 0.012);
        setColor(Mth.lerp(t, startR, END_R), Mth.lerp(t, startG, END_G), Mth.lerp(t, startB, END_B));
        float fade = (1.0F - t) * (1.0F - t);
        setAlpha(startAlpha * fade);
        quadSize = startSize * (1.0F - 0.55F * t);
        move(xd, yd, zd);
    }

    @Override
    protected Layer getLayer() {
        return Layer.TRANSLUCENT;
    }

    @Override
    protected int getLightCoords(float partialTick) {
        return FULL_BRIGHT;
    }
}
