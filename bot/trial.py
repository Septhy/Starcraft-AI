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
# Cities on the way to Berlin. A hit that stalls is aimed at the one
# nearest to where it stalled, to break the line there first.
EAST_FRONT = ["Konigsberg 200", "Warsaw 200", "Krakow 200"]
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
WAVE_EARLIEST = 45             # seconds: do not hit before this (qororo98
                               # and penny[eef] send theirs at 37 to 51)
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
        self.air_moved = -1e9      # when the air was last sent to the front
        # for the general
        self.general = None
        self.battle = None         # the hit being watched
        self.t0 = 0.0
        self.need = BIG_MASS       # how big a mass is wanted for the next hit
        self.last_consult = -1e9
        self.last_chat = -1e9
        self.hit_wanted = False    # the general has said "hit now"
        self.opening_target = None
        self.rekey = 8             # ground keys already re-used this hit
        self.outcomes = []         # how each hit went, for the lessons
        self.looks_kept = 0


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
        if orders % 6 == 5:
            consult(io, watch, mapdata, st)
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
    for name in set(TARGETS) | set(EAST_FRONT) | {f[3] for f in FLIGHTS}:
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
        consult(io, watch, mapdata, st)
        if st.hit_wanted and now >= 40 and massed >= 60:
            why = "the general says hit now"
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
        consult(io, watch, mapdata, st)     # the general is asked mid-hit too
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
                if st.rekey < len(GROUND_KEYS):
                    # the newest groups take over the number keys, so
                    # they can be recalled and given orders
                    io.combo("ctrl", GROUND_KEYS[st.rekey])
                    io.sleep(0.04)
                    st.rekey += 1
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
    st.rekey = len(GROUND_KEYS) if use_keys else 0
    start = None
    for sweep in range(sweeps):
        n, found = sweep_mass(io, watch, mapdata, st, target)
        orders += n
        start = start or max(found, 1)
        if n == 0 or found < 0.15 * start:
            break
        io.sleep(1.5)
    if not use_keys:                    # nothing is forward before the first hit
        orders += push_front(io, watch, mapdata, st, target)
    for key in st.air_keys:             # air is fastest, so it goes last
        io.key(key)
        io.sleep(0.05)
        attack_move(io, *front_point(mapdata, st, target))
        orders += 1
    io.log(f"hit: {orders} groups sent at {target}")
    return orders


def push_front(io, watch, mapdata, st, target, limit=14):
    """Units from earlier hits that are standing still at the front go
    in with this hit, so it arrives with everything."""
    a = watch.units(io.shot("watch", keep=False))
    io.sleep(1.0)
    b = watch.units(io.shot("front"))
    idle = forward_units(a & b, mapdata)
    w = place(mapdata, target)
    idle -= near(idle, (w["x"], w["y"]), 6)        # already there
    orders = 0
    for group in back_to_front(live.clusters(idle, 3, 3), (w["x"], w["y"]),
                               lambda g: live.from_drawn(*g[0]))[:limit]:
        if len(group) >= 4 and select_group(io, group, st, watch):
            attack_move(io, *front_point(mapdata, st, target))
            orders += 1
    if orders:
        io.log(f"  {orders} groups standing at the front sent on as well")
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


# qororo98 and penny[eef] alternate fronts by the clock: north at first,
# south from about 3:30, back north from about 7:30, south again later.
# (seconds from, seconds to, "north" or "south")
PLAN = [(0, 210, "north"), (210, 450, "south"), (450, 720, "north"),
        (720, 960, "south"), (960, 1260, "north")]


def planned_front(seconds_in):
    for start, end, front in PLAN:
        if start <= seconds_in < end:
            return front
    return "north"


def choose_target(io, watch, st, mapdata=None, battle=None):
    """Where the next hit should go.

    The general's choice comes first. Otherwise the plan by the clock:
    south when qororo98 and penny[eef] go south. Otherwise: if the last
    hit stalled or was lost short of its target, aim at the city nearest
    to where that happened. Otherwise south if the Axis has grown in the
    Balkans since the start (Germany starts with troops there), and
    Berlin if not."""
    if st.advised and io.now() - st.advised[1] <= 40:
        io.log(f"next target {st.advised[0]} (the general's choice)")
        return st.advised[0]
    south = "Factory 7" if "Romania 300" in st.sent_at else "Romania 300"
    if planned_front(io.now() - st.t0) == "south":
        io.log(f"next target {south} (the plan: south at this point in the "
               f"game, as qororo98 and penny[eef] do)")
        return south
    if battle and mapdata and battle.front and \
            battle.verdict()[0] in ("stalled", "losing"):
        fx, fy = battle.front
        cities = [place(mapdata, n) for n in EAST_FRONT]
        city = min(cities, key=lambda c: (c["x"] - fx) ** 2 + (c["y"] - fy) ** 2)
        io.log(f"next target {city['name']} (the last hit "
               f"{battle.verdict()[0]} near {place_name(mapdata, fx, fy)})")
        return city["name"]
    seen = axis_in(watch, io.shot("choose"), BALKANS)
    more = seen - st.balkan_start
    if more >= BALKAN_AXIS:
        target = south
        why = "go south"
    else:
        target = "Berlin 1000"
        why = "Berlin again"
    io.log(f"next target {target} (Axis in the Balkans: {seen} pixels, "
           f"{st.balkan_start} at the start: {why})")
    return target


def forward_units(pixels, mapdata):
    """Our units that have gone forward of the massing place: the
    opposite of at_home, leaving out the mass and the Middle East."""
    return pixels - at_home(pixels, mapdata) - at_mass(pixels) \
        - near(pixels, MIDDLE_EAST, 8)


def place_name(mapdata, map_x, map_y):
    """The named place nearest a point."""
    small = [p for p in mapdata["places"]
             if p["w"] * p["h"] < (40 * 32) ** 2 and p["name"][0] != "Z"]
    return min(small, key=lambda p: (p["x"] - map_x) ** 2
               + (p["y"] - map_y) ** 2)["name"]


def find_front(watch, picture, mapdata, target):
    """Where the fighting is: the place where our forward units are
    closest to the most Axis colour, or failing that the forward unit
    nearest the target. Returns (map x, map y, our forward pixels, Axis
    pixels at the front), or None if nothing of ours is forward."""
    forward = forward_units(watch.units(picture), mapdata)
    if len(forward) < 4:
        return None
    axis = watch.others(picture, AXIS)
    w = place(mapdata, target)
    tc, tr = live.to_drawn(w["x"], w["y"])

    def enemy_near(p, reach=5):
        return sum((p[0] + i, p[1] + j) in axis
                   for i in range(-reach, reach + 1)
                   for j in range(-reach, reach + 1))
    lead = sorted(forward, key=lambda p: (p[0] - tc) ** 2 + (p[1] - tr) ** 2)
    # the fight is among the units nearest the target: look at those
    best = max(lead[:40], key=enemy_near)
    contact = enemy_near(best)
    if contact < 3:
        best = lead[0]
    x, y = live.from_drawn(*best)
    return x, y, len(forward), contact


class Battle:
    """Keeps an eye on a hit after it has been sent. It follows the
    front, wherever that is: a hit often stalls well short of its
    target, and the target itself then shows nothing."""

    def __init__(self, target, sent_at):
        self.target, self.sent_at = target, sent_at
        self.samples = []       # (seconds, forward px, Axis at front, gap)
        self.front = None       # (map x, map y) of the latest front
        self.looked = 0
        self.arrived = False

    def sample(self, io, watch, mapdata, picture):
        w = place(mapdata, self.target)
        found = find_front(watch, picture, mapdata, self.target)
        if near(watch.units(picture), (w["x"], w["y"]), 12).__len__() >= 10:
            self.arrived = True
        if found is None:
            self.samples.append((io.now() - self.sent_at, 0, 0, None))
            return
        x, y, ours, axis = found
        self.front = (x, y)
        gap = ((x - w["x"]) ** 2 + (y - w["y"]) ** 2) ** 0.5 / 32
        self.samples.append((io.now() - self.sent_at, ours, axis, gap))

    def verdict(self, mapdata=None):
        """One of "arrived", "losing", "stalled", "advancing", "unclear",
        with the facts behind it."""
        seen = [s for s in self.samples if s[1] > 0]
        if not seen:
            return "unclear", "none of our units are forward of the mass"
        peak = max(s[1] for s in seen)
        t, ours, axis, gap = self.samples[-1]
        where = ""
        if self.front and mapdata:
            where = f" near {place_name(mapdata, *self.front)}"
        facts = (f"front{where}, {gap:.0f} tiles short of {self.target}; "
                 f"our forward units {ours} pixels (peak {peak}); Axis "
                 f"colour at the front {axis}"
                 if gap is not None else
                 f"no units of ours forward now (peak was {peak})")
        if self.arrived:
            return "arrived", facts
        if peak >= 30 and ours < 0.3 * peak:
            return "losing", facts
        earlier = [s for s in seen if s[0] <= t - 20 and s[3] is not None]
        if gap is not None and gap > 8 and earlier and t >= 40 \
                and gap > earlier[-1][3] - 3:
            return "stalled", facts
        if gap is not None and earlier and gap < earlier[-1][3] - 3:
            return "advancing", facts
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
                "Belgrade": "Factory 7", "Warsaw": "Warsaw 200",
                "Konigsberg": "Konigsberg 200", "Krakow": "Krakow 200"}
ENEMY_AT_MASS = 12             # Axis pixels at the mass that mean "defend"
AIR_FOLLOW_EVERY = 8           # seconds between moving the air to the front
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
                  supply, mapdata=None):
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
        kind, facts = battle.verdict(mapdata)
        lines.append(f"Our last hit was sent at {battle.target} "
                     f"{io.now() - battle.sent_at:.0f} s ago. The main view "
                     f"is looking at its front. The program's own reading "
                     f"from the minimap: {kind}: {facts}.")
    else:
        lines.append("No hit has been sent yet; the main view is looking "
                     "at our massing place. Your target now chooses the "
                     "first hit's target.")
    lines.append(f"Hits sent so far: {', '.join(st.sent_at) or 'none'}.")
    lines.append(f"Number keys holding groups: ground "
                 f"{' '.join(st.ground_keys) or 'none'}; air "
                 f"{' '.join(st.air_keys) or 'none'}.")
    return "\n".join(lines)


CONSULT_EVERY = 3.5            # seconds between screenshots for the general
CHAT_EVERY = 45                # seconds between chat lines at most
ORDER_PLACES = {"Odessa": "Odessa 200", "Smolensk": "Smolensk 200",
                "Moscow": "Moscow 1000"}


def order_point(mapdata, st, name):
    """Map pixels of a place the general can name."""
    if name == "mass":
        return MASS
    if name == "front":
        return st.battle.front if st.battle and st.battle.front else MASS
    full = TARGET_NAMES.get(name) or ORDER_PLACES.get(name)
    if not full:
        return None
    w = place(mapdata, full)
    return w["x"], w["y"]


def keys_for(st, group):
    if group == "ground":
        return list(st.ground_keys)
    if group == "air":
        return list(st.air_keys)
    if group == "all":
        return st.ground_keys + st.air_keys
    return [group] if group in st.ground_keys + st.air_keys else []


def carry_out(io, mapdata, st, order, camera):
    """Give one of the general's group orders. Returns True if given."""
    keys = keys_for(st, order["group"])
    kind = order["order"]
    if not keys:
        return False
    if kind in ("attack_point", "yamato_point"):
        # a point in the 1280 x 720 picture the general was shown
        sx = order["x"] * live.SCREEN[0] / 1280
        sy = order["y"] * live.SCREEN[1] / 720
        l, t, r, b = live.GAME_AREA
        if camera is None or not (l + 5 < sx < r - 5 and t + 5 < sy < b - 5):
            return False
        look_at(io, *camera, wait=0.25)     # the same view as the picture
        for key in keys:
            io.key(key)
            io.sleep(0.05)
            if kind == "yamato_point":
                io.key("y")
                io.sleep(0.06)
                io.click(sx, sy)
            else:
                io.click(sx, sy, button="right")
            io.sleep(0.06)
        return True
    point = None if kind == "hold" else order_point(mapdata, st, order["place"])
    if kind != "hold" and point is None:
        return False
    for key in keys:
        io.key(key)
        io.sleep(0.05)
        if kind == "hold":
            io.key("h")
        elif kind == "move":
            io.click(*live.minimap_point(*point), button="right")
        else:
            attack_move(io, *point)
        io.sleep(0.05)
    return True


def say(io, st, text):
    """Type a line to the allies, not too often."""
    text = "".join(c for c in text if " " <= c <= "~")[:60].strip()
    if not text or io.now() - st.last_chat < CHAT_EVERY:
        return False
    st.last_chat = io.now()
    io.combo("shift", "enter")          # opens chat to allies
    io.sleep(0.15)
    io.type_text(text)
    io.sleep(0.1)
    io.key("enter")
    io.sleep(0.1)
    io.log(f"chat to allies: {text}")
    return True


def consult(io, watch, mapdata, st):
    """Show the general the front if it is time to, and carry out any
    answer that has come back. Safe to call often: it does nothing
    without a general, and looks no more than every CONSULT_EVERY
    seconds. It moves the view, so callers look again afterwards."""
    g = st.general
    if g is None:
        return None
    if io.now() - st.last_consult >= CONSULT_EVERY:
        st.last_consult = io.now()
        battle = st.battle
        fx, fy = battle.front if battle and battle.front else MASS
        cam = look_at(io, *centred(fx, fy), wait=0.3)
        st.looks_kept += 1
        view = io.shot("front", keep=st.looks_kept % 8 == 1)
        if battle:
            battle.sample(io, watch, mapdata, view)
        g.submit(view, status_report(
            io, st, st.t0, len(at_mass(watch.units(view))), st.need, battle,
            axis_in(watch, view, BALKANS),
            len(at_mass(watch.others(view, AXIS))),
            numbers.read_supply(view), mapdata), camera=cam)
    advice = g.take()
    if advice is None:
        return None
    io.log(f"general: {advice}")
    name = TARGET_NAMES[advice.target]
    st.advised = (name, io.now())
    if not st.sent_at:
        st.opening_target = name
    if advice.action == "pull_back":
        recall(io, st, "the general says so")
    elif advice.action == "hit_now":
        st.hit_wanted = True
    given = sum(carry_out(io, mapdata, st, o, advice.camera)
                for o in advice.group_orders)
    if advice.group_orders:
        io.log(f"  {given} of {len(advice.group_orders)} group orders given")
    if advice.chat:
        say(io, st, advice.chat)
    return advice


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
            if battle.verdict()[0] in ("losing", "stalled"):
                need = int(BIG_MASS * 1.5)      # come back with more
        # look at the fight itself: every time for the general, now and
        # then for the record otherwise
        if battle and battle.front and st.air_keys and \
                io.now() - st.air_moved >= AIR_FOLLOW_EVERY:
            st.air_moved = io.now()
            for key in st.air_keys:     # the air stays over the front
                io.key(key)
                io.sleep(0.05)
                attack_move(io, *battle.front)
        st.need = need
        if general:
            consult(io, watch, mapdata, st)
        elif battle and waited >= 12 * (battle.looked + 1) and battle.looked < 4:
            battle.looked += 1          # a picture of the front for the record
            w = place(mapdata, battle.target)
            fx, fy = battle.front or (w["x"], w["y"])
            look_at(io, *centred(fx, fy), wait=0.35)
            io.shot("front")
        if st.hit_wanted and massed >= 40:
            io.log("the general says hit now")
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
        io.log(f"last hit at {battle.target}: {battle.verdict(mapdata)[0]} "
               f"({battle.verdict(mapdata)[1]})")
    io.log(f"mass at {io.now() - t0:.0f} s: {massed} minimap pixels of "
           f"units there after {waited:.0f} s; {gathered} idle groups "
           f"brought in; wanted {need}")
    return massed


def close_battle(st, mapdata):
    """Note how the watched hit ended, for the log and the lessons."""
    b = st.battle
    if b:
        kind, facts = b.verdict(mapdata)
        st.outcomes.append(f"hit at {b.target}: {kind} ({facts})")


def run(io, mapdata=None, general=None, save_lessons=None):
    """Returns a short result for the log. `save_lessons` is called with
    the general's lessons for the next game, if it wrote any."""
    mapdata = mapdata or load_map()
    side = mapdata["slots"][SLOT]
    first = io.shot("start")
    watch = live.Watch(first, side["structures"], side["units"])
    if not live.minimap_showing(first) or not watch.ok:
        io.log("The live game's minimap is not on screen. Nothing done.")
        return {"trained": 0, "gathered": 0, "hits": []}
    t0, st = io.now(), State()
    st.general, st.t0 = general, t0
    st.balkan_start = axis_in(watch, first, BALKANS)
    since = lambda: f"{io.now() - t0:.0f} s"
    result = {"trained": 0, "gathered": 0, "hits": []}
    try:
        consult(io, watch, mapdata, st)     # the general's say on the opening
        send_scout(io, mapdata, st)
        result["trained"] = train_everywhere(io, mapdata, st,
                                             check_supply=False)
        io.log(f"  ({since()} since start)")
        result["gathered"] = first_orders(io, watch, mapdata, st, t0)
        io.log(f"  ({since()} since start)")
        wait_for_mass(io, watch, mapdata, st, t0, WAVE_EARLIEST, WAVE_LATEST)
        result["hit_at"] = round(io.now() - t0)
        target = st.opening_target or TARGETS[0]
        if st.opening_target:
            io.log(f"first target {target} (the general's choice)")
        hits = result["hits"]
        st.hit_wanted = False
        hits.append(hit(io, watch, mapdata, st, target,
                        sweeps=FIRST_HIT_SWEEPS))
        st.sent_at.append(target)
        io.log(f"  first hit sent by {since()}; {st.boxes} boxes, "
               f"{st.empty} empty")
        flights_after(io, mapdata, st, 1)
        st.battle = Battle(target, io.now())
        while io.now() - t0 < TRIAL_SECONDS:
            massed = build_big_mass(io, watch, mapdata, st, t0, st.battle,
                                    general)
            if massed < 30:
                io.log("no new mass to send")
                hits.append(0)
                continue
            target = choose_target(io, watch, st, mapdata, st.battle)
            close_battle(st, mapdata)
            st.hit_wanted = False
            hits.append(hit(io, watch, mapdata, st, target, use_keys=False))
            st.sent_at.append(target)
            st.battle = Battle(target, io.now())
            flights_after(io, mapdata, st, len(hits))
            flights_after(io, mapdata, st, target)
            io.log(f"  ({since()} since start; round timer about "
                   f"{round_timer(io.now() - t0)})")
        for name in ("Berlin 1000", "Warsaw 200", "Romania 300", "Factory 7"):
            w = place(mapdata, name)
            look_at(io, w["x"], w["y"], wait=0.5)
            io.shot("at-" + name.split()[0])
    finally:
        # whether it finished or was stopped: the general's lessons
        if general:
            close_battle(st, mapdata)
            lessons = general.write_lessons(
                f"Played {io.now() - t0:.0f} s. "
                + (" ".join(st.outcomes) or "No hit was sent."))
            if lessons and save_lessons:
                save_lessons(lessons)
                io.log("general's lessons for next game saved")
            io.log(general.summary())
    result.update({"targets": st.sent_at,
                   "keys": "".join(st.ground_keys + st.air_keys),
                   "boxes": st.boxes, "empty": st.empty})
    return result
