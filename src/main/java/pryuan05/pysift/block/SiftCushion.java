package pryuan05.pysift.block;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.BlockTags;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.PostSpawnProcessor;
import net.minecraft.world.entity.decoration.Cushion;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.item.context.UseOnContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.gameevent.GameEvent;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.Vec3;

/**
 * 篩靈界顏色的坐墊。原版坐墊（{@link Cushion}）的顏色是 DyeColor，只有 16 色，所以這裡用同一個實體的子類別多記一個
 * 篩靈界顏色：坐上去、被打掉、被火燒等行為都沿用原版。原版程式裡「顏色 → 物品」的地方（掉落物、中鍵選取、
 * 破壞粒子）由 CushionMixin 換成 {@link #item()}；貼圖由客戶端的 SiftCushionRenderer 換。
 */
public class SiftCushion extends Cushion {
    private static final EntityDataAccessor<Integer> DATA_SIFT_COLOR = SynchedEntityData.defineId(SiftCushion.class, EntityDataSerializers.INT);

    @SuppressWarnings("unchecked")
    public SiftCushion(EntityType<? extends SiftCushion> type, Level level) {
        super((EntityType<Cushion>) (EntityType<?>) type, level);
    }

    public SiftColors.SiftColor getSiftColor() {
        SiftColors.SiftColor[] all = SiftColors.SiftColor.values();
        return all[Math.floorMod(this.entityData.get(DATA_SIFT_COLOR), all.length)];
    }

    public void setSiftColor(SiftColors.SiftColor color) {
        this.entityData.set(DATA_SIFT_COLOR, color.ordinal());
    }

    /** This cushion's item. */
    public Item item() {
        return SiftColors.CUSHIONS.get(getSiftColor());
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(DATA_SIFT_COLOR, 0);
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        output.putString("sift_color", getSiftColor().id);
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        String id = input.getStringOr("sift_color", SiftColors.SiftColor.TEAL.id);
        for (SiftColors.SiftColor c : SiftColors.SiftColor.values()) {
            if (c.id.equals(id)) {
                setSiftColor(c);
            }
        }
    }

    /** The cushion item: places a {@link SiftCushion} of its colour (vanilla's CushionItem always places the vanilla entity). */
    public static class SiftCushionItem extends Item {
        private final SiftColors.SiftColor color;

        public SiftCushionItem(SiftColors.SiftColor color, Properties properties) {
            super(properties);
            this.color = color;
        }

        @Override
        public InteractionResult useOn(UseOnContext original) {
            UseOnContext context = onCollisionShape(original);
            Level level = original.getLevel();
            if (context.getClickedFace() != Direction.UP) {
                return InteractionResult.FAIL;
            }
            BlockPlaceContext place = new BlockPlaceContext(context);
            BlockPos pos = place.getClickedPos();
            Vec3 at = Vec3.atCenterOfWithY(pos, context.getClickLocation().y);
            AABB box = SiftColors.CUSHION_TYPE.getSpawnAABB(at);
            if (!Cushion.canBePlacedAt(level, box)) {
                return InteractionResult.FAIL;
            }
            ItemStack stack = original.getItemInHand();
            if (level instanceof ServerLevel server) {
                if (!server.getEntitiesOfClass(Cushion.class, box).isEmpty()) {
                    return InteractionResult.FAIL;
                }
                PostSpawnProcessor<SiftCushion> config = EntityType.createDefaultStackConfig(server, stack, original.getPlayer());
                SiftCushion cushion = SiftColors.CUSHION_TYPE.create(server, config, pos, EntitySpawnReason.SPAWN_ITEM_USE, true, true);
                if (cushion == null) {
                    return InteractionResult.FAIL;
                }
                cushion.setSiftColor(color);
                cushion.snapTo(at, Direction.fromYRot(place.getRotation()).toYRot(), 0.0F);
                server.addFreshEntity(cushion);
                cushion.destroyIfInFire(server);
                level.playSound(null, cushion.getX(), cushion.getY(), cushion.getZ(), SoundEvents.CUSHION_PLACE, SoundSource.BLOCKS, 0.75F, 0.8F);
                cushion.gameEvent(GameEvent.ENTITY_PLACE, original.getPlayer());
                stack.consume(1, place.getPlayer());
            }
            return InteractionResult.SUCCESS;
        }

        /** Vanilla: on cauldrons, hoppers and composters the cushion sits on the collision shape, not the outline. */
        private static UseOnContext onCollisionShape(UseOnContext context) {
            Player player = context.getPlayer();
            if (player == null) {
                return context;
            }
            Level level = context.getLevel();
            BlockPos pos = context.getClickedPos();
            BlockState state = level.getBlockState(pos);
            if (!state.is(BlockTags.CUSHION_USES_COLLISION_SHAPE)) {
                return context;
            }
            Vec3 eye = player.getEyePosition();
            Vec3 through = context.getClickLocation().add(context.getClickLocation().subtract(eye).normalize().scale(0.001));
            BlockHitResult hit = state.getCollisionShape(level, pos).clip(eye, through, pos);
            return hit == null ? context : new UseOnContext(player, context.getHand(), hit);
        }
    }
}
