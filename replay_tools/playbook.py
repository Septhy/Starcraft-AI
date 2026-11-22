"""A slot's habits across many replays, round by round.

Usage: playbook.py map.chk <slot> <name to leave out> r*.json

For each 5 minute round it prints what the slot's players made and
where they sent their armies, as named places from the map.
"""
import json
import struct
import sys
from collections import Counter, defaultdict

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import chk  # noqa: E402

sec, st = chk.load(sys.argv[1])
slot, skip = int(sys.argv[2]), sys.argv[3]

# named places: the map's locations, small ones only (a city, not a region)
places = []
mrgn = sec["MRGN"][-1]
for i in range(0, len(mrgn), 20):
    l, t, r, b, sid, _ = struct.unpack_from("<4IHH", mrgn, i)
    name = chk.clean(st.get(sid, "")).strip()
    if name and r > l and b > t and (r - l) * (b - t) < (40 * 32) ** 2:
        places.append(((l + r) / 2, (t + b) / 2, name))


def place(x, y):
    best = min(places, key=lambda p: (p[0] - x) ** 2 + (p[1] - y) ** 2)
    d = ((best[0] - x) ** 2 + (best[1] - y) ** 2) ** 0.5 / 32
    return best[2] if d <= 8 else f"tile {int(x // 32 // 16) * 16},{int(y // 32 // 16) * 16}"


MAKE = ("Train", "Build", "Train Fighter")
made = defaultdict(Counter)       # round -> unit -> count
went = defaultdict(Counter)       # round -> place -> orders
went_games = defaultdict(lambda: defaultdict(set))
games = defaultdict(int)          # round -> games still running
won = []
for path in sys.argv[4:]:
    d = json.load(open(path))
    h = d["Header"]
    p = [p for p in h["Players"] if p["SlotID"] == slot]
    mins = h["Frames"] / 23.81 / 60
    if not p or p[0]["Name"] == skip or mins < 10:
        continue
    p = p[0]
    won.append(True)
    for r in range(int(mins // 5) + 1):
        games[r] += 1
    for c in d["Commands"]["Cmds"]:
        if c["PlayerID"] != p["ID"]:
            continue
        r = int(c["Frame"] / 23.81 / 60 // 5)
        t = c["Type"]["Name"]
        if t in MAKE:
            made[r][(c.get("Unit") or {}).get("Name") or "Fighter"] += 1
        elif t == "Targeted Order" and c.get("Pos") and \
                (c.get("Order") or {}).get("Name") in ("AttackMove",
                                                       "MoveUnload"):
            name = ((c["Order"]["Name"] == "MoveUnload") and "DROP at " or "") \
                + place(c["Pos"]["X"], c["Pos"]["Y"])
            went[r][name] += 1
            went_games[r][name].add(path)
print(f"slot {slot}: {len(won)} games used")
for r in sorted(games):
    if games[r] < 2:
        break
    n = games[r]
    print(f"\nminutes {r * 5}-{r * 5 + 5}  ({n} games)")
    print("  made per game:", ", ".join(
        f"{u} {c / n:.0f}" for u, c in made[r].most_common(6) if c / n >= 0.5))
    print("  sent armies to:", "; ".join(
        f"{name} ({len(went_games[r][name])} games)"
        for name, c in went[r].most_common(7)
        if len(went_games[r][name]) >= max(2, n // 3)))
