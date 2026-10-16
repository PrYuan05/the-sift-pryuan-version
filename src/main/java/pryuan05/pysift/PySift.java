package pryuan05.pysift;

import net.fabricmc.api.ModInitializer;
import net.minecraft.resources.Identifier;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import pryuan05.pysift.block.ModBlocks;
import pryuan05.pysift.block.SiftPortalRitual;
import pryuan05.pysift.effect.SoulBurn;
import pryuan05.pysift.block.entity.ModBlockEntities;
import pryuan05.pysift.block.ModVegetation;
import pryuan05.pysift.block.SoulCrystal;
import pryuan05.pysift.block.SoulWillowWood;
import pryuan05.pysift.particle.ModParticles;
import pryuan05.pysift.effect.ModEffects;
import pryuan05.pysift.entity.ModEntities;
import pryuan05.pysift.fluid.ModFluids;
import pryuan05.pysift.item.ModItems;
import pryuan05.pysift.worldgen.SoulWillowFoliagePlacer;
import pryuan05.pysift.worldgen.SoulWillowTrunkPlacer;
import pryuan05.pysift.worldgen.SoulWillowVineDecorator;
import pryuan05.pysift.worldgen.BossArenaFeature;
import pryuan05.pysift.worldgen.StrataSpireFeature;

public class PySift implements ModInitializer {
    public static final String MOD_ID = "pysift";
    public static final Logger LOGGER = LoggerFactory.getLogger(MOD_ID);

    public static Identifier id(String path) {
        return Identifier.fromNamespaceAndPath(MOD_ID, path);
    }

    @Override
    public void onInitialize() {
        LOGGER.info("Initializing The Sift (pysift)...");
        ModEffects.registerModEffects();
        SoulBurn.register();                 // 靈魂火灼燒：靈液懲罰、靈魂碎裂、解藥
        ModBlocks.registerModBlocks();
        ModBlockEntities.registerModBlockEntities();
        ModFluids.registerModFluids();
        ModVegetation.registerModVegetation();
        SoulWillowWood.register();
        SoulCrystal.register();
        ModParticles.register();
        SoulWillowTrunkPlacer.register();
        SoulWillowFoliagePlacer.register();
        SoulWillowVineDecorator.register();
        StrataSpireFeature.register();
        BossArenaFeature.register();
        ModEntities.registerModEntities();
        ModItems.registerModItems();
        SiftPortalRitual.register();
        LOGGER.info("The Sift initialized successfully!");
    }
}
