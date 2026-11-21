"""The brain and how it learns (PPO).

One small network is shared by every unit. Each unit looks at its own
surroundings (see spec.py) and picks its own action. All units share
the team's reward.
"""
import numpy as np
import torch
import torch.nn as nn

from . import spec


class Brain(nn.Module):
    def __init__(self, hidden=128):
        super().__init__()
        self.body = nn.Sequential(
            nn.Linear(spec.OBS_DIM, hidden), nn.Tanh(),
            nn.Linear(hidden, hidden), nn.Tanh())
        self.pi = nn.Linear(hidden, spec.N_ACTIONS)
        self.v = nn.Linear(hidden, 1)

    def forward(self, obs, mask):
        h = self.body(obs)
        logits = self.pi(h).masked_fill(~mask, -1e9)
        return torch.distributions.Categorical(logits=logits), \
            self.v(h).squeeze(-1)

    @torch.no_grad()
    def act(self, obs, mask, greedy=False):
        """obs, mask: numpy arrays for the living units. Returns actions."""
        dev = next(self.parameters()).device
        dist, value = self(torch.as_tensor(obs, device=dev),
                           torch.as_tensor(mask, device=dev))
        a = dist.probs.argmax(-1) if greedy else dist.sample()
        return a.cpu().numpy(), dist.log_prob(a).cpu().numpy(), \
            value.cpu().numpy()


def collect(env, brain, n_steps, gamma=0.99, lam=0.95):
    """Play n_steps decisions and return training samples plus results.

    The team is treated as one learner: its value is the mean of the
    units' values, and each step's log-probability is the sum over the
    living units.
    """
    steps, wins, returns = [], [], []
    o = env.reset()
    ep_ret = 0.0
    while len(steps) < n_steps or not steps[-1]["done"]:
        a, logp, v = brain.act(o["obs"], o["mask"])
        o2, r, done, info = env.step(a)
        steps.append({"obs": o["obs"], "mask": o["mask"], "act": a,
                      "logp": logp.sum(), "v": v.mean(), "r": r,
                      "done": done})
        ep_ret += r
        if done:
            wins.append(info["win"])
            returns.append(ep_ret)
            ep_ret = 0.0
            o = env.reset()
        else:
            o = o2
    adv, last = np.zeros(len(steps), dtype=np.float32), 0.0
    for t in reversed(range(len(steps))):
        s = steps[t]
        nxt = 0.0 if s["done"] else steps[t + 1]["v"]
        delta = s["r"] + gamma * nxt - s["v"]
        last = delta + (0.0 if s["done"] else gamma * lam * last)
        adv[t] = last
    for s, a_ in zip(steps, adv):
        s["adv"], s["ret"] = a_, a_ + s["v"]
    return steps, {"win_rate": float(np.mean(wins)),
                   "mean_return": float(np.mean(returns)),
                   "episodes": len(wins)}


def update(brain, opt, steps, epochs=4, batch=256, clip=0.2, ent=0.01):
    dev = next(brain.parameters()).device
    counts = [len(s["act"]) for s in steps]
    owner = torch.as_tensor(np.repeat(np.arange(len(steps)), counts),
                            device=dev)
    obs = torch.as_tensor(np.concatenate([s["obs"] for s in steps]),
                          device=dev)
    mask = torch.as_tensor(np.concatenate([s["mask"] for s in steps]),
                           device=dev)
    act = torch.as_tensor(np.concatenate([s["act"] for s in steps]),
                          device=dev)
    f = lambda k: torch.as_tensor(
        np.array([s[k] for s in steps], dtype=np.float32), device=dev)
    old_logp, adv, ret = f("logp"), f("adv"), f("ret")
    adv = (adv - adv.mean()) / (adv.std() + 1e-8)
    n = len(steps)
    cnt = torch.as_tensor(counts, device=dev, dtype=torch.float32)
    for _ in range(epochs):
        for idx in torch.randperm(n, device=dev).split(batch):
            sel = torch.isin(owner, idx)
            # map each selected unit row to its step's place in the batch
            place = torch.full((n,), -1, device=dev, dtype=torch.long)
            place[idx] = torch.arange(len(idx), device=dev)
            row = place[owner[sel]]
            dist, v = brain(obs[sel], mask[sel])
            zeros = torch.zeros(len(idx), device=dev)
            logp = zeros.index_add(0, row, dist.log_prob(act[sel]))
            value = zeros.index_add(0, row, v) / cnt[idx]
            entropy = zeros.index_add(0, row, dist.entropy()) / cnt[idx]
            ratio = torch.exp(logp - old_logp[idx])
            a = adv[idx]
            loss = -torch.min(ratio * a,
                              ratio.clamp(1 - clip, 1 + clip) * a).mean() \
                + 0.5 * (value - ret[idx]).pow(2).mean() \
                - ent * entropy.mean()
            opt.zero_grad()
            loss.backward()
            nn.utils.clip_grad_norm_(brain.parameters(), 0.5)
            opt.step()
