package pryuan05.pysift.soulpower;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.SingleRecipeInput;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;
import pryuan05.pysift.block.RotSpread;
import pryuan05.pysift.progression.StoryTriggers;
import pryuan05.pysift.sound.ModSounds;

import java.util.Optional;

/**
 * 靈魂淨化篩：研磨機的一種（材料格、結果格、靈魂精華格、同一個介面），配方是 pysift:soul_sifting；
 * 轉動時，每 {@link #PERIOD} tick（32 RPM 時；越快越頻繁）在 {@link #RANGE} 格內找一塊藍色幽匿，變回赤紅幽匿
 * （{@link RotSpread#healOne}）。第一次淨化時，附近的玩家得到成就「篩回赤紅」。
 */
public class SoulSifterBlockEntity extends SoulGrinderBlockEntity {
    public static final int RANGE = 8;
    public static final int PERIOD = 40;
    private float purify;

    public SoulSifterBlockEntity(BlockPos pos, BlockState state) {
        super(SoulPower.SOUL_SIFTER_ENTITY, pos, state);
    }

    @Override
    protected Optional<ItemStack> result(ServerLevel level, SingleRecipeInput input) {
        return level.getServer().getRecipeManager().getRecipeFor(SoulPower.SOUL_SIFTING, input, level)
                .map(r -> r.value().assemble(input));
    }

    @Override
    protected SoundEvent workSound() {
        return ModSounds.SOUL_SIFTER_SIFT;
    }

    @Override
    protected void worldWork(ServerLevel level, BlockPos pos, long now) {
        purify += Math.abs(speed) / SoulSignal.SPEED;
        if (purify < PERIOD) {
            return;
        }
        purify = 0;
        for (int tries = 0; tries < 24; tries++) {
            BlockPos p = pos.offset(level.getRandom().nextInt(RANGE * 2 + 1) - RANGE, level.getRandom().nextInt(RANGE + 1) - RANGE / 2,
                    level.getRandom().nextInt(RANGE * 2 + 1) - RANGE);
            if (p.distSqr(pos) <= RANGE * RANGE && RotSpread.healOne(level, p)) {
                StoryTriggers.sifted(level, Vec3.atCenterOf(pos));
                return;
            }
        }
    }
}
