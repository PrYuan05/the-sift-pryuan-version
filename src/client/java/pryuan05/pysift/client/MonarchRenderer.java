package pryuan05.pysift.client;

import com.geckolib.constant.dataticket.DataTicket;
import com.geckolib.renderer.base.GeoRenderState;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.state.EntityRenderState;
import net.minecraft.client.renderer.rendertype.RenderType;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.resources.Identifier;
import net.minecraft.util.ARGB;
import pryuan05.pysift.entity.mob.MonarchEntity;

/** Monarch：分身（Monarch Echo）畫成半透明、帶淡紫色調的幽影；本體照常渲染。 */
public class MonarchRenderer extends PysiftUniversalGeoRenderer<MonarchEntity> {
    private static final DataTicket<Boolean> ECHO = DataTicket.create("pysift_monarch_echo", Boolean.class);
    /** 分身的顏色：約 55% 不透明的淡紫。 */
    private static final int ECHO_COLOR = ARGB.color(140, 200, 180, 255);

    public MonarchRenderer(EntityRendererProvider.Context context) {
        super(context, "monarch");
    }

    @Override
    public void addRenderData(MonarchEntity animatable, Void relatedObject, EntityRenderState renderState, float partialTick) {
        super.addRenderData(animatable, relatedObject, renderState, partialTick);
        ((GeoRenderState) renderState).addGeckolibData(ECHO, animatable.isEcho());
    }

    @Override
    public int getRenderColor(MonarchEntity animatable, Void relatedObject, float partialTick) {
        return animatable.isEcho() ? ECHO_COLOR : super.getRenderColor(animatable, relatedObject, partialTick);
    }

    @Override
    public RenderType getRenderType(EntityRenderState renderState, Identifier texture) {
        if (((GeoRenderState) renderState).getOrDefaultGeckolibData(ECHO, false) && !renderState.isInvisible) {
            return RenderTypes.entityTranslucent(texture);
        }
        return super.getRenderType(renderState, texture);
    }
}
