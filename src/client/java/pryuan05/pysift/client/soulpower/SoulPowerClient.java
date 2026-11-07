package pryuan05.pysift.client.soulpower;

import net.fabricmc.fabric.api.client.rendering.v1.BlockEntityRendererRegistry;
import net.minecraft.client.gui.Font;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.screens.MenuScreens;
import net.minecraft.client.gui.screens.inventory.AbstractContainerScreen;
import net.minecraft.client.renderer.RenderPipelines;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.world.entity.player.Inventory;
import pryuan05.pysift.PySift;
import pryuan05.pysift.soulpower.SoulGrinderMenu;
import pryuan05.pysift.soulpower.SoulPower;
import pryuan05.pysift.soulpower.SpiritEngineMenu;

/**
 * 靈魂動力機器的介面（底圖由 tools/progression/build_soul_power.py 從原版熔爐介面改出來）：
 * 右側顯示轉速、靈壓容量與需求；過載時改成紅字。
 */
public final class SoulPowerClient {
    private static final int TEXT = 0xFF404040;
    private static final int SOUL = 0xFF3FB8C8;
    private static final int DANGER = 0xFFD03A3A;

    private SoulPowerClient() {
    }

    public static void register() {
        MenuScreens.register(SoulPower.SPIRIT_ENGINE_MENU, EngineScreen::new);
        MenuScreens.register(SoulPower.SOUL_GRINDER_MENU, GrinderScreen::new);
        // Create 式的轉動動畫：所有靈魂動力方塊共用一個渲染器
        animate(SoulPower.SOUL_KINETIC_ENTITY);
        animate(SoulPower.SOUL_GAUGE_ENTITY);
        animate(SoulPower.SPIRIT_ENGINE_ENTITY);
        animate(SoulPower.SOUL_WAVE_ENTITY);
        animate(SoulPower.SOUL_GRINDER_ENTITY);
        animate(SoulPower.SOUL_SIFTER_ENTITY);
        animate(SoulPower.CHAROITE_BEAM_ENTITY);
        animate(SoulPower.SOUL_VEIN_NODE_ENTITY);
        animate(SoulPower.SPIRIT_PUMP_ENTITY);
        animate(SoulPower.SOUL_HAND_CRANK_ENTITY);
        animate(SoulPower.SOUL_FAN_ENTITY);
    }

    private static <E extends pryuan05.pysift.soulpower.KineticBlockEntity> void animate(net.minecraft.world.level.block.entity.BlockEntityType<E> type) {
        net.minecraft.client.renderer.blockentity.BlockEntityRendererProvider<pryuan05.pysift.soulpower.KineticBlockEntity, SoulPowerRenderer.State> provider = SoulPowerRenderer::new;
        BlockEntityRendererRegistry.register(type, provider);
    }

    /** 右側三行：轉速、容量、需求（過載時第三行變成「過載！」）。 */
    private static void status(GuiGraphicsExtractor g, Font font, int x, int speed, int capacity, int stress, boolean overloaded) {
        g.text(font, Component.translatable("gui.pysift.soul_power.speed", speed), x, 20, TEXT, false);
        g.text(font, Component.translatable("gui.pysift.soul_power.capacity", capacity), x, 32, TEXT, false);
        g.text(font, overloaded ? Component.translatable("gui.pysift.soul_power.overloaded")
                : Component.translatable("gui.pysift.soul_power.stress", stress), x, 44, overloaded ? DANGER : TEXT, false);
    }

    static final class EngineScreen extends AbstractContainerScreen<SpiritEngineMenu> {
        private static final Identifier BG = PySift.id("textures/gui/container/spirit_engine.png");

        EngineScreen(SpiritEngineMenu menu, Inventory inventory, Component title) {
            super(menu, inventory, title);
        }

        @Override
        public void extractBackground(GuiGraphicsExtractor g, int mouseX, int mouseY, float partialTick) {
            super.extractBackground(g, mouseX, mouseY, partialTick);
            g.blit(RenderPipelines.GUI_TEXTURED, BG, leftPos, topPos, 0, 0, imageWidth, imageHeight, 256, 256);
            // the fuel left: a soul-blue bar where the furnace flame is (56,36, 14 x 14)
            int h = Math.round(menu.burnProgress() * 14);
            if (h > 0) {
                g.fill(leftPos + 57, topPos + 37 + 14 - h, leftPos + 71, topPos + 51, SOUL);
            }
        }

        @Override
        protected void extractLabels(GuiGraphicsExtractor g, int mouseX, int mouseY) {
            super.extractLabels(g, mouseX, mouseY);
            status(g, font, 84, menu.speed(), menu.capacity(), menu.stress(), menu.overloaded());
        }
    }

    static final class GrinderScreen extends AbstractContainerScreen<SoulGrinderMenu> {
        private static final Identifier BG = PySift.id("textures/gui/container/soul_grinder.png");

        GrinderScreen(SoulGrinderMenu menu, Inventory inventory, Component title) {
            super(menu, inventory, title);
        }

        @Override
        public void extractBackground(GuiGraphicsExtractor g, int mouseX, int mouseY, float partialTick) {
            super.extractBackground(g, mouseX, mouseY, partialTick);
            g.blit(RenderPipelines.GUI_TEXTURED, BG, leftPos, topPos, 0, 0, imageWidth, imageHeight, 256, 256);
            // progress over the arrow (79,34, 24 x 16)
            int w = Math.round(menu.progress() * 24);
            if (w > 0) {
                g.fill(leftPos + 80, topPos + 39, leftPos + 80 + w, topPos + 45, menu.overloaded() ? DANGER : SOUL);
            }
        }

        @Override
        protected void extractLabels(GuiGraphicsExtractor g, int mouseX, int mouseY) {
            super.extractLabels(g, mouseX, mouseY);
            g.text(font, Component.translatable(menu.speed() > 0 ? "gui.pysift.soul_power.running" : "gui.pysift.soul_power.idle",
                    menu.speed()), 8, 64, menu.overloaded() ? DANGER : TEXT, false);
        }
    }
}
