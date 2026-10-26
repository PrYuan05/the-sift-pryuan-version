package pryuan05.pysift.mixin;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.LevelAccessor;
import net.minecraft.world.level.saveddata.maps.MapBanner;
import net.minecraft.world.level.saveddata.maps.MapDecoration;
import net.minecraft.world.level.saveddata.maps.MapDecorationType;
import net.minecraft.world.level.saveddata.maps.MapItemSavedData;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.Redirect;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import pryuan05.pysift.block.SiftColors;

/**
 * 地圖上的篩靈色旗幟標記。原版的 MapBanner 只存 DyeColor（篩靈色旗幟是白色），所以標記的種類改看世界裡的方塊：
 * 標記旗幟時（toggleBanner）直接用自己的標記；讀檔後原版會先畫成白色，玩家拿著地圖經過、原版檢查旗幟（checkBanners）時換回來。
 */
@Mixin(MapItemSavedData.class)
public abstract class SiftMapBannerMixin {
    @Redirect(method = "toggleBanner", at = @At(value = "INVOKE",
            target = "Lnet/minecraft/world/level/saveddata/maps/MapBanner;getDecoration()Lnet/minecraft/core/Holder;"))
    private Holder<MapDecorationType> pysift$siftMarker(MapBanner banner, LevelAccessor level, BlockPos pos) {
        SiftColors.SiftColor color = SiftColors.bannerColor(level, banner.pos());
        return color != null ? SiftColors.MAP_BANNERS.get(color) : banner.getDecoration();
    }

    @Inject(method = "checkBanners", at = @At("TAIL"))
    private void pysift$restoreSiftMarkers(BlockGetter level, int x, int z, CallbackInfo ci) {
        if (!(level instanceof LevelAccessor accessor)) {
            return;
        }
        MapItemSavedDataAccessor self = (MapItemSavedDataAccessor) this;
        for (MapBanner banner : self.pysift$bannerMarkers().values()) {
            BlockPos pos = banner.pos();
            if (pos.getX() != x || pos.getZ() != z) {
                continue;
            }
            SiftColors.SiftColor color = SiftColors.bannerColor(level, pos);
            MapDecoration current = self.pysift$decorations().get(banner.getId());
            if (color != null && (current == null || !current.type().equals(SiftColors.MAP_BANNERS.get(color)))) {
                self.pysift$addDecoration(SiftColors.MAP_BANNERS.get(color), accessor, banner.getId(),
                        pos.getX() + 0.5, pos.getZ() + 0.5, 180.0, banner.name().orElse(null));
            }
        }
    }
}
