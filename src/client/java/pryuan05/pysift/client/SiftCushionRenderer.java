package pryuan05.pysift.client;

import net.minecraft.client.renderer.entity.CushionRenderer;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.state.CushionRenderState;
import net.minecraft.world.entity.decoration.Cushion;
import pryuan05.pysift.PySift;
import pryuan05.pysift.block.SiftCushion;

/** 原版坐墊的模型，貼圖換成篩靈界顏色（textures/entity/cushion/<顏色>_cushion.png）。 */
public class SiftCushionRenderer extends CushionRenderer {
    public SiftCushionRenderer(EntityRendererProvider.Context context) {
        super(context);
    }

    @Override
    public void extractRenderState(Cushion cushion, CushionRenderState state, float partialTick) {
        super.extractRenderState(cushion, state, partialTick);
        if (cushion instanceof SiftCushion sift) {
            state.texture = PySift.id("textures/entity/cushion/" + sift.getSiftColor().id + "_cushion.png");
        }
    }
}
