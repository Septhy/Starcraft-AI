"""How one player works an air group, from replays (plan step 1).

    python3 replay_tools/air.py <player name> <slot> r1.json r2.json ...

The selection is followed through the commands (Select, Select Add,
Select Remove, Hotkey Assign / Add / Select), so every order is known to
belong to a hotkey group or to a box or click. For each game it prints
the orders a minute on each group, then, for the air group (the group
given to --key, else the busiest group that gets Hold Position after
moves), its bursts: runs of orders less than BURST_GAP seconds apart.
For each burst: how long, how many orders, the hop between targets,
how soon after a ground attack it began, how far from the nearest
ground target, and whether it ended with a long move away (a retreat
or a move to the next place).
"""
import json
import statistics as stats
import sys
from collections import Counter, defaultdict

FRAMES = 23.81
ORDERS = ("Right Click", "Targeted Order", "Hold Position", "Stop")
BURST_GAP = 2.0                # seconds: a longer pause ends a burst
LONG_MOVE = 15                 # tiles: a move this far after a burst
MASS = (160, 76)               # tiles: Russia's massing place


def orders_by_group(cmds):
    """(time, group, kind, (tile x, tile y) or None, on a unit) for every
    order, in order."""
    groups, sel, cur, out = {}, set(), None, []
    for c in cmds:
        t = c["Type"]["Name"]
        if t == "Select":
            sel, cur = set(c.get("UnitTags") or []), "box"
        elif t == "Select Add":
            sel |= set(c.get("UnitTags") or [])
            cur = "box"
        elif t == "Select Remove":
            sel -= set(c.get("UnitTags") or [])
        elif t == "Hotkey":
            g, kind = c.get("Group"), c["HotkeyType"]["Name"]
            if kind == "Assign":
                groups[g], cur = set(sel), g
            elif kind == "Add":
                groups[g] = groups.get(g, set()) | sel
                cur = g
            elif kind == "Select":
                sel, cur = set(groups.get(g, set())), g
        elif t in ORDERS:
            kind = (c.get("Order") or {}).get("Name") if t == "Targeted Order" \
                else t
            p = c.get("Pos")
            out.append((c["Frame"] / FRAMES, cur, kind,
                        (p["X"] // 32, p["Y"] // 32) if p else None,
                        bool(c.get("UnitTag"))))
    return out


def air_key(orders):
    """The group that gets the most Hold Position soon after a move."""
    score = Counter()
    by = defaultdict(list)
    for o in orders:
        by[o[1]].append(o)
    for g, seq in by.items():
        if g == "box":
            continue
        score[g] = sum(1 for a, b in zip(seq, seq[1:])
                       if a[2] == "Right Click" and b[2] == "Hold Position"
                       and b[0] - a[0] < 3)
    return score.most_common(1)[0][0] if score else None


def bursts(seq):
    out, cur = [], []
    for o in seq:
        if cur and o[0] - cur[-1][0] > BURST_GAP:
            out.append(cur)
            cur = []
        cur.append(o)
    if cur:
        out.append(cur)
    return [b for b in out if len(b) >= 4]


def dist(a, b):
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


def report(path, name, slot, key=None):
    d = json.load(open(path))
    me = [p for p in d["Header"]["Players"]
          if p["Name"] == name and p["SlotID"] == slot]
    if not me:
        return None
    pid = me[0]["ID"]
    mins = d["Header"]["Frames"] / FRAMES / 60
    cmds = [c for c in d["Commands"]["Cmds"] if c["PlayerID"] == pid]
    orders = orders_by_group(cmds)
    key = key if key is not None else air_key(orders)
    print("=" * 70)
    print(f"{path}: {mins:.0f} min; air group {key}")
    per = Counter(o[1] for o in orders)
    print("  orders a minute:", {g: round(n / mins, 1)
                                 for g, n in per.most_common(8)})
    air = [o for o in orders if o[1] == key]
    ground = [o for o in orders if o[1] not in (key, "box", 0)
              and o[2] in ("AttackMove", "Right Click") and o[3]]
    bs = bursts(air)
    rows = []
    for b in bs:
        start, end = b[0][0], b[-1][0]
        pts = [o[3] for o in b if o[3]]
        hops = [dist(p, q) for p, q in zip(pts, pts[1:])]
        centre = (sum(p[0] for p in pts) / len(pts),
                  sum(p[1] for p in pts) / len(pts)) if pts else None
        before = [g for g in ground if start - 60 <= g[0] <= start]
        since = start - before[-1][0] if before else None
        near_ground = min((dist(centre, g[3]) for g in ground
                           if abs(g[0] - start) <= 30), default=None) \
            if centre else None
        after = [o for o in air if end < o[0] <= end + 5 and o[3]]
        away = None
        if after and centre and dist(after[0][3], centre) >= LONG_MOVE:
            closer = dist(after[0][3], MASS) < dist(centre, MASS)
            away = "back toward the mass" if closer else "on, away from the mass"
        rows.append({"len": end - start, "n": len(b),
                     "hop": stats.median(hops) if hops else 0,
                     "holds": sum(1 for o in b if o[2] == "Hold Position"),
                     "on_unit": sum(1 for o in b if o[4]),
                     "since": since, "near": near_ground, "away": away})
    if not rows:
        print("  no bursts")
        return rows
    med = lambda k: stats.median([r[k] for r in rows if r[k] is not None]) \
        if any(r[k] is not None for r in rows) else None
    print(f"  bursts: {len(rows)}; median {med('len'):.1f} s, {med('n')} "
          f"orders, hop {med('hop'):.1f} tiles, {med('holds')} holds")
    sinces = [r["since"] for r in rows if r["since"] is not None]
    print(f"  began within 10 s of a ground order: "
          f"{sum(1 for x in sinces if x <= 10)} of {len(rows)}")
    nears = [r["near"] for r in rows if r["near"] is not None]
    if nears:
        print(f"  centre to the nearest ground target (+-30 s): median "
              f"{stats.median(nears):.1f} tiles")
    print("  ended with a long move:", dict(Counter(r["away"] for r in rows)))
    print(f"  clicks on a unit: {sum(r['on_unit'] for r in rows)} of "
          f"{sum(r['n'] for r in rows)}")
    return rows


if __name__ == "__main__":
    name, slot = sys.argv[1], int(sys.argv[2])
    for path in sys.argv[3:]:
        report(path, name, slot)
