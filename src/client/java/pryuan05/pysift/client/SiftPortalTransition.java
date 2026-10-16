package pryuan05.pysift.client;

import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.rendering.v1.hud.HudElementRegistry;
import net.fabricmc.fabric.api.client.rendering.v1.hud.VanillaHudElements;
import net.minecraft.client.DeltaTracker;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.client.renderer.RenderPipelines;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.resources.Identifier;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.phys.AABB;
import pryuan05.pysift.PySift;
import pryuan05.pysift.block.ModBlocks;
import pryuan05.pysift.block.SiftPortalBlock;

/**
 * 走進篩靈界傳送門時的過場動畫（只在用戶端）：
 * <ol>
 *   <li>充能：站在門裡的 {@value SiftPortalBlock#PLAYER_TRANSITION_TICKS} tick（與伺服器的傳送延遲相同）內，
 *       畫面逐漸被門面的珠光虹彩（sift_portal_large_canvas.png，兩層反向流動）蓋住，邊緣先亮；
 *       四周的光點往玩家身上旋轉聚攏，一進門時響起上揚的鳴音。</li>
 *   <li>傳送前最後 30%：整個畫面轉為暖白強光。</li>
 *   <li>抵達：換維度後白光閃一下再在約 1 秒內淡出，虹彩跟著退去。</li>
 * </ol>
 * 走出門外時充能值以兩倍速度退回（伺服器端的傳送進度也會同樣歸零）。
 */
public final class SiftPortalTransition {
    private static final Identifier LAYER = PySift.id("sift_portal_transition");
    private static final Identifier CANVAS = PySift.id("textures/block/sift_portal_large_canvas.png");
    private static final int CANVAS_W = 256, CANVAS_H = 128;
    private static final int FLASH_TICKS = 24;

    private static float charge, prevCharge;     // 0..1：在門裡待了多久
    private static float flash, prevFlash;       // 0..1：抵達時的白光
    private static boolean wasInside;
    private static ClientLevel lastLevel;

    private SiftPortalTransition() {
    }

    public static void register() {
        ClientTickEvents.END_CLIENT_TICK.register(SiftPortalTransition::tick);
        HudElementRegistry.attachElementAfter(VanillaHudElements.MISC_OVERLAYS, LAYER, SiftPortalTransition::render);
    }

    private static void tick(Minecraft minecraft) {
        prevCharge = charge;
        prevFlash = flash;
        LocalPlayer player = minecraft.player;
        if (player == null || minecraft.level == null) {
            charge = prevCharge = flash = prevFlash = 0;
            wasInside = false;
            lastLevel = null;
            return;
        }
        if (lastLevel != null && minecraft.level != lastLevel && charge > 0.5F) {
            flash = prevFlash = 1.0F;            // 剛穿過門：抵達的白光
        }
        lastLevel = minecraft.level;

        boolean inside = insidePortal(player);
        if (inside) {
            if (!wasInside) {
                player.playSound(SoundEvents.PORTAL_TRIGGER, 0.35F, 1.6F);
                player.playSound(SoundEvents.AMETHYST_BLOCK_RESONATE, 0.8F, 0.7F);
            }
            charge = Math.min(1.0F, charge + 1.0F / SiftPortalBlock.PLAYER_TRANSITION_TICKS);
            swirl(minecraft.level, player, charge);
        } else {
            charge = Math.max(0.0F, charge - 2.0F / SiftPortalBlock.PLAYER_TRANSITION_TICKS);
        }
        wasInside = inside;
        flash = Math.max(0.0F, flash - 1.0F / FLASH_TICKS);
    }

    private static boolean insidePortal(LocalPlayer player) {
        AABB box = player.getBoundingBox().deflate(1.0E-3);
        for (BlockPos pos : BlockPos.betweenClosed(BlockPos.containing(box.minX, box.minY, box.minZ),
                BlockPos.containing(box.maxX, box.maxY, box.maxZ))) {
            if (player.level().getBlockState(pos).is(ModBlocks.SIFT_PORTAL)) {
                return true;
            }
        }
        return false;
    }

    /** 光點從玩家四周 1.5～2.5 格處旋轉著往身上聚攏，越接近傳送越密。 */
    private static void swirl(ClientLevel level, LocalPlayer player, float charge) {
        RandomSource random = level.getRandom();
        int count = 1 + Math.round(charge * 4);
        for (int i = 0; i < count; i++) {
            double angle = random.nextDouble() * Math.PI * 2;
            double radius = 1.5 + random.nextDouble();
            double x = player.getX() + Math.cos(angle) * radius;
            double y = player.getY() + random.nextDouble() * 2.2;
            double z = player.getZ() + Math.sin(angle) * radius;
            double tangent = 0.08;
            level.addParticle(random.nextInt(3) == 0 ? ParticleTypes.END_ROD : ParticleTypes.PORTAL, x, y, z,
                    (player.getX() - x) * 0.08 - Math.sin(angle) * tangent, 0.01,
                    (player.getZ() - z) * 0.08 + Math.cos(angle) * tangent);
        }
    }

    private static void render(GuiGraphicsExtractor graphics, DeltaTracker delta) {
        float partial = delta.getGameTimeDeltaPartialTick(false);
        float c = Mth.lerp(partial, prevCharge, charge);
        float f = Mth.lerp(partial, prevFlash, flash);
        if (c <= 0 && f <= 0) {
            return;
        }
        int w = graphics.guiWidth(), h = graphics.guiHeight();
        float shimmer = Mth.clamp(Math.max(smooth(c), f * 0.8F), 0.0F, 1.0F);
        if (shimmer > 0) {
            float time = (Minecraft.getInstance().level == null ? 0 : Minecraft.getInstance().level.getGameTime()) + partial;
            // 兩層虹彩：取畫布中 128×64 的一塊鋪滿畫面，兩層以不同速度、反向緩慢游移
            canvasLayer(graphics, w, h, 64 + 60 * Mth.sin(time * 0.021F), 32 + 30 * Mth.cos(time * 0.017F), shimmer * 0.75F);
            canvasLayer(graphics, w, h, 64 - 60 * Mth.sin(time * 0.013F + 1.7F), 32 - 30 * Mth.sin(time * 0.019F), shimmer * 0.4F);
            // 邊緣先亮：上下的暖光漸層
            int edge = argb(shimmer * 0.55F, 0xFFF4D8);
            graphics.fillGradient(0, 0, w, h / 3, edge, 0x00FFF4D8);
            graphics.fillGradient(0, h - h / 3, w, h, 0x00FFF4D8, edge);
        }
        // 傳送前最後 30% 的白光，以及抵達時的閃光
        float white = Math.max(Mth.clamp((c - 0.7F) / 0.3F, 0.0F, 1.0F) * 0.9F, f);
        if (white > 0) {
            graphics.fill(0, 0, w, h, argb(white, 0xFFF8EE));
        }
    }

    private static void canvasLayer(GuiGraphicsExtractor graphics, int w, int h, float u, float v, float alpha) {
        graphics.blit(RenderPipelines.GUI_TEXTURED, CANVAS, 0, 0, u, v, w, h, 128, 64, CANVAS_W, CANVAS_H, argb(alpha, 0xFFFFFF));
    }

    private static float smooth(float t) {
        return t * t * (3 - 2 * t);
    }

    private static int argb(float alpha, int rgb) {
        return (Mth.clamp(Math.round(alpha * 255), 0, 255) << 24) | (rgb & 0xFFFFFF);
    }
}
