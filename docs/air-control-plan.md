# Air control overhaul: plan and handover

The goal: Russia's air fleet handled the way the best Russia player in the replays handles theirs in the
replays, as far as a bot that reads the screen can. This note is the
plan and everything a new session needs to start on it. Read it with
`docs/allied-final-notes.md` (the map, the replays, every trial so far).

Work in the order below, one step per round. After each step the
repository owner plays a test game with the new build and sends the
recording (zip with pictures, `inputs.json` and the bot's log).

## The target: what the best Russia player in the replays does (4 games as Russia: 36, 17, 13, 10 min)

Measured from their replays (selections tracked through hotkeys; see
"Reading the replays" below):

- One air group on number key 5 is worked constantly: 23 to 40 orders a
  minute, their busiest key in three of the four games.
- About 90% of those orders are plain moves (right-clicks), 0.2 to 0.6 s
  apart, each 2 to 5 tiles from the last: they dart the group round the
  edge of a fight, never attack-moves into the middle.
- Nearly every Hold Position comes within 3 s of a move (40 of 41 in one
  game, 55 of 55 in another): move a few tiles, Hold so they stop and
  shoot, move again.
- About 1 right-click in 10 is on an enemy unit: they pick the target.
- Bursts of 10 to 20 s over a fight, then one long move to the next place.
- Battlecruisers on a key of their own (0): 3 to 7 orders a minute, mostly
  moves, a Yamato now and then.
- All of this while their ground keys keep moving.

## Where the bot is now

- Fleet keys 9, 0, 8, 7 (`AIR_KEYS`). Each key starts with one sieged
  Heavy Artillery (Ctrl+key; `open_fleet_key`) so the key never empties
  and the artillery never moves; up to 11 Scouts are added with
  Shift+key (`add_selected_scouts`, `collect_new_scouts`). Counts on a
  key subtract 1 for the artillery (`fleet_left`, `recount_fleet`).
- The fleet is only ever ordered by its keys, never boxed.
- It parks by the mass (`fleet_spot`, `park_fleet`), is attack-moved to
  the front with a hit after most of the ground has been sent
  (`send_fleet_with_hit`, `hit`), and steered every 8 to 16 s while a
  mass builds (`steer_fleet`, `AIR_LOOK_EVERY`). Routes keep to friendly
  ground (`air_route`, `send_fleet`).
- "@R bring air": a ping, then a fleet record (time, units by owner and
  kind read by the model, position); followed 5 tiles behind every 8 s;
  searched at once for up to 10 s when it is not there, then "Lost the
  fleet" (`ping_step`, `follow_ally_air`, `search_fleet`, `read_fleet`,
  `write_record`; `team.ChatEars.fleet_record`).
- Seeing: enemy team colours on the game screen (`enemy_on_screen`,
  `enemy_mask`), our gold Scouts (`gold_mask`, `gold_on_screen`), allied
  teal planes by colour (`ally_air_by_colour`), minimap colours by slot
  (`eyes/live.py` `Watch`).
- About 4 to 7 air orders a minute, all attack-moves: no hops, no Hold,
  no targets.

## Done so far

Step 1 (measure) and step 2 (groundwork), in the build after 040c6b5:

- Every order given through a fleet key is counted (`AirCounting`, a
  wrapper round the game's io): moves, attacks (each queued stop) and
  Holds. An AIR REPORT goes to the log every 5 minutes and at the end:
  orders a minute, Holds after moves, Scouts on the keys over time and
  lost, minutes in each state, each fight's Scouts at its start and end.
- The air brain: one state for the fleet (`set_air_state`, `AIR_STATES`:
  parked, travelling, with the hit, with the army, following, searching,
  fighting), set wherever the fleet is ordered, with the time in each
  added up. `steer_fleet` leaves the fleet alone while it is with an
  ally.
- Upkeep every 90 s while the fleet is parked or with the army
  (`air_upkeep`): each key is pressed and its unit pictures read
  (`read_key`): those like the learnt Scout are its Scouts, anything
  else its Heavy Artillery (the repository owner's way: no clicks on the
  map). A key without its artillery gets one of the four that is not on
  a key yet (`replace_ha`), or goes on with its Scouts alone. The fleet
  is looked for by its gold Scouts (`locate_fleet`).
- Leftover Scouts: when new Scouts do not fit one key, the rest are
  picked again and go on the next key with room; with no room anywhere
  they fly to the fleet without a key, never left by the factory to be
  swept into the mass.
- `replay_tools/air.py`: the air group's bursts in the replays. In the
  four games: bursts are short, 2 to 4 s and 5 to 8 orders, hops of 1
  to 3 tiles; 70 to 90% begin within 10 s of an order to a ground group;
  their middle is 3 to 6 tiles from the ground's targets (the air works
  over its own army, not alone); about 1 click in 9 is on a unit; most
  bursts end without a long move (the next burst follows), the few long
  moves go as often back as on. Holds are fewer than the moves suggest:
  about one burst in three has one. For step 3 this means: short
  bursts, small hops, kept over our own army at the front, alternating
  with the ground's orders rather than one long dogfight.

Step 3 (dogfight, version 1), in the build after 00f01a1:

- `dogfight` runs right after the fleet is sent with a hit
  (`send_fleet_with_hit` in `hit`): the repository owner wants only the
  air worked once most of the hit is out, no taking turns with the
  ground. Up to 60 s (`DOGFIGHT_TIME`).
- Each look: the camera on the fleet; the fleet found as three or more
  gold patches together (one alone may be a walker's lights), our
  buildings' lamps left out (`sense_fight`, `own_buildings_on_screen`);
  the enemy patches near it (`ENGAGE` 9 tiles).
- Enemy near: hop 2 tiles toward the nearest one, keeping 3 tiles off
  (`HOP`, `STANDOFF`), never more than 6 tiles from over our own army
  (`army_anchor`, `ANCHOR_REACH`); Hold after every third hop; every
  ninth order a right-click on the enemy. Bursts of 6 orders 0.35 s
  apart, then a 1 s look.
- Focus fire (the repository owner): every 6 s in a fight the model
  scans the screen for Battlecruisers, SCVs standing by bunkers, and
  bunkers (`team.ChatEars.find_targets`, `scan_targets`); found, they
  are attacked in that order, nearest first, one at a time (A, click on
  it; `attack_target`; never Shift-queued, the repository owner): 2.5 s
  with no hops so the Scouts shoot it, then a hop back, then the next
  (up to 3 from one scan). None found: only hops and Holds. Without the
  model (no API key), every ninth order is a click on the nearest enemy.
- Cover (the repository owner): once the fleet has met the enemy, at
  every count it checks our ground army under it on the minimap
  (`ground_cover`, `covered`): at least 6 of our pixels within about 6
  tiles (less the Scouts' own few) and at least half as many as the
  enemy's there. Two counts in a row without that cover (about 8 s), the
  fleet goes home.
- No enemy near: the fleet attack-moves a few tiles over our army's
  front; once it has fought, 6 looks without an enemy end the dogfight.
- The Scouts counted every 4 s: 3 or more lost since the last count, a
  step back; half lost, the fleet goes home (parked).
- The fake game in the tests draws no Scouts, so its long opening test
  runs with the dogfight off; the dogfight has its own tests.

## The plan

### Step 1: measure first
- An "air report" in each game's log: orders a minute on the air keys,
  Scouts on the keys over time and lost, time parked / travelling /
  fighting / following, each fight won or lost.
- More from the replays: what starts a burst (a hit sent, enemy air
  seen), how long it lasts, where the hops go relative to their own
  ground, what comes before a retreat.
- From the repository owner: 2 or 3 short recordings of their own air
  control in fights (the recorder takes 2 pictures a second and the
  clicks and keys).

### Step 2: groundwork
- Know where the fleet is each look (find the gold Scouts on the
  screen), not only where it was sent.
- Keys: recount them regularly, notice a dead Heavy Artillery, never
  let leftover Scouts be swept into the ground mass (today extras that
  do not fit a key are dropped from the selection and left at the
  factory).
- One "air brain" with clear states: parked, travelling, with the hit,
  fighting, following an ally, retreating. Only it gives the fleet
  orders, so different parts of the bot never fight over it.

### Step 3: dogfight micro, version 1 (move, then Hold)
- A burst starts when the fleet is over a fight: after most of a hit is
  sent, at a ping, or when enemies are near the fleet.
- Every 0.3 to 0.6 s: press the air keys, find the enemy patches near
  the Scouts, right-click 2 to 4 tiles toward the edge of the enemy,
  then H (Hold). About one order in ten a right-click on the nearest or
  biggest enemy clump.
- End after 15 to 20 s, when no enemy is left, or when Scouts are dying
  fast (count the keys): pull back a few tiles or park.
- Check against the targets above: 20 to 40 orders a minute in bursts,
  move then Hold.

### Step 4: knowing what shoots air (the biggest gap)
- Recognise the enemy units that hit air: marines, Goliaths, missile
  turrets, bunkers, enemy air, in red, blue and yellow. Needs picture
  samples of each from the repository owner, and the model for doubtful
  cases (too slow, about 2 s, for every tick).
- Hop away from anti-air, shoot first what cannot shoot back (tanks,
  transports), stay off turrets, retreat early when the anti-air
  outweighs the fleet.

### Step 5: doing two things at once (the hardest limit)
- The bot does one thing at a time. A scheduler gives the air short
  slices between ground actions: during a hit, most of the ground first,
  then air ticks alternating with the rest; while massing, short air
  bursts between training and rally moves.
- Make each air tick cheap (fewer camera moves and screenshots).

### Step 6: using the air where it counts
- When and where to fight: with the hit, over the mass, helping allies,
  hunting enemy transports and air.
- Battlecruisers on their own key, with the ground, Yamato on big
  targets (bunkers, turrets).
- Wait for enough Scouts before a fight; no small groups into anti-air.
- The general (the model adviser) may suggest air plans between fights.

### Step 7: test and tune
- After each step a test game; compare the air report with the targets
  (orders a minute, share of moves followed by Hold, Scouts lost a
  minute, kills) and tune hop size, tick, burst length, retreat rule.

Honest ceiling: the air can be made to look like theirs after steps 2 and
3; step 4 matters most for results; step 5 decides whether it keeps up
during hits. About half their effectiveness is a fair expectation.

## The repository owner's standing rules for the air (keep them)

- Fleet: Scouts plus one sieged Heavy Artillery per key, up to 11
  Scouts a key, keys 9, 0, 8, 7. Battlecruisers go with the ground.
- Ordered only by its keys; never boxed with the ground.
- No air steering while a hit is being sent; the fleet goes once most
  of the hit has gone. Over the army, avoiding more than 3 marines per
  Scout.
- One fleet (no splitting).
- "@R bring air" as described above; "@R return air" brings it home;
  "@R reset" does not touch the air.

## Working in this repository

- Code: `bot/trial.py` (the bot), `bot/team.py` (chat and the model
  calls), `eyes/` (screen reading), `hands/win.py` (mouse and keys),
  `recorder/recorder.py` (the recorder), `bot/app.py` (the app).
- Tests: `timeout 900 python3 -m pytest -q -p no:cacheprovider tests`
  (about 240, 3 to 4 minutes). Add a test for every new behaviour;
  `tests/test_bring_air.py` and `tests/test_fleet.py` show the stubs.
- Builds: pushing to main builds StarcraftTrial.exe and
  StarcraftRecorder.exe on GitHub Actions and puts them on the release
  tagged `recorder`. The app shows its build (commit) in its title and
  log, so the owner can check they run the newest one.
- Write notes and code comments without other players' names (replays
  and recordings hold them; they are not committed). Never commit
  replays, recordings or keys.

## Reading the replays

Replays are read with screp (`screp -cmds -map r.rep > r.json`) and the
scripts in `replay_tools/`. the best Russia player in the replays plays Russia (slot 5) in four games
long enough for air: the 36, 17, 13 and 10 minute ones. To see what a
hotkey group does, follow the selection through the commands: Select /
Select Add / Select Remove set it, Hotkey Assign / Add store it in a
group, Hotkey Select restores it; then count the Right Click, Targeted
Order (AttackMove, Attack, FireYamatoGun), Hold Position and Stop
commands given while each group is selected, with their times and
positions. Unit types are not in the commands; the groups are told
apart by what they do (Yamato means Battlecruisers).
