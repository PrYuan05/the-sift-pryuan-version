# Apply vegetation blockstates, lang, and tags

$blockstatesDir = "src/main/resources/assets/pysift/blockstates"

# 1. Single model blockstates
$simpleBlocks = @(
    "carapace_flower", "carapace_short_grass", "sculk_grass", "sift_short_grass",
    "sift_orange_short_grass", "sift_red_short_grass", "sift_small_flowers",
    "sift_small_flowers_yellow", "soul_bubble_flower", "carapace_vine",
    "green_tree_vine", "orange_tree_vine", "soul_vine", "sift_wall_leaf",
    "sift_cleaver_plant", "sift_soul_cleaver_plant", "weat", "weat_plant",
    "weat_small_plant", "yellow_leaf"
)

foreach ($b in $simpleBlocks) {
    $json = @"
{
  "variants": {
    "": {
      "model": "pysift:block/$b"
    }
  }
}
"@
    [System.IO.File]::WriteAllText("$blockstatesDir/$b.json", $json, [System.Text.Encoding]::UTF8)
    Write-Host "Created blockstate: $b.json"
}

# 2. Double high plants
$doublePlants = @(
    @{ name = "sift_tallgrass"; top = "sift_tallgrass"; bottom = "sift_tallgrass_bottom" },
    @{ name = "sift_orange_tall_grass"; top = "sift_orange_tall_grass"; bottom = "sift_orange_tall_grass_bottom" }
)

foreach ($dp in $doublePlants) {
    $n = $dp.name
    $t = $dp.top
    $b = $dp.bottom
    $json = @"
{
  "variants": {
    "half=lower": {
      "model": "pysift:block/$b"
    },
    "half=upper": {
      "model": "pysift:block/$t"
    }
  }
}
"@
    [System.IO.File]::WriteAllText("$blockstatesDir/$n.json", $json, [System.Text.Encoding]::UTF8)
    Write-Host "Created double blockstate: $n.json"
}

# 3. Update lang files from json
$transJson = [System.IO.File]::ReadAllText("tools/vegetation_translations.json", [System.Text.Encoding]::UTF8) | ConvertFrom-Json
$translations = $transJson.translations

$zhPath = "src/main/resources/assets/pysift/lang/zh_tw.json"
$enPath = "src/main/resources/assets/pysift/lang/en_us.json"

$zhJson = [System.IO.File]::ReadAllText($zhPath, [System.Text.Encoding]::UTF8) | ConvertFrom-Json
$enJson = [System.IO.File]::ReadAllText($enPath, [System.Text.Encoding]::UTF8) | ConvertFrom-Json

foreach ($prop in $translations.PSObject.Properties) {
    $k = $prop.Name
    $val = $prop.Value
    $zhJson | Add-Member -MemberType NoteProperty -Name $k -Value $val.zh -Force
    $enJson | Add-Member -MemberType NoteProperty -Name $k -Value $val.en -Force
}

$zhOut = $zhJson | ConvertTo-Json -Depth 10
$enOut = $enJson | ConvertTo-Json -Depth 10

[System.IO.File]::WriteAllText($zhPath, $zhOut, [System.Text.Encoding]::UTF8)
[System.IO.File]::WriteAllText($enPath, $enOut, [System.Text.Encoding]::UTF8)
Write-Host "Updated zh_tw.json and en_us.json"

# 4. Update replaceable_by_trees tag
$repTagPath = "src/main/resources/data/minecraft/tags/block/replaceable_by_trees.json"
$repJson = [System.IO.File]::ReadAllText($repTagPath, [System.Text.Encoding]::UTF8) | ConvertFrom-Json
$toAdd = @(
    "pysift:carapace_flower", "pysift:carapace_short_grass", "pysift:sculk_grass",
    "pysift:sift_short_grass", "pysift:sift_tallgrass", "pysift:sift_orange_short_grass",
    "pysift:sift_orange_tall_grass", "pysift:sift_red_short_grass", "pysift:sift_small_flowers",
    "pysift:sift_small_flowers_yellow", "pysift:soul_bubble_flower", "pysift:carapace_vine",
    "pysift:green_tree_vine", "pysift:orange_tree_vine", "pysift:soul_vine",
    "pysift:sift_wall_leaf", "pysift:sift_cleaver_plant", "pysift:sift_soul_cleaver_plant",
    "pysift:weat", "pysift:weat_plant", "pysift:weat_small_plant", "pysift:yellow_leaf"
)

$valList = [System.Collections.Generic.List[string]]($repJson.values)
foreach ($item in $toAdd) {
    if (-not $valList.Contains($item)) {
        $valList.Add($item)
    }
}
$repJson.values = $valList.ToArray()
[System.IO.File]::WriteAllText($repTagPath, ($repJson | ConvertTo-Json -Depth 10), [System.Text.Encoding]::UTF8)
Write-Host "Updated replaceable_by_trees.json tag"

# 5. Update small_flowers tag
$flowerTagPath = "src/main/resources/data/minecraft/tags/block/small_flowers.json"
$flowerJson = [System.IO.File]::ReadAllText($flowerTagPath, [System.Text.Encoding]::UTF8) | ConvertFrom-Json
$flowerList = [System.Collections.Generic.List[string]]($flowerJson.values)
$flowerAdds = @(
    "pysift:carapace_flower", "pysift:sift_small_flowers", "pysift:sift_small_flowers_yellow", "pysift:soul_bubble_flower"
)
foreach ($f in $flowerAdds) {
    if (-not $flowerList.Contains($f)) {
        $flowerList.Add($f)
    }
}
$flowerJson.values = $flowerList.ToArray()
[System.IO.File]::WriteAllText($flowerTagPath, ($flowerJson | ConvertTo-Json -Depth 10), [System.Text.Encoding]::UTF8)
Write-Host "Updated small_flowers.json tag"

Write-Host "Code generation completed successfully!"
