package pryuan05.pysift.block;

import java.util.List;
import net.fabricmc.fabric.api.event.player.UseItemCallback;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import pryuan05.pysift.entity.ModEntities;
import pryuan05.pysift.entity.mob.SingerEntity;

/**
 * 遠古城市「伏守者巨口」× 歌者共鳴開門儀式。
 * <ol>
 *   <li>在強化深板岩附近（16 格內）吹響山羊角：24 格內沒有歌者時，在玩家面前召喚一隻（幽匿靈魂粒子、催發體綻放聲）。</li>
 *   <li>手持迴音碎片、靈魂沙、靈魂土或山羊角右鍵歌者：歌者共鳴（音爆 + 信標啟動聲、粒子束），
 *       以 BFS 把周圍 16 格內封閉的強化深板岩框架內部整片填成傳送門；找不到封閉框架時，在歌者前方 3 格召喚無邊框裂隙型傳送門。</li>
 * </ol>
 */
public final class SiftPortalRitual {
    private SiftPortalRitual() {
    }

    public static void register() {
        UseItemCallback.EVENT.register((player, level, hand) -> {
            if (level instanceof ServerLevel server && player.getItemInHand(hand).is(Items.GOAT_HORN)) {
                summonSinger(server, player);
            }
            return InteractionResult.PASS;   // 山羊角照常吹響
        });
    }

    private static boolean nearReinforcedDeepslate(ServerLevel level, BlockPos centre, int radius) {
        for (BlockPos p : BlockPos.betweenClosed(centre.offset(-radius, -radius, -radius), centre.offset(radius, radius, radius))) {
            if (level.getBlockState(p).is(Blocks.REINFORCED_DEEPSLATE)) {
                return true;
            }
        }
        return false;
    }

    private static void summonSinger(ServerLevel level, Player player) {
        BlockPos at = player.blockPosition();
        if (!nearReinforcedDeepslate(level, at, 16)
                || !level.getEntitiesOfClass(SingerEntity.class, new AABB(at).inflate(24)).isEmpty()) {
            return;
        }
        Vec3 look = player.getLookAngle().multiply(1, 0, 1).normalize();
        BlockPos spot = BlockPos.containing(player.position().add(look.scale(3)));
        for (int dy = 2; dy >= -3; dy--) {   // 找最近的站立點
            BlockPos p = spot.above(dy);
            if (level.getBlockState(p).isAir() && level.getBlockState(p.above()).isAir() && level.getBlockState(p.below()).isSolid()) {
                spot = p;
                break;
            }
        }
        SingerEntity singer = ModEntities.SINGER.create(level, EntitySpawnReason.TRIGGERED);
        if (singer == null) {
            return;
        }
        singer.snapTo(spot.getX() + 0.5, spot.getY(), spot.getZ() + 0.5, player.getYRot() + 180, 0);
        singer.startEmerging();   // 從地底爬出
        level.addFreshEntity(singer);
        level.sendParticles(ParticleTypes.SCULK_SOUL, singer.getX(), singer.getY() + 1, singer.getZ(), 24, 0.6, 0.8, 0.6, 0.04);
        singer.playSound(SoundEvents.SCULK_CATALYST_BLOOM, 2.0f, 1.0f);
    }

    /** 歌者共鳴：找封閉框架填門，找不到就在前方蓋測試門。回傳是否開了門。 */
    public static boolean resonate(SingerEntity singer, Player player) {
        if (!(singer.level() instanceof ServerLevel level)) {
            return false;
        }
        singer.playSound(SoundEvents.WARDEN_SONIC_BOOM, 2.0f, 1.2f);
        singer.playSound(SoundEvents.BEACON_ACTIVATE, 2.0f, 1.0f);
        List<BlockPos> filled = SiftPortalBlock.fillFrame(level, singer.blockPosition(), 16);
        Vec3 target;
        if (!filled.isEmpty()) {
            double x = 0, y = 0, z = 0;
            for (BlockPos p : filled) {
                x += p.getX() + 0.5;
                y += p.getY() + 0.5;
                z += p.getZ() + 0.5;
            }
            target = new Vec3(x / filled.size(), y / filled.size(), z / filled.size());
        } else {
            // 歌者前方 3 格召喚無邊框裂隙型傳送門（中央 5×3 主要進入區 + 邊緣擴散光塊），門面面向歌者
            Vec3 fwd = Vec3.directionFromRotation(0, singer.getYRot());
            Direction facing = Direction.getApproximateNearest(fwd.x, 0, fwd.z);
            Direction.Axis axis = facing.getAxis() == Direction.Axis.Z ? Direction.Axis.X : Direction.Axis.Z;
            BlockPos centre = singer.blockPosition().relative(facing, 3);
            for (int dy = 1; dy >= -2; dy--) {
                BlockPos test = centre.above(dy);
                if (level.getBlockState(test.below()).isSolid() && SiftPortalBlock.canPortalReplace(level.getBlockState(test))) {
                    centre = test;
                    break;
                }
            }
            SiftPortalBlock.buildRiftPortal(level, centre, axis);
            target = Vec3.atCenterOf(centre.above(1));
        }
        // 粒子束：從歌者到門中心
        Vec3 from = singer.position().add(0, singer.getBbHeight() * 0.7, 0);
        Vec3 step = target.subtract(from);
        int n = Math.max(4, (int) (step.length() * 2));
        for (int i = 0; i <= n; i++) {
            Vec3 p = from.add(step.scale(i / (double) n));
            level.sendParticles(i % 3 == 0 ? ParticleTypes.SONIC_BOOM : ParticleTypes.END_ROD, p.x, p.y, p.z, 1, 0, 0, 0, 0);
        }
        return true;
    }
}
