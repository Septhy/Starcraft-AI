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

## The repository owner's plan for Norway after the opening

- Norway can do all of these: defend the UK, help on the eastern front,
  help in the Balkans, drop on Spain, drop on France, drop on northern
  Germany.
- Its main job, in most games: the eastern front or the Balkans, with
  Russia (wherever Russia's hits go). The others are situational.
- Opening chat line: "AF Norway AI v0.01". Allies' orders: "@N ...".

## Open questions for the repository owner

- What makes each situational job start: an ally's "@N ..." order only,
  or also what Norway sees (the UK invaded, an opening in Spain, France
  or northern Germany)?
- Home defence when the map's German invasion of Norway comes (the
  samples went home at 15-20 min): always, never, or only when asked?
- Where "northern Germany" drops go (Kiel, Hamburg, the coast?).
