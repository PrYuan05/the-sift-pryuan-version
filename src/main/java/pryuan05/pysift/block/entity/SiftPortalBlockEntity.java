package pryuan05.pysift.block.entity;

import net.minecraft.core.BlockPos;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;

/** 篩靈界傳送門的方塊實體：只用來掛 SiftPortalBlockEntityRenderer（大面積珠光流光、邊緣聖光），本身不存資料。 */
public class SiftPortalBlockEntity extends BlockEntity {
    public SiftPortalBlockEntity(BlockPos pos, BlockState state) {
        super(ModBlockEntities.SIFT_PORTAL, pos, state);
    }
}
