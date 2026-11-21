"""A small stand-in fight: 5 marines against 5 marines.

This is NOT StarCraft. It is a rough copy of a marine fight (same hit
points, damage, range, reload time and speed) with no collisions and no
terrain. It exists so the training code can be run and tested without
the game. Real practice happens on 1.16.1 through the bridge.

The enemy is scripted: each enemy marine shoots the nearest opponent.
"""
import numpy as np

from . import spec

HP = 40.0
DAMAGE = 6.0
RANGE = 128.0     # pixels
COOLDOWN = 15     # frames between shots
SPEED = 4.0       # pixels per frame
FRAMES_PER_STEP = 8
MAX_STEPS = 150


class SimEnv:
    def __init__(self, n_own=5, n_enemy=5, seed=0):
        self.n_own, self.n_enemy = n_own, n_enemy
        self.rng = np.random.default_rng(seed)

    # --- state: per side, arrays of position, hit points, reload timer
    def reset(self):
        def side(n, cx):
            pos = np.stack([cx + self.rng.uniform(-30, 30, n),
                            240 + self.rng.uniform(-80, 80, n)], axis=1)
            return {"pos": pos, "hp": np.full(n, HP), "cd": np.zeros(n, int),
                    "cmd": [None] * n}
        gap = self.rng.uniform(220, 320)
        self.own, self.enemy = side(self.n_own, 320 - gap / 2), \
            side(self.n_enemy, 320 + gap / 2)
        self.t = 0
        return self._observe()

    def _seen(self, s):
        idx = [i for i in range(len(s["hp"])) if s["hp"][i] > 0]
        return idx, [spec.Seen(s["pos"][i, 0], s["pos"][i, 1], s["hp"][i] / HP)
                     for i in idx]

    def _observe(self):
        self.own_idx, own = self._seen(self.own)
        self.enemy_idx, enemy = self._seen(self.enemy)
        self._own_seen = own
        obs, mask, self._orders = spec.build(own, enemy)
        return {"obs": obs, "mask": mask}

    def _frame(self, a, b):
        """One frame of side a acting on side b. Returns damage dealt."""
        dealt = 0.0
        for i in range(len(a["hp"])):
            if a["hp"][i] <= 0:
                continue
            a["cd"][i] = max(0, a["cd"][i] - 1)
            cmd = a["cmd"][i]
            if cmd is None:
                continue
            if cmd[0] == "attack":
                j = cmd[1]
                if b["hp"][j] <= 0:
                    continue
                d = b["pos"][j] - a["pos"][i]
                dist = np.hypot(*d)
                if dist <= RANGE:
                    if a["cd"][i] == 0:
                        hit = min(DAMAGE, b["hp"][j])
                        b["hp"][j] -= hit
                        dealt += hit
                        a["cd"][i] = COOLDOWN
                else:
                    a["pos"][i] += d / dist * SPEED
            else:
                d = np.array(cmd[1:]) - a["pos"][i]
                dist = np.hypot(*d)
                if dist > 1e-6:
                    a["pos"][i] += d / dist * min(SPEED, dist)
        return dealt

    def _script_enemy(self):
        for i in range(self.n_enemy):
            if self.enemy["hp"][i] <= 0:
                continue
            alive = [j for j in range(self.n_own) if self.own["hp"][j] > 0]
            if not alive:
                self.enemy["cmd"][i] = None
                continue
            d = [np.hypot(*(self.own["pos"][j] - self.enemy["pos"][i]))
                 for j in alive]
            self.enemy["cmd"][i] = ("attack", alive[int(np.argmin(d))])

    def advance(self):
        """Run the frames of one decision. Returns (dealt, taken)."""
        dealt = taken = 0.0
        for _ in range(FRAMES_PER_STEP):
            self._script_enemy()
            # both sides fire in the same frame: a unit killed this frame
            # still gets its own shot off
            before = self.enemy["hp"].copy()
            dealt += self._frame(self.own, self.enemy)
            after = self.enemy["hp"].copy()
            self.enemy["hp"] = before
            taken += self._frame(self.enemy, self.own)
            self.enemy["hp"] = after
        return dealt, taken

    def step(self, actions):
        """actions: one action number per living own unit, in obs order."""
        self.own["cmd"] = [None] * self.n_own
        for row, i in enumerate(self.own_idx):
            cmd = spec.decode(int(actions[row]), self._own_seen[row],
                              self._orders[row])
            if cmd[0] == "attack":
                cmd = ("attack", self.enemy_idx[cmd[1]])
            self.own["cmd"][i] = cmd
        dealt, taken = self.advance()
        self.t += 1
        own_alive = (self.own["hp"] > 0).any()
        enemy_alive = (self.enemy["hp"] > 0).any()
        done = not own_alive or not enemy_alive or self.t >= MAX_STEPS
        win = bool(own_alive and not enemy_alive)
        reward = (dealt - taken) / HP + (2.0 if win else 0.0)
        return self._observe(), reward, done, {"win": win}
