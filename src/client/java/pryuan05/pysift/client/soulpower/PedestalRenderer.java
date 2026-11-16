package pryuan05.pysift.client.soulpower;

import com.mojang.blaze3d.vertex.PoseStack;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.blockentity.BlockEntityRenderer;
import net.minecraft.client.renderer.blockentity.BlockEntityRendererProvider;
import net.minecraft.client.renderer.blockentity.state.BlockEntityRenderState;
import net.minecraft.client.renderer.feature.ModelFeatureRenderer;
import net.minecraft.client.renderer.item.ItemModelResolver;
import net.minecraft.client.renderer.item.ItemStackRenderState;
import net.minecraft.client.renderer.state.level.CameraRenderState;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraft.world.phys.Vec3;
import pryuan05.pysift.soulpower.ResonancePedestalBlock;

/** 共鳴台座上的東西：浮在台座上方，上下輕輕飄、慢慢轉。 */
public class PedestalRenderer implements BlockEntityRenderer<ResonancePedestalBlock.Entity, PedestalRenderer.State> {
    private final ItemModelResolver itemModels;

    public PedestalRenderer(BlockEntityRendererProvider.Context context) {
        this.itemModels = context.itemModelResolver();
    }

    @Override
    public State createRenderState() {
        return new State();
    }

    @Override
    public void extractRenderState(ResonancePedestalBlock.Entity be, State s, float partialTick, Vec3 cameraPos,
                                   ModelFeatureRenderer.CrumblingOverlay breakProgress) {
        BlockEntityRenderer.super.extractRenderState(be, s, partialTick, cameraPos, breakProgress);
        s.item.clear();
        if (be.getLevel() != null && !be.item().isEmpty()) {
            itemModels.updateForTopItem(s.item, be.item(), ItemDisplayContext.GROUND, be.getLevel(), null, (int) be.getBlockPos().asLong());
            s.time = be.getLevel().getGameTime() + partialTick;
        }
    }

    @Override
    public void submit(State s, PoseStack poseStack, SubmitNodeCollector collector, CameraRenderState camera) {
        if (s.item.isEmpty()) {
            return;
        }
        poseStack.pushPose();
        poseStack.translate(0.5f, 0.95f + (float) Math.sin(s.time * 0.08) * 0.05f, 0.5f);
        poseStack.rotateDegrees(com.mojang.math.Axis.YP, (s.time * 2f) % 360f);
        poseStack.scale(1.1f, 1.1f, 1.1f);
        s.item.submit(poseStack, collector, s.lightCoords, OverlayTexture.NO_OVERLAY, 0);
        poseStack.popPose();
    }

    public static class State extends BlockEntityRenderState {
        final ItemStackRenderState item = new ItemStackRenderState();
        float time;
    }
}
