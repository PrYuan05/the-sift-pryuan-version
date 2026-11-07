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
 * 靈魂淨化篩（pysift:soul_sifting）：一個材料 → 結果，格式和研磨一樣，例如
 * {"type": "pysift:soul_sifting", "ingredient": "minecraft:sculk", "result": {"id": "pysift:red_sculk"}}。
 * 每次篩另有機率多出一個靈魂精華（{@link SoulGrinderBlockEntity#ESSENCE_CHANCE}）。
 */
public class SoulSiftingRecipe extends SingleItemRecipe {
    public static final MapCodec<SoulSiftingRecipe> MAP_CODEC = simpleMapCodec(SoulSiftingRecipe::new);
    public static final StreamCodec<RegistryFriendlyByteBuf, SoulSiftingRecipe> STREAM_CODEC = simpleStreamCodec(SoulSiftingRecipe::new);
    public static final RecipeSerializer<SoulSiftingRecipe> SERIALIZER = new RecipeSerializer<>(MAP_CODEC, STREAM_CODEC);

    public SoulSiftingRecipe(CommonInfo info, Ingredient input, ItemStackTemplate result) {
        super(info, input, result);
    }

    @Override
    public RecipeSerializer<SoulSiftingRecipe> getSerializer() {
        return SERIALIZER;
    }

    @Override
    public RecipeType<SoulSiftingRecipe> getType() {
        return SoulPower.SOUL_SIFTING;
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
