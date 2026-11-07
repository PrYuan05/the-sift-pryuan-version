package pryuan05.pysift.soulpower;

import com.mojang.serialization.MapCodec;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.world.item.ItemStackTemplate;
import net.minecraft.world.item.crafting.Ingredient;
import net.minecraft.world.item.crafting.RecipeBookCategories;
import net.minecraft.world.item.crafting.RecipeBookCategory;
import net.minecraft.world.item.crafting.RecipeSerializer;
import net.minecraft.world.item.crafting.RecipeType;
import net.minecraft.world.item.crafting.SingleItemRecipe;

/**
 * 靈魂薰染（pysift:soul_haunting）：靈魂風扇的氣流穿過靈魂火後，掉落物依這個配方轉換（整疊一起），例如
 * {"type": "pysift:soul_haunting", "ingredient": "#minecraft:sand", "result": {"id": "minecraft:soul_sand"}}。
 */
public class SoulHauntingRecipe extends SingleItemRecipe {
    public static final MapCodec<SoulHauntingRecipe> MAP_CODEC = simpleMapCodec(SoulHauntingRecipe::new);
    public static final StreamCodec<RegistryFriendlyByteBuf, SoulHauntingRecipe> STREAM_CODEC = simpleStreamCodec(SoulHauntingRecipe::new);
    public static final RecipeSerializer<SoulHauntingRecipe> SERIALIZER = new RecipeSerializer<>(MAP_CODEC, STREAM_CODEC);

    public SoulHauntingRecipe(CommonInfo info, Ingredient input, ItemStackTemplate result) {
        super(info, input, result);
    }

    @Override
    public RecipeSerializer<SoulHauntingRecipe> getSerializer() {
        return SERIALIZER;
    }

    @Override
    public RecipeType<SoulHauntingRecipe> getType() {
        return SoulPower.SOUL_HAUNTING;
    }

    @Override
    public String group() {
        return "";
    }

    @Override
    public RecipeBookCategory recipeBookCategory() {
        return RecipeBookCategories.STONECUTTER;
    }
}
