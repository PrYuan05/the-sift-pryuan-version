package pryuan05.pysift.client;

import com.geckolib.constant.DataTickets;
import com.geckolib.constant.dataticket.DataTicket;
import com.geckolib.renderer.base.GeoRenderState;
import com.geckolib.renderer.base.RenderPassInfo;
import com.geckolib.renderer.layer.builtin.TextureLayerGeoLayer;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.state.EntityRenderState;
import net.minecraft.resources.Identifier;
import net.minecraft.world.item.DyeColor;
import pryuan05.pysift.PySift;
import pryuan05.pysift.entity.ClimateVariant;
import pryuan05.pysift.entity.mob.NuzzleEntity;

/**
 * 蹭蹭怪：像原版的羊一樣剪毛與染色。
 * <ul>
 *   <li>沒剪、沒染：原本的貼圖（天生的紅毛，依氣候變體）。</li>
 *   <li>剪過：nuzzle&lt;氣候&gt;_sheared.png（毛的地方露出皮）。</li>
 *   <li>染過：底圖用 _sheared，再疊一層只有毛的灰階貼圖 nuzzle&lt;氣候&gt;_fur.png，用染料顏色上色（原版羊毛層的做法）。</li>
 * </ul>
 */
public class NuzzleRenderer extends PysiftUniversalGeoRenderer<NuzzleEntity> {
    static final DataTicket<Boolean> SHEARED = DataTicket.create("pysift_nuzzle_sheared", Boolean.class);
    /** 染料顏色（ARGB），沒染是 0。 */
    static final DataTicket<Integer> DYE = DataTicket.create("pysift_nuzzle_dye", Integer.class);

    public NuzzleRenderer(EntityRendererProvider.Context context) {
        super(context, new Model());
        withRenderLayer(new FurLayer(this));
    }

    @Override
    public void addRenderData(NuzzleEntity animatable, Void relatedObject, EntityRenderState renderState, float partialTick) {
        super.addRenderData(animatable, relatedObject, renderState, partialTick);
        DyeColor dye = animatable.getFurColor();
        ((GeoRenderState) renderState).addGeckolibData(SHEARED, animatable.isSheared());
        ((GeoRenderState) renderState).addGeckolibData(DYE, dye == null ? 0 : dye.getTextureDiffuseColor());
    }

    private static Identifier texture(int climate, String part) {
        return PySift.id("textures/entity/nuzzle" + ClimateVariant.suffix(climate) + part + ".png");
    }

    private static int climate(GeoRenderState state) {
        return state.getOrDefaultGeckolibData(CLIMATE, ClimateVariant.NORMAL);
    }

    static class Model extends PysiftUniversalGeoModel<NuzzleEntity> {
        Model() {
            super("nuzzle");
        }

        @Override
        public Identifier getTextureResource(GeoRenderState state) {
            boolean bare = state.getOrDefaultGeckolibData(SHEARED, false) || state.getOrDefaultGeckolibData(DYE, 0) != 0;
            return bare ? texture(climate(state), "_sheared") : super.getTextureResource(state);
        }
    }

    /** 染過色的毛：同一個模型再畫一次，只有毛的灰階貼圖，乘上染料顏色。 */
    static class FurLayer extends TextureLayerGeoLayer<NuzzleEntity, Void, EntityRenderState> {
        FurLayer(NuzzleRenderer renderer) {
            super(renderer, PySift.id("textures/entity/nuzzle_fur.png"));
        }

        @Override
        protected Identifier getTextureResource(EntityRenderState state) {
            return texture(climate((GeoRenderState) state), "_fur");
        }

        @Override
        public void submitRenderTask(RenderPassInfo<EntityRenderState> pass, SubmitNodeCollector collector) {
            GeoRenderState state = (GeoRenderState) pass.renderState();
            int dye = state.getOrDefaultGeckolibData(DYE, 0);
            if (dye == 0 || state.getOrDefaultGeckolibData(SHEARED, false)) {
                return;
            }
            Integer old = state.getGeckolibData(DataTickets.RENDER_COLOR);
            state.addGeckolibData(DataTickets.RENDER_COLOR, 0xFF000000 | dye);
            super.submitRenderTask(pass, collector);
            state.addGeckolibData(DataTickets.RENDER_COLOR, old == null ? -1 : old);
        }
    }
}
