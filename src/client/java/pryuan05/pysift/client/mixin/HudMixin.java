package pryuan05.pysift.client.mixin;

import com.llamalad7.mixinextras.injector.ModifyExpressionValue;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.Hud;
import net.minecraft.resources.Identifier;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import pryuan05.pysift.PySift;
import pryuan05.pysift.effect.ModEffects;

/**
 * 靈魂剝奪期間的血量愛心換成靈魂火愛心（像中凋零時愛心變黑那樣）：
 * 把原版 hud/heart/&lt;種類_&gt;full / half / blinking / hardcore 的圖示換成 pysift:hud/heart/soul_&lt;同名&gt;
 * （tools/items/make_soul_hearts.py 產生）。中毒、凋零、冰凍的愛心也一起換；愛心框、吸收（黃心）與坐騎血量不變。
 * Hud.HeartType 不是公開型別，所以改寫它 getSprite 回傳的圖示名稱，而不碰型別本身。
 */
@Mixin(Hud.class)
public abstract class HudMixin {
    @ModifyExpressionValue(method = "extractHeart", at = @At(value = "INVOKE",
            target = "Lnet/minecraft/client/gui/Hud$HeartType;getSprite(ZZZ)Lnet/minecraft/resources/Identifier;"))
    private Identifier pysift$soulHearts(Identifier sprite) {
        var player = Minecraft.getInstance().player;
        if (player == null || !player.hasEffect(ModEffects.SOUL_DEPRIVATION) || !sprite.getNamespace().equals("minecraft")) {
            return sprite;
        }
        String path = sprite.getPath();
        if (!path.startsWith("hud/heart/")) {
            return sprite;
        }
        String name = path.substring("hud/heart/".length());
        if (name.startsWith("container") || name.startsWith("absorbing") || name.startsWith("vehicle")) {
            return sprite;
        }
        for (String type : new String[]{"poisoned_", "withered_", "frozen_"}) {
            if (name.startsWith(type)) {
                name = name.substring(type.length());
                break;
            }
        }
        return PySift.id("hud/heart/soul_" + name);
    }
}
