# Improvement plan (saved for later)

(Superseded by the second part of `docs/air-overhaul-plan.md`; kept for its history.)

Where the bot stands against the strong Russia players in the replays,
as judged after trial 38 (an estimate from the logs and recordings, not a
measured comparison):

| Area | How close | Why |
|---|---|---|
| Overall plan (when, where, east or Balkans, the road to Belgrade and Amsterdam) | about 70-80% | Timings and routes come from the replays and the repository owner's rules; it reacts less to surprises. |
| Massing and sending hits | about 50-60% | Most of the army goes (40-70 boxes, 6-7 men a box); slower, and the wall is less even. |
| Economy (marines, upgrades, tax) | about 40-50% | Marines and upgrades work; the tax failed in almost every recent game. |
| Air control | about 25-35% | About 8 air orders a minute in trial 37 against 23-40 in the replays' fights; the model's target look takes 6 s. |
| Doing two things at once | about 20-30% | During the 60 s dogfight the ground gets no orders. |
| Reading the fight | about 30% | It cannot tell what shoots air (marines, turrets); it does not judge when to pull a losing hit back. |

Each step below ends with a test game and its recording, and is tuned
from it. Items marked **needs the repository owner** wait for them; the
rest can be done without.

## Step 1: Taxing that works

- Find why the SCV does not start (the "no-scv" picture added in build
  c573c66) and fix it. **Needs the repository owner: a recording with
  the "no-scv" picture if the tax fails.**
- Follow each step of a tax (SCV made, SCV at the city, depot placed,
  depot finished) and retry a failed step instead of giving up after one
  try. **Needs the repository owner: one short recording of a city taxed
  by hand (SCV built, sent, depot placed).**
- A tax report in the log: cities asked for, taxed, how long each took,
  why any failed.
- Done when every city an ally asks for is taxed within one round unless
  the enemy holds it.

## Step 2: Ground and air in turns during a hit

- Short air bursts of 2-3 s with a ground action between them (idle
  groups sent on, a stalled one re-aimed), instead of a 60 s dogfight
  that freezes the ground. The replays: most air bursts begin within 10 s
  of a ground order.
- Cheaper air looks: one camera move and one screenshot a burst.
- **Needs the repository owner: 1-2 short recordings of a fight with the
  air and the ground moved together, rough air control is fine.**
- Done when the ground keeps getting orders through the fight and the air
  still gives at least 20 orders a minute while fighting.

## Step 3: Knowing what shoots air

- Recognise enemy marines, Goliaths, missile turrets, bunkers and
  Battlecruisers. **Needs the repository owner: 3-5 close-up screenshots
  of each, in red, blue and yellow if possible, standing and moving, at
  the normal zoom.**
- Fight rules: hop away from turrets and big marine groups, shoot first
  what cannot shoot back, pull out early when the anti-air outweighs the
  fleet.
- Faster target looks: every 2-3 s instead of 6, with a faster model for
  this one job (cost shown in the log).
- Done when the air report shows fewer Scouts lost a minute of fighting.

## Step 4: Stronger hits

- A tighter wall sent faster: fewer boxes, the back of the mass moving
  first so it arrives together.
- A losing hit pulled back early instead of fed; a winning hit pushed
  straight on to the next city.
- Idle leftovers anywhere (not only the Balkans) sent on to their next
  target. **Needs the repository owner: their rules for when a hit is
  pulled back and where leftovers on the Berlin side go.**
- Done when army size, hit timing and how far each hit gets come close to
  the replays.

## Step 5: A scorecard against the replays

- A tool that reads a test game's recording and a replay and compares:
  army size and time of each hit, cities taken and taxed, air orders a
  minute and Scouts lost, time the army stood idle. Run after every test
  game. Can be built from the replays already at hand.
- **Needs the repository owner (optional): one or two more replays of
  Russia in full games.**

## For every step

- **Needs the repository owner: one test game per build with the
  recorder on, and the zip (log, pictures, inputs).**

See also `docs/air-control-plan.md` (the air plan, steps 4-7 overlap
with steps 2-3 here) and `docs/allied-final-notes.md` (every trial).
