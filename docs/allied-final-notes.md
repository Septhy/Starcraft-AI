# WWII Euro - AF 4.0 ("Allied Final"): notes from replays

Worked out from fifteen replays of the same map version. A replay stores
the whole map, so the map's rules can be read without the map file.

## Reading replays

Replays are read with [screp](https://github.com/icza/screp):

    screp -cmds -map r.rep > r.json      # players and every command
    screp -dumpMapData -outfile m.chk r.rep   # the map itself

Then the scripts in `replay_tools/`:

- `overview.py r.json ...`: players, length, command counts, chat
- `chk.py m.chk summary|strings`: the map's teams and all its text
- `slots.py m.chk <name to leave out> r.json ...`: how each slot played
- `player.py <name> r.json ...`: what one player did
- `playbook.py m.chk <slot> <name to leave out> r.json ...`: a slot's
  habits round by round, with army targets as named places

Replays are not kept in this repository: they hold other people's
names and chat.

## The map

- 256 x 192 tiles, Use Map Settings, about 300 triggers.
- Money: cities pay tax to whoever holds them, once per 5 minute round.
- Many timed events: reinforcements, invasions, D-Day and so on.

| Slot | Country | Side | Starts (tile) | What players mostly make |
| --- | --- | --- | --- | --- |
| 0 | Germany | Axis | 98, 87 | marines, wraiths, battlecruisers, bunkers |
| 1 | Italy | Axis | 92, 135 | marines, bunkers, carrier fighters |
| 7 | Spain | Axis | 22, 145 | marines, dropships, firebats |
| 2 | UK | Allies | 51, 81 | wraiths, a few battlecruisers |
| 3 | France | Allies | 51, 113 | varies: vultures, wraiths or marines |
| 4 | Norway | Allies | 97, 50 | marines, dropships |
| 5 | Russia | Allies | 209, 49 | marines in large numbers |
| 6 | Turkey and the east | computer | 182, 147 | |

Countries are matched to slots by start position and the team names.

- Players give 100 to 230 commands a minute.
- Most orders are attack-moves; drops (unload) matter for Norway,
  Spain and the UK.
- Most slots make their first units at about 2 minutes.

## Examples so far

Fifteen replays; twelve are full games (17 to 66 minutes) and three
ended in the first minutes. The repository owner asked that their own
games not be used as examples of good play. That leaves 2 full games
for Italy, 11 for Spain, 11 for France and 12 for each other country.
The replays do not record which side won.

## Russia (12 games)

Russia makes almost nothing but marines, 70 to 120 per 5 minute round.
It does not send them to the front as they appear. It gathers them west
of Smolensk (around tiles 152 to 176, 64 to 80; the rally points in the
replays are there) and sends them west together, in waves: the attack
orders come in bursts a few minutes apart. `waves.py` shows this.

Where the waves go, by the map's place names (a city's number is its
tax):

- 0 to 5 min: the German invasion area, Konigsberg and Warsaw.
- 5 to 15 min: Warsaw, Krakow, Romania.
- 15 to 25 min: Krakow, Warsaw, Romania, Serbia, then Prague.
- after 25 min: Prague, Krakow, Warsaw, on toward Cologne.

## First trial on the real game (solo game, 1920 x 1080)

- Simulated mouse and keys reach the game.
- Barracks are found from the map data: all 8 selected, 5 on the first
  click, 3 after one or two more tries nearby.
- M queues marines; a box plus A plus a minimap click attack-moves.
- Problems seen: the box drag picked up only 3 of about 10 marines
  (the drag started too fast); a few screen captures came back black.
- A solo game ends the map's triggers, and gives only the starting
  1,000 minerals: 20 marines.

## Second trial

- Right-clicking the minimap with a barracks selected sets its rally
  point; the gathering spot (tile 160, 74) is open ground.
- 20 marines gathered there and were sent on in two box selections;
  they reached Warsaw.

## Russia's opening, from the replays and the repository owner

- Russia starts with about 175 units that can move, spread over the
  whole east (96 marines, 42 hero marines, tanks, vultures, ships).
  Players bring all of them into the first mass attack.
- It has to be fast: players give their first orders within seconds,
  20 to 70 orders into the gathering area in the first two minutes,
  and most send their first attack west inside the first minute.

## Third trial, and corrections from the repository owner

- The whole opening ran on the real game, but slowly: orders to the
  starting army took 191 s and the wave 210 s, and about 60% of its
  boxes were empty.
- The mass should be complete about 1:30 to 2:00 into the game, with
  most of the units, not all.
- The mass goes to Berlin (place "Berlin 1000", tile 100, 89), not
  Warsaw.

## How the bot sees (eyes/live.py)

- The live minimap is drawn two pixels lower than its frame: fitted to
  Russia's known starting positions, 99% of them land on our colour
  with left 14, top 819, width 288, height 217.
- A unit is drawn as a block about three pixels across. Buildings are
  bigger blocks. `Watch` learns the buildings from the first picture
  of the game and reports our colour anywhere else as units.
- On the third trial's pictures the count of unit pixels at the
  massing place goes 6, 38, 101, ... 190 as the army arrives, then
  down to 4 as the wave leaves.

## Fourth trial

- On the real game: marines started at all 8 barracks by 11 s, 32
  groups ordered to the massing place by 60 s, the mass judged
  complete at 90 s, the wave of 30 groups sent by 147 s, and the army
  arrived at Berlin. 28 of 100 boxes were empty.
- The wave went front first and strung out into a line on the minimap.
  The repository owner: Russia selects from the back to the front, so
  the army arrives as a wall and not a "conga line". The wave now goes
  back to front.

## Whose Russia to learn from

The repository owner: focus mostly on qororo98. Two of the fifteen
replays have qororo98 as Russia: one full game (36 minutes) and one
that ended after a minute. `onegame.py` prints a game minute by minute.

What the full game shows:

- All ten number-key groups are in use from the first minute, and
  re-assigned through the game (10 to 20 times each). Hotkey presses
  run at 30 to 180 a minute. The bot uses none yet.
- First minute: about 48 train commands and the first orders toward
  Smolensk (the massing area).
- Second minute (1:00 to 2:00): the attack is already going: 45 move
  orders at Konigsberg, attack-moves at Berlin and the German invasion
  area. That matches "mass complete by 1:30 to 2:00".
- In the fight, plain right-click moves outnumber attack-moves several
  times over: units are pulled back and pushed forward by hand.
- Minutes 4 to 8: a second front in the south, at Romania and Odessa.
- Marines are trained in bursts right after each tax round (about
  minutes 5, 9 to 10, 12, 14 to 15, ...), not steadily.

## Fifth trial, and more from the repository owner

- Back-to-front wave on the real game: 41 groups sent in 65 s; 11 of
  its 52 boxes were empty.
- Russia gets a large spawn in the Middle East, and those units go into
  the hit too. Russia also hits several times in a game, and puts its
  air units on number keys and controls them.

## The Middle East spawn (from the map's triggers; `trig.py`)

Trigger 22, Russia only, fires once: when Russia has at least one unit
(any unit that is not a building) at the location "Russians in Middle
East" (tile 218, 128), Russia gets 32 marines there and 4,000 minerals.
Any unit will do; players send a scout because it flies. Two of
Russia's scouts start at tiles (224, 75) and (224, 78).

A solo game ends the map's triggers ("Mission completed"), so this
cannot be tested alone. It needs a game with at least one opponent.

## qororo98's opening (4 Russia games in 20 replays)

- 2 s: a unit is sent to the Middle East spot (3 of 4 games).
- First minute: 13 to 16 number-key groups assigned; all ten keys used.
- Massing place: about tile (160 to 163, 76 to 78).
- 47 to 59 s: the first attack-moves at Berlin. The hit is sent with the
  number keys: key, attack, a point at Berlin, ten times in about eight
  seconds, each group to a slightly different point (tiles 102 to 106,
  84 to 94), plus boxes for the rest.
- Two of the groups are fought by hand afterwards and fire Yamato, so
  they hold the battlecruisers.
- From about 1:30 on: new marines are boxed, sent forward and put on
  keys again, and Berlin is attacked again around 1:55. Hits keep
  coming through the game.

## Sixth trial (a game with a second player, so triggers ran)

- Scout sent at 2 s; the Middle East marines appeared and were sent to
  the mass. Number keys 1 to 8 assigned; no air group got a key.
- Mass at 64 s. The eight key groups were sent in 2.5 s; the rest took
  until 131 s. Three more hits followed, each finding new marines.
- 21 of 183 boxes empty; about 1.3 s per box.
- The repository owner: still too many empty selections and too slow;
  later hits should also go to the Balkans through Romania; Russia
  should contest the tax of cities such as Warsaw and Odessa; the tax
  turn is when the round timer reaches 2:00. penny[eef] is also a very
  good Russia to learn from.

## Tax (from the map's triggers)

Each city pays when the countdown timer is at 2:00 (120 s), to the
player who has at least one building at the city's location while the
other sides have none there. Rounds are 5 minutes, so the first tax
falls at 3:00 into the game.

- Odessa (tile 164, 103): Russia starts with a barracks inside the
  location (163, 99), so it holds Odessa's tax from the start.
- Warsaw (130, 91): no Russian building. qororo98 lifts the Smolensk
  barracks (173, 80) at about 70 s and flies it west. A lifted barracks
  moves under a tile a second, so Warsaw is about a minute's flight.
- Russia's liftable buildings: 8 barracks, 4 starports, 2 factories,
  2 command centres, 2 engineering bays, a science facility.
- A building floating over the city counts; it does not have to land
  (the repository owner).

## Russia players in the 25 replays

qororo98: 5 games (36, 17, 4, 1 and under 1 minute). penny[eef]: 2
(9 and 5 minutes). zapda: 2 (26, 12). 1939-iknockoutz: 3 (38, 22, 17).

## Belgrade and the Balkan factory (repository owner; triggers 234, 235)

After Romania, the Balkan city that matters most is Belgrade: the
location "Factory 7" (tile 137, 129).

- Taking it: a player with at least one building at the location, while
  the opposing side has none there, is given the factory, but only
  while the round timer is at 2:00 or more: from the round's start
  (5:00) down to 2:00. Players float a building there.
- Paying out: once the timer is at 2:00 or less, the factory's owner
  gets 6 hero marines and 2 artillery pieces there, each round.

The bot's third hit goes there. It does not yet fly a building to it.
