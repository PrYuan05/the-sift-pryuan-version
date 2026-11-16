package pryuan05.pysift.client.particle;

import net.minecraft.client.Camera;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.particle.SingleQuadParticle;
import net.minecraft.client.renderer.texture.TextureAtlasSprite;
import net.minecraft.util.Mth;
import org.joml.Quaternionf;
import org.joml.Vector3f;

/**
 * 靈魂光尾的一個柔光點：原地停留、慢慢縮小變淡，顏色從起始色（淡藍／白）漸漸轉成深藍。
 * 全亮度渲染（不受環境光影響），所以在暗處看起來會發光。也拿來當靈魂頭部的光暈（尺寸大、透明度低、壽命短）。
 * 靈魂的長方形光帶由 SoulWispParticle 自己每一幀畫；這裡另外放兩者共用的 {@link #alongPath}。
 */
public class SoulTrailParticle extends SingleQuadParticle {
    /** 光尾尾端的深藍色。 */
    static final float END_R = 0.10F, END_G = 0.42F, END_B = 1.0F;
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

    /**
     * 面向鏡頭、再繞視線轉到方塊的上方對齊「路徑在螢幕上的走向」的旋轉。(rx, ry, rz) 是這一段相對鏡頭的位置、
     * (dx, dy, dz) 是路徑方向。走向用透視投影的導數算（點 r 沿 d 移動時，螢幕座標 x/z、y/z 怎麼變），所以順著路徑
     * 看（光帶朝鏡頭或背離鏡頭）時，段落沿著畫面上往外張開的方向排，而不是因為投影太短而亂轉、斷成虛線。
     * 遊戲內截圖（2026-11-08）確認轉角取 atan2(-side, up)；取正號時斜的光帶每段都往反方向歪。
     */
    static Quaternionf alongPath(FacingCameraMode mode, Camera camera, float partialTick,
                                 float rx, float ry, float rz, float dx, float dy, float dz) {
        Quaternionf q = new Quaternionf();
        mode.setRotation(q, camera, partialTick);
        Vector3f lx = q.transform(new Vector3f(1, 0, 0));
        Vector3f ly = q.transform(new Vector3f(0, 1, 0));
        Vector3f lz = q.transform(new Vector3f(0, 0, 1));
        float px = rx * lx.x + ry * lx.y + rz * lx.z, py = rx * ly.x + ry * ly.y + rz * ly.z, pz = rx * lz.x + ry * lz.y + rz * lz.z;
        float vx = dx * lx.x + dy * lx.y + dz * lx.z, vy = dx * ly.x + dy * ly.y + dz * ly.z, vz = dx * lz.x + dy * lz.y + dz * lz.z;
        // d/dt (p + t v).xy / (p + t v).z ∝ v.xy · p.z − p.xy · v.z（共同的 1/p.z² 只影響長度；p.z 的正負會把方向轉 180°，
        // 所以統一成「往遠離鏡頭的那邊」看：p.z < 0 時整個反過來，頭部與光帶的上方才不會翻到下面）
        float side = vx * pz - px * vz, up = vy * pz - py * vz;
        if (pz < 0) {
            side = -side;
            up = -up;
        }
        if (side * side + up * up < 1.0E-10F) {                     // 正對鏡頭：沒有走向可言，保持直立
            return q;
        }
        return q.rotateZ((float) Math.atan2(-side, up));
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
