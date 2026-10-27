package pryuan05.pysift.client.render;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.block.BlockModelRenderState;
import net.minecraft.client.renderer.block.BlockModelResolver;
import net.minecraft.client.renderer.block.model.BlockDisplayContext;
import net.minecraft.client.renderer.blockentity.BlockEntityRenderer;
import net.minecraft.client.renderer.blockentity.BlockEntityRendererProvider;
import net.minecraft.client.renderer.blockentity.state.BlockEntityRenderState;
import net.minecraft.client.renderer.feature.ModelFeatureRenderer;
import net.minecraft.client.renderer.state.level.CameraRenderState;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.core.Direction;
import net.minecraft.world.phys.Vec3;
import pryuan05.pysift.block.SoulSiftAxle;

/**
 * 靈魂隙浮輪軸的輪子：支架是一般的方塊模型，輪子（models/block/soul_sift_axle_wheel.json）在這裡依角度旋轉後畫出，
 * 和 Create 的齒輪、傳動軸同一個做法。角度與轉速在方塊實體（SoulSiftAxle.Entity）裡逐 tick 累加，這裡用 partialTick 內插。
 */
public class SoulSiftAxleRenderer implements BlockEntityRenderer<SoulSiftAxle.Entity, SoulSiftAxleRenderer.State> {
    private final BlockModelResolver blockModels;

    public SoulSiftAxleRenderer(BlockEntityRendererProvider.Context context) {
        this.blockModels = context.blockModelResolver();
    }

    @Override
    public State createRenderState() {
        return new State();
    }

    @Override
    public void extractRenderState(SoulSiftAxle.Entity axle, State state, float partialTick, Vec3 cameraPos,
                                   ModelFeatureRenderer.CrumblingOverlay breakProgress) {
        BlockEntityRenderer.super.extractRenderState(axle, state, partialTick, cameraPos, breakProgress);
        state.angle = axle.angle(partialTick);
        state.axis = axle.getBlockState().getValue(SoulSiftAxle.AXIS);
        blockModels.update(state.wheel, SoulSiftAxle.WHEEL.defaultBlockState(), BlockDisplayContext.create());
    }

    @Override
    public void submit(State s, PoseStack poseStack, SubmitNodeCollector collector, CameraRenderState camera) {
        poseStack.pushPose();
        poseStack.translate(0.5f, 0.5f, 0.5f);           // the wheel model turns around the block centre
        if (s.axis == Direction.Axis.Z) {
            poseStack.rotateDegrees(Axis.YP, 90.0f);     // same as the frame's blockstate y: 90
        }
        poseStack.rotateDegrees(Axis.XP, s.angle);
        poseStack.translate(-0.5f, -0.5f, -0.5f);
        s.wheel.submit(poseStack, collector, s.lightCoords, OverlayTexture.NO_OVERLAY, 0);
        poseStack.popPose();
    }

    public static class State extends BlockEntityRenderState {
        public final BlockModelRenderState wheel = new BlockModelRenderState();
        public float angle;
        public Direction.Axis axis = Direction.Axis.X;
    }
}
