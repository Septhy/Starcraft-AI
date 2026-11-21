"""A stand-in for the Java bridge and the game, for testing.

It speaks the bridge's protocol but runs the practice simulator behind
it, so the trainer's side of the link can be tested without StarCraft.
"""
import json
import socket
import time

from scai.sim import SimEnv, HP


def run(port, max_messages):
    for _ in range(100):
        try:
            sock = socket.create_connection(("127.0.0.1", port))
            break
        except OSError:
            time.sleep(0.05)
    f = sock.makefile("r")
    world, frame, idle, base = SimEnv(seed=3), 0, 0, 0
    world.reset()

    def units(side, first_id):
        return [[first_id + i, int(side["pos"][i, 0]), int(side["pos"][i, 1]),
                 int(side["hp"][i]), int(HP), 1]
                for i in range(len(side["hp"])) if side["hp"][i] > 0]

    for _ in range(max_messages):
        msg = {"frame": frame, "own": units(world.own, base + 100),
               "enemy": units(world.enemy, base + 200)}
        sock.sendall((json.dumps(msg) + "\n").encode())
        world.own["cmd"] = [None] * world.n_own
        restart = False
        while True:
            line = f.readline()
            if not line:
                return
            w = line.split()
            if w[0] == "END":
                break
            if w[0] == "RESTART":
                restart = True
            elif w[0] == "A":
                world.own["cmd"][int(w[1]) - base - 100] = \
                    ("attack", int(w[2]) - base - 200)
            elif w[0] == "M":
                world.own["cmd"][int(w[1]) - base - 100] = \
                    ("move", float(w[2]), float(w[3]))
        frame += 8
        over = not (world.own["hp"] > 0).any() or \
            not (world.enemy["hp"] > 0).any()
        if over:
            idle += 1
        else:
            world.advance()
        if restart or idle >= 3:      # the map brings both sides back
            world.reset()
            idle, base = 0, base + 1000   # new units get new ids
    sock.close()
