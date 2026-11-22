"""Write the map facts the bot needs into a small JSON file.

Usage: mapdata.py map.chk out.json

For each slot: its start position and its starting buildings (name and
centre, in pixels of the map; one tile is 32 pixels) and where its
starting units stand. Also every named
place on the map.
"""
import json
import struct
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import chk  # noqa: E402

BUILDINGS = {106: "Command Center", 111: "Barracks", 113: "Factory",
             114: "Starport", 125: "Bunker", 109: "Supply Depot",
             124: "Missile Turret", 122: "Engineering Bay",
             154: "Nexus", 160: "Gateway",
             167: "Stargate"}

AIR = {8: "Wraith", 12: "Battlecruiser", 70: "Scout", 58: "Valkyrie",
       60: "Corsair", 72: "Carrier", 11: "Dropship", 9: "Science Vessel"}

sec, st = chk.load(sys.argv[1])
dim = struct.unpack("<2H", sec["DIM "][-1][:4])
slots = {}
units = sec["UNIT"][-1]
for i in range(0, len(units), 36):
    _, x, y, uid, _, _, _, owner = struct.unpack_from("<IHHHHHHB", units, i)
    s = slots.setdefault(owner, {"start": None, "buildings": [], "units": [],
                                 "structures": [], "air": []})
    if uid == 214:
        s["start"] = [x, y]
    if uid in BUILDINGS:
        s["buildings"].append({"type": BUILDINGS[uid], "x": x, "y": y})
    if 106 <= uid <= 202:
        s["structures"].append([x, y])
    if uid in BUILDINGS or uid == 214:
        pass
    elif uid < 106 and uid != 13:        # units that can move (no mines)
        s["units"].append([x, y])
        if uid in AIR:
            s["air"].append({"type": AIR[uid], "x": x, "y": y})
places = []
mrgn = sec["MRGN"][-1]
for i in range(0, len(mrgn), 20):
    l, t, r, b, sid, _ = struct.unpack_from("<4IHH", mrgn, i)
    name = chk.clean(st.get(sid, "")).strip()
    if name and r > l and b > t:
        places.append({"name": name, "x": (l + r) // 2, "y": (t + b) // 2,
                       "w": r - l, "h": b - t})
json.dump({"map": "WWII Euro - AF 4.0", "tiles": list(dim),
           "slots": {str(k): v for k, v in sorted(slots.items()) if k < 8},
           "places": places},
          open(sys.argv[2], "w"), indent=1)
