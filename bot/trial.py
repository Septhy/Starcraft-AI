"""Trial: Russia's opening and follow-up hits, after qororo98's games.

What the replays show Russia doing, and what this copies:
  1. In the first seconds, send a scout to the Middle East. The map
     gives Russia 32 marines and 4,000 minerals when one of its units
     arrives there.
  2. Start marines at every barracks, rallying to the massing place
     west of Smolensk.
  3. Order most of the starting army (about 175 units) to the massing
     place, putting groups on the number keys as it goes: air groups on
     9 and 0, ground groups on 1 to 8.
  4. Bring the Middle East marines over too.
  5. When the mass is there, hit Berlin: the number-key groups at once,
     each to its own point across Berlin's front, then everything else
     at the massing place from the back to the front, then the air.
  6. Fly the Smolensk barracks to Warsaw, to take Warsaw's tax. Tax is
     paid when the round timer reaches 2:00, to whoever has a building
     at a city while the other sides have none. Floating counts.
  7. Keep going: train again, let a new mass build, hit again. Not
     always Berlin: the second hit goes to Romania, and a starport is
     flown there for its tax; the third goes to Belgrade, where the
     Balkan factory is. That factory goes to whoever has a building
     there with the round timer between 5:00 and 2:00, and then pays
     out units each round at 2:00.

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
# Where each hit goes. "Factory 7" is the factory at Belgrade.
TARGETS = ["Berlin 1000", "Romania 300", "Factory 7", "Berlin 1000"]
# Points across a target's front, in tiles from its centre. Each group
# is sent to its own, so the army arrives as a wall, not a line.
FRONT = [(4, -5), (4, -1), (4, 3), (6, -3), (6, 1), (6, 5), (2, -3),
         (2, 1), (0, 5), (2, -7)]
MASS = (160 * 32, 76 * 32)     # map pixels: where the army masses
MASS_RADIUS = 13               # minimap pixels around it that count as there
MIDDLE_EAST = (219 * 32, 129 * 32)   # bring a unit here for the spawn
# Buildings to fly to a city, each after the hit with that number has
# been sent: (hit, kind of building, its tile, the city). A building
# floating over a city counts as holding it.
FLIGHTS = [(1, "Barracks", (173, 80), "Warsaw 200"),     # Smolensk's
           (2, "Starport", (190, 110), "Romania 300")]   # Sevastopol's
MARINES_PER_BARRACKS = 5       # a building queues at most five
# Where to try clicking, relative to where the barracks should appear.
TRIES = [(0, 0), (40, 80), (-60, 0), (60, 0), (0, -70), (0, 150), (-90, 90)]
MARGIN = 100                   # screen pixels added round a group for the box
GROUP = (8, 4)                 # a group is at most this many minimap pixels wide, tall
CELLS = (8, 3)                 # the view is cut into this many boxes at the mass
GROUND_KEYS = list("12345678")
AIR_KEYS = list("90")
FIRST_ORDERS_UNTIL = 45        # seconds: stop the first round of orders
WAVE_EARLIEST = 55             # seconds: do not hit before this
WAVE_LATEST = 100              # seconds: hit by now whatever happens
LATER_HITS = 3                 # how many more hits to try after the first
LATER_WAIT = 45                # seconds to let each new mass build


class Stopped(Exception):
    pass


class State:
    def __init__(self):
        self.boxes = self.empty = 0
        self.ground_keys, self.air_keys = [], []
        self.orders_sent = 0       # counts hit orders, to walk along FRONT
        self.flown = set()         # barracks (tiles) that have been flown off


def load_map():
    return json.load(open(live.data_path("af40.json")))


def barracks_of(mapdata, slot=SLOT):
    s = mapdata["slots"][slot]
    sx, sy = s["start"]
    b = [b for b in s["buildings"] if b["type"] == "Barracks"]
    return sorted(b, key=lambda b: (b["x"] - sx) ** 2 + (b["y"] - sy) ** 2)


def place(mapdata, name):
    return next(p for p in mapdata["places"] if p["name"] == name)


def front_point(mapdata, st, target):
    """The next point along the target's front, in map pixels."""
    w = place(mapdata, target)
    dx, dy = FRONT[st.orders_sent % len(FRONT)]
    st.orders_sent += 1
    return w["x"] + dx * 32, w["y"] + dy * 32


def look_at(io, x, y, wait=0.15):
    """Move the view to a map point. Returns the camera centre."""
    mx, my = live.minimap_point(x, y)
    io.click(mx, my)
    io.sleep(wait)
    return live.camera_after_click(mx, my)


def centred(x, y):
    """Where to look so a map point lands in the middle of the free
    game area (the screen above the panels)."""
    l, t, r, b = live.GAME_AREA
    return (x - ((l + r) / 2 - live.CENTRE[0]) / live.ZOOM,
            y - ((t + b) / 2 - live.CENTRE[1]) / live.ZOOM)


def box_and_check(io, box, st):
    """Drag a box. True if the screen then shows units selected."""
    io.drag(*box)
    io.sleep(0.07)
    st.boxes += 1
    if live.units_selected(io.card()):
        return True
    st.empty += 1
    return False


def select_group(io, pixels, st, watch=None):
    """Look at the units drawn at these minimap pixels and box them."""
    cols = [p[0] for p in pixels]
    rows = [p[1] for p in pixels]
    x0, y0 = live.from_drawn(min(cols) - 0.5, min(rows) - 0.5)
    x1, y1 = live.from_drawn(max(cols) + 0.5, max(rows) + 0.5)
    l, t, r, b = live.GAME_AREA
    cam = look_at(io, *centred((x0 + x1) / 2, (y0 + y1) / 2))
    sx0, sy0 = live.on_screen(x0, y0, cam)
    sx1, sy1 = live.on_screen(x1, y1, cam)
    box = (max(l + 4, sx0 - MARGIN), max(t + 4, sy0 - MARGIN),
           min(r - 4, sx1 + MARGIN), min(b - 4, sy1 + MARGIN))
    if box[2] - box[0] < 40 or box[3] - box[1] < 40:
        return False
    if box_and_check(io, box, st):
        return True
    if watch:
        watch.forget(pixels)            # nothing there: not units
    return False


def attack_move(io, map_x, map_y):
    """Attack-move whatever is selected to a map point."""
    io.key("a")
    io.sleep(0.06)
    io.click(*live.minimap_point(map_x, map_y))
    io.sleep(0.06)


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
    if not select_group(io, [live.to_drawn(a["x"], a["y"]) for a in pair], st):
        io.log("scout: not found")
        return False
    io.click(*live.minimap_point(*MIDDLE_EAST), button="right")
    io.sleep(0.06)
    io.log("scout sent to the Middle East")
    return True


def select_barracks(io, b):
    """Look at a barracks and click it. True once the screen shows a
    barracks selected."""
    l, t, r, btm = live.GAME_AREA
    cam = look_at(io, b["x"], b["y"], wait=0.25)
    px, py = live.on_screen(b["x"], b["y"], cam)
    for dx, dy in TRIES:
        x, y = px + dx, py + dy
        if not (l + 5 < x < r - 5 and t + 5 < y < btm - 5):
            continue
        io.click(x, y)
        io.sleep(0.12)
        if live.barracks_selected(io.card()):
            return True
    return False


def train_everywhere(io, mapdata, st):
    gx, gy = live.minimap_point(*MASS)

    def one(b):
        if not select_barracks(io, b):
            return False
        io.click(gx, gy, button="right")                  # rally point
        io.sleep(0.06)
        for _ in range(MARINES_PER_BARRACKS):
            io.key("m")
            io.sleep(0.04)
        return True

    todo = [b for b in barracks_of(mapdata)
            if (b["x"] // 32, b["y"] // 32) not in st.flown]
    missed = [b for b in todo if not one(b)]
    still = [b for b in missed if not one(b)]             # one more go
    found = len(todo) - len(still)
    io.log(f"marines started at {found} of {len(todo)} barracks")
    return found


def air_groups(mapdata):
    """Russia's starting air units that stay with the army, as groups of
    units standing together."""
    air = [a for a in mapdata["slots"][SLOT]["air"]]
    d = lambda a: (a["x"] - MIDDLE_EAST[0]) ** 2 + (a["y"] - MIDDLE_EAST[1]) ** 2
    scouts = sorted([a for a in air if a["type"] == "Scout"], key=d)[:2]
    rest = [a for a in air if a not in scouts]
    groups = []
    for a in rest:
        for g in groups:
            if abs(g[0]["x"] - a["x"]) < 12 * 32 and abs(g[0]["y"] - a["y"]) < 8 * 32:
                g.append(a)
                break
        else:
            groups.append([a])
    return groups


def first_orders(io, watch, mapdata, st, t0):
    """Order the starting army to the massing place: the air first, on
    keys 9 and 0, then the ground groups, biggest first, on 1 to 8."""
    orders = 0
    air_px = set()
    for group in air_groups(mapdata)[:len(AIR_KEYS)]:
        pixels = [live.to_drawn(a["x"], a["y"]) for a in group]
        air_px.update(pixels)
        if select_group(io, pixels, st):
            attack_move(io, *MASS)
            key = AIR_KEYS[len(st.air_keys)]
            io.combo("ctrl", key)
            io.sleep(0.04)
            st.air_keys.append(key)
            orders += 1
    pixels = watch.units(io.shot("before-orders"))
    pixels -= at_mass(pixels)
    pixels -= near(pixels, MIDDLE_EAST, 6)
    pixels = {p for p in pixels if not any(
        abs(p[0] - c) <= 3 and abs(p[1] - r) <= 3 for c, r in air_px)}
    for group in live.clusters(pixels, *GROUP):
        if io.now() - t0 > FIRST_ORDERS_UNTIL:
            break
        if len(group) < 3:
            continue                    # a stray dot: not worth a trip
        if not select_group(io, group, st, watch):
            continue
        attack_move(io, *MASS)
        orders += 1
        if len(st.ground_keys) < len(GROUND_KEYS):
            key = GROUND_KEYS[len(st.ground_keys)]
            io.combo("ctrl", key)
            io.sleep(0.04)
            st.ground_keys.append(key)
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


def at_home(pixels, mapdata):
    """Leave out units that have gone forward: only pixels farther from
    Berlin than the massing place, and not near any target, count as
    still at home and may be called to the mass."""
    w = place(mapdata, TARGETS[0])
    tc, tr = live.to_drawn(w["x"], w["y"])
    mc, mr = live.to_drawn(*MASS)
    reach = ((mc - tc) ** 2 + (mr - tr) ** 2) ** 0.5 - MASS_RADIUS
    out = {p for p in pixels
           if ((p[0] - tc) ** 2 + (p[1] - tr) ** 2) ** 0.5 > reach}
    for name in set(TARGETS) | {f[3] for f in FLIGHTS}:
        t = place(mapdata, name)
        out -= near(out, (t["x"], t["y"]), 22)
    return out


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
        idle = at_home((a & b) - at_mass(b) - near(b, MIDDLE_EAST, 6), mapdata)
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


def back_to_front(items, target_xy, where):
    """Order things so the ones farthest from the target go first.

    Sent front first, the army strings out into a thin line on the way
    (a "conga line"). Sent back first, the rear catches up with the
    front as the front sets off, and it arrives as a wall.
    `where(item)` gives an item's place in map pixels."""
    def far(item):
        x, y = where(item)
        return -((x - target_xy[0]) ** 2 + (y - target_xy[1]) ** 2)
    return sorted(items, key=far)


def sweep_mass(io, watch, mapdata, st, target):
    """One pass over the massing place: look at it once or twice, and
    box every part of the view where the minimap shows units standing
    still, back to front. Returns (orders given, pixels found)."""
    w = place(mapdata, target)
    a = watch.units(io.shot("sweep"))
    io.sleep(1.2)                       # only those still standing there
    there = at_mass(a) & watch.units(io.shot("watch", keep=False))
    if len(there) < 12:
        return 0, len(there)
    l, t, r, b = live.GAME_AREA
    cw, ch = (r - l) / CELLS[0], (b - t) / CELLS[1]
    orders = 0
    # the mass is often wider than one view: take it a view at a time
    views = back_to_front(live.clusters(there, 20, 8), (w["x"], w["y"]),
                          lambda g: live.from_drawn(*g[0]))
    for view in views:
        cols = [p[0] for p in view]
        rows = [p[1] for p in view]
        cx, cy = live.from_drawn((min(cols) + max(cols)) / 2,
                                 (min(rows) + max(rows)) / 2)
        cam = look_at(io, *centred(cx, cy))
        cells = {}
        for p in view:
            sx, sy = live.on_screen(*live.from_drawn(*p), cam)
            i, j = int((sx - l) // cw), int((sy - t) // ch)
            if 0 <= i < CELLS[0] and 0 <= j < CELLS[1]:
                cells.setdefault((i, j), []).append(p)
        order = back_to_front(list(cells), (w["x"], w["y"]),
                              lambda c: live.from_drawn(*cells[c][0]))
        for i, j in order:
            if len(cells[(i, j)]) < 2:
                continue                # the edge of a neighbour's block
            box = (int(l + i * cw) + 3, int(t + j * ch) + 3,
                   int(l + (i + 1) * cw) - 3, int(t + (j + 1) * ch) - 3)
            if box_and_check(io, box, st):
                attack_move(io, *front_point(mapdata, st, target))
                orders += 1
            else:
                watch.forget(cells[(i, j)])
    return orders, len(there)


def hit(io, watch, mapdata, st, target, use_keys=True):
    """Send the mass at the target as a wall."""
    orders = 0
    if use_keys:
        for key in st.ground_keys:      # all the key groups in a few seconds
            io.key(key)
            io.sleep(0.05)
            attack_move(io, *front_point(mapdata, st, target))
            orders += 1
        io.sleep(1.5)                   # let them step off
    start = None
    for sweep in range(4):
        n, found = sweep_mass(io, watch, mapdata, st, target)
        orders += n
        start = start or max(found, 1)
        if n == 0 or found < 0.15 * start:
            break
        io.sleep(1.5)
    if use_keys:
        for key in st.air_keys:         # air is fastest, so it goes last
            io.key(key)
            io.sleep(0.05)
            attack_move(io, *front_point(mapdata, st, target))
            orders += 1
    io.log(f"hit: {orders} groups sent at {target}")
    return orders


def round_timer(seconds_in):
    """What the round's countdown shows, given the seconds since the
    game began. Rounds are five minutes; tax is paid at 2:00."""
    left = 300 - int(seconds_in) % 300
    return f"{left // 60}:{left % 60:02d}"


def fly_building(io, mapdata, st, kind, tile, city_name):
    """Lift a building and send it to float over a city."""
    b = next((b for b in mapdata["slots"][SLOT]["buildings"]
              if b["type"] == kind and (b["x"] // 32, b["y"] // 32) == tile),
             None)
    if not b:
        return False
    l, t, r, btm = live.GAME_AREA
    cam = look_at(io, b["x"], b["y"], wait=0.25)
    px, py = live.on_screen(b["x"], b["y"], cam)
    for dx, dy in TRIES:
        x, y = px + dx, py + dy
        if not (l + 5 < x < r - 5 and t + 5 < y < btm - 5):
            continue
        io.click(x, y)
        io.sleep(0.12)
        if live.building_selected(io.card()):
            break
    else:
        io.log(f"flight: the {kind} was not found")
        return False
    io.key("l")                         # lift off
    io.sleep(0.3)
    city = place(mapdata, city_name)
    io.click(*live.minimap_point(city["x"], city["y"]), button="right")
    io.sleep(0.1)
    io.shot("flight-" + city_name.split()[0])
    if kind == "Barracks":
        st.flown.add(tile)
    io.log(f"flight: {kind} lifted and sent to {city_name}")
    return True


def flights_after(io, mapdata, st, hit_number):
    for n, kind, tile, city in FLIGHTS:
        if n == hit_number:
            fly_building(io, mapdata, st, kind, tile, city)


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
    trained = train_everywhere(io, mapdata, st)
    io.log(f"  ({since()} since start)")
    gathered = first_orders(io, watch, mapdata, st, t0)
    io.log(f"  ({since()} since start)")
    wait_for_mass(io, watch, mapdata, st, t0, WAVE_EARLIEST, WAVE_LATEST)
    hit_at = round(io.now() - t0)
    hits = [hit(io, watch, mapdata, st, TARGETS[0])]
    io.log(f"  first hit sent by {since()}; {st.boxes} boxes, "
           f"{st.empty} empty")
    flights_after(io, mapdata, st, 1)
    for n in range(LATER_HITS):
        target = TARGETS[(n + 1) % len(TARGETS)]
        train_everywhere(io, mapdata, st)
        start = io.now() - t0
        massed = wait_for_mass(io, watch, mapdata, st, t0,
                               start + LATER_WAIT, start + LATER_WAIT + 15)
        if massed >= 30:
            hits.append(hit(io, watch, mapdata, st, target, use_keys=False))
            flights_after(io, mapdata, st, n + 2)
        else:
            io.log(f"hit {n + 2}: no new mass to send")
            hits.append(0)
        io.log(f"  ({since()} since start; round timer about "
               f"{round_timer(io.now() - t0)})")
    for name in ("Berlin 1000", "Warsaw 200", "Romania 300", "Factory 7"):
        w = place(mapdata, name)
        look_at(io, w["x"], w["y"], wait=0.5)
        io.shot("at-" + name.split()[0])
    return {"trained": trained, "gathered": gathered, "hit_at": hit_at,
            "hits": hits, "keys": "".join(st.ground_keys + st.air_keys),
            "boxes": st.boxes, "empty": st.empty}
