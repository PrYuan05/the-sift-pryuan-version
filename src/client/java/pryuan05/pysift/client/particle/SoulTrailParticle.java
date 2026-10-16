package pryuan05.pysift.client.particle;

import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.particle.SingleQuadParticle;
import net.minecraft.client.renderer.texture.TextureAtlasSprite;
import net.minecraft.util.Mth;

/**
 * 靈魂光尾的一個柔光點：原地停留、慢慢縮小變淡，顏色從起始色（淡藍／白）漸漸轉成深藍。
 * 全亮度渲染（不受環境光影響），所以在暗處看起來會發光。也拿來當靈魂頭部的光暈（尺寸大、透明度低、壽命短）。
 */
public class SoulTrailParticle extends SingleQuadParticle {
    /** 光尾尾端的深藍色。 */
    private static final float END_R = 0.10F, END_G = 0.42F, END_B = 1.0F;
    static final int FULL_BRIGHT = 0xF000F0;

    private final float startR, startG, startB, startAlpha, startSize;

    public SoulTrailParticle(ClientLevel level, double x, double y, double z, TextureAtlasSprite sprite,
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
        this.xd = 0;
        this.yd = 0.004;
        this.zd = 0;
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
        setColor(Mth.lerp(t, startR, END_R), Mth.lerp(t, startG, END_G), Mth.lerp(t, startB, END_B));
        setAlpha(startAlpha * (1 - t));
        quadSize = startSize * (1 - 0.6F * t);
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
