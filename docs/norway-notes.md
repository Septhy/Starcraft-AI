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
