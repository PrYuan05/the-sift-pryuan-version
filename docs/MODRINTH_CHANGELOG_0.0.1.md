## v0.0.1

### Fixed: food saturation
Most Sift foods passed a vanilla-style saturation *modifier* (0.3–0.8) where 26.3's `FoodProperties` expects
saturation *points*, so they filled the hunger bar but left you hungry again almost at once. They now use vanilla's
formula (nutrition × modifier × 2):

| Food | Hunger | Saturation (before → after) |
|---|---|---|
| Sift Stew | 10 | 0.8 → 16 |
| Cooked Slabber Steak | 8 | 0.8 → 12.8 |
| Cooked Nuzzle Meat | 6 | 0.8 → 9.6 |
| Gloomcap Stew | 7 | 0.6 → 8.4 |
| Blub Jelly, Cooked Dartback Meat | 6 | 0.6 → 7.2 |
| Fried Nester Egg, Baked Roamroot Tuber | 5 | 0.6 → 6 |
| Soul Nectar | 4 | 0.4 → 3.2 |
| Wobble Jelly | 4 | 0.3 → 2.4 |
| Soul Berries | 3 | 0.4 → 2.4 |
| Raw Slabber Steak | 3 | 0.3 → 1.8 |
| Blub Gel, Raw Dartback Meat, Raw Nuzzle Meat | 2 | 0.3 → 1.2 |
| Roamroot Tuber | 1 | 0.3 → 0.6 |

The Aurum Apple, Aurum Carrot and Aurum Berries were already right and are unchanged.

### Fixed: names
- The 10 Sift biomes have names on the map, the F3 screen and `/locate` (they showed raw IDs before).
- Chinese: every creature now has one name everywhere (Codex, advancements, `/locate boss`, blocks named after
  it), the Codex is always 隙浮手記, and the Sculk Hammer is 幽匿重錘.
- Removed language keys for charoite blocks that no longer exist.

### New: The Sift Wiki
- A bilingual (繁體中文 / English) wiki in a minecraft.wiki-style layout:
  https://pryuan05.github.io/the-sift-pryuan-version/
- Story, progression guide, every block and item with crafting grids, uses and where it is found, all mobs with stats,
  spawns, drops and climate variants, biomes, structures, Soul Power and other mechanics, foods with hunger and
  saturation.
- Generated from the mod's own data by `tools/wiki/build_wiki.py`; see `tools/wiki/README.md`.

