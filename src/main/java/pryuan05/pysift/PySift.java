package pryuan05.pysift;

import net.fabricmc.api.ModInitializer;
import net.minecraft.resources.Identifier;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import pryuan05.pysift.block.ModBlocks;
import pryuan05.pysift.entity.ModEntities;
import pryuan05.pysift.item.ModItems;

public class PySift implements ModInitializer {
    public static final String MOD_ID = "pysift";
    public static final Logger LOGGER = LoggerFactory.getLogger(MOD_ID);

    public static Identifier id(String path) {
        return Identifier.fromNamespaceAndPath(MOD_ID, path);
    }

    @Override
    public void onInitialize() {
        LOGGER.info("Initializing The Sift (pysift)...");
        ModBlocks.registerModBlocks();
        ModEntities.registerModEntities();
        ModItems.registerModItems();
        LOGGER.info("The Sift initialized successfully!");
    }
}
