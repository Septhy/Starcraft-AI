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
from bot import team as team_rules

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
        "Frankfurt 200": "Amsterdam 100", "Amsterdam 100": "Paris 500",
        "Konigsberg 200": "Berlin 1000",
        "Warsaw 200": "Berlin 1000", "Krakow 200": "Berlin 1000",
        # the repository owner: once Berlin is cleared, on to Paris and
        # then Madrid; the Balkan road also ends at Paris and Madrid,
        # after the Netherlands (Amsterdam)
        "Berlin 1000": "Paris 500", "Paris 500": "Madrid 1000"}
CLEARED = 8                    # fewer enemy minimap pixels than this at a
                               # target: it is cleared, and the troops go on
ADVANCE_EVERY = 5              # seconds between checks for idle troops forward
IDLE_FORWARD = 20              # minimap pixels at a target that mean it is taken
MIN_FORWARD = 6                # idle troops of the hit this big are sent on
SCOUT_WAIT = 150               # seconds: the Middle East spawn point is left to the
                               # scout and its spawn until then, and fetched after
BALKANS = (126, 106, 172, 142) # tiles: left, top, right, bottom
BALKAN_AXIS = 60               # this many more Axis pixels there than at the start: go south
# Points across a target's front, in tiles from its centre. Each group
# is sent to its own, so the army arrives as a wall, not a line.
FRONT = [(4, -5), (4, -1), (4, 3), (6, -3), (6, 1), (6, 5), (2, -3),
         (2, 1), (0, 5), (2, -7)]
HOME_MASS = (160 * 32, 76 * 32)  # map pixels: where the army masses, west of Smolensk
MASS = HOME_MASS               # where it masses now: the allies may move it
MASS_RADIUS = 13               # minimap pixels around it that count as there
MIDDLE_EAST = (219 * 32, 129 * 32)   # bring a unit here for the spawn
# Buildings to fly to a city: (when, kind of building, its tile, the
# city). "When" is a hit's number, or a target's name for the first
# hit sent at that target. A building
# floating over a city counts as holding it.
# (when, city): after the first hit, or once a city is reached, a spare
# building (never a barracks: they make the marines) floats to the city.
FLIGHTS = [(1, "Warsaw 200"), ("Warsaw 200", "Warsaw 200"),
           ("Krakow 200", "Warsaw 200"), ("Konigsberg 200", "Konigsberg 200")]
# Krakow, Romania and Factory 7 are looked after all game by tax_rounds().
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
OPENING_ANNOUNCE = 30          # seconds: the first hit is announced (it goes 30 s later)
TRIAL_SECONDS = 7200           # play for up to two hours
GAME_OVER_LOOKS = 8            # looks in a row with no minimap: the game has ended
# How big a hit has to be, in men. The repository owner: at least 140,
# and normally 160 to 300. How many are at hand is judged at a glance
# (men_at_mass): the supply figure less the men spread out elsewhere.
# No boxes are drawn to count.
MIN_HIT = 140                  # never send less than this as a hit
WANT_HIT = 180                 # what a hit normally waits for
BIG_HIT = 240                  # after a hit was lost or stalled
NEW_TROOPS = 40                # a new hit needs at least this many at the mass
SUPPLY_SLACK = 4               # this close to the limit counts as at it
RETRY_IDLE = 30                # seconds before the same idle group is tried again
BIG_MASS = WANT_HIT
RETRAIN_EVERY = 55             # seconds between rounds of the barracks
FIRST_HIT_SWEEPS = 3           # passes over the massing place at the first hit
HIT_SWEEPS = 4                 # and at the later ones, stopping once it is empty


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
        self.men_per_pixel = 1.0   # at the mass, from the last glance
        self.selected = 0          # units picked up by the hit's boxes, in all
        self.selections = 0        # and how many boxes that took
        self.last_consult = -1e9
        self.last_chat = -1e9
        self.hit_wanted = False    # the general has said "hit now"
        self.opening_target = None
        self.rekey = 8             # ground keys already re-used this hit
        self.outcomes = []         # how each hit went, for the lessons
        self.last_advance = -1e9   # when idle forward troops were last sent on
        self.last_heard = -1e9
        self.told_capped = False
        self.tax_sent = {}         # tax city -> (when sent, building tile, arrival)
        self.start_px = set()      # our pixels in the first picture of the game
        self.flights_cities = set() # cities a FLIGHTS building has gone to
        self.f7_told = None
        self.idle_orders = {}      # idle body spot -> times it was ordered
        self.hits_sent = 0
        self.strength_log = []     # (game clock, men for the next hit)
        self.box_px = None         # minimap pixels that make a box of twelve
        self.depots = {}           # tax city -> the SCV-and-depot job for it
        self.depot_tries = {}
        self.tax_tries = {}        # tax city -> buildings sent there so far
        self.guards = {}           # tax city -> when a detachment was sent
        self.last_tax = -1e9       # when the tax cities were last looked at
        self.go_pending = False    # the team plan said go: the hit leaves now
        self.team = None           # the plan agreed with the allies (bot/team.py)
        self.ears = None           # reads the allies' chat, with an API key
        self.clock = None          # the game clock at the bottom of the screen
        self.planned_target = None # where the hit being announced goes
        self.chosen_target = None  # where the hit that has gone goes
        self.blind, self.over = 0, False   # looks without a minimap; game ended
        self.reached = set()       # targets our troops have stood on
        self.supply_seen = None    # (supply, when) last read off the screen
        self.home_axis0 = 0        # Axis pixels inside Russia at the start
        self.last_defence = -1e9   # when troops were last sent at intruders
        self.air_home = False      # the air has been pulled back to the mass
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


SPREAD_MEN = 0.3               # men a minimap pixel holds where troops are spread out
CROWD_MEN = 4.0                # the most a pixel holds where they stand packed


def men_at_mass(supply, mass_px, elsewhere_px):
    """Roughly how many men stand at the massing place, at a glance.

    The supply figure at the top of the screen says how many men Russia
    has in all. Those not at the massing place are spread out, where a
    minimap pixel is about SPREAD_MEN men; the rest are the mass. (The
    mass itself cannot be judged from its pixels: packed men share
    them.) With no supply figure to read, the mass's pixels are all
    there is to go on."""
    if supply is None:
        return int(mass_px)
    # two readings, each too low in its own case: the supply less the
    # men spread out elsewhere (too low when those are packed as well),
    # and the mass's share of our pixels (too low when the mass is packed)
    by_rest = supply[0] - SPREAD_MEN * elsewhere_px
    by_share = supply[0] * mass_px / max(1, mass_px + elsewhere_px)
    men = max(by_rest, by_share)
    return int(max(0, min(men, supply[0], CROWD_MEN * mass_px)))


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
        if io.now() - t0 >= OPENING_ANNOUNCE:
            # the first hit is announced on time; it goes 30 s later
            team_gate(io, watch, mapdata, st, True,
                      st.opening_target or TARGETS[0])
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
            | {f[1] for f in FLIGHTS}:
        t = place(mapdata, name)
        out -= near(out, (t["x"], t["y"]), 22)
    return out


def wait_for_mass(io, watch, mapdata, st, t0, earliest, latest):
    """Watch the mass grow; meanwhile pick up groups standing still away
    from it. Once it is time to hit, the hit is announced to the allies
    and goes 30 seconds later, unless they say to wait (then the army
    keeps gathering and training) or send it elsewhere."""
    tried, history, collected = set(), [], False
    ready, why, last_train = False, "", io.now()
    while True:
        a = watch.units(io.shot("watch", keep=False))
        io.sleep(1.0)
        b = watch.units(io.shot("watch", keep=False))
        now = io.now() - t0
        massed = len(at_mass(b))
        history.append((now, massed))
        old = [m for (t, m) in history if t <= now - 6]
        if not ready:
            if now >= OPENING_ANNOUNCE:
                # announced now, it goes in 30 seconds: by then the
                # starting army has had a minute to gather
                ready, why = True, "announced at the usual time"
            elif now >= latest:
                ready, why = True, "time is up"
            elif now >= earliest and old and massed <= old[-1] * 1.04:
                ready, why = True, "the mass stopped growing"
        consult(io, watch, mapdata, st)
        if not ready and st.hit_wanted and now >= 40 and massed >= MIN_HIT:
            ready, why = True, "the general says hit now"
        target = st.opening_target or TARGETS[0]
        if st.go_pending or \
                team_gate(io, watch, mapdata, st, ready, target) == "go":
            break
        if not collected:
            collected = collect_middle_east(io, watch, st) > 0
        if io.now() - last_train >= RETRAIN_EVERY:
            last_train = io.now()       # waiting on the allies: keep building
            train_everywhere(io, mapdata, st)
        idle = at_home((a & b) - at_mass(b) - near(b, MIDDLE_EAST, 6), mapdata)
        for group in live.clusters(idle, *GROUP)[:2]:
            key = min(group)
            if len(group) >= 9 and key not in tried and len(tried) < 6:
                tried.add(key)
                if select_group(io, group, st, watch):
                    attack_move(io, *MASS)
    io.shot("mass")
    io.log(f"mass at {now:.0f} s: {massed} minimap pixels of units there "
           f"({why or 'the allies asked'})")
    return massed


def target_for_front(st, mapdata, front, battle=None):
    """The target on the front the allies named: the Balkans road from
    where Russia has got to, or toward Berlin in the east."""
    if front == "balks":
        return south_next(st)
    if battle and battle.front and \
            battle.verdict()[0] in ("stalled", "losing"):
        fx, fy = battle.front
        cities = [place(mapdata, n) for n in EAST_FRONT]
        return min(cities, key=lambda c: (c["x"] - fx) ** 2
                   + (c["y"] - fy) ** 2)["name"]
    return east_next(st)


def team_gate(io, watch, mapdata, st, ready, target):
    """Ask the team plan whether the hit goes now. `ready`: Russia's own
    rules say so, toward `target`. On "go", st.chosen_target is where
    it goes: the allies' front if they named one."""
    if st.team is None:
        return "go" if ready else "mass"
    if ready and st.planned_target is None:
        st.planned_target = target
    planned = st.planned_target or target
    asked = st.team.ally_front()
    answer = st.team.gate(st.clock.time(), ready,
                          team_rules.front_of(planned))
    if answer == "go":
        front = st.team.front
        if st.team.target:              # "@R hit Warsaw": that city
            planned = st.team.target
            io.log(f"the hit goes to {planned}, as the allies asked")
        elif front != team_rules.front_of(planned) or asked:
            planned = target_for_front(st, mapdata, front, st.battle)
            io.log(f"the hit goes {front}, as the allies asked: {planned}")
        st.chosen_target, st.planned_target = planned, None
        st.go_pending = True            # in case the caller cannot go at once
    return answer


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
    # how many minimap pixels make a box of twelve: learnt from the boxes
    # themselves; at first a guess from the army estimate
    want = st.box_px or max(3, round(FULL / max(st.men_per_pixel, 0.2)))
    take, chosen, n = max(2, want), [], 0
    for attempt in range(3):
        chosen = near_first[:take]
        box = box_around(chosen, cam)
        if box is None:
            break
        io.drag(*box)
        io.sleep(0.05)
        st.boxes += 1
        n = live.selected_count(io.shot("box", keep=False))
        if n >= FULL:
            # full: the box may have held many more than twelve, and
            # those were not picked. Draw the next ones smaller.
            st.box_px = max(2, int(take * 0.6))
            break
        if n >= GOOD_BOX or take >= len(near_first):
            if n >= GOOD_BOX:
                st.box_px = take        # about right
            break
        # too few: reach for more, in proportion to how short it fell
        take = min(len(near_first), int(take * min(3.0, FULL / max(n, 2))) + 2)
        st.box_px = take
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
            if n >= FULL and len(boxed) > 1:
                # a full box: more may stand there than were picked, so
                # only the nearest half of it counts as done (trial 21:
                # a third of every hit was left at the massing place)
                left -= set(boxed[:max(1, len(boxed) // 2)])
            else:
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


def hit(io, watch, mapdata, st, target, use_keys=True, sweeps=HIT_SWEEPS):
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
    if not use_keys:
        # bodies behind the mass set off first, so they are not left
        # trailing after it
        orders += push_front(io, watch, mapdata, st, target, side="rear")
    start = None
    for sweep in range(sweeps):
        n, found = sweep_mass(io, watch, mapdata, st, target)
        orders += n
        start = start or max(found, 1)
        # sweep again until the massing place is about empty
        if n == 0 or found < 0.1 * start:
            break
        io.sleep(1.5)
    if not use_keys:                    # nothing is forward before the first hit
        orders += push_front(io, watch, mapdata, st, target, side="forward")
    for key in st.air_keys:             # air is fastest, so it goes last
        io.key(key)
        io.sleep(0.035)
        attack_move(io, *front_point(mapdata, st, target))
        orders += 1
    st.hit_sent = io.now()
    st.hits_sent += 1
    st.go_pending = False
    st.air_home = False
    per_box = st.selected / max(st.selections, 1)
    io.log(f"hit: {orders} groups sent at {target}; its boxes have held "
           f"{per_box:.1f} units each on average so far")
    return orders


def push_front(io, watch, mapdata, st, target, limit=20, side="all"):
    """Everyone else goes in with the hit: every body of ours anywhere
    on the map, not only those at the massing place. `side` "rear":
    bodies behind the massing place, standing or still walking to it
    (they set off before the mass); "forward": bodies standing forward
    of it, from earlier hits or sent at intruders. Tax guards and the
    Middle East spawn point are left alone."""
    a = watch.units(io.shot("watch", keep=False))
    io.sleep(1.0)
    b = watch.units(io.shot("front"))
    w = place(mapdata, target)
    rest = b - at_mass(b) - scout_spot(io, st, b)
    rest -= near(rest, (w["x"], w["y"]), 6)        # already there
    rest -= guarding(st, mapdata, rest, io.now())
    rear = at_home(rest, mapdata)
    if side == "rear":
        idle = rear                     # walking to the mass counts too
    elif side == "forward":
        idle = (a & b) & (rest - rear)
    else:
        idle = rear | ((a & b) & (rest - rear))
    orders = 0
    bodies = [g for g in live.clusters(idle, 6, 6) if len(g) >= GATHER_LEAST
              and (len(g) >= 9 or not all(p in st.start_px for p in g))]
    bodies = back_to_front(bodies, (w["x"], w["y"]),
                           lambda g: live.from_drawn(*g[0]))[:limit]
    for group in bodies:
        if select_group(io, group, st, watch, margin=60):
            attack_move(io, *front_point(mapdata, st, target))
            orders += 1
    if orders:
        where = {"rear": "behind the mass", "forward": "forward of the mass"
                 }.get(side, "elsewhere on the map")
        io.log(f"  {orders} bodies {where} sent as well")
    return orders


# The round countdown at the top of the screen runs in game seconds,
# 1.488 of them to a real second (fitted to 47 pictures of trial 18, to
# within a second over 24 minutes). So a "5:00" round lasts about 3:22
# of the real clock at the bottom, and the tax at "2:00" comes about
# 2:01 of real time into each round.
COUNTDOWN_RATE = 1.488


def round_timer(clock_seconds):
    """What the round's countdown at the top shows, given the game clock
    at the bottom (real seconds since the game began)."""
    left = 300 - int(clock_seconds * COUNTDOWN_RATE) % 300
    return f"{left // 60}:{left % 60:02d}"


def until_tax(clock_seconds):
    """Real seconds until the next tax (the countdown reaching 2:00)."""
    into = (clock_seconds * COUNTDOWN_RATE) % 300     # game seconds into the round
    return ((180 - into) % 300) / COUNTDOWN_RATE


def fly_building(io, mapdata, st, kind, tile, city_name):
    """Lift a building and send it to float over a city. Never a
    barracks (they make the marines) or a command centre."""
    if kind in ("Barracks", "Command Center"):
        io.log(f"flight: a {kind} is never floated")
        return False
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


# ------------------------------------------------------------ tax cities
# The repository owner: Russia always tries to float buildings over the
# Krakow and Romania beacons, and over Factory 7 (Belgrade), when no
# enemies are near; if there are, a detachment of twelve goes to
# secure the city first. Any building will do except command centres.
# Factory 7 goes to whoever has a building there while the round
# countdown is above 2:00, so the building sets off when the countdown
# shows 1:00 and must arrive before the next round's countdown reaches
# 3:00.
TAX_CITIES = ["Krakow 200", "Romania 300", "Factory 7"]
TAX_EVERY = 45                 # seconds between looks at the tax cities
TAX_AFTER_HITS = 2             # no tax efforts before the second hit has gone
TAX_ENEMY = 6                  # minimap pixels from a city: enemies "nearby"
TAX_ENEMY_LEAST = 4            # enemy pixels there that count as enemies
TAX_HEAVY = 20                 # more than this: too strong for a detachment
TAX_HERE = 3                   # our pixels this close to the city: a building is there
GUARD_SIZE = 12                # a detachment: one full selection
GUARD_EVERY = 300              # seconds between detachments to one city
GUARD_KEEP = 90                # seconds a detachment is left to guard its city
FLOAT_SPEED = 0.75             # tiles a real second, a lifted building (guess)
FLOAT_SLACK = 20               # seconds after arrival before a missing building is replaced
F7_SET_OFF = 60                # countdown seconds: set off for Factory 7 at 1:00
F7_ARRIVE = 180                # and arrive before the countdown reaches 3:00
# Never a barracks (the repository owner: they make the marines), never
# a command centre.
TAX_KINDS = ["Engineering Bay", "Factory", "Starport"]
KEEP_BUILDINGS = {(163, 99)}   # the barracks on Odessa: it taxes Odessa
TAX_TRIES = 3                  # buildings sent to one city in a game at most


def countdown_left(clock_seconds):
    """Game seconds left on the round countdown at the top."""
    return 300 - (clock_seconds * COUNTDOWN_RATE) % 300


def until_countdown(clock_seconds, mark):
    """Real seconds until the countdown next shows `mark` game seconds."""
    return ((countdown_left(clock_seconds) - mark) % 300) / COUNTDOWN_RATE


def spare_buildings(mapdata, st):
    """Buildings that may be floated to a tax city: factories,
    starports and engineering bays; never barracks or command centres."""
    out = []
    for b in mapdata["slots"][SLOT]["buildings"]:
        tile = (b["x"] // 32, b["y"] // 32)
        if b["type"] not in TAX_KINDS or tile in KEEP_BUILDINGS \
                or tile in st.flights_done or tile in st.flown:
            continue
        out.append(b)
    return out


def float_time(b, city):
    d = ((b["x"] - city["x"]) ** 2 + (b["y"] - city["y"]) ** 2) ** 0.5 / 32
    return d / FLOAT_SPEED


def guarding(st, mapdata, pixels, now):
    """Our pixels around tax cities a detachment was sent to lately:
    they stay to guard it, and are not called back to the mass."""
    out = set()
    for name, when in st.guards.items():
        flight = st.tax_sent.get(name)
        waiting = flight and now < flight[2] + FLOAT_SLACK
        if now - when < GUARD_KEEP or waiting:
            c = place(mapdata, name)
            out |= near(pixels, (c["x"], c["y"]), TAX_ENEMY + 4)
    return out


def send_guard(io, watch, mapdata, st, name, picture):
    """A detachment of twelve from the massing place (or the nearest
    idle troops) to clear and hold a tax city."""
    city = place(mapdata, name)
    ours = watch.units(picture)
    pool = at_mass(ours)
    if len(pool) < 6:
        pool = ours - near(ours, MIDDLE_EAST, 6)
    if not pool:
        return False
    cc, cr = live.to_drawn(city["x"], city["y"])
    seed = min(pool, key=lambda p: (p[0] - cc) ** 2 + (p[1] - cr) ** 2)
    sx, sy = live.from_drawn(*seed)
    cam = look_at(io, *centred(sx, sy))
    saved = st.men_per_pixel
    st.men_per_pixel = max(st.men_per_pixel, 1.0)
    boxed, n = select_full(io, st, seed, pool, cam)
    st.men_per_pixel = saved
    if n == 0:
        return False
    attack_move(io, city["x"], city["y"])
    st.guards[name] = io.now()
    io.log(f"tax: enemies near {name}: a detachment of {n} sent to "
           f"secure it")
    return True


COMMAND_CENTRES = [(157, 51), (209, 49)]   # tiles: Russia's two command centres
SCV_SPEED = 2.0                # tiles a real second, an SCV walking (guess)
SCV_TRAIN = 12                 # real seconds to make one
DEPOT_TRIES = 2                # depots tried at one city in a game at most
DEPOT_BUILD = 45               # real seconds to see whether the depot went up
DEPOT_SPOTS = [(0, 110), (110, 0), (-110, 0), (0, -110), (110, 110),
               (-110, 110)]    # screen pixels from the beacon to try


def select_building(io, b):
    """Click a building until the game shows it selected."""
    l, t, r, btm = live.GAME_AREA
    cam = look_at(io, b["x"], b["y"], wait=0.25)
    px, py = live.on_screen(b["x"], b["y"], cam)
    for dx, dy in TRIES:
        x, y = px + dx, py + dy
        if l + 5 < x < r - 5 and t + 5 < y < btm - 5:
            io.click(x, y)
            io.sleep(0.12)
            if live.building_selected(io.card()):
                return True
    return False


def depot_at(io, watch, mapdata, st, name, ours):
    """With no factory or starport left to float, Russia makes an SCV at
    the nearest command centre, sends it to the city (the centre's
    rally point), and has it build a supply depot next to the beacon.
    Called on each round of the tax cities; returns 1 when it gave an
    order."""
    city = place(mapdata, name)
    cx, cy = city["x"], city["y"]
    job = st.depots.get(name)
    now = io.now()
    if job is None:
        if st.depot_tries.get(name, 0) >= DEPOT_TRIES:
            return 0
        tile = min(COMMAND_CENTRES, key=lambda t: (t[0] * 32 - cx) ** 2
                   + (t[1] * 32 - cy) ** 2)
        b = next((b for b in mapdata["slots"][SLOT]["buildings"]
                  if b["type"] == "Command Center"
                  and (b["x"] // 32, b["y"] // 32) == tile), None)
        st.depot_tries[name] = st.depot_tries.get(name, 0) + 1
        if b is None or not select_building(io, b):
            io.log(f"tax: the command centre for {name}'s SCV was not found")
            return 0
        io.key("s")                     # build an SCV
        io.sleep(0.1)
        io.click(*live.minimap_point(cx, cy), button="right")   # its rally
        io.sleep(0.1)
        walk = ((b["x"] - cx) ** 2 + (b["y"] - cy) ** 2) ** 0.5 / 32 / SCV_SPEED
        st.depots[name] = {"stage": "walking", "due": now + SCV_TRAIN + walk}
        io.log(f"tax: no factory or starport left: an SCV is on its way to "
               f"build a depot at {name} (about {SCV_TRAIN + walk:.0f} s)")
        return 1
    if job["stage"] == "walking":
        if now < job["due"]:
            return 0
        here = near(ours, (cx, cy), 8)
        if not here:
            if now > job["due"] + 60:
                del st.depots[name]     # it never came: try again later
                io.log(f"tax: the SCV for {name} did not arrive")
            return 0
        if not select_group(io, sorted(here)[:4], st, watch, margin=40):
            return 0
        cam = look_at(io, *centred(cx, cy), wait=0.2)
        sx, sy = live.on_screen(cx, cy, cam)
        io.key("b")                     # build a basic structure:
        io.sleep(0.1)
        io.key("s")                     # a supply depot
        io.sleep(0.15)
        l, t, r, btm = live.GAME_AREA
        for dx, dy in DEPOT_SPOTS:      # the first good spot takes it;
            x, y = sx + dx, sy + dy     # the others then just click
            if l + 40 < x < r - 40 and t + 40 < y < btm - 40:
                io.click(x, y)
                io.sleep(0.15)
        io.key("esc")                   # out of placing, if still in it
        job.update(stage="building", due=now + DEPOT_BUILD)
        io.shot("depot-" + name.split()[0])
        io.log(f"tax: depot ordered at {name}")
        return 1
    if job["stage"] == "building" and now >= job["due"]:
        if near(ours, (cx, cy), TAX_HERE + 2):
            job["stage"] = "done"
            io.log(f"tax: a depot stands at {name}")
        else:
            del st.depots[name]
            io.log(f"tax: no depot to be seen at {name}")
    return 0


def float_to(io, watch, mapdata, st, name, ours, to_arrive=None):
    """Float the best spare building to a tax city; with none left, an
    SCV builds a depot there. Returns 1 if it gave an order."""
    city = place(mapdata, name)
    clock = st.clock.time() if st.clock else io.now()
    choices = spare_buildings(mapdata, st)
    if to_arrive is not None:
        choices = [b for b in choices if float_time(b, city) <= to_arrive]
    elif "Factory 7" not in st.tax_sent:
        # keep the buildings that can reach Factory 7 in its window
        # for Factory 7, while there are others
        f7 = place(mapdata, "Factory 7")
        window = (300 - F7_ARRIVE + F7_SET_OFF) / COUNTDOWN_RATE
        others = [b for b in choices if float_time(b, f7) > window]
        if others:
            choices = others
    if not choices:
        if not spare_buildings(mapdata, st):
            # nothing left to float: an SCV builds a depot there
            return depot_at(io, watch, mapdata, st, name, ours)
        if to_arrive is not None:
            rnd = int(clock * COUNTDOWN_RATE // 300)
            if st.f7_told != rnd:       # once a round is enough
                st.f7_told = rnd
                io.log(f"tax: no building can reach {name} before 3:00")
        return 0
    choices.sort(key=lambda b: (TAX_KINDS.index(b["type"]),
                                float_time(b, city)))
    b = choices[0]
    tile = (b["x"] // 32, b["y"] // 32)
    st.flights_done.add(tile)
    if not fly_building(io, mapdata, st, b["type"], tile, name):
        return 0
    st.tax_sent[name] = (io.now(), tile, io.now() + float_time(b, city))
    st.tax_tries[name] = st.tax_tries.get(name, 0) + 1
    io.log(f"tax: {b['type']} floated to {name}, there in about "
           f"{float_time(b, city):.0f} s")
    return 1


def tax_with_hit(io, watch, mapdata, st, target, picture):
    """A hit clears the way: from the second hit on, a building follows
    a hit east to Krakow, or a hit to the Balkans to Romania, unless one
    is there or on its way already."""
    if st.hits_sent < TAX_AFTER_HITS:
        return 0
    name = "Romania 300" if team_rules.front_of(target) == "balks" \
        else "Krakow 200"
    city = place(mapdata, name)
    ours = watch.units(picture) if picture is not None else set()
    flight = st.tax_sent.get(name)
    if flight and io.now() < flight[2] + FLOAT_SLACK:
        return 0                        # one is on its way
    if flight and near(ours, (city["x"], city["y"]), TAX_HERE):
        return 0                        # and it is there
    if st.tax_tries.get(name, 0) >= TAX_TRIES:
        return 0
    io.log(f"tax: a building follows the hit to {name}")
    return float_to(io, watch, mapdata, st, name, ours)


def tax_rounds(io, watch, mapdata, st, picture):
    """Look after the tax cities: float a building over each that has
    none, if no enemies are near; send a detachment first if there are
    a few; leave it to the hits if there are many."""
    if st.clock is None or st.hits_sent < TAX_AFTER_HITS:
        return 0
    # Krakow and Romania now and then; Factory 7 on every pass, because
    # its moment (1:00 to 0:00 on the countdown) lasts only about 40
    # real seconds and must not be missed
    due = io.now() - st.last_tax >= TAX_EVERY
    if due:
        st.last_tax = io.now()
    clock = st.clock.time()
    ours = watch.units(picture)
    hostile = watch.others(picture, HOSTILE)
    sent = 0
    for name in TAX_CITIES:
        if name != "Factory 7" and not due:
            continue
        city = place(mapdata, name)
        cx, cy = city["x"], city["y"]
        if st.depots.get(name, {}).get("stage") in ("walking", "building"):
            sent += depot_at(io, watch, mapdata, st, name, ours)
            continue                    # an SCV is seeing to it
        if near(ours, (cx, cy), TAX_HERE) and name not in st.tax_sent:
            continue                    # something of ours is there already
        flight = st.tax_sent.get(name)
        if flight and io.now() < flight[2] + FLOAT_SLACK:
            continue                    # on its way
        if flight and near(ours, (cx, cy), TAX_HERE):
            continue                    # arrived and still there
        if st.tax_tries.get(name, 0) >= TAX_TRIES:
            continue                    # lost twice: no more buildings there
        if name == "Factory 7":
            # set off at 1:00 on the countdown; the window closes when
            # it can no longer arrive before 3:00
            to_arrive = until_countdown(clock, F7_ARRIVE)
            # at 1:00 there are 60 + 120 game seconds until 3:00 of the
            # next round; more than that means it is not yet 1:00
            if to_arrive * COUNTDOWN_RATE > 300 - F7_ARRIVE + F7_SET_OFF + 1:
                continue                # too early: before 1:00
        else:
            to_arrive = None
        enemies = len(near(hostile, (cx, cy), TAX_ENEMY))
        if enemies >= TAX_ENEMY_LEAST:
            if enemies > TAX_HEAVY:
                continue                # a job for a hit, not twelve men
            if io.now() - st.guards.get(name, -1e9) >= GUARD_EVERY:
                send_guard(io, watch, mapdata, st, name, picture)
            continue
        sent += float_to(io, watch, mapdata, st, name, ours, to_arrive)
    return sent


def flights_after(io, mapdata, st, when):
    """Send the buildings whose turn has come: the nearest spare
    building (not a barracks) to each city, once per city."""
    for w, city_name in FLIGHTS:
        if w != when or city_name in st.flights_cities:
            continue
        st.flights_cities.add(city_name)
        city = place(mapdata, city_name)
        choices = spare_buildings(mapdata, st)
        if not choices:
            io.log(f"flight: no spare building left for {city_name}")
            continue
        # keep the few that can reach Factory 7 in its window for it
        f7 = place(mapdata, "Factory 7")
        window = (300 - F7_ARRIVE + F7_SET_OFF) / COUNTDOWN_RATE
        others = [b for b in choices if float_time(b, f7) > window]
        b = min(others or choices, key=lambda b: float_time(b, city))
        tile = (b["x"] // 32, b["y"] // 32)
        st.flights_done.add(tile)
        fly_building(io, mapdata, st, b["type"], tile, city_name)


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
    # after the studied part of the game: keep alternating
    turn = int((seconds_in - PLAN[-1][1]) // 270)
    return "south" if turn % 2 == 0 else "north"


def east_next(st):
    """Where a new hit to the east goes: always Berlin. Paris and Madrid
    are only ever reached through Berlin (the repository owner): a hit
    that takes and clears Berlin is carried on from there by
    advance_front, and a hit sent later goes to Berlin first and is
    carried on again once it is there."""
    return "Berlin 1000"


def south_next(st):
    """Where a new hit to the Balkans is sent: always Romania, the way
    in. From Smolensk a straight march to Belgrade, Hungary or beyond
    goes through German Poland, which is the eastern front, not the
    Balkans (trial 21: "gone balks" at Frankfurt marched east). Once
    the hit reaches Romania it is carried on down the road
    (advance_front): Factory 7, Hungary, Munich, Frankfurt, Amsterdam."""
    return "Romania 300"


def choose_target(io, watch, st, mapdata=None, battle=None):
    """Where the next hit should go.

    The general's choice comes first. Otherwise the plan by the clock:
    south when qororo98 and penny[eef] go south. Otherwise: if the last
    hit stalled or was lost short of its target, aim at the city nearest
    to where that happened. Otherwise south if the Axis has grown in the
    Balkans since the start (Germany starts with troops there), and
    Berlin if not."""
    if st.advised and io.now() - st.advised[1] <= 40:
        name = st.advised[0]
        if team_rules.front_of(name) == "balks":
            name = south_next(st)       # the Balkans: in through Romania
        while name in st.reached and name in NEXT and \
                team_rules.front_of(name) == "east" and name != "Berlin 1000":
            name = NEXT[name]           # already ours: on to Berlin, never
                                        # past it (Paris goes through Berlin)
        io.log(f"next target {name} (the general's choice"
               + ("" if name == st.advised[0] else
                  f" was {st.advised[0]}, which is already taken") + ")")
        return name
    south = south_next(st)
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
        target = east_next(st)
        why = "Berlin again" if "Berlin 1000" not in st.reached else \
            "through Berlin, and on west from there"
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
        self.retreated = False  # its survivors have been pulled back
        self.clearing = False   # reached, but enemies are still there

    def sample(self, io, watch, mapdata, picture):
        w = place(mapdata, self.target)
        found = find_front(watch, picture, mapdata, self.target)
        if len(near(watch.units(picture), (w["x"], w["y"]), ARRIVED_WITHIN)) >= 10:
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


GATHER_LEAST = 3               # minimap pixels: a body this big is worth fetching
GATHER_PER_PASS = 8            # bodies ordered to the mass in one pass at most
STUCK_AFTER = 3                # orders to one body that never moves, then leave it


def taken_on_the_way(st, target):
    """Cities already taken on the road that leads to `target`: troops
    left standing there follow the push on, rather than walk home."""
    out = []
    for name in st.reached:
        at, steps = name, 0
        while at in NEXT and steps < 10:
            at, steps = NEXT[at], steps + 1
            if at == target:
                out.append(name)
                break
    return out


def in_battle(st, mapdata, pixels):
    """Our pixels that belong to the hit being fought: around its target
    or its front. advance_front moves those, not the gathering."""
    battle = st.battle
    if battle is None or battle.retreated or \
            battle.verdict()[0] in ("losing", "stalled"):
        return set()                    # its survivors go back to the mass
    w = place(mapdata, battle.target)
    out = near(pixels, (w["x"], w["y"]), 26)
    if battle.front:
        out |= near(pixels, battle.front, 14)
    for name in taken_on_the_way(st, battle.target):
        c = place(mapdata, name)
        out |= near(pixels, (c["x"], c["y"]), 12)
    return out


def scout_spot(io, st, pixels):
    """Our pixels at the Middle East spawn point, while the scout and the
    spawn are still being dealt with there (collect_middle_east). After
    that, anyone left there is fetched like everyone else."""
    if io.now() - st.t0 < SCOUT_WAIT:
        return near(pixels, MIDDLE_EAST, 6)
    return set()


def gather_idle(io, watch, mapdata, st, tried):
    """Send every body of ours that is standing still to the mass, so
    the next hit has everyone: the reinforcements the map gives Russia
    at Moscow, Finland, Stalingrad and Siberia, defenders sent at an
    intruder, the remains of earlier hits, and anyone missed. Small
    bodies too, and those forward of the mass. Left alone: the hit
    being fought, troops in contact with the enemy, the Middle East
    spawn point and the detachments guarding tax cities."""
    a = watch.units(io.shot("watch", keep=False))
    io.sleep(1.0)
    b_picture = io.shot("watch", keep=False)
    b = watch.units(b_picture)
    still = a & b
    idle = still - at_mass(b) - scout_spot(io, st, b)
    idle -= in_battle(st, mapdata, idle)
    idle -= guarding(st, mapdata, idle, io.now())
    hostile = watch.others(b_picture, HOSTILE)
    mc, mr = live.to_drawn(*MASS)
    # A small body standing exactly where something of ours stood at the
    # start may be a building that a unit hid then: buildings never
    # move, while spawns and leftovers of hits turn up in new places.
    bodies = [g for g in live.clusters(idle, 6, 6)
              if len(g) >= GATHER_LEAST and not in_contact(g, hostile)
              and (len(g) >= 9 or not all(p in st.start_px for p in g))]
    # the farthest first: they take longest to arrive
    bodies.sort(key=lambda g: -((g[0][0] - mc) ** 2 + (g[0][1] - mr) ** 2))
    orders = 0
    for group in bodies:
        if orders >= GATHER_PER_PASS:
            break
        cx = sum(p[0] for p in group) // len(group)
        cy = sum(p[1] for p in group) // len(group)
        key = (cx // 4, cy // 4)
        # a place is tried again after a while: new troops appear at
        # the same spots all game
        if io.now() - tried.get(key, -1e9) < RETRY_IDLE:
            continue
        tried[key] = io.now()
        st.idle_orders[key] = st.idle_orders.get(key, 0) + 1
        if st.idle_orders[key] > STUCK_AFTER:
            continue                    # ordered three times and never moved
        if select_group(io, group, st, watch, margin=60):
            attack_move(io, *MASS)
            orders += 1
            if st.idle_orders[key] == STUCK_AFTER:
                # it has not moved for two orders: keep a picture of it
                # (to learn what it is) and leave it be from now on
                x, y = live.from_drawn(cx, cy)
                io.shot("stuck")
                io.log(f"  a body near {place_name(mapdata, x, y)} has not "
                       f"moved after {STUCK_AFTER} orders: left alone "
                       f"(picture 'stuck')")
    if orders:
        io.log(f"  {orders} idle bodies sent to the massing place")
    return orders, b_picture, still


def in_contact(group, hostile, reach=4):
    return sum((c + i, r + j) in hostile for c, r in group
               for i in range(-reach, reach + 1)
               for j in range(-reach, reach + 1)) >= 6


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
    for name in taken_on_the_way(st, battle.target):
        c = place(mapdata, name)         # left behind at a city taken earlier
        mine |= near(idle, (c["x"], c["y"]), 12)
    idle = mine
    # Troops standing forward count toward the next hit, unless they are
    # already holding the end of their road: those have arrived.
    holding = near(idle, (w["x"], w["y"]), 9) \
        if battle.target not in NEXT else set()
    st.reserve = len(idle - holding)
    if len(idle) < MIN_FORWARD:
        return 0
    st.last_advance = io.now()
    hostile = watch.others(picture, HOSTILE)

    def fighting(group, reach=4):
        return sum((c + i, r + j) in hostile for c, r in group
                   for i in range(-reach, reach + 1)
                   for j in range(-reach, reach + 1)) >= 6
    at_target = near(idle, (w["x"], w["y"]), 9)
    objective = battle.target
    enemy_left = len(near(hostile, (w["x"], w["y"]), 8))
    if enemy_left >= CLEARED and (battle.arrived
                                  or len(at_target) >= IDLE_FORWARD):
        # there, but not cleared: the troops there finish the job first
        if not battle.clearing:
            battle.clearing = True
            io.log(f"{battle.target} reached but not cleared "
                   f"({enemy_left} pixels of enemy): clearing it first")
    elif battle.arrived or len(at_target) >= IDLE_FORWARD:
        st.reached.add(battle.target)
        objective = NEXT.get(battle.target)
        if objective is None:
            return 0                    # the last objective: hold it
        if len(idle) * SPREAD_MEN * 2 < MIN_HIT:
            return 0                    # too few to go on alone: they hold
                                        # the city and go in with the next hit
        st.outcomes.append(f"hit at {battle.target}: arrived, sent on to "
                           f"{objective}")
        io.log(f"{battle.target} reached: sending the troops there on to "
               f"{objective}")
        st.battle = battle = Battle(objective, io.now())
        st.sent_at.append(objective)
    # (troops of this hit that have stopped short of its target are sent
    # at it again whatever their number: the hit has to keep advancing)
    o = place(mapdata, objective)
    idle -= near(idle, (o["x"], o["y"]), 6)        # already at the objective
    orders = 0
    groups = back_to_front(live.clusters(idle, 4, 4), (o["x"], o["y"]),
                           lambda g: live.from_drawn(*g[0]))
    for group in groups[:24]:
        if len(group) < 4 or fighting(group):
            continue
        # a tight box: wide ones overlap and pick the same troops again
        if select_group(io, group, st, watch, margin=45):
            attack_move(io, *front_point(mapdata, st, objective))
            orders += 1
    if orders:
        io.log(f"  {orders} idle groups forward sent at {objective}")
    return orders


# Deep Russia only: east of the massing place and north of the Black
# Sea. Enemy standing near Odessa, Romania or the Polish border has been
# there all along, and only shows on the minimap once our troops come
# near: that is not an invasion (trial 18).
HOME = (170, 0, 256, 98)       # tiles: left, top, right, bottom
INTRUDERS = 10                 # more Axis pixels there than at the start: defend
DEFEND_EVERY = 20              # seconds between sending troops at intruders
AIR_REACH = 10                 # minimap pixels from the front the air looks for prey


def axis_at_home(watch, picture):
    """Axis units inside Russia, away from the border fighting."""
    l, t, r, b = HOME
    out = set()
    for c, row in watch.others(picture, AXIS):
        x, y = live.from_drawn(c, row)
        if l <= x / 32 < r and t <= y / 32 < b:
            out.add((c, row))
    return out - at_mass(out)           # at the mass itself: the recall rule


def middle(pixels):
    """The map point at the middle of some minimap pixels."""
    return live.from_drawn(sum(p[0] for p in pixels) / len(pixels),
                           sum(p[1] for p in pixels) / len(pixels))


def defend_home(io, watch, mapdata, st, picture, still):
    """Respond to the enemy coming into Russia: the troops standing at
    the massing place and the air go to meet him. Returns orders given."""
    inside = axis_at_home(watch, picture)
    if len(inside) - st.home_axis0 < INTRUDERS or \
            io.now() - st.last_defence < DEFEND_EVERY:
        return 0
    body = live.clusters(inside, 8, 8)[0]
    if len(body) < 6:
        return 0                        # scattered dots, not an attack
    st.last_defence = io.now()
    x, y = middle(body)
    orders = 0
    for group in live.clusters(at_mass(still), *GROUP)[:6]:
        if len(group) >= 4 and select_group(io, group, st, watch):
            attack_move(io, x, y)
            orders += 1
    for key in st.air_keys:
        io.key(key)
        io.sleep(0.05)
        attack_move(io, x, y)
        orders += 1
    io.log(f"Axis inside Russia near {place_name(mapdata, x, y)} "
           f"({len(inside)} pixels): {orders} groups sent to meet it")
    return orders


def fight(io, watch, mapdata, st, picture):
    """Look after a hit once it is in contact.

    A hit that is being lost is broken off: what is left of it near the
    front walks back to the massing place, and the air with it, to go
    in again with the next hit. Otherwise the air is kept on the enemy
    nearest our front, not on a fixed spot."""
    battle = st.battle
    if battle is None or not battle.front:
        return 0
    orders = 0
    if battle.verdict()[0] == "losing" and not battle.retreated:
        battle.retreated = True
        left = near(forward_units(watch.units(picture), mapdata),
                    battle.front, 16)
        home = live.minimap_point(*MASS)
        for group in live.clusters(left, 3, 3)[:8]:
            if len(group) >= 3 and select_group(io, group, st, watch,
                                                margin=45):
                io.click(*home, button="right")     # walk, do not fight back
                io.sleep(0.04)
                orders += 1
        for key in st.air_keys:
            io.key(key)
            io.sleep(0.05)
            io.click(*home, button="right")
            io.sleep(0.04)
        st.air_home = True
        io.log(f"hit at {battle.target} is being lost: {orders} groups of "
               f"survivors and the air pulled back to the massing place")
        return orders
    if st.air_keys and not st.air_home and \
            io.now() - st.air_moved >= AIR_FOLLOW_EVERY:
        st.air_moved = io.now()
        prey = near(watch.others(picture, HOSTILE), battle.front, AIR_REACH)
        spot = middle(prey) if len(prey) >= 6 else battle.front
        for key in st.air_keys:         # the air goes for the enemy at the front
            io.key(key)
            io.sleep(0.05)
            attack_move(io, *spot)
    return orders


TARGET_NAMES = {"Berlin": "Berlin 1000", "Romania": "Romania 300",
                "Belgrade": "Factory 7", "Warsaw": "Warsaw 200",
                "Konigsberg": "Konigsberg 200", "Krakow": "Krakow 200"}
ENEMY_AT_MASS = 12             # Axis pixels at the mass that mean "defend"
AIR_FOLLOW_EVERY = 8           # seconds between moving the air to the front
RECALL_COOLDOWN = 20           # seconds between recalls of the army
RECALL_AFTER_HIT = 45          # seconds: a hit just sent is not called back
ARRIVED_WITHIN = 6             # minimap pixels from a target that count as there


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
    now = st.clock.time() if st.clock else io.now() - t0
    lines = [f"Game clock (bottom of the screen): "
             f"{int(now) // 60}:{int(now) % 60:02d}. Round countdown (top) "
             f"about {round_timer(now)}; next tax in about "
             f"{until_tax(now):.0f} real seconds.",
             f"Men for the next hit, by the program's count: about "
             f"{st.strength} (the mass waiting at the massing place plus "
             f"about {int(st.reserve * SPREAD_MEN)} standing forward "
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


def say(io, st, text, force=False):
    """Type a line to the allies, not too often (announcements of hits
    always go)."""
    text = "".join(c for c in text if " " <= c <= "~")[:60].strip()
    if not text or (not force and io.now() - st.last_chat < CHAT_EVERY):
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
    went = False
    train_everywhere(io, mapdata, st)
    collected, tried, gathered = False, {}, 0
    need, readings, strength = WANT_HIT, [], 0
    capped, told = False, -99
    while io.now() - t0 < TRIAL_SECONDS:
        orders, picture, still = gather_idle(io, watch, mapdata, st, tried)
        gathered += orders
        st.blind = 0 if live.minimap_showing(picture) else st.blind + 1
        if st.blind >= GAME_OVER_LOOKS:
            st.over = True
            io.log("the minimap has gone: the game seems to be over")
            break
        advance_front(io, watch, mapdata, st, still, picture)
        battle = st.battle              # it may have moved on to a new objective
        # The minimap gives a rough figure cheaply, and says when it is
        # worth counting properly. It jumps about as troops arrive, so
        # take the middle of the last few looks.
        mass_pixels = at_mass(watch.units(picture))
        readings.append(len(mass_pixels))
        rough = sorted(readings[-5:])[len(readings[-5:]) // 2]
        # At the supply limit the army cannot grow: whatever is there
        # is the hit, so the least is enough.
        supply = numbers.read_supply(picture)
        if supply:
            st.supply_seen = (supply, io.now())
        elif st.supply_seen and io.now() - st.supply_seen[1] <= 30:
            supply = st.supply_seen[0]  # unreadable this look: the last one
        capped = bool(supply) and supply[0] >= supply[1] - SUPPLY_SLACK
        st.capped = capped
        # How many are there is judged at a glance, with no boxes drawn.
        ours = watch.units(picture)
        massed = men_at_mass(supply, rough, len(ours - mass_pixels))
        if capped and rough >= NEW_TROOPS:
            massed = max(massed, MIN_HIT)   # full supply: this is the army
        if rough >= 20:
            st.men_per_pixel = min(6.0, max(0.3, massed / rough))
        strength = st.strength = int(massed + st.reserve * SPREAD_MEN)
        if st.clock:
            st.strength_log.append((st.clock.time(), strength))
            del st.strength_log[:-120]
        if abs(massed - told) >= 25:
            told = massed
            io.log(f"about {massed} men at the massing place (supply "
                   f"{supply[0] if supply else '?'}, {rough} minimap "
                   f"pixels there, {len(ours - mass_pixels)} elsewhere)")
        waited = io.now() - began
        # the fast rule: the enemy is at the mass
        axis_mass = len(at_mass(watch.others(picture, AXIS)))
        if axis_mass >= ENEMY_AT_MASS and \
                io.now() - getattr(st, "hit_sent", -1e9) >= RECALL_AFTER_HIT:
            recall(io, st, f"{axis_mass} pixels of Axis colour there")
        if battle:
            battle.sample(io, watch, mapdata, picture)
            if battle.verdict()[0] in ("losing", "stalled"):
                need = BIG_HIT          # come back with more
            if battle.arrived and not battle.taxed:
                battle.taxed = True     # the city is ours: fly a building in
                st.reached.add(battle.target)
                io.log(f"{battle.target} reached: holding it")
                flights_after(io, mapdata, st, battle.target)
        fight(io, watch, mapdata, st, picture)
        defend_home(io, watch, mapdata, st, picture, still)
        tax_rounds(io, watch, mapdata, st, picture)
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
        # At the supply limit the army cannot grow any more: whatever is
        # there is the hit, so the least is enough. (This comes after the
        # "last hit was lost: want more" rule, which must not undo it:
        # in trial 19 it did, and the bot never hit again.)
        if capped and need > MIN_HIT:
            if not st.told_capped:
                io.log(f"supply is full ({supply[0]}/{supply[1]}): the army "
                       f"cannot grow, so {MIN_HIT} men are enough")
            st.told_capped = True
            need = MIN_HIT
        elif not capped:
            st.told_capped = False
        st.need = need
        fresh = massed >= NEW_TROOPS
        ready = fresh and strength >= need
        if st.hit_wanted and fresh and strength >= MIN_HIT:
            if not ready:
                io.log("the general says hit now")
            ready = True
        else:
            st.hit_wanted = False       # not enough for a hit: asked again later
        # Russia's own plan for where it goes, fixed when it is first ready
        target = st.planned_target
        if ready and target is None:
            target = choose_target(io, watch, st, mapdata, battle)
        # the allies have the last word on when, and where
        if team_gate(io, watch, mapdata, st, ready,
                     target or TARGETS[0]) == "go":
            went = True
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
           f"hit (about {massed} at the massing place, about "
           f"{strength - massed} forward in reserve) after "
           f"{io.now() - began:.0f} s; {gathered} idle groups brought in; "
           f"wanted {need}")
    return strength, went


def close_battle(st, mapdata):
    """Note how the watched hit ended, for the log and the lessons."""
    b = st.battle
    if b:
        kind, facts = b.verdict(mapdata)
        st.outcomes.append(f"hit at {b.target}: {kind} ({facts})")


def move_mass(io, mapdata, st, order):
    """An ally said "@R mass at <place>": move the massing place there,
    if Russia's troops can walk there; otherwise say so."""
    global MASS
    from bot import places
    asked = order.place.strip()
    if asked.lower() in ("home", "smolensk", "smolensk 200", "back"):
        MASS = HOME_MASS
        say(io, st, "massing at Smolensk", force=True)
        io.log(f"{order.colour} said {order.said!r}: massing at Smolensk again")
        return
    name = places.resolve(mapdata, asked)
    if name is None:
        say(io, st, "I can't find that place", force=True)
        io.log(f"{order.colour} said {order.said!r}: no place called {asked!r}")
        return
    city = place(mapdata, name)
    if not places.walkable(city["x"], city["y"]):
        say(io, st, "I can't mass there", force=True)
        io.log(f"{order.colour} said {order.said!r}: {name} cannot be walked to")
        return
    MASS = (city["x"], city["y"])
    say(io, st, f"massing at {places.plain(name)}", force=True)
    io.log(f"{order.colour} said {order.said!r}: massing at {name} from now on")


def place_for_hit(mapdata, text):
    """"@R hit <city>": the city meant, if the troops can walk there.
    Returns (map name, name to type) or (None, the answer to type)."""
    from bot import places
    name = places.resolve(mapdata, text)
    if name is None:
        return None, "I can't find that place"
    city = place(mapdata, name)
    if not places.walkable(city["x"], city["y"]):
        return None, "I can't hit there"
    return name, places.plain(name)


def mass_name(mapdata):
    """The name of the place Russia masses at now."""
    if MASS == HOME_MASS:
        return "Smolensk"
    from bot import places
    return places.plain(place_name(mapdata, *MASS))


STATUS_LOOKBACK = 90           # seconds of army growth used to guess the next hit


def next_hit_eta(st, now):
    """When Russia's own next hit should go, on the game clock: when the
    army is big enough (judged from how fast it has grown lately), plus
    the 30 seconds' warning. None if it cannot be guessed."""
    if st.capped or st.strength >= st.need:
        return now + team_rules.ANNOUNCE
    old = [(t, s) for t, s in st.strength_log if t <= now - 20]
    if not old:
        return None
    t0, s0 = max((p for p in old if p[0] >= now - STATUS_LOOKBACK),
                 default=old[-1])
    rate = (st.strength - s0) / max(now - t0, 1)
    if rate <= 0.05:
        return None                     # not growing: no telling
    wait = (st.need - st.strength) / rate
    return now + min(wait, 900) + team_rules.ANNOUNCE


def status_line(io, mapdata, st):
    """"@R status": supply, massing place, plan and the time of the next
    hit, in one chat line."""
    seen = st.supply_seen
    pop = f"{seen[0][0]}/{seen[0][1]}" if seen else "?/200"
    now = st.clock.time() if st.clock else io.now()
    told = st.team.plan(now) if st.team else None
    if told is not None:
        plan, at = told
        if plan == "waiting":
            # after the wait the hit still needs the army to be ready
            own = next_hit_eta(st, now)
            if own is not None:
                at = max(at, own)
            elif not (st.capped or st.strength >= st.need):
                at = None               # not ready, not growing: no telling
    else:
        target = st.planned_target
        front = team_rules.front_of(target) if target else \
            ("east" if planned_front(now) == "north" else "balks")
        plan = f"{st.strength}/{st.need} men, {front}"
        at = next_hit_eta(st, now)
    when = f"hit est. {team_rules.clock_text(at)}" if at is not None \
        else "hit est. ?"
    return f"{pop} | {mass_name(mapdata)} | {plan} | {when}"


def reset_orders(io, mapdata, st):
    """"@R reset": every order dropped, mass back at Smolensk, and the
    usual pattern again."""
    global MASS
    MASS = HOME_MASS
    st.planned_target = st.chosen_target = None
    st.go_pending = False
    say(io, st, "reset: massing at Smolensk, usual plan", force=True)
    io.log("reset by the allies: massing at Smolensk, usual plan")


class Listening:
    """The game's io, but every screenshot is also used to read the game
    clock and to listen to the allies' chat."""

    def __init__(self, io, st):
        self.io, self.st = io, st

    def __getattr__(self, name):
        return getattr(self.io, name)

    def shot(self, label, keep=True):
        picture = self.io.shot(label, keep)
        hear(self.io, self.st, picture)
        return picture


HEAR_EVERY = 0.5               # seconds between readings of the clock and chat


def hear(io, st, picture):
    """Read the game clock, and act on what the allies have said."""
    if st.clock is None or io.now() - st.last_heard < HEAR_EVERY:
        return
    st.last_heard = io.now()
    now = st.clock.update(picture)
    ears = st.ears
    if ears is None:
        return
    if ears.dead():
        io.log(f"the chat reader is out: {ears.summary()}")
        st.ears = None
        return
    ears.listen(picture, now)
    for when, colour, text in ears.lines(now):
        io.log(f"chat [{colour}] {text}")
    for order in ears.orders(now):
        st.team.heard(order, now)


def run(io, mapdata=None, general=None, save_lessons=None, ears=None):
    """Returns a short result for the log. `save_lessons` is called with
    the general's lessons for the next game, if it wrote any. `ears`
    reads the allies' chat (bot/team.py); without it Russia still
    announces its hits but cannot hear the answers."""
    mapdata = mapdata or load_map()
    side = mapdata["slots"][SLOT]
    first = io.shot("start")
    watch = live.Watch(first, side["structures"], side["units"])
    if not live.minimap_showing(first) or not watch.ok:
        io.log("The live game's minimap is not on screen. Nothing done.")
        return {"trained": 0, "gathered": 0, "hits": []}
    t0, st = io.now(), State()
    st.general, st.t0 = general, t0
    raw = io
    st.clock = team_rules.GameClock(raw.now)
    st.clock.update(first)
    st.ears = ears

    def announce(text):
        say(raw, st, text, force=True)
        if st.ears:
            st.ears.context = text
    global MASS
    MASS = HOME_MASS                    # every game starts at Smolensk
    st.team = team_rules.Team(
        announce, raw.log,
        on_mass=lambda o: move_mass(raw, mapdata, st, o),
        on_status=lambda: say(raw, st, status_line(raw, mapdata, st),
                              force=True),
        on_reset=lambda: reset_orders(raw, mapdata, st),
        resolve=lambda text: place_for_hit(mapdata, text))
    if ears is not None:
        from bot import places
        ears.places = places.names_for_chat(mapdata)
    io = Listening(raw, st)
    if ears is None:
        io.log("no API key: hits are announced, but the allies' answers "
               "cannot be read")
    st.balkan_start = axis_in(watch, first, BALKANS)
    st.home_axis0 = len(axis_at_home(watch, first))
    st.start_px = watch.units(first)
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
        target = st.chosen_target or st.opening_target or TARGETS[0]
        if st.opening_target and not st.chosen_target:
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
            massed, went = build_big_mass(io, watch, mapdata, st, t0,
                                          st.battle, general)
            if st.over or not went:
                if not went and not st.over:
                    io.log(f"about {massed} men, not sent: time is up")
                break
            target = st.chosen_target or choose_target(io, watch, st,
                                                       mapdata, st.battle)
            close_battle(st, mapdata)
            st.hit_wanted = False
            hits.append(hit(io, watch, mapdata, st, target, use_keys=False))
            st.sent_at.append(target)
            st.battle = Battle(target, io.now())
            flights_after(io, mapdata, st, len(hits))
            flights_after(io, mapdata, st, target)
            tax_with_hit(io, watch, mapdata, st, target,
                         io.shot("watch", keep=False))
            game = st.clock.time() if st.clock else io.now() - t0
            io.log(f"  ({since()} since start; round countdown about "
                   f"{round_timer(game)}, tax in about "
                   f"{until_tax(game):.0f} s)")
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
        if st.ears:
            io.log(st.ears.summary())
    result.update({"targets": st.sent_at,
                   "units_per_box": round(st.selected / max(st.selections, 1), 1),
                   "keys": "".join(st.ground_keys + st.air_keys),
                   "boxes": st.boxes, "empty": st.empty})
    return result
