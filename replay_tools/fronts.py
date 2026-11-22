"""Where Russia's orders go, minute by minute: north (Poland, Berlin) or
south (Odessa, Romania, the Balkans), next to where Germany and Italy
are pushing. Usage: fronts.py r*.json"""
import json, sys
def region(x, y):
    if x < 150 and 60 <= y < 108: return "N"       # Konigsberg, Warsaw, Krakow, Berlin
    if 120 <= x < 172 and y >= 108: return "S"     # Romania, Serbia, Hungary, Athens
    if 150 <= x < 200 and 95 <= y < 115: return "O" # Odessa, Ukraine
    return None
for path in sys.argv[1:]:
    d = json.load(open(path)); h = d["Header"]; mins = h["Frames"] / 23.81 / 60
    if mins < 8: continue
    ids = {p["SlotID"]: p for p in h["Players"]}
    if 5 not in ids: continue
    rows = {}
    for c in d["Commands"]["Cmds"]:
        pos = c.get("Pos")
        if not pos or c["Type"]["Name"] not in ("Targeted Order", "Right Click"): continue
        m = int(c["Frame"] / 23.81 / 60); x, y = pos["X"] // 32, pos["Y"] // 32
        for slot, tag in ((5, "R"), (0, "G"), (1, "I")):
            if slot in ids and c["PlayerID"] == ids[slot]["ID"]:
                if tag == "R":
                    r = region(x, y)
                    if r: rows.setdefault(m, {}).setdefault(r, 0); rows[m][r] += 1
                elif tag == "G" and x >= 140 and y < 108:      # Germany pushing into Russia
                    rows.setdefault(m, {}).setdefault("g", 0); rows[m]["g"] += 1
                elif tag == "G" and 120 <= x < 172 and y >= 108:
                    rows.setdefault(m, {}).setdefault("gs", 0); rows[m]["gs"] += 1
                elif tag == "I" and 120 <= x < 172 and y >= 108:   # Italy in the Balkans
                    rows.setdefault(m, {}).setdefault("i", 0); rows[m]["i"] += 1
    line = ""
    for m in range(min(int(mins) + 1, 16)):
        r = rows.get(m, {})
        n, s = r.get("N", 0), r.get("S", 0) + r.get("O", 0)
        mark = "." if n + s < 8 else ("N" if n >= 2 * s else "S" if s >= 2 * n else "b")
        line += mark
    first_s = next((m for m in sorted(rows) if rows[m].get("S", 0) >= 10), None)
    g_east = sum(rows.get(m, {}).get("g", 0) for m in range(2, 6))
    axis_s = sum(rows.get(m, {}).get("i", 0) + rows.get(m, {}).get("gs", 0) for m in range(2, 6))
    print(f"{path[:-5]:4} {ids[5]['Name']:16} {mins:3.0f}m  minutes 0-15: {line:16}  first Balkan push at min {first_s}  | German orders into Russia min 2-5: {g_east:4d} | Axis orders in Balkans min 2-5: {axis_s:4d}")
