"""Trial: Russia's opening and follow-up hits, after qororo98's games.

What the replays show Russia doing, and what this copies:
  1. In the first seconds, send a scout to the Middle East. The map
     gives Russia 32 marines and 4,000 minerals when one of its units
     arrives there.
  2. Start marines at every barracks, rallying to the massing place
     west of Smolensk.
  3. Order most of the starting army (about 175 units) to the massing
     place, putting groups on the number keys as it goes: ground groups
     on 1 to 8, air groups on 9 and 0.
  4. Bring the Middle East marines over too.
  5. When the mass is there, hit Berlin: the number-key groups first,
     each to its own point across Berlin's front, then everything else
     at the massing place from the back to the front, then the air.
  6. Keep going: train again, let a new mass build, hit again.

The steps only use an `io` object (see hands/win.py for the real one),
so they can be tested without Windows or the game.

How it sees: the minimap shows where its own units are (eyes/live.py,
Watch). It boxes only where units are, watches the mass build up, and
gives an order only when the screen shows units are selected. It does
not see the enemy yet.
"""
import json

from eyes import live

SLOT = "5"                     # Russia
TARGET = "Berlin 1000"
# Points across Berlin's front, in tiles from Berlin's centre. Each
# group is sent to its own, so the army arrives as a wall, not a line.
FRONT = [(4, -5), (4, -1), (4, 3), (6, -3), (6, 1), (6, 5), (2, -3),
         (2, 1), (0, 5), (2, -7)]
MASS = (160 * 32, 76 * 32)     # map pixels: where the army masses
MASS_RADIUS = 13               # minimap pixels around it that count as there
MIDDLE_EAST = (219 * 32, 129 * 32)   # bring a unit here for the spawn
MARINES_PER_BARRACKS = 5       # a building queues at most five
# Where to try clicking, relative to where the barracks should appear.
TRIES = [(0, 0), (40, 80), (-60, 0), (60, 0), (0, -70), (0, 150), (-90, 90)]
MARGIN = 120                   # screen pixels added round a group for the box
GROUP = (8, 4)                 # a group is at most this many minimap pixels wide, tall
GROUND_KEYS = list("12345678")
AIR_KEYS = list("90")
FIRST_ORDERS_UNTIL = 50        # seconds: stop the first round of orders
WAVE_EARLIEST = 60             # seconds: do not hit before this
WAVE_LATEST = 105              # seconds: hit by now whatever happens
LATER_HITS = 3                 # how many more hits to try after the first
LATER_WAIT = 45                # seconds to let each new mass build


class Stopped(Exception):
    pass


class State:
    def __init__(self):
        self.boxes = self.empty = 0
        self.ground_keys, self.air_keys = [], []
        self.orders_sent = 0       # counts hit orders, to walk along FRONT


def load_map():
    return json.load(open(live.data_path("af40.json")))


def barracks_of(mapdata, slot=SLOT):
    s = mapdata["slots"][slot]
    sx, sy = s["start"]
    b = [b for b in s["buildings"] if b["type"] == "Barracks"]
    return sorted(b, key=lambda b: (b["x"] - sx) ** 2 + (b["y"] - sy) ** 2)


def place(mapdata, name):
    return next(p for p in mapdata["places"] if p["name"] == name)


def front_point(mapdata, st):
    """The next point along the target's front, in map pixels."""
    w = place(mapdata, TARGET)
    dx, dy = FRONT[st.orders_sent % len(FRONT)]
    st.orders_sent += 1
    return w["x"] + dx * 32, w["y"] + dy * 32


def look_at(io, x, y, wait=0.2):
    """Move the view to a map point. Returns the camera centre."""
    mx, my = live.minimap_point(x, y)
    io.click(mx, my)
    io.sleep(wait)
    return live.camera_after_click(mx, my)


def select_group(io, pixels, st, watch=None):
    """Box the units drawn at these minimap pixels. True if the screen
    then shows units selected."""
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
    st.boxes += 1
    if live.units_selected(io.shot("box", keep=False)):
        return True
    st.empty += 1
    if watch:
        watch.forget(pixels)            # nothing there: not units
    return False


def attack_move(io, map_x, map_y):
    """Attack-move whatever is selected to a map point."""
    io.key("a")
    io.sleep(0.08)
    io.click(*live.minimap_point(map_x, map_y))
    io.sleep(0.08)


def near(pixels, map_xy, radius):
    c, r = live.to_drawn(*map_xy)
    return {p for p in pixels
            if abs(p[0] - c) <= radius and abs(p[1] - r) <= radius}


def at_mass(pixels):
    return near(pixels, MASS, MASS_RADIUS)


# ------------------------------------------------------------ the steps
def send_scout(io, mapdata, st):
    """Send the two scouts that start nearest the Middle East there."""
    air = [a for a in mapdata["slots"][SLOT]["air"] if a["type"] == "Scout"]
    d = lambda a: (a["x"] - MIDDLE_EAST[0]) ** 2 + (a["y"] - MIDDLE_EAST[1]) ** 2
    pair = sorted(air, key=d)[:2]
    if not pair:
        return False
    pixels = [live.to_drawn(a["x"], a["y"]) for a in pair]
    if not select_group(io, pixels, st):
        io.log("scout: not found")
        return False
    io.click(*live.minimap_point(*MIDDLE_EAST), button="right")
    io.sleep(0.08)
    io.log("scout sent to the Middle East")
    return True


def train_everywhere(io, mapdata):
    gx, gy = live.minimap_point(*MASS)
    l, t, r, btm = live.GAME_AREA

    def one(b):
        cam = look_at(io, b["x"], b["y"], wait=0.3)
        px, py = live.on_screen(b["x"], b["y"], cam)
        for dx, dy in TRIES:
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

    todo = barracks_of(mapdata)
    missed = [b for b in todo if not one(b)]
    still = [b for b in missed if not one(b)]             # one more go
    found = len(todo) - len(still)
    io.log(f"marines started at {found} of {len(todo)} barracks")
    return found


def first_orders(io, watch, mapdata, st, t0):
    """Order the starting army to the massing place, biggest groups
    first, putting each on a number key while keys remain."""
    pixels = watch.units(io.shot("before-orders"))
    pixels -= at_mass(pixels)
    pixels -= near(pixels, MIDDLE_EAST, 6)
    air = [live.to_drawn(a["x"], a["y"])
           for a in mapdata["slots"][SLOT]["air"]]
    orders = 0
    for group in live.clusters(pixels, *GROUP):
        if io.now() - t0 > FIRST_ORDERS_UNTIL:
            break
        if len(group) < 3:
            continue                    # a stray dot: not worth a trip
        if not select_group(io, group, st, watch):
            continue
        attack_move(io, *MASS)
        orders += 1
        is_air = any(abs(c - ac) <= 3 and abs(r - ar) <= 3
                     for c, r in group for ac, ar in air)
        free, used = (AIR_KEYS, st.air_keys) if is_air else \
            (GROUND_KEYS, st.ground_keys)
        if len(used) < len(free):
            key = free[len(used)]
            io.combo("ctrl", key)
            io.sleep(0.05)
            used.append(key)
    io.log(f"starting army: {orders} groups ordered to the massing place; "
           f"number keys {''.join(st.ground_keys)} ground, "
           f"{''.join(st.air_keys)} air")
    return orders


def collect_middle_east(io, watch, st):
    """If the Middle East marines have appeared, send them to the mass."""
    there = near(watch.units(io.shot("watch", keep=False)), MIDDLE_EAST, 6)
    orders = 0
    if len(there) >= 40:                # far more than a scout or two
        for group in live.clusters(there, 4, 3)[:6]:
            if select_group(io, group, st, watch):
                attack_move(io, *MASS)
                orders += 1
        io.shot("middle-east")
        io.log(f"Middle East: {orders} groups sent to the massing place")
    return orders


def behind_mass(pixels, mapdata):
    """Only the pixels farther from the target than the massing place:
    units that have gone forward to fight are not to be called back."""
    w = place(mapdata, TARGET)
    tc, tr = live.to_drawn(w["x"], w["y"])
    mc, mr = live.to_drawn(*MASS)
    reach = ((mc - tc) ** 2 + (mr - tr) ** 2) ** 0.5 - MASS_RADIUS
    return {p for p in pixels
            if ((p[0] - tc) ** 2 + (p[1] - tr) ** 2) ** 0.5 > reach}


def wait_for_mass(io, watch, mapdata, st, t0, earliest, latest):
    """Watch the mass grow; meanwhile pick up groups standing still away
    from it. Returns when it is time to hit."""
    tried, history, collected = set(), [], False
    while True:
        a = watch.units(io.shot("watch", keep=False))
        io.sleep(1.0)
        b = watch.units(io.shot("watch", keep=False))
        now = io.now() - t0
        massed = len(at_mass(b))
        history.append((now, massed))
        if now >= latest:
            why = "time is up"
            break
        old = [m for (t, m) in history if t <= now - 6]
        if now >= earliest and old and massed <= old[-1] * 1.04:
            why = "the mass stopped growing"
            break
        if not collected:
            collected = collect_middle_east(io, watch, st) > 0
        idle = behind_mass((a & b) - at_mass(b) - near(b, MIDDLE_EAST, 6),
                           mapdata)
        for group in live.clusters(idle, *GROUP)[:2]:
            key = min(group)
            if len(group) >= 9 and key not in tried and len(tried) < 6:
                tried.add(key)
                if select_group(io, group, st, watch):
                    attack_move(io, *MASS)
    io.shot("mass")
    io.log(f"mass at {now:.0f} s: {massed} minimap pixels of units there "
           f"({why})")
    return massed


def back_to_front(groups, target_x):
    """Order the groups so the ones farthest from the target go first.

    Sent front first, the army strings out into a thin line on the way
    (a "conga line"). Sent back first, the rear catches up with the
    front as the front sets off, and it arrives as a wall."""
    west = target_x < MASS[0]
    middle = lambda g: sum(p[0] for p in g) / len(g)
    return sorted(groups, key=middle, reverse=west)


def hit(io, watch, mapdata, st, use_keys=True):
    """Send the mass at the target as a wall."""
    w = place(mapdata, TARGET)
    orders = 0
    if use_keys:
        for key in st.ground_keys:      # ten seconds' work in about three
            io.key(key)
            io.sleep(0.06)
            attack_move(io, *front_point(mapdata, st))
            orders += 1
    start = None
    for sweep in range(4):
        if orders:
            io.sleep(2.0)               # let those just ordered step off
        a = watch.units(io.shot(f"hit-sweep{sweep}"))
        io.sleep(1.5)                   # only those still standing there
        there = at_mass(a) & watch.units(io.shot("watch", keep=False))
        start = start or max(len(there), 1)
        if len(there) < 12 or (sweep and len(there) < 0.15 * start):
            break
        for group in back_to_front(live.clusters(there, 3, 3), w["x"]):
            if select_group(io, group, st, watch):
                attack_move(io, *front_point(mapdata, st))
                orders += 1
    if use_keys:
        for key in st.air_keys:         # air is fastest, so it goes last
            io.key(key)
            io.sleep(0.06)
            attack_move(io, *front_point(mapdata, st))
            orders += 1
    io.log(f"hit: {orders} groups sent at {TARGET}")
    return orders


def run(io, mapdata=None):
    """Returns a short result for the log."""
    mapdata = mapdata or load_map()
    side = mapdata["slots"][SLOT]
    first = io.shot("start")
    watch = live.Watch(first, side["structures"], side["units"])
    if not live.minimap_showing(first) or not watch.ok:
        io.log("The live game's minimap is not on screen. Nothing done.")
        return {"trained": 0, "gathered": 0, "hits": []}
    t0, st = io.now(), State()
    since = lambda: f"{io.now() - t0:.0f} s"
    send_scout(io, mapdata, st)
    trained = train_everywhere(io, mapdata)
    io.log(f"  ({since()} since start)")
    gathered = first_orders(io, watch, mapdata, st, t0)
    io.log(f"  ({since()} since start)")
    wait_for_mass(io, watch, mapdata, st, t0, WAVE_EARLIEST, WAVE_LATEST)
    hit_at = round(io.now() - t0)
    hits = [hit(io, watch, mapdata, st)]
    io.log(f"  first hit sent by {since()}; {st.boxes} boxes, "
           f"{st.empty} empty")
    w = place(mapdata, TARGET)
    io.sleep(12)
    look_at(io, w["x"], w["y"])
    io.shot("target")
    for n in range(LATER_HITS):
        train_everywhere(io, mapdata)
        start = io.now() - t0
        massed = wait_for_mass(io, watch, mapdata, st, t0, start + LATER_WAIT,
                               start + LATER_WAIT + 15)
        if massed >= 30:
            hits.append(hit(io, watch, mapdata, st, use_keys=False))
        else:
            io.log(f"hit {n + 2}: no new mass to send")
            hits.append(0)
        io.log(f"  ({since()} since start)")
    look_at(io, w["x"], w["y"])
    io.shot("target")
    return {"trained": trained, "gathered": gathered, "hit_at": hit_at,
            "hits": hits, "keys": "".join(st.ground_keys + st.air_keys),
            "boxes": st.boxes, "empty": st.empty}
