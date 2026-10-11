package pryuan05.pysift;

import net.fabricmc.api.ModInitializer;
import net.minecraft.resources.Identifier;
import org.slf4j.Logger;

public class TheSiftPrYuanSVersion implements ModInitializer {
    public static final String MOD_ID = PySift.MOD_ID;
    public static final Logger LOGGER = PySift.LOGGER;

    @Override
    public void onInitialize() {
        // Forwarded to PySift
    }

    public static Identifier id(String path) {
        return PySift.id(path);
    }
}
