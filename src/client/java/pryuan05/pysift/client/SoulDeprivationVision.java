package pryuan05.pysift.client;

import com.mojang.blaze3d.systems.RenderSystem;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.minecraft.client.Camera;
import net.minecraft.client.Minecraft;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.resources.Identifier;
import net.minecraft.util.Mth;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.phys.Vec3;
import org.joml.Matrix4f;
import org.lwjgl.BufferUtils;
import pryuan05.pysift.PySift;
import pryuan05.pysift.effect.ModEffects;

import java.nio.ByteBuffer;
import java.util.List;

/**
 * 靈魂剝奪的視野：中了效果時，每個方塊看起來都像伏聆（深藏青底、青色紋點、幾個一閃一閃的亮青像素；
 * shaders/post/sculk_vision.fsh 依深度還原世界座標，把紋點畫在每個方塊面的 16×16 像素格上）。
 * <ul>
 *   <li>26.3 的 GameRenderer 每幀套用 {@link LocalPlayer#getActivePostEffects()} 裡的後製；這裡在每個 client tick
 *       把 pysift:sculk_vision 放進去或拿掉。</li>
 *   <li>強度：等級 I 為 0.6，每升一級 +0.2，最高 1.0；每 tick 往目標移動 1/{@value #FADE_TICKS}（約 1 秒漸入漸出），
 *       畫面上再依 partial tick 內插。</li>
 *   <li>相機資料由 PostPassMixin 每幀用 {@link #cameraUniform()} 寫入 SculkCamera。</li>
 * </ul>
 */
public final class SoulDeprivationVision {
    public static final String UNIFORM_BLOCK = "SculkCamera";
    private static final Identifier EFFECT = PySift.id("sculk_vision");
    private static final int FADE_TICKS = 20;
    private static final int UNIFORM_BYTES = 6 * 16;          // 6 x vec4 (std140)
    private static float fade;
    private static float prevFade;

    private SoulDeprivationVision() {
    }

    public static void register() {
        ClientTickEvents.END_CLIENT_TICK.register(SoulDeprivationVision::tick);
    }

    private static void tick(Minecraft minecraft) {
        LocalPlayer player = minecraft.player;
        prevFade = fade;
        if (player == null) {
            fade = prevFade = 0;
            return;
        }
        MobEffectInstance effect = player.getEffect(ModEffects.SOUL_DEPRIVATION);
        float target = effect == null ? 0.0F : Math.min(1.0F, 0.6F + 0.2F * effect.getAmplifier());
        float step = 1.0F / FADE_TICKS;
        fade = fade < target ? Math.min(target, fade + step) : Math.max(target, fade - step);

        List<Identifier> active = player.getActivePostEffects();
        active.removeIf(EFFECT::equals);
        if (fade > 0 || prevFade > 0) {
            active.add(EFFECT);
        }
    }

    /** SculkCamera for this frame: inverse(projection * view rotation) columns, camera position, strength, depth range. */
    public static ByteBuffer cameraUniform() {
        Minecraft minecraft = Minecraft.getInstance();
        Camera camera = minecraft.gameRenderer.mainCamera();
        Matrix4f inv = camera.getViewRotationProjectionMatrix(new Matrix4f()).invert();
        Vec3 pos = camera.position();
        float partial = minecraft.getDeltaTracker().getGameTimeDeltaPartialTick(false);
        float strength = Mth.lerp(partial, prevFade, fade);
        boolean zeroToOne = RenderSystem.getDevice().getDeviceInfo().isZZeroToOne();

        ByteBuffer data = BufferUtils.createByteBuffer(UNIFORM_BYTES);
        inv.get(data);                                         // 4 columns = InvViewProj0..3 (64 bytes)
        data.position(64);
        // camera position modulo 1024 keeps float precision; whole blocks, so the 16x16 texel grid stays aligned
        data.putFloat((float) (pos.x - Math.floor(pos.x / 1024.0) * 1024.0));
        data.putFloat((float) (pos.y - Math.floor(pos.y / 1024.0) * 1024.0));
        data.putFloat((float) (pos.z - Math.floor(pos.z / 1024.0) * 1024.0));
        data.putFloat(strength);
        data.putFloat(zeroToOne ? 1.0F : 0.0F).putFloat(0).putFloat(0).putFloat(0);
        data.flip();
        return data;
    }
}
