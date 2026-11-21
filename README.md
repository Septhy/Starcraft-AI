# StarCraft micro AI

An AI that learns to win a small StarCraft fight (5 marines against 5
marines). It practises on the old StarCraft: Brood War 1.16.1, and is
meant to play later on StarCraft: Remastered by reading the screen.

## The plan

1. **Brain** (done): a small network that controls each marine. It is
   given only what a screen can show: where units are and how full
   their health bars are.
2. **Practice fight without the game** (done): a rough copy of a marine
   fight, used to test the training code.
3. **Practice on 1.16.1** (written, not yet run against the game): a
   bridge that connects the trainer to the real game.
4. **Eyes and hands for Remastered** (not started): read the screen,
   move the mouse.

## Parts

| Path | What it is |
| --- | --- |
| `scai/spec.py` | What the brain sees and what it can do |
| `scai/sim.py` | The practice fight (not StarCraft) |
| `scai/ppo.py` | The brain and how it learns |
| `scai/train.py` | Start training, or test a saved brain |
| `scai/bwapi_env.py` | The trainer's side of the link to 1.16.1 |
| `bridge/` | The game's side of the link (Java) |
| `tests/` | Tests, with a stand-in for the game link |

## Try it without the game

Needs Python 3.10 or later.

```bash
pip install -r requirements.txt
```

```bash
python -m pytest -q tests
```

```bash
python -m scai.train --env sim
```

```bash
python -m scai.train --env sim --watch brain.pt
```

## Practise on StarCraft 1.16.1 (Windows)

This part has not been run against the game yet. Expect to fix things.

1. Get StarCraft: Brood War 1.16.1 into `C:\starcraft`. It sits beside
   Remastered and does not replace it. The Java BWAPI tutorial lists
   download links (at your own risk):
   https://github.com/JavaBWAPI/Java-BWAPI-Tutorial/wiki/Setup
2. Install BWAPI 4.4.0 with its default settings:
   https://github.com/bwapi/bwapi/releases/tag/v4.4.0
   It needs the Visual C++ 2017 x86 redistributable.
3. Copy the practice map `maps/micro/m5v5_c_far.scm` from
   https://github.com/TorchCraft/TorchCraft into
   `C:\starcraft\maps\BroodWar\micro\`.
4. In `C:\starcraft\bwapi-data\bwapi.ini` set:

   ```ini
   [auto_menu]
   auto_menu = SINGLE_PLAYER
   auto_restart = ON
   map = maps/BroodWar/micro/m5v5_c_far.scm
   race = Terran
   enemy_count = 1
   game_type = USE_MAP_SETTINGS
   ```
5. Install a Java JDK (8 or later) and Maven, then build the bridge:

   ```bash
   cd bridge
   mvn package
   ```
6. Start the trainer:

   ```bash
   python -m scai.train --env bwapi
   ```
7. Start the bridge:

   ```bash
   java -jar bridge/target/bridge.jar
   ```
8. Start Chaoslauncher, tick `BWAPI 4.4.0 [RELEASE]` and `W-MODE`, and
   press Start.

Add `-Dscai.gui=0` before `-jar` to stop the game drawing, which is
faster.
