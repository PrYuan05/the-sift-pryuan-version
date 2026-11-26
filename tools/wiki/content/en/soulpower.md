=== item:spirit_engine | Spirit Engine
The power source of Soul Power: it turns souls into song.

- **Fuel**: a bucket of spirit liquid, soul essence, soul sand or soul soil. A [[pysift:spirit_pump|Spirit Pump]] can feed it spirit liquid through [[pysift:spirit_pipe|spirit pipes]]; when the fuel slot is empty it burns what the pipes bring.
- **Output**: while running it sends a **strength 15** soul signal and supplies **256 SP** (soul pressure).
- **Wiring**: [[pysift:soul_conduit|soul conduits]] connect on every side except the front.
- **Master switch**: a vanilla redstone signal touching the engine switches it off and pauses the fuel.
- Open it to see the fuel and burn time.

See [[page:soul_power|Soul Power]] for how the whole system works.

=== item:spirit_pump | Spirit Pump
Moves spirit liquid from a pool to the engine.

- Point its **intake** at a spirit liquid pool and give it a soul signal: it drinks the source in front of it into a **4000 mB** tank.
- On a kinetic network at 32 RPM it pumps one bucket every 2 s.
- Sends the liquid along [[pysift:spirit_pipe|spirit pipes]] to a [[pysift:spirit_engine|Spirit Engine]].

=== item:spirit_pipe | Spirit Pipe
Carries spirit liquid from a [[pysift:spirit_pump|Spirit Pump]] to a [[pysift:spirit_engine|Spirit Engine]], connecting to neighbouring pipes, pumps and engines on its own.

- **A pipe connected at one end only leaks**: the liquid turns the dirt or sand below into soul soil.
- 3 patina ingots make 6.

=== item:soul_conduit | Soul Conduit
A living vein of red sculk that carries the engine's song where you need it.

- Connects in **all six directions**, so it runs up walls, across gaps and through the air. It glows red while souls flow through it.
- The signal **drops one level every 2 blocks**, so it reaches about 30 blocks from the engine; use [[pysift:soul_repeater|Soul Repeaters]] to go further.
- **Redstone parts see it as a power source**: lamps light, pistons push, repeaters and comparators read it.
- **It also carries vanilla signals**: a lever, repeater, comparator, redstone torch or block of redstone touching it sends its signal along, but that signal has **no soul**: the conduit turns the dead blue of Overworld sculk and machines do not run. Redstone dust cannot feed a conduit.
- **Hiding it**: use any full block on it to wrap the conduit in that block's look; it still carries the signal and stops glowing. Use an empty hand to take the block off.
- Next to vanilla parts it grows a fitting joint: a collar for lamps, pistons and hoppers; it bends to the floor for redstone dust, rails and repeaters; a thin tendril reaches levers, buttons and torches.
- **Special sources**: a [[mob:singer|Singer]] within 3 blocks sings into it (strength 15, 64 SP, about two and a half minutes, then half a minute of rest); a sculk catalyst touching it sends a 10 s signal (32 SP) when something dies nearby; a sculk shrieker touching it screams when the circuit overloads.

=== item:soul_repeater | Soul Repeater
Placed in a conduit line, facing the way the signal should go.

- A signal entering at the back leaves the front at **strength 15** again.
- The signal never runs backwards, so it works as a one-way valve.
- Uses **16 SP** while carrying a soul signal.

=== item:soul_filter | Soul Filter
Conduits carry soul signals and vanilla redstone on the same line; the filter lets only one through. Use it to switch.

- **Red core**: soul signals only.
- **Blue core**: vanilla signals only; machines behind it will not run, but lamps and pistons still work.

=== item:soul_gauge | Soul Gauge
Reads the load on a circuit.

- Place it in a conduit line. As the load nears capacity the needle swings from green into red.
- Use it to see the signal strength and the exact SP; a comparator reads the load (0–15).
- A machine's load = its full-load value × signal strength ÷ 15. Above 100 % the circuit **overloads**: the soul signal drops to 0, and 5 s later every creature within 6 blocks gets soul deprivation.

=== item:soul_note_block | Soul Note Block
Holds the eight notes of the song that opens the door; use it to change the note.

- It sounds once when a signal arrives: with a **soul signal** it sings in a Singer's voice; with only vanilla redstone it gives a dull thud.
- Set out eight and pass the signal along with repeaters to play the door order **1 3 7 6 5 2 4 8** at home.

=== item:soul_grinder | Soul Grinder
A machine that grinds things; open it to put materials in.

- **Recipes**: ores are doubled (siftite ore → 2 raw siftite, copper ore → 6 raw copper), cobblestone → gravel → sand, bone → 6 bone meal, soul soil → soul sand, fully rusted rusted blackstone → 4 iron nuggets; sometimes a bonus soul essence.
- **Power**: **64 SP** at signal strength 15; a weaker signal grinds slower and uses less.
- A vanilla redstone signal touching it pauses it, like a locked hopper.
- Runs 50 % faster within 8 blocks of a working [[pysift:resonance_core|Resonance Core]].

=== item:soul_sifter | Soul Sifter
Ancient craft that sifts the rot back to red.

- **Cleans its surroundings**: while it runs, rotten blue sculk **within 8 blocks** slowly turns back into [[pysift:red_sculk|red sculk]].
- **Sifts items**: sculk → red sculk, gravel → flint, sand → clay balls, soul sand → soul soil.
- **Power**: **96 SP** at signal strength 15; connect the conduit on the flywheel side.
- Runs 50 % faster within 8 blocks of a working [[pysift:resonance_core|Resonance Core]].

=== item:charoite_beam_emitter | Charoite Beam Emitter
Sends a soul signal without wires.

- Fires a violet beam up to **32 blocks**; it connects when it hits the **front** of a [[pysift:charoite_beam_receiver|receiver]].
- The signal **does not weaken**, but the beam has to be aimed.
- The beam passes through glass and plants, and burns anything standing in it.
- Bend it with a [[pysift:charoite_prism|Charoite Prism]].

=== item:charoite_beam_receiver | Charoite Beam Receiver
Catches the violet beam of an [[pysift:charoite_beam_emitter|emitter]]: when the beam hits its **front**, it passes the soul signal into the conduit behind it at full strength.

=== item:charoite_prism | Charoite Prism
Turns a charoite beam. Use it to change direction, sneak + use to turn it back. Glass, charoite and amethyst make 2.

=== item:resonance_core | Resonance Core
The centre of a Resonance Array, which makes rare materials with ancient craft.

- **Layout**: up to eight [[pysift:resonance_pedestal|Resonance Pedestals]] 3 blocks from the core (four sides and four corners). Put the catalyst on the core, the materials on the pedestals, and give the core a soul signal (**128 SP** at strength 15).
- **Recipes**:
  - Amethyst shard + 4 sculk + 4 soul essence → 2 echo shards
  - Amethyst cluster + 4 soul essence → 4 charoite
  - Deepslate + 4 bone blocks + 4 soul crystal blocks → reinforced deepslate
  - Resonant disc + 4 amethyst shards + 2 soul essence + 2 note blocks → 2 copies of the disc (to copy ritual discs)
- A working core makes grinders and sifters within 8 blocks run 50 % faster; on a kinetic network it runs 1.5× faster.

=== item:resonance_pedestal | Resonance Pedestal
Holds materials for a [[pysift:resonance_core|Resonance Core]], 3 blocks away on the four sides and four corners, up to eight. Amethyst, patina ingots and polished deepslate make 2.

=== item:soul_fan | Soul Fan
Blows things away and haunts items with souls. (Kinetic add-on)

- Pushes mobs and dropped items up to **8 blocks** at signal strength 15; a weaker signal blows less far.
- **Soul haunting**: put soul fire in the airflow and items resting behind it are haunted: sand → soul sand, dirt → soul soil, torch → soul torch, lantern → soul lantern, campfire → soul campfire, sculk vein → red sculk vein.

=== item:soul_drill | Soul Drill
Bores through the block in front of it. (Kinetic add-on)

- Power it from the back with a conduit or a shaft.
- Drops are the same as mining with an iron pickaxe; harder blocks take longer (hardness × 30 ticks), and a stronger signal drills faster.
- Unbreakable blocks such as bedrock stop it. **Don't stand in front of it.**

=== item:soul_shaft | Soul Shaft
The kinetic add-on's shaft: it passes **rotation** along its axis and drives machines directly, no conduit needed. Only registered when `config/pysift.properties` sets `kinetic_addon=on`; with Create installed, use Create's parts instead.

=== item:soul_cogwheel | Soul Cogwheel
Cogwheels side by side drive each other **in opposite directions**. Meshed diagonally with a [[pysift:large_soul_cogwheel|Large Soul Cogwheel]], the small one turns **twice as fast**. (Kinetic add-on)

=== item:large_soul_cogwheel | Large Soul Cogwheel
Meshes diagonally with a small [[pysift:soul_cogwheel|Soul Cogwheel]]: the small wheel turns twice as fast and the large one half as fast, for changing speed. (Kinetic add-on)

=== item:soul_gearbox | Soul Gearbox
Turns power through 90°. Four bevel gears sit around the axis; rotation coming in on any side goes out the other three, and the opposite side turns the other way. (Kinetic add-on)

=== item:soul_clutch | Soul Clutch
Holds two half-shafts. Give it a redstone signal (the lamp lights) and it lets go of the far half (the east, south or top end), stopping the machines behind it. (Kinetic add-on)

=== item:soul_gearshift | Soul Gearshift
Holds two half-shafts. Give it a redstone signal (the lamp lights) and the far half (the east, south or top end) turns the other way. (Kinetic add-on)

=== item:soul_hand_crank | Soul Hand Crank
Muscle power. Attach it to a shaft or one side of a machine and hold use: **32 RPM and 96 SP**, enough for one grinder or one sifter. Cranking for long makes you hungry. (Kinetic add-on)

=== item:siftite_gear | Siftite Gear
A part for Soul Power machines: the engine, grinder, resonance core and others need it. 4 siftite ingots and 1 soul essence make 2.
