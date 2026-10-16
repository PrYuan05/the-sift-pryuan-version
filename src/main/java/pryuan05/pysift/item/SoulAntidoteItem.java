package pryuan05.pysift.item;

import net.minecraft.core.component.DataComponents;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.ItemUseAnimation;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.Consumable;
import net.minecraft.world.level.Level;
import pryuan05.pysift.effect.SoulBurn;

/**
 * 靈魂解藥（pysift:soul_antidote）：像藥水一樣喝（0.8 秒，不需要飢餓），喝完留下玻璃瓶。
 * 解除靈魂剝奪（含靈魂火、伏聆視野）與靈魂碎裂的上限鎖定；沒有碎裂時把被抽走的血量全部還回來（規則見 {@link SoulBurn#cure}）。
 */
public class SoulAntidoteItem extends Item {
    public SoulAntidoteItem(Item.Properties properties) {
        super(properties.stacksTo(16)
                .component(DataComponents.CONSUMABLE, Consumable.builder()
                        .consumeSeconds(0.8f)
                        .animation(ItemUseAnimation.DRINK)
                        .sound(SoundEvents.GENERIC_DRINK)
                        .hasConsumeParticles(false)
                        .build())
                .usingConvertsTo(Items.GLASS_BOTTLE));
    }

    @Override
    public ItemStack finishUsingItem(ItemStack stack, Level level, LivingEntity entity) {
        if (!level.isClientSide() && entity instanceof ServerPlayer player) {
            SoulBurn.cure(player);
        }
        return super.finishUsingItem(stack, level, entity);
    }
}
