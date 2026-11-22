"""One player's game, minute by minute. Usage: onegame.py mapdata.json <name> <slot> r*.json"""
import json, sys
from collections import Counter
m = json.load(open(sys.argv[1])); name, slot = sys.argv[2], int(sys.argv[3])
small = [p for p in m["places"] if p["w"] * p["h"] < (40 * 32) ** 2]
def place(x, y):
    b = min(small, key=lambda p: (p["x"] - x) ** 2 + (p["y"] - y) ** 2)
    d = ((b["x"] - x) ** 2 + (b["y"] - y) ** 2) ** 0.5 / 32
    return b["name"] if d <= 7 else f"({x // 32},{y // 32})"
for path in sys.argv[4:]:
    d = json.load(open(path)); h = d["Header"]
    p = [p for p in h["Players"] if p["Name"] == name and p["SlotID"] == slot]
    if not p: continue
    mins = h["Frames"] / 23.81 / 60
    cs = [c for c in d["Commands"]["Cmds"] if c["PlayerID"] == p[0]["ID"]]
    print("=" * 70, "\n", path, f"{mins:.0f} min, {len(cs)} commands")
    hk = Counter((c.get("HotkeyType", {}).get("Name"), c.get("Group")) for c in cs if c["Type"]["Name"] == "Hotkey")
    print(" hotkeys:", sorted((str(k), v) for k, v in hk.items()))
    sel = [len(c.get("UnitTags") or []) for c in cs if c["Type"]["Name"] == "Select"]
    print(" box selections:", len(sel), "sizes", sorted(Counter(sel).items()))
    step = 0.5 if mins < 3 else 1
    n = int(mins / step) + 1
    for i in range(min(n, 40)):
        lo, hi = i * step, (i + 1) * step
        w = [c for c in cs if lo <= c["Frame"] / 23.81 / 60 < hi]
        types = Counter(c["Type"]["Name"] for c in w)
        orders = Counter()
        for c in w:
            o = (c.get("Order") or {}).get("Name"); pos = c.get("Pos")
            if c["Type"]["Name"] == "Targeted Order" and pos:
                orders[(o.replace("AttackMove", "A").replace("RallyPointTile", "Rally"), place(pos["X"], pos["Y"]))] += 1
            elif c["Type"]["Name"] == "Right Click" and pos:
                orders[("rc", place(pos["X"], pos["Y"]))] += 1
        top = ", ".join(f"{o} {pl} x{k}" for (o, pl), k in orders.most_common(5))
        print(f" {lo:4.1f}m  train {types.get('Train', 0):3d} sel {types.get('Select', 0):3d} hot {types.get('Hotkey', 0):3d} | {top}")
