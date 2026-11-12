package pryuan05.pysift.client.soulpower;

import com.mojang.blaze3d.vertex.PoseStack;
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
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import net.minecraft.world.phys.shapes.VoxelShape;
import org.joml.Matrix4f;
import pryuan05.pysift.soulpower.SoulConductor;
import pryuan05.pysift.soulpower.SoulConduitBlock;
import pryuan05.pysift.soulpower.SoulParts;
import pryuan05.pysift.soulpower.SoulParts.Part;

import java.util.ArrayList;
import java.util.List;

/**
 * 靈魂導線的「觸鬚」：導線的接頭只到自己這一格的邊緣，可是拉桿、按鈕、紅石火把、絆線鉤這類小東西並不貼著那一面
 * （地上的拉桿在格子中間，牆上的按鈕可能在對面那道牆）。這裡替每個插頭或貼地接頭看一下隔壁方塊的外框：
 * 外框沒有碰到接頭的位置，就從接頭長出一條細細的幽匿脈，沿著軸向伸進隔壁那一格，再轉彎碰到那個元件。
 * 隔壁是整塊的方塊（紅石燈、活塞…）或本來就貼著地面接得到的（紅石粉、鐵軌、中繼器）時什麼都不畫。
 */
public class ConduitRenderer implements BlockEntityRenderer<SoulConduitBlock.Entity, ConduitRenderer.State> {
    private static final float T = 1f / 16f;           // 觸鬚的半徑：1 px（2 px 粗）
    private final BlockModelResolver blockModels;

    public ConduitRenderer(BlockEntityRendererProvider.Context context) {
        this.blockModels = context.blockModelResolver();
    }

    @Override
    public State createRenderState() {
        return new State();
    }

    @Override
    public boolean shouldRenderOffScreen() {
        return true;    // 觸鬚伸到隔壁那一格
    }

    @Override
    public void extractRenderState(SoulConduitBlock.Entity be, State s, float partialTick, Vec3 cameraPos,
                                   ModelFeatureRenderer.CrumblingOverlay breakProgress) {
        BlockEntityRenderer.super.extractRenderState(be, s, partialTick, cameraPos, breakProgress);
        s.count = 0;
        Level level = be.getLevel();
        BlockState state = be.getBlockState();
        if (level == null || !(state.getBlock() instanceof SoulConduitBlock)) {
            return;
        }
        Part part = switch (state.getValue(SoulConduitBlock.LOOK)) {
            case SOUL -> Part.TENDRIL_SOUL;
            case PLAIN -> Part.TENDRIL_PLAIN;
            case OFF -> Part.TENDRIL_OFF;
        };
        BlockPos pos = be.getBlockPos();
        for (Direction dir : Direction.values()) {
            SoulConduitBlock.Side side = state.getValue(SoulConduitBlock.SIDES.get(dir));
            if (side != SoulConduitBlock.Side.PLUG && side != SoulConduitBlock.Side.LOW) {
                continue;
            }
            BlockPos np = pos.relative(dir);
            BlockState ns = level.getBlockState(np);
            if (ns.getBlock() instanceof SoulConductor) {
                continue;
            }
            VoxelShape shape = ns.getShape(level, np);
            if (shape.isEmpty()) {
                continue;
            }
            AABB b = shape.bounds().move(dir.getStepX(), dir.getStepY(), dir.getStepZ());     // in this block's coordinates
            // where the connector ends: the middle of the shared face (plug) or its bottom edge (low)
            double[] from = {0.5 + dir.getStepX() * 0.5, side == SoulConduitBlock.Side.LOW ? T : 0.5 + dir.getStepY() * 0.5,
                    0.5 + dir.getStepZ() * 0.5};
            double[] lo = {b.minX, b.minY, b.minZ}, hi = {b.maxX, b.maxY, b.maxZ};
            double[] to = new double[3];
            double far = 0;
            for (int i = 0; i < 3; i++) {       // the nearest point of the part, one pixel inside it
                double a = Math.min(lo[i] + T, (lo[i] + hi[i]) / 2), z = Math.max(hi[i] - T, (lo[i] + hi[i]) / 2);
                to[i] = Math.clamp(from[i], a, z);
                far = Math.max(far, Math.abs(to[i] - from[i]));
            }
            if (far < 1.5 * T) {
                continue;                       // the part already sits against the connector
            }
            // along the connector's own axis first, then across (vertical last, so the tendril drops onto floor parts)
            int axis = dir.getAxis().ordinal();
            int[] order = axis == 1 ? new int[]{1, 0, 2} : new int[]{axis, axis == 0 ? 2 : 0, 1};
            double[] cur = from.clone();
            for (int i : order) {
                if (Math.abs(to[i] - cur[i]) < 1e-4) {
                    continue;
                }
                double[] next = cur.clone();
                next[i] = to[i];
                segment(s, part, cur, next);
                cur = next;
            }
        }
    }

    /** 一段軸向的觸鬚：部件是 1×1×1 的方塊，縮放成 2 px 粗、兩端各多出 1 px（轉角才會接起來）。 */
    private void segment(State s, Part part, double[] a, double[] b) {
        float x0 = (float) Math.min(a[0], b[0]) - T, y0 = (float) Math.min(a[1], b[1]) - T, z0 = (float) Math.min(a[2], b[2]) - T;
        float x1 = (float) Math.max(a[0], b[0]) + T, y1 = (float) Math.max(a[1], b[1]) + T, z1 = (float) Math.max(a[2], b[2]) + T;
        if (s.count == s.parts.size()) {
            s.parts.add(new BlockModelRenderState());
            s.poses.add(new Matrix4f());
        }
        blockModels.update(s.parts.get(s.count), SoulParts.of(part), BlockDisplayContext.create());
        s.poses.get(s.count).identity().translate(x0, y0, z0).scale(x1 - x0, y1 - y0, z1 - z0);
        s.count++;
    }

    @Override
    public void submit(State s, PoseStack poseStack, SubmitNodeCollector collector, CameraRenderState camera) {
        for (int i = 0; i < s.count; i++) {
            poseStack.pushPose();
            poseStack.mulPose(s.poses.get(i));
            s.parts.get(i).submit(poseStack, collector, s.lightCoords, OverlayTexture.NO_OVERLAY, 0);
            poseStack.popPose();
        }
    }

    public static class State extends BlockEntityRenderState {
        final List<BlockModelRenderState> parts = new ArrayList<>();
        final List<Matrix4f> poses = new ArrayList<>();
        int count;
    }
}
