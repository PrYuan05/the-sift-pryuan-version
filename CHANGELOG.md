# Changelog

## v2.1.0

The underground update. The Sift's underground is no longer one thin cave biome sealed off from the surface: it is the
Sift's **blood vessels**, in four layers, and there are now ways down.

### New: underground layers
Chosen by depth below the surface, in every climate. Spirit liquid wells up from the deep and life follows it: the
deeper, the more alive; the shallower, the more it rots.
- **Withered Hollows** (about 26-54 blocks down): cut off from the spirit liquid. Ash-grey strata floors, patches of
  rotten blue sculk, gloomcaps. A Mourner is seen now and then.
- **Red Zone Caves** (54-87 blocks down): the singing caves, now with red sculk patches. Tuners and Echo Golems
  wander here.
- **Resonant Vaults** (87+ blocks down): void stone floors and ceilings, charoite and soul crystal growing
  from the floor, Sentinels, Tuners and Echo Golems with their Singers.
- **Spirit Deeps** (87+ blocks down, wet regions): glowing magma-vein floors, large red sculk fields, glowshade grass.
- The Echo Den can now start in any underground layer.
- Biome borders no longer flicker: columns that sat exactly on a shared climate boundary used to alternate between two
  surface biomes with height.
- The borders between layers undulate (about +-7 blocks) instead of following the ground as flat sheets.
- The deep ores that used to belong to the surface biomes (soul crystal, patina) still generate underground.

### New: a way down
- **Sinkholes**: a funnel in the ground narrows into a shaft and opens into a small bell-shaped chamber about 34 blocks
  down, floored with red sculk and charoite. One in three has a small spirit liquid spring in the shaft wall: a thin
  stream falls to a little basin in the chamber floor, and the chamber stays dry. They never form on steep ground, near water or in the volcano.

### New: cave decoration
- **Pointed stones**: every cave type has its own dripstone-like block, made of its own stone - **Pointed Dark Slate**
  (Withered Hollows), **Pointed Crimson Vein Stone** (Red Zone Caves), **Pointed Void Stone** (Resonant Vaults) and
  **Pointed Violet Strata** (Spirit Deeps). They behave like pointed dripstone (tip, frustum, middle, base; hanging ones
  fall, standing ones hurt to land on) and grow in clusters and loose groups like a dripstone cave.
- **Stalagmites and stalactites**: tapered columns of the layer's stone that end in its pointed stone. They get taller with
  depth: 2-5 blocks in the shallows, up to 14 in the vaults.
- **Hanging vines**: three vines that hang down from cave ceilings, after the green, orange and carapace wall vines -
  orange in the Red Zone Caves, green in the Resonant Vaults, carapace in the Spirit Deeps. They can be climbed.
- **Charoite clusters hang from the ceilings** of the Resonant Vaults and Spirit Deeps.
- **Wall vines** in the Red Zone Caves (orange) and Spirit Deeps (carapace), and green vines down sinkhole walls.

### New: underground lore
- The Sift Codex has entries for **Withered Hollows**, **Resonant Vaults** and **Spirit Deeps**, a new entry on the
  underground as a whole (**The Blood Vessels**: the four layers and the sinkholes), and a rewritten Red Zone Caves entry.
- Three new **Ancient Pages** (XI-XIII), songs the Singers sing about the underground: *Cracks in the Shallows*,
  *The Hall That Remembers*, *Where the Liquid Is Born*. They are extras (not part of the Ancient Chronicle): one is
  guaranteed in every Echo Den vault, and they turn up now and then in Sift ruin chests.

### New: underground ambience
- Withered Hollows, Resonant Vaults and Spirit Deeps have their own synthesised ambience (they used to share the Red Zone
  Caves'): wind whistling through cracks and a lone dry drip in the shallows; a huge echoing hall with a clear far-off
  choir, ringing crystals and long drips in the vaults; deep liquid flow, gulps, bubbles and a rising soul in the deeps.
  Their music is made from CC0 tracks (OpenGameArt) picked for each place: dry wind and drips in the shallows, a
  cathedral choir and crystal bells in the vaults, deep rumbling cavern drones in the deeps.

### Changed: real cave shapes
Each layer now takes after a real kind of cave (the caves are the vanilla cave generator with per-layer settings that
blend across the layer borders):
- **Withered Hollows**: narrow, tall cracks like karst joint fissures (grikes), thin tunnels, no big chambers.
- **Red Zone Caves**: fat winding horizontal passages like the phreatic tubes of Mammoth Cave, with a few small rooms.
- **Resonant Vaults**: huge high halls with many rock columns, like the great chambers of Carlsbad and Son Doong.
- **Spirit Deeps**: flat, low, bedded chambers like flooded lake caves (cenotes), more of them under spirit liquid.
- Vaults and Deeps are now one smooth field instead of a humidity line, and the floor blocks blend across it.
- No more lava underground: the vanilla lava pools and the lava below y = -54 are spirit liquid or air here.
- **Bigger caves**: the Red Zone Caves and especially the Resonant Vaults and Spirit Deeps now open into much larger,
  taller halls (about twice the open space of before in the test world).
- **Fewer soul particles**: spirit liquid releases souls about four times less often (and three times less again under
  ground), soul crystals and Spirit Engines far less, the soul-deprivation effect half as much, and the biomes' floating
  soul wisps are thinned out.

### Changed: colours
- The cave floors use a low-contrast ladder of blocks (cool grey, rose grey, violet grey, violet) and every layer already
  holds some of its neighbours' blocks, so layer borders are gradients instead of lines. The bright teal strata that
  showed on cave floors and sinkhole chambers is gone.

### Changed: blocks
- **Graystone** (was Gray Strata) and **Rust Blackstone** (was Rusted Dark Cobble) are renamed, with redrawn textures for
  their whole families. Graystone also gets **Smooth Graystone** (with slab, stairs and wall, smelted from Graystone) and a
  **Graystone Pillar**. Block ids are unchanged, so existing worlds keep them.
- **Rust Blackstone rusts like copper weathers.** The Soul Caldera's crater lake breathes out a damp, soul-laden steam
  that rusts the iron-rich scoria of the cone, which is why it gets rustier towards the top. Placed within 3 blocks of
  spirit liquid it keeps rusting, one stage at a time (up to stage 3). Right-click with an axe to scrape a stage off,
  with honeycomb to seal it (sealed blocks stop rusting; an axe takes the seal off first). Mined blocks keep their rust
  and seal. The rustiest unsealed blocks grind into 4 iron nuggets in a Soul Grinder. The Sift Codex explains it.
- **Teal Strata** and its building set (bricks, chiseled bricks, slabs, stairs, walls) are removed: nothing in the world
  used them. The teal-capped blocks that share its look stay.
- The creative tabs show one Pointed Stone and one Hanging Vine of each kind instead of every shape, and Violet Strata and
  Crimson Strata moved to the main block tab. Building and natural blocks that the world never generates stay in our
  own tabs and are no longer added to vanilla's tabs.

### Notes
- No new creatures: the existing ones are redistributed across the layers.

## v2.0.0

The soul redstone update. The Sift now gives you a reason to come back with something: a better redstone. A **soul
signal** runs on vanilla redstone rules, joins vanilla circuits both ways, and is the only thing that runs the new
soul machines.

### New: soul redstone
- **Soul signal**: a redstone signal (0-15) that carries soul pressure (SP). It is 15 beside its source and drops one
  level every 2 blocks, so it reaches about 30 blocks. A machine runs at strength / 15 and loads the circuit by the
  same share.
- **Soul Conduit** (redstone, soul essence and 2 patina ingots make 6): the wire. It joins on all six sides and runs
  through rock.
  - To vanilla parts it is a signal source: it lights lamps and feeds dust, repeaters and comparators.
  - A lever, repeater, comparator, torch or redstone block against it sends a vanilla signal down the wire. That
    signal lights lamps but runs no machine. Redstone dust is not an input.
  - It is red with a soul signal, dead blue with only a vanilla one, grey when off.
  - **Connectors**: a collar where it plugs into a vanilla part, a bend down to floor-level parts (dust, rails,
    repeaters), and a thin tendril to small parts such as levers, buttons and torches.
  - **Covers**: right-click it with a full block to wrap it in that block; an empty hand takes the cover off. A
    wrapped conduit gives off no light.
- **Sources**
  - **Spirit Engine**: strength 15, 256 SP. Burns a spirit liquid bucket (160 s), soul essence (40 s) or soul sand /
    soul soil (10 s), or spirit liquid piped in by a pump.
  - **A Singer on the line**: a Singer within 3 blocks of a conduit stops and sings a set (the new *Song of the
    Sieve* between three older tunes, about two and a half minutes). While it sings the conduit is a source of
    strength 15, 64 SP. It rests half a minute between sets. A Mourner's song feeds a signal with no soul.
  - **Sculk Catalyst** against a conduit: a creature dying nearby gives strength 15 for 10 seconds (32 SP).
- **Circuit parts**
  - **Soul Repeater**: brings the signal back to 15, one way, costs 16 SP.
  - **Soul Filter**: lets through soul signals only, or plain signals only. Right-click to switch.
  - **Soul Note Block**: the eight notes of the Eight-Song Ritual. A Singer's voice on a soul signal, a dull knock
    on a plain one. Right-click to change the note.
  - **Soul Gauge**: sits in the conduit line and shows the signal as n/15 and the load; comparators read the load.
  - **Charoite Beam Emitter, Prism and Receiver**: the wireless link. A violet beam carries the signal up to 32
    blocks at no cost, prisms turn it, glass and plants let it through, and it burns creatures that stand in it.
- **Control and overload**
  - A vanilla redstone signal **pauses a machine** and **switches an engine off**.
  - When the machines ask for more than the sources give, the circuit is **overloaded**: the signal drops to zero
    and the machines shake. After 5 seconds, creatures within 6 blocks of its machines lose their souls.
  - A **Sculk Shrieker** against a conduit shrieks while the circuit is overloaded. It calls no Warden.

### New: soul machines
- **Soul Grinder**: ores ×2, cobblestone → gravel → sand, bones → bone meal, sometimes soul essence.
- **Soul Sifter** (the story's "sift the rot back to red"): while it runs it slowly turns rotten blue sculk within 8
  blocks back into red sculk (advancement **Sifted Back to Red**). It also sifts what lies on the sieve: sculk → red
  sculk, sculk vein → red sculk vein, gravel → flint, sand → clay, soul sand → soul soil.
- **Soul Drill**: bores out the block in front of it and drops what an iron pickaxe would. Harder blocks take longer;
  bedrock and obsidian-like blocks resist it. It hurts whatever stands in front of it.
- **Soul Fan**: blows creatures and items up to 8 blocks. A stream that passes through **soul fire** haunts the items
  behind it: sand → soul sand, dirt → soul soil, torches, lanterns and campfires turn into their soul versions, sculk
  veins turn red.
- **Resonance array**: a running **Resonance Core** with up to eight **Resonance Pedestals** 3 blocks away. A catalyst
  on the core and ingredients on the pedestals become, for example, 2 echo shards, 4 charoite or reinforced
  deepslate. A running core also makes grinders and sifters within 8 blocks work 50% faster.
- **Spirit Pump** and **Spirit Pipes**: the pump drinks the spirit liquid source in front of its intake (a bucket
  every 2 s at full strength) and pipes it to Spirit Engines, so one pool keeps a power plant running.
  - Placed by hand, the intake turns to face the spirit liquid next to it.
  - Every face but the intake takes a conduit and a pipe.
  - A pipe left open at one end **leaks**: spirit liquid spills out and the dirt or sand below turns into soul soil.
- **Siftite Gear** (4 siftite ingots + soul essence → 2) is the moving part of every machine. Patina is used for
  casings, conduits, pipes and pumps. Every recipe unlocks in the recipe book once you carry one of its ingredients.
- **Everything moves and sounds**: flywheels spin, pistons pump, the millstone turns with the item lying on it, the
  sieve shakes. The engine chugs, the grinder grates, the sieve rattles, and an overload groans.
- **Look**: chunky casings in the sculk family's shapes (claw corners, ribs, glowing pores) with hand-painted
  verdigris bronze, deepslate plates and solid siftite gears. Every texture has LabPBR normal and specular maps for
  Iris shader packs. The Spirit Engine and Soul Grinder screens have their own painted backgrounds.

### New: the Echo Den powerhouse
- A new room in the Echo Den, as rare as the vault: a soul redstone circuit that is still running. An engine fed by
  its own pump, a charoite beam across the room, a sifter, a grinder, a repeater, a filter and two soul note blocks,
  with a Singer standing by the wire.

### New: story
- Sift Codex: the Soul Power chapter is rewritten around the soul signal. The signal is song; living red sculk
  carries it. Vanilla redstone is a signal with no soul.
- A tenth Ancient Page, *The Wires That Do Not Sing*, can be found in Ancient City chests. It explains the redstone
  rooms under the Ancient Cities.

### Optional: the mechanical layer
- **Soul Shafts, Cogwheels, Large Cogwheels, Gearbox, Clutch, Gearshift and Hand Crank** are not part of the base
  mod. Set `kinetic_addon=on` in `config/pysift.properties` to register them as a stand-alone rotation layer; machines
  then take either a soul signal or a shaft.
- Create: `docs/CREATE_ADDON.md` describes what The Sift will add on top of Create (the engine as a stress source,
  wireless rotation, resonance speed-up). Not implemented: Create has no release for this Minecraft version.

### Technical
- **Shapes follow the models**: every block with a model of its own has an outline, collision and occlusion that
  match what is drawn (`tools/models/build_block_shapes.py` → `assets/pysift/block_shapes.json`, `ModelShapeMixin`).
- **Automatic connections**: spirit pipes and every Sift wall, fence, glass pane and stair detect their neighbours
  however they are placed - /setblock, /fill, structures, WorldEdit or Axiom (`block/AutoConnect`).
- Resources: `tools/progression/build_soul_power.py`. Checks on the test server:
  `tools/progression/test_soul_redstone.py` (base mod) and `test_soul_power.py` (mechanical layer).

### Worlds from development builds after v1.0.4
- Soul Wave Emitters / Receivers and Soul Vein Nodes no longer exist; placed ones disappear. Soul-veined stone stays
  as a building block.
- Shafts, cogwheels and the other mechanical blocks disappear unless `kinetic_addon=on` is set.
- Spirit Pumps placed before this version keep their old facing; break and place them again.

## v1.0.4

### New: the Singers' own voices
- Singers and Mourners have their own synthesised voices (no vanilla or third-party recordings): a shouted, organ-like
  choir for the Singer, the same voice starved, flat and sobbing for the Mourner.
- Every interaction has its own line and a matching face (mouth and ears): greeting after emerging, beckoning, answering
  the goat horn, sweeping, summoning, gasping when the ritual goes wrong, cheering, giggling with the little golem,
  thanking a golem, whimpering at a Warden, sighing while starving, hollowing, wailing, being soothed in spirit liquid or
  by the censer, falling quiet at the Mourning Horn, and being reborn. The ritual songs are sung in this voice too.
- Willow Grove has a new synthesised ambience: wind in the willows, a distant choir, crystal chimes and drips.
- Sounds are generated by `tools/audio/build_sounds.py`; expressions by `tools/models/singer_faces.py`.

### New: every creature has its own voice, and boss fights have music
- All the remaining creatures got their own sounds, made from free Pixabay recordings that are cut, pitch-shifted,
  filtered and layered with synthesis (sources in `assets/pysift/sounds/CREDITS.md`): Pollinator, Roamroot, Bloombud,
  Sentinel, Stalker, Hunter, Trapper, Dartback, Prickle, Nester, Seedling, Sprout, Scavenger, Hurler, Wobble, Lootkin,
  Monarch and Sculk Monstrosity. Tuner, Fusefly, Harmonizer, Echo Golem, Nuzzle and Slabber got theirs earlier.
- Every skill has its own sound, as do the other things a creature does: the swarm turning on you, the Stalker
  fading into the dark and its backstab, the Dartback's shell blocking a hit, the Scavenger's bleeding bite, the
  Wobble bursting, the Nester's dying cry, the Lootkin running off jingling, the Monarch's echo, the Sculk
  Monstrosity's second phase and the Sentinel breaking a shield.
- The six remaining biomes have synthesised ambience (wind, drips, distant choirs, chimes, lava bubbles, soul whooshes).
- **Boss music**: the Harmonizer (an epic choir), the Monarch (a heroic orchestral march) and the Sculk Monstrosity
  (dark epic orchestra) each have their own fight music, real orchestral tracks from Pixabay Music. It starts when you come within 48 blocks of the boss and
  stops as soon as it dies.
- `tools/audio/verify_sounds.py` checks that every sound is registered, has its files and subtitles, and that every
  creature skill has a sound.

### New: the Echo Den choir, cradles and guards
- The Echo Den's hub has a **Singer choir** on its stage. While someone listens, the lead Singer sings the eight notes the
  right way round about once a minute and the choir joins in.
- **Echo Cradle** (amethyst-like crystal in the grottoes): Singers' song builds resonance in it until a new Echo Golem
  is born; feeding it an echo shard helps.
- **Den guards**: Sift Wardens at the doors and the vault. Hit a Singer or golem, open the chests, or break crystals,
  cradles or note blocks nearby and they wake and chase you. The choir's song or a Mourning Horn calms them; an awake
  guard will not take an echo shard.
- **Ancient Page IX** ("The Choir Below") is always in the Echo Den vault; the Ancient Chronicle still binds pages I-VIII.

### New: the story's tools and its ending (story act 7 and finale)
- **Sift Warden** is now a real companion: it hears monsters through walls and makes them glow, never hunts on its own
  or investigates sounds, and fights only a monster that hits you or that you hit (15 melee damage, sonic boom halved). One echo shard tames
  it; following, it stays within a few blocks and teleports to you when you are far away; right-click it to make it sit
  and wait (new sitting pose), again to call it. It keeps wild Wardens
  within 24 blocks calm, and turns the blue sculk it walks over red again. Feed it sculk to heal it.
- **Mourning Horn** (goat horn + Octave and Kin sherds + echo shard): plays the eight notes backwards; Wardens within
  24 blocks calm down for 30 s and Mourners stop weeping. 1 minute cooldown, 32 uses.
- **Octave Pottery Sherd**: use it to hear the eight jukeboxes left to right, with the disc each one wants.
- **Rift Seal** (Gate sherd + soul crystal blocks + echo shards): use it on a portal in The Sift to close the rift; the
  rot within 12 blocks stops and heals, even before the Sculk Monstrosity is defeated.
- **Lullaby Censer** (soul lantern + Singer sherd + soul crystal block + spirit liquid bucket): Singers within 16 blocks
  never hollow and Mourners within 8 heal in about a minute.
- **Sift Heart**: drop the Sculk Monstrosity's heart in spirit liquid to purify it; use it on a Warden or a Mourner to
  cure it at once.
- **Ancient Chronicle**: the eight ancient pages bound into one book.
- **Finale - They Went Home**: once the rot is stilled, bring a Singer and a Sift Warden to an Ancient City's
  reinforced door and blow the Mourning Horn. The Singer sings the right octave, both go home, and the city's sculk
  turns red. Next time you enter The Sift they are waiting nearby.
- New advancements: Stitched Shut, The Ancient Chronicle, They Went Home. New codex entries for all of the above.

### New: kin, hollowing and homecoming (story acts 4-6)
- **Singers recognise Wardens.** Bring a Singer within 24 blocks of a Warden: it trembles, then sings the eight notes
  backwards. The Warden calms down for 30 seconds - no anger, no targets, slowed.
- **Mourner**, a new neutral creature: a Singer that starved in the Overworld, bald and blue with rot. It wanders the
  Deep Dark (rare), weeps the backwards song when you come close and brings Darkness. It never attacks.
- **Hollowing:** a Singer that spends about five minutes in the Overworld without a Soul Crystal Block or spirit liquid
  within six blocks becomes a Mourner. Soak a Mourner in spirit liquid for ten seconds and it is a Singer again.
- **Sift Warden:** soak a Warden in spirit liquid for 15 seconds (or keep it in The Sift for 30) and its red fur grows
  back. It never gets angry, never spreads Darkness and never digs away. Feed it an echo shard to make it follow you,
  another to make it wait.
- Starved creatures (Wardens and Mourners) drink spirit liquid instead of being hurt by it (`#pysift:soul_starved`);
  everything else, healthy Singers included, takes in too many souls and is hurt. A freshly cured creature has
  10 seconds to climb out.
- **The rot spreads and can be stopped.** Red sculk within 10 blocks of a rift slowly rots blue. Defeating the Sculk
  Monstrosity stops the rot in that world, and the sculk around the rifts slowly turns red again.
  Opening a portal on the Sift side (a Soul Crystal frame, or the portal you arrive through) grows the same ring of
  rot around it. Healing sculk gives off red sparks.
  Test command: `/pysift_rot stilled <true|false>`.
- **Four ancient pottery sherds** (Gate, Singer, Kin, Octave) in Ancient City and Sift ruin chests; they work in
  decorated pots like vanilla sherds. The Octave sherd's eight bars spell the right disc order.
- New story advancements: Lullaby for the Deep, Homeward Song, Bring It Home, The Rot Recedes.
- Sift Codex: new entries Kin, Hollowing, Homecoming, The Rot Spreads, Pottery Sherds, and bestiary pages for the
  Mourner and the Sift Warden.

### New: aurum, tools and golden foods
- Aurum ore (Lullaby Hills river beds) now drops **Raw Aurum**, more the richer the ore: richness 0 drops 1-2, solid
  ore (richness 4) 4-7; Fortune applies, Silk Touch keeps the ore with its richness.
- Smelt or blast raw aurum (or the ore) into an **Aurum Ingot**; 9 **Aurum Nuggets** make an ingot.
- **Aurum tools** (sword, pickaxe, axe, shovel, hoe): 450 durability, mining speed 10, enchantability 22, mine
  iron-tier blocks.
- **Aurum Apple** (apple + 8 ingots, always edible): Regeneration II 5 s, Absorption 2 min, Soul Ward 1 min.
- **Aurum Carrot** (carrot + 8 nuggets): very filling; Night Vision and Echo Sight 30 s.
- **Aurum Berries** (sweet berries + 4 nuggets, quick to eat): Speed and Haste 45 s.

### New: soulshale building set
- **Soulshale**, a deep teal shale in the colours of chiseled soulshale, with the whole deepslate family: polished,
  bricks, cracked bricks, tiles, cracked tiles (each with slab, stairs and wall) and **Chiseled Soulshale**.
- Craft 8 abyssal strata around a soul sand or soul soil into 8 soulshale; the rest crafts, stonecuts and smelts like
  deepslate.
- Placing Chiseled Soulshale rings one of the eight notes of the Eight-Song Ritual.

### New: the Sift Codex and the ancient pages (story prologue)
- **New required mod: [Modonomicon](https://modrinth.com/mod/modonomicon)** (Fabric, 2.20.0 or newer).
- The written Sift Guidebook is replaced by the **Sift Codex**, an interactive book with six maps of entries: the way in
  (ritual and arrival), the Sift (spirit liquid, red sculk, rifts, seven biomes), a **bestiary** with a rotatable model of
  every creature, the three **guardians** with their weapon recipes, crafting and gear, and the ancient pages.
- Bestiary and guardian pages start as locked shadows and fill in the first time you **meet** the creature (hit it, get
  hit by it, or use something on it).
- Eight **Ancient Pages** tell what happened at the Ancient City. Pages I-IV are in about half of all Ancient City
  chests, V-VII in Sift ruins (always one in the echo den vault), and VIII is carried by the Sculk Monstrosity. Use a
  page to read it; picking it up also opens its entry in the codex. All eight unlock "The Whole Story".
- You get the codex the first time you enter The Sift; craft another from a book and an echo shard.
- Reinforced deepslate and echo shards have a line of lore in their tooltips.

### New: red sculk and the rot around the rifts (story act 2-3)
- **Red Sculk** and **Red Sculk Vein**: the living sculk of The Sift, crimson with glowing pink veins, in patches beside
  the spirit ponds of the Willow Grove, Violet Slate Abyss, Lullaby Hills and Crimson Strata Canyon.
- Every wild rift is ringed by rot: blue (vanilla) sculk right at the portal, blue and red mixed further out, then a
  last ring of red - the soulless overworld air leaking in and killing the sculk.

### Changed: the Eight-Song Ritual can go wrong
- Ritual discs now fit in any Resonant Jukebox; only left-to-right in rainbow order (each jukebox's faint beam shows
  its colour) plays the right melody.
- Play them out of order and the ancients' disaster repeats: the wrong note goes flat, the screen darkens, the portal
  tears open and flickers, dark sculk bursts from the ground in front of it, and the Singer sings the melody backwards
  to close it again. All eight discs are thrown out, ready for another try.
- Fixed: closing a rift portal could leave a few stray portal blocks behind, which then stopped the next portal from opening.

### New: 3D boss weapons with use animations
- The Sonic Staff, Dash Charm and Sculk Hammer are 3D models in your hand (still 2D icons in the inventory, on the
  ground and in item frames, like the spyglass).
- **Sonic Staff**: hold right-click to chant for 0.6 s - you lift the staff to the sky with your other hand reaching out,
  sparks stream into the crystal as it swells and shards orbit it - then the sonic boom fires. Letting go early breaks the spell (no cooldown).
- **Sculk Hammer**: lifted overhead with both hands while charging, pulled further back as it charges, trembling when full; sculk souls spiral up into the head, a heartbeat quickens,
  spines grow out of the head when it is ready and the core blazes at full charge.
- **Dash Charm**: you thrust the blade forward with both hands as you dash, leaving a streak of soul fire and a sweep.
- New left-click attacks: the Sonic Staff pokes straight ahead with a longer reach (4.5 blocks), the Sculk Hammer chops down diagonally with
  both hands, alternating right-to-left and left-to-right.
- The hammer's sculk tendrils are now **Sculk Maws**: a ring of fangs bursts out of the ground around a glowing soul,
  twitches, then opens wide and snaps shut as the soul explodes, and sinks back into the ground.

### Changed: arrival portals
- The arrival spot is now picked from the flattest, lowest ground within 32 blocks that is not the top of a lone mesa or
  pillar, and the portal is built right on it (it used to move 4 blocks aside and could end up floating over a drop), so arrival portals no longer perch on high terrain with tall, broken ramps.
- Foundations and ramp fill use the strata under the surface block instead of stacking surface (capped) blocks.

## v1.0.3

### New biome: Soul Caldera
- A volcanic plateau covered in souls instead of lava: cooled **Ember Basalt** fields cut by shallow rifts (at most
  about 6 blocks deep) with a thin stream of Spirit Liquid along their floor.
- **Magma Vein Slate** grades into every rift and crater: the veins grow from the rim inward, and the fully intruded
  face is the rarest.
- Round **soul volcanoes** rise in the biome's core, never at its edge: a cone of rusty scoria, ash and embers with a
  flat **crater lake** of Spirit Liquid. About 20 volcanoes in a 6000 x 6000 area.
- Sparse plants: violet and crimson tufts, soul cleavers, bone spires, ferns, puff grass, gloomcaps and short vines.
- Blurred borders with its neighbours, its own sounds, Blub variant and an arrival portal.

### New: patina and metal blocks
- **Patina Ore** (replaces Argent Ore) grows in the Soul Caldera's rift walls: weathered green near the surface,
  fresh hydrothermal breccia deeper down. It drops **Raw Patina** (fortune works); smelt it into **Patina Ingots**,
  kept for the soul power machines that are coming later.
- **Block of Patina**, **Block of Raw Patina**, **Block of Siftite** and **Block of Raw Siftite**, crafted 9 to 1
  like the vanilla metal blocks. Patina and siftite blocks also work as beacon bases.

### New: Soul Essence reshapes blocks
- Use **Soul Essence** on a block to switch it to its next variant (colour tone, pattern, facing, stair shape...),
  one essence per change; sneak + use picks which variant to change. Properties that would duplicate blocks or skip
  growth are locked, and two-block blocks (doors, beds, double chests) can't be reshaped.

### New: blocks and stones
- Stone upgrade from real-world references: the **void stone** family (bricks, tiles, polished, smooth, cracked),
  violet slate, marbles, banded mudstone, white sandstone, **Aurum Ore**, smooth ash marble and hand-painted amber
  and pale sandstone. Every stone has slabs, stairs and walls.
- **Ember Basalt** with bricks, slabs, stairs and walls; **Corrupted Vine** that climbs any face and spreads in four
  stages; a two-layer connected **Soul Crystal Block**.
- Block ids are now readable and every block keeps its assets in its own folder.

### Changed: portals
- New arrival portals for **Lullaby Hills** (crimson vein stone) and the **Soul Caldera** (ember basalt and glowing
  magma vein slate). Arrival portals can be edited in game with `/pysift_showcase portal`.
- Portal light now stays on the portal: the rays shoot out from the rim along the portal's facing instead of lying
  over the frame, and the night haze sits on the face.
- Fixed: the two end columns of portals facing east-west had no glow, and portal cells next to walls, slabs or stairs
  showed no portal texture.

### Removed
- Argent Ore (now Patina Ore), Corrupted Slate and its building set, the Soul Sift Axle (being redesigned).

### Lore
- The story of The Sift was rewritten: sculk is native, red and alive in The Sift and rots blue in the soulless
  overworld; the Warden and the Mourner are Sift creatures turned undead; the ancients put the discs in the wrong
  jukeboxes and tore the portal open.

## v1.0.1

### Changed: Crimson Strata Canyon terrain
- The canyon's mesas now grow out of the terrain itself: irregular buttes of every size with steep walls and up to three
  shelves (Y78 / Y89 / Y100), and free-standing rock pillars on the canyon floor. The old round mesas are kept but rare.
- Each shelf has its own cap (rose, teal, then the canyon cap on top), walls of ember stone mixed with crimson strata,
  and the floor is a patchwork of canyon cap, silted strata, teal cap and banded mudstone that blends block by block.

### New: the Eight-Song Ritual (replaces the old one-click portal)
- Blow a Goat Horn at an Ancient City portal frame: a **Singer** climbs out and stays in place.
- The Singer beckons until you give it an **Echo Shard**; then it calls two **Echo Golems** that climb out of the ground, carry eight
  **Resonant Jukeboxes** to the floor below the frame and set them down from left to right (all animated).
- Fill the jukeboxes with eight discs from eight places (Pigstep, Relic, Precipice, Creator, 5, Otherside, 13, Tears);
  left to right they shine red, orange, yellow, green, blue, indigo, purple, pink. When all eight play, the beams meet,
  the portal opens and the Singer waves goodbye and burrows away.
- The jukeboxes are the key: break one and the portal closes, the disc drops out.
- In The Sift: a closed **Soul Crystal** frame + an Echo Shard opens a portal back to the overworld.
- The ritual Singer stands on the exact centre of the portal, stays perfectly still while waiting, plays with a tiny
  Echo Golem when bored, and can no longer wake the Warden. New advancement "Eight Songs"; the Guidebook has a 12th page.

### New: day, night and sky
- Three phases shared with the overworld clock: a warm gold-pink **morning**, the mint **day** and a deep-blue **night**
  (use `/time set pysift:morning|pysift:day|pysift:night`).
- Night sky: seven aurora ribbons in three colour schemes; clouds almost vanish at night so stars and aurora show.

### New: portals
- Arriving in The Sift builds a decorated **arrival portal** in the biome's colours (ember stone, dark slate, silted
  strata and desert sandstone designs, built in game), randomly turned and mirrored.
- Arrival portals sit on a filled **half-circle fan of steps** in front and behind that reaches all the way to the ground
  (gentle where low, steeper over big drops), made of the local ground with matching slabs, ragged at the edge, with
  rubble at the foot. Foundations reach solid ground; trees no longer count as ground.
- You land on a safe spot in front of the portal instead of inside blocks.
- Portals glow at night: longer rays, a pink-gold haze in front and behind, light on the ground, drifting sparks.
  Rendering is much lighter, so large portals no longer lag.
- The small rift portal appears very rarely in the wild and works both ways.

### New: biomes and landmarks (after Minecraft Dungeons II)
- **Lullaby Hills**: a grand canyon of crimson vein stone walls climbing in three terraces to void-capped plateaus; on
  the canyon floor a marble road at the wall foot, bleached sandstone, and a river of Spirit Liquid lined with golden
  aurum ore. Every border between floor materials blends block by block. Echo Golems roam here.
- **Red Zone Caves**: an underground biome with crimson floors, red plants and charoite.
- **The Echo Den**: a deep underground domed singing amphitheatre of the Echo Golems, with tunnels branching to crystal
  grottoes, resonance rooms, collapsed halls and a rare vault - every one laid out differently.
- **Humbler Husks** (walk-through giant skeletons in the Amber Dunes, achievement *Carapace Explorer*), scattered
  **fossils**, and **Lullaby Hilltop shrines** on hill tops.
- Boss arenas, ruins, arrival portals and landmarks are now structure files that can be edited in game
  (`/pysift_showcase`, see `art_requests/structures_edit_guide.md`); several have been reshaped by hand.

### New: blocks, colours and dyes
- **Nine new colours**: Teal, Mint, Coral, Amber, Lavender, Crimson Rose, Soul Blue, Void and Dusk Gold, each with a dye
  and wool (with slabs and stairs), carpet, concrete (with slabs and stairs), concrete powder, terracotta, glazed
  terracotta, stained glass and panes (108 blocks), crafted like the vanilla ones; every block takes its palette from
  its hand-drawn dye. The new dyes also colour leather armour.
- Sift plants craft into dyes: the new colours from matching plants, vanilla dyes from the rest.
- **Beds, banners and cushions** in all nine new colours, crafted and re-dyed like the vanilla ones. Beds and cushions
  use cloth painted from each dye (frame and pillow stay vanilla); banners take vanilla patterns from the loom on a base
  of the new colour - placed, in the inventory, on shields and as map markers. Cushions are seats like the vanilla ones
  (drops, pick block and breaking particles in their own colour).
- **Amber and pale sandstone** families (chiseled, cut, smooth, slabs, stairs, walls); amber and pale sand now fall.
- **Spiritlogging**: any block that can hold water can hold Spirit Liquid instead (buckets, placing blocks in it).
- Covered natural surface blocks turn into the block below, like vanilla grass.
- Night-glow tufts grow in clusters in the Willow Grove.
- Crimson vein stone and void-capped crimson share one hue; crimson vein stone no longer looks like ember stone.

### New: Soul Sift Axle
- An animated machine of the Singers: its wheel turns slowly, and spins up when you put a sculk block in to sift it back
  into soul sand, soul soil and soul essence. Lore: sculk is Sift soul energy leaking through a rift; Wardens are fallen
  Singers; the Ancient City is the seal over the rift.

### New: creatures
- **Blub**: lies down when told to sit, has a bite attack, dog-like subtitles (hurts, dies, growls, whines, lies down)
  and action-bar hints; it is tamed, healed, bred and tempted with **Soul Crystal Blocks** only.

### Changes
- Creative tabs are grouped and sorted (block families together, blocks that generate in the world first).
- Monarch model lowered so it no longer floats above the ground.

## v2.1.0（繁體中文）

地底更新。隙浮的地底不再是一層和地表隔開的薄薄洞穴，而是隙浮的**血管**，分成四層，並且有了通往地底的路。

### 新增：地底分層
依離地表的深度決定，所有氣候都一樣。靈液從深處湧上來，生命跟著靈液走：越深越有生氣，越淺越腐爛。
- **枯竭窟**（地表下約 26-54 格）：和靈液隔絕。灰色地層地面、腐爛的藍幽匿、幽暗菇，偶爾遇見哀悼者。
- **紅區洞穴**（54-87 格）：歌聲洞穴，新增赤紅幽匿；調音者與迴音傀儡在這裡遊蕩。
- **共鳴穹窟**（87 格以下）：虛黑岩地面與天花板，地面長出 charoite 與靈魂晶體；哨兵、調音者、迴音傀儡與歌者。
- **靈液深淵**（87 格以下、潮濕區域）：發光的熔脈地面、大片赤紅幽匿、微光草。
- 回音窟現在可以出現在任何一層地底。
- 生態系邊界不再閃爍：剛好落在共用氣候邊界上的柱子，以前會隨高度在兩個地表生態系之間來回切換。
- 層與層的交界會起伏（約 ±7 格），不再是貼著地表的平面。
- 原本屬於地表生態域的深層礦物（靈魂晶體、銅綠礦）仍然會在地底生成。

### 新增：通往地底的路
- **天坑**：地面的漏斗口往下收成豎井，通到約 34 格深的鐘形洞室，地面鋪赤紅幽匿與 charoite。三分之一的天坑井壁上有一個小靈液泉眼，
  細細一道落進洞室地面的小水池，洞室本身保持乾燥。不會出現在陡坡、水邊與火山。

### 新增：洞穴裝飾
- **尖石**：每一種洞穴都有自己的滴水石，用自己那層的石材長成：**尖暗板岩**（枯竭窟）、**尖赤紅脈石**（紅區洞穴）、
  **尖虛空石**（共鳴穹窟）、**尖紫地層**（靈液深淵）。行為和鋒利滴水石一樣（尖端、錐台、中段、底座；懸空的會掉下來，
  摔在石筍上會加傷害），像滴水石洞一樣成叢或零星地長。
- **鐘乳石與石筍**：該層石材的錐形岩柱，尾端接上該層的尖石。越深越高：淺層 2–5 格，穹窟最高 14 格。
- **垂吊藤**：從洞穴天花板垂下來的三種藤蔓，照綠、橙隙浮藤與甲殼藤的樣子：紅區洞穴是橙色、共鳴穹窟是綠色、
  靈液深淵是甲殼藤。可以攀爬。
- 共鳴穹窟與靈液深淵的**天花板長出倒掛的 charoite 晶簇**。
- 紅區洞穴（橘）與靈液深淵（甲殼）有**貼牆藤蔓**，天坑洞壁垂著綠色藤蔓。

### 新增：地底的故事
- 《隙浮手記》新增**枯竭窟**、**共鳴穹窟**、**靈液深淵**三個條目、一個講整個地底的新條目（**隙浮的血管**：四層與天坑），
  並重寫了紅區洞穴的條目。
- 三張新的**遠古殘頁**（其十一～其十三），是歌者唱的地底之歌：〈淺處的裂縫〉、〈記得聲音的大廳〉、〈靈液出生的地方〉。
  它們是番外（不算在《遠古編年史》裡）：每個回音窟的寶庫一定有一張，隙浮遺跡的箱子偶爾也有。

### 新增：地底環境音
- 枯竭窟、共鳴穹窟、靈液深淵各有自己合成的環境音（以前共用紅區洞穴的）：淺層是風從岩縫鑽過的口哨聲與一滴乾脆的水；
  穹窟是極大的回音大廳、清楚的遠處合唱、水晶共鳴與久久不散的滴水；深淵是深處液體的流動、悶響的冒泡與升起的靈魂。
  三層的背景音樂用 CC0 曲目（OpenGameArt）依各地氣氛挑選：淺層是乾燥的風與滴水，穹窟是教堂合唱與水晶鐘聲，深淵是低沉轟鳴的洞穴底噪。

### 變更：貼近現實的洞穴形狀
每一層參考一種真實的洞穴（洞穴仍是原版洞穴生成，只是各層參數不同，層界處會平滑過渡）：
- **枯竭窟**：像喀斯特節理裂隙（grike）的窄而高的裂縫、細隧道，沒有大洞室。
- **紅區洞穴**：像猛獁洞的潛水層管狀坑道，粗而蜿蜒的水平通道，偶爾有小廳。
- **共鳴穹窟**：像卡爾斯巴德與韓松洞的巨大高廳，有很多岩柱。
- **靈液深淵**：像灌水的天坑湖洞（cenote），低而扁平、沿層面延伸的洞室，更常被靈液淹沒。
- 穹窟與深淵改用同一個平滑的場來分區（不再是濕度線），地面方塊也在交界處混色過渡。
- 地底不再有岩漿：原版的岩漿池與 y = -54 以下的岩漿，在這裡改成靈液或空氣。
- **更大的洞穴**：紅區洞穴，尤其是共鳴穹窟與靈液深淵，現在會打開成更大、更高的大廳（測試世界裡的開闊空間約是原本的兩倍）。
- **靈魂粒子變少**：靈液冒出靈魂的機率約降為四分之一（地底再少三倍），靈魂晶塊與靈魂引擎少很多，靈魂剝奪效果減半，
  各生態域飄浮的靈魂光點也變稀疏。

### 變更：顏色
- 洞穴地面改用低對比的方塊階梯（冷灰、玫瑰灰、紫灰、紫），每一層的地面都混入相鄰層的方塊，
  層界是漸層而不是一條線。洞穴地面與天坑洞室原本鮮豔的青綠地層已移除。

### 變更：方塊
- **灰石**（原灰色地層岩）與**鏽黑石**（原鏽蝕深色圓石）改名，整組方塊重新繪製材質。灰石另外新增**平滑灰石**
  （附半磚、階梯、牆，由灰石燒製）與**灰石柱**。方塊 id 沒變，舊世界裡的方塊會保留。
- **鏽黑石會像銅一樣變化。** 靈魂火山口的靈液湖冒出帶著靈魂的濕氣，讓火山錐上富含鐵的火山渣生鏽，所以越往山上越鏽。
  放在靈液 3 格內會一階一階繼續鏽（最多到第 3 階）。斧頭右鍵刮掉一階鏽，蜂巢右鍵封住（封住的不再生鏽；斧頭會先刮掉封蠟）。
  挖下來會保留鏽蝕程度與封蠟。最鏽、沒封住的鏽黑石放進靈魂研磨機會磨出 4 顆鐵粒。《隙浮手記》有說明。
- 移除**青碧地層岩**與它的建材組（磚、浮雕磚、半磚、階梯、牆）：世界生成沒有用到。外觀相近的青碧覆蓋方塊保留。
- 創造模式分頁裡，尖石與垂吊藤每種只放一個（不再列出每種形狀）；紫晶地層岩與赤紅地層岩移到主要方塊分頁。世界生成沒用到的建築與自然方塊只留在我們自己的分頁，不再放進原版分頁。

### 備註
- 沒有新增生物，現有生物依層重新分配。

## v2.0.0（繁體中文）

靈魂紅石更新。現在去隙浮有了帶東西回來的理由：更好的紅石。**靈魂訊號**照原版紅石的規則運作，和原版線路雙向相接，
也是唯一能讓新的靈魂機器運轉的東西。

### 新增：靈魂紅石
- **靈魂訊號**：帶著靈壓（SP）的紅石訊號（0～15）。訊號源旁邊是 15，每 2 格少一級，大約能傳 30 格。
  機器的速度是強度 ÷ 15，吃的負載也是同樣的比例。
- **靈魂導線**（紅石、靈魂精華加 2 個銅綠錠，做 6 個）：就是線。六個方向都能接，也能穿過岩層。
  - 對原版元件它是訊號源：能點亮紅石燈，也能餵給紅石粉、中繼器、比較器。
  - 拉桿、中繼器、比較器、紅石火把或紅石塊貼著它，原版訊號就沿著線傳。這種訊號能點亮紅石燈，但推不動機器。
    紅石粉不能當輸入。
  - 有靈魂訊號時是赤紅色，只有原版訊號時是枯死的藍色，沒有訊號時是灰色。
  - **接頭**：插在原版元件上的接環、往下彎去接地面元件（紅石粉、鐵軌、中繼器），以及伸向拉桿、按鈕、
    紅石火把等小元件的細觸鬚。
  - **包覆**：拿完整方塊對導線右鍵，導線就包成那個方塊的外觀；空手右鍵拆下來。包起來的導線不發光。
- **訊號源**
  - **靈液引擎**：強度 15、256 SP。燒靈液桶（160 秒）、靈魂精華（40 秒）或靈魂沙／靈魂土（10 秒），
    也能燒靈液泵用管子送來的靈液。
  - **線上的歌者**：歌者在導線 3 格內會停下來唱一整套歌（新的《篩網之歌》穿插三首老曲子，約兩分半鐘）。
    唱歌期間那段導線是強度 15、64 SP 的訊號源。每套歌之間休息半分鐘。哀悼者的歌只會送出沒有靈魂的訊號。
  - **幽匿催化體**貼著導線：附近有生物死亡時，供應 10 秒強度 15 的訊號（32 SP）。
- **線路元件**
  - **靈魂中繼器**：把訊號補回 15，單向，吃 16 SP。
  - **靈魂濾波器**：只讓靈魂訊號通過，或只讓原版訊號通過。右鍵切換。
  - **靈魂音符盒**：八音儀式的八個音。靈魂訊號時是歌者的歌聲，原版訊號時只有一聲悶響。右鍵換音。
  - **靈壓計**：串在導線中間，以 n/15 顯示訊號並顯示負載；比較器讀得到負載。
  - **紫龍晶光束發射器、稜鏡、接收器**：無線連結。紫色光束把訊號送到最遠 32 格外，不損耗；稜鏡讓它轉向，
    玻璃與花草擋不住它，站在光束裡的生物會被灼傷。
- **控制與過載**
  - 原版紅石訊號會**暫停機器**、**關閉引擎**。
  - 機器要的靈壓超過訊號源給得出的量，就是**過載**：訊號歸零，機器抖動。過載 5 秒後，機器 6 格內的生物會被奪走靈魂。
  - **幽匿尖嘯體**貼著導線時，迴路過載就尖叫示警，不會召喚監守者。

### 新增：靈魂機器
- **靈魂研磨機**：礦石變兩倍、鵝卵石 → 礫石 → 沙、骨頭 → 骨粉，偶爾多出靈魂精華。
- **靈魂淨化篩**（故事裡的「把腐爛篩回赤紅」）：運轉時會慢慢把 8 格內腐爛的藍色幽匿變回赤紅幽匿（成就「篩回赤紅」）。
  篩網上的東西也會被篩：幽匿 → 赤紅幽匿、幽匿脈 → 赤紅幽匿脈、礫石 → 燧石、沙 → 黏土球、靈魂沙 → 靈魂土。
- **靈魂鑽頭**：鑽掉正前方的方塊，掉落物和用鐵鎬挖的一樣。越硬的方塊鑽越久，基岩與黑曜石這類方塊鑽不動。
  站在鑽頭前的東西會被鑽傷。
- **靈魂風扇**：把生物和掉落物吹走，最遠 8 格。氣流穿過**靈魂火**時，後面的掉落物會被靈魂薰染：沙 → 靈魂沙、
  泥土 → 靈魂土，火把、燈籠、營火變成靈魂版本，幽匿脈變紅。
- **共鳴靈陣**：運轉中的**共鳴核心**，周圍 3 格外最多八個**共鳴台座**。核心放觸媒、台座放材料，就能做出
  2 個迴音碎片、4 個紫龍晶或強化深板岩等成品。運轉中的核心也讓 8 格內的研磨機與淨化篩快 50%。
- **靈液泵**與**靈液管**：泵吸走吸口正前方的靈液源頭（滿強度時每 2 秒一桶），用管子送給靈液引擎，
  一池靈液就能讓整座發電站一直運轉。
  - 手動放下時，吸口會自動對著旁邊的靈液。
  - 除了吸口以外的每一面，都能接導線和靈液管。
  - 只接一頭、另一頭空著的管子會**漏**：靈液漏出來，下面的泥土或沙子變成靈魂土。
- **隙浮金齒輪**（4 隙浮金錠＋靈魂精華 → 2 個）是所有機器會動的零件。銅綠用在機殼、導線、管線與泵。
  拿到任何一種材料，配方就會出現在配方書裡。
- **全部會動、會響**：飛輪轉、活塞上下，石磨帶著正在磨的東西一起轉，篩網搖晃。引擎噗噗響、研磨機磨石頭、
  篩網沙沙響，過載時會呻吟。
- **外觀**：大塊的機殼借用幽匿家族的造型（爪形轉角、骨肋、發光的孔），配上手繪的銅綠青銅、深板岩面板與隙浮金齒輪。
  每張貼圖都附 LabPBR 法線與高光貼圖，可搭配 Iris 光影。靈液引擎與研磨機的介面有自己畫的底圖。

### 新增：回音窟的動力室
- 回音窟的新房間，和寶庫一樣稀有：一組還在運轉的靈魂紅石線路。引擎靠自己的泵供應靈液，紫龍晶光束橫過房間，
  還有淨化篩、研磨機、中繼器、濾波器和兩個靈魂音符盒，線旁邊站著一隻歌者。

### 新增：故事
- 隙浮手記：「靈魂動力」章依靈魂訊號改寫。訊號就是歌聲，由活的赤紅幽匿傳遞；原版紅石是沒有靈魂的訊號。
- 第十張遠古殘頁〈不會唱歌的線〉，在遠古城市的箱子裡找得到。它解釋了遠古城市地下的紅石室。

### 選用：機械層
- **靈魂傳動軸、齒輪、大齒輪、齒輪箱、離合器、換向器、手搖曲柄**不屬於基本內容。在 `config/pysift.properties`
  設定 `kinetic_addon=on`，它們才會註冊成獨立的轉動層；這時機器吃靈魂訊號或傳動軸都可以。
- Create：`docs/CREATE_ADDON.md` 寫了隙浮要在 Create 上疊加的能力（引擎當應力來源、無線傳動、共鳴加速）。
  尚未實作，因為 Create 還沒有這個 Minecraft 版本。

### 技術
- **方塊外框跟著模型**：所有有自己模型的方塊，外框、碰撞與遮光都和看到的模型一致
  （`tools/models/build_block_shapes.py` → `assets/pysift/block_shapes.json`、`ModelShapeMixin`）。
- **自動偵測連接**：靈液管與所有隙浮的牆、柵欄、玻璃片、階梯，不管是怎麼放的（/setblock、/fill、結構、WorldEdit、Axiom）
  都會自己接起來（`block/AutoConnect`）。
- 資源：`tools/progression/build_soul_power.py`。測試伺服器上的檢查：`tools/progression/test_soul_redstone.py`（基本內容）
  與 `test_soul_power.py`（機械層）。

### 從 v1.0.4 之後的開發版升級的世界
- 靈魂振波發送器／接收器與靈脈節點已經不存在，放下的會消失。靈脈石保留成建築方塊。
- 傳動軸、齒輪等機械方塊，沒有設定 `kinetic_addon=on` 就會消失。
- 這一版之前放下的靈液泵維持原本的方向，請拆掉重放。

## v1.0.4（繁體中文）

### 新增：歌者自己的聲音
- 歌者與哀悼者有自己合成的聲音（沒有用原版或第三方錄音）：歌者是吶喊式、帶風琴感的齊唱；哀悼者是同一副嗓子餓壞了，走音、帶抽泣。
- 每個互動都有專屬的一句和對應的表情（嘴巴與耳朵）：爬出地面打招呼、招手、回應山羊角、以歌聲清掃、召喚、儀式走調倒抽一口氣、歡呼、
  抱小傀儡咯咯笑、向傀儡道謝、看到監守者發抖嗚咽、快要屍化的嘆息、屍化、哀號、泡靈液或聽香爐被安慰、被哀悼號角安撫、重生。儀式的歌也改用這副嗓子唱。
- 柳絮林地有新的合成環境音：柳間的風、遠處的合唱、水晶叮噹與滴落聲。

### 新增：每隻生物都有自己的聲音，Boss 戰有配樂
- 其餘的生物都有自己的聲音了，用 Pixabay 的免費錄音裁切、變調、濾波，再疊上合成音色做成（來源見 `assets/pysift/sounds/CREDITS.md`）：
  授粉者、漫遊根、盛開花苞、哨兵、追蹤者、獵人、陷阱師、飛鏢背、刺球、築巢者、幼苗、萌芽、清道夫、投擲者、搖晃怪、掠奪精、君王、幽匿巨怪。
  調音器、引信蠅、調和者、迴音傀儡、蹭蹭怪、泥板獸之前已經做好。
- 每個技能都有專屬的聲音，其他動作也有：蟲群被激怒、追蹤者隱入黑暗與背刺、飛鏢背用背甲擋下攻擊、清道夫咬出血、搖晃怪炸開、
  築巢者死前的爆鳴、掠奪精叮叮噹噹地逃跑、君王分出鏡像、幽匿巨怪進入第二階段、哨兵劈碎盾牌。
- 其餘 6 個生態域也換成合成的環境音（風聲、滴水、遠處的合唱、水晶叮噹、岩漿冒泡、靈魂呼嘯）。
- **Boss 戰配樂**：調和者（史詩合唱）、君王（英雄管弦進行曲）、幽匿巨怪（暗黑史詩管弦）各有自己的戰鬥曲，用的是 Pixabay Music 的真實管弦配樂。
  走到 Boss 48 格內就開始播，Boss 死掉就立刻停。
- `tools/audio/verify_sounds.py` 會檢查每個聲音都有註冊、有音檔與字幕，以及每個生物技能都有聲音。

### 新增：魂頁岩建材
- **魂頁岩**：深青色的頁岩，用雕紋魂頁岩的配色做出原版深板岩的整組建材：磨製、磚、裂紋磚、磚瓦、裂紋磚瓦（都有半磚、階梯、牆）與**雕紋魂頁岩**。
- 8 個深淵地層圍住 1 個靈魂沙或靈魂土，合成 8 個魂頁岩；其他合成、切石與燒製都和深板岩一樣。
- 放下雕紋魂頁岩時，會響起八音儀式 8 個音的其中一個。

### 新增：隙浮手記與遠古殘頁（故事序幕）
- **新的必要前置模組：[Modonomicon](https://modrinth.com/mod/modonomicon)**（Fabric 版，2.20.0 以上）。
- 原本的成書《隙浮指南書》改成互動式的**《隙浮手記》**，共六張條目地圖：啟程（儀式與抵達）、隙浮（靈液、赤紅幽匿、裂隙、七個生態域）、
  每種生物都有可旋轉模型的**生物圖鑑**、三位**守護者**與牠們的武器配方、器物與裝備，以及遠古殘頁。
- 生物圖鑑與守護者的頁面一開始只是上鎖的影子，第一次**遇到**那種生物（打牠、被牠打，或對牠用東西）就會補上。
- 8 張**遠古殘頁**講述遠古城市當年發生的事：其一～其四在約一半的遠古城市箱子裡，其五～其七在隙浮遺跡（迴音巢穴的寶庫一定有一張），
  其八在幽匿巨怪身上。手持殘頁右鍵可以直接閱讀，撿起來時手記裡對應的條目也會打開；集滿 8 張會解鎖「完整的故事」。
- 第一次進入隙浮時會獲得手記；也可以用書＋迴音碎片合成。
- 強化深板岩與迴音碎片的說明欄多了一行世界觀文字。

### 新增：赤紅幽匿與裂隙門周圍的腐爛（故事第二、三幕）
- **赤紅幽匿**與**赤紅幽匿脈絡**：隙浮原生、活著的幽匿，赤紅色帶著發光的粉紅脈絡，成片長在柳絮林地、紫晶深板岩區、搖籃曲山丘和赤紅沉積峽谷的靈液池邊。
- 每道野外裂隙門周圍都有一圈腐爛帶：門邊是原版的藍色幽匿，往外藍紅交錯，最外圈還是紅色。這是主世界沒有靈魂的空氣倒灌進來，把幽匿害死了。

### 修改：八音儀式可能出錯
- 儀式唱片現在可以放進任何一個共鳴唱片盒；只有由左到右照彩虹順序放（每個唱片盒淡淡的光柱會顯示顏色），才奏得出正確的旋律。
- 順序放錯就會重演遠古人的災難：放錯的那一格走調、畫面一暗、門被撕開並閃爍、深色幽匿從門前的地面爆開，歌者把旋律倒過來唱，把門闔上。8 張唱片全部彈出來，可以重新再試。
- 修正：裂隙門關閉時可能留下幾格傳送門殘塊，導致下一次開不了門。

### 新增：3D 的 Boss 武器與使用動畫
- 音波法杖、衝刺護符、重錘拿在手上是 3D 模型（物品欄、地上和展示框裡維持 2D 圖示，跟望遠鏡一樣）。
- **音波法杖**：按住右鍵詠唱 0.6 秒，把法杖舉向天空、另一隻手往前伸，火花往晶體匯聚、晶體變大，碎晶繞著它轉，接著才放出音爆；中途放開會中斷（沒有冷卻）。
- **重錘**：蓄力時雙手把錘子舉過頭頂、越蓄越往後拉，蓄滿後全身發抖，幽匿的靈魂盤旋著被吸進錘頭，心跳越來越急；蓄到可以砸時錘頭長出尖刺，蓄滿時核心大亮。
- **衝刺護符**：衝刺時雙手握著羽刃往前刺，沿路留下一道靈魂火和一道劃痕。
- 新的左鍵攻擊：音波法杖改成往前戳刺，攻擊距離比較遠（4.5 格），重錘雙手斜劈，右上劈到左下、左上劈到右下輪流交替。
- 重錘的幽匿藤蔓改成**幽匿咬刺**：一圈尖牙圍著發光的靈魂從地面竄出、抽動，接著張大口猛然咬合、靈魂炸開，再縮回地底。

### 修改：到達門
- 抵達位置改成在周圍 32 格內挑最平坦、偏低、又不是孤立台地或石柱頂端的地面，門直接蓋在那裡（以前會往旁邊挪 4 格，可能懸在落差上方），到達門不會再蓋在高處、拖出又高又斷斷續續的坡道。
- 地基和坡道下方的填充改用地表方塊底下的地層岩，不再一直往下疊帶頂蓋的地表方塊。

## v1.0.3（繁體中文）

### 新生態域：靈魂火山高原
- 噴發的不是岩漿而是靈魂的火山高原：冷卻的**餘燼玄武岩**熔岩原被淺淺的裂谷切開（最深約 6 格），谷底中線有一條靈液細流。
- 裂谷與火山口都有**熔脈板岩**的漸變：由外往內脈越來越多，完全被侵入的那一種最少。
- 生態域核心會長出圓形的**靈魂火山**，不會出現在生態域邊緣：火山渣、灰燼與餘燼組成的錐體，頂上是湖面平整的靈液**火山口湖**。6000 × 6000 格內約 20 座。
- 稀疏的植物：紫色與赤紅草叢、靈魂劈葉植物、骨刺、捲蕨、蓬鬆草、陰菇與短垂藤。
- 和相鄰生態域之間的邊界會互相交錯，有自己的音效、布魯布變種與到達門。

### 新增：銅綠與金屬方塊
- **銅綠礦**（取代銀白礦）生成在靈魂火山高原的裂谷壁：靠近地表是風化的綠色，深處是新鮮的熱液角礫岩。挖掘會掉落**粗銅綠**（可用時運），熔煉成**銅綠錠**，留給之後的靈魂動力機器使用。
- **銅綠錠塊**、**粗銅綠塊**、**隙浮金錠塊**、**粗隙浮金塊**，像原版金屬方塊一樣 9 個合成 1 個。銅綠錠塊與隙浮金錠塊也能當信標底座。

### 新增：靈魂精華可以改變方塊型態
- 拿**靈魂精華**對方塊右鍵，換成下一種型態（色調、紋路、朝向、樓梯形狀…），每次消耗 1 個；潛行＋右鍵選擇要換哪一種型態。會複製方塊或跳過成長的型態不能改，門、床、大箱子這類兩格的方塊也不能改。

### 新增：方塊與石材
- 依現實參考升級石材：**虛黑岩**家族（石磚、磚瓦、磨製、平滑、裂紋）、紫晶板岩、大理石、條紋泥岩、白砂岩、**金岩礦**、平滑灰大理石，以及手繪的琥珀與淺沙砂岩。每種石材都有半磚、階梯和牆。
- **餘燼玄武岩**與它的石磚、半磚、階梯、牆；能貼在任何一面、分四階段蔓延的**腐化藤蔓**；雙層、會互相連接的**靈魂晶塊**。
- 方塊 ID 改成看得懂的名稱，每個方塊的資源都放在自己的資料夾。

### 修改：傳送門
- 新增**搖籃曲山丘**（赤紅脈岩）與**靈魂火山高原**（餘燼玄武岩加發光的熔脈板岩）的到達門。到達門可以用 `/pysift_showcase portal` 在遊戲裡修改。
- 傳送門的光只留在門上：光束從門邊沿門面方向往外射，不再平躺在門框上；夜晚的光霧貼在門面上。
- 修正：沿東西向擺的門最兩端那一排沒有光暈；貼著牆、半磚、樓梯的傳送門格子看不到傳送門貼圖。

### 移除
- 銀白礦（改為銅綠礦）、腐化板岩與它的建材組、靈魂隙浮輪軸（重新設計中）。

### 世界觀
- 重寫隙浮的故事：幽匿是隙浮原生的生命，在隙浮是紅色、活著的，到了沒有靈魂的主世界才腐爛成藍色；監守者與哀悼者是屍化的隙浮生物；遠古人把唱片放錯了共鳴唱片盒，撕開了傳送門。

## v1.0.1（繁體中文）

篩靈界的中文名稱改為**隙浮**。

### 新增：八音開門儀式（取代原本一鍵開門）
- 在遠古城市的傳送門框架附近吹山羊角：**歌者**從地底爬出並站在原地。
- 歌者會一直招手，直到你給它**迴音碎片**：它召喚兩隻**迴音傀儡**從地底爬出，把 8 個**共鳴唱片盒**搬到框架下方的地面，由左到右放好（全程有動畫）。
- 放入 8 張來自 8 個地方的唱片（Pigstep、Relic、Precipice、Creator、5、Otherside、13、Tears），由左到右依序是紅橙黃綠藍靛紫粉的光柱；8 張都放好時光柱匯聚、傳送門開啟，歌者揮手道別後鑽回地底。
- 唱片盒就是鑰匙：打破任一個，門就關閉，唱片掉出來。
- 隙浮：用**靈魂晶塊**蓋封閉框架，拿迴音碎片右鍵，就能開出回主世界的傳送門。
- 儀式歌者精準出現在傳送門正中央，等待時完全不轉頭，無聊時會和小傀儡玩；儀式不會再引來伏守者。新成就「八音共鳴」；指南書增加第 12 頁。

### 新增：日夜與天空
- 三個時段，跟主世界共用時鐘：暖金粉色的**晨間**、薄荷色的**日間**、深藍的**夜間**（可用 `/time set pysift:morning|pysift:day|pysift:night`）。
- 夜空：七條三種配色的極光；入夜後雲淡到幾乎看不見，星星和極光更清楚。

### 新增：傳送門
- 抵達隙浮時會蓋出一座依生態域色系裝飾的**到達傳送門**（餘燼石、深色板岩、淤積地層岩與沙漠砂岩四種，在遊戲裡設計），每座隨機轉向與鏡像。
- 到達門前後是一片完全填滿的**半圓扇形階梯**，一路鋪到地面（低的地方緩、落差大的地方陡），用當地地表方塊與同色系半磚，外緣自然參差、坡腳散落碎石；地基會補到實心地面，樹不再被當成地面。
- 傳送後會站在門前的空地，不會卡在方塊裡。
- 夜晚的傳送門更明顯：光芒拉長、門前後浮出粉金光霧、地上鋪一片光、光點往外飄；渲染大幅減輕，靠近大型傳送門不再卡頓。
- 小裂隙門極少數在野外生成，可雙向傳送。

### 新增：生態域與地標（參考 Minecraft Dungeons II）
- **搖籃曲山丘**：赤紅脈石的高聳地形牆分三層階梯爬上虛黑覆蓋的台地；谷底牆腳是灰白大理石道路，再來是漂白砂岩，最低一層是金岩礦河岸圍著的靈液河與湖。谷底每條材質交界都一格一格互相滲透。迴音傀儡在這裡出沒。
- **紅區洞穴**：新的地底生態域，赤紅地面、紅色植物與紫龍晶。
- **迴音穴**：地底深處的圓頂歌唱劇場，迴音傀儡聚在這裡；隧道往外分岔到晶洞、共鳴室、坍塌大廳與稀有的寶庫，每座格局都不一樣。
- **迅從者殘骸**（琥珀沙丘裡可以走進去的巨大骨架，成就「甲殼探險家」）、散落的**小化石**、山頂的**搖籃曲山丘神殿**。
- Boss 競技場、遺跡、到達門與地標都改成可以在遊戲裡修改的結構檔（`/pysift_showcase`，見 `art_requests/structures_edit_guide.md`），其中幾座已經手工改過。

### 新增：方塊、顏色與染料
- **9 種新顏色**：青碧、薄荷、珊瑚、琥珀、薰衣草、赤紅玫瑰、靈魂藍、虛黑、暮光金。每種有染料，以及羊毛（含半磚、階梯）、地毯、混凝土（含半磚、階梯）、混凝土粉末、陶土、彩繪陶瓦、染色玻璃與玻璃片（共 108 個方塊），做法和原版一樣；每個方塊的色盤都取自手繪的染料。新染料也能染皮甲。
- 隙浮的植物可以合成染料：顏色相符的做新顏色，其他做原版染料。
- **琥珀砂岩、蒼白砂岩**整套（雕紋、切製、平滑、半磚、階梯、牆）；琥珀沙與蒼白沙會像原版沙一樣掉落。
- **含靈液**：所有能含水的方塊都能改成含靈液（桶子倒入、舀起、在靈液裡放方塊都可以）。
- 被蓋住的天然地表方塊會像原版草地一樣變成下面那層。
- 靈柳林的夜光草叢改成成叢生長。
- 赤紅脈石與虛黑覆蓋赤紅岩統一色相，赤紅脈石不再和餘燼石長得一樣。

### 新增：生物
- **布魯布**：坐下時改成趴著，新增咬擊動畫、跟原版狗一樣的字幕（受傷、死亡、低吼、嗚咽、趴下）與快捷列提示；改成只吃**靈魂晶塊**（馴服、回血、繁殖、吸引）。

### 調整
- 創造模式分頁分組排序（同一族的方塊放在一起，會在世界生成的排前面）。
- Monarch 模型下移，不再懸空。

## v1.0.0 — First release (Minecraft 26.3, Fabric)

The first public release of The Sift, an AI-powered Minecraft mod made by PrYuan05.

### Dimension
- New dimension **The Sift**, reached through a Singer-activated portal in an Ancient City.
- 4 biomes: Crimson Strata Canyon, Violet Slate Abyss, Willow Grove, Amber Dunes.
- Gently rolling terrain, cliff-edged plateaus, large round stepped mesas and Spirit Liquid ponds (no rivers or oceans).
- 4 ruins with loot: Strata Shrine, Abyss Obelisk, Willow Hut, Dune Tomb. Soul crystal geodes underground.
- Ambient particles per biome, soft pale fog, mint sky.

### Spirit Liquid & Soul Deprivation
- Spirit Liquid drains your health to a fifth; damage taken while deprived shatters the lost health.
- Soul Antidote restores it. Spirit Liquid + water → Soul Crystal.
- Deprived mobs burn with blue soul fire, take 30 % more damage and slowly lose health.

### Creatures & bosses
- 26 animated creatures with their own AI, including new Hunter, Trapper and Sculk Cube models.
- 3 bosses — Harmonizer, Monarch, Sculk Monstrosity — with enrage phases, arenas and death sequences.
- Fusefly explosions match their damage radius.
- **Blub** can be tamed with Soul Sand / Soul Soil; it fights for you and fetches dropped items into your inventory.

### Progression
- Siftite ore, Charoite clusters, Raw Siftite, Fuse Powder, Soul Essence.
- Siftite tools and armor (full set halves Spirit Liquid drain).
- Boss cores and shards; three boss weapons (Sonic Staff, Dash Charm, Sculk Hammer) with smithing-table **awakening**.
- **Sift Altar** + **Summoning Sigil** to fight a boss again (within 48 blocks of its arena; the chat tells you where the nearest arena is).
- **Sift Beacon Gem** inlaid in a chestplate: Soul Deprivation immunity within 8 blocks.
- **Soulite** — stronger than netherite: tools and armor carrying boss powers, upgraded from netherite with the Soulite Upgrade template.
- Advancement line from your first step into The Sift to Soulite.

### Helpers
- **Sift Guidebook** (11 pages), given on your first visit and craftable.
- **Soul Compass** — points to boss arenas or the nearest ruins.
- **Homeward Stone** — returns you to your overworld spawn.

### Farming & brewing
- **Soul Berry Bush** (grows beside Spirit Liquid), **Soul Berries**, **Gloomcap**, **Gloomcap Stew**.
- New potions (vanilla brewing stand): **Soul Ward** (Soul Deprivation immunity) and **Echo Sight** (enemies within 32 blocks glow).

### Blocks
- 450+ blocks, 38 building sets with stonecutter recipes, the full Soul Willow wood set, ground-tinted plants and flowers.

### Known issues
- Some item and block textures are still placeholders (see `art_requests/texture_todo.md`).

---

## v1.0.0 — 首次發布（Minecraft 26.3，Fabric）

The Sift（篩靈界）的第一個公開版本，由 PrYuan05 製作的 AI-powered Minecraft 模組。

### 維度
- 新維度**篩靈界**：在遠古城市由歌者開啟傳送門前往。
- 4 個生態域：赤紅沉積峽谷、紫晶深板岩區、柳絮林地、琥珀沙丘。
- 平緩起伏的地形、懸崖台地、大型階梯圓台與靈液池塘（沒有河流與海洋）。
- 4 種附戰利品的遺跡：地層神殿、深淵方尖碑、靈柳小屋、沙丘古墓；地底有靈魂晶洞。
- 各生態域的環境粒子、淡色薄霧、薄荷色天空。

### 靈液與靈魂剝奪
- 靈液會把血量抽到五分之一；剝奪期間受傷，被抽走的血量會碎裂。
- 靈魂解藥可以恢復；靈液碰到水會凝結成靈魂晶塊。
- 被剝奪的怪物會燃起藍色靈魂火、受到傷害 +30%，並持續流失血量。

### 生物與 Boss
- 26 種有專屬 AI 與動畫的生物（含重做的獵人、陷阱師、幽匿方塊模型）。
- 3 隻 Boss：調和者、君王、幽匿巨怪，有狂暴階段、競技場與死亡演出。
- 引信蠅的爆炸範圍與傷害範圍一致。
- **布魯布**可用靈魂沙／靈魂土馴服，會幫你打架、把掉落物叼回你的背包。

### 進度與裝備
- 篩金石礦、紫龍晶簇、粗篩金石、引信粉、靈魂精華。
- 篩金石工具與盔甲（整套時靈液抽血減半）。
- Boss 核心與碎片；三把 Boss 武器（音波法杖、衝刺護符、幽匿重錘），可在鍛造台**覺醒**。
- **篩靈祭壇**＋**召喚印記**再次挑戰 Boss（放在競技場中心 48 格內，聊天欄會提示最近的競技場在哪）。
- **篩靈信標寶石**鑲嵌胸甲：8 格內免疫靈魂剝奪。
- **靈髓**：比獄髓更強，帶有 Boss 能力的工具與盔甲，用靈髓升級模板從獄髓裝備升級。
- 從進入篩靈界到靈髓的成就線。

### 上手輔助
- **篩靈指南書**（11 頁）：第一次進入時獲得，也能合成。
- **靈魂羅盤**：指向 Boss 競技場或最近的遺跡。
- **回程符石**：傳回主世界的重生點。

### 種植與釀造
- **靈莓叢**（長在靈液旁）、**靈莓**、**幽光菇**、**幽光菇燉湯**。
- 新藥水（原版釀造台）：**靈魂守護**（免疫靈魂剝奪）、**回音視界**（32 格內敵人發光）。

### 方塊
- 450 種以上的方塊、38 組建材（含切石機配方）、完整靈魂柳木組、會依地面變色的植物與花。

### 已知問題
- 部分物品與方塊貼圖仍是臨時圖（見 `art_requests/texture_todo.md`）。
