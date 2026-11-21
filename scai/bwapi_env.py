"""Practice on real StarCraft 1.16.1, through the Java bridge.

The trainer listens on a port. The bridge (bridge/) runs next to the
game, connects, and sends one line per decision describing both sides.
This file turns that into the same input the practice simulator gives,
and turns the brain's actions back into commands.

The brain is shown only units that are visible. Units out of sight are
used for keeping score only (so a fight is not called won while an
enemy is merely out of view).
"""
import json
import socket

from . import spec

MAX_STEPS = 150
WAIT_BEFORE_RESTART = 40   # decisions to wait for a new fight to appear


class BwapiEnv:
    def __init__(self, port=11111):
        srv = socket.socket()
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(("127.0.0.1", port))
        srv.listen(1)
        print(f"waiting for the bridge on port {port} ...", flush=True)
        self.conn, _ = srv.accept()
        self.conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.file = self.conn.makefile("r", encoding="utf-8")
        print("bridge connected", flush=True)
        self.state = None
        self.pending = False   # a state has been read and not answered

    # --- talking to the bridge
    def _read(self):
        line = self.file.readline()
        if not line:
            raise ConnectionError("the bridge closed the connection")
        self.state = json.loads(line)
        self.pending = True

    def _reply(self, lines=()):
        self.conn.sendall(("\n".join(list(lines) + ["END"]) + "\n").encode())
        self.pending = False

    # --- one side's units as {id: (x, y, hp_fraction, visible)}
    @staticmethod
    def _units(raw):
        return {u[0]: (u[1], u[2], u[3] / max(u[4], 1), bool(u[5]))
                for u in raw}

    def _observe(self):
        self.own = self._units(self.state["own"])
        self.enemy = self._units(self.state["enemy"])
        self.own_ids = sorted(self.own)
        self.enemy_ids = sorted(i for i in self.enemy if self.enemy[i][3])
        self._own_seen = [spec.Seen(*self.own[i][:3]) for i in self.own_ids]
        enemy_seen = [spec.Seen(*self.enemy[i][:3]) for i in self.enemy_ids]
        obs, mask, self._orders = spec.build(self._own_seen[:spec.N_OWN],
                                             enemy_seen)
        self.own_ids = self.own_ids[:spec.N_OWN]
        return {"obs": obs, "mask": mask}

    def reset(self):
        """Wait for a fresh fight: both sides present at full health."""
        waited = 0
        while True:
            if self.pending:
                self._reply()
            self._read()
            own = self._units(self.state["own"])
            enemy = self._units(self.state["enemy"])
            fresh = own and enemy and all(
                u[2] >= 0.999 for u in list(own.values()) + list(enemy.values()))
            if fresh:
                break
            waited += 1
            if waited == WAIT_BEFORE_RESTART:
                self._reply(["RESTART"])
        self.t = 0
        return self._observe()

    def step(self, actions):
        lines = []
        for row, uid in enumerate(self.own_ids):
            cmd = spec.decode(int(actions[row]), self._own_seen[row],
                              self._orders[row])
            if cmd[0] == "attack":
                lines.append(f"A {uid} {self.enemy_ids[cmd[1]]}")
            else:
                lines.append(f"M {uid} {int(cmd[1])} {int(cmd[2])}")
        before_own, before_enemy = self.own, self.enemy
        self._reply(lines)
        self._read()
        obs = self._observe()
        # a unit that is gone has lost all the health it had
        lost = lambda before, now: sum(
            hp - (now[i][2] if i in now else 0.0)
            for i, (_, _, hp, _) in before.items())
        dealt, taken = lost(before_enemy, self.enemy), lost(before_own, self.own)
        self.t += 1
        done = not self.own or not self.enemy or self.t >= MAX_STEPS
        win = bool(self.own and not self.enemy)
        reward = dealt - taken + (2.0 if win else 0.0)
        return obs, reward, done, {"win": win}
