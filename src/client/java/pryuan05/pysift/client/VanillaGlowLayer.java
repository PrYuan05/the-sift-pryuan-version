package pryuan05.pysift.client;

import com.geckolib.animatable.GeoAnimatable;
import com.geckolib.renderer.base.GeoRenderState;
import com.geckolib.renderer.base.GeoRenderer;
import com.geckolib.renderer.layer.builtin.AutoGlowingGeoLayer;
import net.minecraft.client.renderer.entity.state.EntityRenderState;
import net.minecraft.client.renderer.rendertype.RenderType;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import org.jspecify.annotations.Nullable;

/**
 * 發光層（讀 {@code <貼圖>_glowmask.png}），但改用原版的 {@link RenderTypes#eyes} 渲染類型。
 * GeckoLib 5.5.7 自己的 geckolib_emissive 沒有設定 26.3 的 OIT 管線，畫出來會直接當機。
 */
public class VanillaGlowLayer<T extends GeoAnimatable, O, R extends GeoRenderState> extends AutoGlowingGeoLayer<T, O, R> {
    public VanillaGlowLayer(GeoRenderer<T, O, R> renderer) {
        super(renderer);
    }

    @Override
    protected @Nullable RenderType getRenderType(R renderState) {
        if (renderState instanceof EntityRenderState entityRenderState && entityRenderState.isInvisible) {
            return null;
        }
        return RenderTypes.eyes(getTextureResource(renderState));
    }
}
