package pryuan05.pysift.client;

import com.geckolib.constant.dataticket.DataTicket;
import com.geckolib.renderer.base.BoneSnapshots;
import com.geckolib.renderer.base.GeoRenderState;
import com.geckolib.renderer.base.RenderPassInfo;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.state.EntityRenderState;
import pryuan05.pysift.entity.mob.EchoGolemEntity;

/** 迴音傀儡：頭頂的靈魂晶塊被取下或送給歌者後，隱藏模型的 crystal 骨骼（支架 cage 保留）。 */
public class EchoGolemRenderer extends PysiftUniversalGeoRenderer<EchoGolemEntity> {
    private static final DataTicket<Boolean> HAS_CRYSTAL = DataTicket.create("pysift_echo_golem_has_crystal", Boolean.class);

    public EchoGolemRenderer(EntityRendererProvider.Context context) {
        super(context, "echo_golem");
    }

    @Override
    public void addRenderData(EchoGolemEntity animatable, Void relatedObject, EntityRenderState renderState, float partialTick) {
        super.addRenderData(animatable, relatedObject, renderState, partialTick);
        ((GeoRenderState) renderState).addGeckolibData(HAS_CRYSTAL, animatable.hasCrystal());
    }

    @Override
    public void adjustModelBonesForRender(RenderPassInfo<EntityRenderState> renderPass, BoneSnapshots snapshots) {
        super.adjustModelBonesForRender(renderPass, snapshots);
        if (!((GeoRenderState) renderPass.renderState()).getOrDefaultGeckolibData(HAS_CRYSTAL, true)) {
            snapshots.ifPresent("crystal", bone -> bone.setScale(0, 0, 0));
        }
    }
}
