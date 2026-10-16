package pryuan05.pysift.client;

import com.geckolib.cache.model.GeoBone;
import com.geckolib.renderer.base.BoneSnapshots;
import com.geckolib.renderer.base.GeoRenderState;
import com.geckolib.renderer.base.GeoRenderer;
import com.geckolib.renderer.base.RenderPassInfo;
import com.geckolib.renderer.layer.builtin.BlockAndItemGeoLayer;
import com.mojang.blaze3d.vertex.PoseStack;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.block.BlockModelRenderState;
import net.minecraft.client.renderer.block.model.BlockDisplayContext;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.state.EntityRenderState;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.DoublePlantBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.DoubleBlockHalf;
import pryuan05.pysift.entity.mob.SlabberEntity;

import java.util.ArrayList;
import java.util.List;

/**
 * 泥板獸：背上種的花用那種花本身的方塊模型畫在 flower_1~5 骨骼上（所以每種花長得不一樣），
 * 生長階段 0/1/2/3 依序顯示 1/2/3/5 朵。舊模型的 mushrooms 骨骼一律隱藏（背是光禿的土）。
 */
public class SlabberRenderer extends PysiftUniversalGeoRenderer<SlabberEntity> {
    private static final int[] FLOWERS_PER_STAGE = {1, 2, 3, 5};
    /** 背上一朵花的大小（方塊單位）。 */
    private static final float FLOWER_SCALE = 0.7f;

    public SlabberRenderer(EntityRendererProvider.Context context) {
        super(context, "slabber");
        withRenderLayer(new FlowerLayer(context, this));
    }

    @Override
    public void adjustModelBonesForRender(RenderPassInfo<EntityRenderState> renderPass, BoneSnapshots snapshots) {
        super.adjustModelBonesForRender(renderPass, snapshots);
        snapshots.ifPresent("mushrooms", bone -> bone.setScale(0, 0, 0));
    }

    private static class FlowerLayer extends BlockAndItemGeoLayer<SlabberEntity, Void, EntityRenderState> {
        FlowerLayer(EntityRendererProvider.Context context, GeoRenderer<SlabberEntity, Void, EntityRenderState> renderer) {
            super(context, renderer);
        }

        @Override
        protected List<RenderData> getRelevantBones(SlabberEntity slabber, Void relatedObject, EntityRenderState state, float partialTick) {
            ItemStack flower = slabber.getFlower();
            if (flower.isEmpty() || !(flower.getItem() instanceof BlockItem blockItem)) {
                return List.of();
            }
            BlockState block = blockItem.getBlock().defaultBlockState();
            if (block.hasProperty(DoublePlantBlock.HALF)) {          // 高花：畫上半部（花朵那一截）
                block = block.setValue(DoublePlantBlock.HALF, DoubleBlockHalf.UPPER);
            }
            int count = FLOWERS_PER_STAGE[Math.min(slabber.getGrowth(), SlabberEntity.MAX_GROWTH)];
            List<RenderData> out = new ArrayList<>();
            for (int i = 1; i <= count; i++) {
                BlockModelRenderState model = new BlockModelRenderState();
                this.blockModelResolver.update(model, block, BlockDisplayContext.create());
                out.add(RenderData.block("flower_" + i, model));
            }
            return out;
        }

        @Override
        public void addRenderData(SlabberEntity slabber, Void relatedObject, EntityRenderState state, float partialTick) {
            List<RenderData> flowers = getRelevantBones(slabber, relatedObject, state, partialTick);
            if (!flowers.isEmpty()) {
                ((GeoRenderState) state).addGeckolibData(CONTENTS, flowers);
            }
        }

        /** 花的根部對齊骨骼位置（GeckoLib 預設是把半格大小的方塊置中）。 */
        @Override
        protected void submitBlockRender(PoseStack poseStack, GeoBone bone, BlockModelRenderState model, EntityRenderState state,
                                         SubmitNodeCollector collector, int packedLight) {
            poseStack.pushPose();
            poseStack.translate(-FLOWER_SCALE / 2, 0, -FLOWER_SCALE / 2);
            poseStack.scale(FLOWER_SCALE, FLOWER_SCALE, FLOWER_SCALE);
            model.submit(poseStack, collector, packedLight, OverlayTexture.NO_OVERLAY, state.outlineColor);
            poseStack.popPose();
        }
    }
}
