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
 * 靈魂研磨（pysift:soul_grinding）：一個材料 → 結果，格式和切石機一樣：
 * {"type": "pysift:soul_grinding", "ingredient": "pysift:siftite_ore", "result": {"id": "pysift:raw_siftite", "count": 2}}。
 * 每次研磨另有機率多出一個靈魂精華（{@link SoulGrinderBlockEntity#ESSENCE_CHANCE}）。
 */
public class SoulGrindingRecipe extends SingleItemRecipe {
    public static final MapCodec<SoulGrindingRecipe> MAP_CODEC = simpleMapCodec(SoulGrindingRecipe::new);
    public static final StreamCodec<RegistryFriendlyByteBuf, SoulGrindingRecipe> STREAM_CODEC = simpleStreamCodec(SoulGrindingRecipe::new);
    public static final RecipeSerializer<SoulGrindingRecipe> SERIALIZER = new RecipeSerializer<>(MAP_CODEC, STREAM_CODEC);

    public SoulGrindingRecipe(CommonInfo info, Ingredient input, ItemStackTemplate result) {
        super(info, input, result);
    }

    @Override
    public RecipeSerializer<SoulGrindingRecipe> getSerializer() {
        return SERIALIZER;
    }

    @Override
    public RecipeType<SoulGrindingRecipe> getType() {
        return SoulPower.SOUL_GRINDING;
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
