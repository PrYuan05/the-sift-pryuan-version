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
 * 靈魂導線的兩樣動態外觀：
 * <ul>
 *   <li><b>包覆</b>：導線被一個完整方塊包起來時（{@link SoulConduitBlock.Entity#cover}），畫出那個方塊，導線本身藏在裡面。</li>
 *   <li><b>觸鬚</b>：導線的接頭只到自己這一格的邊緣，可是拉桿、按鈕、紅石火把這類小東西並不貼著那一面（地上的拉桿在格子中間，
 *       牆上的按鈕可能在對面那道牆）。替每個插頭或貼地接頭看一下隔壁方塊的外框：外框沒有碰到接頭的位置，就從接頭長出一條細細的
 *       幽匿脈，沿著軸向伸進隔壁那一格，再轉彎碰到那個元件。觸鬚由 2 px 的小方塊一節一節排成（不拉伸貼圖、彼此不重疊）。</li>
 * </ul>
 */
public class ConduitRenderer implements BlockEntityRenderer<SoulConduitBlock.Entity, ConduitRenderer.State> {
    private static final float T = 1f / 16f;           // 觸鬚的半徑：1 px（2 px 粗）
    private static final float PIECE = 2f / 16f;       // 一節的長度
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
        if (be.cover() != null) {   // a hair larger than the block, so it never fights the conduit's own end faces
            add(s, be.cover(), new Matrix4f().translate(0.5f, 0.5f, 0.5f).scale(1.002f).translate(-0.5f, -0.5f, -0.5f));
            return;
        }
        BlockState piece = SoulParts.of(switch (state.getValue(SoulConduitBlock.LOOK)) {
            case SOUL -> Part.TENDRIL_SOUL;
            case PLAIN -> Part.TENDRIL_PLAIN;
            case OFF -> Part.TENDRIL_OFF;
        });
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
            float[] from = {0.5f + dir.getStepX() * 0.5f, side == SoulConduitBlock.Side.LOW ? T : 0.5f + dir.getStepY() * 0.5f,
                    0.5f + dir.getStepZ() * 0.5f};
            double[] lo = {b.minX, b.minY, b.minZ}, hi = {b.maxX, b.maxY, b.maxZ};
            float[] to = new float[3];
            float far = 0;
            for (int i = 0; i < 3; i++) {       // the nearest point of the part, one pixel inside it; snapped to whole pixels
                double a = Math.min(lo[i] + T, (lo[i] + hi[i]) / 2), z = Math.max(hi[i] - T, (lo[i] + hi[i]) / 2);
                to[i] = Math.round(Math.clamp(from[i], a, z) * 16f) / 16f;
                far = Math.max(far, Math.abs(to[i] - from[i]));
            }
            if (far < 1.5f * T) {
                continue;                       // the part already sits against the connector
            }
            // along the connector's own axis first, then across (vertical last, so the tendril drops onto floor parts)
            int axis = dir.getAxis().ordinal();
            int[] order = axis == 1 ? new int[]{1, 0, 2} : new int[]{axis, axis == 0 ? 2 : 0, 1};
            float[] cur = from.clone();
            boolean first = true;
            for (int i : order) {
                float d = to[i] - cur[i];
                if (Math.abs(d) < 1e-4f) {
                    continue;
                }
                float sign = Math.signum(d);
                // a run covers the corner cube at its far end; the next run starts just past the corner it leaves
                float start = cur[i] + (first ? 0 : sign * T), end = to[i] + sign * T;
                run(s, piece, cur, i, start, end);
                cur[i] = to[i];
                first = false;
            }
        }
    }

    /** 沿著 axis 軸、從 start 到 end 排一列 2 px 的小方塊；最後一節不足 2 px 時只沿軸向縮短。 */
    private void run(State s, BlockState piece, float[] at, int axis, float start, float end) {
        float lo = Math.min(start, end), hi = Math.max(start, end);
        for (float p = lo; p < hi - 1e-4f; p += PIECE) {
            float len = Math.min(PIECE, hi - p);
            float[] o = {at[0] - T, at[1] - T, at[2] - T};
            o[axis] = p;
            float[] scale = {1f, 1f, 1f};
            scale[axis] = len / PIECE;
            add(s, piece, new Matrix4f().translate(o[0], o[1], o[2]).scale(scale[0], scale[1], scale[2]));
        }
    }

    private void add(State s, BlockState model, Matrix4f pose) {
        if (s.count == s.parts.size()) {
            s.parts.add(new BlockModelRenderState());
            s.poses.add(new Matrix4f());
        }
        blockModels.update(s.parts.get(s.count), model, BlockDisplayContext.create());
        s.poses.get(s.count).set(pose);
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
