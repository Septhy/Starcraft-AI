"""Where a slot gathers its army and when it sends it.
Usage: waves.py mapdata.json <slot> <skip name> r*.json"""
import json
import sys
from collections import Counter

m = json.load(open(sys.argv[1]))
slot, skip = int(sys.argv[2]), sys.argv[3]
small = [p for p in m["places"] if p["w"] * p["h"] < (40 * 32) ** 2]


def place(x, y):
    b = min(small, key=lambda p: (p["x"] - x) ** 2 + (p["y"] - y) ** 2)
    d = ((b["x"] - x) ** 2 + (b["y"] - y) ** 2) ** 0.5 / 32
    return b["name"] if d <= 8 else f"tile {x // 32 // 8 * 8},{y // 32 // 8 * 8}"


rally_all, tiles_all = Counter(), Counter()
for path in sys.argv[4:]:
    d = json.load(open(path))
    h = d["Header"]
    mins = h["Frames"] / 23.81 / 60
    p = [p for p in h["Players"] if p["SlotID"] == slot]
    if not p or p[0]["Name"] == skip or mins < 10:
        continue
    rally, moves, per_min = Counter(), Counter(), Counter()
    for c in d["Commands"]["Cmds"]:
        if c["PlayerID"] != p[0]["ID"] or c["Type"]["Name"] != "Targeted Order":
            continue
        o, pos = (c.get("Order") or {}).get("Name"), c.get("Pos")
        if not pos:
            continue
        if o == "RallyPointTile":
            rally[place(pos["X"], pos["Y"])] += 1
            tiles_all[(pos["X"] // 32 // 8 * 8, pos["Y"] // 32 // 8 * 8)] += 1
        elif o in ("AttackMove", "Move"):
            per_min[int(c["Frame"] / 23.81 / 60)] += 1
            moves[(place(pos["X"], pos["Y"]), int(c["Frame"] / 23.81 / 60 // 5))] += 1
    rally_all.update(rally.keys())
    print(path.split("/")[-1][:-5], f"{mins:.0f} min | rally points:",
          dict(rally.most_common(4)))
    print("   attack/move orders per minute:",
          " ".join(f"{per_min.get(i, 0):d}" for i in range(int(mins) + 1)))
print("rally places (games):", rally_all.most_common(8))
print("rally tiles (8x8 blocks, orders):", tiles_all.most_common(8))
