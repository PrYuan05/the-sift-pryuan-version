package pryuan05.pysift.client;

import net.fabricmc.fabric.api.client.rendering.v1.EntityRendererRegistry;
import net.fabricmc.fabric.api.client.rendering.v1.ModelLayerRegistry;
import net.minecraft.client.model.geom.ModelLayerLocation;
import net.minecraft.client.model.object.boat.BoatModel;
import net.minecraft.client.renderer.entity.BoatRenderer;
import pryuan05.pysift.PySift;
import pryuan05.pysift.block.SoulWillowWood;

/**
 * 靈魂柳船的渲染。BoatRenderer 由模型層的 id 推出貼圖：pysift:boat/soul_willow → textures/entity/boat/soul_willow.png。
 * 告示牌在 26.3 是方塊模型 + 方塊實體文字，編輯畫面貼圖（textures/gui/signs、gui/hanging_signs）由 Fabric 依 WoodType 處理，
 * 這裡不用另外註冊。
 */
public final class SoulWillowWoodClient {
    public static final ModelLayerLocation BOAT_LAYER = new ModelLayerLocation(PySift.id("boat/soul_willow"), "main");
    public static final ModelLayerLocation CHEST_BOAT_LAYER = new ModelLayerLocation(PySift.id("chest_boat/soul_willow"), "main");

    private SoulWillowWoodClient() {
    }

    public static void register() {
        ModelLayerRegistry.registerModelLayer(BOAT_LAYER, BoatModel::createBoatModel);
        ModelLayerRegistry.registerModelLayer(CHEST_BOAT_LAYER, BoatModel::createChestBoatModel);
        EntityRendererRegistry.register(SoulWillowWood.SOUL_WILLOW_BOAT_TYPE, context -> new BoatRenderer(context, BOAT_LAYER));
        EntityRendererRegistry.register(SoulWillowWood.SOUL_WILLOW_CHEST_BOAT_TYPE, context -> new BoatRenderer(context, CHEST_BOAT_LAYER));
    }
}
