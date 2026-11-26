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

## Open questions for the repository owner

- Is the reading above right; anything missing or in the wrong order?
- Copy the most common choices (Starport to Murmansk (154, 4), Factory
  and Engineering Bay to Shetland, Command Center to Kiruna, Barracks to
  Finland), or other spots?
- Which cities are "Finland" for the tax (Helsinki, Kiruna, Murmansk,
  Factory 10)? Which ones are taxed by a floating building, which by a
  depot?
- Why the depots in the far north-east (by "Place Artillery" and
  Arkhangelsk): supply room, or tax?
