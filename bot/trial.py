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
# Who Russia's troops actually fight: the Axis, and the computer player
# (white) that holds the Balkans, Turkey and the east.
HOSTILE = AXIS + [6]
# Where a hit goes on to once it has taken its target, so the troops do
# not stand idle there.
# In the south: Romania, the factory at Belgrade, then north-west
# toward the Netherlands (the repository owner), by way of the cities
# that lie between.
NEXT = {"Romania 300": "Factory 7", "Factory 7": "Hungary 200",
        "Hungary 200": "Munich 200", "Munich 200": "Frankfurt 200",
        "Frankfurt 200": "Amsterdam 100", "Konigsberg 200": "Berlin 1000",
        "Warsaw 200": "Berlin 1000", "Krakow 200": "Berlin 1000"}
ADVANCE_EVERY = 5              # seconds between checks for idle troops forward
IDLE_FORWARD = 20              # minimap pixels of idle forward units worth an order
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
           # Warsaw and Krakow are taxed together: taking either sends
           # a building to each.
           ("Warsaw 200", "Barracks", (173, 80), "Warsaw 200"),
           ("Warsaw 200", "Factory", (165, 49), "Krakow 200"),
           ("Krakow 200", "Factory", (165, 49), "Krakow 200"),
           ("Krakow 200", "Barracks", (173, 80), "Warsaw 200"),
           ("Konigsberg 200", "Engineering Bay", (162, 58), "Konigsberg 200"),
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
# How big a hit has to be, in men. The repository owner: at least 140,
# and normally 160 to 300. The men are counted on the game screen
# itself: the bot boxes the troops patch by patch and reads how many the
# game says are selected (count_men). The minimap only says when it is
# worth counting.
MIN_HIT = 140                  # never send less than this as a hit
WANT_HIT = 180                 # what a hit normally waits for
BIG_HIT = 240                  # after a hit was lost or stalled
COUNT_WHEN = 0.6               # count once the minimap suggests this share of the need
RECOUNT_GROWTH = 1.15          # and again when the minimap figure has grown this much
NEW_TROOPS = 40                # a new hit needs at least this many at the mass
BIG_MASS = WANT_HIT
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
        self.need = WANT_HIT       # how big a mass is wanted for the next hit
        self.reserve = 0           # minimap pixels of troops standing forward in reserve
        self.strength = 0          # men for the next hit: mass plus reserve
        self.men_per_pixel = 1.0   # from the last count on the game screen
        self.selected = 0          # units picked up by the hit's boxes, in all
        self.selections = 0        # and how many boxes that took
        self.last_consult = -1e9
        self.last_chat = -1e9
        self.hit_wanted = False    # the general has said "hit now"
        self.opening_target = None
        self.rekey = 8             # ground keys already re-used this hit
        self.outcomes = []         # how each hit went, for the lessons
        self.last_advance = -1e9   # when idle forward troops were last sent on
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


def look_at(io, x, y, wait=0.12):
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
    io.sleep(0.05)
    st.boxes += 1
    if live.units_selected(io.card()):
        return True
    st.empty += 1
    return False


def select_group(io, pixels, st, watch=None, margin=None):
    """Look at the units drawn at these minimap pixels and box them."""
    margin = MARGIN if margin is None else margin
    cols = [p[0] for p in pixels]
    rows = [p[1] for p in pixels]
    x0, y0 = live.from_drawn(min(cols) - 0.5, min(rows) - 0.5)
    x1, y1 = live.from_drawn(max(cols) + 0.5, max(rows) + 0.5)
    l, t, r, b = live.GAME_AREA
    cam = look_at(io, *centred((x0 + x1) / 2, (y0 + y1) / 2))
    sx0, sy0 = live.on_screen(x0, y0, cam)
    sx1, sy1 = live.on_screen(x1, y1, cam)
    box = (max(l + 4, sx0 - margin), max(t + 4, sy0 - margin),
           min(r - 4, sx1 + margin), min(b - 4, sy1 + margin))
    if box[2] - box[0] < 40 or box[3] - box[1] < 40:
        return False
    if box_and_check(io, box, st):
        return True
    if watch:
        watch.forget(pixels)            # nothing there: not units
    return False


COUNT_PATCH = 104              # map pixels: the side of one patch of ground counted


def count_box(io, box, depth=0):
    """How many units stand in a box on the game screen: box them and
    read how many the game says are selected. The game selects at most
    twelve, so a box that comes back full is cut in four and each part
    counted."""
    io.drag(*box)
    io.sleep(0.05)
    n = live.selected_count(io.shot("count", keep=False))
    l, t, r, b = box
    if n < 12 or depth >= 2 or r - l < 90 or b - t < 90:
        return n
    mx, my = (l + r) // 2, (t + b) // 2
    return sum(count_box(io, q, depth + 1) for q in
               [(l, t, mx - 1, my - 1), (mx, t, r, my - 1),
                (l, my, mx - 1, b), (mx, my, r, b)])


def count_men(io, pixels):
    """Count the men standing at these minimap pixels by looking at them
    on the game screen.

    The ground is cut into fixed square patches, and each patch that
    the minimap shows troops on is boxed once, whichever view it is
    seen from, so nobody is counted twice."""
    patches = set()
    for p in pixels:
        x, y = live.from_drawn(*p)
        patches.add((int(x // COUNT_PATCH), int(y // COUNT_PATCH)))
    l, t, r, b = live.GAME_AREA
    men = 0
    while patches:
        # look at the middle of a screenful of the patches still to do
        i0, j0 = min(patches, key=lambda c: (c[1], c[0]))
        near_by = [c for c in patches
                   if 0 <= c[0] - i0 < 7 and 0 <= c[1] - j0 < 3]
        cx = (sum(c[0] for c in near_by) / len(near_by) + 0.5) * COUNT_PATCH
        cy = (sum(c[1] for c in near_by) / len(near_by) + 0.5) * COUNT_PATCH
        cam = look_at(io, *centred(cx, cy))
        done = set()
        for c in sorted(near_by):
            x0, y0 = live.on_screen(c[0] * COUNT_PATCH, c[1] * COUNT_PATCH, cam)
            x1, y1 = live.on_screen((c[0] + 1) * COUNT_PATCH,
                                    (c[1] + 1) * COUNT_PATCH, cam)
            if x0 < l + 2 or y0 < t + 2 or x1 > r - 2 or y1 > b - 2:
                continue                # not wholly in view: another look
            men += count_box(io, (x0, y0, x1 - 1, y1 - 1))
            done.add(c)
        patches -= done or {(i0, j0)}   # never loop on one that will not fit
    return men


def attack_move(io, map_x, map_y):
    """Attack-move whatever is selected to a map point."""
    io.key("a")
    io.sleep(0.04)
    io.click(*live.minimap_point(map_x, map_y))
    io.sleep(0.04)


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
            io.sleep(0.03)
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
    for name in set(TARGETS) | set(EAST_FRONT) | set(NEXT.values()) \
            | {f[3] for f in FLIGHTS}:
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
        if st.hit_wanted and now >= 40 and massed >= MIN_HIT:
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


FULL = 12                      # the most units one selection holds
GOOD_BOX = 9                   # a box with at least this many is good enough


def box_around(pixels, cam, pad=36):
    """The screen box round the troops drawn at these minimap pixels,
    for the view `cam`, kept inside the game area. None if too small."""
    l, t, r, b = live.GAME_AREA
    pts = []
    for c, row in pixels:           # a pixel covers a square of ground
        pts.append(live.on_screen(*live.from_drawn(c - 0.5, row - 0.5), cam))
        pts.append(live.on_screen(*live.from_drawn(c + 0.5, row + 0.5), cam))
    box = (max(l + 3, min(p[0] for p in pts) - pad),
           max(t + 3, min(p[1] for p in pts) - pad),
           min(r - 3, max(p[0] for p in pts) + pad),
           min(b - 3, max(p[1] for p in pts) + pad))
    return box if box[2] - box[0] >= 40 and box[3] - box[1] >= 40 else None


def select_full(io, st, seed, pool, cam):
    """Select as near to twelve units as it can, starting from the
    troops at `seed` and reaching out to their neighbours in `pool`.

    The box is sized from how many men a minimap pixel has been holding
    (from the last count). It then reads how many the game selected:
    if that is well short of twelve and there are neighbours left, it
    draws a bigger box round more of them and looks again. Returns (the
    pixels boxed, how many units were selected)."""
    near_first = sorted(pool, key=lambda p: (p[0] - seed[0]) ** 2
                        + (p[1] - seed[1]) ** 2)
    want = max(3, round(FULL / max(st.men_per_pixel, 0.2)))
    take, chosen, n = want, [], 0
    for attempt in range(3):
        chosen = near_first[:take]
        box = box_around(chosen, cam)
        if box is None:
            break
        io.drag(*box)
        io.sleep(0.05)
        st.boxes += 1
        n = live.selected_count(io.shot("box", keep=False))
        if n >= GOOD_BOX or take >= len(near_first):
            break
        # too few: reach for more, in proportion to how short it fell
        take = min(len(near_first), int(take * min(3.0, FULL / max(n, 2))) + 2)
    if n == 0:
        st.empty += 1
    st.selected += n
    st.selections += 1
    return chosen, n


def sweep_mass(io, watch, mapdata, st, target):
    """One pass over the massing place: every part of it where the
    minimap shows units standing still is boxed, back to front, each
    box drawn to hold as near to twelve units as it can. Returns
    (orders given, pixels found)."""
    w = place(mapdata, target)
    a = watch.units(io.shot("sweep"))
    io.sleep(1.2)                       # only those still standing there
    there = at_mass(a) & watch.units(io.shot("watch", keep=False))
    if len(there) < 12:
        return 0, len(there)
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
        left = set(view)
        while left:
            # the troops farthest from the target go first
            seed = back_to_front(list(left), (w["x"], w["y"]),
                                 lambda p: live.from_drawn(*p))[0]
            boxed, n = select_full(io, st, seed, left, cam)
            left -= set(boxed) or {seed}
            if n == 0:
                watch.forget(boxed)
                continue
            attack_move(io, *front_point(mapdata, st, target))
            orders += 1
            if st.rekey < len(GROUND_KEYS):
                # the newest groups take over the number keys, so
                # they can be recalled and given orders
                io.combo("ctrl", GROUND_KEYS[st.rekey])
                io.sleep(0.04)
                st.rekey += 1
    return orders, len(there)


def hit(io, watch, mapdata, st, target, use_keys=True, sweeps=4):
    """Send the mass at the target as a wall."""
    orders = 0
    if use_keys:
        for key in st.ground_keys:      # all the key groups in a few seconds
            io.key(key)
            io.sleep(0.035)
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
        io.sleep(0.035)
        attack_move(io, *front_point(mapdata, st, target))
        orders += 1
    per_box = st.selected / max(st.selections, 1)
    io.log(f"hit: {orders} groups sent at {target}; its boxes have held "
           f"{per_box:.1f} units each on average so far")
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
    # a building takes a couple of seconds to leave the ground, and
    # ignores orders until it has; so wait, then say it twice
    io.sleep(2.6)
    city = place(mapdata, city_name)
    for _ in range(2):
        io.click(*live.minimap_point(city["x"], city["y"]), button="right")
        io.sleep(0.8)
    io.shot("flight-" + city_name.split()[0])
    if kind == "Barracks":
        st.flown.add(tile)
    io.log(f"flight: {kind} lifted and sent to {city_name}")
    return True


def flights_after(io, mapdata, st, when):
    """Send the buildings whose turn has come. Each building flies once."""
    for w, kind, tile, city in FLIGHTS:
        if w == when and tile not in st.flights_done:
            st.flights_done.add(tile)
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
    # going south means carrying on from the farthest point reached on
    # the southern road, not starting it again
    south, at = "Romania 300", "Romania 300"
    while at in NEXT and at in st.sent_at:
        at = NEXT[at]
        south = at
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
    axis = watch.others(picture, HOSTILE)
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
        self.taxed = False      # a building has been sent for its tax

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
    return orders, b_picture, a & b


def advance_front(io, watch, mapdata, st, still, picture):
    """Keep the troops forward from standing idle.

    `still` is the set of our unit pixels that have not moved between
    two looks a second apart. Those forward of the mass that are not in
    contact with the enemy are idle. If the hit has taken its target
    they are sent on to the next objective; if they have stopped short
    of it they are sent at it again. Returns the orders given."""
    battle = st.battle
    if battle is None or io.now() - st.last_advance < ADVANCE_EVERY:
        return 0
    w = place(mapdata, battle.target)
    # only the troops of this hit: those around its target or its front.
    # Troops holding somewhere else, such as Berlin, are left alone.
    idle = forward_units(still, mapdata)
    mine = near(idle, (w["x"], w["y"]), 26)
    if battle.front:
        mine |= near(idle, battle.front, 14)
    idle = mine
    # Troops standing forward count toward the next hit, unless they are
    # already holding the end of their road: those have arrived.
    holding = near(idle, (w["x"], w["y"]), 9) \
        if battle.target not in NEXT else set()
    st.reserve = len(idle - holding)
    if len(idle) * st.men_per_pixel < MIN_HIT:
        return 0                        # too few to be a hit: they hold, and
                                        # go in with the next one
    st.last_advance = io.now()
    hostile = watch.others(picture, HOSTILE)

    def fighting(group, reach=4):
        return sum((c + i, r + j) in hostile for c, r in group
                   for i in range(-reach, reach + 1)
                   for j in range(-reach, reach + 1)) >= 6
    at_target = near(idle, (w["x"], w["y"]), 9)
    objective = battle.target
    if battle.arrived or len(at_target) >= IDLE_FORWARD:
        objective = NEXT.get(battle.target)
        if objective is None:
            return 0                    # the last objective: hold it
        st.outcomes.append(f"hit at {battle.target}: arrived, sent on to "
                           f"{objective}")
        io.log(f"{battle.target} reached: sending the troops there on to "
               f"{objective}")
        st.battle = battle = Battle(objective, io.now())
        st.sent_at.append(objective)
    o = place(mapdata, objective)
    idle -= near(idle, (o["x"], o["y"]), 6)        # already at the objective
    orders = 0
    groups = back_to_front(live.clusters(idle, 3, 3), (o["x"], o["y"]),
                           lambda g: live.from_drawn(*g[0]))
    for group in groups[:14]:
        if len(group) < 4 or fighting(group):
            continue
        # a tight box: wide ones overlap and pick the same troops again
        if select_group(io, group, st, watch, margin=45):
            attack_move(io, *front_point(mapdata, st, objective))
            orders += 1
    if orders:
        io.log(f"  {orders} idle groups forward sent at {objective}")
    return orders


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
             f"Men for the next hit, by the program's count: about "
             f"{st.strength} (the mass waiting at the massing place plus "
             f"about {int(st.reserve * st.men_per_pixel)} standing forward "
             f"in reserve). A hit needs at least {MIN_HIT}; the program is "
             f"waiting for {need}.",
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
    if kind != "hold" and order["place"] not in ("front", "mass") and \
            any(k in st.ground_keys for k in keys):
        return False    # a few groups sent at a city is not a hit: only
                        # the action "hit_now" sends ground troops there
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
    io.combo("ctrl", "enter")           # Ctrl+Enter: allies only (Shift+Enter is everyone)
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
    if g.dead():
        io.log(f"the general is out: {g.summary()}")
        st.general = None
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
    """Build the next hit, and do not send it until it is big enough.

    Keeps the barracks busy (when supply allows), brings in the
    reinforcements, and watches the last hit. The strength of the next
    hit is the mass at the massing place plus the troops standing
    forward in reserve, who go in with it. It returns that strength
    when it reaches what is wanted, or when the general says to hit and
    there is at least the minimum. Until then everyone is held back.
    All the while it reacts: the rules to an enemy at the mass, the
    general to what it is shown."""
    began = last_train = io.now()
    train_everywhere(io, mapdata, st)
    collected, tried, gathered = False, set(), 0
    need, readings, strength = WANT_HIT, [], 0
    counted, counted_at = None, 0       # men counted on screen, and the
                                        # minimap figure when they were
    while io.now() - t0 < TRIAL_SECONDS:
        orders, picture, still = gather_idle(io, watch, mapdata, st, tried)
        gathered += orders
        advance_front(io, watch, mapdata, st, still, picture)
        battle = st.battle              # it may have moved on to a new objective
        # The minimap gives a rough figure cheaply, and says when it is
        # worth counting properly. It jumps about as troops arrive, so
        # take the middle of the last few looks.
        mass_pixels = at_mass(watch.units(picture))
        readings.append(len(mass_pixels))
        rough = sorted(readings[-5:])[len(readings[-5:]) // 2]
        guess = (rough + st.reserve) * st.men_per_pixel
        if guess >= COUNT_WHEN * need and rough >= NEW_TROOPS and \
                rough >= counted_at * RECOUNT_GROWTH:
            # count the men themselves, on the game screen
            men = count_men(io, mass_pixels & still)
            counted_at = rough
            if len(mass_pixels) >= 20 and men:
                st.men_per_pixel = min(3.0, max(0.3, men / len(mass_pixels)))
            counted = men
            io.log(f"counted {men} men at the massing place "
                   f"({len(mass_pixels)} minimap pixels)")
        massed = counted if counted is not None else 0
        strength = st.strength = int(massed + st.reserve * st.men_per_pixel)
        waited = io.now() - began
        # the fast rule: the enemy is at the mass
        axis_mass = len(at_mass(watch.others(picture, AXIS)))
        if axis_mass >= ENEMY_AT_MASS:
            recall(io, st, f"{axis_mass} pixels of Axis colour there")
        if battle:
            battle.sample(io, watch, mapdata, picture)
            if battle.verdict()[0] in ("losing", "stalled"):
                need = BIG_HIT          # come back with more
            if battle.arrived and not battle.taxed:
                battle.taxed = True     # the city is ours: fly a building in
                io.log(f"{battle.target} reached: holding it")
                flights_after(io, mapdata, st, battle.target)
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
        # A new hit needs new troops at the massing place to send. Troops
        # already forward are moved by advance_front, not by a new hit.
        fresh = massed >= NEW_TROOPS
        if st.hit_wanted and fresh and strength >= MIN_HIT:
            io.log("the general says hit now")
            break
        st.hit_wanted = False           # not enough for a hit: asked again later
        if fresh and strength >= need:
            break
        if not collected:
            collected = collect_middle_east(io, watch, st) > 0
        if io.now() - last_train >= RETRAIN_EVERY:
            last_train = io.now()
            train_everywhere(io, mapdata, st)
        io.sleep(0.5 if general else 1.5)
    io.shot("mass")
    if battle:
        io.log(f"last hit at {battle.target}: {battle.verdict(mapdata)[0]} "
               f"({battle.verdict(mapdata)[1]})")
    io.log(f"mass at {io.now() - t0:.0f} s: {strength} men for the next "
           f"hit ({massed} counted at the massing place, about "
           f"{strength - massed} forward in reserve) after "
           f"{io.now() - began:.0f} s; {gathered} idle groups brought in; "
           f"wanted {need}")
    return strength


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
            if massed < MIN_HIT:
                io.log(f"about {massed} men is too few for a hit "
                       f"(the least is {MIN_HIT}): kept in reserve")
                break
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
                   "units_per_box": round(st.selected / max(st.selections, 1), 1),
                   "keys": "".join(st.ground_keys + st.air_keys),
                   "boxes": st.boxes, "empty": st.empty})
    return result
