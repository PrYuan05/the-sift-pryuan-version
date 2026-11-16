package pryuan05.pysift.entity.mob;

import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

/**
 * Sculk Monstrosity 的「幽匿觸媒召喚」：在場上冒出幾個原版幽匿觸媒方塊，周圍逐漸長出幽匿脈絡；
 * {@link #FUSE} tick 後還沒被打掉的觸媒會爆開——半徑 4 格內的非敵對生物受傷，並替 Boss 回血。
 * 玩家可以提前把觸媒挖掉（觸媒硬度很低）。爆炸或 Boss 消失時，觸媒和脈絡都會清掉，不會留在世界上。
 */
public final class SculkCatalystField {
    private static final int FUSE = 120;
    private static final double BLAST_RADIUS = 4.0;
    private static final float BLAST_DAMAGE = 10.0f;
    private static final float HEAL_FRACTION = 0.05f;

    private static final class Catalyst {
        final BlockPos pos;
        final int explodeAt;
        final List<BlockPos> veins = new ArrayList<>();

        Catalyst(BlockPos pos, int explodeAt) {
            this.pos = pos;
            this.explodeAt = explodeAt;
        }
    }

    private final Mob boss;
    private final List<Catalyst> catalysts = new ArrayList<>();

    public SculkCatalystField(Mob boss) {
        this.boss = boss;
    }

    public boolean isActive() {
        return !catalysts.isEmpty();
    }

    /** 在 centre 周圍 radius 格內、地面上冒出 count 個觸媒。 */
    public void summon(ServerLevel level, Vec3 centre, int count, double radius) {
        RandomSource r = boss.getRandom();
        for (int i = 0; i < count; i++) {
            double a = r.nextDouble() * Math.PI * 2;
            double d = 3 + r.nextDouble() * (radius - 3);
            BlockPos column = BlockPos.containing(centre.x + Math.cos(a) * d, centre.y, centre.z + Math.sin(a) * d);
            BlockPos spot = findGround(level, column);
            if (spot == null) {
                continue;
            }
            level.setBlock(spot, Blocks.SCULK_CATALYST.defaultBlockState(), Block.UPDATE_ALL);
            catalysts.add(new Catalyst(spot, boss.tickCount + FUSE));
            level.sendParticles(ParticleTypes.SCULK_SOUL, spot.getX() + 0.5, spot.getY() + 1.0, spot.getZ() + 0.5, 12, 0.4, 0.3, 0.4, 0.03);
            level.playSound(null, spot, SoundEvents.SCULK_CATALYST_BLOOM, boss.getSoundSource(), 1.5f, 0.8f);
        }
    }

    /** 柱子裡最靠近 y 的「空氣、下方是固體」位置。 */
    private static BlockPos findGround(ServerLevel level, BlockPos column) {
        for (int dy = 3; dy >= -4; dy--) {
            BlockPos p = column.above(dy);
            if (level.getBlockState(p).isAir() && level.getBlockState(p.below()).isSolid()) {
                return p;
            }
        }
        return null;
    }

    public void tick(ServerLevel level) {
        Iterator<Catalyst> it = catalysts.iterator();
        while (it.hasNext()) {
            Catalyst c = it.next();
            boolean alive = level.getBlockState(c.pos).is(Blocks.SCULK_CATALYST);
            if (!alive) {   // 被玩家挖掉：只清脈絡
                clearVeins(level, c);
                level.sendParticles(ParticleTypes.SCULK_CHARGE_POP, c.pos.getX() + 0.5, c.pos.getY() + 0.5, c.pos.getZ() + 0.5, 10, 0.3, 0.3, 0.3, 0.05);
                it.remove();
                continue;
            }
            int left = c.explodeAt - boss.tickCount;
            if (left > 0 && boss.tickCount % 8 == 0) {
                spreadVein(level, c, 1 + (FUSE - left) * 3 / FUSE);
                level.sendParticles(ParticleTypes.SCULK_CHARGE_POP, c.pos.getX() + 0.5, c.pos.getY() + 1.0, c.pos.getZ() + 0.5, 2, 0.2, 0.1, 0.2, 0.01);
            }
            if (left <= 0) {
                explode(level, c);
                it.remove();
            }
        }
    }

    /** 在觸媒周圍 radius 格內的地面上長一條脈絡（只長在空氣裡、下方是固體的位置）。 */
    private void spreadVein(ServerLevel level, Catalyst c, int radius) {
        RandomSource r = boss.getRandom();
        for (int attempt = 0; attempt < 3; attempt++) {
            BlockPos p = c.pos.offset(r.nextInt(radius * 2 + 1) - radius, 0, r.nextInt(radius * 2 + 1) - radius);
            BlockPos spot = findGround(level, p);
            if (spot != null && !spot.equals(c.pos)) {
                BlockState vein = Blocks.SCULK_VEIN.defaultBlockState().setValue(BlockStateProperties.DOWN, true);
                level.setBlock(spot, vein, Block.UPDATE_CLIENTS);
                c.veins.add(spot);
                return;
            }
        }
    }

    private void explode(ServerLevel level, Catalyst c) {
        Vec3 at = Vec3.atCenterOf(c.pos);
        level.removeBlock(c.pos, false);
        clearVeins(level, c);
        level.sendParticles(ParticleTypes.SCULK_SOUL, at.x, at.y, at.z, 30, 1.2, 0.6, 1.2, 0.08);
        level.sendParticles(ParticleTypes.EXPLOSION, at.x, at.y, at.z, 2, 0.5, 0.3, 0.5, 0.0);
        level.playSound(null, c.pos, SoundEvents.SCULK_SHRIEKER_SHRIEK, boss.getSoundSource(), 2.0f, 0.7f);
        for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, new AABB(c.pos).inflate(BLAST_RADIUS),
                e -> e.isAlive() && !(e instanceof Enemy) && e.distanceToSqr(at) <= BLAST_RADIUS * BLAST_RADIUS)) {
            if (e.hurtServer(level, boss.damageSources().indirectMagic(boss, boss), BLAST_DAMAGE)) {
                Vec3 away = e.position().subtract(at).multiply(1, 0, 1);
                Vec3 dir = away.lengthSqr() < 1.0E-4 ? Vec3.ZERO : away.normalize();
                e.setDeltaMovement(e.getDeltaMovement().add(dir.x * 0.7, 0.4, dir.z * 0.7));
                e.needsSync = true;
            }
        }
        if (boss.isAlive()) {   // 靈魂流回 Boss：回血
            boss.heal(boss.getMaxHealth() * HEAL_FRACTION);
            Vec3 to = boss.position().add(0, boss.getBbHeight() * 0.5, 0).subtract(at);
            for (int i = 1; i <= 8; i++) {
                Vec3 p = at.add(to.scale(i / 8.0));
                level.sendParticles(ParticleTypes.SCULK_SOUL, p.x, p.y, p.z, 1, 0.1, 0.1, 0.1, 0.0);
            }
        }
    }

    private static void clearVeins(ServerLevel level, Catalyst c) {
        for (BlockPos v : c.veins) {
            if (level.getBlockState(v).is(Blocks.SCULK_VEIN)) {
                level.removeBlock(v, false);
            }
        }
        c.veins.clear();
    }

    /** Boss 死亡或被移除時：把還在的觸媒和脈絡清掉。 */
    public void clear(ServerLevel level) {
        for (Catalyst c : catalysts) {
            if (level.getBlockState(c.pos).is(Blocks.SCULK_CATALYST)) {
                level.removeBlock(c.pos, false);
            }
            clearVeins(level, c);
        }
        catalysts.clear();
    }
}
