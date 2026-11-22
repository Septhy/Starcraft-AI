"""Trial: Russia's opening. Gather everything, then hit as one wave.

What Russia players do in the replays, and what this copies:
  1. In the first seconds, start marines at every barracks, with the
     rally point at the gathering place west of Smolensk.
  2. Order the whole starting army (about 175 units spread over the
     east) to the gathering place.
  3. Send everything at the gathering place west together.

The steps only use an `io` object (see hands/win.py for the real one),
so they can be tested without Windows or the game.

Nothing is recognised by sight except two buttons. The map file says
where Russia's barracks and starting units stand, so the bot moves the
view there with the minimap and clicks or drags where they should be.
It presses M only when the screen shows a barracks is selected, and
gives an order only when the screen shows units are selected.
"""
import json

from eyes import live

SLOT = "5"                 # Russia
TARGET = "Warsaw 200"
GATHER = (160 * 32, 74 * 32)   # map pixels: where the army gathers
MARINES_PER_BARRACKS = 5   # a building queues at most five
# Where to try clicking, relative to where the barracks should appear.
TRIES = [(0, 0), (40, 80), (-60, 0), (60, 0), (0, -70), (0, 150), (-90, 90)]
MARGIN = 130               # pixels: how far off a predicted position may be
GRID = (4, 3)              # the view is swept in this many boxes
WAVE_AT = 170              # seconds after the start: send the wave
WAVE_SWEEPS = 6            # at most this many sweeps of the gathering place


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


def look_at(io, x, y, wait=0.3):
    """Move the view to a map point. Returns the camera centre."""
    mx, my = live.minimap_point(x, y)
    io.click(mx, my)
    io.sleep(wait)
    return live.camera_after_click(mx, my)


def boxes():
    """The game area cut into GRID boxes: (left, top, right, bottom)."""
    l, t, r, b = live.GAME_AREA
    w, h = (r - l) / GRID[0], (b - t) / GRID[1]
    return [(int(l + i * w) + 4, int(t + j * h) + 4,
             int(l + (i + 1) * w) - 4, int(t + (j + 1) * h) - 4)
            for j in range(GRID[1]) for i in range(GRID[0])]


def order_box(io, box, tx, ty, label):
    """Select what is in the box; if units were picked up, attack-move
    them to the minimap point. Returns True if an order was given."""
    io.drag(*box)
    io.sleep(0.12)
    if not live.units_selected(io.shot(label, keep=False)):
        return False
    io.key("a")
    io.sleep(0.1)
    io.click(tx, ty)
    io.sleep(0.1)
    return True


# ------------------------------------------------------------ the steps
def train_everywhere(io, mapdata):
    gx, gy = live.minimap_point(*GATHER)
    l, t, r, btm = live.GAME_AREA
    found = 0
    for n, b in enumerate(barracks_of(mapdata)):
        cam = look_at(io, b["x"], b["y"])
        px, py = live.on_screen(b["x"], b["y"], cam)
        for k, (dx, dy) in enumerate(TRIES):
            x, y = px + dx, py + dy
            if not (l + 5 < x < r - 5 and t + 5 < y < btm - 5):
                continue
            io.click(x, y)
            io.sleep(0.15)
            if live.barracks_selected(io.shot(f"b{n}-try{k}", keep=False)):
                io.click(gx, gy, button="right")          # rally point
                io.sleep(0.08)
                for _ in range(MARINES_PER_BARRACKS):
                    io.key("m")
                    io.sleep(0.05)
                found += 1
                break
        else:
            io.log(f"barracks {n}: NOT selected (expected near {px},{py})")
            io.shot(f"b{n}-missed")
    io.log(f"marines started at {found} barracks")
    return found


def views_of(units):
    """Camera positions that between them show every starting unit:
    the map cut into view-sized blocks, keeping the blocks with units,
    farthest from the gathering place first."""
    l, t, r, b = live.GAME_AREA
    bw, bh = (r - l - 2 * MARGIN) / live.ZOOM, (b - t - 2 * MARGIN) / live.ZOOM
    blocks = {}
    for x, y in units:
        blocks.setdefault((int(x // bw), int(y // bh)), []).append((x, y))
    out = []
    for (i, j), us in blocks.items():
        out.append(((i + 0.5) * bw, (j + 0.5) * bh, us))
    far = lambda v: -((v[0] - GATHER[0]) ** 2 + (v[1] - GATHER[1]) ** 2)
    return sorted(out, key=far)


def gather_starting_army(io, mapdata):
    gx, gy = live.minimap_point(*GATHER)
    l, t, r, b = live.GAME_AREA
    # look so that the block lands in the middle of the free game area
    off_x = ((l + r) / 2 - live.CENTRE[0]) / live.ZOOM
    off_y = ((t + b) / 2 - live.CENTRE[1]) / live.ZOOM
    orders = 0
    for v, (cx, cy, units) in enumerate(views_of(mapdata["slots"][SLOT]["units"])):
        cam = look_at(io, cx - off_x, cy - off_y)
        seen = [live.on_screen(x, y, cam) for x, y in units]
        for k, box in enumerate(boxes()):
            near = any(box[0] - MARGIN < sx < box[2] + MARGIN and
                       box[1] - MARGIN < sy < box[3] + MARGIN
                       for sx, sy in seen)
            if near and order_box(io, box, gx, gy, f"g{v}-{k}"):
                orders += 1
        if v % 6 == 0:
            io.shot(f"gather-view{v}")
    io.log(f"starting army: {orders} groups ordered to the gathering place")
    return orders


def launch_wave(io, mapdata):
    """Sweep the gathering place box by box, sending each group west,
    again and again until a whole sweep finds nobody left."""
    w = place(mapdata, TARGET)
    tx, ty = live.minimap_point(w["x"], w["y"])
    l, t, r, b = live.GAME_AREA
    off_x = ((l + r) / 2 - live.CENTRE[0]) / live.ZOOM
    off_y = ((t + b) / 2 - live.CENTRE[1]) / live.ZOOM
    # a big army stands wider than one screen: sweep four overlapping views
    dx, dy = (r - l) / live.ZOOM / 3, (b - t) / live.ZOOM / 3
    views = [(GATHER[0] + i * dx - off_x, GATHER[1] + j * dy - off_y)
             for i in (-1, 1) for j in (-1, 1)]
    orders = 0
    for sweep in range(WAVE_SWEEPS):
        found = 0
        for v, (vx, vy) in enumerate(views):
            look_at(io, vx, vy)
            if v == 0:
                io.shot(f"wave-sweep{sweep}")
            for k, box in enumerate(boxes()):
                if order_box(io, box, tx, ty, f"w{sweep}-{v}-{k}"):
                    found += 1
                    # if the order did not take, that click moved the view
                    look_at(io, vx, vy, wait=0.15)
        orders += found
        if not found:
            break
    io.log(f"wave: {orders} groups sent toward {TARGET}")
    return orders


def run(io, mapdata=None):
    """Returns a short result for the log."""
    mapdata = mapdata or load_map()
    if not live.minimap_showing(io.shot("start")):
        io.log("The live game's minimap is not on screen. Nothing done.")
        return {"trained": 0, "gathered": 0, "sent": 0}
    t0 = io.now()
    trained = train_everywhere(io, mapdata)
    io.log(f"  ({io.now() - t0:.0f} s since start)")
    gathered = gather_starting_army(io, mapdata)
    io.log(f"  ({io.now() - t0:.0f} s since start)")
    io.sleep(max(0, WAVE_AT - (io.now() - t0)))
    sent = launch_wave(io, mapdata)
    io.log(f"  ({io.now() - t0:.0f} s since start)")
    w = place(mapdata, TARGET)
    for wait in (20, 20):
        io.sleep(wait)
        look_at(io, w["x"], w["y"])
        io.shot("target")
    return {"trained": trained, "gathered": gathered, "sent": sent}
