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

## The fleet in a hit (user's rules)

- At a hit the fleet keys get a plain move (stays stacked) to a point
  6 tiles ahead of the mass toward the target; then every 8 s
  steer_fleet puts it, as one, over the middle of our own forward
  troops at the front (attack-move there), never over the enemy.
- More than 3 enemy to one Scout round that spot: it steps back 4 tiles
  toward the mass, up to 4 times. Enemy counted on the GAME SCREEN
  (user): look at the spot, count patches of Germany red (R>200, G<60,
  B<60) and Italy blue (B>170, R<50, G<80) within 7 tiles, one man per
  patch or per 150 pixels of a big patch; health bars (one cell tall),
  the kills list and Russia's own buildings (red lamps; positions from
  the map) left out; yellow dropped (Russia's Scouts are gold on
  screen). On trial pictures: a German marine fight read 31; quiet
  views 0 (78 of 96). Every 5th "too many" keeps a picture
  "fleet-too-many" for tuning MAN_COLOUR.
- The hit fades (under half its peak forward): the fleet is pulled back
  (move) to fleet_spot and waits for the next hit; the ground's own
  retreat still comes at under 30%.

## "@R bring air"

- From teal (UK), orange (Norway) or purple (France): the whole fleet
  (every fleet key) goes by attack-move to where that ally's air is
  thickest. Their air: their colour over water on the minimap (land
  from data/land.png); else their colour that moved between two looks
  a second apart (buildings do not move), then a look at it on the game
  screen (picture "ally-air" kept).
- The way: Dijkstra over minimap pixels (about 0.2 s): cost 1 within 8
  pixels of our side's units and buildings (friendly ground, out of the
  fog), 4 in the fog, +6 per enemy pixel within 4 (enemy buildings stay
  shown in the fog; turrets cannot be told from other buildings on the
  minimap, so all are avoided). Stops every 25 pixels; first stop
  attack-move, the rest queued with Shift+click.
- User: the fleet stays with the ally's air even through Russia's own
  hits and planned hits; only "@R return air" (or another "@R bring
  air") moves it. "@R reset" is for massing and hitting only and leaves
  the air alone. "@Reset" is NOT taken (user: other countries' bots
  will play together later and have their own tags). While it is away, own_fleet_keys() is
  empty: hits, recalls, retreats, defence and the general's orders do
  not use the fleet keys.
  Replies: "air on its way to you", "I can't find your air", "I have no
  air". Whether Shift+click after A queues in Remastered is untested.
- User: while the fleet is with an ally, check on it every 8 s and keep
  massing. follow_ally_air (called in both massing loops, between the
  other steps): find their air again; moved 6+ minimap pixels -> send
  the fleet after it along the safe way; else attack-move on the same
  spot; not seen -> the fleet waits (logged after 3 misses). No checks
  while a hit is being sent (30-60 s).

## After the user's demo game (air, parking, tax only)

The user played Russia to show air control, parking and taxing, and
said to learn nothing else from that game. The user's answers: the
Battlecruiser on their air key was there by accident (keys stay Scouts
plus one Heavy Artillery), and tax efforts still start after the
second hit (the demo only shows how).

- Battlecruiser misclicks (trial 23): learn_scout learns the Scout's
  panel picture from the starting Scout farthest from every
  Battlecruiser, and the Battlecruiser's from the one farthest from
  every Scout. picked_are_scouts refuses a single unit that looks
  nearer the Battlecruiser than the Scout. click_scout checks every
  click; build_fleet uses it.
- New Scouts by colour: Russia's Scouts are gold on screen.
  gold_mask/gold_on_screen find gold patches (tuned on the demo's
  frames; the kills list, the countdown and the yellow buttons over the
  minimap left out). scouts_on_top clicks the gold near the spawn point
  first, then the old spots, and checks each pick (trial 23: the
  factory's middle held Heavy Tanks).
- Parking: the fleet waits about tile (181, 65), north-east of
  Smolensk, as in the demo (FLEET_PARK 21, -11 tiles from the mass).
- Tax: Krakow gets the factory nearest it (165, 49), Romania the
  starport nearest it (190, 110) (TAX_BUILDING); those two are kept
  from Warsaw's flight and from Factory 7 (the Engineering Bay at
  162, 58 still reaches Factory 7 from 1:00). They stay floating over
  the beacon. A building follows a hit only into a city that is clear
  or just taken (our troops 3 to 1 against the enemy left there:
  city_clear); otherwise the tax rounds send it later. Our own troops
  at a city no longer count as "something there already".
- "@R bring air": each ally's air mass (ALLY_AIR): orange 8 Wraiths,
  purple 11 Scouts, teal 22 Wraiths. Places where their colour is over
  water or moving are looked at on the game screen, and their Wraiths
  or Scouts counted by the model (ChatEars.count_air, Haiku, told not
  to count dropships, ground units or buildings). A place with their
  mass is taken at once, else the one with the most; none: "I can't
  find your air". While following, near where their air last was, no
  count. Without an API key: their biggest group, as before.
- Stuck: a body only counts as stuck if it did not get smaller after an
  order (SHRANK 2 minimap pixels); a big spawn leaving a dozen at a
  time is not stuck (trial 23).
- Balkans choke (recording 10e35650): the way from Odessa into Romania
  (CHOKE, 7 minimap pixels either side). Troops standing in it or in
  Romania are never gathered back to the mass; every 10 s clear_choke
  sends them on to the next stop of the Balkan road past every city
  taken (Romania itself while the enemy holds it; Romania counts as
  taken once our troops stand there and see no enemy). Before a new
  hit to the Balkans, the choke is cleared first. land.png shows no
  narrowing there (the choke is terrain), so the zone is a line.
- Opening (user's Messaging screenshots): at the very start, "AF
  Russia AI v0.01" typed with Enter (to everyone), then the Messaging
  button over the minimap (225, 748), "Send to allies" (597, 314),
  checked by its yellow dot, and Accept (778, 590). The window is
  recognised by the blue ring of its first choice and its dark blue
  inside. After that, chat lines go with plain Enter; if the window
  could not be set (picture "messaging-failed"), Ctrl+Enter as before.

## Trials 24 and 25 (the user's two recordings after the demo changes)

- Tax: pressing "L" never lifted a building (pictures "flight-Krakow",
  "flight-Romania": still on the ground, Lift Off showing). Now the
  Lift Off button (bottom right of the card, 1862, 1022) is clicked; a
  building in the air shows Move as its first button, like units: that
  is the check (pictures from the user's demo and trial 24 in
  tests/data/card_lifted.png, card_grounded.png). Not lifted: not sent,
  picture "lift-failed", tried again later (twice per building).
- Scouts refused: the framed pictures are laid out by how many are
  selected (two one above the other, three as two and one, seven as
  four and three; live.frame_box). The check looked in the 12-unit
  places, so the second Scout was an empty slot. It now also compares
  outlines (bright green/yellow/red: health colour does not matter),
  not colours. Factory spawn spots are kept from ground boxes until
  that round's Scouts are on a key.
- The general (Claude) no longer orders the fleet keys ("9 move mass"
  a dozen times in trial 24 undid the parking and fight orders).
- Blood: a bright red patch in a spread of darker red with no grey
  metal round it is blood, not an enemy (trails of blood counted 57).
- "@R bring air": a place that cannot be counted is never taken (trial
  25 went to a place with 0 Wraiths); while following, their air is
  counted again every third check (about 24 s).
- Choke: the head of the column is ordered first (user); on the Balkan
  road advance_front orders front to back too.
- Gathering: bodies sent to the mass in the last 60 s, standing on
  their way there, are left to walk (crowds look still a second apart);
  crowds of 12+ minimap pixels are boxed all over at once (sweep with a
  7-pixel reach); a fresh look before each box, and no box where the
  troops have gone.
- Supply unreadable: the last reading is used, however old.
- Forward troops count toward the next hit only if it goes the same
  way (trial 25: a Balkans hit with 28 men).
- No troops forward, or too few at the front: the front is cleared and
  the fleet parks, instead of hanging over empty ground.
- Looked at and left: the sweeps already centre on the troops (the
  "sweep" picture is taken before the view moves, which misled); an
  enemy picked by a click gets no order, as every pick is checked.
- The Messaging button over the minimap was missing in trial 24 and
  there in trial 25: it depends on the kind of game.

## Trial 26 (backup branch backup/2026-11-24-b before these changes)

- Hits (user): while a hit is ready or announced, the mass is put on
  keys 1-7 (twelve to a key, back first, Scouts left out, refreshed
  every 30 s; key_mass). At "go": 1 attack, 2 attack ... 7, the fleet
  at once, then the rest boxed as before. Boxing the whole mass took
  60-80 s in trial 26 and hits arrived in pieces.
- Balkans (user): a hit to Romania attacks Romania, then goes on,
  queued (Shift), to tile (143, 145) toward Serbia (send_at).
- Overlapping hits: "supply full: 140 is enough" only with 150+
  minimap pixels at the mass; no new hit within 90 s of the last unless
  it was lost or arrived; an announced hit no longer ready is called
  off ("hold, regrouping"); an ally's order still goes.
- Idle waits: the hit size wanted is capped at what the supply limit
  leaves for the mass (0.9 x (limit - men away from the mass)).
- Targets: the general chooses only the front. East is Berlin, the
  Balkans Romania (trial 26: "Warsaw" after "gone east"). The "aim at
  the city nearest a stalled front" rule is gone.
- Air: Scouts are taken out of every box (outline check, Shift+click
  their pictures; drop_scouts). The fleet goes with the hit at once, 14
  tiles ahead of the mass (past its boxes), is steered every 4 s, also
  while the hit is being sent (fleet_tick in the sweeps), and parks
  only when no troops are at the front after 60 s, not when the hit
  merely shrinks. Scouts' way from the factories to the parking spot
  does not cross the mass (checked), so no detour.
- Tax: buildings are clicked on their lower half first (Scouts
  hovering over the Airport were clicked); the building is checked
  selected before each Lift Off. Factory 7 (user, timing kept): only
  once Belgrade is cleared; a starport that can arrive in time, else an
  SCV builds a depot by the Heavy Industry there.
- Factory spawns walk out 6 tiles toward the mass first (plain move),
  then attack-move on, queued (tanks "stuck" at Factory 2).
- A box that picks up a building makes the next box smaller.

## Trial 27 and the user's latest replays

- Keying the mass on 1-7 before a hit made it worse (trial 27): taken
  out; hits box the mass as before. The fleet still goes with the hit.
- The Middle East scouts' box keeps its Scouts (select_group air=True):
  trial 27 emptied it and no scout went.
- From the one replay with a strong player as Russia, the user chose:
  - Krakow: the factory lands at tile (134, 94) (Land button, then a
    click on the ground there); no factory within 120 s of flight: an
    SCV builds a depot there (TAX_LAND).
  - Tax from the first hit on, when there is time (not while a hit is
    announced).
  - Balkans hits go on past Romania to (150, 146).
  - Unchanged: barracks never moved; no Hold Position; one fleet over
    the army avoiding marines; no hotkey hits for now.

## The keys version (StarcraftTrialKeys.exe)

- A second app for the user to try: trial.HIT_STYLE = "keys". When a
  hit is announced, the mass is put on keys 1-7 (twelve a key, Scouts
  left out) and walked out into a wide line 7 tiles ahead of the mass,
  across the way to the target, 4 tiles between keys (spread_mass). At
  "go" each key attacks its own point along the target's front, keeping
  its place in the line (keyed_attack); the fleet goes with it; the rest
  of the mass is boxed as usual. Keys older than 60 s are set again.
- StarcraftTrial.exe is unchanged: it boxes the whole mass.
- Keys version, after trial 28 (compared with the replays: the strong
  player's 5-second bursts were 3-11 groups, the bot's 9-10; but the
  bot's full sweep after the keys took 60-90 s):
  - Quick tail: after the keys and the fleet, one pass of at most 5
    boxes over the front of the mass (front first, no air steering in
    between); no far bodies behind or forward of the mass.
  - For 60 s after a hit that is not being lost, gathered troops go
    straight to its front (send_at) instead of to the mass.
  - Between rounds of marines the crowd at the mass is boxed from its
    thickest part (up to 6 boxes) and walked to spots 4 tiles apart
    round the mass point (spread_at_mass); not while a hit is announced.
- The usual version spreads the mass too (the repository owner): after
  each round of marines, up to 6 boxes from the thickest part are walked
  to spots 8 tiles apart over an area 24 tiles across round the mass
  point (SPREAD_WIDE, -12/-4/4/12 tiles each way). MASS_RADIUS is now 15
  minimap pixels so all of it still counts as the mass (the parked
  fleet, 21 tiles east, stays outside).
- Keys version revised after the user's own recording (from 0:46 on
  the game clock): while massing, every 6 s a dozen from the left of
  the mass go on the next key (1-7) and are moved aside into their place
  in a line across the way to the next target (key_step). At the hit:
  3 boxes from the back of the mass first (keyed groups left out), then
  every key attacks, keeping its place in the line, then the rest of the
  mass is boxed back to front (no far bodies; they come on as
  reinforcements). The keys version no longer spreads between rounds of
  marines: it spreads as it keys. The quick 5-box tail is gone.
- The rel version (StarcraftTrialRel.exe, HIT_STYLE "rel"): the keys
  version, but each keyed group's place is set by where the mass stands
  from the target (the repository owner): mass to the top right of the
  target (more than 8 tiles higher) -> an up-and-down line 8 tiles to
  the mass's left; to the bottom right -> 8 tiles to its right; level
  with it -> alternately left and right. Groups 4 tiles apart. From
  Smolensk, Berlin and Romania are both "top right" (line on the left);
  Konigsberg is level (both sides).
- Rally points (the repository owner, all versions): each barracks
  rallies to its own spot round the mass point, on a 3 x 3 grid 8 tiles
  apart (an area 16 tiles across; RALLY_SPOTS, rally_spot), instead of
  all to the one point. Set at every round of marines as before.
- Groups brought in (spawns, leftovers) go each to its own spot round
  the mass (the repository owner, all versions): taking turns through a
  4 x 4 grid 8 tiles apart, 24 tiles across (SPREAD_WIDE, spawn_spot),
  between the barracks' rally spots (also 8 tiles apart). A crowd swept
  in goes to one spot.
- Fixed: troops that went on past Romania to (150, 146) counted as idle
  and were walked back to the mass; that area now belongs to a Balkans
  hit (in_battle, advance_front).
- The two trial versions are renamed for what they do: the keys version
  is StarcraftTrialLineAhead.exe (bot/app_line_ahead.py), the rel
  version StarcraftTrialLineBeside.exe (bot/app_line_beside.py). The
  old StarcraftTrialKeys.exe and StarcraftTrialRel.exe are removed from
  the release. Inside the code they are still HIT_STYLE "keys" and "rel".

## The three recordings compared (normal, line ahead, line beside)

- Second hit, "gone" to last group: normal 85 s, line ahead 57 s (5 of
  7 keys), line beside 36 s (7 keys). No hit won in any version.
- The bot clicked its air a lot (normal: 6.5 fleet selections a minute,
  28 of 39 while a hit was being sent). Now, all versions:
  - No air steering while a hit is being sent; the fleet gets its first
    order once most of the hit has gone (the repository owner).
  - Steering looked at every 8 s (was 4); a new order only if the spot
    moved 3+ tiles (or too many enemy there); the enemy round a fleet
    that has not moved is counted again only every 16 s.
- Faster hits, all versions: no fetching of far bodies behind or forward
  of the mass during a hit (they are gathered as usual afterwards), a
  0.6 s settle between the two looks of a sweep (was 1.2), 0.4 s
  between sweeps (was 1.5), the box's own picture reused for the Scout
  check (one look fewer a box). Pretend game: 49 -> 40 s and 52 -> 26 s.
- Krakow must land (the repository owner): from 5 s after it should
  have arrived, every 20 s, the bot clicks round the landing spot; a
  building still in the air (Move, and the yellow corner button) is
  landed again, a few tiles to one side in turn; on the ground (no
  Move, the corner button) it is done (check_landed, corner_button).
- Fixed: build_big_mass could end with no men counted when time was
  already up ("massed" unset).
- A fourth app, StarcraftTrialBackFirst.exe (HIT_STYLE "back7", the
  repository owner): the line ahead version, but at the hit seven
  groups (BACK_FORMATIONS) are boxed and sent from the back of the mass
  before the keys attack, then the rest.
- The user chose the normal version (StarcraftTrial.exe). The line
  ahead, line beside and back first apps are no longer built, and their
  downloads are removed from the release; their code stays (HIT_STYLE
  "keys", "rel", "back7"; bot/app_line_ahead.py, app_line_beside.py,
  app_back_first.py) in case they are wanted again.

## New ally orders

- "@R tax <city>" (tax_order, tax_order_step): one try at any city
  Russia can walk to. Enemies there: a detachment of up to twelve
  (send_guard) secures it, two minutes at most. Then an SCV is made at
  Moscow's command centre (it cannot yet tell an SCV already standing
  at Moscow from other units), walks to 5 tiles below the beacon, is
  picked by a click (one unit selected), builds a depot at the first
  spot next to the beacon that takes it (the money drops), then walks
  back to Moscow, queued. A standing depot: "<city> taxed", the
  detachment walks back to within 6 tiles of the mass point. Anything
  failing: "couldn't tax <city>", not tried again until asked again.
  Replies: "taxing <city>", "I can't find that place", "I can't reach
  <city>", "still taxing <city>".
- "@R upgrade" (upgrade_order, upgrade_step): infantry weapons (W) at
  one Engineering Bay, infantry armor (A) at the other, each when the
  minerals (read off the top of the screen; gas is always the same on
  this map) cover it: 100, 175, 250 for levels 1-3. Not enough: "I'll
  upgrade infantry when I have the resources", and it is done once there
  is (looked at every 15 s). Started: "upgrading infantry weapons and
  armor". The Engineering Bays are no longer floated for tax.

## Trial 30: the new orders reworked

- Tax money: each city an ally asks to tax keeps 150 minerals back (an
  SCV and a depot) until its depot is placed; marines never eat into it
  (trial 30: they spent everything, the SCV never came; a picture shows
  0 minerals and 1,650 gas, so gas is NOT always the same as minerals).
  Several cities may be taxed at once (st.tax_jobs); one that the money
  cannot cover with the others is answered "not enough money to tax
  <city>: ask me next tax turn". The chat reader makes one tax order
  per city named.
- Upgrades go on to 3/3: each level as soon as minerals (less the tax
  money) and gas (read when it can be) cover it, the next level of one
  upgrade no sooner than 240 s after the last; a bay that does not take
  it, the other is tried (trial 30: armor never started at the second
  bay). Both at 3 and finished: "all upgrades completed", and the bays
  are left alone.
- "@R bring air" redone (the repository owner): Russia types "ping the
  map" and watches every look for new yellow on the minimap (10 s, then
  "can't find ping"). At the ping it looks at the ground: the ally's air
  there (counted by the model, 2+): "following your air", the fleet goes
  by the safe way and follows it, attack-moving; mostly enemy (4+):
  "attacking at your ping", and once the place is clear "area cleared,
  air coming back"; nothing: "I can't find your air". Every check-up
  counts the planes left on the fleet keys; none: "my air is gone", no
  more following. The mass cycle goes on throughout. The ping colour and
  size are a guess: no picture of a ping yet.
- The app has a "Recommended settings" button (bot/settings_view.py):
  a page laid out like the game's Options > Video screen, with the
  repository owner's settings (Windowed (Fullscreen), gamma 6th of 8,
  FPS cap off, SD filter Sharp, HD Graphics, Smooth Unit Turning and
  Shadow Stacking on, the rest off) and Windows at 1920 x 1080, 100%
  scale. A picture of it: docs/recommended-settings.png.
- The ping, from the repository owner's recording (tests/data/ping_*.png):
  a hollow yellow square on the minimap about 40 pixels across with a
  thick edge, after four yellow bars sweep in from the map's edges.
  find_ping takes only new yellow (not there when Russia asked), joined
  up: a square-ish outline (8-45 px a side, mostly on its edge, 24+
  px), or, before it, two upright and two lying bars, whose middle is
  near the ping; the bars wait up to 2 s for the square, which is exact.
  Spain's moving units (small blobs of new yellow) are not taken.

## Trial 31

- "@R bring air": at the ping the screen showed about twenty teal Wraiths,
  but the model's count came back empty, so Russia said "I can't find your
  air". Now every allied Wraith and Scout (teal, purple and orange
  together) is counted, 5 is enough to follow, a count by colour on the
  screen stands in when the model cannot count (or counts fewer), and the
  reason the model gave nothing is logged.
- Tax by SCV: the SCV walked to the city first and was then looked for by
  the beacon; it was lost and looked for in the same place again and
  again. Now it waits by the command centre and is ordered to build the
  depot as soon as it is out. Not seen at the second look: "couldn't tax
  <city>".
- New "@R commands": lists every order, a line each.

## Trial 32

- The game was played with the build before the trial 31 fixes: the ping
  log still read "? teal planes", which the new code cannot write, and
  "@R commands" was not known. The app now shows its build in the window
  title and the log's first lines, so this can be checked.
- "@R commands" is also read straight from the chat line, not only from
  the model's orders; it is typed once even if both pass it on.
- The colour count of allied planes is teal only and greener than the
  beacons' cyan (a beacon and fires were counted as planes).
- "@R tax Warsaw": Warsaw was held by about twenty Axis after a stalled
  hit; seven men were sent, lost, and two minutes later "couldn't tax".
  Now a city held that strongly (or with fewer than 8 men to send) gets
  no detachment: the ally is told "Axis hold Warsaw: I'll tax it once
  it's clear", and the depot follows once a hit clears it (up to 3
  minutes).
- The repository owner: a tax city is clear when no enemy is there at
  all; the detachment then walks back at once, it need not stay while
  the SCV comes.

## Trial 33

- Right build; "@R commands" and "@R bring air" worked.
- Tax orders: an SCV was never found by the command centre (Serbia,
  Krakow): its rally point was set on the minimap, a tile or two off the
  spot then looked at. Now it is set on the screen, and picked with the
  same view; supply full makes it wait (up to 3 minutes) instead.
- "@R tax romania" waited out a hit, sent its men 105 s later and gave
  up 22 s after: the detachment's time now counts from when it is sent.
- The repository owner: a city Russia can see (something of ours there)
  is looked at on the screen; no enemy, and the SCV comes at once with
  no detachment. Only a city no one of ours sees gets a detachment, to
  look.
- Ground troops not brought to the mass: once a spot by a factory had
  been "stuck", it was left alone all game, though the factories make
  tanks and men there every round. A stuck spot is now tried again
  after 150 s.
- Scouts: "every fleet key is full" from 20 minutes on: the count of
  Scouts per key never went down when they died. Now the keys are
  counted again when they look full.
- The repository owner's pictures of building a depot: the Engineer
  (SCV) comes out beside the Command Outpost; B opens its build menu
  (only an Engineer has one, so a marine picked by mistake is let go);
  S then "Select Location" with a green or red ghost; once placed, the
  Engineer's own buttons are back. A depot costs 100 minerals and 100
  gas on this map, so a tax order now checks the gas too.

## "@R bring air" with a fleet record (the repository owner)

- At the ping the allies' air is written down: FLEET RECORD with the
  game time, the units (how many of which kind, by owner, read by the
  model; teal by colour without it) and the position (minimap, tile,
  nearest place). A picture is kept.
- Every 8 seconds the fleet is looked for near its last record; roughly
  the same (total within 30%, same main owner and kind): our air
  follows 5 tiles behind it and a new record is written.
- Not there: searched at once, not on the timer: the allies' groups on
  the minimap near the last record, then the camera round it (10, 20
  and 32 tiles, eight ways); our air does not move until it is found.
  Found: our air goes there by the safe way and a new record is written.
  Not found in 10 seconds: "Lost the fleet", the air parks, the mass
  cycle goes on.

## Trial 34

- Every dogfight ended after 2 s, "the fleet is out of sight": it looked
  for the fleet where it was going, but the fleet was still on its way
  from its parking spot. Now it looks where the fleet should be by then
  (from where it set off, at about 3.5 tiles a second), where it is
  going and where it set off from, in turn, for up to 15 s.
- The repository owner: no marines are made while the air is still out
  with a hit; they start again once the air is back (parked) or lost, or
  150 s after the hit at the latest (a stalled hit can keep it out).
- Spreading the mass boxed the same spot six times in a row: the men
  just sent had not yet walked off and the thickest part was still
  there. The ground round each box is now left alone for the round. In
  the hit's sweeps, the far half of a full box is boxed again only once
  the rest of the view is done, not straight away.
- The Heavy Artillery picture check was wrong in play ("no Heavy
  Artillery", then "0 Scouts" just after adding six): it is off; the keys
  are counted again by units less one, and a few pictures of pressed
  keys are kept to tune it.
- At the end, 8 groups went to meet "Axis inside Russia" west of Moscow;
  no picture showed why. The enemy is now looked at again 1.5 s later
  (a picture kept) before anyone is sent.
