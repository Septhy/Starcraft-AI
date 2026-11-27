# Norway (slot 4, orange): notes from replays

The repository owner chose six players as the samples for Norway: 17 of
their Norway games in the replays (5 to 66 minutes). Names are not kept
here (see `docs/allied-final-notes.md` on replays). Read with the same
tools; the scratch script for this note followed each building through
Lift Off, its flights (Right Click while it alone is selected) and Land.

Positions in a replay's Land and Build commands are in tiles; in every
other command (Right Click, Targeted Order, Lift Off) in map pixels.

## Norway at the start

Start: Oslo (tile 97, 50). Buildings (map pixels in `data/af40.json`):
Command Center (91, 54), Barracks (112, 35), Starport (103, 41),
Factory (109, 45), Engineering Bay (103, 48), 6 supply depots, 13
bunkers, 9 missile turrets. One Dropship, 41 ground units.

## The opening in the sample games (first 2 to 4 minutes)

| What | When (sample games) | Where |
|---|---|---|
| Starport lifted | 3-22 s, all 17 | lands at Murmansk, tile (154, 4) in every game (one at 154, 5), 46-129 s, median about 87 s |
| Factory lifted | 3-93 s, 16 | floats to Shetland 300 (most), else Factory 10; does not land |
| Engineering Bay lifted | 5-216 s, 16 | floats to Shetland 300 (most), some Trondheim first |
| Command Center lifted | 0-90 s, 17 (most 12-24 s) | to Kiruna 200 or Murmansk, landing at 84-234 s round tiles (123-146, 2-21) |
| Barracks lifted | 4-180 s, 16 | lands in Finland, 27-182 s: by Kiruna (tiles 136-139, 8-12), the "Russian army-Finland" spot (145-148, 24-32) or east of Murmansk (158-163, 18-28) |
| Finland attacked | first attack-move 2-30 s, median about 22 s | the starting army attack-moves at the "Russian army-Finland" spot, Factory 10 and Helsinki (tiles 125-160, 25-55); 361 such orders in the 17 games |
| Shetland | first unload 2-97 s: either at once (2-22 s, 7 games) or after a minute (44-97 s) | Shetland 300 (tile 64, 33) |
| Supply depots | first at 43-103 s, about 8 a game in the first 3 min | mostly in the far north-east: near "Place Artillery" (182, 46) and Arkhangelsk (208, 10), some by Kiruna, Murmansk and Factory 10 |
| SCVs | 2 at once (all games), 35 in the first 3 min | build the depots |
| Dropships | first at 97-142 s, 213 in the first 3 min of the 17 games | from the Starport at Murmansk |

The repository owner (trial 38): "0-2 min requires taking and taxing
Finland, lifting key buildings from Norway to Russia and the taking of
Shetland."

## The repository owner's rules for the opening

- Finland: every red (Germany) building there destroyed and cleared, and
  Norway's Barracks floating over Finland, before 3:25 on the top timer
  (the round countdown, 5:00 at the start of the game). In the map data
  Germany's buildings in Finland are: Barracks (143, 31); supply depots
  (145, 20), (146, 29), (139, 32), (137, 43); bunkers (134, 36), (140,
  39); missile turrets (131, 40), (133, 44), (141, 45), (137, 45) (tiles).
- Then Norway destroys Russia's Starport at Murmansk (tile 156, 5) and
  lands its own Starport there (154, 4), taking the Control Tower. If
  Russia has moved its Starport away, Norway just lands there.
- Copy the most common choices of the sample games (Factory and
  Engineering Bay floated to Shetland, Command Center to Kiruna).
- Tax in Finland: Helsinki and Factory 10, both taxed at once by one
  floating building.
- Supply depots in the far north-east: for safety.
- Shetland: the drop goes at once, with the starting Dropship.

- The Barracks lands next to the Heavy Industry (the "Factory 10"
  building in Finland), our marines moved out of the way first; landed
  there it taxes Helsinki and Factory 10.
- Russia's Starport at Murmansk is destroyed by the marines, right after
  Finland is taken.
- Russia's bot does not need to lift its Murmansk Starport.
- Chat commands: "@N ...", as "@R ..." for Russia.

## After the opening, in the sample games

Regions are rough boxes of tiles; drops weigh three times an attack-move.

- 5-10 min: marines in numbers (about 45 a game in these five minutes,
  then 50-80 a round), some Firebats, more Barracks (14 built in the 17
  games), Dropships to about 15 in all. Drops start: the east front
  (Konigsberg, the German invasion area), the UK and Ireland, Italy, the
  Balkans (Belgrade, Hungary, Sarajevo), now and then the Middle East.
- 10-15 min: mostly the UK and Ireland (Scotland, London), then the
  Balkans (Romania, Odessa) and the east front (Warsaw).
- 15-20 min: back home to Norway and Sweden in half the games (Oslo,
  Sweden; the map's German invasion of Norway), the rest the UK, the
  Balkans or the Middle East.
- Later: the east front (the German invasion area, Konigsberg), the UK,
  Sweden.
- Every player differs: one went mostly to the UK, one mostly east and
  to the Balkans, one to the Middle East. The common thread: Norway is
  the Allies' fire brigade, dropping marines wherever an ally or a city
  needs them, and going home when Norway itself is invaded.

## Drops with Russia: how the best Norway player does it (2 games)

How (the commands):
- Loading at Murmansk: small selections of new marines are right-clicked
  onto a Dropship standing there (2 to 12 at a time), and the loaded
  Dropships are added to one key (7; a second group on 5).
- The flight: the Dropship key pressed and right-clicked every 0.2 to
  0.5 s, a few tiles at a time, along a route (Murmansk, Finland, the
  Baltic, then over Russia's army: Konigsberg, Warsaw, Prague, the
  German invasion area), never one long move. On the way the Dropships
  are often told to follow Russia's own units ("Follow" on a Russian
  unit; 17 such orders in one game), so they ride over Russia's army.
- The drop: one Dropship is taken out of the selection (kept back, empty
  or hurt), then U and a click (Unload at a point), then the same again
  three or four times within 2 s at points a tile or two apart, so the
  marines come down spread out.

Where (the decision), compared with Russia's attack-moves in the minute
before each drop:
- Every big drop (5 to 13 unloads) landed where Russia was attacking, 1
  to 12 tiles from Russia's own target: Capital City 7 with Russia going
  at Frankfurt; Damascus and Baghdad with Russia in the Middle East;
  Odessa and Romania with Russia at Odessa; the "Italy Draft" and
  Hungary, just past Belgrade and Serbia, with Russia attacking Factory
  7 and Serbia; the German invasion area with Russia at Capital City 8.
  Into the fight Russia is in, or just behind the enemy line it is
  attacking, never far from it.
- The small drops of one or two Dropships go to the UK (London,
  Scotland, the English air fields): not with Russia.
- The first drop is at 3 to 4.5 minutes, then one with Russia every
  2 to 5 minutes.

The repository owner accepted: the bot cannot tell which of Russia's
units to follow on the minimap, so the Dropships fly to where Russia's
army is thickest, looked at every few seconds, instead of "Follow".

## The repository owner's recording of the opening (trial 40)

Read from the recorder's pictures and inputs (the minimap's view box on
each picture gives the camera, so every click is a map tile):
- 0-25 s: every starting trooper boxed onto keys 1 to 4 (5 later):
  Oslo and Sweden's (tiles 97-112, 56-66), the Norwegian partisans and
  reinforcements (112-120, 16-26), Narvik (99-112, 6-17), Kiruna
  (136-146, 11-19). The starting Dropship is empty: the few men beside it
  at Oslo (tiles 85-89, 45-49) are boxed and right-clicked onto it, then
  U and Shetland (64, 33) at 8 s.
- 10-22 s: the buildings lifted; Factory and Engineering Bay to Shetland.
- 25 s: every key moved to Kiruna (143, 16): the army gathers.
- 30 s: every key attack-moved at the "Russian army-Finland" spot
  (147, 30-37); 39 s: Factory 10 (143, 35); 40-44 s: Helsinki (135-137,
  37-39); then boxes and attacks round Factory 10 and Helsinki.
- About 61 s (3:28 on the countdown): Finland clear.
- 63-65 s (3:23): every key moved to Murmansk (155, 10) and attacked
  Russia's Starport (156, 4).
- 68 s on: an SCV builds depots by Arkhangelsk (tiles 194-209, 13-27).
- 104 s (2:23): the Barracks lands just north of the Heavy Industry
  (about tile 138, 30), having floated over Finland since early on.
- One order a key about every ten seconds, not a stream of boxes (the
  bot's first try re-boxed six groups every 3 s and never cleared
  Finland).

## Trial 41: the bot's second try against the owner's recording

- Keys: one box a key (one empty), so the troops of Sweden, Narvik and the
  Norwegian partisans were never keyed; the owner filled each key with
  two or three boxes (Shift). Now boxes are added to a key until it holds
  a dozen, and the men on each key are logged.
- SCVs: ordered at 11 s; the owner's first act (2 s). Now first.
- Stages: Helsinki attacked at 60 s; the owner moved on at 39-40 s and
  attacked Helsinki at 41-44 s. Now: the Finland spot once most of the
  army is at Kiruna (45 s at most), then a move to Helsinki 9 s later
  and the attack there 2 s after.
- Clean-up: every key attack-moved at the same minimap point every 10 s
  (by tile 131, 37) for 45 s and the red stayed. The owner boxed men on
  the screen and attacked the buildings themselves every 1 to 2 s. Now
  every 4 s the camera goes to the red that is left and each key attacks
  one red building seen there (A, then a click on it).
- Pictures of Finland are kept at each stage and clean-up.

## Trial 42: the bot's third try against the owner's recording

| | Owner | Bot (build 67fd737) |
|---|---|---|
| SCVs | 2 s | 5 s |
| Army keyed | 3-25 s, between other jobs | 5-20 s, all at once (15 boxes) |
| Shetland drop | 8 s | 23 s |
| Buildings lifted | 10-22 s | 24-30 s |
| Gathered at Kiruna | 25 s | 31 s |
| Attack on Finland | 30 s | 75 s: it waited for most of the army at Kiruna (45 s at most) |
| Helsinki | 40-44 s | 88-92 s |
| Finland clear | about 61 s | not by 121 s |
| Depots | an SCV followed and building from 47 s | the camera on empty ground by Arkhangelsk every 3 s from 58 s to 75 s, no SCV there yet |

Changes: no wait at Kiruna (the attack 5 s after the gather order, as
the owner); the drop and the lifts before the army is keyed; at most 10
bigger boxes for the keys; the depots looked for from 60 s, every 12 s,
5 times at most, after Finland's orders.

## Trial 43 (build 8fa22cb): on time, but too few and split up

The timing now matched the owner's (gathered 21 s, attack 29.5 s,
Helsinki 39-43 s). Our minimap pixels, owner's recording / the bot:

| Seconds | Finland | Narvik and partisans |
|---|---|---|
| 45 | 101 / 123 | 158 / 192 |
| 60 | 140 / 13 | 156 / 176 |

- The keys held only 25 men (11, 11, 3): the ten boxes ran out before
  Narvik and the partisans, and two boxes came up empty; those men never
  moved. The owner's army grew as they arrived. Now up to 16 boxes, one
  for each place first (Oslo, Sweden, Narvik, the partisans, Kiruna).
- The clean-up shared the keys out over several red buildings; the
  army was cut down piece by piece between 47 and 60 s. The owner kept
  it together (and drew back toward Factory 10 at 45 s). Now every key
  attacks the red building nearest our men (found on the minimap: the
  screen check for our colour is Russia's brown).

## Trial 44 (build 66594a2): better, still slow; the Barracks shot up

- Four keys (11, 11, 11, 3); red in Finland down to 75 pixels by 67 s,
  but the army was gone by 74 s. Keyed at 14-25 s after the lifts;
  gathered 26 s, the Finland attack at 37 s (owner 30 s), Helsinki 50 s
  (owner 41-44 s); the Command Center's lift and the key counts sat
  between the stage orders.
- The Barracks floated straight over the Heavy Industry and was shot up
  by the bunkers and turrets (the owner: it should not be badly damaged
  when it arrives).
- Now: the army keyed and sent to Kiruna right after the drop, before
  the lifts; no key counts between stage orders; the Command Center
  lifted only after the stages; the Barracks waits by the Norwegian
  military camp (tile 127, 22) until Finland is clear, then flies in to
  land.

## Trial 45 (build 6f48a5f)

- The owner: the men at (105, 66) by Sweden and (142, 9) by Kiruna were
  never brought; and Germany's missile turrets in Finland must also be
  gone by 3:25 on the countdown.
- Both groups stand beside a bunker: the minimap reading leaves out our
  buildings' pixels, so they were hidden and never boxed. Now the army
  is boxed from the map's own starting positions (13 patches of
  ground, the biggest first), then anything else the minimap shows.
- Clean-up: Germany's 11 buildings in Finland from the map (4 depots,
  the Barracks, 2 bunkers, 4 missile turrets), the nearest to our army
  first: the camera on it, crossed off once no red is left there, else
  every key attacks it. Finland counts as clear only when the list is
  empty.
- Keys held 11, 11, 12 and 6 men; the army attacked Finland at 28 s and
  Helsinki at 37-41 s (the owner: 30 s and 41-44 s), but was gone by
  about 73 s with 100 red pixels left.

## Trial 46 (build eca55e7): still too slow; the Barracks too late

- Five keys (12, 12, 12, 11, 4); Finland attacked 29.5 s, Helsinki
  42.8 s, as the owner. But three of Germany's buildings were crossed off
  in one second at 46 s while still standing (the screen's bright team
  red is too little on their buildings), the army moved on and was gone
  by about 80 s with red still on the minimap.
- The owner: the Barracks must reach Helsinki much sooner. A floating
  building is slow (about 20 s across Finland) and it waited for
  Finland to be clear.
- Now: a building is gone when the minimap shows no red on it (2
  pixels round); the Barracks flies in over Finland (by the Heavy
  Industry) as soon as the army moves on to Helsinki, and lands once
  Finland is clear.

## Trial 47 (played on build eca55e7, not the newest 675dedc)

- The owner: still too slow; the Barracks did not make it in time; for a
  wider flank the marines move to (147, 31) just 2 s before they attack
  Germany's bunkers.
- Now the stages: gather at Kiruna; attack the Finland spot (147, 30);
  8 s later move to (147, 31); 2 s later attack the east bunker (140,
  39), then the west bunker (134, 36), then Helsinki. The Barracks flies
  in over Finland as the army attacks the Finland spot (about 29 s).

## Trial 48 (build 675dedc): still too slow

- Germany's buildings fell one by one from 52 s, but an order only every
  6 to 13 s: between them the bot lifted the Command Center (45 s),
  ordered the depots (63 s) and moved the camera onto each building.
  Stopped at 78 s with 5 left (the owner: clear by 61 s).
- Now every army key gets all of Germany's buildings in one chain of
  attack-moves (the nearest first, Shift for the rest, minimap clicks,
  no camera), so the army goes on by itself; given again when the first
  falls or every 10 s. The Command Center and the depots wait until
  Finland is clear (or 100 s).
- The owner: each box of men sets off for Kiruna as soon as it is keyed,
  while the rest are keyed.

## Trial 49 (build 1815372): "so close"

- Bunkers and the northern buildings gone by 56 s; turrets 131,40 and
  133,44 by 76 s; stopped at 81 s with a depot and two turrets left.
- The owner: the Barracks should be around (139, 33) (it went to about
  138, 30); the army paused a few seconds (a chain of five buildings for
  each of four keys took 6 s to give, then 10 s before the next); after
  the flank the infantry should move further in before the bunkers;
  once the bunkers are down, every turret at once.
- Now: the Barracks floats to and lands at (139, 33); stages: Kiruna, the
  Finland spot, the flank (147, 31), in to (143, 34), the east bunker,
  the west bunker; then chains of three, bunkers and turrets before
  anything else, given again every 6 s.

## Trial 50 (build 79dcc22): Finland taken

- Every German building in Finland gone, Finland clear at 71.7 s (3:13
  on the countdown). The owner: good work.
- Then two faults: the Starport's key was read too soon after the
  depots (the SCV's build menu still showed) and counted as landed, so
  Russia's Starport was never attacked and the Barracks (waiting for that
  attack) never landed; and the Command Center's pick missed, the
  floating Starport stayed selected and its bottom-right button (Land)
  was pressed: "Select Location" over Oslo from 77 s on.
- The owner's recording after Finland: every key to Murmansk (155, 10)
  and at Russia's Starport (63-65 s); depots by Arkhangelsk in rounds
  from 68 s; the Barracks down at 104 s; the Command Center by Kiruna
  (141, 9) at 114 s, then the Starport; Dropships from it.
- Now: Esc twice before every lift and landing; a building counts as
  down only after its landing was tried and two reads a moment apart
  agree; the army attacks Russia's Starport first, then Norway's tries
  to land there; an SCV from the depots' place repairs the Barracks
  once it is down (the owner); the Command Center lands by Kiruna at
  (141, 9) first.

## Trial 51 (build afef924): late again

- The owner: Finland must be taken by about 63 s (3:25), or the German
  army comes; it did, at about 70 s, and wiped Norway's army out (the
  turrets stood till 132 s). Ignore Denmark's marines.
- Keyed 7-19.5 s (with Denmark's), the Factory and Engineering Bay lifts
  held the attack on the Finland spot back to 30.4 s, and the stage gaps
  added 16 s.
- Now: Denmark (tiles 80-95, 60-75) left out; the Factory and the
  Engineering Bay lifted after the army's stages; stage gaps 6, 2, 2, 3 s;
  with the bunkers down the keys share the four turrets out (each starts
  on a different one; turrets do not shoot men on foot).

## Trial 52 (build 5f80f28, the folder zip)

- Finland clear at 69 s (late: the Factory and Engineering Bay lifts at
  45-47 s, and the smallest key alone on the last turret); the German army
  came by 120 s.
- The Barracks, floating at (139, 33) from 25 s, was shot by the west
  bunker down to 60 of 1000, could not land there, landed at (144, 37)
  at 120 s after clicks on spot after spot.
- Russia's Starport was destroyed by about 150 s, but our marines stood on
  its spot: "You can't land there" every 8 s to the end.
- No depot: the click at Arkhangelsk picked marines, and four depots
  queued with Shift in one order.
- The owner: move the units off before the Starport lands; just land
  the Barracks at (149, 39), not many clicks; ten depots by Arkhangelsk,
  as in their recording.
- Now: the Shetland lifts after Finland is clear; with the bunkers down the
  keys split into two groups at the two ends of the turrets; the
  Barracks waits at (143, 28), out of the bunkers' reach, moves over
  (149, 39) once they are down, and lands there with one click (again
  only after 20 s); the army steps aside to (148, 16) 4 s before each
  Starport landing; depots one an order every 6 s, the SCVs boxed and
  checked by B, on spots a depot's width apart, ten in all.

## The repository owner's plan for Norway after the opening

- Norway can do all of these: defend the UK, help on the eastern front,
  help in the Balkans, drop on Spain, drop on France, drop on northern
  Germany.
- Its main job, in most games: the eastern front or the Balkans, with
  Russia (wherever Russia's hits go). The others are situational.
- Opening chat line: "AF Norway AI v0.01". Allies' orders: "@N ...".

- Situational jobs start both ways: Norway sees the need itself and
  types its plan in the allied chat, and a player can always override it
  with "@N ...".
- The map's German invasion of Norway: Norway goes home to defend,
  unless a player overrides it with "@N ...".
- Northern Germany drops go to Kiel.

## Build plan

Step 2 (v0.01, the opening) is in `bot/norway.py`; the app has a Russia
or Norway choice (remembered in country.txt beside the lessons). Norway
reuses the Russia bot's camera, clicks, building picks, chat and minimap
reading from `bot/trial.py`, so Russia's play is unchanged (step 1 is
done by that reuse for now; a fuller split can follow). Keys: Barracks
6, Starport 7, Command Center 8 while they fly. Not yet seen in a real
game: the Land button (taken to be the lifted building's bottom-right
button), the Dropship's U then a minimap click, the SCVs' depots, and
the attack on Russia's Starport.

1. The parts Russia and Norway share split out of bot/trial.py; a
   Russia or Norway choice in the app. Russia plays exactly as before.
2. Norway v0.01: the opening (chat line, buildings lifted, Shetland drop
   with the starting Dropship, Finland cleared and the Barracks landed by
   the Heavy Industry before 3:25, Russia's Murmansk Starport destroyed
   and Norway's landed on its Control Tower, Factory and Engineering Bay
   to Shetland, Command Center to Kiruna, depots in the far north-east).
3. Norway v0.02: marines and Dropships, drops with Russia's hits (east
   front or Balkans, from Russia's "gone east" / "gone balks").
4. Norway v0.03: the situational jobs (UK, Spain, France, Kiel, home
   defence), its plan typed in chat, and "@N ..." orders.

## Trial 53

- Finland clear at 69.8 s (the last turret, 141,45, came last). Still over
  the 63 s goal.
- The SCVs walked to Arkhangelsk straight through German Finland and were
  lost. Now they wait by the Norwegian military camp (126,17) and go on
  once Finland is clear. Depots start 25 s after that.
- Landings failed with "you can't land there". Now the bot hovers first and
  reads the outline: green means clear, red means something is in the way.
  On red it moves the spot a tile at a time (up to 2 tiles) until it is
  green. If it stays red it does not click (picture "<label>-red" saved).
  Depots use the same check.
- Starport (the owner): its green footprint must line up with the Control
  Tower's outline, which is a light green box. The bot finds that box and
  puts the Starport's middle 2 tiles left of the box's left side and 1.5
  tiles above its bottom. It is never moved off that spot, and it lands
  only when the outline is all green.
- The colour thresholds are guesses, not tuned on real pictures yet. They
  should be tuned from the next recording.

## Trial 54

- Finland clear at 69.6 s (countdown 3:16).
- The landings still went in over red. The footprint is a dim, see-through
  tint: green is about (28, 90, 20), red about (100, 40, 25), and grass
  (29, 34, 16). The bright-colour thresholds never matched, so the bot saw
  "no outline" and clicked anyway. Now the tint is measured over the
  building's footprint (4 x 3, depot 3 x 2). If any square is red, it does
  not land there. If no footprint is seen, it never clicks. Checked against
  the real pictures (tests/data).
- The marines shot at the Control Tower, and the Starport landing was over
  it too. Russia's Starport stood 3 tiles left of the map data's spot, so
  attack and landing now aim there (PORT_SHIFT). Russia's Starport was left
  burning and was never destroyed.
- The light green box (the owner's recording, frame 172) is a thin, bright
  green line, 4 x 3 tiles, drawn exactly where the Starport must land to
  take the tower. The tower is just right of it. The bot finds the pair of
  lines 3 tiles apart and 4 tiles apart nearest the spot, and centres the
  Starport on it.
