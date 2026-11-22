"""Trial: as Russia, gather marines, then send them to Warsaw as a wave.

Russia players do not send marines to the front one by one. They gather
them west of Smolensk and send them together; the replays show their
rally points there and their orders coming in bursts.

The steps only use an `io` object (see hands/win.py for the real one),
so they can be tested without Windows or the game.

It does not look for buildings on screen. The map file says where
Russia's barracks stand, so it moves the view there with the minimap
and clicks where the barracks should be. It presses M only after the
screen shows that a barracks is really selected.
"""
import json

from eyes import live

SLOT = "5"                 # Russia
TARGET = "Warsaw 200"
MARINES_PER_BARRACKS = 5   # a building queues at most five
# Where to try clicking, relative to where the barracks should appear.
TRIES = [(0, 0), (40, 80), (-60, 0), (60, 0), (0, -70), (0, 150), (-90, 90)]
GATHER = (160 * 32, 74 * 32)   # map pixels: where the army gathers
WAIT_FOR_MARINES = 90      # seconds: five marines built and walked over
WAVE_ROUNDS = 3            # a box holds 12 units, so order in rounds


class Stopped(Exception):
    pass


def load_map():
    return json.load(open(live.data_path("af40.json")))


def barracks_of(mapdata, slot=SLOT):
    s = mapdata["slots"][slot]
    sx, sy = s["start"]
    b = [b for b in s["buildings"] if b["type"] == "Barracks"]
    return sorted(b, key=lambda b: (b["x"] - sx) ** 2 + (b["y"] - sy) ** 2)


def place(mapdata, name):
    return next(p for p in mapdata["places"] if p["name"] == name)


def look_at(io, x, y):
    """Move the view to a map point. Returns the camera centre."""
    mx, my = live.minimap_point(x, y)
    io.click(mx, my)
    io.sleep(0.5)
    return live.camera_after_click(mx, my)


def select_barracks(io, b, n):
    cam = look_at(io, b["x"], b["y"])
    px, py = live.on_screen(b["x"], b["y"], cam)
    io.shot(f"b{n}-view")
    l, t, r, btm = live.GAME_AREA
    for k, (dx, dy) in enumerate(TRIES):
        x, y = px + dx, py + dy
        if not (l + 5 < x < r - 5 and t + 5 < y < btm - 5):
            continue
        io.click(x, y)
        io.sleep(0.3)
        if live.barracks_selected(io.shot(f"b{n}-try{k}")):
            io.log(f"barracks {n}: selected with click {k} at {x},{y}")
            return (x, y)
    io.log(f"barracks {n}: NOT selected (expected near {px},{py})")
    return None


def run(io, mapdata=None):
    """Returns a short result for the log."""
    mapdata = mapdata or load_map()
    first = io.shot("start")
    if not live.minimap_showing(first):
        io.log("The live game's minimap is not on screen. Nothing done.")
        return {"trained": 0, "sent": 0}
    found = []
    for n, b in enumerate(barracks_of(mapdata)):
        hit = select_barracks(io, b, n)
        if hit:
            io.click(*live.minimap_point(*GATHER), button="right")   # rally
            io.sleep(0.2)
            for _ in range(MARINES_PER_BARRACKS):
                io.key("m")
                io.sleep(0.1)
            io.sleep(0.3)
            io.shot(f"b{n}-queued")
            found.append((b, hit))
    io.log(f"trained at {len(found)} barracks; waiting for marines to gather")
    if not found:
        return {"trained": 0, "sent": 0}
    io.sleep(WAIT_FOR_MARINES)
    w = place(mapdata, TARGET)
    tx, ty = live.minimap_point(w["x"], w["y"])
    l, t, r, btm = live.GAME_AREA
    look_at(io, *GATHER)
    io.shot("gathered")
    sent = 0
    for n in range(WAVE_ROUNDS):
        # a box over the whole view picks up to 12 of the marines there
        io.drag(l + 20, t + 20, r - 20, btm - 20)
        io.sleep(0.3)
        io.shot(f"wave{n}-selected")
        io.key("a")
        io.sleep(0.15)
        io.click(tx, ty)
        io.sleep(0.4)
        look_at(io, *GATHER)             # in case the order did not take
        io.shot(f"wave{n}-ordered")
        sent += 1
        io.sleep(4)                      # let that group walk off
    io.sleep(10)
    io.shot("gather-point-after")
    look_at(io, w["x"], w["y"])
    io.sleep(1)
    io.shot("target")
    io.log(f"sent {sent} rounds toward {TARGET}")
    return {"trained": len(found), "sent": sent}
