"""Per slot: where it starts on the map, and how each replay's player
in that slot played. Usage: slots.py map.chk skip_name r*.json"""
import json
import struct
import sys
from collections import Counter, defaultdict

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import chk  # noqa: E402

sec, st = chk.load(sys.argv[1])
skip = sys.argv[2]
units = sec["UNIT"][-1]
start, count, cx, cy = {}, Counter(), Counter(), Counter()
for i in range(0, len(units), 36):
    _, x, y, uid, _, _, _, owner = struct.unpack_from("<IHHHHHHB", units, i)
    if uid == 214:
        start[owner] = (x // 32, y // 32)
    else:
        count[owner] += 1
        cx[owner] += x // 32
        cy[owner] += y // 32
print("map 256 x 192 tiles. start location and placed units per slot:")
for o in sorted(count):
    print(f"  slot {o}: start {start.get(o)}  units {count[o]}  "
          f"centre ({cx[o] // count[o]}, {cy[o] // count[o]})")

MAKE = ("Train", "Build", "Train Fighter", "Unit Morph", "Building Morph")
rows = defaultdict(list)
for path in sys.argv[3:]:
    d = json.load(open(path))
    h = d["Header"]
    mins = h["Frames"] / 23.81 / 60
    by_id = {p["ID"]: p for p in h["Players"]}
    cmds = defaultdict(list)
    for c in d["Commands"]["Cmds"]:
        cmds[c["PlayerID"]].append(c)
    for pid, p in by_id.items():
        cs = cmds.get(pid, [])
        if not cs:
            continue
        made = Counter((c.get("Unit") or {}).get("Name") or c["Type"]["Name"]
                       for c in cs if c["Type"]["Name"] in MAKE)
        orders = Counter((c.get("Order") or {}).get("Name") for c in cs
                         if c["Type"]["Name"] == "Targeted Order")
        grid = Counter()
        for c in cs:
            pos = c.get("Pos")
            if pos and c["Type"]["Name"] in ("Right Click", "Targeted Order"):
                grid[(pos["X"] // 32 // 32, pos["Y"] // 32 // 32)] += 1
        first = [(round(c["Frame"] / 23.81 / 60, 1),
                  (c.get("Unit") or {}).get("Name"))
                 for c in cs if c["Type"]["Name"] in MAKE][:10]
        rows[p["SlotID"]].append({
            "game": path.split("/")[-1][:2], "mins": round(mins),
            "skip": p["Name"] == skip, "apm": round(len(cs) / mins),
            "made": made.most_common(8), "orders": orders.most_common(5),
            "areas": grid.most_common(5), "first": first})
for slot in sorted(rows):
    print("=" * 60, "\nSLOT", slot)
    for r in rows[slot]:
        tag = " (the user: not to be used as an example)" if r["skip"] else ""
        print(f"  {r['game']} {r['mins']} min, {r['apm']} cmds/min{tag}")
        print("     made:", r["made"])
        print("     orders:", r["orders"])
        print("     busiest map areas (x,y of 8x6):", r["areas"])
        print("     first:", r["first"])
