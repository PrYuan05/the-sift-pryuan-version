package pryuan05.pysift.mixin;

import net.minecraft.core.Holder;
import net.minecraft.network.chat.Component;
import net.minecraft.world.level.LevelAccessor;
import net.minecraft.world.level.saveddata.maps.MapBanner;
import net.minecraft.world.level.saveddata.maps.MapDecoration;
import net.minecraft.world.level.saveddata.maps.MapDecorationType;
import net.minecraft.world.level.saveddata.maps.MapItemSavedData;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.gen.Accessor;
import org.spongepowered.asm.mixin.gen.Invoker;

import java.util.Map;

@Mixin(MapItemSavedData.class)
public interface MapItemSavedDataAccessor {
    @Accessor("bannerMarkers")
    Map<String, MapBanner> pysift$bannerMarkers();

    @Accessor("decorations")
    Map<String, MapDecoration> pysift$decorations();

    @Invoker("addDecoration")
    void pysift$addDecoration(Holder<MapDecorationType> type, LevelAccessor level, String id, double x, double z, double rotation, Component name);
}
