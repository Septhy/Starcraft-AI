import threading

import numpy as np

from scai import spec
from scai.sim import SimEnv
from tests import fake_bridge


def play(env, policy, games):
    wins = 0
    for _ in range(games):
        o, done = env.reset(), False
        while not done:
            o, r, done, info = env.step(policy(o))
        wins += info["win"]
    return wins / games


def nearest(o):
    return [0 if m[0] else spec.N_ATTACK for m in o["mask"]]


def weakest(o):
    out = []
    for ob, m in zip(o["obs"], o["mask"]):
        ks = [k for k in range(spec.N_ENEMY) if m[k]]
        out.append(min(ks, key=lambda k: (ob[1 + k * 5 + 4], k))
                   if ks else spec.N_ATTACK)
    return out


def test_obs_shape_and_mask():
    own = [spec.Seen(0, 0, 1.0), spec.Seen(10, 0, 0.5)]
    enemy = [spec.Seen(200, 0, 1.0), spec.Seen(50, 0, 0.25)]
    obs, mask, orders = spec.build(own, enemy)
    assert obs.shape == (2, spec.OBS_DIM)
    assert orders[0] == [1, 0]                 # nearest first
    assert mask[0, :2].all() and not mask[0, 2:spec.N_ATTACK].any()
    assert spec.decode(0, own[0], orders[0]) == ("attack", 1)
    assert spec.decode(spec.N_ATTACK, own[0], orders[0])[0] == "move"


def test_sim_rewards_focus_fire():
    assert play(SimEnv(seed=1), weakest, 100) > \
        play(SimEnv(seed=1), nearest, 100) + 0.2


def test_sim_is_repeatable():
    a = play(SimEnv(seed=5), nearest, 30)
    assert a == play(SimEnv(seed=5), nearest, 30)


def test_trainer_side_of_the_bridge():
    from scai.bwapi_env import BwapiEnv
    port = 11987
    t = threading.Thread(target=fake_bridge.run, args=(port, 100000),
                         daemon=True)
    t.start()
    env = BwapiEnv(port=port)
    results = []
    for _ in range(20):
        o, done, total = env.reset(), False, 0.0
        assert o["obs"].shape == (5, spec.OBS_DIM)
        while not done:
            o, r, done, info = env.step(weakest(o))
            total += r
        results.append(info["win"])
        if info["win"]:
            assert total > 2.0
    assert np.mean(results) > 0.6    # focus fire wins most fights
