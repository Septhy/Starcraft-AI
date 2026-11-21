"""What the brain sees and what it can do.

This file is the contract between the brain and whatever feeds it: the
practice simulator, the BWAPI bridge on 1.16.1, and later the screen
reader on Remastered. All three hand over the same thing: for each unit
on each side, a position in game pixels and a health fraction. Nothing
else. Anything a screen cannot show (weapon cooldown, exact hit points,
orders, units off screen) is deliberately left out, so the brain cannot
learn to depend on it.
"""
from dataclasses import dataclass

import numpy as np

N_OWN = 5          # most units the brain controls
N_ENEMY = 5        # most enemy units it looks at
DIST_SCALE = 256.0  # pixels; positions are divided by this

# Actions for one unit: attack the k-th nearest enemy, or step in one of
# eight directions.
N_ATTACK = N_ENEMY
N_MOVE = 8
N_ACTIONS = N_ATTACK + N_MOVE
MOVE_STEP = 48.0   # pixels a move order aims ahead

_DIRS = np.array(
    [[np.cos(a), np.sin(a)] for a in np.arange(N_MOVE) * (2 * np.pi / N_MOVE)]
)

OBS_DIM = 1 + N_ENEMY * 5 + (N_OWN - 1) * 4


@dataclass
class Seen:
    """One unit as an observer sees it."""
    x: float
    y: float
    hp: float  # 0..1, the fraction of the health bar that is filled


def _nearest(me, others):
    """Indices of `others`, nearest to `me` first."""
    d = [np.hypot(o.x - me.x, o.y - me.y) for o in others]
    return sorted(range(len(others)), key=lambda i: (d[i], i))


def build(own, enemy):
    """Turn what is seen into the brain's input.

    own, enemy: lists of Seen (living units only).
    Returns (obs, mask, enemy_order):
      obs   [len(own), OBS_DIM]   one row per own unit
      mask  [len(own), N_ACTIONS] which actions are allowed
      enemy_order  for each own unit, enemy indices nearest first, so
                   "attack the k-th nearest" can be turned into a target
    """
    n = len(own)
    obs = np.zeros((n, OBS_DIM), dtype=np.float32)
    mask = np.zeros((n, N_ACTIONS), dtype=bool)
    mask[:, N_ATTACK:] = True
    orders = []
    for i, me in enumerate(own):
        row = [me.hp]
        order = _nearest(me, enemy)[:N_ENEMY]
        orders.append(order)
        for k in range(N_ENEMY):
            if k < len(order):
                e = enemy[order[k]]
                dx, dy = (e.x - me.x) / DIST_SCALE, (e.y - me.y) / DIST_SCALE
                row += [1.0, dx, dy, float(np.hypot(dx, dy)), e.hp]
                mask[i, k] = True
            else:
                row += [0.0] * 5
        mates = [m for j, m in enumerate(own) if j != i]
        mate_order = _nearest(me, mates)[: N_OWN - 1]
        for k in range(N_OWN - 1):
            if k < len(mate_order):
                m = mates[mate_order[k]]
                row += [1.0, (m.x - me.x) / DIST_SCALE,
                        (m.y - me.y) / DIST_SCALE, m.hp]
            else:
                row += [0.0] * 4
        obs[i] = row
    return obs, mask, orders


def decode(action, me, enemy_order):
    """Turn one unit's action number into a command.

    Returns ("attack", enemy_index) or ("move", x, y).
    """
    if action < N_ATTACK:
        return ("attack", enemy_order[action])
    dx, dy = _DIRS[action - N_ATTACK] * MOVE_STEP
    return ("move", me.x + dx, me.y + dy)
