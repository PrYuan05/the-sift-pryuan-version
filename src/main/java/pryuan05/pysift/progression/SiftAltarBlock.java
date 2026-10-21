package pryuan05.pysift.progression;

import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.ChatFormatting;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.BlockHitResult;
import pryuan05.pysift.entity.BossMechanics;
import pryuan05.pysift.worldgen.BossArenaSavedData;

import java.util.Comparator;
import java.util.Optional;

/**
 * 篩靈祭壇：放在 Boss 競技場（{@link BossArenaSavedData} 記錄的中心）{@link #ARENA_RANGE} 格內，
 * 手持召喚印記右鍵，消耗一個印記，在競技場中心重新召喚那座競技場的 Boss。
 * 競技場 {@link #BUSY_RANGE} 格內還有同種 Boss 活著時不會召喚。
 * 放下祭壇時就會告訴玩家它連結到哪座競技場（或最近的競技場在哪個方向、多遠）；失敗原因寫在聊天欄。
 */
public class SiftAltarBlock extends Block {
    public static final int ARENA_RANGE = 48;
    public static final int BUSY_RANGE = 64;

    public SiftAltarBlock(Properties properties) {
        super(properties);
    }

    private static Optional<BossArenaSavedData.ArenaRecord> nearestArena(ServerLevel level, BlockPos pos) {
        return BossArenaSavedData.get(level).getArenas().stream().min(Comparator.comparingDouble(a -> a.pos().distSqr(pos)));
    }

    private static boolean inRange(BossArenaSavedData.ArenaRecord arena, BlockPos pos) {
        return arena.pos().distSqr(pos) <= ARENA_RANGE * ARENA_RANGE;
    }

    private static Component bossName(BossArenaSavedData.ArenaRecord arena) {
        return BuiltInRegistries.ENTITY_TYPE.getOptional(Identifier.parse(arena.bossKey()))
                .map(EntityType::getDescription).orElse(Component.literal(arena.bossKey()));
    }

    /** 「往東北 56 格」：從祭壇看競技場中心的方向與距離。 */
    private static Component direction(BlockPos from, BlockPos to) {
        int dx = to.getX() - from.getX(), dz = to.getZ() - from.getZ();
        String ns = dz < -Math.abs(dx) / 2 ? "north" : dz > Math.abs(dx) / 2 ? "south" : "";
        String ew = dx > Math.abs(dz) / 2 ? "east" : dx < -Math.abs(dz) / 2 ? "west" : "";
        String key = ns.isEmpty() && ew.isEmpty() ? "here" : ns + ew;
        return Component.translatable("message.pysift.altar.dir." + key, (int) Math.sqrt(to.distSqr(from)));
    }

    /** 沒有競技場可連結：說明最近的競技場在哪。 */
    private static void explainTooFar(ServerLevel level, BlockPos pos, Player player) {
        Optional<BossArenaSavedData.ArenaRecord> nearest = nearestArena(level, pos);
        if (nearest.isPresent()) {
            player.sendSystemMessage(Component.translatable("message.pysift.altar.too_far", bossName(nearest.get()),
                    direction(pos, nearest.get().pos()), ARENA_RANGE).withStyle(ChatFormatting.RED));
        } else {
            player.sendSystemMessage(Component.translatable("message.pysift.altar.no_arena_found").withStyle(ChatFormatting.RED));
        }
    }

    @Override
    public void setPlacedBy(Level level, BlockPos pos, BlockState state, LivingEntity placer, ItemStack stack) {
        super.setPlacedBy(level, pos, state, placer, stack);
        if (!(level instanceof ServerLevel server) || !(placer instanceof Player player)) {
            return;
        }
        Optional<BossArenaSavedData.ArenaRecord> arena = nearestArena(server, pos).filter(a -> inRange(a, pos));
        if (arena.isPresent()) {
            player.sendSystemMessage(Component.translatable("message.pysift.altar.linked", bossName(arena.get()))
                    .withStyle(ChatFormatting.LIGHT_PURPLE));
            server.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, pos.getX() + 0.5, pos.getY() + 1.1, pos.getZ() + 0.5, 20, 0.3, 0.2, 0.3, 0.02);
        } else {
            explainTooFar(server, pos, player);
        }
    }

    @Override
    protected InteractionResult useItemOn(ItemStack stack, BlockState state, Level level, BlockPos pos, Player player,
                                          InteractionHand hand, BlockHitResult hit) {
        if (!stack.is(BossRewards.SUMMONING_SIGIL)) {
            return InteractionResult.TRY_WITH_EMPTY_HAND;
        }
        if (!(level instanceof ServerLevel server)) {
            return InteractionResult.SUCCESS;
        }
        Optional<BossArenaSavedData.ArenaRecord> arena = nearestArena(server, pos).filter(a -> inRange(a, pos));
        if (arena.isEmpty()) {
            explainTooFar(server, pos, player);
            return InteractionResult.FAIL;
        }
        Optional<EntityType<?>> type = BuiltInRegistries.ENTITY_TYPE.getOptional(Identifier.parse(arena.get().bossKey()));
        if (type.isEmpty()) {
            return InteractionResult.FAIL;
        }
        BlockPos center = arena.get().pos();
        boolean alive = !server.getEntitiesOfClass(Mob.class, new AABB(center).inflate(BUSY_RANGE),
                m -> m.getType() == type.get() && m.isAlive()).isEmpty();
        if (alive) {
            player.sendSystemMessage(Component.translatable("message.pysift.altar.boss_alive", bossName(arena.get()))
                    .withStyle(ChatFormatting.RED));
            return InteractionResult.FAIL;
        }
        if (!(type.get().create(server, EntitySpawnReason.TRIGGERED) instanceof Mob boss)) {
            return InteractionResult.FAIL;
        }
        BlockPos spawn = center.above();
        boss.snapTo(spawn.getX() + 0.5, spawn.getY(), spawn.getZ() + 0.5, player.getYRot() + 180.0f, 0.0f);
        BossMechanics.setArena(boss, spawn);
        boss.finalizeSpawn(server, server.getCurrentDifficultyAt(spawn), EntitySpawnReason.TRIGGERED, null);
        server.addFreshEntity(boss);
        stack.consume(1, player);
        server.playSound(null, pos, SoundEvents.WITHER_SPAWN, SoundSource.HOSTILE, 1.5f, 0.8f);
        server.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, pos.getX() + 0.5, pos.getY() + 1.2, pos.getZ() + 0.5, 60, 0.4, 0.6, 0.4, 0.08);
        server.sendParticles(ParticleTypes.SCULK_SOUL, spawn.getX() + 0.5, spawn.getY() + 1.0, spawn.getZ() + 0.5, 40, 1.5, 1.5, 1.5, 0.05);
        player.sendOverlayMessage(Component.translatable("message.pysift.altar.summoned", boss.getDisplayName()));
        return InteractionResult.SUCCESS_SERVER;
    }
}
