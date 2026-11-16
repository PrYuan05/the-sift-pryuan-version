package pryuan05.pysift.client;

import net.minecraft.client.renderer.Sheets;
import net.minecraft.client.resources.model.sprite.SpriteId;
import pryuan05.pysift.PySift;
import pryuan05.pysift.block.SiftColors;

/**
 * 篩靈界顏色的界伏殼貼圖：方塊實體與原版共用（DyeColor 是白色），ShulkerBoxRendererMixin 依方塊換成
 * textures/entity/shulker/shulker_<顏色>.png（原版 shulker_boxes 圖集會收進所有命名空間的 entity/shulker/）。
 * 物品欄的界伏殼用原版特殊模型，貼圖寫在 items/<顏色>_shulker_box.json。
 */
public final class SiftShulkerSprites {
    private SiftShulkerSprites() {
    }

    public static SpriteId sprite(SiftColors.SiftColor color) {
        return Sheets.SHULKER_MAPPER.apply(PySift.id("shulker_" + color.id));
    }

    /** ShulkerBoxRenderState 多記的貼圖（null = 原版界伏殼）。 */
    public interface State {
        SpriteId pysift$siftSprite();

        void pysift$setSiftSprite(SpriteId sprite);
    }
}
