package pryuan05.pysift.block;

import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.component.DataComponentType;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.saveddata.maps.MapDecorationType;
import net.minecraft.core.component.DataComponents;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobCategory;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.item.BannerItem;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.DyeColor;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.LevelReader;
import net.minecraft.world.level.block.BannerBlock;
import net.minecraft.world.level.block.BedBlock;
import net.minecraft.world.level.block.ShulkerBoxBlock;
import net.minecraft.world.item.component.ItemContainerContents;
import net.minecraft.world.level.block.WallBannerBlock;
import net.minecraft.world.level.block.entity.BannerBlockEntity;
import net.minecraft.world.level.block.entity.BannerPatternLayers;
import net.minecraft.world.level.block.entity.BlockEntityTypes;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.CandleBlock;
import net.minecraft.world.level.block.CandleCakeBlock;
import net.minecraft.world.level.block.CarpetBlock;
import net.minecraft.world.level.block.ConcretePowderBlock;
import net.minecraft.world.level.block.GlazedTerracottaBlock;
import net.minecraft.world.level.block.IronBarsBlock;
import net.minecraft.world.level.block.SlabBlock;
import net.minecraft.world.level.block.StairBlock;
import net.minecraft.world.level.block.TransparentBlock;
import net.minecraft.world.level.block.state.BlockBehaviour;
import pryuan05.pysift.PySift;
import pryuan05.pysift.item.ModItems;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Function;

/**
 * 篩靈界的 9 種新顏色（原版 16 色寫死在 DyeColor，不能擴充，所以每個顏色有自己的一整套方塊）：
 * 染料（由同色的篩靈界植物合成，也能染皮甲：{@link SiftDyeRecipe}）＋羊毛（含半磚、階梯）、地毯、混凝土（含半磚、階梯）、
 * 混凝土粉末、陶土、彩繪陶瓦、染色玻璃、玻璃片、蠟燭、床、旗幟與坐墊。
 * 床與坐墊用畫好的貼圖（tools/progression/paint_sift_colors.py）；旗幟和原版一樣是白色底圖著色，
 * 由客戶端的 SiftBannerTint 換成這裡的顏色（原版旗幟的 DyeColor 只有 16 色）。坐墊是實體（{@link SiftCushion}）。
 * 所有方塊和物品都沿用原版白色版本的貼圖，再由客戶端依 {@link SiftColor#rgb} 著色（模型的面有 tintindex 0），
 * 不複製任何原版貼圖。資源（模型、blockstate、配方、掉落物、標籤、語系）由 tools/progression/build_sift_colors.py 產生。
 */
public final class SiftColors {
    public enum SiftColor {
        TEAL("teal", 0x2EB8A6),
        MINT("mint", 0x8FE3C0),
        CORAL("coral", 0xF08A6C),
        AMBER("amber", 0xE8A33A),
        LAVENDER("lavender", 0xB39DDB),
        ROSE("rose", 0xD9536E),
        SOUL_BLUE("soul_blue", 0x8EC5F0),
        VOID("void", 0x3A2E48),
        DUSK_GOLD("dusk_gold", 0xF2CF6B);

        public final String id;
        /** 0xRRGGBB。 */
        public final int rgb;

        SiftColor(String id, int rgb) {
            this.id = id;
            this.rgb = rgb;
        }

        public static java.util.Optional<SiftColor> byId(String id) {
            return java.util.Arrays.stream(values()).filter(c -> c.id.equals(id)).findFirst();
        }

        public static final com.mojang.serialization.Codec<SiftColor> CODEC = com.mojang.serialization.Codec.STRING.comapFlatMap(
                id -> byId(id).map(com.mojang.serialization.DataResult::success)
                        .orElseGet(() -> com.mojang.serialization.DataResult.error(() -> "Unknown Sift colour: " + id)),
                c -> c.id);
        public static final net.minecraft.network.codec.StreamCodec<io.netty.buffer.ByteBuf, SiftColor> STREAM_CODEC =
                net.minecraft.network.codec.ByteBufCodecs.VAR_INT.map(i -> values()[Math.floorMod(i, values().length)], SiftColor::ordinal);
    }

    /**
     * 篩靈色系統：原版到處用 DyeColor（16 色）記「底色」，這個模組的顏色另外記在這裡，和原版並存。
     * - 旗幟方塊：方塊本身就是顏色（{@link #BANNER_COLORS}），方塊實體與原版共用，DyeColor 是白色。
     * - 盾牌：套上篩靈色旗幟時另外記 {@code pysift:base_color}（原版的 base_color 仍是白色，沒有本模組時也能正常讀取）。
     * - 地圖：篩靈色旗幟的標記用自己的標記種類（{@link #MAP_BANNERS}，SiftMapBannerMixin）。
     * 繪製時 SiftBannerTint（客戶端）把旗幟／盾牌的底層換成這個顏色。
     */
    public static final DataComponentType<SiftColor> BASE_COLOR = Registry.register(BuiltInRegistries.DATA_COMPONENT_TYPE,
            PySift.id("base_color"), DataComponentType.<SiftColor>builder().persistent(SiftColor.CODEC)
                    .networkSynchronized(SiftColor.STREAM_CODEC).build());
    /** 每個顏色的地圖旗幟標記（貼圖 textures/map/decorations/<顏色>_banner.png）。 */
    public static final Map<SiftColor, Holder<MapDecorationType>> MAP_BANNERS = new LinkedHashMap<>();

    /** 每個顏色的染料。 */
    public static final Map<SiftColor, SiftDyeItem> DYES = new LinkedHashMap<>();
    /** 方塊 → 著色用的 0xRRGGBB（客戶端讀這張表）。 */
    public static final Map<Block, Integer> TINTS = new LinkedHashMap<>();
    /** 每個顏色的坐墊物品。 */
    public static final Map<SiftColor, Item> CUSHIONS = new LinkedHashMap<>();
    /** 旗幟方塊（站立與牆上）→ 顏色，客戶端著色用。 */
    public static final Map<Block, SiftColor> BANNER_COLORS = new LinkedHashMap<>();
    /** 界伏殼方塊 → 顏色（方塊實體與原版共用，DyeColor 是白色；客戶端 ShulkerBoxRendererMixin 換貼圖）。 */
    public static final Map<Block, SiftColor> SHULKER_COLORS = new LinkedHashMap<>();
    /** 篩靈界顏色的坐墊實體（原版坐墊的大小與追蹤距離）。 */
    public static EntityType<SiftCushion> CUSHION_TYPE;
    /** 物品欄的排列順序。 */
    private static final List<Item> ORDER = new ArrayList<>();

    private SiftColors() {
    }

    public static void register() {
        for (SiftColor c : SiftColor.values()) {
            ResourceKey<Item> dyeKey = ResourceKey.create(Registries.ITEM, PySift.id(c.id + "_dye"));
            SiftDyeItem dye = Registry.register(BuiltInRegistries.ITEM, dyeKey, new SiftDyeItem(c, new Item.Properties().setId(dyeKey)));
            DYES.put(c, dye);
            ORDER.add(dye);
            Block wool = block(c, "wool", Block::new, Blocks.WOOL.white());
            block(c, "wool_slab", SlabBlock::new, Blocks.WOOL_SLAB.white());
            block(c, "wool_stairs", p -> new StairBlock(wool.defaultBlockState(), p), Blocks.WOOL_STAIRS.white());
            block(c, "carpet", CarpetBlock::new, Blocks.CARPET.white());
            Block concrete = block(c, "concrete", Block::new, Blocks.CONCRETE.white());
            block(c, "concrete_slab", SlabBlock::new, Blocks.CONCRETE_SLAB.white());
            block(c, "concrete_stairs", p -> new StairBlock(concrete.defaultBlockState(), p), Blocks.CONCRETE_STAIRS.white());
            block(c, "concrete_powder", p -> new ConcretePowderBlock(concrete, p), Blocks.CONCRETE_POWDER.white());
            block(c, "terracotta", Block::new, Blocks.DYED_TERRACOTTA.white());
            block(c, "glazed_terracotta", GlazedTerracottaBlock::new, Blocks.GLAZED_TERRACOTTA.white());
            block(c, "stained_glass", SiftGlassBlock::new, Blocks.STAINED_GLASS.white());
            block(c, "stained_glass_pane", SiftGlassPaneBlock::new, Blocks.STAINED_GLASS_PANE.white());
            Block candle = block(c, "candle", CandleBlock::new, Blocks.DYED_CANDLE.white());
            blockOnly(c, "candle_cake", p -> new SiftCandleCakeBlock(candle, p), Blocks.DYED_CANDLE_CAKE.white());
            Block bed = blockOnly(c, "bed", p -> new BedBlock(DyeColor.WHITE, p), Blocks.BED.white());
            item(c, "bed", props -> new BlockItem(bed, props.stacksTo(1)));
            Block banner = blockOnly(c, "banner", p -> new SiftBannerBlock(c, p), Blocks.BANNER.white());
            Block wallBanner = blockOnly(c, "wall_banner", p -> new SiftWallBannerBlock(c, p.overrideLootTable(banner.getLootTable())
                    .overrideDescription(banner.getDescriptionId())), Blocks.WALL_BANNER.white());
            BlockEntityTypes.BANNER.addValidBlock(banner);
            BlockEntityTypes.BANNER.addValidBlock(wallBanner);
            BANNER_COLORS.put(banner, c);
            BANNER_COLORS.put(wallBanner, c);
            item(c, "banner", props -> new BannerItem(banner, wallBanner,
                    props.stacksTo(16).component(DataComponents.BANNER_PATTERNS, BannerPatternLayers.EMPTY)));
            Block shulker = blockOnly(c, "shulker_box", p -> new ShulkerBoxBlock(DyeColor.WHITE, p), Blocks.DYED_SHULKER_BOX.white());
            BlockEntityTypes.SHULKER_BOX.addValidBlock(shulker);
            SHULKER_COLORS.put(shulker, c);
            item(c, "shulker_box", props -> new BlockItem(shulker,
                    props.stacksTo(1).component(DataComponents.CONTAINER, ItemContainerContents.EMPTY)));
            CUSHIONS.put(c, item(c, "cushion", props -> new SiftCushion.SiftCushionItem(c, props)));
            MAP_BANNERS.put(c, Registry.registerForHolder(BuiltInRegistries.MAP_DECORATION_TYPE, PySift.id(c.id + "_banner"),
                    new MapDecorationType(PySift.id(c.id + "_banner"), true, true)));
        }
        ResourceKey<EntityType<?>> cushionKey = ResourceKey.create(Registries.ENTITY_TYPE, PySift.id("sift_cushion"));
        CUSHION_TYPE = Registry.register(BuiltInRegistries.ENTITY_TYPE, cushionKey,
                EntityType.Builder.<SiftCushion>of(SiftCushion::new, MobCategory.MISC)
                        .sized(EntityTypes.CUSHION.getWidth(), EntityTypes.CUSHION.getHeight())
                        .eyeHeight(EntityTypes.CUSHION.getDimensions().eyeHeight())
                        .clientTrackingRange(EntityTypes.CUSHION.clientTrackingRange())
                        .updateInterval(EntityTypes.CUSHION.updateInterval())
                        .build(cushionKey));
        Registry.register(BuiltInRegistries.RECIPE_SERIALIZER, PySift.id("crafting_sift_dye"), SiftDyeRecipe.SERIALIZER);
        pryuan05.pysift.item.SiftCreativeTabs.source(ModItems.BLOCKS_TAB_KEY, output -> ORDER.forEach(output::accept));
    }

    /** A block without an item of its own (candle cakes: you get one by putting the candle on a cake). */
    private static Block blockOnly(SiftColor c, String kind, Function<BlockBehaviour.Properties, Block> factory, Block like) {
        ResourceKey<Block> blockKey = ResourceKey.create(Registries.BLOCK, PySift.id(c.id + "_" + kind));
        Block block = Registry.register(BuiltInRegistries.BLOCK, blockKey,
                factory.apply(BlockBehaviour.Properties.ofFullCopy(like).setId(blockKey)));
        TINTS.put(block, c.rgb);
        return block;
    }

    private static Item item(SiftColor c, String kind, Function<Item.Properties, Item> factory) {
        ResourceKey<Item> itemKey = ResourceKey.create(Registries.ITEM, PySift.id(c.id + "_" + kind));
        Item item = Registry.register(BuiltInRegistries.ITEM, itemKey, factory.apply(new Item.Properties().setId(itemKey)));
        ORDER.add(item);
        return item;
    }

    private static Block block(SiftColor c, String kind, Function<BlockBehaviour.Properties, Block> factory, Block like) {
        String name = c.id + "_" + kind;
        ResourceKey<Block> blockKey = ResourceKey.create(Registries.BLOCK, PySift.id(name));
        Block block = Registry.register(BuiltInRegistries.BLOCK, blockKey,
                factory.apply(BlockBehaviour.Properties.ofFullCopy(like).setId(blockKey)));
        ResourceKey<Item> itemKey = ResourceKey.create(Registries.ITEM, PySift.id(name));
        Item item = Registry.register(BuiltInRegistries.ITEM, itemKey,
                new BlockItem(block, new Item.Properties().setId(itemKey)));
        TINTS.put(block, c.rgb);
        ORDER.add(item);
        return block;
    }

    /** 新顏色的染料：記住自己的顏色，給染皮甲的配方用。 */
    public static final class SiftDyeItem extends Item {
        public final SiftColor color;

        public SiftDyeItem(SiftColor color, Properties properties) {
            super(properties);
            this.color = color;
        }
    }

    /** 染色玻璃（原版 StainedGlassBlock 需要 DyeColor，這裡用沒有顏色的透明方塊，顏色由著色決定）。 */
    public static final class SiftGlassBlock extends TransparentBlock {
        public SiftGlassBlock(Properties properties) {
            super(properties);
        }
    }

    /** 蠟燭蛋糕：建構時會登記到 CandleCakeBlock 的「蠟燭 → 蛋糕」表，所以把新蠟燭插到蛋糕上就會變成這個。 */
    public static final class SiftCandleCakeBlock extends CandleCakeBlock {
        public SiftCandleCakeBlock(Block candle, Properties properties) {
            super(candle, properties);
        }
    }

    /** 旗幟：原版的白色旗幟（底色在客戶端換成 {@link #color}），中鍵選取拿到自己的旗幟物品。 */
    public static final class SiftBannerBlock extends BannerBlock {
        public final SiftColor color;

        public SiftBannerBlock(SiftColor color, Properties properties) {
            super(DyeColor.WHITE, properties);
            this.color = color;
        }

        @Override
        protected ItemStack getCloneItemStack(LevelReader level, BlockPos pos, BlockState state, boolean includeData) {
            return bannerStack(this, level, pos);
        }
    }

    public static final class SiftWallBannerBlock extends WallBannerBlock {
        public final SiftColor color;

        public SiftWallBannerBlock(SiftColor color, Properties properties) {
            super(DyeColor.WHITE, properties);
            this.color = color;
        }

        @Override
        protected ItemStack getCloneItemStack(LevelReader level, BlockPos pos, BlockState state, boolean includeData) {
            return bannerStack(this, level, pos);
        }
    }

    /** The Sift colour of a banner item, or null for vanilla banners. */
    public static SiftColor bannerColor(ItemStack stack) {
        return stack.getItem() instanceof BannerItem banner ? BANNER_COLORS.get(banner.getBlock()) : null;
    }

    /** The Sift colour of the banner block at pos, or null. */
    public static SiftColor bannerColor(BlockGetter level, BlockPos pos) {
        return BANNER_COLORS.get(level.getBlockState(pos).getBlock());
    }

    /** Vanilla's BannerBlockEntity.getItem() would give the vanilla white banner: our item with the block entity's patterns. */
    private static ItemStack bannerStack(Block block, LevelReader level, BlockPos pos) {
        ItemStack stack = new ItemStack(block.asItem());
        if (level.getBlockEntity(pos) instanceof BannerBlockEntity banner) {
            stack.applyComponents(banner.collectComponents());
        }
        return stack;
    }

    /** 玻璃片（同上，原版 StainedGlassPaneBlock 需要 DyeColor）。 */
    public static final class SiftGlassPaneBlock extends IronBarsBlock {
        public SiftGlassPaneBlock(Properties properties) {
            super(properties);
        }
    }
}
