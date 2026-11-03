package pryuan05.pysift.block;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.Registry;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.RandomSource;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.TransparentBlock;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.block.state.BlockState;
import pryuan05.pysift.PySift;
import pryuan05.pysift.fluid.SpiritInteractions;
import pryuan05.pysift.item.ModItems;
import pryuan05.pysift.particle.ModParticles;

/**
 * 靈魂晶塊：迴音傀儡頭頂慢慢凝結的晶瑩剔透的水晶（外觀同傀儡模型頭頂那顆方塊）。
 * 傀儡會把它送給歌者，玩家也能右鍵傀儡取下；泥板厚甲怪用它繁殖。
 * 靈液碰到水也會凝成靈魂晶塊（SpiritInteractions）。放在世界裡的晶塊挖得掉但不掉落（掉落表是空的），
 * 消失時（挖掉、炸掉、被取代）會放出一群自訂的靈魂粒子 soul_wisp。
 * 模型是「外深內淺的半透明青色外殼＋內縮 1 格的熾白靈魂晶核」；客戶端透過 Fabric Renderer API（SoulCrystalModel）
 * 即時讀取周圍 26 個鄰格（含斜對角），將外殼切為 4 象限 CTM 拼接圖、並以 3×3×3 子方塊體素填滿所有相連交界處與邊柱，
 * 徹底消除 2×2 與 2×2×2 中心的空洞（貼圖與靜態模型由 tools/worldgen/paint_soul_crystal.py 產生）。
 */
public final class SoulCrystal {
    public static final Block SOUL_CRYSTAL_BLOCK;
    public static final Item SOUL_CRYSTAL_BLOCK_ITEM;

    static {
        ResourceKey<Block> blockKey = ResourceKey.create(Registries.BLOCK, PySift.id("soul_crystal_block"));
        ResourceKey<Item> itemKey = ResourceKey.create(Registries.ITEM, PySift.id("soul_crystal_block"));
        SOUL_CRYSTAL_BLOCK = Registry.register(BuiltInRegistries.BLOCK, blockKey, new SoulCrystalBlock(
                BlockBehaviour.Properties.ofFullCopy(Blocks.GLASS).sound(SoundType.AMETHYST).strength(1.5f)
                        .lightLevel(state -> 12).setId(blockKey)));
        SOUL_CRYSTAL_BLOCK_ITEM = Registry.register(BuiltInRegistries.ITEM, itemKey,
                new BlockItem(SOUL_CRYSTAL_BLOCK, new Item.Properties().setId(itemKey)));
    }

    private SoulCrystal() {
    }

    /** 方塊消失時，晶塊裡的靈魂飄出來；平常外露面也會緩緩散發靈魂微光與魂體粒子。 */
    public static class SoulCrystalBlock extends TransparentBlock {
        public SoulCrystalBlock(BlockBehaviour.Properties properties) {
            super(properties);
        }

        @Override
        public void animateTick(BlockState state, Level level, BlockPos pos, RandomSource random) {
            Direction dir = Direction.getRandom(random);
            BlockPos neighborPos = pos.relative(dir);
            BlockState neighbor = level.getBlockState(neighborPos);
            if (neighbor.is(this) || neighbor.isSolidRender()) {
                return;
            }
            double x = pos.getX() + 0.5 + (dir.getStepX() == 0 ? (random.nextDouble() - 0.5) * 0.85 : dir.getStepX() * 0.56);
            double y = pos.getY() + 0.5 + (dir.getStepY() == 0 ? (random.nextDouble() - 0.5) * 0.85 : dir.getStepY() * 0.56);
            double z = pos.getZ() + 0.5 + (dir.getStepZ() == 0 ? (random.nextDouble() - 0.5) * 0.85 : dir.getStepZ() * 0.56);
            if (random.nextInt(3) == 0) {
                level.addParticle(ModParticles.SOUL_WISP, x, y, z,
                        dir.getStepX() * 0.01, 0.02 + random.nextDouble() * 0.025, dir.getStepZ() * 0.01);
            }
            if (random.nextInt(5) == 0) {
                level.addParticle(ParticleTypes.GLOW, x, y, z, 0.0, 0.01, 0.0);
            }
        }

        @Override
        protected void affectNeighborsAfterRemoval(BlockState state, ServerLevel level, BlockPos pos, boolean movedByPiston) {
            super.affectNeighborsAfterRemoval(state, level, pos, movedByPiston);
            if (!movedByPiston) {
                SpiritInteractions.releaseSouls(level, pos, 8);
                level.playSound(null, pos, SoundEvents.SOUL_ESCAPE.value(), SoundSource.BLOCKS, 1.2f, 1.0f);
            }
        }
    }

    public static void register() {
        pryuan05.pysift.item.SiftCreativeTabs.source(ModItems.BLOCKS_TAB_KEY, output -> output.accept(SOUL_CRYSTAL_BLOCK_ITEM));
        PySift.LOGGER.info("Registered soul crystal block");
    }
}
