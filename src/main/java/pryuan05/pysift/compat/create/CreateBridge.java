package pryuan05.pysift.compat.create;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;

/**
 * The seam between soul redstone and the Create mod. With Create installed The Sift does not bring its own shafts
 * and cogwheels: Create's are used, and this bridge adds what Create does not have (docs/CREATE_ADDON.md):
 * <ol>
 *   <li>the spirit engine as a Create stress source;</li>
 *   <li>wireless rotation: waves, beams and veins join two Create kinetic networks;</li>
 *   <li>resonance: a running resonance core speeds up Create machines near it;</li>
 *   <li>conversion both ways between a soul signal and rotation;</li>
 *   <li>the soul overload hazard when a Create network fed by an engine is overstressed.</li>
 * </ol>
 * This interface names no Create class, so the mod loads without Create. {@link #NONE} is what runs today:
 * Create has no Minecraft 26.x release yet, so there is nothing to compile a real implementation against.
 * When it has one, the implementation goes in this package and {@link #get()} returns it when
 * {@code FabricLoader.isModLoaded("create")}. Nothing calls these methods yet; the call sites are listed in the spec.
 */
public interface CreateBridge {
    /** No Create: every ability is off. */
    CreateBridge NONE = new CreateBridge() {
    };

    static CreateBridge get() {
        return NONE;
    }

    /** Is a real Create implementation behind this bridge? */
    default boolean present() {
        return false;
    }

    /**
     * 1. Engine as a stress source: the Create rotation speed (RPM) the engine at {@code engine} should generate
     * for the given soul signal strength (0-15), and the stress capacity (SU) it adds. Called from the engine's tick.
     */
    default void driveFromEngine(ServerLevel level, BlockPos engine, int strength) {
    }

    /**
     * 2. Wireless rotation: {@code from} and {@code to} are the two ends of a wave / beam / vein link that both touch a
     * Create kinetic block. Makes the two Create networks turn as one (same speed, shared stress), as long as the
     * link stands. Called when the soul circuit finds or loses the link.
     */
    default void linkNetworks(ServerLevel level, BlockPos from, BlockPos to, boolean linked) {
    }

    /**
     * 3. Resonance: the speed multiplier Create machines within {@code radius} of a running core should get
     * (1 = none). Called from the resonance core's tick.
     */
    default void boostAround(ServerLevel level, BlockPos core, int radius, float multiplier) {
    }

    /**
     * 4a. Rotation to soul signal: the soul signal strength (0-15) a converter at {@code pos} should emit for the
     * Create rotation arriving at it (0 when it is not turning). The stress it takes from the Create network pays
     * for the soul pressure.
     */
    default int signalFromRotation(ServerLevel level, BlockPos pos) {
        return 0;
    }

    /** 5. Is the Create network that the engine at {@code engine} feeds overstressed? Drives the soul overload hazard. */
    default boolean overstressed(ServerLevel level, BlockPos engine) {
        return false;
    }
}
