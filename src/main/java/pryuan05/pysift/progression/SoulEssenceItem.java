package pryuan05.pysift.progression;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.context.UseOnContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.block.state.properties.Property;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

/**
 * 靈魂精華：像除錯棒一樣改變方塊的型態，但做成生存模式用的道具。
 * <ul>
 *   <li>右鍵方塊：把選中的型態換成下一個（例如色調、紋路、朝向），每次消耗 1 個靈魂精華（創造模式不消耗）。</li>
 *   <li>潛行＋右鍵：換選下一個型態，不消耗。</li>
 * </ul>
 * 會複製方塊或作弊的型態不能改（半磚疊層、海鞘數量、作物生長、液面高度、紅石訊號…），換完放不住的狀態會跳過；
 * 由兩格組成的方塊（門、床、大箱子、活塞）整個不能改，改一半會壞掉。
 * 每位玩家選的型態只記在伺服器記憶體裡，精華不帶資料，所以還是能疊在一起。
 */
public class SoulEssenceItem extends HintItem {
    /** 會複製方塊、跳過成長，或下一刻就被遊戲改回去的型態。 */
    private static final Set<String> LOCKED = Set.of(
            "waterlogged", "occupied", "extended", "short",
            "pickles", "eggs", "candles", "layers", "flower_amount", "segment_amount", "bites", "charges",
            "level", "honey_level", "age", "stage", "hatch", "distance", "persistent",
            "power", "powered", "triggered", "enabled", "lit", "open", "has_book", "has_record");
    private static final Map<UUID, String> SELECTED = new HashMap<>();

    public SoulEssenceItem(Properties properties) {
        super(properties, "tooltip.pysift.soul_essence.use", "tooltip.pysift.soul_essence.select");
    }

    @Override
    public InteractionResult useOn(UseOnContext context) {
        Level level = context.getLevel();
        if (!(context.getPlayer() instanceof ServerPlayer player)) {
            return level.isClientSide() ? InteractionResult.SUCCESS : InteractionResult.PASS;
        }
        BlockPos pos = context.getClickedPos();
        BlockState state = level.getBlockState(pos);
        List<Property<?>> properties = changeable(state);
        if (properties.isEmpty() || state.getDestroySpeed(level, pos) < 0 || !player.mayBuild()
                || !level.mayInteract(player, pos)) {
            player.sendOverlayMessage(Component.translatable("message.pysift.soul_essence.no_variants").withStyle(ChatFormatting.GRAY));
            return InteractionResult.FAIL;
        }
        Property<?> property = selected(player, properties);
        if (context.isSecondaryUseActive()) {
            property = properties.get((properties.indexOf(property) + 1) % properties.size());
            SELECTED.put(player.getUUID(), property.getName());
            player.sendOverlayMessage(Component.translatable("message.pysift.soul_essence.selected", property.getName(),
                    valueName(state, property)).withStyle(ChatFormatting.AQUA));
            return InteractionResult.SUCCESS;
        }
        BlockState next = cycle(state, property, level, pos);
        if (next == state) {
            player.sendOverlayMessage(Component.translatable("message.pysift.soul_essence.no_variants").withStyle(ChatFormatting.GRAY));
            return InteractionResult.FAIL;
        }
        level.setBlock(pos, next, Block.UPDATE_ALL);
        if (!player.hasInfiniteMaterials()) {
            context.getItemInHand().shrink(1);
        }
        ServerLevel server = (ServerLevel) level;
        server.sendParticles(ParticleTypes.SOUL, pos.getX() + 0.5, pos.getY() + 0.5, pos.getZ() + 0.5, 8, 0.35, 0.35, 0.35, 0.02);
        level.playSound(null, pos, SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.BLOCKS, 1.0f, 0.8f + level.getRandom().nextFloat() * 0.4f);
        player.sendOverlayMessage(Component.translatable("message.pysift.soul_essence.changed", property.getName(),
                valueName(next, property)).withStyle(ChatFormatting.AQUA));
        return InteractionResult.SUCCESS;
    }

    private static List<Property<?>> changeable(BlockState state) {
        List<Property<?>> out = new ArrayList<>();
        if (state.hasProperty(BlockStateProperties.DOUBLE_BLOCK_HALF) || state.hasProperty(BlockStateProperties.BED_PART)
                || state.hasProperty(BlockStateProperties.CHEST_TYPE) || state.hasProperty(BlockStateProperties.PISTON_TYPE)
                || state.hasProperty(BlockStateProperties.EXTENDED)) {
            return out;
        }
        for (Property<?> property : state.getProperties()) {
            if (property != BlockStateProperties.SLAB_TYPE && !LOCKED.contains(property.getName())
                    && property.getPossibleValues().size() > 1) {
                out.add(property);
            }
        }
        return out;
    }

    private static Property<?> selected(ServerPlayer player, List<Property<?>> properties) {
        String name = SELECTED.get(player.getUUID());
        return properties.stream().filter(p -> p.getName().equals(name)).findFirst().orElse(properties.getFirst());
    }

    /** 下一個放得住的值；全部都放不住就回傳原狀態。 */
    private static <T extends Comparable<T>> BlockState cycle(BlockState state, Property<T> property, Level level, BlockPos pos) {
        List<T> values = property.getPossibleValues();
        int start = values.indexOf(state.getValue(property));
        for (int i = 1; i < values.size(); i++) {
            BlockState candidate = state.setValue(property, values.get((start + i) % values.size()));
            if (candidate.canSurvive(level, pos)) {
                return candidate;
            }
        }
        return state;
    }

    private static <T extends Comparable<T>> String valueName(BlockState state, Property<T> property) {
        return property.getName(state.getValue(property));
    }
}
