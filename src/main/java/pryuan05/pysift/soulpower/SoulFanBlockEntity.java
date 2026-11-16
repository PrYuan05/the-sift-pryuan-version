package pryuan05.pysift.soulpower;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.tags.BlockTags;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.SingleRecipeInput;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.CampfireBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

/**
 * 靈魂風扇的氣流：長度 = |RPM| ÷ 4 格（最多 {@link #MAX_RANGE}），碰到實心方塊就停。氣流裡的生物與掉落物被推（或吸）著走；
 * 在靈魂火之後的掉落物待滿 {@link #HAUNT_TICKS} tick 就依 pysift:soul_haunting 轉換。
 */
public class SoulFanBlockEntity extends KineticBlockEntity {
    public static final int MAX_RANGE = 12;
    public static final int HAUNT_TICKS = 60;
    private final Map<UUID, Integer> haunting = new HashMap<>();

    public SoulFanBlockEntity(BlockPos pos, BlockState state) {
        super(SoulPower.SOUL_FAN_ENTITY, pos, state);
    }

    /** 氣流往哪吹：正轉吹向正面，反轉吸向風扇。 */
    public Direction flow() {
        Direction facing = getBlockState().getValue(SoulMachineBlock.FACING);
        float along = speed * (facing.getAxisDirection() == Direction.AxisDirection.POSITIVE ? 1 : -1);
        return along >= 0 ? facing : facing.getOpposite();
    }

    /** 氣流的長度（格）。 */
    public int range(Level level) {
        Direction facing = getBlockState().getValue(SoulMachineBlock.FACING);
        int max = Math.min(MAX_RANGE, Math.max(1, Math.round(Math.abs(speed) / 4f)));
        for (int i = 1; i <= max; i++) {
            BlockState s = level.getBlockState(worldPosition.relative(facing, i));
            if (s.isCollisionShapeFullBlock(level, worldPosition.relative(facing, i))) {
                return i - 1;
            }
        }
        return max;
    }

    private static boolean soulFire(BlockState s) {
        return s.is(Blocks.SOUL_FIRE) || s.is(Blocks.SOUL_CAMPFIRE) && s.getValue(CampfireBlock.LIT);
    }

    public static void serverTick(Level level, BlockPos pos, BlockState state, SoulFanBlockEntity fan) {
        ServerLevel server = (ServerLevel) level;
        long now = level.getGameTime();
        if (now - fan.network.time() > SoulSignal.INTERVAL * 3L && now % SoulSignal.INTERVAL == 0) {
            fan.network = SoulSignal.Result.IDLE;
            SoulSignal.poll(server, pos);
        }
        if (fan.speed == 0) {
            fan.haunting.clear();
            return;
        }
        Direction facing = state.getValue(SoulMachineBlock.FACING);
        int range = fan.range(level);
        if (range <= 0) {
            return;
        }
        int fire = -1;   // the first soul fire in the stream
        for (int i = 1; i <= range && fire < 0; i++) {
            if (soulFire(level.getBlockState(pos.relative(facing, i)))) {
                fire = i;
            }
        }
        AABB stream = new AABB(pos.relative(facing)).expandTowards(Vec3.atLowerCornerOf(facing.getUnitVec3i()).scale(range - 1));
        Vec3 push = Vec3.atLowerCornerOf(fan.flow().getUnitVec3i()).scale(0.045 * Math.min(2.0, Math.abs(fan.speed) / SoulSignal.SPEED));
        for (Entity e : level.getEntitiesOfClass(Entity.class, stream)) {
            if (e instanceof Player p && (p.isSpectator() || p.getAbilities().flying)) {
                continue;
            }
            e.setDeltaMovement(e.getDeltaMovement().add(push));
            e.needsSync = true;   // send the new motion to clients (players)
            e.fallDistance = 0;
            if (fire > 0 && e instanceof ItemEntity item && beyond(pos, facing, item.blockPosition(), fire)) {
                fan.haunt(server, item);
            }
        }
        if (now % 4 == 0) {   // a visible stream
            double d = 1 + level.getRandom().nextDouble() * (range - 1);
            Vec3 c = Vec3.atCenterOf(pos).add(Vec3.atLowerCornerOf(facing.getUnitVec3i()).scale(d));
            Vec3 v = Vec3.atLowerCornerOf(fan.flow().getUnitVec3i()).scale(0.2);
            server.sendParticles(fire > 0 && d >= fire ? ParticleTypes.SOUL : ParticleTypes.CLOUD, c.x, c.y, c.z, 0, v.x, v.y, v.z, 1.0);
        }
        if (now % 100 == 0) {
            fan.haunting.keySet().removeIf(id -> server.getEntity(id) == null);
        }
    }

    /** item 在靈魂火之後（從風扇數過去，比火更遠）。 */
    private static boolean beyond(BlockPos fan, Direction facing, BlockPos at, int fire) {
        BlockPos rel = at.subtract(fan);
        int along = rel.getX() * facing.getStepX() + rel.getY() * facing.getStepY() + rel.getZ() * facing.getStepZ();
        return along >= fire;
    }

    private void haunt(ServerLevel level, ItemEntity item) {
        int t = haunting.merge(item.getUUID(), 1, Integer::sum);
        if (t % 10 == 0) {
            level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, item.getX(), item.getY() + 0.3, item.getZ(), 2, 0.1, 0.1, 0.1, 0.01);
        }
        if (t < HAUNT_TICKS) {
            return;
        }
        haunting.remove(item.getUUID());
        ItemStack stack = item.getItem();
        var recipe = level.getServer().getRecipeManager().getRecipeFor(SoulPower.SOUL_HAUNTING, new SingleRecipeInput(stack), level);
        if (recipe.isEmpty()) {
            return;
        }
        ItemStack result = recipe.get().value().assemble(new SingleRecipeInput(stack));
        result.setCount(result.getCount() * stack.getCount());
        item.setItem(result);
        level.sendParticles(ParticleTypes.SOUL, item.getX(), item.getY() + 0.3, item.getZ(), 4, 0.15, 0.15, 0.15, 0.02);
    }
}
