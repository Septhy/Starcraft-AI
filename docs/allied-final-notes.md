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
