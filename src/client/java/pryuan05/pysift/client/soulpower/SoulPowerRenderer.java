package pryuan05.pysift.client.soulpower;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.block.BlockModelRenderState;
import net.minecraft.client.renderer.block.BlockModelResolver;
import net.minecraft.client.renderer.block.model.BlockDisplayContext;
import net.minecraft.client.renderer.blockentity.BlockEntityRenderer;
import net.minecraft.client.renderer.blockentity.BlockEntityRendererProvider;
import net.minecraft.client.renderer.blockentity.state.BlockEntityRenderState;
import net.minecraft.client.renderer.feature.ModelFeatureRenderer;
import net.minecraft.client.renderer.item.ItemModelResolver;
import net.minecraft.client.renderer.item.ItemStackRenderState;
import net.minecraft.client.renderer.state.level.CameraRenderState;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.util.Mth;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;
import org.joml.Matrix4f;
import pryuan05.pysift.soulpower.CharoiteBeam;
import pryuan05.pysift.soulpower.CharoiteBeamBlockEntity;
import pryuan05.pysift.soulpower.KineticBlockEntity;
import pryuan05.pysift.soulpower.SoulCogBlock;
import pryuan05.pysift.soulpower.SoulGaugeBlock;
import pryuan05.pysift.soulpower.SoulGrinderBlockEntity;
import pryuan05.pysift.soulpower.SoulMachineBlock;
import pryuan05.pysift.soulpower.SoulParts;
import pryuan05.pysift.soulpower.SoulParts.Part;
import pryuan05.pysift.soulpower.SoulShaftBlock;
import pryuan05.pysift.soulpower.SoulShiftBlock;
import pryuan05.pysift.soulpower.SoulHandCrankBlock;
import pryuan05.pysift.soulpower.SoulFanBlock;
import pryuan05.pysift.soulpower.SoulSifterBlockEntity;
import pryuan05.pysift.soulpower.SoulVeinNodeBlockEntity;
import pryuan05.pysift.soulpower.ResonanceCoreBlockEntity;
import pryuan05.pysift.soulpower.ResonancePedestalBlock;
import pryuan05.pysift.soulpower.SoulWaveBlock;
import pryuan05.pysift.soulpower.SpiritEngineBlock;
import pryuan05.pysift.soulpower.SpiritPumpBlock;

import java.util.ArrayList;
import java.util.List;

/**
 * 靈魂動力的動畫（Create 的做法）：會動的部件（{@link SoulParts}）依「遊戲時間 × 轉速」算出的角度旋轉後畫出來，
 * 所以同一個網路裡所有東西完全同步。
 * <ul>
 *   <li>傳動軸：整根轉；齒輪：中心軸加齒盤，奇偶格錯開半齒，讓相鄰的齒卡在齒縫裡；</li>
 *   <li>靈液引擎：側面的飛輪轉動，頂上的活塞隨飛輪上下；</li>
 *   <li>研磨機：石磨轉動，正在磨的材料躺在石磨上跟著轉；</li>
 *   <li>振波發送／接收器：天線碟轉、外環反轉、晶核脈動；</li>
 *   <li>靈壓計：四面錶盤上的指針平滑擺到負載比例，超過 100% 發抖；</li>
 *   <li>過載：整台機器輕微抖動；轉速衝突：停住。</li>
 * </ul>
 */
public class SoulPowerRenderer implements BlockEntityRenderer<KineticBlockEntity, SoulPowerRenderer.State> {
    private static final float SMALL_COG_OFFSET = 22.5f;   // 8 齒：半齒 22.5°
    private static final float LARGE_COG_OFFSET = 11.25f;  // 16 齒：半齒 11.25°
    private final BlockModelResolver blockModels;
    private final ItemModelResolver itemModels;

    public SoulPowerRenderer(BlockEntityRendererProvider.Context context) {
        this.blockModels = context.blockModelResolver();
        this.itemModels = context.itemModelResolver();
    }

    @Override
    public State createRenderState() {
        return new State();
    }

    @Override
    public boolean shouldRenderOffScreen() {
        return true;   // 大齒輪比一格大
    }

    @Override
    public void extractRenderState(KineticBlockEntity be, State s, float partialTick, Vec3 cameraPos,
                                   ModelFeatureRenderer.CrumblingOverlay breakProgress) {
        BlockEntityRenderer.super.extractRenderState(be, s, partialTick, cameraPos, breakProgress);
        s.count = 0;
        s.item.clear();
        s.beams.clear();
        if (be.getLevel() == null) {
            return;
        }
        BlockState state = be.getBlockState();
        BlockPos pos = be.getBlockPos();
        double time = be.getLevel().getGameTime() + partialTick;
        float angle = be.angle(time);
        s.shake = be.isOverloaded() ? (float) Math.sin(time * 2.7 + pos.hashCode()) * 0.012f : 0f;

        if (state.getBlock() instanceof SoulCogBlock cog) {
            Direction.Axis axis = state.getValue(SoulShaftBlock.AXIS);
            boolean even = (perpendicularSum(pos, axis) & 1) == 0;
            float offset = cog.isLarge() ? (even ? 0f : LARGE_COG_OFFSET) : (even ? SMALL_COG_OFFSET : 0f);
            add(s, cog.isLarge() ? Part.LARGE_COG : Part.COG, spin(positive(axis), angle + offset));
        } else if (state.getBlock() instanceof SoulGaugeBlock) {
            Direction.Axis axis = state.getValue(SoulShaftBlock.AXIS);
            add(s, Part.SHAFT, spin(positive(axis), angle));
            float load = be.load();
            float needle = 135f - 270f * Mth.clamp(load, 0f, 1.08f);
            if (load > 1f) {
                needle += (float) Math.sin(time * 3.1) * 4f;      // 紅區：指針發抖
            }
            for (Direction face : Direction.values()) {
                if (face.getAxis() != axis) {
                    Matrix4f dial = spin(face, upright(face));
                    add(s, Part.DIAL, dial);
                    add(s, Part.NEEDLE, new Matrix4f(dial).translate(0.5f, 0f, 0.5f).rotateY(Mth.DEG_TO_RAD * needle).translate(-0.5f, 0f, -0.5f));
                }
            }
        } else if (state.getBlock() instanceof SoulShiftBlock shift) {
            // 兩段半軸：負方向那段跟著網路轉；正方向那段在換向器通電時反轉、在離合器分開時跟著另一頭（或停住）
            Direction.Axis axis = state.getValue(SoulShaftBlock.AXIS);
            Direction pos2 = positive(axis), neg = pos2.getOpposite();
            add(s, Part.HALF_SHAFT, spin(neg, angle * sign(neg)));
            float other = be.speed();
            if (state.getValue(SoulShiftBlock.SHIFTED)) {
                other = shift.gearshift ? -be.speed()
                        : be.getLevel().getBlockEntity(pos.relative(pos2)) instanceof KineticBlockEntity k ? k.speed() : 0f;
            }
            add(s, Part.HALF_SHAFT, spin(pos2, (float) ((time * other * 0.3) % 360.0)));
        } else if (state.getBlock() instanceof SoulHandCrankBlock || state.getBlock() instanceof SoulFanBlock) {
            Direction facing = state.getValue(SoulMachineBlock.FACING);
            add(s, state.getBlock() instanceof SoulFanBlock ? Part.FAN : Part.CRANK, spin(facing, angle * sign(facing)));
        } else if (state.getBlock() instanceof SoulShaftBlock) {
            add(s, Part.SHAFT, spin(positive(state.getValue(SoulShaftBlock.AXIS)), angle));
        } else if (state.getBlock() instanceof SpiritEngineBlock) {
            Direction facing = state.getValue(SoulMachineBlock.FACING);
            Direction side = facing.getClockWise();
            add(s, Part.SHAFT, spin(positive(side.getAxis()), angle));
            add(s, Part.FLYWHEEL, spin(side, angle * sign(side)));
            float bob = (float) Math.sin(Mth.DEG_TO_RAD * angle * sign(side)) * 0.07f;
            add(s, Part.PISTON, yaw(facing).translate(0, bob, 0));
        } else if (state.getBlock() instanceof SoulWaveBlock wave) {
            Direction facing = state.getValue(SoulMachineBlock.FACING);
            float a = angle * sign(facing);
            add(s, wave.emitter ? Part.EMITTER_DISH : Part.RECEIVER_DISH, spin(facing, a));
            add(s, Part.WAVE_RING, spin(facing, -a * 0.5f));
            float pulse = be.speed() == 0 ? 1f : 1f + 0.12f * (float) Math.sin(time * 0.35);
            add(s, Part.WAVE_CORE, spin(facing, a * 0.25f).translate(0.5f, 0.6f, 0.5f).scale(pulse).translate(-0.5f, -0.6f, -0.5f));
        } else if (state.getBlock() instanceof SpiritPumpBlock) {
            // 側面的曲柄輪轉動（朝上下擺時，曲柄在東側）
            Direction facing = state.getValue(SoulMachineBlock.FACING);
            Direction side = facing.getAxis() == Direction.Axis.Y ? Direction.EAST : facing.getClockWise();
            add(s, Part.SHAFT, spin(positive(side.getAxis()), angle));
            add(s, Part.FLYWHEEL, spin(side, angle * sign(side)));
        } else if (be instanceof ResonanceCoreBlockEntity core) {
            add(s, Part.WAVE_RING, spin(Direction.UP, angle).translate(0f, 0.25f, 0f));
            add(s, Part.WAVE_RING, spin(Direction.UP, -angle * 1.5f).translate(0f, 0.35f, 0f));
            ItemStack item = core.item();
            if (!item.isEmpty()) {
                float bob = (float) Math.sin(time * 0.08) * 0.05f;
                itemModels.updateForTopItem(s.item, item, ItemDisplayContext.GROUND, be.getLevel(), null, (int) pos.asLong());
                s.itemPose = new Matrix4f().translate(0.5f, 1.05f + bob, 0.5f).rotateY((float) (time * 0.05)).scale(1.2f);
            }
            if (core.crafting()) {
                for (BlockPos p : ResonanceCoreBlockEntity.ring(pos)) {
                    if (be.getLevel().getBlockEntity(p) instanceof ResonancePedestalBlock.Entity pedestal && !pedestal.item().isEmpty()) {
                        BlockPos rel = p.subtract(pos);
                        float dx = -rel.getX(), dz = -rel.getZ();
                        float len = (float) Math.sqrt(dx * dx + dz * dz);
                        s.beams.add(new float[]{rel.getX() + 0.5f, 1.1f, rel.getZ() + 0.5f, dx / len, 0f, dz / len, len});
                    }
                }
                s.time = (float) time;
            }
        } else if (be instanceof SoulVeinNodeBlockEntity) {
            add(s, Part.WAVE_CORE, spin(Direction.UP, angle).translate(0f, -0.15f, 0f));
            add(s, Part.WAVE_RING, spin(Direction.UP, -angle * 0.5f).translate(0f, -0.2f, 0f));
        } else if (be instanceof CharoiteBeamBlockEntity beam) {
            Direction facing = state.getValue(SoulMachineBlock.FACING);
            add(s, Part.LENS, spin(facing, angle * sign(facing)));
            if (beam.isEmitter() && be.speed() != 0) {
                for (CharoiteBeam.Segment seg : CharoiteBeam.trace(be.getLevel(), pos, facing).segments()) {
                    BlockPos rel = seg.from().subtract(pos);
                    s.beams.add(new float[]{rel.getX() + 0.5f, rel.getY() + 0.5f, rel.getZ() + 0.5f,
                            seg.dir().getStepX(), seg.dir().getStepY(), seg.dir().getStepZ(), seg.length()});
                }
                s.time = (float) time;
            }
        } else if (be instanceof SoulSifterBlockEntity sifter) {
            // 曲柄輪在右手邊轉，篩網沿著朝向前後搖晃（每圈兩下），正在篩的東西躺在篩網上一起晃
            Direction facing = state.getValue(SoulMachineBlock.FACING);
            Direction side = facing.getClockWise();
            add(s, Part.SHAFT, spin(positive(side.getAxis()), angle));
            add(s, Part.FLYWHEEL, spin(side, angle * sign(side)));
            float shake = (float) Math.sin(Mth.DEG_TO_RAD * angle * 2f) * 0.055f;
            add(s, Part.SIEVE, yaw(facing).translate(0f, 0f, shake));
            ItemStack input = sifter.input();
            if (!input.isEmpty()) {
                itemModels.updateForTopItem(s.item, input, ItemDisplayContext.FIXED, be.getLevel(), null, (int) pos.asLong());
                s.itemPose = yaw(facing).translate(6.5f / 16f, 10.1f / 16f, 0.5f + shake).rotateX(Mth.HALF_PI).scale(0.35f);
            }
        } else if (be instanceof SoulGrinderBlockEntity grinder) {
            add(s, Part.MILLSTONE, spin(Direction.UP, angle));
            ItemStack input = grinder.input();
            if (!input.isEmpty()) {
                itemModels.updateForTopItem(s.item, input, ItemDisplayContext.FIXED, be.getLevel(), null, (int) pos.asLong());
                s.itemPose = new Matrix4f().translate(0.5f, 15.6f / 16f, 0.5f).rotateY(Mth.DEG_TO_RAD * angle)
                        .rotateX(Mth.HALF_PI).scale(0.375f);
            }
        }
    }

    /** 渲染時要畫的部件（狀態與變換）。 */
    private void add(State s, Part part, Matrix4f pose) {
        if (s.count == s.parts.size()) {
            s.parts.add(new BlockModelRenderState());
            s.poses.add(new Matrix4f());
        }
        blockModels.update(s.parts.get(s.count), SoulParts.of(part), BlockDisplayContext.create());
        s.poses.get(s.count).set(pose);
        s.count++;
    }

    /** 部件都繞 Y 軸建模：先把 +Y 轉到 dir，再繞它轉 angle 度（以方塊中心為原點）。 */
    static Matrix4f spin(Direction dir, float angle) {
        Matrix4f m = new Matrix4f().translate(0.5f, 0.5f, 0.5f);
        switch (dir) {
            case DOWN -> m.rotateX(Mth.PI);
            case NORTH -> m.rotateX(-Mth.HALF_PI);
            case SOUTH -> m.rotateX(Mth.HALF_PI);
            case EAST -> m.rotateZ(-Mth.HALF_PI);
            case WEST -> m.rotateZ(Mth.HALF_PI);
            default -> {
            }
        }
        return m.rotateY(Mth.DEG_TO_RAD * angle).translate(-0.5f, -0.5f, -0.5f);
    }

    /** 和方塊狀態的 y 旋轉一樣（模型朝北），用在不會轉的部件（活塞）。 */
    private static Matrix4f yaw(Direction facing) {
        return new Matrix4f().translate(0.5f, 0.5f, 0.5f).rotateY(-Mth.DEG_TO_RAD * facing.toYRot() + Mth.PI)
                .translate(-0.5f, -0.5f, -0.5f);
    }

    /** 錶盤轉正：側面的錶盤上方朝上。 */
    private static float upright(Direction face) {
        return switch (face) {
            case NORTH -> 180f;
            case EAST -> 90f;
            case WEST -> -90f;
            default -> 0f;
        };
    }

    private static Direction positive(Direction.Axis axis) {
        return Direction.fromAxisAndDirection(axis, Direction.AxisDirection.POSITIVE);
    }

    /** 部件朝負方向擺時，同樣的轉速要反著轉，才會和同軸的傳動軸一致。 */
    private static float sign(Direction dir) {
        return dir.getAxisDirection() == Direction.AxisDirection.POSITIVE ? 1f : -1f;
    }

    private static int perpendicularSum(BlockPos pos, Direction.Axis axis) {
        return switch (axis) {
            case X -> pos.getY() + pos.getZ();
            case Y -> pos.getX() + pos.getZ();
            case Z -> pos.getX() + pos.getY();
        };
    }

    @Override
    public void submit(State s, PoseStack poseStack, SubmitNodeCollector collector, CameraRenderState camera) {
        poseStack.pushPose();
        if (s.shake != 0f) {
            poseStack.translate(s.shake, 0f, -s.shake * 0.7f);
        }
        for (int i = 0; i < s.count; i++) {
            poseStack.pushPose();
            poseStack.mulPose(s.poses.get(i));
            s.parts.get(i).submit(poseStack, collector, s.lightCoords, OverlayTexture.NO_OVERLAY, 0);
            poseStack.popPose();
        }
        if (!s.beams.isEmpty()) {
            collector.submitCustomGeometry(poseStack, RenderTypes.lightning(), (pose, vc) -> {
                for (float[] b : s.beams) {
                    beam(vc, pose, b, s.time);
                }
            });
        }
        if (!s.item.isEmpty()) {
            poseStack.pushPose();
            poseStack.mulPose(s.itemPose);
            s.item.submit(poseStack, collector, s.lightCoords, OverlayTexture.NO_OVERLAY, 0);
            poseStack.popPose();
        }
        poseStack.popPose();
    }

    // ---------------------------------------------------------------- 紫龍晶光束
    private static final float CORE = 0.05f, GLOW = 0.14f, PIECE = 0.5f;

    /** 一段光束：兩片交叉的面（核心＋外暈），切成 0.5 格一段，亮度沿著光束往前流動。 */
    private static void beam(VertexConsumer vc, PoseStack.Pose pose, float[] b, float time) {
        float x = b[0], y = b[1], z = b[2], dx = b[3], dy = b[4], dz = b[5], len = b[6];
        // two directions across the beam
        float ax = dy != 0 ? 1 : 0, ay = dy != 0 ? 0 : 1, az = 0;
        float bx = dy * az - dz * ay, by = dz * ax - dx * az, bz = dx * ay - dy * ax;
        for (float d = 0; d < len - 1e-3f; d += PIECE) {
            float e = Math.min(len, d + PIECE);
            float flow = 0.5f + 0.5f * (float) Math.sin(d * 2.4f - time * 0.45f);
            int core = argb((int) (150 + 100 * flow), 235, 205, 255);
            int glow = argb((int) (40 + 60 * flow), 160, 80, 230);
            for (int k = 0; k < 2; k++) {
                float ux = k == 0 ? ax : bx, uy = k == 0 ? ay : by, uz = k == 0 ? az : bz;
                strip(vc, pose, x + dx * d, y + dy * d, z + dz * d, x + dx * e, y + dy * e, z + dz * e, ux, uy, uz, CORE, core);
                strip(vc, pose, x + dx * d, y + dy * d, z + dz * d, x + dx * e, y + dy * e, z + dz * e, ux, uy, uz, GLOW, glow);
            }
        }
    }

    /** 一片雙面的長條：從 p0 到 p1，寬度往 ±u 方向各 w。 */
    private static void strip(VertexConsumer vc, PoseStack.Pose pose, float x0, float y0, float z0, float x1, float y1, float z1,
                              float ux, float uy, float uz, float w, int color) {
        float[][] q = {{x0 - ux * w, y0 - uy * w, z0 - uz * w}, {x0 + ux * w, y0 + uy * w, z0 + uz * w},
                {x1 + ux * w, y1 + uy * w, z1 + uz * w}, {x1 - ux * w, y1 - uy * w, z1 - uz * w}};
        for (int i : new int[]{0, 1, 2, 3, 3, 2, 1, 0}) {
            vc.addVertex(pose, q[i][0], q[i][1], q[i][2]).setColor(color);
        }
    }

    private static int argb(int a, int r, int g, int b) {
        return Math.clamp(a, 0, 255) << 24 | r << 16 | g << 8 | b;
    }

    public static class State extends BlockEntityRenderState {
        final List<float[]> beams = new ArrayList<>();
        float time;
        final List<BlockModelRenderState> parts = new ArrayList<>();
        final List<Matrix4f> poses = new ArrayList<>();
        int count;
        float shake;
        final ItemStackRenderState item = new ItemStackRenderState();
        Matrix4f itemPose = new Matrix4f();
    }
}
