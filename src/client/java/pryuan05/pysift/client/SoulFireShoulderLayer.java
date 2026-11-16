package pryuan05.pysift.client;

import com.geckolib.animatable.GeoAnimatable;
import com.geckolib.cache.model.GeoBone;
import com.geckolib.renderer.base.GeoRenderState;
import com.geckolib.renderer.base.GeoRenderer;
import com.geckolib.renderer.layer.builtin.BlockAndItemGeoLayer;
import com.mojang.blaze3d.vertex.PoseStack;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.block.BlockModelRenderState;
import net.minecraft.client.renderer.block.model.BlockDisplayContext;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.state.EntityRenderState;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.util.LightCoordsUtil;
import net.minecraft.world.level.block.Blocks;
import org.jspecify.annotations.Nullable;

import java.util.ArrayList;
import java.util.List;

/**
 * 在指定骨骼上畫原版靈魂火方塊（{@link Blocks#SOUL_FIRE}）：貼圖與閃動動畫都直接用原版的 soul_fire_0 / soul_fire_1，
 * 全亮度渲染。骨骼的位移、旋轉、縮放都會套用，所以動畫裡對該骨骼做的縮放（火焰跳動）也會作用在火上。
 * 火焰的底部中心放在骨骼 pivot 上，大小為 {@code size} 格（模型單位，之後再乘上生物的 SCALE）。
 */
public class SoulFireShoulderLayer<T extends GeoAnimatable, O, R extends GeoRenderState> extends BlockAndItemGeoLayer<T, O, R> {
    private static final BlockDisplayContext DISPLAY_CONTEXT = BlockDisplayContext.create();
    private final List<String> bones;
    private final float size;

    public SoulFireShoulderLayer(EntityRendererProvider.Context context, GeoRenderer<T, O, R> renderer, float size, String... bones) {
        super(context, renderer);
        this.bones = List.of(bones);
        this.size = size;
    }

    @Override
    protected List<RenderData> getRelevantBones(T animatable, @Nullable O relatedObject, R renderState, float partialTick) {
        List<RenderData> out = new ArrayList<>(this.bones.size());
        for (String bone : this.bones) {
            BlockModelRenderState fire = new BlockModelRenderState();
            this.blockModelResolver.update(fire, Blocks.SOUL_FIRE.defaultBlockState(), DISPLAY_CONTEXT);
            out.add(RenderData.block(bone, fire));
        }
        return out;
    }

    @Override
    public void addRenderData(T animatable, @Nullable O relatedObject, R renderState, float partialTick) {
        renderState.addGeckolibData(CONTENTS, getRelevantBones(animatable, relatedObject, renderState, partialTick));
    }

    @Override
    protected void submitBlockRender(PoseStack poseStack, GeoBone bone, BlockModelRenderState blockState, R renderState,
                                     SubmitNodeCollector renderTasks, int packedLight) {
        poseStack.pushPose();
        poseStack.translate(-this.size / 2f, 0f, -this.size / 2f);
        poseStack.scale(this.size, this.size, this.size);
        blockState.submit(poseStack, renderTasks, LightCoordsUtil.FULL_BRIGHT, OverlayTexture.NO_OVERLAY,
                renderState instanceof EntityRenderState entityState ? entityState.outlineColor : 0);
        poseStack.popPose();
    }
}
