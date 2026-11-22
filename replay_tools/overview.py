import json
import sys
from collections import Counter

for path in sys.argv[1:]:
    d = json.load(open(path))
    h = d["Header"]
    print("=" * 70)
    print(path.split("/")[-1], "| engine", h.get("Engine", {}).get("Name"),
          h.get("Version"), "| frames", h["Frames"],
          "| minutes", round(h["Frames"] / 23.81 / 60, 1), "|", h["StartTime"])
    print("  title:", repr(h["Title"]), "| map:", repr(h["Map"]),
          h["MapWidth"], "x", h["MapHeight"], "| type", h["Type"]["Name"],
          "| speed", h.get("Speed", {}).get("Name"), "| host", h.get("Host"))
    names = {}
    for p in h["Players"]:
        names[p["ID"]] = p["Name"]
        print("   slot", p["SlotID"], "id", p["ID"], p["Type"]["Name"],
              p["Race"]["Name"], "team", p["Team"], repr(p["Name"]),
              p["Color"]["Name"])
    print("  top-level keys:", list(d.keys()))
    cmds = (d.get("Commands") or {}).get("Cmds") or []
    print("  commands:", len(cmds))
    per = Counter(c["PlayerID"] for c in cmds)
    last = {}
    for c in cmds:
        last[c["PlayerID"]] = c["Frame"]
    for pid, n in sorted(per.items()):
        mins = last[pid] / 23.81 / 60
        print(f"    {names.get(pid, pid)!r:28} cmds {n:6d}  last at "
              f"{mins:5.1f} min  apm {n / max(mins, .01):5.0f}")
    types = Counter(c["Type"]["Name"] for c in cmds)
    print("  command types:", dict(types.most_common(25)))
    comp = d.get("Computed") or {}
    print("  computed keys:", list(comp.keys()))
    for k in ("LeaveGameCmds", "ChatCmds", "WinnerTeam"):
        v = comp.get(k)
        if k == "ChatCmds" and v:
            print("  chat lines:", len(v))
            for c in v[:60]:
                print("     ", round(c["Frame"] / 23.81 / 60, 1),
                      names.get(c.get("SenderSlotID"), c.get("SenderSlotID")),
                      "|", c.get("Message"))
        elif v:
            print(" ", k, json.dumps(v)[:600])
