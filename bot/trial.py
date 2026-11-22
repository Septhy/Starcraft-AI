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
  7. Keep going, with bigger hits: keep the barracks busy and wait
     until the new mass is large before sending it. Where it goes
     depends on what the minimap shows: south to Romania, and then to
     the factory at Belgrade, when the Axis is in the Balkans; Berlin
     again when it is not. A starport is flown to Romania for its tax
     when the first hit goes there.

The steps only use an `io` object (see hands/win.py for the real one),
so they can be tested without Windows or the game.

How it sees: the minimap shows where its own units are (eyes/live.py,
Watch). It boxes only where units are, watches the mass build up, and
gives an order only when the screen shows units are selected. It reads
the supply number, and does not train at the limit. It sees other
players' colours on the minimap too: it uses that to choose where a
later hit goes, to judge how the last hit is doing (Battle), and to
call the army back when the Axis reaches the massing place. With an
API key, Claude is shown the fight every few seconds and advises
(bot/general.py): keep massing, hit now, or pull back, and where.
"""
import json

from eyes import live, numbers

SLOT = "5"                     # Russia
# The first hit goes to Berlin. Later hits go to Berlin again, or south
# to Romania and then the factory at Belgrade ("Factory 7"). In the
# replays Russia turns south early mostly when the Axis is busy in the
# Balkans, so the bot looks: enough Axis colour there, and it goes south.
TARGETS = ["Berlin 1000", "Romania 300", "Factory 7"]
AXIS = [0, 1, 7]               # Germany, Italy, Spain: Russia's enemies
BALKANS = (126, 106, 172, 142) # tiles: left, top, right, bottom
BALKAN_AXIS = 60               # this many more Axis pixels there than at the start: go south
# Points across a target's front, in tiles from its centre. Each group
# is sent to its own, so the army arrives as a wall, not a line.
FRONT = [(4, -5), (4, -1), (4, 3), (6, -3), (6, 1), (6, 5), (2, -3),
         (2, 1), (0, 5), (2, -7)]
MASS = (160 * 32, 76 * 32)     # map pixels: where the army masses
MASS_RADIUS = 13               # minimap pixels around it that count as there
MIDDLE_EAST = (219 * 32, 129 * 32)   # bring a unit here for the spawn
# Buildings to fly to a city: (when, kind of building, its tile, the
# city). "When" is a hit's number, or a target's name for the first
# hit sent at that target. A building
# floating over a city counts as holding it.
FLIGHTS = [(1, "Barracks", (173, 80), "Warsaw 200"),     # Smolensk's
           ("Romania 300", "Starport", (190, 110), "Romania 300")]   # Sevastopol's
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
TRIAL_SECONDS = 480            # stop starting new hits after this long
BIG_MASS = 140                 # minimap pixels at the mass for a later hit
LATER_WAIT_MAX = 200           # seconds: hit with what there is by then
RETRAIN_EVERY = 55             # seconds between rounds of the barracks
FIRST_HIT_SWEEPS = 2           # stragglers wait for the next mass


class Stopped(Exception):
    pass


class State:
    def __init__(self):
        self.boxes = self.empty = 0
        self.ground_keys, self.air_keys = [], []
        self.orders_sent = 0       # counts hit orders, to walk along FRONT
        self.flown = set()         # barracks (tiles) that have been flown off
        self.sent_at = []          # the target of each hit so far
        self.flights_done = set()
        self.balkan_start = 0      # Axis pixels in the Balkans at the start
        self.capped = False        # supply was at its limit at the last look
        self.last_recall = -1e9    # when the army was last called back
        self.advised = None        # (target, when) from the general


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


def room_for_marines(io):
    """How many more marines the supply limit allows, read off the
    screen. None if the number cannot be read."""
    supply = numbers.read_supply(io.shot("supply", keep=False))
    if supply is None:
        return None
    return max(0, supply[1] - supply[0])


def train_everywhere(io, mapdata, st, check_supply=True):
    """Queue marines at the barracks, but only as many as the supply
    limit has room for. At the limit, nothing is queued at all."""
    gx, gy = live.minimap_point(*MASS)
    room = room_for_marines(io) if check_supply else None
    if room is not None and room < 3:
        if not st.capped:
            io.log("supply is at its limit: not training")
        st.capped = True
        return 0
    st.capped = False

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
    if room is not None:                # no more barracks than there is room for
        todo = todo[:max(1, -(-room // MARINES_PER_BARRACKS))]
    missed = [b for b in todo if not one(b)]
    still = [b for b in missed if not one(b)]             # one more go
    found = len(todo) - len(still)
    io.log(f"marines started at {found} of {len(todo)} barracks"
           + (f" (room for {room})" if room is not None else ""))
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


def hit(io, watch, mapdata, st, target, use_keys=True, sweeps=4):
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
    for sweep in range(sweeps):
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


def flights_after(io, mapdata, st, when):
    for w, kind, tile, city in FLIGHTS:
        if w == when and (w, city) not in st.flights_done:
            st.flights_done.add((w, city))
            fly_building(io, mapdata, st, kind, tile, city)


def axis_in(watch, screen, box):
    """How many minimap pixels of Axis colour lie in a box of tiles."""
    l, t, r, b = box
    n = 0
    for c, row in watch.others(screen, AXIS):
        x, y = live.from_drawn(c, row)
        if l <= x / 32 < r and t <= y / 32 < b:
            n += 1
    return n


def choose_target(io, watch, st):
    """Where the next hit should go, from what the minimap shows.

    Germany starts the game with troops in the Balkans, so what counts
    is how much more Axis colour is there now than at the start."""
    if st.advised and io.now() - st.advised[1] <= 40:
        io.log(f"next target {st.advised[0]} (the general's choice)")
        return st.advised[0]
    seen = axis_in(watch, io.shot("choose"), BALKANS)
    more = seen - st.balkan_start
    if more >= BALKAN_AXIS:
        target = "Factory 7" if "Romania 300" in st.sent_at else "Romania 300"
        why = "go south"
    else:
        target = "Berlin 1000"
        why = "Berlin again"
    io.log(f"next target {target} (Axis in the Balkans: {seen} pixels, "
           f"{st.balkan_start} at the start: {why})")
    return target


class Battle:
    """Keeps an eye on a hit after it has been sent: how much of our
    colour and of the Axis colour is at the target, time after time."""

    def __init__(self, target, sent_at):
        self.target, self.sent_at = target, sent_at
        self.samples = []               # (seconds since sent, ours, Axis)
        self.looked = 0

    def sample(self, io, watch, mapdata, picture):
        w = place(mapdata, self.target)
        ours = len(near(watch.units(picture), (w["x"], w["y"]), 14))
        axis = len(near(watch.others(picture, AXIS), (w["x"], w["y"]), 14))
        self.samples.append((io.now() - self.sent_at, ours, axis))

    def verdict(self):
        """"winning", "losing" or "unclear", with the numbers behind it."""
        arrived = [s for s in self.samples if s[1] >= 10]
        if not arrived:
            return "unclear", "the army has not been seen at the target"
        peak = max(s[1] for s in arrived)
        _, ours, axis = self.samples[-1]
        axis_before = self.samples[0][2]
        facts = (f"ours there {ours} (peak {peak}), Axis there {axis} "
                 f"(was {axis_before})")
        if ours < 0.3 * peak and axis > 0.5 * max(axis_before, 1):
            return "losing", facts
        if axis < 0.5 * max(axis_before, 1) and ours >= 0.3 * peak:
            return "winning", facts
        return "unclear", facts


def gather_idle(io, watch, mapdata, st, tried):
    """Send groups that are standing still at home to the mass: the
    reinforcements the map gives Russia at Moscow, Finland, Stalingrad
    and Siberia, and anyone missed earlier."""
    a = watch.units(io.shot("watch", keep=False))
    io.sleep(1.0)
    b_picture = io.shot("watch", keep=False)
    b = watch.units(b_picture)
    idle = at_home((a & b) - at_mass(b) - near(b, MIDDLE_EAST, 6), mapdata)
    orders = 0
    for group in live.clusters(idle, *GROUP)[:4]:
        key = min(group)
        if len(group) >= 9 and key not in tried:
            tried.add(key)
            if select_group(io, group, st, watch):
                attack_move(io, *MASS)
                orders += 1
    return orders, b_picture


TARGET_NAMES = {"Berlin": "Berlin 1000", "Romania": "Romania 300",
                "Belgrade": "Factory 7"}
ENEMY_AT_MASS = 12             # Axis pixels at the mass that mean "defend"
RECALL_COOLDOWN = 20           # seconds between recalls of the army


def recall(io, st, why):
    """Bring the number-key groups back to the massing place."""
    if io.now() - st.last_recall < RECALL_COOLDOWN:
        return False
    st.last_recall = io.now()
    for key in st.ground_keys + st.air_keys:
        io.key(key)
        io.sleep(0.05)
        attack_move(io, *MASS)
    io.log(f"army recalled to the massing place: {why}")
    return True


def status_report(io, st, t0, massed, need, battle, axis_balkans, axis_mass,
                  supply):
    """The few lines the general is given with each screenshot."""
    now = io.now() - t0
    lines = [f"Time in game: {int(now) // 60}:{int(now) % 60:02d}. "
             f"Round timer about {round_timer(now)}.",
             f"Our mass waiting at the massing place: {massed} minimap "
             f"pixels of units (the program wants {need} before hitting).",
             f"Axis colour at our massing place: {axis_mass} pixels.",
             f"Axis colour in the Balkans: {axis_balkans} pixels "
             f"({st.balkan_start} at the start of the game)."]
    if supply:
        lines.append(f"Supply: {supply[0]} of {supply[1]}.")
    if battle:
        lines.append(f"Our last hit went to {battle.target} "
                     f"{io.now() - battle.sent_at:.0f} s ago; the main view "
                     f"is looking there. From the minimap: "
                     f"{battle.verdict()[1]}.")
    lines.append(f"Hits sent so far: {', '.join(st.sent_at) or 'none'}.")
    return "\n".join(lines)


def build_big_mass(io, watch, mapdata, st, t0, battle=None, general=None):
    """Keep the barracks busy (when supply allows), bring in the
    reinforcements, watch how the last hit is doing, and wait until the
    mass is big or it has been long enough. All the while it reacts:
    the rules to an enemy at the mass, the general to what it is shown.
    Returns the mass's size."""
    began = last_train = io.now()
    train_everywhere(io, mapdata, st)
    collected, tried, gathered = False, set(), 0
    need = BIG_MASS
    while True:
        orders, picture = gather_idle(io, watch, mapdata, st, tried)
        gathered += orders
        massed = len(at_mass(watch.units(picture)))
        waited = io.now() - began
        # the fast rule: the enemy is at the mass
        axis_mass = len(at_mass(watch.others(picture, AXIS)))
        if axis_mass >= ENEMY_AT_MASS:
            recall(io, st, f"{axis_mass} pixels of Axis colour there")
        if battle:
            battle.sample(io, watch, mapdata, picture)
            if battle.verdict()[0] == "losing":
                need = int(BIG_MASS * 1.5)      # come back with more
        # look at the fight itself: every time for the general, now and
        # then for the record otherwise
        look = battle and (general or (waited >= 12 * (battle.looked + 1)
                                       and battle.looked < 4))
        if look:
            battle.looked += 1
            w = place(mapdata, battle.target)
            look_at(io, w["x"], w["y"], wait=0.35)
            fight = io.shot(f"fight-{battle.target.split()[0]}",
                            keep=battle.looked <= 4)
            if general:
                general.submit(fight, status_report(
                    io, st, t0, massed, need, battle,
                    axis_in(watch, picture, BALKANS), axis_mass,
                    numbers.read_supply(fight)))
        advice = general.take() if general else None
        if advice:
            io.log(f"general: {advice}")
            st.advised = (TARGET_NAMES[advice.target], io.now())
            if advice.action == "pull_back":
                recall(io, st, "the general says so")
            elif advice.action == "hit_now" and massed >= 40:
                break
        if massed >= need or waited >= LATER_WAIT_MAX:
            break
        if not collected:
            collected = collect_middle_east(io, watch, st) > 0
        if io.now() - last_train >= RETRAIN_EVERY:
            last_train = io.now()
            train_everywhere(io, mapdata, st)
        io.sleep(1.0 if general else 2.0)
    io.shot("mass")
    if battle:
        io.log(f"last hit at {battle.target}: {battle.verdict()[0]} "
               f"({battle.verdict()[1]})")
    io.log(f"mass at {io.now() - t0:.0f} s: {massed} minimap pixels of "
           f"units there after {waited:.0f} s; {gathered} idle groups "
           f"brought in; wanted {need}")
    return massed


def run(io, mapdata=None, general=None):
    """Returns a short result for the log."""
    mapdata = mapdata or load_map()
    side = mapdata["slots"][SLOT]
    first = io.shot("start")
    watch = live.Watch(first, side["structures"], side["units"])
    if not live.minimap_showing(first) or not watch.ok:
        io.log("The live game's minimap is not on screen. Nothing done.")
        return {"trained": 0, "gathered": 0, "hits": []}
    t0, st = io.now(), State()
    st.balkan_start = axis_in(watch, first, BALKANS)
    since = lambda: f"{io.now() - t0:.0f} s"
    send_scout(io, mapdata, st)
    trained = train_everywhere(io, mapdata, st, check_supply=False)
    io.log(f"  ({since()} since start)")
    gathered = first_orders(io, watch, mapdata, st, t0)
    io.log(f"  ({since()} since start)")
    wait_for_mass(io, watch, mapdata, st, t0, WAVE_EARLIEST, WAVE_LATEST)
    hit_at = round(io.now() - t0)
    hits = [hit(io, watch, mapdata, st, TARGETS[0], sweeps=FIRST_HIT_SWEEPS)]
    st.sent_at.append(TARGETS[0])
    io.log(f"  first hit sent by {since()}; {st.boxes} boxes, "
           f"{st.empty} empty")
    flights_after(io, mapdata, st, 1)
    battle = Battle(TARGETS[0], io.now())
    while io.now() - t0 < TRIAL_SECONDS:
        massed = build_big_mass(io, watch, mapdata, st, t0, battle, general)
        if massed < 30:
            io.log("no new mass to send")
            hits.append(0)
            continue
        target = choose_target(io, watch, st)
        hits.append(hit(io, watch, mapdata, st, target, use_keys=False))
        st.sent_at.append(target)
        battle = Battle(target, io.now())
        flights_after(io, mapdata, st, len(hits))
        flights_after(io, mapdata, st, target)
        io.log(f"  ({since()} since start; round timer about "
               f"{round_timer(io.now() - t0)})")
    if general:
        io.log(general.summary())
    for name in ("Berlin 1000", "Warsaw 200", "Romania 300", "Factory 7"):
        w = place(mapdata, name)
        look_at(io, w["x"], w["y"], wait=0.5)
        io.shot("at-" + name.split()[0])
    return {"trained": trained, "gathered": gathered, "hit_at": hit_at,
            "hits": hits, "targets": st.sent_at,
            "keys": "".join(st.ground_keys + st.air_keys),
            "boxes": st.boxes, "empty": st.empty}
