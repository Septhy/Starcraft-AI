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

Result (the owner's recording, 115 s, made by hand):

- A fleet key pressed twice moves the view to the average place of
  everything on the key. The Heavy Artillery at Moscow pulls it off the
  Scouts: about 11 tiles with six Scouts on the key (they show at the
  screen's left edge, 5 tries of 5), about 15 with four (at the edge or
  off the screen, 7 tries). The view landed one seventh of the way from
  the Scouts to Moscow, to a tile or two, in each jump measured.
- One Scout's small picture clicked, then Ctrl+C: the view jumps to
  that Scout and puts it in the middle (to about half a tile).
- The Scout's and the artillery's small pictures are told apart
  without a mistake (564 pictures; also on the bot's own older game
  pictures, where the old picture check had failed).
- So the artillery stays on the keys (decision 2 is settled).

### Phase 1: always know where the fleet is

Built (not yet tried in a game): `where_is_fleet` in `bot/trial.py`: a
fleet key, the first small picture that is a Scout clicked, Ctrl+C, the
white box on the minimap read, a gold Scout checked for in the middle.
About half a second. The dogfight asks it at its start and whenever it
does not see the fleet where it thought; the guesses at where the fleet
"should be by now" are gone; three looks in a row without a Scout end
the dogfight. The upkeep's look uses it too. The air report counts the
finds, their time, and the times no Scout was seen where the view
landed (a picture "fleet-not-centred" is kept once). With a single
fleet key, the view is put back before each hop (a key pressed twice
running may move the view).


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

# Beyond the air: the ground, the economy, and the order of work

Added after the same review. This replaces `docs/improvement-plan.md`
(kept for its history). The best player's figures are measured from the
four long replays; the bot's are from the log of its last game (18
minutes); the percentages are estimates.

## Where the bot stands overall

| Area | Bot against the best player | Why |
|---|---|---|
| Overall plan (when and where) | about 70 to 80% | Timings and routes come from the replays and the owner's rules; it reacts poorly to surprises. |
| Hand speed (keys and clicks a minute) | about equal | About 247 a minute against 244 to 254. |
| Massing and sending attacks | about 50% | Most of the army goes (47 to 68 groups), but one attack takes 40 to 60 s to send, then it waits for 120 men again. |
| Winning the attacks | about 30% | Four attacks in 18 minutes: one arrived, one stalled, two lost. |
| Economy (marines, upgrades, tax) | about 40% | Tax mostly fails; barracks training fell from 8 to as few as 1. |
| Air control | about 10 to 15% | See the table at the top. |
| Several things at once | about 20% | One job at a time. |
| Reading the fight | about 25% | Only colours on the minimap; no idea what shoots air. |

Fair ceiling if all of this works: about 60% of the best player overall.

## The ground items

### G1: keep the army fighting, not in waves

- Replays: 75 to 83 ground orders a minute; the ground left alone for
  more than 20 s once in four games. Three or four keys hold the
  fighting groups and are steered all the time; new men are boxed and
  sent forward in a steady stream.
- Bot: masses 120, sends all, masses again; the men at the front get
  almost no orders between attacks.
- Build: the big attack stays. After it, every 20 to 30 s whatever has
  gathered is sent to join the front, and the groups at the front are
  re-aimed. The front's groups go on keys of their own.
- Done when: the longest stretch without a ground order at the front is
  under 30 s, and men reach the front every minute.

### G2: fight with moves and Hold, not only attack-move

- Replays: 15 to 32% of ground orders are attack-moves; the rest are
  moves and Hold Position (up to 145 Holds a game).
- Bot: everything by attack-move, then left.
- Build: "step and hold" for the leading groups; a step back when the
  enemy's colour in front of them grows faster than ours.
- Done when: at most half the ground orders at the front are
  attack-moves, and more of each attack is alive after a minute of
  fighting.

### G3: judge the fight and act on it

- Bot: an attack is "being lost" only when one group of survivors is
  left.
- Build: our colour and the enemy's at the front compared every few
  seconds. Losing: back to the reinforcements early. Winning: on to the
  next city without going home to mass.
- Needs the owner: the rule for when an attack is pulled back, and to
  where.
- Done when: no attack is lost to the last group, and a won city is
  followed by the next within a minute.

### G4: never stop making marines

- Replays: back at the barracks every 13 to 35 s all game; up to 8
  more barracks built.
- Bot: 8 barracks training at the start, 3 by 5 minutes, later 1 to 4.
  The cause is not yet known (lost, floated for tax, or not found on
  the screen).
- Build: first the cause, from the recording. Then training at every
  barracks every 20 to 30 s, and lost ones rebuilt.
- Done when: every standing barracks trains in every round of training
  and their number does not fall unless the enemy destroys them.

### G5: tax that works

- Replays: buildings lifted 9 to 18 times in a long game and landed in
  taken cities; depots too, less often.
- Bot: failed again (a city not taken; the SCV for a depot never
  found).
- Build: reuse the Norway work (exact views `live.view_after_click`,
  the proved SCV selection, the green outline before a landing or a
  depot); every step of a tax followed and retried; a tax report in
  the log.
- Needs the owner: one short recording of a city taxed by hand.
- Done when: every city an ally asks for is taxed within one round
  unless the enemy holds it.

## The scheduler (under all of it)

The bot does one job at a time, so every item competes with the others.
Phase 3 of the air plan (short turns) is built as a scheduler for all
jobs: air turns, feeding the front (G1), training (G4), tax steps (G5),
judging the fight (G3). Each job is short, sets its own view first, and
says when it next wants a turn.

## The order of work

1. Air phases 0 to 2 (know where the fleet is; stop the losses).
2. The scheduler, with G1 and G4 as its first ground jobs, and air
   phase 3, stage 1.
3. G5 (tax).
4. G2 and G3 (step and hold; judging the fight).
5. Air phases 4 to 7, and phase 3, stage 2 if the owner agrees.

A scorecard run after every test game (from the log): air report as
now, plus ground orders a minute at the front, longest ground pause,
barracks training each round, men sent a minute, each attack's outcome,
cities taxed.

## What is needed from the owner, by step

| Step | Needed |
|---|---|
| Air phase 0 | A 2-minute recording made by hand: a sieged Heavy Artillery and some Scouts on one key, the Scouts flown away, the key double-tapped (2 to 3 s still); then the key, one Scout's small picture clicked, Ctrl+C (2 to 3 s still); if time, a key of Scouts alone double-tapped. |
| Air phases 1, 2 | One test game each with the recording; for phase 2, 15 minutes or more, with real anti-air at the front if possible. |
| Scheduler, G1, G4 | One test game with the recording, and a word on whether the ground felt slower. |
| G5 | A short recording of a city taxed by hand; then a test game. |
| G2, G3 | The pull-back rule; a test game. |
| Air phase 4 | A recording with marines, Goliaths, Missile Turrets, Bunkers and enemy fighters, and things that cannot shoot up, clearly on screen in each Axis colour. |
| Air phase 5 | Optional: a recording of an opening air strike by hand. |
| Air phases 6, 7 | A test game each (20 minutes or more for phase 7). |
| Any time | More replays of strong Russia play; a recording of good air play from the player's own screen. |

# Trial 40 (build f514f2c, 13.6 minutes): phase 1 in a game, and the hits

Phase 1: the fleet was found by Ctrl+C on a Scout 11 times, 0.81 s
each, never missed; no dogfight ended "out of sight". The small
pictures told 11 Scouts and the artillery on key 9 rightly. But the
fights were still lost (4 Scouts to 2 in 20 s; 7 to 2), and in the
third (61 s, 42 orders) the fleet stood over our own ground with no
enemy near, ordered to one spot on the minimap again and again: inside
a fight the fleet is still looked for by its gold colour, and the game
is only asked when none is seen. Phase 2 asks at every look.

The three hits (measured in the log):

| | Hit 1 | Hit 2 | Hit 3 |
|---|---|---|---|
| Mass ready | 62 s | 272 s | 655 s |
| Main boxes sent | 27 s, 25 boxes | 43 s, 56 boxes | 42 s, 49 boxes |
| Leftovers after the fleet is sent | 18 s, 11 boxes | 24 s, 14 boxes | 21 s, 9 boxes |
| Scouts taken out of boxes (clicks) | 5 | 21 | 24 (about 6 s) |
| Dogfight (no ground orders) | 22 s | 17 s | 61 s |
| From ready to done | 67 s | 83 s | 123 s |
| Units a box | 6.6 | 6.0 | 6.5 |
| Outcome | lost | lost | lost (supply 194 to 25 in a minute) |

Germany's kills rose by about 230 during the third hit; three of its
Battlecruisers were seen at the front in the second.

The best player's replays, measured the same way: there are no separate
hits. Every minute 50 to 200 units get an order forward (the bot: none
between hits); a unit gets 4 to 5 forward orders in its life (the bot:
one); 130 to 190 units go forward in the first minute (the bot's first
hit leaves at 62 to 129 s); orders go to a dozen units at a time (the
bot's boxes hold six); plain moves go to a line 34 to 47 tiles from the
mass, attack-moves 49 to 63 tiles: up to a line first, then in.

To do (with the owner's answers): Scouts caught in a ground box are
sent with it, not taken out; no long tail of leftover boxes; boxes of a
dozen; the army moved to a line near the front and sent in from there
together; orders forward every minute and to the units at the front
again; ground orders during the dogfight.

After trial 40 (the owner: the air did not come back although the hit
had gone): in a dogfight, at every count, the ground troops of ours
forward of the massing place are counted on the minimap (the Scouts'
own pixels left out); fewer than 10 two counts in a row, from 8 s into
the dogfight, and the fleet goes home, also when it has met no enemy
(before, the ground under it was only judged once it had). The same is
looked at when a dogfight ends.

## The owner's answers after trial 40

Russia:
1. The first hit may vary: the present one stays, and a first-minute
   variant (as in the replays) is added that happens now and then.
2. The massing place as the line to form up on is fine as it is (a
   player can ask Russia to mass elsewhere).
3. Russia is meant to grind the enemy down with mass marine hits; the
   third hit of trial 40 is what is expected. What matters is how fast
   the units are boxed and sent: wanted is more speed there.
4. No ground orders while the air is fighting (the rule stands).

Norway:
- No recording of a full Dropship cycle; one with Firebats and
  Battlecruisers will be tried.
- Kerrigans are among the reinforcements at the camp; Siege Tanks too,
  and tanks also come out at Factory 4.

Where a box's time goes now (trial 40, hit 2): the drag 0.16 s, a look
at what it took (a screenshot: for Scouts and empty boxes) about 0.15 s,
A and the click 0.2 s, a pause 0.25 s: about 0.55 s a box, six men a
box; 0.6 s a screen before its first box; 12 screens.
