package pryuan05.pysift.block;

import com.mojang.serialization.MapCodec;
import net.minecraft.core.component.DataComponents;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.DyedItemColor;
import net.minecraft.world.item.crafting.CraftingInput;
import net.minecraft.world.item.crafting.CustomRecipe;
import net.minecraft.world.item.crafting.RecipeSerializer;
import net.minecraft.world.level.Level;

import java.util.ArrayList;
import java.util.List;
import java.util.Set;

/**
 * 用篩靈界的新染料染皮甲（皮革頭盔、胸甲、護腿、靴子、皮革馬鎧、狼鎧）：一件可染色的物品 + 一個以上的新染料。
 * 原版的染色配方只認 16 色的 DyeColor，所以另外寫；混色的算法和原版一樣（顏色平均，再把亮度拉回最亮的那個）。
 * 資料檔：data/pysift/recipe/sift_dye_armor.json（{"type": "pysift:crafting_sift_dye"}）。
 */
public final class SiftDyeRecipe extends CustomRecipe {
    public static final SiftDyeRecipe INSTANCE = new SiftDyeRecipe();
    public static final RecipeSerializer<SiftDyeRecipe> SERIALIZER =
            new RecipeSerializer<>(MapCodec.unit(INSTANCE), StreamCodec.unit(INSTANCE));
    private static final Set<Item> DYEABLE = Set.of(Items.LEATHER_HELMET, Items.LEATHER_CHESTPLATE, Items.LEATHER_LEGGINGS,
            Items.LEATHER_BOOTS, Items.LEATHER_HORSE_ARMOR, Items.WOLF_ARMOR);

    private SiftDyeRecipe() {
    }

    @Override
    public boolean matches(CraftingInput input, Level level) {
        int targets = 0, dyes = 0;
        for (ItemStack stack : input.items()) {
            if (stack.isEmpty()) {
                continue;
            }
            if (DYEABLE.contains(stack.getItem())) {
                targets++;
            } else if (stack.getItem() instanceof SiftColors.SiftDyeItem) {
                dyes++;
            } else {
                return false;
            }
        }
        return targets == 1 && dyes > 0;
    }

    @Override
    public ItemStack assemble(CraftingInput input) {
        ItemStack target = ItemStack.EMPTY;
        List<Integer> colours = new ArrayList<>();
        for (ItemStack stack : input.items()) {
            if (DYEABLE.contains(stack.getItem())) {
                target = stack;
            } else if (stack.getItem() instanceof SiftColors.SiftDyeItem dye) {
                colours.add(dye.color.rgb);
            }
        }
        if (target.isEmpty() || colours.isEmpty()) {
            return ItemStack.EMPTY;
        }
        DyedItemColor old = target.get(DataComponents.DYED_COLOR);
        if (old != null) {
            colours.add(old.rgb());
        }
        int r = 0, g = 0, b = 0, brightest = 0;
        for (int c : colours) {
            int cr = c >> 16 & 0xFF, cg = c >> 8 & 0xFF, cb = c & 0xFF;
            r += cr;
            g += cg;
            b += cb;
            brightest += Math.max(cr, Math.max(cg, cb));
        }
        int n = colours.size();
        r /= n;
        g /= n;
        b /= n;
        float scale = (float) (brightest / n) / Math.max(1, Math.max(r, Math.max(g, b)));
        r = Math.min(255, Math.round(r * scale));
        g = Math.min(255, Math.round(g * scale));
        b = Math.min(255, Math.round(b * scale));
        ItemStack result = target.copyWithCount(1);
        result.set(DataComponents.DYED_COLOR, new DyedItemColor(r << 16 | g << 8 | b));
        return result;
    }

    @Override
    public RecipeSerializer<SiftDyeRecipe> getSerializer() {
        return SERIALIZER;
    }
}
