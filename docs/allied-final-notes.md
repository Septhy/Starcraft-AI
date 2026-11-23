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

## Seventh trial

It stopped at 72 s, in the middle of the first hit: a box was dragged
across the bot's own status window, which took StarCraft out of front,
and the safety check halted it. The window is now hidden during play.
Up to then: orders to the starting army done by 46 s with air on keys
9 and 0, mass at 58 s, 0.9 s per box (was 1.3), 9 of 61 boxes empty.

## North or south for the second hit (`fronts.py`, 34 replays)

The repository owner: the second hit is not always the Balkans;
sometimes Berlin again is much better.

In the replays (26 Russia games of 8 minutes or more) Russia's first
real push into the Balkans comes anywhere from minute 0 to minute 17.
The clearest pattern is the Axis: counting Italy's and Germany's orders
into the Balkans in minutes 2 to 5,

- with 140 or more such orders, Russia goes south early, by minute 2
  to 4 (11 of 12 games);
- with fewer, Russia mostly keeps hitting Berlin and Poland until
  minute 5 to 9 or later (9 of 14 games).

So the choice depends on seeing the Axis in the Balkans, which the bot
cannot do yet. Until it can, it hits Berlin twice, then Romania.

## Russia players in the 34 replays

qororo98 5 games (36, 17, 4, 1, 0 min); penny[eef] 2 (9, 5);
STC-Goliath 5; zapda 3; 1939-iknockoutz 3; Teia 3; WestKronos 2;
danger[eef] 2; alysaliufan 2; and one each for Exo001, rocky1242,
DaeDroy[EEF], unit[u], 1939-Lurker, PosingasMe, Harrison000.

## Eighth trial: a full run among idle computer players

The repository owner filled the other slots with computer players that
do nothing. So this is not a real game, but the map's triggers ran and
the minimap showed every player.

- Four hits completed. 0.66 s per box; 25 of 238 boxes empty.
- The first hit took from 55 s to 131 s to send: the key groups left in
  2.5 s, then 85 more orders over four sweeps of the massing place.
- Money was not being spent: 3,750 minerals at 1:00 and 5,500 at 6:00,
  with supply at 154 to 200 of 200.
- The repository owner: hits after the first two are too small; the
  mass must be much bigger before it goes.

## Seeing other players (the live minimap among other players)

Our own side is drawn bright green; every other player in their own
colour (Germany red, Italy blue, Spain yellow, UK teal, France purple,
Norway orange, the computer white). `Watch.others` reads them.

Germany starts with troops in the Balkans: about 190 minimap pixels of
Axis colour in the box of tiles (126, 106) to (172, 142) at the very
start. So "the Axis is in the Balkans" has to be measured as growth
over that starting count.

## Russia players in 48 replays (47 different games)

qororo98 7 games (36, 17, 10, 4, 1, 0, 0 min); penny[eef] 2 (9, 5);
1939-iknockoutz 6; STC-Goliath 6; WestKronos 5; zapda 3; Teia 3; and
one or two each for ten others.

## Ninth trial, among idle computer players

Worse than the one before, as the repository owner said. Supply sat at
its limit (200 of 200, at one point 212) with 8,800 minerals unspent,
and the bot went round the barracks every 55 s all the same. The mass
for the later hits stayed small (81 and 55 minimap pixels after 200 s)
because nothing new could be trained, while reinforcements the map had
given Russia stood idle all over the east.

The repository owner:

- Do not train at the population limit.
- After the first hit Russia gets reinforcements at Moscow, Finland
  (once), Stalingrad and Siberia. They have to be brought in.
- Watching the minimap is not enough. The bot has to look at the game
  screen itself and check how well its attacks are doing.

What the bot does about it now:

- `eyes/numbers.py` reads the supply number from the screen; at the
  limit the bot skips the barracks, and below it visits only as many
  as there is room for.
- While building a mass it sends idle groups anywhere at home to the
  massing place (`gather_idle`), which picks up the reinforcements
  wherever they appear.
- `Battle` samples our colour and the Axis colour at the target after
  a hit and calls it winning, losing or unclear; after a losing hit the
  next mass has to be half as big again. It also moves the view to the
  fight a few times and keeps a picture.

Still missing: reading the fight on the main screen itself (which
units, whose, how hurt). The battle check is made from the minimap.

## The general: Claude looks at the fight (bot/general.py)

The repository owner agreed to add an LLM that looks at the game
screen, using Claude, and asked that it be responsive.

- While a mass builds, the bot goes round about once every three
  seconds: it looks at where the last hit went, takes a screenshot, and
  offers it to the general with a few lines of status.
- The general runs in the background. It takes the newest screenshot
  whenever it has finished the last one, and answers with: what it
  sees, how the fight is going, an action (keep massing, hit now, pull
  back) and a target (Berlin, Romania, Belgrade). Advice older than 25
  seconds is dropped.
- The fast rules do not wait for it: Axis colour at the massing place
  recalls the number-key groups at once.
- Model `claude-opus-5-5` at low effort, a 1280 x 720 JPEG per look,
  the fixed instructions cached. It can be changed with the
  STARCRAFT_BOT_MODEL setting. Spending is counted from each reply and
  capped at 3 dollars a run.
- The key is typed into the app, encrypted with Windows' own data
  protection and kept in the user's AppData folder. It is not in the
  log or the zips.
- Not yet tried against the real API or a real game.

## Tenth trial: first run with the general, among idle computer players

- The general worked: 37 looks, each answered in 2 to 5 seconds, about
  $0.29 in all on `claude-opus-5-5` at low effort.
- Every look was at Berlin, and every answer was "no fight, keep
  massing, Berlin": the army never got there. All five hits stalled 22
  to 28 tiles short, around Konigsberg, Warsaw and the "Germany-Invasion
  on Russia" location, and Germany's kill count went to 392 against
  ours of 10. Several hundred minimap pixels of our units stood at that
  front the whole time, holding supply at its limit.
- The repository owner: it must look at where the hits are on the
  eastern front, not at Berlin, and adjust. And Russia has to micro its
  air units and control them better.

What changed:

- `find_front` finds where our forward units meet the Axis colour, and
  `Battle` follows that front. The bot looks there, the general is
  shown that view, and the status report names the place.
- The battle's verdict is now arrived, losing, stalled, advancing or
  unclear. After a stalled or lost hit the next one needs a bigger mass
  and is aimed at the eastern-front city nearest to where it stalled
  (Konigsberg, Warsaw or Krakow), unless the general says otherwise.
  The general can now name those cities too.
- Each later hit also sends on the units standing still at the front.
- The air groups are sent to the front every 8 seconds while a mass
  builds, so they stay over the fight. This is not yet micro.

## How qororo98 handles the air (3 games)

- Battlecruisers sit on one key (0 in these games): 3 to 7 orders a
  minute, mostly plain moves, a few attack-moves, a Yamato now and then.
- One other key (5) gets 24 to 40 orders a minute, almost all plain
  moves and Hold Position: a group worked by hand constantly. What is
  on that key is not known from the replay.

## Russia players in 55 replays (52 different games)

qororo98 7 games, penny[eef] 2, as before. New names: kor-boy (2 games,
10 and 13 minutes, over 200 commands a minute), 1939-RavExel, and more
from STC-Goliath and danger[eef] (one of 46 minutes).

## Whose games to use, and whose not

- Learn mostly from qororo98; penny[eef] is also very good.
- Do not use kor-boy's games as examples (the repository owner).
- Do not use the repository owner's own games as examples of good play.

## The general commands (second version of bot/general.py)

The repository owner asked that the LLM control units, act during a
hit, read and write chat, change the opening, and remember.

- Asked all through the game: `consult` is called from the waiting
  loops, between views while a hit is being sent, and during the first
  orders; it looks at the front (or the massing place before any hit)
  at most every 3.5 seconds.
- Orders to number-key groups: attack-move or move to a named place,
  the front or the mass; hold; attack a point in the picture; Yamato a
  point in the picture. Later hits put their newest groups on keys 1 to
  8 so the general has current groups to command.
- Chat: it reads chat in the screenshot and may type one line to the
  allies (Ctrl+Enter; Shift+Enter is all players), at most every 45 seconds.
- The opening: it is asked at the very start, and its target becomes
  the first hit's target; "hit now" can launch the first hit early.
  The scout, the training and the massing stay fixed.
- Memory: each request carries its last eight answers and its running
  notes; at the end of a game, or when stopped, it writes lessons that
  are saved on the PC (`bot/memory.py`) and shown to it next game.
- The app has a model choice: Opus 5.5 (default), Sonnet 5.5, Haiku
  5.5. The spending cap is 5 dollars a run.
- None of this has been tried against the real API or a real game yet.
  Unknowns: how
  well a model can point at things in a shrunken screenshot; whether
  typing reaches the chat box.

## Playing like qororo98 and penny[eef]

Asked to train the bot to play like them. There are five usable games
(qororo98 36, 17 and 10 minutes; penny[eef] 9 and 5), far too few to
train a model on. Their habits were measured and written in instead:
into the general's instructions, and into the bot's default plan.

Measured (attack waves are bursts of eight or more attack-moves):

- First wave at 37 to 51 s, at Berlin, in all five games.
- More waves north through the first three minutes, 50 to 90 s apart.
- A turn south at about 3:35 to 5:25 in all four games of nine minutes
  or more: the bunkers and Italian army near Romania, then Romania,
  Serbia, 40 or more attack orders in under a minute.
- Back north (Warsaw, Krakow, Konigsberg, the approach to Berlin) from
  about 7:30 to 11:00; south again from about 13:00 in the longest game.
- Marines queued in bursts of 30 to 70 roughly every three minutes.
- About four number-key assignments a minute, all game.
- Buildings lifted from the first seconds (4 to 7 s in qororo98's
  games) and again through the game.

In the bot: the first hit may leave from 45 s; `PLAN` sends later hits
south from 3:30 to 7:30 and from 12:00 to 16:00, north otherwise,
unless the general chooses differently.

## Commands per minute

Counted from the tenth trial's log the way the game counts them
(selections, hotkeys, orders, training, key assignments): 124 a minute
on average, about 150 in the busy minutes, from about 207 raw mouse
and key actions a minute. An earlier guess of 60 to 90 was too low.
The players in the replays give 100 to 250.

The repository owner wants more. The pauses between actions were cut
by about a third (a click from about 90 ms to 60, a box drag from
about 290 ms to 190, shorter waits after each order). The game reads
input once a frame, 24 times a second, so much shorter pauses risk
dropped inputs; if the next run shows more empty boxes or missed
orders, lengthen them again.

## Eleventh trial, among idle computer players

- The general did not run: the API refused the key (AuthenticationError)
  on the first look, with Haiku 5.5 chosen. Nothing was spent. The run
  was the rules alone.
- Commands a minute, counted as before: 153, 139, 141, 121, 107, 139,
  121, 130. No clear gain yet from the shorter pauses.
- Hits: Berlin, Berlin, Romania (by the plan, at 5:00), Berlin. The
  Romania hit arrived, and then 160 to 240 minimap pixels of troops
  stood there idle for the rest of the run.
- The repository owner: generally better, but the second hit was bad.
  The troops idled in Romania. Russia has to check the front for idle
  units.

What changed:

- `advance_front`: every five seconds while a mass builds, troops of
  the current hit that are forward, standing still and not in contact
  with the enemy are sent on: to the next objective if the target is
  taken (Romania, then the factory at Belgrade, then Serbia, then
  Athens; an eastern-front city, then Berlin), or at the same target
  again if they stopped short. Troops holding somewhere else are left.
- The computer player (white), which holds the Balkans, now counts as
  an enemy when judging contact at the front.
- A refused key stops the general at once and is said plainly in the
  log; the app checks a key when it is entered and says whether it
  works.

The road south (the repository owner): Belgrade, then roughly toward
the Netherlands. In the bot: Romania, Factory 7 (Belgrade), Hungary,
Munich, Frankfurt, Amsterdam. The cities in between are the bot's own
choice of stepping stones and have not been confirmed.

## Twelfth trial: the first run with the general working (Haiku 5.5)

- 66 looks, each answered in about 2 s, about $0.03 in all.
- Hits went out at about 111, 124, 85, 89 and 58 men: far too small.
  The general said "hit now" when the mass crossed its threshold and
  "keep massing" a look later; the bot remembered the first and hit
  with whatever was there. Before the first hit it also ordered the
  ground groups at Berlin on its own, several times.
- After Krakow and Warsaw were reached, the idle troops there were
  sent on at Berlin a few groups at a time.
- The barracks sent to Warsaw for the tax never left: it was told to
  fly 0.3 s after lifting off, before it could take orders, and hung
  near the massing place for the rest of the game.

The repository owner: the second hit was really bad. Having taken
Warsaw it should have been taxing the two cities. The idle troops
should not have been made to attack: that is not a hit. A hit is at
least 140 men and should vary from 160 to 300; the bot must check its
mass is large enough, and if not hold the troops in reserve.

What changed:

- `MIN_HIT` 160, `WANT_HIT` 200, `BIG_HIT` 260 after a lost or stalled
  hit, in minimap pixels of units, taken as men. No hit below the
  minimum, whoever asks. There is no longer a time after which it hits
  anyway.
- A hit's strength is the mass plus the troops standing forward short
  of their objective, who go in with it. A new hit also needs at least
  40 fresh men at the massing place.
- Troops standing forward go on by themselves only as a hit-sized
  body. Fewer hold where they are, in reserve.
- The general's orders to ground groups are limited to the front, the
  mass, hold, or a point. It is told the hit-size rule.
- A lifted building is given 2.6 s to leave the ground and its order
  twice. When a hit reaches Warsaw, Konigsberg, Krakow or Romania, a
  building is flown there for the tax.
- The southern road continues from the farthest point reached.
- The mass count is the middle of the last five looks.

Not known: how well pixels stand for men. Supply could give a better
count; it is read but not yet used for this.

The recorder now covers a whole game: every 3 s the minimap and the
top strip, every 30 s the whole screen, for up to 45 minutes.

## Counting men on the game screen, and the two cities

The repository owner: do not count minimap pixels; look at the units
on the in-game screen. And the two cities to tax are Warsaw and
Krakow.

- `live.selected_count` reads how many units the game shows as
  selected, from the framed pictures in the bottom panel (0 to 12).
  It is right on all eleven real pictures with a known count.
- `count_men` cuts the ground into fixed patches, boxes each patch the
  troops stand on, and adds up the selection counts; a patch that comes
  back with the full twelve is cut in four and counted again. Fixed
  patches mean nobody is counted twice from overlapping views.
- A hit is decided on that count: at least 140 men, normally 180, 240
  after a lost or stalled hit. The minimap is used only to tell when a
  count is worth making, and to estimate the reserve standing forward
  from the men-per-pixel ratio of the last count.
- In the pretend game the count came to about half the minimap figure
  (54 men for 127 pixels, 89 for 164), so the earlier pixel thresholds
  were sending much smaller hits than their numbers suggested.
- Taking Warsaw or Krakow now sends a building to each of them.

Not yet tried on the real game: counting takes a box per patch, so a
count of a large mass may take ten seconds or more.

## Fuller boxes

The repository owner: the box selection is poor; it usually does not
manage to select twelve units.

The hit's boxes used to be a fixed grid over the view, whatever stood
in each square. `select_full` now sizes each box from how many men a
minimap pixel has been holding, reads how many units the game actually
selected, and if that is well short of twelve draws a bigger box round
more of the neighbours, up to twice. In the pretend game its boxes
hold 10 to 11 units on average and the first hit takes about a third
fewer orders. The log now reports units per box. Not yet tried on the
real game.

## Live recordings 3 and 4 (user playing Italy, real opponents)

- Both came from the old recorder (first 5-6 minutes only, full
  pictures every 3 s). Italy's view, so little on Russia.
- A paused game greys the whole screen, minimap included. The bot now
  waits while the minimap has no colour (hands/win.py `paused`),
  checked against recording 4: only its four paused pictures match.
- Allied chat: Ctrl+Enter is allies, Shift+Enter is everyone. The user
  wants Russia to set allied chat under Messages at the start; the bot
  uses Ctrl+Enter for every line instead. No picture of the Messages
  window yet.

## Trial 13 (real opponents): froze after the first hit

- First hit left 64-102 s (orders spread over 36 s) and was destroyed
  near the German border: supply 190 -> 119 by 147 s.
- Spawns and training took supply back to 204/200 by 236 s, all of it
  standing in a tight crowd at the massing place. The bot had counted
  18 men there at 121 s and never counted again: a crowd covers hardly
  more minimap pixels than a few men, so the "it has grown" test never
  fired. It believed 39 men, needed 140, could not train (supply), and
  did nothing for four minutes.
- Fix: count again every 20 s (10 s at the supply limit) whatever the
  minimap says; at the supply limit the least hit (140) is enough;
  idle groups at a place are tried again after 30 s (they were tried
  once per mass, so later spawns at the same spots were left).
- Still open: the first hit is sent too slowly and too thin against a
  defended border.

## Trial 14: ran the build from before the recount fix

- No count between 107 s and 517 s, so this was the older exe. Idle
  from about 220 s to 400 s (only the air group moved), as in trial 13.
- The count at 477-517 s took 40 s of boxes with no orders (the user
  saw "selection boxes that do nothing") and said 550 men with supply
  at 243: a box selects men who only overlap its edge, and small boxes
  count them several times.
- Fix: each box's figure is scaled by box area over (box + one man)
  area; counting stops once it has reached what the hit needs.

## Trial 15 (fixed build): no freeze, four hits

- Counts ran every 20-40 s (23, 78, 226 men...), hits at 54 s, 217 s,
  409 s, 487 s. No long idle stretch. One count read 0 with 82 pixels.
- A hit took 45-65 s from decision to "sent": the general was asked
  between views and its "ground attack_move front" order sent the
  groups just put on the number keys to the old front, not the hit's
  target; four sweeps re-boxed men already ordered (54 groups for 269
  men). Now: no consult inside a hit, two sweeps.
- "Reached" fired seconds after a hit was sent (Krakow 4 s, Factory 7
  10 s, Hungary 5 s): any ten of our pixels within 12 of the target
  counted. Now within 6.
- The army was recalled 30 s after hit 2 for Axis colour at the mass.
  Now a hit is not called back for 45 s after it is sent.
- Germany's ground did not shrink in nine minutes: hits reach the
  border and Poland, not Berlin.
- Trial 15, user's view: "it keeps making selection boxes and does
  nothing with them". Those are the counts: 625 boxes in the run, only
  296 followed by an order; one count took 77 boxes. A full box is now
  sampled (two quarters, then one quarter of a full quarter: at most 5
  boxes a patch, was up to 21), and counts come every 30 s (15 s at
  the supply limit). The Axis slots were computers.
- User: do not count with boxes at all; tell roughly at a glance.
  count_men/count_box removed. men_at_mass: supply figure (top right)
  less 0.3 men per minimap pixel of ours away from the mass (measured:
  18 men/57 px, 23/81, 41/143 when spread out), capped at 4 men per
  mass pixel. At full supply with troops at the mass it is taken as a
  hit. No supply figure readable: mass pixels as before.

## Battle behaviour added (user: "it must be capable of doing these")

- fight(): a hit judged "losing" (under 30% of its peak forward) is
  broken off once: survivors near the front and the air walk back to
  the mass (right-click, not attack). Otherwise the air attack-moves to
  the middle of the enemy colour within 10 minimap pixels of our front.
- defend_home(): 10 more Axis pixels inside Russia (tiles x>=154,
  y<=105) than at the start, in one body of 6+, sends the troops
  standing at the mass and the air to meet it, at most every 20 s.
- Ally requests and focus fire on a named target stay with the general
  (Claude reads the chat and can give attack_point orders).
- Not done: retreating single hurt units, rule-based focus fire. All of
  this is untested against opponents that move.

## Trial 16: clumps left out of hits; clog at Romania

- User: bodies idling on the minimap were not in the hit; in the
  Balkans it checked the front and did nothing; Romania clogged.
- Log: six hits; four of the last five aimed at Romania again (the
  general kept choosing it though it was held), so troops piled up
  there. Idle troops at a held city were sent on at most 14 small
  groups a time and only if hit-sized; the hit's own troops stopped
  short were left unless hit-sized.
- Now: a chosen target that is already reached moves on down the road
  (st.reached); troops of the hit stopped short are sent at it again
  whatever their number (20+ pixels); up to 24 groups a pass; a hit
  also takes every still body anywhere on the map (push_front), not
  only the massing place and the front.
- The glance estimate swung (0, 145, 253, 0): supply was often
  unreadable and "elsewhere" pixels were huge with troops packed at
  Romania. Now floored at one man a mass pixel, and the last supply
  reading is kept for 30 s. Still rough.
- First hit lost again: supply 190 -> 124 by 103 s against computers.

## Trial 17 and the two-hour game

- User: the computer opponents do nothing, so losses come from
  Germany's standing defences. Hit 3 took supply from 190 to 28.
- The glance said "240 men" with supply at 136 (the one-man-a-pixel
  floor): hit 2 went under-strength. men_at_mass is now the larger of
  supply less spread-out men and the mass's share of our pixels, never
  more than the supply.
- "Bodies elsewhere" worked: 18, 20, 29 bodies joined hits 2-4.
- TRIAL_SECONDS 480 -> 7200 (user: two hours). The plan alternates
  fronts every 4.5 min after the studied 21 min. The bot stops when
  the minimap is gone for 8 looks. After 40 pictures it keeps one per
  45 s at lower quality (expect roughly 200 pictures a full game).
  Tests keep 480 s (tests/conftest.py).
- The general's $5 cap: Haiku is about $0.20/hour; a dearer model may
  hit the cap in a long game and the general then stops.

## Team chat: announcing hits and obeying the allies (bot/team.py)

The repository owner's rules:
- 30 s before every hit type "gone east in 30 seconds" / "gone balks in
  30 seconds"; at 30 s type "gone east" / "gone balks" and send it.
- Orange, teal or purple (Norway, UK, France) saying "no", "don't",
  "stop", "wait", "halt" or the like: wait 2 minutes of the game clock,
  then restart the 30 s. A named wait is obeyed exactly. While waiting
  the army keeps training and gathering.
- "go east" / "go balks": the hit goes there; "go east in 2": wait 2
  minutes, then hit east. Allies' orders override the bot's own plan.
  After the hit, back to the usual preparation.
- The game clock is the one at the BOTTOM of the screen (console,
  around x 990-1075, y 820-838): it counts up in real seconds from
  00:00 and stops when paused. The countdown at the top runs about 1.47
  times faster (game seconds): a 5:00 round is about 200 real seconds,
  so round_timer() in trial.py is wrong and should not be trusted.
- eyes/clock.py reads the bottom clock from templates built from 47
  pictures of trial 18 (all read right; checked on trials 15 and 17).
- Chat is read by Claude Haiku from the strip (0,360)-(1300,660) when
  new white-with-shadow text appears there (at most every 1.5 s, cap
  $2 a game). It returns lines (logged as "chat [colour] text") and
  orders of fixed kinds only; orders from any colour but teal, purple
  or orange are dropped in code. No key: hits are still announced but
  answers cannot be read. Never tested on real chat yet.
- The first hit is announced at 0:30 and goes at about 1:00.

## Fixes 1 and 4 after trial 18

- "Inside Russia" (defend_home) is now tiles x >= 170, y < 98: east of
  the massing place, north of the Black Sea. Odessa (164,104), Romania
  and the Polish border are out: Axis there was always there and only
  showed once our troops came near.
- Round countdown: 1.488 game seconds per real second (least squares on
  47 pairs of bottom clock and top countdown, max error 1.1 s). A round
  is about 201.6 real seconds; tax at countdown 2:00 is about 121 real
  seconds into each round. round_timer() and until_tax() take the
  bottom clock; Claude's status now gives both clocks and the seconds
  to the next tax.

## Trial 19: no hit after the first

- First hit lost; build_big_mass then set need = 240 on every pass
  ("last hit losing"), after the supply-full rule had set it to 140.
  Supply was full at 235 with 166-191 men at the mass: never ready,
  never hit again for six minutes. The supply-full rule now comes last.
  Test: test_at_full_supply_a_lost_hit_does_not_stop_the_next (fails on
  the old code).
- Chat worked: announcements typed and seen in brown; the reader logged
  map messages. Ally orders not tested (no human ally).
- "Axis inside Russia" fired near Moscow (Capital City 13, 164 px) at
  133 s and Smolensk (136 px) at 365 s against idle computers. Cause
  unknown: map triggers do spawn Axis units (the Norway invasion
  message), or the minimap pings (dark green boxes) confuse the colour
  reading. Not fixed.

## Trial 20, and taxing Krakow, Romania and Factory 7

- Trial 20: hits went again after the first (supply-full rule worked:
  hits at 4:58 and 8:15), but every Berlin hit was lost.
- Clumps left idle (user): gather_idle took only bodies of 9+ minimap
  pixels at home, 4 a pass. Now every still body of 3+ pixels anywhere
  (forward ones too), 8 a pass, farthest first; left alone: the hit
  being fought (in_battle), troops in contact, tax guards, the Middle
  East spawn. Small bodies standing exactly where something of ours
  stood at the start are skipped (buildings hidden under units at the
  start): empty boxes in the fake game 62 -> 30 of about 330.
- At a hit, bodies behind the mass (standing or walking) are ordered
  before the mass sweeps, bodies forward of it after.
- Tax (user rules): Krakow 200, Romania 300 and Factory 7 always get a
  floated building when no enemies are within 6 minimap pixels; with a
  few enemies (4-40 px) a detachment of 12 is sent first (every 120 s
  at most per city), more than 40 is left to hits. Factory 7: sets off
  at countdown 1:00, must arrive before the next round's 3:00 (about
  121 real s); buildings able to reach it are kept for it. Never a
  barracks or a command centre (fly_building refuses them); 2 buildings
  per city per game at most. With no factory, starport or engineering
  bay left: the nearest command centre makes an SCV (S), rallies it to
  the city, and it builds a supply depot (B, S, click around the
  beacon, Esc). Warsaw and Konigsberg flights now take the nearest
  spare building, never the Smolensk barracks.
- Guesses to check in a real game: lifted building speed 0.75 tiles/s
  (Krakow about 2 minutes away), SCV 2 tiles/s, that a floated
  building shows on the minimap as our colour at the city (presence
  check), that the CC trains SCVs on this map, and S/B/S hotkeys.

## Trial 21: clumps left behind, no tax, "gone balks" that went east

- Clumps (user: visible on the minimap after a few hits, should have
  joined the hit). Causes found in the log:
  - Tax detachments to Krakow every 2 minutes (11 in the game); troops
    near a city with a recent detachment were "guarding" and never
    fetched, and with a new detachment every 2 minutes Krakow was
    always guarded. Now: guards are kept 90 s (or while their building
    is still flying in), detachments at most every 5 minutes, only
    against light enemy (4-20 px), and only after the second hit.
  - Survivors of a lost or stalled hit counted as "the battle" and were
    only moved once 20+ pixels of them stood idle. Now a lost or stalled
    hit's troops are fetched back to the mass; a live hit's idle troops
    are sent on from 6 pixels.
  - Everything near the Middle East spawn point was ignored all game.
    Now only for the first 150 s.
  - A body ordered three times that never moves is left alone, with a
    picture "stuck" taken of it, to learn what it is.
- Tax: nothing happened before 6:40, then Krakow had enemies and got
  detachments. Now (user): efforts start after the second hit, now and
  then (every 45 s look); a building follows each later hit, east to
  Krakow, balks to Romania. Factory 7 is checked on every pass: its
  moment (countdown 1:00 to 0:00) lasts only about 40 real seconds and
  a 45 s look could miss it. The few buildings that can reach Factory 7
  in time are kept for it, by the Warsaw/Konigsberg flights too.
- "gone balks" at Frankfurt went east: the general chose Factory 7,
  which was marked reached, so the road walked on to Frankfurt; a
  fresh hit from Smolensk to Frankfurt marches through Poland. Now a
  new Balkans hit always goes to Romania, and is carried on down the
  road from there.

## The clumps left behind (confirmed with the user)

- What the user meant: after each hit, clumps stayed at and around the
  massing place, just west of Smolensk. Confirmed in trials 20 and 21:
  about 66-73 men still counted there seconds after a hit left.
- Cause: select_full sized boxes from the army estimate (men per
  minimap pixel), which takes packed men for spread out; a box covered
  20-40 men, the game picked 12, and sweep_mass marked the whole box
  done. Boxes averaged 10-11 units (mostly full). Only 2 sweeps.
- Fix: box size is learnt from the boxes (full -> next 40% smaller;
  short -> bigger); a full box marks only its nearest half done; up to
  4 sweeps (3 at the first hit), stopping when under 10% is left.
  Fake test, 170 packed men: left behind 134 -> 0; boxes 40 -> 79.

## Talking to Russia: "@R", "@Russ", "@Russia"

- User: allies must start a message with @R, @Russ or @Russia for the
  bot to take it as meant for it. Checked in code (team.addressed), not
  only by Claude: an order whose words do not start with the tag is
  dropped. "@Rus", "@Romania", "rus go" are not orders.
- "@R hit east" with no time: hit east right now ("gone east", no 30 s
  countdown), even if a 30 s announcement is running. "@R hit east in
  2": announce 30 s before, hit at 2 minutes. "@R go" with no front:
  Russia's own front. Stop words as before, with the tag.
- Who can override: any of the three allies; the latest order wins
  (a stop cancels a pending go, a go cancels a wait). Enemy colours
  never count. The Claude adviser cannot hit through an ally's wait.

## After Berlin: Paris, then Madrid

- User: once a hit has cleared Berlin, the army goes on to Paris and
  then Madrid. NEXT: Berlin 1000 -> Paris 500 -> Madrid 1000.
- "Cleared": troops are at Berlin and fewer than 8 enemy minimap pixels
  are within 8 of it. Reached but not cleared: the troops there keep
  attacking Berlin first (logged once). Same rule on the Balkan road.
- Moving on still needs a hit-sized body; a handful holds the city.
- Troops left at a city taken earlier on the road (Berlin when the push
  is at Paris) follow the push instead of being fetched home.
- User: Russia must always go through Berlin. Every new eastern hit is
  sent to Berlin (east_next), even once Berlin and Paris are taken; it
  is carried on to Paris and Madrid from Berlin once there and cleared.
  A chosen target is never moved past Berlin. Announced "gone east".
- User: the Balkan road also goes on to Paris and Madrid, after the
  Netherlands: Romania, Factory 7, Hungary, Munich, Frankfurt,
  Amsterdam, Paris, Madrid. New Balkan hits still start at Romania, so
  Paris is only reached from Berlin or from Amsterdam.

## "@R mass at <place>"

- User: allies may move Russia's massing place anywhere its troops can
  walk; anywhere else Russia types "I can't mass there".
- bot/places.py: plain city names from the map (the map's 222
  locations less trigger areas: ~100 cities), other names (Belgrade ->
  Serbia 100, Kiev -> Ukraine 200, Gibraltar -> Gilbritar 100, ...).
  data/land.png: land/sea per drawn-minimap pixel, made from a start
  picture (averaged over 7x7, sea bluer than red); flood fill from
  Smolensk. Not walkable: Britain, Ireland, Shetland, Faeroe,
  America/Halifax/Newfoundland, Corsica, Sardinia, Sicily, Crete.
  Mountains and cliffs are not known: walkable means joined by land.
- trial.MASS is now set by move_mass; replies "massing at Warsaw",
  "I can't mass there", "I can't find that place"; "@R mass home" goes
  back to Smolensk. Every game starts at Smolensk.
- Not handled: what counts as "at home" and "forward" is measured
  toward Berlin from the massing place, so a massing place west of
  Berlin would confuse gathering and the front.

## "@R hit <city>", "@R status", "@R reset"

- "@R hit Warsaw": the mass is sent at that city, now ("gone Warsaw"),
  or at a time given ("@R hit Warsaw in 2": "gone Warsaw in 30
  seconds" then "gone Warsaw"). Any city the troops can walk to;
  otherwise "I can't hit there" / "I can't find that place". From the
  city the usual road carries on (Berlin -> Paris and so on).
- "@R status": one line, at most 60 characters, with the time of the
  next hit on the game clock: "185/200 | Smolensk | 120/140 men, east
  | hit est. 10:50". Own plan: (need - men) / growth over the last 90 s,
  plus the 30 s warning; at full supply or enough men, now + 30 s; not
  growing: "hit est. ?". After an ally's wait: the later of the wait's
  end + 30 s and the army's own estimate ("waiting | hit est. 11:30").
  "gone balks | hit est. 10:30", "hit Warsaw | hit est. 12:00".
- "@R reset": drops waits, pending hits and announcements, masses at
  Smolensk again; reply "reset: massing at Smolensk, usual plan".
- All from teal, purple or orange only, tag required, as before.
- Status is now two chat lines: "Pop 185/200. Mass: Smolensk." and
  "Plan: 120/140 men, east. Next hit est. 10:50." (or "Plan: waiting.",
  "Plan: gone balks.", "Next hit est. unknown.").
- When the massing place moves (mass at, mass home, reset), the army
  at the old place is swept over as one (relocate_mass: the hit's
  sweep, up to 4 passes, boxes learnt) instead of by the idle pickup,
  which left some behind (its "stuck" rule). Fake test: 170 packed at
  Smolensk, all ordered to Warsaw, none left.

## The air fleet (user's rules)

- Map names: Scout = "Light Fighter" (unit 70, Russia has 6), BC =
  "Battle ship" (12, Russia has 3), "Heavy Defensive Artillery" = unit
  25 (Edmund Duke, siege mode), Russia's 4 at map pixels (5684,2489)
  Smolensk, (5231,1701), (6796,1665) Moscow, (7458,2443).
- Fleet key: one Heavy Artillery + up to 11 Scouts; full -> next key
  (keys 9, then 0), each with its own Heavy Artillery. Built at the
  very start, before anything moves: click the artillery, Ctrl+key;
  click each Scout, Shift+key (the user's way of adding). Clicks try a
  few spots until the command card shows the unit picked.
- Battlecruisers go with the ground army (ordered to the mass at the
  start, swept into hits).
- The fleet is ordered only as whole keys. First order at 40 s (the two
  Middle East scouts are in it and must arrive first), to fleet_spot():
  16 tiles east, 4 north of the mass, out of the mass sweeps and the
  idle pickup. Recall and retreat send it there; hits and fight() as
  before.
- New Scouts (from the map's triggers): each factory Russia holds
  (Factory 1 @167,55, Factory 2 @226,91, Factory 3 @203,43; "Heavy
  Industry" buildings) makes 2 Scouts, 2 Heavy Tanks and 2 Veteran
  Infantry at every tax (countdown 2:00); 12 Scouts appear at "ZMoscow
  Air" (201,41) at 1800 and 2800 game seconds (about 20:10 and 31:20 on
  the clock). A Wraith built is swapped for a Scout (bot builds none).
- collect_new_scouts: 3 game s after each tax, click each factory's
  middle (Scouts hover over the building, where ground units cannot
  stand; a click that shows the Move button is a Scout), Ctrl+click
  (every Scout on screen), Shift+fleet key, then fly them to the fleet.
  Moscow: box the location, trim to the room (Shift+click on panel
  pictures), two passes, 3 s apart. A pair that does not fit starts the
  next key instead of being split. Keys 9, 0, then 8 and 7 (taken from
  the ground keys). The spawn spots are kept out of the idle pickup for
  30 game s (Moscow until fetched).
- Untested in a real game: whether the click on the factory middle
  picks a Scout, and Ctrl+click selecting only Scouts.
- Telling Scouts from ground (user: separate the unit types in the
  spawns accurately; key and park the air first). At the start the bot
  learns what a Scout looks like in the bottom panel from Russia's own
  starting Scouts: one alone (picture and name, PANEL_ONE) and a group
  (a framed picture, via Ctrl+click on the starting pair). Every pick
  at a spawn is checked against these before Shift+key: one picture
  that differs (mean colour difference >= 22) and nothing is added
  ("not-scouts" picture kept).
- Air first: each spawn point is tried on the next passes (3 times at
  most) while it is kept from the idle pickup, so the ground there
  goes to the mass only after the Scouts are keyed and flying to the
  fleet. Moscow now uses click + Ctrl+click (only Scouts) instead of a
  box; later passes plain clicks for those left. Scouts go to a key
  with room for them all, else a new key; twelve fill a new key and
  the twelfth joins a key with room.
