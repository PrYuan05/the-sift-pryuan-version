# The Sift × Create: add-on spec

Status: **spec only**. Create has no Minecraft 26.x release (Fabric stops at 1.20.1, NeoForge at 1.21.1, checked
2026-11-10), so nothing here is compiled or tested against Create. The Create class names below are from Create 6
(1.21.1) and have to be checked again when a 26.x build exists.

## Principle

Soul power has two layers.

| Layer | What the player gets | Needs |
| :-- | :-- | :-- |
| **Soul redstone** (base) | Spirit engine, soul conduit, gauge, machines, wireless relays. A soul signal is a redstone signal (0-15) that carries soul pressure. No shafts, no cogwheels. | nothing |
| **Create add-on** | The same blocks gain abilities **on top of Create's own kinetics**. The Sift adds no shaft or cogwheel of its own. | Create |

The Sift's own shafts, cogwheels, gearbox, clutch, gearshift and hand crank (`soulpower/kinetic/`) are a
**stand-alone test layer**: registered only with `kinetic_addon=on` in `config/pysift.properties`. They keep the
rotation solver (`SoulNetwork`) testable until Create can be used, and are not shown to players otherwise.

`kinetic_addon` values:

| Value | The Sift's own shafts and cogwheels | Create bridge |
| :-- | :-- | :-- |
| `auto` (default) | off | on when Create is installed (once implemented) |
| `on` | on | on when Create is installed |
| `off` | off | off |

## Abilities

Each ability is one method of `compat/create/CreateBridge`. `CreateBridge.NONE` (no-op) is what runs today.

| # | Ability | Bridge method | Called from | Create side (to verify) |
| :-- | :-- | :-- | :-- | :-- |
| 1 | Spirit engine is a stress source: 64 RPM, 256 SU × strength / 15 | `driveFromEngine` | `SpiritEngineBlockEntity.serverTick` | a `GeneratingKineticBlockEntity` on the engine's flywheel side; `BlockStressValues` capacity |
| 2 | Wireless rotation: a charoite beam joins two Create networks | `linkNetworks` | `SoulCircuit.update`, where relay edges are built | `RotationPropagator`, `KineticNetwork` (merge and split) |
| 3 | Resonance: a running core speeds Create machines within 8 blocks by 50 % | `boostAround` | `ResonanceCoreBlockEntity.serverTick` | per-machine processing speed (`KineticBlockEntity.getSpeed` consumers) |
| 4 | Conversion: rotation → soul signal, soul signal → rotation | `signalFromRotation`, `driveFromEngine` | a new converter block (not built yet) | `KineticBlockEntity` speed and stress |
| 5 | Soul overload: an overstressed Create network fed by an engine triggers soul deprivation | `overstressed` | `SoulCircuit.update`, overload branch | `KineticNetwork` stress vs capacity |

Rules that carry over from soul redstone:

- A charoite beam costs a soul signal nothing. For rotation the link is lossless in speed; the cost is paid as
  stress (5 % of the transferred stress).
- A vanilla redstone signal on the engine switches it off, for Create as well.

## What is not decided

- Whether the engine should turn Create machines directly (ability 1) or only through a converter block (ability 4).
  Both are in the interface; only one should ship.
- Create recipe data (crushing siftite / patina ore, haunting sculk into red sculk). Left out on purpose: the
  recipe JSON format cannot be validated without Create.

## When Create reaches 26.x

1. Add Create as a `modCompileOnly` dependency.
2. Write `compat/create/CreateBridgeImpl` and return it from `CreateBridge.get()` when `create` is loaded.
3. Add the five call sites from the table.
4. Tests: a Create shaft line driven by a spirit engine; two networks joined by a beam; a resonance core next to a
   millstone; an overstressed network.
