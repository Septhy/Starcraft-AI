"""What one named player did in each replay."""
import json
import sys
from collections import Counter

name = sys.argv[1]
for path in sys.argv[2:]:
    d = json.load(open(path))
    h = d["Header"]
    me = [p for p in h["Players"] if p["Name"] == name]
    if not me:
        continue
    me = me[0]
    cmds = [c for c in d["Commands"]["Cmds"] if c["PlayerID"] == me["ID"]]
    mins = h["Frames"] / 23.81 / 60
    print("=" * 60)
    print(path.split("/")[-1], f"{mins:.0f} min, slot {me['SlotID']},",
          me["Race"]["Name"], "| commands", len(cmds))
    print("  types:", dict(Counter(c["Type"]["Name"] for c in cmds)
                           .most_common(12)))
    made = Counter()
    for c in cmds:
        if c["Type"]["Name"] in ("Train", "Build", "Train Fighter",
                                 "Unit Morph", "Building Morph"):
            made[(c["Type"]["Name"], (c.get("Unit") or {}).get("Name"))] += 1
    print("  made:", {f"{t}:{u}": n for (t, u), n in made.most_common(20)})
    orders = Counter((c.get("Order") or {}).get("Name") for c in cmds
                     if c["Type"]["Name"] == "Targeted Order")
    print("  targeted orders:", dict(orders.most_common(10)))
    hk = Counter((c.get("HotkeyType", {}).get("Name"), c.get("Group"))
                 for c in cmds if c["Type"]["Name"] == "Hotkey")
    print("  hotkey groups used:", len({g for _, g in hk}),
          "| assigns", sum(n for (t, _), n in hk.items() if t == "Assign"),
          "selects", sum(n for (t, _), n in hk.items() if t == "Select"))
    # where on the map the orders went (map is 256 x 192 tiles)
    grid = Counter()
    for c in cmds:
        p = c.get("Pos")
        if p and c["Type"]["Name"] in ("Right Click", "Targeted Order"):
            grid[(p["X"] // 32 // 32, p["Y"] // 32 // 32)] += 1
    print("  orders by map area (8 x 6 grid, x right, y down):")
    for y in range(6):
        print("    ", " ".join(f"{grid.get((x, y), 0):5d}" for x in range(8)))
    # activity per 5 minutes
    per = Counter(int(c["Frame"] / 23.81 / 60 // 5) for c in cmds)
    print("  commands per 5 min:", [per.get(i, 0)
                                    for i in range(int(mins // 5) + 1)])
    first = [c for c in cmds if c["Type"]["Name"] in ("Train", "Build")][:12]
    print("  first makes:", [(round(c["Frame"] / 23.81 / 60, 1),
                              (c.get("Unit") or {}).get("Name"))
                             for c in first])
