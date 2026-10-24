Add-Type -AssemblyName System.IO.Compression.FileSystem

$zipPath = "sift_vegetation_assets.zip"
$targetRes = "src/main/resources/assets/pysift"

$blockTextures = @(
    "carapace_flower.png", "carapace_shortgrass.png", "sculk_grass.png",
    "sift_short_grass.png", "sift_tallgrass_top.png", "sift_tallgrass_down.png",
    "sift_orange_short_grass.png", "sift_orange_tall_grass_top.png", "sift_orange_tall_grass_down.png",
    "sift_red_tallgrass.png", "sift_small_flowers.png", "sift_small_flowers_yellow.png",
    "soul_bubble_flower.png", "carapace_vine.png", "green_sift_vine.png",
    "orange_sift_vine.png", "souls_vine.png", "sift_wall_leaf.png",
    "cleaver_plant.png", "soul_sift_cleaver_plant.png", "weat.png",
    "weat_plant.png", "weat_plant2.png", "yellow_leaf.png", "souls_sapling.png"
)

$itemTextures = @(
    "carapace_vine.png", "cleaver_plant.png", "green_sift_vine.png",
    "orange_sift_vine.png", "soul_bubble_flower.png", "soul_sift_cleaver_plant.png",
    "souls_vine.png", "sunflower_seeds.png", "yellow_leaf.png"
)

$customModels = @(
    "carapace_vine.json", "cleaver_plant.json", "green_tree_vine.json",
    "orange_tree_vine.json", "sift_cleaver_plant.json", "sift_soul_cleaver_plant.json",
    "sift_wall_leaf.json", "soul_bubble_flower.json", "soul_bubble_pop_flower.json",
    "soul_bubble_popflower.json", "soul_cleaver_plant.json", "soul_vine.json",
    "weat.json", "yellow_leaf.json"
)

$blockModels = @(
    "carapace_flower.json", "carapace_short_grass.json", "sculk_grass.json",
    "sift_short_grass.json", "sift_tallgrass.json", "sift_tallgrass_bottom.json",
    "sift_orange_short_grass.json", "sift_orange_tall_grass.json", "sift_orange_tall_grass_bottom.json",
    "sift_red_short_grass.json", "sift_small_flowers.json", "sift_small_flowers_yellow.json",
    "soul_bubble_flower.json", "carapace_vine.json", "green_tree_vine.json",
    "orange_tree_vine.json", "soul_vine.json", "sift_wall_leaf.json",
    "sift_cleaver_plant.json", "sift_soul_cleaver_plant.json", "weat.json",
    "weat_plant.json", "weat_small_plant.json", "yellow_leaf.json"
)

$itemModels = @(
    "carapace_flower.json", "carapace_short_grass.json", "sculk_grass.json",
    "sift_short_grass.json", "sift_tallgrass.json", "sift_orange_short_grass.json",
    "sift_orange_tall_grass.json", "sift_red_short_grass.json", "sift_small_flowers.json",
    "sift_small_flowers_yellow.json", "soul_bubble_flower.json", "carapace_vine.json",
    "green_tree_vine.json", "orange_tree_vine.json", "soul_vine.json",
    "sift_wall_leaf.json", "sift_cleaver_plant.json", "sift_soul_cleaver_plant.json",
    "weat.json", "weat_plant.json", "weat_small_plant.json", "yellow_leaf.json",
    "sunflower_seeds.json"
)

$zip = [System.IO.Compression.ZipFile]::OpenRead($zipPath)

# 1. Extract block textures
New-Item -ItemType Directory -Force -Path "$targetRes/textures/block" | Out-Null
foreach ($bt in $blockTextures) {
    $entry = $zip.Entries | Where-Object { $_.FullName -eq "textures/block/$bt" }
    if ($entry) {
        $outPath = "$targetRes/textures/block/$bt"
        [System.IO.Compression.ZipFileExtensions]::ExtractToFile($entry, $outPath, $true)
        Write-Host "Extracted texture/block: $bt"
    }
}
# Also update soul_willow_sapling.png
$saplingEntry = $zip.Entries | Where-Object { $_.FullName -eq "textures/block/souls_sapling.png" }
if ($saplingEntry) {
    $saplingDest = "$targetRes/textures/block/vegetation/soul_willow_sapling.png"
    [System.IO.Compression.ZipFileExtensions]::ExtractToFile($saplingEntry, $saplingDest, $true)
    Write-Host "Updated vegetation/soul_willow_sapling.png"
}

# 2. Extract item textures
New-Item -ItemType Directory -Force -Path "$targetRes/textures/item" | Out-Null
foreach ($it in $itemTextures) {
    $entry = $zip.Entries | Where-Object { $_.FullName -eq "textures/item/$it" }
    if ($entry) {
        $outPath = "$targetRes/textures/item/$it"
        [System.IO.Compression.ZipFileExtensions]::ExtractToFile($entry, $outPath, $true)
        Write-Host "Extracted texture/item: $it"
    }
}

# 3. Extract custom models and replace namespace
New-Item -ItemType Directory -Force -Path "$targetRes/models/custom" | Out-Null
foreach ($cm in $customModels) {
    $entry = $zip.Entries | Where-Object { $_.FullName -eq "models/custom/$cm" }
    if ($entry) {
        $stream = $entry.Open()
        $reader = New-Object System.IO.StreamReader($stream)
        $content = $reader.ReadToEnd()
        $reader.Close()
        $stream.Close()
        $content = $content.Replace("dungeons_content_two:", "pysift:")
        [System.IO.File]::WriteAllText("$targetRes/models/custom/$cm", $content, [System.Text.Encoding]::UTF8)
        Write-Host "Extracted model/custom: $cm"
    }
}

# 4. Extract block models and replace namespace
New-Item -ItemType Directory -Force -Path "$targetRes/models/block" | Out-Null
foreach ($bm in $blockModels) {
    $entry = $zip.Entries | Where-Object { $_.FullName -eq "models/block/$bm" }
    if ($entry) {
        $stream = $entry.Open()
        $reader = New-Object System.IO.StreamReader($stream)
        $content = $reader.ReadToEnd()
        $reader.Close()
        $stream.Close()
        $content = $content.Replace("dungeons_content_two:", "pysift:")
        [System.IO.File]::WriteAllText("$targetRes/models/block/$bm", $content, [System.Text.Encoding]::UTF8)
        Write-Host "Extracted model/block: $bm"
    }
}

# 5. Extract item models and replace namespace
New-Item -ItemType Directory -Force -Path "$targetRes/models/item" | Out-Null
foreach ($im in $itemModels) {
    $entry = $zip.Entries | Where-Object { $_.FullName -eq "models/item/$im" }
    if ($entry) {
        $stream = $entry.Open()
        $reader = New-Object System.IO.StreamReader($stream)
        $content = $reader.ReadToEnd()
        $reader.Close()
        $stream.Close()
        $content = $content.Replace("dungeons_content_two:", "pysift:")
        [System.IO.File]::WriteAllText("$targetRes/models/item/$im", $content, [System.Text.Encoding]::UTF8)
        Write-Host "Extracted model/item: $im"
    }
}

$zip.Dispose()
Write-Host "All assets successfully extracted and sanitized!"
