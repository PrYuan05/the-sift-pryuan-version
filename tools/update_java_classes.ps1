$vegFile = "src/main/java/pryuan05/pysift/block/ModVegetation.java"
$content = [System.IO.File]::ReadAllText($vegFile, [System.Text.Encoding]::UTF8)

# 1. Update soul_willow_sapling registration to remove tint
$oldSapling = 'public static final Block SOUL_WILLOW_SAPLING = tint(register("soul_willow_sapling",
            p -> new SaplingBlock(SOUL_WILLOW_GROWER, p), Blocks.OAK_SAPLING, false), 0xFF7FD6C8);'

$newSapling = 'public static final Block SOUL_WILLOW_SAPLING = register("soul_willow_sapling",
            p -> new SaplingBlock(SOUL_WILLOW_GROWER, p), Blocks.OAK_SAPLING, false);'

$content = $content.Replace($oldSapling, $newSapling)
# Also handle CRLF if needed
$oldSaplingCRLF = "public static final Block SOUL_WILLOW_SAPLING = tint(register(`"soul_willow_sapling`",`r`n            p -> new SaplingBlock(SOUL_WILLOW_GROWER, p), Blocks.OAK_SAPLING, false), 0xFF7FD6C8);"
$newSaplingCRLF = "public static final Block SOUL_WILLOW_SAPLING = register(`"soul_willow_sapling`",`r`n            p -> new SaplingBlock(SOUL_WILLOW_GROWER, p), Blocks.OAK_SAPLING, false);"
$content = $content.Replace($oldSaplingCRLF, $newSaplingCRLF)

# 2. Add new vegetation blocks before private ModVegetation()
$target = "    private ModVegetation() {"
$newBlocks = @"
    // ===== 篩靈新增植被 (Sift Vegetation Expansion) =====
    public static final Block CARAPACE_FLOWER = register("carapace_flower",
            p -> new FlowerBlock(MobEffects.RESISTANCE, 5.0F, p), Blocks.DANDELION, false);
    public static final Block CARAPACE_SHORT_GRASS = register("carapace_short_grass", SiftGrassBlock::new, Blocks.SHORT_GRASS, false);
    public static final Block SCULK_GRASS = register("sculk_grass", SiftGrassBlock::new, Blocks.SHORT_GRASS, false);
    public static final Block SIFT_SHORT_GRASS = register("sift_short_grass", SiftGrassBlock::new, Blocks.SHORT_GRASS, false);
    public static final Block SIFT_TALLGRASS = register("sift_tallgrass", DoublePlantBlock::new, Blocks.TALL_GRASS, true);
    public static final Block SIFT_ORANGE_SHORT_GRASS = register("sift_orange_short_grass", SiftGrassBlock::new, Blocks.SHORT_GRASS, false);
    public static final Block SIFT_ORANGE_TALL_GRASS = register("sift_orange_tall_grass", DoublePlantBlock::new, Blocks.TALL_GRASS, true);
    public static final Block SIFT_RED_SHORT_GRASS = register("sift_red_short_grass", SiftGrassBlock::new, Blocks.SHORT_GRASS, false);
    public static final Block SIFT_SMALL_FLOWERS = register("sift_small_flowers",
            p -> new FlowerBlock(MobEffects.SPEED, 5.0F, p), Blocks.DANDELION, false);
    public static final Block SIFT_SMALL_FLOWERS_YELLOW = register("sift_small_flowers_yellow",
            p -> new FlowerBlock(MobEffects.GLOWING, 5.0F, p), Blocks.DANDELION, false);
    public static final Block SOUL_BUBBLE_FLOWER = register("soul_bubble_flower",
            p -> new FlowerBlock(MobEffects.WATER_BREATHING, 5.0F, p.lightLevel(state -> 6)), Blocks.DANDELION, false);

    // 立體藤蔓與攀緣植被
    public static final Block CARAPACE_VINE = register("carapace_vine", p -> new BushBlock(p.noOcclusion()), Blocks.VINE, false);
    public static final Block GREEN_TREE_VINE = register("green_tree_vine", p -> new BushBlock(p.noOcclusion()), Blocks.VINE, false);
    public static final Block ORANGE_TREE_VINE = register("orange_tree_vine", p -> new BushBlock(p.noOcclusion()), Blocks.VINE, false);
    public static final Block SOUL_VINE = register("soul_vine", p -> new BushBlock(p.noOcclusion()), Blocks.VINE, false);
    public static final Block SIFT_WALL_LEAF = register("sift_wall_leaf", p -> new BushBlock(p.noOcclusion()), Blocks.VINE, false);

    // 奇異植物與作物
    public static final Block SIFT_CLEAVER_PLANT = register("sift_cleaver_plant", BushBlock::new, Blocks.BUSH, false);
    public static final Block SIFT_SOUL_CLEAVER_PLANT = register("sift_soul_cleaver_plant", p -> new BushBlock(p.lightLevel(state -> 8)), Blocks.BUSH, false);
    public static final Block WEAT_SMALL_PLANT = register("weat_small_plant", SiftGrassBlock::new, Blocks.SHORT_GRASS, false);
    public static final Block WEAT_PLANT = register("weat_plant", SiftGrassBlock::new, Blocks.SHORT_GRASS, false);
    public static final Block WEAT = register("weat", BushBlock::new, Blocks.BUSH, false);
    public static final Block YELLOW_LEAF = register("yellow_leaf", BushBlock::new, Blocks.BUSH, false);

    private ModVegetation() {
"@

if ($content.Contains($target)) {
    $content = $content.Replace($target, $newBlocks)
    [System.IO.File]::WriteAllText($vegFile, $content, [System.Text.Encoding]::UTF8)
    Write-Host "Updated ModVegetation.java successfully!"
} else {
    Write-Warning "Target not found in ModVegetation.java"
}

# 3. Update ModItems.java
$itemFile = "src/main/java/pryuan05/pysift/item/ModItems.java"
$itemContent = [System.IO.File]::ReadAllText($itemFile, [System.Text.Encoding]::UTF8)

$oldReg = 'public static final Item CHAROITE = registerItem("charoite", Item::new);'
$newReg = 'public static final Item CHAROITE = registerItem("charoite", Item::new);
    public static final Item SUNFLOWER_SEEDS = registerItem("sunflower_seeds", Item::new);'

$oldTab = 'output.accept(CHAROITE);'
$newTab = 'output.accept(CHAROITE);
                output.accept(SUNFLOWER_SEEDS);'

$itemContent = $itemContent.Replace($oldReg, $newReg)
$itemContent = $itemContent.Replace($oldTab, $newTab)

[System.IO.File]::WriteAllText($itemFile, $itemContent, [System.Text.Encoding]::UTF8)
Write-Host "Updated ModItems.java successfully!"
