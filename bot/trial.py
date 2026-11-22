"""Trial: Russia's opening. Mass the army fast, then hit Berlin.

What Russia players do, and what this copies:
  1. In the first seconds, start marines at every barracks, with the
     rally point at the massing place west of Smolensk.
  2. Order most of the starting army (about 175 units spread over the
     east) to the massing place. Not every last unit: most of them.
  3. Have the mass complete about 1:30 to 2:00 into the game, then
     send it at Berlin together.

The steps only use an `io` object (see hands/win.py for the real one),
so they can be tested without Windows or the game.

How it sees: the minimap shows where its own units are (eyes/live.py,
Watch). It boxes only where units are, watches the mass build up at
the massing place, picks up units that were missed and are standing
still, and sends the wave when the mass has stopped growing. It gives
an order only when the screen shows units are selected, and presses M
only when the screen shows a barracks is selected.
"""
import json

from eyes import live

SLOT = "5"                     # Russia
TARGET = "Berlin 1000"
MASS = (160 * 32, 74 * 32)     # map pixels: where the army masses
MASS_RADIUS = 13               # minimap pixels around it that count as there
MARINES_PER_BARRACKS = 5       # a building queues at most five
# Where to try clicking, relative to where the barracks should appear.
TRIES = [(0, 0), (40, 80), (-60, 0), (60, 0), (0, -70), (0, 150), (-90, 90)]
MARGIN = 120                   # screen pixels added round a group for the box
GROUP = (8, 4)                 # a group is at most this many minimap pixels wide, tall
FIRST_ORDERS_UNTIL = 60        # seconds: stop the first round of orders
WAVE_EARLIEST = 90             # seconds: do not send the wave before this
WAVE_LATEST = 115              # seconds: send it by now whatever happens
WAVE_STOP = 210                # seconds: stop sweeping the massing place


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


def look_at(io, x, y, wait=0.2):
    """Move the view to a map point. Returns the camera centre."""
    mx, my = live.minimap_point(x, y)
    io.click(mx, my)
    io.sleep(wait)
    return live.camera_after_click(mx, my)


class Counts:
    boxes = 0
    empty = 0


def order_group(io, pixels, tx, ty, counts, watch=None):
    """Box the units drawn at these minimap pixels and attack-move them
    to the minimap point. Returns True if an order was given."""
    cols = [p[0] for p in pixels]
    rows = [p[1] for p in pixels]
    x0, y0 = live.from_drawn(min(cols) - 0.5, min(rows) - 0.5)
    x1, y1 = live.from_drawn(max(cols) + 0.5, max(rows) + 0.5)
    l, t, r, b = live.GAME_AREA
    # look so the group lands in the middle of the free game area
    cam = look_at(io, (x0 + x1) / 2 - ((l + r) / 2 - live.CENTRE[0]) / live.ZOOM,
                  (y0 + y1) / 2 - ((t + b) / 2 - live.CENTRE[1]) / live.ZOOM)
    sx0, sy0 = live.on_screen(x0, y0, cam)
    sx1, sy1 = live.on_screen(x1, y1, cam)
    box = (max(l + 4, sx0 - MARGIN), max(t + 4, sy0 - MARGIN),
           min(r - 4, sx1 + MARGIN), min(b - 4, sy1 + MARGIN))
    if box[2] - box[0] < 40 or box[3] - box[1] < 40:
        return False
    io.drag(*box)
    io.sleep(0.1)
    counts.boxes += 1
    if not live.units_selected(io.shot("box", keep=False)):
        counts.empty += 1
        if watch:
            watch.forget(pixels)        # nothing there: not units
        return False
    io.key("a")
    io.sleep(0.08)
    io.click(tx, ty)
    io.sleep(0.08)
    return True


def at_mass(pixels):
    c, r = live.to_drawn(*MASS)
    return {p for p in pixels
            if abs(p[0] - c) <= MASS_RADIUS and abs(p[1] - r) <= MASS_RADIUS}


# ------------------------------------------------------------ the steps
def train_everywhere(io, mapdata):
    gx, gy = live.minimap_point(*MASS)
    l, t, r, btm = live.GAME_AREA

    def one(n, b):
        cam = look_at(io, b["x"], b["y"], wait=0.3)
        px, py = live.on_screen(b["x"], b["y"], cam)
        for k, (dx, dy) in enumerate(TRIES):
            x, y = px + dx, py + dy
            if not (l + 5 < x < r - 5 and t + 5 < y < btm - 5):
                continue
            io.click(x, y)
            io.sleep(0.15)
            if live.barracks_selected(io.shot("try", keep=False)):
                io.click(gx, gy, button="right")          # rally point
                io.sleep(0.08)
                for _ in range(MARINES_PER_BARRACKS):
                    io.key("m")
                    io.sleep(0.05)
                return True
        return False

    todo = list(enumerate(barracks_of(mapdata)))
    missed = [(n, b) for n, b in todo if not one(n, b)]
    still = [(n, b) for n, b in missed if not one(n, b)]     # one more go
    for n, b in still:
        io.log(f"barracks {n}: NOT selected")
    found = len(todo) - len(still)
    io.log(f"marines started at {found} barracks")
    return found


def first_orders(io, watch, mx, my, counts, t0):
    """Order the starting army to the massing place: biggest groups
    first, until the time for this round is up."""
    pixels = watch.units(io.shot("before-orders"))
    pixels -= at_mass(pixels)
    orders = 0
    for group in live.clusters(pixels, *GROUP):
        if io.now() - t0 > FIRST_ORDERS_UNTIL:
            break
        if len(group) < 3:
            continue                    # a stray dot: not worth a trip
        orders += order_group(io, group, mx, my, counts, watch)
    io.log(f"starting army: {orders} groups ordered to the massing place")
    return orders


def wait_for_mass(io, watch, mx, my, counts, t0):
    """Watch the mass grow. While waiting, pick up groups that are
    standing still away from it. Returns when it is time to attack."""
    tried, history = set(), []
    while True:
        a = watch.units(io.shot("watch", keep=False))
        io.sleep(1.0)
        b = watch.units(io.shot("watch", keep=False))
        now = io.now() - t0
        massed = len(at_mass(b))
        history.append((now, massed))
        if now >= WAVE_LATEST:
            why = "time is up"
            break
        old = [m for (t, m) in history if t <= now - 6]
        if now >= WAVE_EARLIEST and old and massed <= old[-1] * 1.04:
            why = "the mass stopped growing"
            break
        idle = (a & b) - at_mass(b)                 # same place both looks
        for group in live.clusters(idle, *GROUP)[:3]:
            key = min(group)
            if len(group) >= 4 and key not in tried:
                tried.add(key)
                order_group(io, group, mx, my, counts, watch)
    io.shot("mass")
    io.log(f"mass at {now:.0f} s: {massed} minimap pixels of units there "
           f"({why})")
    return massed


def launch_wave(io, watch, mapdata, counts, t0):
    """Send the mass at the target, group by group from the side
    nearest the target, until the massing place is nearly empty."""
    w = place(mapdata, TARGET)
    tx, ty = live.minimap_point(w["x"], w["y"])
    start = None
    orders = 0
    for sweep in range(6):
        a = watch.units(io.shot(f"wave-sweep{sweep}"))
        there = at_mass(a)
        if sweep:
            io.sleep(0.8)                           # only those standing still
            there &= watch.units(io.shot("watch", keep=False))
        start = start or max(len(there), 1)
        if len(there) < 0.15 * start or io.now() - t0 > WAVE_STOP:
            break
        groups = live.clusters(there, 3, 3)
        toward = 1 if w["x"] > MASS[0] else -1
        groups.sort(key=lambda g: -toward * min(p[0] for p in g))
        for group in groups:
            orders += order_group(io, group, tx, ty, counts, watch)
    io.log(f"wave: {orders} groups sent toward {TARGET}")
    return orders


def run(io, mapdata=None):
    """Returns a short result for the log."""
    mapdata = mapdata or load_map()
    side = mapdata["slots"][SLOT]
    first = io.shot("start")
    watch = live.Watch(first, side["structures"], side["units"])
    if not live.minimap_showing(first) or not watch.ok:
        io.log("The live game's minimap is not on screen. Nothing done.")
        return {"trained": 0, "gathered": 0, "sent": 0}
    t0, counts = io.now(), Counts()
    mx, my = live.minimap_point(*MASS)
    trained = train_everywhere(io, mapdata)
    io.log(f"  ({io.now() - t0:.0f} s since start)")
    gathered = first_orders(io, watch, mx, my, counts, t0)
    io.log(f"  ({io.now() - t0:.0f} s since start)")
    wait_for_mass(io, watch, mx, my, counts, t0)
    wave_at = io.now() - t0
    sent = launch_wave(io, watch, mapdata, counts, t0)
    io.log(f"  ({io.now() - t0:.0f} s since start); "
           f"{counts.boxes} boxes, {counts.empty} empty")
    w = place(mapdata, TARGET)
    for wait in (15, 20):
        io.sleep(wait)
        look_at(io, w["x"], w["y"])
        io.shot("target")
    return {"trained": trained, "gathered": gathered, "sent": sent,
            "wave_at": round(wave_at), "boxes": counts.boxes,
            "empty": counts.empty}
