package pryuan05.pysift.progression;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.Holder;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.BlockTags;
import net.minecraft.util.RandomSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.effect.MobEffectCategory;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.MobCategory;
import net.minecraft.world.entity.TamableAnimal;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.food.FoodProperties;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.alchemy.Potion;
import net.minecraft.world.item.component.Consumables;
import net.minecraft.world.item.consume_effects.ApplyStatusEffectsConsumeEffect;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.LevelReader;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.BonemealSource;
import net.minecraft.world.level.block.BonemealableBlock;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.VegetationBlock;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.block.state.properties.IntegerProperty;
import net.minecraft.world.level.material.FluidState;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;
import pryuan05.pysift.PySift;
import pryuan05.pysift.fluid.ModFluids;

/**
 * 生活（B）：作物、食物與靈魂釀造。
 * <ul>
 *   <li><b>靈莓叢</b>：種在任何實心方塊或泥土上；只有 4 格內有靈液才會長大（靈液澆灌），越熟越亮。
 *       熟了右鍵採 2～3 顆靈莓。生成在靈液池邊。</li>
 *   <li><b>幽光菇</b>：地底洞穴的小菇，會在暗處（亮度 &lt; 13）慢慢蔓延，本身發出微光。</li>
 *   <li>靈莓：可以吃（短暫的靈魂守護）；幽光菇燉湯：飽食＋回音視界。</li>
 *   <li>釀造（原版釀造台，資料驅動的 26.3 釀造配方由 build_progression.py 產生）：
 *       粗製藥水＋靈莓 → 靈魂守護藥水（免疫靈魂剝奪）；粗製藥水＋幽光菇 → 回音視界藥水（32 格內的敵人發光）。
 *       紅石延長、火藥／龍息轉換成噴濺與滯留型。</li>
 * </ul>
 */
public final class SiftFarming {
    // ===== 效果 =====
    /** 靈魂守護：期間完全不會被靈魂剝奪（SoulWard.isImmune）。 */
    public static final Holder<MobEffect> SOUL_WARD = Registry.registerForHolder(BuiltInRegistries.MOB_EFFECT,
            PySift.id("soul_ward"), new MobEffect(MobEffectCategory.BENEFICIAL, 0x7FE8E0) {
            });
    /** 回音視界：每秒讓 32 格內的敵對生物發光 1.5 秒，並在牠們頭上冒出只有自己看得到的幽匿粒子。 */
    public static final Holder<MobEffect> ECHO_SIGHT = Registry.registerForHolder(BuiltInRegistries.MOB_EFFECT,
            PySift.id("echo_sight"), new EchoSightEffect());

    // ===== 藥水 =====
    public static final Holder<Potion> SOUL_WARD_POTION = potion("soul_ward", new MobEffectInstance(SOUL_WARD, 3600));
    public static final Holder<Potion> LONG_SOUL_WARD_POTION = potion("long_soul_ward", "soul_ward", new MobEffectInstance(SOUL_WARD, 9600));
    public static final Holder<Potion> ECHO_SIGHT_POTION = potion("echo_sight", new MobEffectInstance(ECHO_SIGHT, 3600));
    public static final Holder<Potion> LONG_ECHO_SIGHT_POTION = potion("long_echo_sight", "echo_sight", new MobEffectInstance(ECHO_SIGHT, 9600));

    // ===== 作物 =====
    public static final Block SOUL_BERRY_BUSH = registerPlant("soul_berry_bush", SoulBerryBushBlock::new,
            BlockBehaviour.Properties.ofFullCopy(Blocks.SWEET_BERRY_BUSH)
                    .lightLevel(state -> state.getValue(SoulBerryBushBlock.AGE) * 3));
    public static final Item SOUL_BERRIES = ModProgression.registerItem("soul_berries", p -> new BlockItem(SOUL_BERRY_BUSH, p),
            new Item.Properties().useItemDescriptionPrefix().food(new FoodProperties(3, 0.4f, false),
                    Consumables.defaultFood().onConsume(new ApplyStatusEffectsConsumeEffect(new MobEffectInstance(SOUL_WARD, 200))).build()));
    public static final Block GLOOMCAP = ModProgression.registerBlock("gloomcap",
            p -> new GloomcapBlock(p.lightLevel(state -> 5).sound(SoundType.FUNGUS)), Blocks.BROWN_MUSHROOM);
    public static final Item GLOOMCAP_STEW = ModProgression.registerItem("gloomcap_stew", Item::new,
            new Item.Properties().stacksTo(1).usingConvertsTo(Items.BOWL).food(new FoodProperties(7, 0.6f, false),
                    Consumables.defaultFood().onConsume(new ApplyStatusEffectsConsumeEffect(new MobEffectInstance(ECHO_SIGHT, 900))).build()));

    private SiftFarming() {
    }

    private static Holder<Potion> potion(String name, MobEffectInstance effect) {
        return potion(name, name, effect);
    }

    /** baseName：藥水的語系名稱（延長版和一般版同名，像原版的 long_night_vision）。 */
    private static Holder<Potion> potion(String name, String baseName, MobEffectInstance effect) {
        return Registry.registerForHolder(BuiltInRegistries.POTION, PySift.id(name), new Potion("pysift." + baseName, effect));
    }

    private static Block registerPlant(String name, java.util.function.Function<BlockBehaviour.Properties, Block> factory,
                                       BlockBehaviour.Properties properties) {
        ResourceKey<Block> key = ResourceKey.create(Registries.BLOCK, PySift.id(name));
        return Registry.register(BuiltInRegistries.BLOCK, key, factory.apply(properties.setId(key)));
    }

    static boolean isSpirit(FluidState fluid) {
        return fluid.is(ModFluids.SPIRIT_LIQUID) || fluid.is(ModFluids.FLOWING_SPIRIT_LIQUID);
    }

    // ------------------------------------------------------------ effects
    private static final class EchoSightEffect extends MobEffect {
        private EchoSightEffect() {
            super(MobEffectCategory.BENEFICIAL, 0x29DFEB);
        }

        @Override
        public boolean shouldApplyEffectTickThisTick(int duration, int amplifier) {
            return duration % 20 == 0;
        }

        @Override
        public boolean applyEffectTick(ServerLevel level, LivingEntity entity, int amplifier) {
            for (Mob mob : level.getEntitiesOfClass(Mob.class, entity.getBoundingBox().inflate(ECHO_RADIUS), m -> isHostile(m, entity))) {
                mob.addEffect(new MobEffectInstance(MobEffects.GLOWING, 30, 0, false, false), entity);
                if (entity instanceof ServerPlayer player) {   // 只有喝藥的人看得到：敵人頭上冒出幽匿粒子
                    level.sendParticles(player, ParticleTypes.SCULK_CHARGE_POP, true, false,
                            mob.getX(), mob.getY() + mob.getBbHeight() + 0.4, mob.getZ(), 4, 0.2, 0.1, 0.2, 0.0);
                }
            }
            return true;
        }
    }

    public static final double ECHO_RADIUS = 32.0;

    /** 敵對生物：Enemy、MONSTER 類別（有些隙浮生物不是 Enemy，例如 Roamroot），或正把 viewer 當目標的生物。 */
    public static boolean isHostile(Mob mob, LivingEntity viewer) {
        return mob.isAlive() && mob != viewer && !(mob instanceof TamableAnimal pet && pet.isOwnedBy(viewer))
                && (mob instanceof Enemy || mob.getType().getCategory() == MobCategory.MONSTER || mob.getTarget() == viewer);
    }

    // ------------------------------------------------------------ soul berry bush
    public static class SoulBerryBushBlock extends VegetationBlock implements BonemealableBlock {
        public static final IntegerProperty AGE = BlockStateProperties.AGE_3;
        private static final VoxelShape SAPLING = Block.box(3.0, 0.0, 3.0, 13.0, 8.0, 13.0);
        private static final VoxelShape GROWN = Block.box(1.0, 0.0, 1.0, 15.0, 16.0, 15.0);

        public SoulBerryBushBlock(Properties properties) {
            super(properties);
            this.registerDefaultState(this.stateDefinition.any().setValue(AGE, 0));
        }

        @Override
        protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
            builder.add(AGE);
        }

        @Override
        protected boolean mayPlaceOn(BlockState state, BlockGetter level, BlockPos pos) {
            return state.is(BlockTags.DIRT) || state.isFaceSturdy(level, pos, Direction.UP);
        }

        @Override
        protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
            return state.getValue(AGE) == 0 ? SAPLING : GROWN;
        }

        @Override
        protected ItemStack getCloneItemStack(LevelReader level, BlockPos pos, BlockState state, boolean includeData) {
            return new ItemStack(SOUL_BERRIES);
        }

        @Override
        protected boolean isRandomlyTicking(BlockState state) {
            return state.getValue(AGE) < 3;
        }

        /** 靈液澆灌：周圍 4 格（同層與下一層）有靈液才會長。 */
        static boolean watered(LevelReader level, BlockPos pos) {
            for (BlockPos p : BlockPos.betweenClosed(pos.offset(-4, -1, -4), pos.offset(4, 0, 4))) {
                if (isSpirit(level.getFluidState(p))) {
                    return true;
                }
            }
            return false;
        }

        @Override
        protected void randomTick(BlockState state, ServerLevel level, BlockPos pos, RandomSource random) {
            int age = state.getValue(AGE);
            if (age < 3 && random.nextInt(4) == 0 && watered(level, pos)) {
                level.setBlock(pos, state.setValue(AGE, age + 1), Block.UPDATE_CLIENTS);
            }
        }

        @Override
        protected InteractionResult useItemOn(ItemStack stack, BlockState state, Level level, BlockPos pos, Player player,
                                              InteractionHand hand, BlockHitResult hit) {
            if (state.getValue(AGE) != 3 && stack.is(Items.BONE_MEAL)) {
                return InteractionResult.PASS;
            }
            return super.useItemOn(stack, state, level, pos, player, hand, hit);
        }

        @Override
        protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
            if (state.getValue(AGE) < 3) {
                return super.useWithoutItem(state, level, pos, player, hit);
            }
            if (level instanceof ServerLevel) {
                Block.popResource(level, pos, new ItemStack(SOUL_BERRIES, 2 + level.getRandom().nextInt(2)));
                level.playSound(null, pos, SoundEvents.SWEET_BERRY_BUSH_PICK_BERRIES, SoundSource.BLOCKS, 1.0f,
                        0.8f + level.getRandom().nextFloat() * 0.4f);
                level.setBlock(pos, state.setValue(AGE, 1), Block.UPDATE_CLIENTS);
            }
            return InteractionResult.SUCCESS;
        }

        @Override
        public boolean isValidBonemealTarget(LevelReader level, BlockPos pos, BlockState state, BonemealSource source) {
            return state.getValue(AGE) < 3;
        }

        @Override
        public boolean isBonemealSuccess(Level level, RandomSource random, BlockPos pos, BlockState state, BonemealSource source) {
            return true;
        }

        @Override
        public void performBonemeal(ServerLevel level, RandomSource random, BlockPos pos, BlockState state, BonemealSource source) {
            level.setBlock(pos, state.setValue(AGE, Math.min(3, state.getValue(AGE) + 1)), Block.UPDATE_CLIENTS);
        }
    }

    // ------------------------------------------------------------ gloomcap
    public static class GloomcapBlock extends VegetationBlock {
        private static final VoxelShape SHAPE = Block.box(5.0, 0.0, 5.0, 11.0, 7.0, 11.0);

        public GloomcapBlock(Properties properties) {
            super(properties);
        }

        @Override
        protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
            return SHAPE;
        }

        @Override
        protected boolean mayPlaceOn(BlockState state, BlockGetter level, BlockPos pos) {
            return state.isFaceSturdy(level, pos, Direction.UP);
        }

        @Override
        protected boolean canSurvive(BlockState state, LevelReader level, BlockPos pos) {
            BlockPos below = pos.below();
            return mayPlaceOn(level.getBlockState(below), level, below) && level.getRawBrightness(pos, 0) < 13;
        }

        @Override
        protected boolean isRandomlyTicking(BlockState state) {
            return true;
        }

        /** 和原版蘑菇一樣慢慢蔓延：附近（9x3x9）不到 5 朵時，往旁邊長一朵。 */
        @Override
        protected void randomTick(BlockState state, ServerLevel level, BlockPos pos, RandomSource random) {
            if (random.nextInt(25) != 0) {
                return;
            }
            int nearby = 0;
            for (BlockPos p : BlockPos.betweenClosed(pos.offset(-4, -1, -4), pos.offset(4, 1, 4))) {
                if (level.getBlockState(p).is(this) && ++nearby >= 5) {
                    return;
                }
            }
            BlockPos target = pos.offset(random.nextInt(3) - 1, random.nextInt(2) - random.nextInt(2), random.nextInt(3) - 1);
            if (level.isEmptyBlock(target) && state.canSurvive(level, target)) {
                level.setBlock(target, state, Block.UPDATE_CLIENTS);
            }
        }
    }

    static void load() {
        // 靜態欄位在 class 載入時註冊；這裡只是確保順序
    }
}
