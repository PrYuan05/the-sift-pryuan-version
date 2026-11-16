package pryuan05.pysift.client;

import com.geckolib.constant.dataticket.DataTicket;
import com.geckolib.renderer.base.BoneSnapshots;
import com.geckolib.renderer.base.GeoRenderState;
import com.geckolib.renderer.base.RenderPassInfo;
import com.geckolib.renderer.layer.builtin.ItemInHandGeoLayer;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.state.EntityRenderState;
import net.minecraft.client.renderer.rendertype.RenderType;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.resources.Identifier;
import pryuan05.pysift.entity.mob.EchoGolemEntity;

/** 迴音傀儡：頭頂的靈魂晶塊被取下或送給歌者後，隱藏模型的 crystal 骨骼（支架 cage 保留）。 */
public class EchoGolemRenderer extends PysiftUniversalGeoRenderer<EchoGolemEntity> {
    private static final DataTicket<Boolean> HAS_CRYSTAL = DataTicket.create("pysift_echo_golem_has_crystal", Boolean.class);

    public EchoGolemRenderer(EntityRendererProvider.Context context) {
        super(context, "echo_golem");
        // 儀式工人抱著的唱片盒（手持物品畫在 right_hand 骨骼上）
        withRenderLayer(new ItemInHandGeoLayer<>(context, this, "right_hand", "left_hand"));
    }

    @Override
    public void addRenderData(EchoGolemEntity animatable, Void relatedObject, EntityRenderState renderState, float partialTick) {
        super.addRenderData(animatable, relatedObject, renderState, partialTick);
        ((GeoRenderState) renderState).addGeckolibData(HAS_CRYSTAL, animatable.hasCrystal());
    }

    /** 頭頂的靈魂晶塊是半透明的水晶（裡面有小靈魂）：整隻用半透明渲染，不透明的像素畫起來和原本一樣。 */
    @Override
    public RenderType getRenderType(EntityRenderState renderState, Identifier texture) {
        return renderState.isInvisible ? super.getRenderType(renderState, texture) : RenderTypes.entityTranslucent(texture);
    }

    @Override
    public void adjustModelBonesForRender(RenderPassInfo<EntityRenderState> renderPass, BoneSnapshots snapshots) {
        super.adjustModelBonesForRender(renderPass, snapshots);
        if (!((GeoRenderState) renderPass.renderState()).getOrDefaultGeckolibData(HAS_CRYSTAL, true)) {
            snapshots.ifPresent("crystal", bone -> bone.setScale(0, 0, 0));
        }
    }
}
