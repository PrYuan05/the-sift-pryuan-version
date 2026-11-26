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
import pryuan05.pysift.PySift;
import pryuan05.pysift.entity.ClimateVariant;
import pryuan05.pysift.entity.mob.NuzzleEntity;

/**
 * 蹭蹭怪：像原版的羊一樣剪毛與染色，完整支援原版 16 色＋本模組 9 種隙浮顏色，且適應普通／熱帶／寒帶氣候變體。
 * <ul>
 *   <li>沒剪、沒染：原本的貼圖（依氣候變體）。</li>
 *   <li>剪過：nuzzle&lt;氣候&gt;_sheared.png（毛與花朵／冬帽皆剪掉，露出皮）。</li>
 *   <li>染過（未剪）：底圖使用 _sheared（熱帶則使用 _dyed_base 以保留背上彩色熱帶花朵），再疊一層只有毛的灰階貼圖
 *       nuzzle&lt;氣候&gt;_fur.png，並依氣候微調染色色溫（寒帶微霜雪亮藍、熱帶微暖陽鮮豔）。</li>
 * </ul>
 */
public class NuzzleRenderer extends PysiftUniversalGeoRenderer<NuzzleEntity> {
    static final DataTicket<Boolean> SHEARED = DataTicket.create("pysift_nuzzle_sheared", Boolean.class);
    /** 染料顏色（0xRRGGBB），沒染是 0。 */
    static final DataTicket<Integer> DYE = DataTicket.create("pysift_nuzzle_dye", Integer.class);

    public NuzzleRenderer(EntityRendererProvider.Context context) {
        super(context, new Model());
        withRenderLayer(new FurLayer(this));
    }

    @Override
    public void addRenderData(NuzzleEntity animatable, Void relatedObject, EntityRenderState renderState, float partialTick) {
        super.addRenderData(animatable, relatedObject, renderState, partialTick);
        ((GeoRenderState) renderState).addGeckolibData(SHEARED, animatable.isSheared());
        ((GeoRenderState) renderState).addGeckolibData(DYE, animatable.getFurTintRgb());
    }

    private static Identifier texture(int climate, String part) {
        return PySift.id("textures/entity/nuzzle" + ClimateVariant.suffix(climate) + part + ".png");
    }

    private static int climate(GeoRenderState state) {
        return state.getOrDefaultGeckolibData(CLIMATE, ClimateVariant.NORMAL);
    }

    /** 依氣候變體微調染色色調：寒帶帶微霜雪感、熱帶帶暖陽鮮明感、普通維持原染料原色。 */
    private static int climateAdaptTint(int rgb, int climate) {
        int r = (rgb >> 16) & 0xFF;
        int g = (rgb >> 8) & 0xFF;
        int b = rgb & 0xFF;
        if (climate == ClimateVariant.COLD) {
            // 混入 16% 冰霜雪白 (0xDCEEFF)，讓所有染料在寒帶厚毛上呈現自然的雪地粉霜感
            r = Math.min(255, Math.round(r * 0.84f + 220 * 0.16f));
            g = Math.min(255, Math.round(g * 0.84f + 238 * 0.16f));
            b = Math.min(255, Math.round(b * 0.84f + 255 * 0.16f));
        } else if (climate == ClimateVariant.TROPICAL) {
            // 輕微暖陽提亮與飽滿，讓所有染料在熱帶日照下更鮮活
            r = Math.min(255, Math.round(r * 1.05f + 8));
            g = Math.min(255, Math.round(g * 1.02f + 4));
            b = Math.max(0, Math.round(b * 0.94f));
        }
        return (r << 16) | (g << 8) | b;
    }

    static class Model extends PysiftUniversalGeoModel<NuzzleEntity> {
        Model() {
            super("nuzzle");
        }

        @Override
        public Identifier getTextureResource(GeoRenderState state) {
            boolean sheared = state.getOrDefaultGeckolibData(SHEARED, false);
            int dye = state.getOrDefaultGeckolibData(DYE, 0);
            int c = climate(state);
            if (sheared) {
                return texture(c, "_sheared");
            }
            if (dye != 0) {
                // 熱帶染色時保留背上的彩色熱帶花朵，只對羊毛層著色
                return texture(c, c == ClimateVariant.TROPICAL ? "_dyed_base" : "_sheared");
            }
            return super.getTextureResource(state);
        }
    }

    /** 染過色的毛：同一個模型再畫一次，只有毛的灰階貼圖，乘上氣候適應後的染料顏色。 */
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
            int tinted = climateAdaptTint(dye, climate(state));
            Integer old = state.getGeckolibData(DataTickets.RENDER_COLOR);
            state.addGeckolibData(DataTickets.RENDER_COLOR, 0xFF000000 | tinted);
            super.submitRenderTask(pass, collector);
            state.addGeckolibData(DataTickets.RENDER_COLOR, old == null ? -1 : old);
        }
    }
}
