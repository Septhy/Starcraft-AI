"""Train the brain.

    python -m scai.train --env sim              # practice fight, no game
    python -m scai.train --env bwapi            # StarCraft 1.16.1 (bridge)
    python -m scai.train --env sim --watch brain.pt   # test a saved brain
"""
import argparse

import torch

from . import ppo


def make_env(name, seed):
    if name == "sim":
        from .sim import SimEnv
        return SimEnv(seed=seed)
    from .bwapi_env import BwapiEnv
    return BwapiEnv()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--env", choices=["sim", "bwapi"], default="sim")
    p.add_argument("--updates", type=int, default=150)
    p.add_argument("--steps", type=int, default=2048,
                   help="decisions played per update")
    p.add_argument("--lr", type=float, default=3e-4)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--save", default="brain.pt")
    p.add_argument("--load", default=None, help="continue from a saved brain")
    p.add_argument("--watch", default=None,
                   help="play a saved brain without learning")
    args = p.parse_args()

    torch.manual_seed(args.seed)
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    brain = ppo.Brain().to(dev)
    env = make_env(args.env, args.seed)

    if args.watch:
        brain.load_state_dict(torch.load(args.watch, map_location=dev))
        wins = 0
        for ep in range(100):
            o, done = env.reset(), False
            while not done:
                a, _, _ = brain.act(o["obs"], o["mask"], greedy=True)
                o, _, done, info = env.step(a)
            wins += info["win"]
        print(f"won {wins} of 100")
        return

    if args.load:
        brain.load_state_dict(torch.load(args.load, map_location=dev))
    opt = torch.optim.Adam(brain.parameters(), lr=args.lr)
    print(f"training on {dev}")
    for u in range(1, args.updates + 1):
        steps, stats = ppo.collect(env, brain, args.steps)
        ppo.update(brain, opt, steps)
        print(f"update {u:4d}  games {stats['episodes']:4d}  "
              f"win rate {stats['win_rate']:.2f}  "
              f"return {stats['mean_return']:+.2f}", flush=True)
        torch.save(brain.state_dict(), args.save)


if __name__ == "__main__":
    main()
