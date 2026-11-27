# Air control overhaul: the plan after the review

This replaces "The plan" in `docs/air-control-plan.md` (steps 1 to 3 of
that plan are built; its description of the bot and of the replays still
holds). It was written after the bot's last Russia game (18 minutes) was
set beside the four long replays of the best Russia player.

## Where we stand

| | Best player (4 games) | Bot (last game) |
|---|---|---|
| Air orders a minute, whole game | 23 to 40 | 5 |
| Share of the game the air is worked | 50 to 62% | about 7% |
| First air action | 0.7 to 1.1 min | 1.5 min |
| Order mix | 88 to 95% moves, 4 to 7% Hold, 1 to 6% attack-move | half attack-moves |
| Time between orders in a burst | 0.2 to 0.4 s | 0.35 s, then a 1 s look |
| Clicks on a unit | 8 to 15% | almost none |
| Turns on the air key | 8 to 16 a minute, 1 or 2 orders each | one block of up to 60 s per hit |
| Longest idle stretch | 1 to 2 min | 4 to 6 min |

What failed in the bot's game:

- Three of four dogfights ended after 1 or 2 orders: "the fleet is out
  of sight".
- The one real fight: 21 Scouts flown toward a capital, 13 lost in about
  20 seconds.
- No opening strike, no raids; the fleet moved only when a hit was sent.

More from the replays:

- Opening: 42 to 59 orders in minute 1 round Konigsberg and Warsaw, 7 to
  15 of them clicks on single units, in every game.
- One key of up to 12 fighters, refilled as planes arrive (55 planes
  through that key in 36 minutes). Battlecruisers on a key of their own.
- About 60% of hops are under 3 tiles; 35 to 45% of quick moves turn
  back on the one before.
- Most bursts are within a few tiles of the ground's own fight. In three
  of the four games, 8 to 10 bursts are raids with no ground near.

## Targets (checked in every test game by the air report)

| Measure | Now | After phases 1 and 2 | After phases 3 to 6 |
|---|---|---|---|
| Dogfights ended by "out of sight" | 3 of 4 | 0 | 0 |
| Scouts lost in the worst 20 s | 13 of 21 | at most a quarter | at most a quarter |
| Orders a minute while fighting | about 10 | 60 or more | 60 or more |
| Orders a minute, whole game | 5 | 8 to 10 | 20 or more |
| Share of the game the air is worked | 7% | 10 to 15% | 40% or more |
| Share of orders that are plain moves | 40% | 80% or more | 80% or more |
| First air action | 1.5 min | 1.5 min | by 1.0 min |

## The phases

One phase a round. After each, a test game from the repository owner
with the recording; the next phase starts from what that game shows.

### Phase 0: a test build (no change to play)

Purpose: learn how the game answers before anything is built on it.

- Early in the game, for each fleet key: double-tap it, save a picture,
  read the white box on the minimap, log where the screen landed and
  whether gold Scouts are on it.
- The same with one Scout picked from the key (a click on its small
  picture) and the "centre on selection" shortcut (believed to be
  Ctrl+C; not confirmed for this game).
- Done when: the log says which of the two puts the Scouts on screen,
  with the Heavy Artillery on the key.

### Phase 1: always know where the fleet is

- A single `where_is_fleet`: jump the screen to the fleet (the way
  phase 0 proved), read the white box with the exact reader made for
  Norway (`live.camera_from_minimap`, `live.view_after_click`), confirm
  by the gold Scouts on screen. Returns the fleet's tile and its age.
- Used at every look of a dogfight, and every several seconds while the
  fleet travels or waits. The guessing (`on_way`, `dest`, `origin` in
  `dogfight`) goes.
- With several keys: the first key with Scouts is "the fleet"; the
  others are checked less often and brought to it when they stray.
- If neither way of phase 0 works with the artillery on the key: the
  artillery comes off the keys (the owner's decision 2), and an empty
  key is handled by `recount_fleet` instead.
- Tests: the fake game gets a fleet that is not where it was sent; real
  pictures of the white box.
- Done when: no dogfight ends by "out of sight" in a test game.

### Phase 2: fight without throwing the fleet away

- Approach: the fleet travels by plain move to a point over our own
  army's front, never by attack-move to a city.
- In a fight, only short moves: 1 to 3 tiles toward the edge of the
  enemy, then back out; about four moves in ten turn back. Hold now and
  then. Attack-move rare.
- Known anti-air from the map file: the starting Missile Turrets and
  Bunkers of the Axis slots are in `data/af40.json`. The fleet keeps a
  stated distance from them (no samples needed; they may have been
  destroyed, which costs only caution).
- Retreat sooner: the Scouts are counted every 2 s in a fight; a
  quarter lost in any 6 s is a pull back to the army, half lost is
  home.
- A fight is not begun with fewer Scouts than a stated least (data).
- Cheaper looks: one picture a look, the 1 s pause between bursts cut,
  so the orders in a fight reach one a second or more.
- Done when: the worst 20 s of a test game costs at most a quarter of
  the fleet, and four orders in five are plain moves.

### Phase 3: short turns for the air, all game

- A scheduler in the main loop: every few seconds, between ground jobs,
  the air gets a turn of 1 to 3 orders (key, look, order, back).
- Stage 1: no air turns while a hit is being sent (the owner's rule
  kept for that moment); turns at all other times.
- Stage 2, after a test game: turns during the sending too (the owner's
  decision 1).
- The 60 s block after a hit stays as the heavy part of a fight, but is
  cut short when the ground has work waiting.
- Done when: the air is worked in at least 40% of the game and no
  ground job is later than before by more than a stated margin.

### Phase 4: knowing what shoots air

- Picture samples from the owner of marines, Goliaths, Missile Turrets,
  Bunkers and enemy fighters, in each Axis colour (a short recording
  with each on screen is enough).
- A reader that marks, on each look, the patches that shoot air and
  those that cannot (tanks, artillery, transports, workers).
- The hops go round the first and onto the second; the fleet leaves
  when what shoots air outweighs it (the measure is data).
- The model stays for doubtful cases only, between fights.
- Done when: Scouts lost per enemy unit killed falls in test games
  (counted by the model from before and after pictures, or by the
  owner's eye).

### Phase 5: the opening strike

- In the first minute the starting Scouts go to Konigsberg and Warsaw
  and pick single targets, as in every replay; back to the army before
  the first hit.
- Needs phases 1, 2 and 6 at least in part.
- Done when: first air action by 1.0 min and no more than 2 Scouts lost
  in it.

### Phase 6: choosing targets on the screen

- About one order in ten is a click on an enemy unit, chosen from the
  picture of that look (nearest of the kinds that cannot shoot back,
  else the nearest), not from the 6 s model scan.
- The owner's focus-fire order (Battlecruisers, SCVs by bunkers,
  bunkers) is kept as the order of preference.

### Phase 7: Battlecruisers and raids

- Battlecruisers on their own key, with the ground, Yamato on Bunkers
  and Missile Turrets.
- When the front is quiet and the fleet is large enough: a raid on a
  weak place (enemy seen on the minimap without anti-air near), then
  back.
- Last, because it needs every phase before it.

## The owner's decisions

1. Air turns while a hit is being sent (phase 3, stage 2). Proposal:
   allow them after stage 1 has worked in a test game.
2. The Heavy Artillery on the fleet keys. Proposal: keep it if phase 0
   shows the screen can still be put on the Scouts; else take it off.
3. Several fleet keys. Proposal: keep them.

## Standing rules kept

- The fleet is ordered only by its keys, never boxed with the ground.
- One fleet, no splitting (a raid in phase 7 takes the whole fleet).
- "@R bring air", "@R return air" and "@R reset" as they are.
- No more than 3 marines to a Scout.

## Risks and limits

- The bot does one thing at a time and reads the screen. About half the
  best player's effect is a fair ceiling.
- Phase 3 takes time from the ground. It is measured, and the turns are
  cut if the ground suffers.
- Phase 4 depends on samples and on colours that differ by slot; it may
  take more than one round.
- Each look costs a camera jump. Phase 1 must not make the ground's
  clicks land on the wrong view: every ground job sets its own view
  first, as now.
