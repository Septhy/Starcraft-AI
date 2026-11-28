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
import math
import re

from eyes import live, numbers
from bot import team as team_rules

SLOT = "5"                     # Russia
# The first hit goes to Berlin. Later hits go to Berlin again, or south
# to Romania and then the factory at Belgrade ("Factory 7"). In the
# replays Russia turns south early mostly when the Axis is busy in the
# Balkans, so the bot looks: enough Axis colour there, and it goes south.
TARGETS = ["Berlin 1000", "Romania 300", "Factory 7"]
# Cities on the way to Berlin. East hits are always aimed at Berlin itself,
# even after a stall here (the repository owner, trial 37).
EAST_FRONT = ["Konigsberg 200", "Warsaw 200", "Krakow 200"]
AXIS = [0, 1, 7]               # Germany, Italy, Spain: Russia's enemies
# Who Russia's troops actually fight: the Axis, and the computer player
# (white) that holds the Balkans, Turkey and the east.
HOSTILE = AXIS + [6]
# For the tax only the Axis counts (trial 37: "Axis hold Warsaw" when it
# was not: the white of the computer's beacons and of the minimap's view
# box, which sits on the city being looked at, was counted as enemy).
TAX_HOSTILE = AXIS
# Where a hit goes on to once it has taken its target, so the troops do
# not stand idle there.
# In the south: Romania, the factory at Belgrade, then north-west
# toward the Netherlands (the repository owner), by way of the cities
# that lie between.
NEXT = {"Romania 300": "Factory 7",
        "Factory 7": "Amsterdam 100",  # the repository owner: Belgrade
                                       # secured, on to Amsterdam (was Hungary)
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
ADVANCE_EVERY_BALKS = 2.5      # on the Balkan road (the repository owner: idle
                               # men were left round Greece)
BALKS_AREA = (100, 108, 200, 192)  # tiles: the Balkans, Greece and Serbia;
                               # idle men anywhere here go on with the hit
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
MASS_RADIUS = 15               # minimap pixels around it that count as there
                               # (the spread mass reaches 12 tiles out)
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
GROUND_KEYS = list("1234567")   # (the repository owner: 8 is an air key)
AIR_KEYS = list("908")         # the fleet keys: 9 and 0, then 8 and 7 are
                               # taken from the ground keys if needed
# The repository owner: Russia's air is kept apart from the spawns, on
# its own number keys, as one fleet: up to eleven Scouts ("Light
# Fighter" in the game) and one Heavy Artillery ("Heavy Defensive
# Artillery", sieged in place) on a key; when a key is full, the next
# key. New Scouts are added to the key (select them, then Shift + the
# key). Never the Battlecruisers ("Battle ship"): they go with the
# ground army.
FLEET_SIZE = 11                # Scouts on one fleet key
HEAVY_ARTILLERY = [(5684, 2489), (5231, 1701), (6796, 1665), (7458, 2443)]
MOSCOW_HA = (6796, 1665)       # the Heavy Defensive Artillery at Moscow: the
                               # same gun on keys 9, 0 and 8 (the repository
                               # owner), keyed right after the allied chat
FLEET_PARK = (21 * 32, -11 * 32)  # map pixels from the mass: where the fleet waits,
                                 # clear of the sweeps of the massing place
FLEET_MOVE_AFTER = 40          # seconds: the fleet's first order (the Middle East
                               # scouts in it must reach the Middle East first)
FIRST_ORDERS_UNTIL = 45        # seconds: stop the first round of orders
WAVE_EARLIEST = 45             # seconds: do not hit before this (qororo98
                               # and penny[eef] send theirs at 37 to 51)
WAVE_LATEST = 100              # seconds: hit by now whatever happens
OPENING_ANNOUNCE = 30          # seconds: the first hit is announced (it goes 30 s later)
TRIAL_SECONDS = 7200           # play for up to two hours
GAME_OVER_LOOKS = 8            # looks in a row with no minimap: the game has ended
# How big a hit has to be, in men. The repository owner: at least 140,
# and normally 160 to 300; trial 37: 20 fewer all round (120, 160, 220).
# How many are at hand is judged at a glance (men_at_mass): the supply figure less the men spread out elsewhere.
# No boxes are drawn to count.
MIN_HIT = 120                  # never send less than this as a hit
WANT_HIT = 160                 # what a hit normally waits for
BIG_HIT = 220                  # after a hit was lost or stalled
NEW_TROOPS = 40                # a new hit needs at least this many at the mass
SUPPLY_SLACK = 4               # this close to the limit counts as at it
CAPPED_CROWD = 150             # minimap pixels at the mass that make it the army
SUPPLY_REACH = 0.9             # of what the supply limit leaves for the mass
HIT_GAP = 90                   # seconds after a hit before the next, unless it
                               # was lost or has arrived
RETRY_IDLE = 30                # seconds before the same idle group is tried again
BIG_MASS = WANT_HIT
RETRAIN_EVERY = 25             # seconds between rounds of the barracks (the
                               # repository owner: more often between hits)
FIRST_HIT_SWEEPS = 3           # passes over the massing place at the first hit
HIT_SWEEPS = 4                 # and at the later ones, stopping once it is empty


class Stopped(Exception):
    pass


class State:
    def __init__(self):
        global _PARK_AT
        _PARK_AT = None            # a new game: no beacon chosen yet
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
        self.idle_stuck = {}       # idle body spot -> when it was given up on
        self.idle_sizes = {}       # idle body spot -> its size at the last order
        self.last_choke = -1e9
        self.last_balks_sweep = -1e9
        self.tax_jobs = {}         # "@R tax <city>": city -> its one try
        self.upgrade_wanted = set()  # "@R upgrade": the upgrades still to start
        self.upgrade_level = {"weapons": 0, "armor": 0}
        self.upgrade_next = {}     # upgrade -> when its next level may start
        self.upgrades_done = False # 3/3 both: the bays are left alone
        self.upgrade_asked = False # an ally asked ("@R upgrade": up to 3/3)
        self.last_upgrade_look = -1e9
        self.krakow_landed = False # Krakow's building is on the ground
        self.land_tries = 0
        self.last_land_check = -1e9
        self.fleet_spot = None     # where the fleet was last ordered to stay
        self.fleet_looked = -1e9   # when the enemy round it was last counted
        self.spread_next = 0       # the next spot the mass is spread to
        self.spawn_next = 0        # the next spot a group brought in goes to
        self.keyed = []            # keys version: (key, its place in the line)
        self.last_key_step = -1e9
        self.mass_keyed = None     # the keys version: (when, keys, target)
        self.empty_skipped = 0     # boxes not drawn: nothing there any more
        self.walking = []          # (when, minimap pixel) bodies sent to the mass
        self.lift_fails = {}       # building tile -> lifts that did not happen
        self.allied_chat = False   # the Messaging window was set to allies     # when the Odessa-Romania choke was last cleared
        self.hits_sent = 0
        self.fleet = []            # the fleet keys: key, Scouts on it, its artillery
        self.fleet_moved = False
        self.scouts_done = set()   # (tax round, factory) whose Scouts were fetched
        self.scout_tries = {}
        self.moscow_tries = {}
        self.scout_one = None      # what one Scout looks like in the panel
        self.scout_frame = None    # and its framed picture in a group
        self.ship_one = None       # what one Battlecruiser looks like there
        self.last_added_key = None
        self.moscow_done = set()   # the Moscow air spawns already fetched
        self.fleet_checks = 0
        self.fleet_task = None     # bring air: the ally the fleet is with
        self.air_ping = None       # bring air: waiting for an ally's ping
        self.watch = None
        self.old_mass = None       # the massing place just left: its army moves
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
        self.air = None            # the air brain: AirStats
        self.ha_gone = set()       # Heavy Artillery spots known to be empty
        self.ha_keys = set()       # air keys holding the Moscow artillery
        self.ha_frame = None       # the artillery's framed picture in a group
        self.factory_ground = set()   # (round, factory): its new ground fetched
        self.park_at = None        # where the fleet waits (a beacon near the mass)
        self.park_chosen = -1e9
        self.screen_per_box = 12   # men (patches on the screen) a box is drawn round
        self.key_pictures = 0      # pictures of a pressed fleet key kept
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


BALKS_POINT = (150 * 32, 146 * 32)   # the repository owner: a hit to the
                               # Balkans attacks on to here, past Romania


def send_at(io, mapdata, st, target, point=None):
    """Attack-move what is selected at a target. A hit to Romania clears
    Romania first and then goes on, queued (Shift), to the point beyond
    it toward Serbia (the repository owner)."""
    attack_move(io, *(point or front_point(mapdata, st, target)))
    if target == "Romania 300":
        io.key("a")
        io.sleep(0.04)
        io.click_with("shift", *live.minimap_point(*BALKS_POINT))
        io.sleep(0.04)


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


def box_and_check(io, box, st, air=False):
    """Drag a box. True if the screen then shows units selected. Scouts
    are taken out unless `air` (a box meant for the air)."""
    io.drag(*box)
    io.sleep(0.05)
    st.boxes += 1
    if live.units_selected(io.card()):
        if not air and st.scout_frame is not None and drop_scouts(io, st) == 0:
            return False                # only Scouts: not for the ground
        return True
    st.empty += 1
    return False


FRESH = 2                      # minimap pixels round a group where it may have moved


def select_group(io, pixels, st, watch=None, margin=None, air=False):
    """Look at the units drawn at these minimap pixels and box them."""
    margin = MARGIN if margin is None else margin
    cols = [p[0] for p in pixels]
    rows = [p[1] for p in pixels]
    x0, y0 = live.from_drawn(min(cols) - 0.5, min(rows) - 0.5)
    x1, y1 = live.from_drawn(max(cols) + 0.5, max(rows) + 0.5)
    l, t, r, b = live.GAME_AREA
    cam = look_at(io, *centred((x0 + x1) / 2, (y0 + y1) / 2))
    if watch is not None:
        # a fresh look: the box goes round where the troops are now, not
        # where they stood a moment ago; none there, no box (trials 24,
        # 25: boxes on empty ground picked up depots and factories)
        now = watch.units(io.shot("box-look", keep=False))
        c0, c1, r0, r1 = min(cols), max(cols), min(rows), max(rows)
        here = [p for p in now if c0 - FRESH <= p[0] <= c1 + FRESH
                and r0 - FRESH <= p[1] <= r1 + FRESH]
        if not here:
            st.empty_skipped += 1
            return False
        cols = [p[0] for p in here]
        rows = [p[1] for p in here]
        x0, y0 = live.from_drawn(min(cols) - 0.5, min(rows) - 0.5)
        x1, y1 = live.from_drawn(max(cols) + 0.5, max(rows) + 0.5)
    sx0, sy0 = live.on_screen(x0, y0, cam)
    sx1, sy1 = live.on_screen(x1, y1, cam)
    box = (max(l + 4, sx0 - margin), max(t + 4, sy0 - margin),
           min(r - 4, sx1 + margin), min(b - 4, sy1 + margin))
    if box[2] - box[0] < 40 or box[3] - box[1] < 40:
        return False
    if box_and_check(io, box, st, air=air):
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
    if not select_group(io, [live.to_drawn(a["x"], a["y"]) for a in pair], st,
                        air=True):
        # (trial 27: the box was emptied of its Scouts as if it were for
        # the ground, and the Middle East was never visited)
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


RALLY_SPOTS = [(dx, dy) for dy in (0, -8, 8) for dx in (0, -8, 8)]
                               # tiles from the mass point: each barracks its
                               # own, within an area 16 tiles across (the
                               # repository owner), so new marines arrive
                               # spread out, not in one clump


def rally_spot(mapdata, b):
    """The rally point (map pixels) of one barracks: its own spot round
    the mass point, by its place in the list of barracks."""
    tiles = [(x["x"] // 32, x["y"] // 32) for x in barracks_of(mapdata)]
    k = tiles.index((b["x"] // 32, b["y"] // 32)) \
        if (b["x"] // 32, b["y"] // 32) in tiles else 0
    dx, dy = RALLY_SPOTS[k % len(RALLY_SPOTS)]
    return MASS[0] + dx * 32, MASS[1] + dy * 32


AIR_OUT_STATES = ("with the hit", "fighting")   # (trial 35: not "with the
                               # army" too: that held the barracks 145 s)
AIR_OUT_MAX = 150              # seconds after a hit when training goes on
                               # anyway (a stalled hit can keep the air out)


def air_out_with_hit(io, st):
    """The air is still out with a hit (not back at its spot, not lost):
    the repository owner wants no marines made until then."""
    a = getattr(st, "air", None)
    if a is None or not st.air_keys or a.state not in AIR_OUT_STATES:
        return False
    if a.state == "fighting" and st.fleet_task is not None:
        return False                    # at an ally's ping, not a hit
    return io.now() - getattr(st, "hit_sent", -1e9) < AIR_OUT_MAX


def train_everywhere(io, mapdata, st, check_supply=True):
    """Queue marines at the barracks, but only as many as the supply
    limit has room for. At the limit, nothing is queued at all. Not
    while the air is still out with a hit (the repository owner)."""
    if air_out_with_hit(io, st):
        if not getattr(st, "told_air_out", False):
            st.told_air_out = True
            io.log("marines wait: the air is still out with the hit")
        return 0
    st.told_air_out = False
    room = room_for_marines(io) if check_supply else None
    keep = tax_reserve(st)
    if keep:
        money = numbers.read_minerals(io.shot("money", keep=False))
        if money is not None:
            can = max(0, (money - keep) // MARINE_PRICE)
            room = can if room is None else min(room, can)
            if can < 3:
                io.log(f"marines wait: {keep} minerals kept for the tax "
                       f"the allies asked for")
                return 0
    if room is not None and room < 3:
        if not st.capped:
            io.log("supply is at its limit: not training")
        st.capped = True
        return 0
    st.capped = False

    def one(b):
        if not select_barracks(io, b):
            return False
        io.click(*live.minimap_point(*rally_spot(mapdata, b)), button="right")
        io.sleep(0.06)                  # its own rally point by the mass
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


_PARK_AT = None                # the beacon spot chosen for the fleet (choose_park)


def fleet_spot():
    """Where the fleet waits: by a city beacon near the mass with our or
    allied troops by it (choose_park), else a fixed spot beside the
    mass; outside the mass either way, so the boxes of the massing place
    do not pick the Scouts up."""
    if _PARK_AT is not None:
        return _PARK_AT
    return (MASS[0] + FLEET_PARK[0], MASS[1] + FLEET_PARK[1])


# The repository owner (trial 37): while the army masses, the air sat in
# the way at the massing place; it waits by a nearby beacon instead, one
# with brown or allied troops by it.
PARK_MIN = 16                  # tiles from the mass point: past the spread mass
PARK_MAX = 32                  # tiles from it at most
PARK_FRIENDS = 3               # our or allied minimap pixels by the beacon
PARK_NEAR = 4                  # minimap pixels round the beacon looked at
PARK_SAFE = 8                  # no Axis pixels this near the beacon
PARK_SIDE = 3                  # tiles beside the beacon the fleet waits
PARK_EVERY = 60                # seconds between choices
PARK_FORWARD = 5               # tiles nearer the enemy than the mass allowed


def is_beacon(name):
    """A city's beacon: its place name ends in its tax ("Smolensk 200")."""
    return bool(re.search(r"\d+$", name)) and not name.startswith("Factory")


def choose_park(io, watch, mapdata, st, picture):
    """Pick where the fleet waits: the nearest city beacon 16 to 32 tiles
    from the mass, not nearer the enemy than the mass is, with our or
    allied troops by it and no Axis there. None found: the fixed spot.
    True if the spot changed."""
    global _PARK_AT
    now = io.now()
    if watch is None or picture is None or now - st.park_chosen < PARK_EVERY:
        return False
    st.park_chosen = now
    friends = watch.units(picture) | watch.others(picture,
                                                  list(ALLY_SLOTS.values()))
    axis = watch.others(picture, AXIS)
    front = place(mapdata, TARGETS[0])
    def dist(a, b):
        return math.hypot(a[0] - b[0], a[1] - b[1]) / 32
    mass_front = dist(MASS, (front["x"], front["y"]))
    best = None
    for p in mapdata["places"]:
        if not is_beacon(p["name"]):
            continue
        xy = (p["x"], p["y"])
        d = dist(MASS, xy)
        if not PARK_MIN <= d <= PARK_MAX or \
                dist(xy, (front["x"], front["y"])) < mass_front - PARK_FORWARD:
            continue
        if len(near(friends, xy, PARK_NEAR)) < PARK_FRIENDS or \
                near(axis, xy, PARK_SAFE):
            continue
        if best is None or d < best[0]:
            best = (d, p["name"], xy)
    spot = None if best is None else \
        (best[2][0] + PARK_SIDE * 32, best[2][1])
    if spot == _PARK_AT:
        return False
    _PARK_AT = spot
    st.park_at = spot
    io.log("air: the fleet waits " + (f"by {best[1]}'s beacon" if best else
                                      "beside the mass (no beacon by friends)"))
    return True


def click_unit(io, x, y, movable=True):
    """Click the unit standing at a map point, trying a few spots round
    it until the game shows it picked: the Move button for a unit that
    can move, or any command buttons for the sieged Heavy Artillery.
    Returns the screen point that picked it, or None."""
    l, t, r, b = live.GAME_AREA
    cam = look_at(io, x, y, wait=0.15)
    px, py = live.on_screen(x, y, cam)
    for dx, dy in TRIES:
        sx, sy = px + dx, py + dy
        if not (l + 5 < sx < r - 5 and t + 5 < sy < b - 5):
            continue
        io.click(sx, sy)
        io.sleep(0.08)
        card = io.card()
        if live.units_selected(card) if movable else \
                not live._first_button_is(card, "blank_card.png"):
            return (sx, sy)
    return None


def free_ground_keys(st):
    """The number keys the ground groups may use: 1 to 8, less any the
    fleet has taken."""
    return [k for k in GROUND_KEYS if k not in st.air_keys]


def fleet_room(st):
    return FLEET_SIZE - st.fleet[-1]["scouts"] if st.fleet else 0


# where the gun shows is a little off the estimate (the same offset
# TRIES allows for, 40 right and 80 down): a grid round that, nearest first
HA_SPOTS = list(TRIES) + [(40 + dx, 80 + dy) for dx in (-35, 0, 35)
                          for dy in (-35, 0, 35) if (dx, dy) != (0, 0)]


HA_BOX = (40, 50)              # half the box drawn round where the gun shows


def pick_ha(io, st, x, y):
    """Select the sieged Heavy Defensive Artillery at a map point the way
    the repository owner does: a small box dragged round it, tried at a
    few spots round where it should show, until the game shows a gun
    selected: no Move, the first button empty and Stop second (trial 36
    pictures; a click that missed left the Scouts selected in trial 35).
    True if picked."""
    l, t, r, b = live.GAME_AREA
    cam = look_at(io, x, y, wait=0.15)
    px, py = live.on_screen(x, y, cam)
    hx, hy = HA_BOX
    for dx, dy in HA_SPOTS:
        sx, sy = px + dx, py + dy
        box = (max(l + 3, sx - hx), max(t + 3, sy - hy),
               min(r - 3, sx + hx), min(b - 3, sy + hy))
        if box[2] - box[0] < 20 or box[3] - box[1] < 20:
            continue
        io.drag(*box)
        io.sleep(0.08)
        if live.gun_selected(io.shot("ha-pick", keep=False)):
            return True
    return False


def key_moscow_ha(io, st):
    """Right after the allied chat is set (the repository owner): the
    Heavy Defensive Artillery at Moscow is picked and put on every air
    key (Ctrl + 9, 0, 8), so each key starts with it."""
    if pick_ha(io, st, *MOSCOW_HA):
        for key in AIR_KEYS:
            io.combo("ctrl", key)
            io.sleep(0.04)
        st.ha_keys = set(AIR_KEYS)
        for key in AIR_KEYS:
            if key in st.ground_keys:
                st.ground_keys.remove(key)
        io.shot("moscow-artillery")
        io.log(f"fleet: the Heavy Artillery at Moscow on keys "
               f"{' '.join(AIR_KEYS)}")
        return True
    io.shot("moscow-artillery")
    io.log("fleet: the Heavy Artillery at Moscow was not picked; the keys "
           "start without it and it is tried again later")
    return False


def open_fleet_key(io, st):
    """Start the next fleet key: it already holds the Moscow Heavy
    Artillery if that was keyed at the start; otherwise its first Scouts
    make it (Ctrl + key: Shift + key does nothing to a key not yet made,
    trial 36). False if there is no key left."""
    if len(st.fleet) >= len(AIR_KEYS):
        return False
    key = AIR_KEYS[len(st.fleet)]
    has_gun = key in st.ha_keys
    st.fleet.append({"key": key, "scouts": 0, "ha": MOSCOW_HA,
                     "ha_dead": not has_gun, "new": not has_gun})
    if has_gun:
        key_in_use(st, key)
    io.log(f"fleet: key {key} started" + ("" if has_gun else
                                          " (without the artillery)"))
    return True


def add_to_key(io, st, entry):
    """The selection onto a fleet key: Ctrl + key the first time if the
    key is not made yet, Shift + key after."""
    if entry.get("new"):
        io.combo("ctrl", entry["key"])
        entry["new"] = False
    else:
        io.combo("shift", entry["key"])
    io.sleep(0.04)
    key_in_use(st, entry["key"])


REGROUP_REACH = 700            # screen pixels round the parking spot looked at
REGROUP_STEP = 4               # tiles a keyed group steps aside, so the
                               # next box takes the others


def regroup_fleet(io, st):
    """Before a hit (the repository owner: every brown plane keyed and sent
    with the hit): the Scouts at the parking spot are put on the air keys
    afresh, a dozen at a time; a keyed group steps aside so the next box
    takes the rest (trial 36: an unkeyed squadron sat at the parking spot
    and the dogfight's camera jumped between the two). A key that holds
    the Moscow Heavy Artillery is pressed first and the box added to it
    (Shift + drag), so the gun stays on it and is never picked again
    (trial 37: the keys were made afresh without it and the gun was
    fetched from Moscow again and again)."""
    a = getattr(st, "air", None)
    if not st.fleet or (a is not None and a.state != "parked"):
        return 0
    park = fleet_spot()
    entries, keyed = [], 0
    for key in AIR_KEYS:
        cam = look_at(io, *centred(*park), wait=0.25)
        pic = io.shot("regroup", keep=False)
        if pic is None:
            break
        px, py = live.on_screen(park[0], park[1], cam)
        gold = gold_on_screen(pic, px, py, REGROUP_REACH)
        if not gold:
            break
        # the thickest bunch of gold: the nearest to the first, a box round it
        g0 = gold[0]
        bunch = [p for p in gold if (p[0] - g0[0]) ** 2 + (p[1] - g0[1]) ** 2
                 <= 300 ** 2]
        l, t, r, b = live.GAME_AREA
        box = (max(l + 3, min(p[0] for p in bunch) - 50),
               max(t + 3, min(p[1] for p in bunch) - 50),
               min(r - 3, max(p[0] for p in bunch) + 50),
               min(b - 3, max(p[1] for p in bunch) + 50))
        has_gun = key in st.ha_keys and hasattr(io, "drag_with")
        if has_gun:
            io.key(key)                 # the gun and the key's Scouts
            io.sleep(0.06)
            io.drag_with("shift", *box)  # and the Scouts here added
        else:
            io.drag(*box)
        io.sleep(0.08)
        n = live.selected_count(io.shot("regroup-box", keep=False))
        got = scouts_picked(io, st, n, guns=1 if has_gun else 0) if n else None
        if got is None:
            break
        n, guns = got
        if n - guns > FLEET_SIZE:
            n = trim_selection(io, FLEET_SIZE + guns, st)
        if n - guns <= 0:
            break
        io.combo("ctrl", key)           # the key afresh, the gun kept on it
        io.sleep(0.04)
        entries.append({"key": key, "scouts": n - guns, "ha": MOSCOW_HA,
                        "ha_dead": not guns, "new": False})
        keyed += n - guns
        if guns:
            st.ha_keys.add(key)
        else:
            st.ha_keys.discard(key)
        # aside, so the next box does not take them again
        side = (park[0] + REGROUP_STEP * 32 * len(entries), park[1])
        io.click(*live.minimap_point(*side), button="right")
        io.sleep(0.8)
    if not entries:
        return 0
    st.fleet = entries
    st.air_keys = []
    for e in entries:
        key_in_use(st, e["key"])
    io.log(f"fleet: {keyed} Scouts at the parking spot keyed afresh on "
           f"{' '.join(e['key'] for e in entries)} before the hit"
           + (" (the gun kept on " + " ".join(e["key"] for e in entries
                                              if not e["ha_dead"]) + ")"
              if any(not e["ha_dead"] for e in entries) else ""))
    return keyed


def key_in_use(st, key):
    """A fleet key with something on it: ordered with the fleet from now
    on, no longer a ground key (an empty one is never pressed)."""
    if key not in st.air_keys:
        st.air_keys.append(key)
    if key in st.ground_keys:           # 8 or 7: no longer a ground key
        st.ground_keys.remove(key)


def add_to_fleet(io, st, x, y, kind="Scout"):
    """Select the Scout at a map point and add it to the fleet key with
    room (Shift + key); a full key starts the next, with its own Heavy
    Artillery. False if every fleet key is full."""
    if fleet_room(st) <= 0 and not open_fleet_key(io, st):
        return False
    entry = st.fleet[-1]
    if not click_scout(io, st, x, y, reach=2):
        io.log(f"fleet: no Scout found at {x}, {y}: not added")
        return False
    add_to_key(io, st, entry)            # added to the key
    entry["scouts"] += 1
    return True


def trim_selection(io, keep, st=None):
    """Drop units from the selection (Shift + click on their pictures in
    the bottom panel, the last first) until `keep` are left; never the
    Moscow Heavy Artillery (the repository owner, trial 37): with `st`,
    only Scouts are taken out. After each click the panel is read again
    until it shows one fewer (trial 37: read too soon, each picture was
    clicked twice and two units went). Returns how many are selected in
    the end."""
    pic = io.shot("trim", keep=False)
    n = live.selected_count(pic)
    for _ in range(12):
        if n <= keep:
            break
        i = min(n, 12) - 1
        kinds = frame_kinds(st, pic, n) if st is not None else None
        if kinds is not None:
            scouts = [j for j, k in enumerate(kinds) if k == "scout"]
            if not scouts:
                break
            i = scouts[-1]
        x0, y0, x1, y1 = _frame_box(i, min(n, 12))
        io.click_with("shift", (x0 + x1) // 2, (y0 + y1) // 2)
        pic = panel_changed(io, n, "trim")
        n = live.selected_count(pic)
    return n


def panel_changed(io, before, label):
    """The panel read again, a few times if need be, until its count of
    units differs from `before`. The last picture."""
    pic = None
    for _ in range(4):
        io.sleep(0.08)
        pic = io.shot(label, keep=False)
        if live.selected_count(pic) != before:
            break
    return pic


FLEET_RECOUNT = 60             # seconds between counts of what is on the keys


HA_BY_PICTURE = False          # trial 34: the picture check said "no Heavy
                               # Artillery" and "0 Scouts" when they were
                               # there; off until it is tuned on real pictures
KEY_PICTURES = 6               # pictures of a pressed fleet key kept a game


def read_key(st, pic):
    """What a fleet key shows when pressed: (units, Scouts, Heavy
    Artillery there?). Each unit's picture is checked against the Scout
    learnt at the start: anything not a Scout on a fleet key is its
    Heavy Artillery (the repository owner: check the key's unit
    pictures, no clicks on the map). Unknown (None) before the Scout is
    learnt."""
    n = live.selected_count(pic)
    if n == 0:
        return 0, 0, False
    if n == 1:
        if st.scout_one is None:
            return 1, None, None
        scout = alike(_crop(pic, PANEL_ONE), st.scout_one, trim=0) >= SHAPE_SAME
        return 1, int(scout), not scout
    if st.scout_frame is None:
        return n, None, None
    scouts = sum(1 for i in range(min(n, 12))
                 if alike(_crop(pic, _frame_box(i, n)), st.scout_frame)
                 >= SHAPE_SAME)
    return n, scouts, scouts < n


def on_key(e):
    """Units on a fleet key besides its Scouts: its Heavy Artillery, if
    it still stands."""
    return 0 if e.get("ha_dead") else 1


def recount_fleet(io, st, force=False):
    """Count the Scouts left on each fleet key (pressing it; the Heavy
    Artillery not counted), so lost Scouts make room. True if a key
    turned out to have room. Selects the keys: callers select again."""
    if not force and \
            io.now() - getattr(st, "fleet_counted", -1e9) < FLEET_RECOUNT:
        return False
    st.fleet_counted = io.now()
    found = False
    total, read = 0, False
    for e in st.fleet:
        io.key(e["key"])
        io.sleep(0.06)
        pic = io.shot("fleet-count", keep=False)
        if pic is None:
            continue
        units, scouts, ha = read_key(st, pic) if HA_BY_PICTURE else \
            (live.selected_count(pic), None, None)
        if scouts is None:              # by the count, less the artillery
            scouts = max(0, units - on_key(e))
            learn_ha_frame(io, st, e, pic, units)
        elif not ha and not e.get("ha_dead"):
            e["ha_dead"] = True
            io.log(f"air: key {e['key']} has no Heavy Artillery any more "
                   f"(none of its pictures is not a Scout)")
        elif ha and e.get("ha_dead"):
            e["ha_dead"] = False
        if st.key_pictures < KEY_PICTURES:
            st.key_pictures += 1        # kept, to tune the picture check
            io.shot(f"fleet-key-{e['key']}")
        n = scouts
        total, read = total + n, True
        if n < e["scouts"]:
            io.log(f"fleet: key {e['key']} has {n} Scouts left, not "
                   f"{e['scouts']}")
            e["scouts"] = n
        found = found or n < FLEET_SIZE
    if read:
        air_stats(io, st).count(total, io.now())
    return found


def key_with_room(st, n):
    """The first fleet key with room for n more Scouts, or None."""
    for e in st.fleet:
        if FLEET_SIZE - e["scouts"] >= n:
            return e
    return None


def add_selected_scouts(io, st, reselect, depth=0):
    """Put the Scouts that `reselect()` selects onto the fleet, after
    checking they are Scouts (ground units picked with them are taken
    out; the Moscow Heavy Artillery, if picked too, is left in: it is
    on the keys anyway, trial 37): on a key with room for them all, or
    a new key, rather than split them (one left over would stay behind
    and be swept into the mass); twelve at once fill a new key and the
    rest are fetched on the next look. They then fly to the fleet.
    Returns how many Scouts."""
    def pick(refuse=True):
        n = reselect()
        if n == 0:
            return None
        got = scouts_picked(io, st, n)
        if got is None:
            if refuse:
                io.shot("not-scouts")
                io.log("fleet: what was picked is not all Scouts: not added "
                       "(picture 'not-scouts')")
            return None
        return got[0] - got[1], got[1]

    got = pick()
    if got is None:
        return 0
    n, guns = got
    if n <= 0:
        return 0
    entry = key_with_room(st, min(n, FLEET_SIZE))
    if entry is None:
        if open_fleet_key(io, st):
            got = pick(refuse=False)    # starting the key changed the selection
            if got is None or got[0] <= 0:
                return 0
            n, guns = got
            entry = st.fleet[-1]
        else:
            entry = max(st.fleet, key=lambda e: FLEET_SIZE - e["scouts"],
                        default=None)
    room = FLEET_SIZE - entry["scouts"] if entry else 0
    if room <= 0 and recount_fleet(io, st):
        # trial 33: "every fleet key is full" for the last half of the
        # game, the keys' Scouts long dead; counted again, room is found
        got = pick(refuse=False)
        if got is None or got[0] <= 0:
            return 0
        n, guns = got
        entry = key_with_room(st, min(n, FLEET_SIZE)) or \
            max(st.fleet, key=lambda e: FLEET_SIZE - e["scouts"])
        room = FLEET_SIZE - entry["scouts"]
    if room <= 0:
        # no room on any key: they still fly to the fleet, so they are
        # never swept into the ground mass (plan step 2)
        attack_move(io, *fleet_spot())
        st.last_added_key = "none (no room: sent to the fleet unkeyed)"
        io.log(f"fleet: every fleet key is full: {n} Scouts sent to the "
               f"fleet's spot without a key")
        return n
    whole = n
    if n > room:
        n = trim_selection(io, room + guns, st) - guns
        if n <= 0 or n > room:
            return 0
    add_to_key(io, st, entry)
    entry["scouts"] += n
    st.last_added_key = entry["key"]
    attack_move(io, *fleet_spot())      # off to the fleet, out of the mass
    if whole > n and depth < 2:
        # the rest did not fit: once those added have flown off, the
        # others are picked again and go on the next key with room, or
        # to the fleet unkeyed (before, they stayed by the factory and
        # were swept into the mass)
        io.sleep(MOSCOW_GONE)
        n += add_selected_scouts(io, st, reselect, depth + 1)
    return n


SCOUT_FACTORIES = ["Factory 1", "Factory 2", "Factory 3"]  # Russia's industry:
                               # each makes 2 Scouts (with 2 Heavy Tanks and 2
                               # Veteran Infantry) at every tax, if Russia holds it
TAX_MARK = 180                 # game seconds into a round: the countdown at 2:00
MOSCOW_AIR = (1800, 2800)      # game seconds: 12 Scouts at "ZMoscow Air"
SCOUT_WAIT = 3                 # game seconds after a spawn before looking
SCOUT_HOLD = 30                # game seconds the spawn spots are kept from the mass
SCOUT_LOOKING = 90             # game seconds after a tax the factories are looked at
MOSCOW_GONE = 3                # real seconds for added Scouts to leave the spawn spot


SPAWN_LOOK = 7                 # tiles round a spawn point where new Scouts are looked for


def scouts_on_top(io, st, x, y, every=True):
    """Pick a new Scout at a spawn point by its gold on the screen (not
    the factory's middle, where the Heavy Tanks made with it stand:
    trial 23), checked against the learnt Scout picture. With `every`,
    Ctrl + click on it then picks every Scout on screen, and nothing
    else. Returns how many are selected."""
    p = click_scout(io, st, x, y, reach=SPAWN_LOOK)
    if not p:
        return 0
    if every:
        io.click_with("ctrl", *p)
        io.sleep(0.08)
    return live.selected_count(io.shot("scouts", keep=False))


SCOUT_TRIES = 3                # looks at a spawn point before giving up on it
FACTORY_GROUND = 330           # screen pixels round a factory's middle looked at


def fetch_factory_ground(io, mapdata, st, name):
    """Once a factory's new Scouts are on the keys: the Heavy Tanks and
    soldiers it made at the tax, found on the game screen, are boxed and
    sent to the mass (the Scouts taken out). Trial 37: Factory 3 stands
    among Moscow's buildings, where the minimap hides our units (the
    buildings' own pixels are left out), and its tanks, made in the
    factory's middle, never left; its soldiers walked out of the
    buildings and were seen. Returns how many were sent."""
    f = place(mapdata, name)
    cam = look_at(io, *centred(f["x"], f["y"]), wait=0.25)
    pic = io.shot("factory-ground", keep=False)
    if pic is None:
        return 0
    fx, fy = live.on_screen(f["x"], f["y"], cam)
    pts = [p for p in own_on_screen(pic)
           if (p[0] - fx) ** 2 + (p[1] - fy) ** 2 <= FACTORY_GROUND ** 2]
    if len(pts) < 2:
        return 0
    l, t, r, b = live.GAME_AREA
    box = (max(l + 3, min(p[0] for p in pts) - 40),
           max(t + 3, min(p[1] for p in pts) - 40),
           min(r - 3, max(p[0] for p in pts) + 40),
           min(b - 3, max(p[1] for p in pts) + 40))
    if box[2] - box[0] < 20 or box[3] - box[1] < 20:
        return 0
    io.drag(*box)
    io.sleep(0.08)
    if not live.units_selected(io.card()):
        return 0
    n = drop_scouts(io, st)             # the Scouts are the fleet's
    if n == 0:
        return 0
    to_mass(io, mapdata, (f["x"], f["y"]), st)
    io.log(f"  {n} new ground units at {name} sent to the massing place "
           f"(seen on the screen)")
    return n


def collect_new_scouts(io, watch, mapdata, st):
    """New Scouts go onto the fleet keys, never into the mass: those the
    factories make at every tax, and the two flights of twelve at Moscow.
    The air is fetched first: while it is, the spawn points are kept from
    the idle pickup (scout_spots), so the ground there goes to the mass
    only afterwards. Each spawn point is looked at again on the next
    passes until its Scouts are on the keys, a few times at most.
    Returns how many were added."""
    if st.clock is None or not st.fleet:
        return 0
    g = st.clock.time() * COUNTDOWN_RATE
    added = 0
    k = int((g - TAX_MARK - SCOUT_WAIT) // 300)
    window = k >= 0 and (g - TAX_MARK) % 300 < SCOUT_LOOKING
    for name in SCOUT_FACTORIES if window else []:
        job = (k, name)
        if job in st.scouts_done:
            continue
        f = place(mapdata, name)
        n = add_selected_scouts(io, st, lambda: scouts_on_top(
            io, st, f["x"], f["y"]))
        st.scout_tries[job] = st.scout_tries.get(job, 0) + 1
        if n:
            added += n
            st.scouts_done.add(job)
            io.log(f"fleet: {n} new Scouts from {name} added to key "
                   f"{st.last_added_key}")
        elif st.scout_tries[job] >= SCOUT_TRIES:
            st.scouts_done.add(job)     # none there (not Russia's factory)
        if job in st.scouts_done and job not in st.factory_ground:
            st.factory_ground.add(job)
            fetch_factory_ground(io, mapdata, st, name)
    for t in MOSCOW_AIR:
        if g >= t + SCOUT_WAIT and t not in st.moscow_done:
            m = place(mapdata, "ZMoscow Air")
            got, first = 0, True
            for _ in range(4):          # twelve: a new key, then the rest
                n = add_selected_scouts(io, st, lambda: scouts_on_top(
                    io, st, m["x"], m["y"], every=first))
                got += n
                if n == 0:
                    break
                first = False           # later: only those still there
                io.sleep(MOSCOW_GONE)   # those added fly off first
            if got:
                added += got
                io.log(f"fleet: {got} new Scouts from Moscow added")
            st.moscow_tries[t] = st.moscow_tries.get(t, 0) + 1
            if got or st.moscow_tries[t] >= SCOUT_TRIES:
                st.moscow_done.add(t)
    return added


def scout_spots(io, mapdata, st, pixels):
    """Our pixels at the spots where new Scouts appear, while they are
    being put on the fleet keys: kept out of the mass."""
    if st.clock is None:
        return set()
    g = st.clock.time() * COUNTDOWN_RATE
    out = set()
    k = int((g - TAX_MARK - SCOUT_WAIT) // 300)
    for name in SCOUT_FACTORIES:
        # until this round's Scouts there are on the keys (trial 25:
        # boxes took Scouts in with the tanks and marines made with them)
        if (g - TAX_MARK) % 300 < SCOUT_HOLD or \
                (k >= 0 and (k, name) not in st.scouts_done):
            f = place(mapdata, name)
            out |= near(pixels, (f["x"], f["y"]), 3)
    for t in MOSCOW_AIR:
        if g >= t and t not in st.moscow_done:
            m = place(mapdata, "ZMoscow Air")
            out |= near(pixels, (m["x"], m["y"]), 5)
    return out


PANEL_ONE = (600, 875, 1140, 1045)  # bottom panel for one unit: its picture and name


def _crop(picture, box):
    import numpy as np
    return np.asarray(picture.convert("RGB").crop(box)).astype(int)


def _frame_box(i, n=12):
    return live.frame_box(i, n)


SHAPE_SAME = 0.6               # outlines this alike (shared / joined): the same kind
SHAPE_LEAST = 50               # bright pixels a learnt picture needs to be of use


def _shape(a, trim=8):
    """A unit picture's outline: where it is bright green, yellow or red
    (its colour shows its health, so colour itself is not compared)."""
    if trim:
        a = a[trim:-trim, trim:-trim]
    return a[..., :2].max(axis=2) > 100


def alike(a, b, trim=8):
    """How alike two unit pictures are in outline: 0 to 1."""
    x, y = _shape(a, trim), _shape(b, trim)
    return float((x & y).sum()) / max(1, float((x | y).sum()))


def _apart(things, others):
    """Each of `things` with how far (map pixels) it stands from the
    nearest of `others`."""
    return [(min((((t["x"] - o["x"]) ** 2 + (t["y"] - o["y"]) ** 2) ** 0.5
                  for o in others), default=1e9), t) for t in things]


def learn_scout(io, st, mapdata):
    """Learn what a Scout and a Battlecruiser look like in the bottom
    panel, from Russia's own starting air: a Scout far from every
    Battlecruiser (alone: its picture and name; with Ctrl + click, its
    small framed picture in a group), and a Battlecruiser far from every
    Scout. A unit is put on a fleet key only if it looks like the Scout
    and not like the Battlecruiser (trial 23: a Battlecruiser standing
    next to a Scout was picked and put on the key)."""
    air = mapdata["slots"][SLOT]["air"]
    scouts = [a for a in air if a["type"] == "Scout"]
    ships = [a for a in air if a["type"] == "Battlecruiser"]
    if not scouts:
        return False
    _, scout = max(_apart(scouts, ships), key=lambda d: d[0])
    p = click_unit(io, scout["x"], scout["y"])
    if not p:
        return False
    st.scout_one = _crop(io.shot("scout-one", keep=False), PANEL_ONE)
    if _shape(st.scout_one, trim=0).sum() < SHAPE_LEAST:
        st.scout_one = None             # nothing to see there: cannot tell
    io.click_with("ctrl", *p)            # every Scout on screen
    io.sleep(0.08)
    pic = io.shot("scout-group", keep=False)
    n = live.selected_count(pic)
    if n >= 2:
        st.scout_frame = _crop(pic, _frame_box(0, n))
        if _shape(st.scout_frame).sum() < SHAPE_LEAST:
            st.scout_frame = None
    if ships:
        import numpy as np
        _, ship = max(_apart(ships, scouts), key=lambda d: d[0])
        if click_unit(io, ship["x"], ship["y"]):
            one = _crop(io.shot("ship-one", keep=False), PANEL_ONE)
            if st.scout_one is not None and \
                    _shape(one, trim=0).sum() >= SHAPE_LEAST and \
                    alike(one, st.scout_one, trim=0) < SHAPE_SAME:
                st.ship_one = one       # not the Scout again: a Battlecruiser
    io.log("fleet: learnt what a Scout looks like"
           + ("" if st.scout_frame is not None else " (alone only)")
           + (", and a Battlecruiser" if st.ship_one is not None else ""))
    return True


def picked_are_scouts(io, st, n):
    """True if every unit selected looks like the Scouts learnt at the
    start: the panel picture for one unit (and nearer the Scout than the
    Battlecruiser), each framed picture for several. Anything else (a
    Battlecruiser, a tank or infantry picked by mistake) is not added
    to the fleet."""
    pic = io.shot("check", keep=False)
    if n <= 1:
        if st.scout_one is None:
            return True                 # nothing learnt: cannot tell
        one = _crop(pic, PANEL_ONE)
        d = alike(one, st.scout_one, trim=0)
        if st.ship_one is not None and alike(one, st.ship_one, trim=0) >= d:
            return False                # a Battlecruiser
        return d >= SHAPE_SAME
    if st.scout_frame is None:
        return True
    for i in range(min(n, 12)):
        # (the pictures are laid out by how many there are: trials 24
        # and 25 looked in the wrong places and refused real Scouts)
        if alike(_crop(pic, _frame_box(i, n)), st.scout_frame) < SHAPE_SAME:
            return False
    return True


def frame_kinds(st, pic, n):
    """What each unit picture in the bottom panel shows: "scout", "gun"
    (the Moscow Heavy Artillery, once its picture is learnt) or "other".
    None when it cannot be told (the Scout not learnt, one unit)."""
    if st is None or st.scout_frame is None or pic is None or n < 2:
        return None
    out = []
    for i in range(min(n, 12)):
        c = _crop(pic, _frame_box(i, n))
        if alike(c, st.scout_frame) >= SHAPE_SAME:
            out.append("scout")
        elif st.ha_frame is not None and alike(c, st.ha_frame) >= SHAPE_SAME:
            out.append("gun")
        else:
            out.append("other")
    return out


def learn_ha_frame(io, st, e, pic, n):
    """A pressed fleet key that holds the gun and Scouts: its one picture
    that is not a Scout is the gun's. Learnt once, so the gun is never
    taken out of a selection (trial 37)."""
    if st.ha_frame is not None or e.get("ha_dead") or \
            e["key"] not in st.ha_keys:
        return
    kinds = frame_kinds(st, pic, n)
    if kinds is None:
        return
    others = [i for i, k in enumerate(kinds) if k != "scout"]
    if len(others) == 1:
        st.ha_frame = _crop(pic, _frame_box(others[0], n))
        io.log(f"fleet: learnt what the Heavy Artillery looks like (key "
               f"{e['key']})")


def scouts_picked(io, st, n, guns=0):
    """What a pick for the fleet holds: (units, guns among them), or None
    if it is not for the fleet. Scouts, and at most `guns` Heavy
    Artillery, are kept: ground units picked with them are taken out
    (Shift + click on their pictures, trial 37), never the artillery.
    Before the artillery's picture is learnt, one picture that is not a
    Scout is taken as the gun when one is expected (a fleet key
    pressed), and anything else makes the pick refused."""
    if picked_are_scouts(io, st, n):
        return n, 0
    pic = io.shot("check", keep=False)
    for _ in range(12):
        kinds = frame_kinds(st, pic, n)
        if kinds is None:
            return None
        others = [i for i, k in enumerate(kinds) if k == "other"]
        gun = [i for i, k in enumerate(kinds) if k == "gun"]
        if st.ha_frame is None:
            if guns and len(others) == 1:
                return n, 1             # the key's own gun
            return None                 # cannot tell the gun: refused
        if not others:
            if len(gun) > max(1, guns):
                return None
            return n, len(gun)
        x0, y0, x1, y1 = _frame_box(others[-1], n)
        io.click_with("shift", (x0 + x1) // 2, (y0 + y1) // 2)
        pic = panel_changed(io, n, "check")
        n = live.selected_count(pic)
        if n == 0:
            return None
    return None


def drop_scouts(io, st, pic=None):
    """Take any Scouts out of what a box selected (Shift + click on their
    small pictures), so they are never sent off with the ground army
    (trial 26: boxes at the mass took the fleet into the hits). Returns
    how many units are left selected."""
    if pic is None:
        pic = io.shot("box-check", keep=False)
    n = live.selected_count(pic)
    if st.scout_frame is None or n == 0:
        return n
    if n == 1:
        # one alone: its big picture; a Scout alone is not a ground unit
        if st.scout_one is not None and \
                alike(_crop(pic, PANEL_ONE), st.scout_one, trim=0) >= SHAPE_SAME:
            io.key("esc")
            return 0
        return 1
    for _ in range(12):
        scouts = [i for i in range(min(n, 12))
                  if alike(_crop(pic, _frame_box(i, n)), st.scout_frame)
                  >= SHAPE_SAME]
        if not scouts:
            break
        if len(scouts) == n:
            return 0                    # all air: nothing to send
        x0, y0, x1, y1 = _frame_box(scouts[-1], n)
        io.click_with("shift", (x0 + x1) // 2, (y0 + y1) // 2)
        io.sleep(0.06)
        pic = io.shot("box-check", keep=False)
        n = live.selected_count(pic)
    return n


SCOUT_LOOK = 4                 # tiles round a point where a Scout is looked for


def click_scout(io, st, x, y, reach=SCOUT_LOOK):
    """Click a Scout at or near a map point and check that what was
    picked is a Scout: first on the gold patches the screen shows near
    the point (a Scout is gold), then on the spots round it. Returns
    the screen point that picked a Scout, or None."""
    l, t, r, b = live.GAME_AREA
    cam = look_at(io, x, y, wait=0.15)
    px, py = live.on_screen(x, y, cam)
    gold = gold_on_screen(io.shot("gold", keep=False), px, py,
                          reach * 32 * live.ZOOM)
    spots = [(int(gx), int(gy)) for gx, gy in gold[:6]] + \
        [(px + dx, py + dy) for dx, dy in TRIES]
    for sx, sy in spots:
        if not (l + 5 < sx < r - 5 and t + 5 < sy < b - 5):
            continue
        io.click(sx, sy)
        io.sleep(0.08)
        if live.units_selected(io.card()) and picked_are_scouts(io, st, 1):
            return (sx, sy)
    return None


def build_fleet(io, mapdata, st):
    """At the start: every Scout on the fleet keys, with a Heavy
    Artillery on each key. The Battlecruisers are not in it."""
    scouts = [a for a in mapdata["slots"][SLOT]["air"] if a["type"] == "Scout"]
    scouts.sort(key=lambda a: (a["x"] - MASS[0]) ** 2 + (a["y"] - MASS[1]) ** 2)
    if scouts:
        learn_scout(io, st, mapdata)
    added = sum(add_to_fleet(io, st, a["x"], a["y"]) for a in scouts)
    guns = sum(1 for e in st.fleet if not e.get("ha_dead"))
    io.log(f"fleet: {added} Scouts and {guns} Heavy Artillery on "
           f"key {' '.join(st.air_keys) or 'none'}")
    return added


def battleship_groups(mapdata):
    """The Battlecruisers, in groups of those standing together. They go
    with the ground army, not with the fleet."""
    ships = [a for a in mapdata["slots"][SLOT]["air"]
             if a["type"] == "Battlecruiser"]
    groups = []
    for a in ships:
        for g in groups:
            if abs(g[0]["x"] - a["x"]) < 12 * 32 and \
                    abs(g[0]["y"] - a["y"]) < 8 * 32:
                g.append(a)
                break
        else:
            groups.append([a])
    return groups


RUSH_ODDS = 2 / 15             # games whose first hit is the first-minute one
                               # (the owner: about 2 games in 15)


def first_orders(io, watch, mapdata, st, t0, rush=None):
    """Order the starting army to the massing place: the Battlecruisers
    with it, the ground groups biggest first, on 1 to 8. (The fleet was
    put on its keys before; it is ordered once the Middle East scouts
    have arrived.) With `rush` (a target): the first-minute variant, as
    the best player in the replays often opens: every starting group goes
    straight at the target instead (130 to 190 units were sent forward in
    their first minute)."""
    orders = 0
    air_px = set(live.to_drawn(a["x"], a["y"])
                 for a in mapdata["slots"][SLOT]["air"])
    for group in battleship_groups(mapdata):
        pixels = [live.to_drawn(a["x"], a["y"]) for a in group]
        if select_group(io, pixels, st):
            if rush:
                send_at(io, mapdata, st, rush)
            else:
                attack_move(io, *MASS)   # with the ground army
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
        if io.now() - t0 >= OPENING_ANNOUNCE and not rush:
            # the first hit is announced on time; it goes 30 s later
            team_gate(io, watch, mapdata, st, True,
                      st.opening_target or TARGETS[0])
        if not select_group(io, group, st, watch):
            continue
        if rush:
            send_at(io, mapdata, st, rush)
        else:
            attack_move(io, *MASS)
        orders += 1
        free = free_ground_keys(st)
        if len(st.ground_keys) < len(free):
            key = free[len(st.ground_keys)]
            io.combo("ctrl", key)
            io.sleep(0.04)
            st.ground_keys.append(key)
    io.log(f"starting army: {orders} groups ordered to "
           f"{'the front at ' + rush if rush else 'the massing place'}; "
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
        relocate_mass(io, watch, mapdata, st)
        follow_ally_air(io, watch, mapdata, st)
        air_upkeep(io, watch, mapdata, st)
        if not collected:
            collected = collect_middle_east(io, watch, st) > 0
        if not st.fleet_moved and now >= FLEET_MOVE_AFTER:
            st.fleet_moved = True       # the Middle East scouts are there
            set_air_state(io, st, "parked", "to its spot by the mass",
                          target=fleet_spot())
            for key in st.air_keys:
                io.key(key)
                io.sleep(0.04)
                attack_move(io, *fleet_spot())
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
    # east is always Berlin itself (the repository owner, trial 37), even
    # after a hit stalled at Warsaw or Krakow; an ally who wants a city on
    # the way names it ("@R hit Warsaw")
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


def front_to_back(items, target_xy, where):
    """The nearest the target first: where the way is narrow (the
    Odessa-Romania choke), the head of the column must move before the
    rest can (the repository owner, trial 24)."""
    return list(reversed(back_to_front(items, target_xy, where)))


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
        pic = io.shot("box", keep=False)
        n = live.selected_count(pic)
        if n == 0 and live.building_selected(io.card()):
            # a building, not troops: the next box smaller (trial 25:
            # depots and command centres picked up)
            st.box_px = max(2, int(take * 0.6))
            break
        if n and st.scout_frame is not None:
            n = drop_scouts(io, st, pic)        # (the same picture: no new look)
            if n == 0:
                break
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


# Russia's units on the game screen (the repository owner: the boxes of a
# hit are planned on the game screen, never on the minimap): the rusty
# brown of their shoulder pads and trim, about one patch a man. Our
# factories' stripes match too; a box over a building takes only units.
OWN_LEAST = 3                  # pixels of Russia's brown that make a patch
CHAT_BAND = (0, 470, 720, 700) # screen box where chat lines show (left out)


def own_mask(picture):
    import numpy as np
    l, t, r, b = live.GAME_AREA
    a = np.asarray(picture.convert("RGB").crop((l, t, r, b))).astype(int)
    R, G, B = a[..., 0], a[..., 1], a[..., 2]
    m = (R > 85) & (R < 150) & (R - G > 40) & (G > 30) & (G < 75) & \
        (B < 45) & (G - B > 10)
    m[:240, :400] = False               # the kills list
    x0, y0, x1, y1 = CHAT_BAND
    m[y0 - t:y1 - t, x0 - l:x1 - l] = False
    return m


def own_on_screen(picture):
    """Our units on the game screen: their screen points (one a man,
    roughly)."""
    if picture is None:
        return []
    return [(x, y) for n, x, y in patches(own_mask(picture)) if n >= OWN_LEAST]


def plan_screen_boxes(points, toward_target, per_box):
    """Every box of the view, planned on the game screen before any is
    drawn: from the back (the far side from the target) forward, each box
    round the `per_box` men nearest its starting man, and every man inside
    it counted as taken, so no two boxes cover the same men. Screen boxes
    (x0, y0, x1, y1), with the men each holds."""
    tx, ty = toward_target
    left = sorted(points, key=lambda p: p[0] * tx + p[1] * ty)   # back first
    l, t, r, b = live.GAME_AREA
    taken, plan = [], []

    def box_of(group, pad):
        return (max(l + 3, min(p[0] for p in group) - pad),
                max(t + 3, min(p[1] for p in group) - pad),
                min(r - 3, max(p[0] for p in group) + pad),
                min(b - 3, max(p[1] for p in group) + pad))

    def holds(box, p):
        return box[0] <= p[0] <= box[2] and box[1] <= p[1] <= box[3]
    while left:
        seed = left[0]
        near_ = sorted(left, key=lambda p: (p[0] - seed[0]) ** 2
                       + (p[1] - seed[1]) ** 2)[:max(1, per_box)]
        box = None
        # as many of the nearest as fit without covering a man an earlier
        # box took (he is still standing there: he would be boxed again)
        for pad in (SCREEN_PAD, 10):
            for k in range(len(near_), 0, -1):
                trial_box = box_of(near_[:k], pad)
                if not any(holds(trial_box, p) for p in taken):
                    box = trial_box
                    break
            if box is not None:
                break
        if box is None:
            box = box_of([seed], 4)
        inside = [p for p in left if holds(box, p)] or [seed]
        plan.append((box, len(inside)))
        taken += inside
        left = [p for p in left if p not in inside]
    return plan


SCREEN_PAD = 28                # screen pixels round the men a box is drawn


CHECK_EVERY = 4                # in a hit, every fourth box is looked at (and the
                               # first of each view): what it took sizes the next
VIEW_LEAST = 8                 # men in a view, in a hit's later passes: fewer
                               # are left for the next hit


def sweep_screen(io, watch, mapdata, st, target, w, cam, dest, max_boxes,
                 boxes, least=0):
    """One view of a hit, the boxes planned on the game screen (the
    repository owner): our men are found on the screen, every box mapped
    out round them, back to front, before any is drawn; then each is drawn,
    what it took read, and sent. Box sizes follow what the boxes took.
    Men left behind by a full box are taken by the hit's next sweep.
    Returns (orders, boxes drawn so far)."""
    orders = 0
    mx, my = live.on_screen(*MASS, cam)
    tx, ty = live.on_screen(w["x"], w["y"], cam)
    toward_target = (tx - mx, ty - my)
    # only men standing still: two looks a moment apart (those already
    # sent are walking off and are not boxed again)
    first = own_on_screen(io.shot("hit-view", keep=False))
    io.sleep(STILL_GAP)
    second = own_on_screen(io.shot("hit-view", keep=False))
    points = [p for p in second if any(abs(p[0] - q[0]) <= STILL_PX and
                                       abs(p[1] - q[1]) <= STILL_PX for q in first)]
    if not points or len(points) < least:
        return orders, boxes
    per_box = st.screen_per_box
    plan = plan_screen_boxes(points, toward_target, per_box)
    io.log(f"  hit: {len(plan)} boxes planned on the screen for "
           f"{len(points)} men in view")
    # Speed (the owner, after trial 40: what counts in a hit is how fast
    # the units are boxed and sent). A box cost about 0.55 s, of which the
    # look at what it took (a whole screenshot, to count it) was 0.15 s
    # and more: now only the first box of a view and every fourth are
    # counted; for the others the small look at the buttons says whether
    # anyone was taken. Scouts a box catches go with it (taking them out
    # cost up to 6 s a hit); the fleet's own order calls them back.
    have = False
    for k, (box, men) in enumerate(plan):
        if max_boxes is not None and boxes >= max_boxes:
            break
        boxes += 1
        io.drag(*box)
        io.sleep(0.03)
        st.boxes += 1
        if k % CHECK_EVERY == 0 or not have:
            # (also every box until one of this view has taken someone:
            # before that, what is selected is whatever was before, the
            # fleet perhaps, and must not get the ground's order)
            n = live.selected_count(io.shot("box", keep=False))
            st.selected += n
            st.selections += 1
            if n == 0:
                st.empty += 1
                continue
            have = True
        elif not live.units_selected(io.card()):
            st.empty += 1               # (the small look at the buttons:
            continue                    # quick, and enough to tell nobody)
            # the next boxes are sized from what this one took
            if n >= FULL:
                st.screen_per_box = max(6, st.screen_per_box - 1)
            elif n < GOOD_BOX and men:
                st.screen_per_box = min(24, st.screen_per_box + 2)
        if dest is not None:
            attack_move(io, *dest)
        else:
            send_at(io, mapdata, st, target)
            free = free_ground_keys(st)
            if st.rekey < len(free):
                io.combo("ctrl", free[st.rekey])
                io.sleep(0.04)
                st.rekey += 1
        orders += 1
    return orders, boxes


STILL_GAP = 0.3                # seconds between the two looks at a view
STILL_PX = 5                   # screen pixels a standing man may seem to move


def sweep_mass(io, watch, mapdata, st, target, centre=None, dest=None,
               radius=MASS_RADIUS, least=12, max_boxes=None, front_first=False,
               steer=True, skip=(), settle=1.2, plan_first=False,
               view_least=0):
    """One pass over the massing place (or the ground round `centre`):
    every part of it where the minimap shows units standing still is
    boxed, back to front, each box drawn to hold as near to twelve units
    as it can, and sent at the target (or moved to `dest`). Returns
    (orders given, pixels found)."""
    if dest is not None:
        w = {"x": dest[0], "y": dest[1]}
    else:
        w = place(mapdata, target)
    a = watch.units(io.shot("sweep"))
    io.sleep(settle)                    # only those still standing there
    area = near(a, centre, radius) if centre else at_mass(a)
    there = area & watch.units(io.shot("watch", keep=False))
    if len(there) < least:
        return 0, len(there)
    orders = 0
    # the mass is often wider than one view: take it a view at a time
    order = front_to_back if front_first else back_to_front
    views = order(live.clusters(there, 20, 8), (w["x"], w["y"]),
                  lambda g: live.from_drawn(*g[0]))
    boxes = 0
    for view in views:
        if max_boxes is not None and boxes >= max_boxes:
            break
        cols = [p[0] for p in view]
        rows = [p[1] for p in view]
        cx, cy = live.from_drawn((min(cols) + max(cols)) / 2,
                                 (min(rows) + max(rows)) / 2)
        if steer:
            fleet_tick(io, watch, mapdata, st)   # the air is looked after meanwhile
        cam = look_at(io, *centred(cx, cy))
        if plan_first:
            # a hit: the boxes planned on the game screen (the repository
            # owner; the old minimap way is in docs/archive/old_hit_boxes.py)
            o, b = sweep_screen(io, watch, mapdata, st, target, w, cam, dest,
                                max_boxes, boxes, least=view_least)
            orders += o
            boxes = b
            continue
        left, later, rounds = set(view), set(), 0
        while left or later:
            if not left:
                # what full boxes left behind, once the rest of the view
                # is done (trial 34: boxed again at once, the same men,
                # who had not yet walked off)
                rounds += 1
                if rounds > 1:
                    break
                io.sleep(0.3)
                left, later = later, set()
            if max_boxes is not None and boxes >= max_boxes:
                break
            boxes += 1
            # the troops farthest from the target go first (or, for a
            # quick tail, the nearest)
            seed = order(list(left), (w["x"], w["y"]),
                         lambda p: live.from_drawn(*p))[0]
            boxed, n = select_full(io, st, seed, left, cam)
            if n >= FULL and len(boxed) > 1:
                # a full box: more may stand there than were picked, so
                # the far half of it is boxed again (trial 21: a third
                # of every hit was left at the massing place), but only
                # after the rest of the view
                half = max(1, len(boxed) // 2)
                left -= set(boxed)
                later |= set(boxed[half:])
            else:
                left -= set(boxed) or {seed}
                later -= set(boxed)
            if n == 0:
                watch.forget(boxed)
                continue
            if dest is not None:
                attack_move(io, *dest)
                orders += 1
                continue
            send_at(io, mapdata, st, target)
            orders += 1
            free = free_ground_keys(st)
            if st.rekey < len(free):
                # the newest groups take over the number keys, so
                # they can be recalled and given orders
                io.combo("ctrl", free[st.rekey])
                io.sleep(0.04)
                st.rekey += 1
    return orders, len(there)


# The keys version (StarcraftTrialKeys), the repository owner's way:
# while massing, a dozen at a time from the left of the mass goes on the
# next key (1 to 7) and is moved aside into its place in a line across
# the way to the target. At the hit, the back of the mass is boxed and
# sent first; while it sets off every key attacks, keeping its place in
# the line; then the rest is boxed, back to front. The usual version
# boxes the whole mass.
HIT_STYLE = "boxes"            # "back7" in the back first version (the line
                               # ahead version, but seven groups from the back
                               # of the mass go before the keys);
                               # "keys" in the line ahead version
                               # (StarcraftTrialLineAhead), "rel" in the line
                               # beside version (StarcraftTrialLineBeside;
                               # the line placed by where the mass stands
                               # from the target)


def keys_style():
    return HIT_STYLE in ("keys", "rel", "back7")
MASS_KEYS = list("1234567")     # the mass is put on these before a hit
KEY_FRESH = 600                # seconds: keys older than this are not used
KEYED_ROOM = 3                 # minimap pixels round a keyed group's place
REINFORCE_FOR = 60             # seconds after a hit when new troops go straight
                               # to its front, not to the mass (keys version)
SPREAD_BOXES = 6               # boxes spread out over the massing place a round
SPREAD_GAP = 2                 # minimap pixels round a box left alone after it
SPREAD_WIDE = [(dx, dy) for dy in (-4, 4, -12, 12) for dx in (-4, 4, -12, 12)]
                               # the usual version (the repository owner): 8
                               # tiles apart over an area 24 tiles across


def reinforce_target(io, st):
    """The line versions: the target new troops walk straight to, for a
    minute after a hit that is not being lost; None: to the mass."""
    b = st.battle
    if not keys_style() or b is None or \
            io.now() - b.sent_at >= REINFORCE_FOR or \
            b.verdict()[0] == "losing":
        return None
    return b.target


def spread_at_mass(io, watch, mapdata, st):
    """Between rounds of marines, the crowd at the
    massing place is boxed from its thickest part and walked out over a
    wide area round the mass point (the repository owner), so it does
    not stand in one clump. Returns the boxes moved."""
    if busy(st) or keys_style():
        return 0                        # (the keys version spreads as it keys)
    spots = SPREAD_WIDE
    a = watch.units(io.shot("watch", keep=False))
    io.sleep(1.0)
    there = at_mass(a) & watch.units(io.shot("watch", keep=False))
    if len(there) < 12:
        return 0
    moved = 0
    left = set(there)
    while left and moved < SPREAD_BOXES:
        # the thickest part first: the pixel with the most neighbours
        seed = max(left, key=lambda p: sum((p[0] + i, p[1] + j) in left
                                           for i in (-2, -1, 0, 1, 2)
                                           for j in (-2, -1, 0, 1, 2)))
        cam = look_at(io, *centred(*live.from_drawn(*seed)))
        boxed, n = select_full(io, st, seed, left, cam)
        # the ground just boxed is done: its men were just sent off but
        # have not left yet, and the thickest part is still there (trial
        # 34: six boxes in a row on the same marines)
        done = set(boxed) or {seed}
        left = {p for p in left if all(abs(p[0] - q[0]) > SPREAD_GAP or
                                       abs(p[1] - q[1]) > SPREAD_GAP
                                       for q in done)}
        if n == 0:
            continue
        dx, dy = spots[st.spread_next % len(spots)]
        st.spread_next += 1
        io.click(*live.minimap_point(MASS[0] + dx * 32, MASS[1] + dy * 32),
                 button="right")         # a plain move: out over the ground
        io.sleep(0.04)
        moved += 1
    if moved:
        io.log(f"  the mass spread out: {moved} groups walked apart")
    return moved


def mass_keys(st):
    return [k for k in MASS_KEYS if k not in st.air_keys]


SPREAD_AHEAD = 7               # tiles ahead of the mass where the line forms
SPREAD_GAP = 4                 # tiles between the keys along the line


def line_offsets(n, mass, target):
    """Map-pixel offsets of n groups along a line across the way from
    the mass to the target (left to right), SPREAD_GAP tiles apart."""
    dx, dy = target[0] - mass[0], target[1] - mass[1]
    d = (dx * dx + dy * dy) ** 0.5 or 1.0
    px, py = -dy / d, dx / d            # across the way
    return [((k - (n - 1) / 2) * SPREAD_GAP * 32 * px,
             (k - (n - 1) / 2) * SPREAD_GAP * 32 * py) for k in range(n)]


KEY_EVERY = 6                  # seconds between keying steps while massing
KEY_LEAST = 6                  # men a box must hold to be put on a key
BACK_BOXES = 3                 # boxes from the back before the keys go
BACK_FORMATIONS = 7            # the back first version (StarcraftTrialBackFirst,
                               # the repository owner): seven groups formed
                               # and sent from the back before the keys


REL_SIDE = 8                   # tiles from the mass to its line (rel version)
REL_LEVEL = 8                  # tiles of height within which the mass is level
                               # with the target ("the middle")


def rel_side(mass, target):
    """Which side of the mass the line forms on (the repository owner,
    the rel version): the mass to the top right of the target, on its
    left; to the bottom right, on its right; level with it, both."""
    dy = (mass[1] - target[1]) / 32     # tiles; the map's y grows downward
    if abs(dy) <= REL_LEVEL:
        return "both"
    return "left" if dy < 0 else "right"


def rel_spot(k, n, mass, target):
    """The k-th of n keyed groups' place (map pixels), rel version: an
    up-and-down line REL_SIDE tiles left or right of the mass, 4 tiles
    between groups; level with the target, half on each side."""
    side = rel_side(mass, target)
    if side == "both":
        half = k % 2                    # left, right, left, right ...
        x = mass[0] + (-1 if half == 0 else 1) * REL_SIDE * 32
        row, rows = k // 2, (n + 1 - half) // 2
    else:
        x = mass[0] + (-1 if side == "left" else 1) * REL_SIDE * 32
        row, rows = k, n
    y = mass[1] + (row - (rows - 1) / 2) * SPREAD_GAP * 32
    return x, y


def key_step(io, watch, mapdata, st, target):
    """The keys version, while massing (the repository owner's way):
    take the next dozen from the left of the mass, put them on the next
    key, and move them aside into their place in a line across the way
    to the target, so the mass is spread out and keyed before the hit.
    One key a step; returns True if one was set."""
    keys = mass_keys(st)
    if len(st.keyed) >= len(keys) or io.now() - st.last_key_step < KEY_EVERY:
        return False
    st.last_key_step = io.now()
    a = watch.units(io.shot("watch", keep=False))
    io.sleep(1.0)
    there = at_mass(a) & watch.units(io.shot("watch", keep=False))
    for _, spot in st.keyed:            # those keyed stand in the line
        there -= near(there, spot, KEYED_ROOM)
    if len(there) < 8:
        return False
    seed = min(there, key=lambda p: (p[0], p[1]))   # from the left
    cam = look_at(io, *centred(*live.from_drawn(*seed)))
    boxed, n = select_full(io, st, seed, there, cam)
    if n < KEY_LEAST:
        return False
    key = keys[len(st.keyed)]
    io.combo("ctrl", key)
    io.sleep(0.04)
    if key not in st.ground_keys:
        st.ground_keys.append(key)
    w = place(mapdata, target)
    if HIT_STYLE == "rel":
        spot = rel_spot(len(st.keyed), len(keys), MASS, (w["x"], w["y"]))
    else:
        centre = toward(MASS, (w["x"], w["y"]), SPREAD_AHEAD)
        ox, oy = line_offsets(len(keys), MASS, (w["x"], w["y"]))[len(st.keyed)]
        spot = (centre[0] + ox, centre[1] + oy)
    io.click(*live.minimap_point(*spot), button="right")   # aside, into line
    io.sleep(0.04)
    st.keyed.append((key, spot))
    st.mass_keyed = (io.now(), [k for k, _ in st.keyed], target)
    io.log(f"  key {key}: {n} men put on it and moved aside into the line")
    return True


def keyed_attack(io, mapdata, st, target, keys):
    """Each key attacks, keeping its place in the line: its own point
    across the target's front."""
    w = place(mapdata, target)
    offsets = line_offsets(len(keys), MASS, (w["x"], w["y"]))
    for key, (ox, oy) in zip(keys, offsets):
        x, y = front_point(mapdata, st, target)
        io.key(key)
        io.sleep(0.035)
        send_at(io, mapdata, st, target, (x + ox, y + oy))
    return len(keys)


def send_fleet_with_hit(io, mapdata, st, target):
    """The fleet goes with the hit at once, as one stack, to a point
    just ahead of the mass over the army's back; from there it is kept
    over the army."""
    w = place(mapdata, target)
    over = toward(MASS, (w["x"], w["y"]), AIR_LEAD)
    orders = 0
    if own_fleet_keys(st):
        set_air_state(io, st, "with the hit", target, target=over)
    for key in own_fleet_keys(st):
        io.key(key)
        io.sleep(0.035)
        attack_move(io, *over)
        orders += 1
    st.air_moved = io.now()
    st.air_home = False
    st.fleet_spot = over
    return orders


TAIL_SHARE = 0.2               # a pass that sent fewer than this share of the
                               # first pass's boxes is the last
HIT_SETTLE_LOOK = 0.6          # seconds between the two looks of a sweep at a hit


def hit(io, watch, mapdata, st, target, use_keys=True, sweeps=HIT_SWEEPS):
    """Send the mass at the target as a wall, the fleet with it. In the
    keys version the keyed line goes first."""
    orders = 0
    t_hit = io.now()
    regroup_fleet(io, st)               # every Scout parked on a key first
    a = pic = None
    if watch is not None:
        a = watch.units(io.shot("watch", keep=False))
        io.sleep(1.0)
        pic = io.shot("watch", keep=False)
        # men of earlier hits idle in the Balkans go on first (trial 38)
        orders += sweep_balkans(io, watch, mapdata, st, a & watch.units(pic),
                                pic, force=True)
    if team_rules.front_of(target) == "balks" and watch is not None:
        # the last hit's troops still in the choke go on first, so the
        # new hit does not pile up behind them
        orders += clear_choke(io, watch, mapdata, st, a & watch.units(pic),
                              pic, force=True)
    keyed = st.mass_keyed if keys_style() and st.mass_keyed and \
        st.mass_keyed[1] and io.now() - st.mass_keyed[0] < KEY_FRESH else None
    spots = [spot for _, spot in st.keyed]
    st.mass_keyed, st.keyed = None, []
    if keyed:
        # the keys version (the repository owner's way): the back of
        # the mass is boxed first, and while it sets off every key
        # attacks; then the rest is boxed, back to front
        skip = set()
        a = watch.units(io.shot("watch", keep=False))
        for spot in spots:
            skip |= near(a, spot, KEYED_ROOM)
        n, _ = sweep_mass(io, watch, mapdata, st, target,
                          max_boxes=BACK_FORMATIONS if HIT_STYLE == "back7"
                          else BACK_BOXES, steer=False, skip=skip)
        orders += n
        orders += keyed_attack(io, mapdata, st, target, keyed[1])
    elif use_keys:
        for key in st.ground_keys:      # all the key groups in a few seconds
            io.key(key)
            io.sleep(0.035)
            send_at(io, mapdata, st, target)
            orders += 1
    st.battle = Battle(target, io.now())
    if use_keys or keyed:
        io.sleep(0.5)                   # let them step off
    st.rekey = len(free_ground_keys(st)) if (use_keys or keyed) else 0
    # the rest of the mass, back to front, as fast as it goes: no air
    # steering in between, no fetching of far bodies (they come on as
    # reinforcements, straight to the hit), short pauses
    start = None
    fleet_sent = False
    first_n = None
    for sweep in range(sweeps):
        # (the later passes: only views with a body of men left; a few
        # stragglers wait for the next hit. Trial 40: after the fleet was
        # sent, 18 to 24 s went on views of 1 to 18 men)
        n, found = sweep_mass(io, watch, mapdata, st, target, steer=False,
                              settle=HIT_SETTLE_LOOK, plan_first=True,
                              view_least=VIEW_LEAST if sweep else 0)
        orders += n
        start = start or max(found, 1)
        if first_n is None:
            first_n = n
        elif n < TAIL_SHARE * first_n:
            if not fleet_sent and n:
                orders += send_fleet_with_hit(io, mapdata, st, target)
                fleet_sent = True
            break                       # the tail: enough
        if not fleet_sent and n:
            # the first pass has sent most of the mass: the fleet goes
            # now, not after the tail (trial 35: 38 s later), as one
            # stack over the army's back (the repository owner)
            orders += send_fleet_with_hit(io, mapdata, st, target)
            fleet_sent = True
        if n == 0 or found < 0.1 * start:
            break
        io.sleep(0.4)
    if not fleet_sent:
        orders += send_fleet_with_hit(io, mapdata, st, target)
    io.log(f"hit: the ground and the fleet sent in {io.now() - t_hit:.0f} s "
           f"({orders} groups)")
    st.air_waits_serbia = False
    if DOGFIGHT and own_fleet_keys(st) and \
            team_rules.front_of(target) == "balks":
        # a Balkan hit (the owner, trial 41): no air work until the army
        # has reached Romania and been sent on into Serbia (the minute of
        # dogfight came first, and the army stood at Romania meanwhile)
        st.air_waits_serbia = True
        io.log("air: a Balkan hit: no dogfight until the army has been sent "
               "on into Serbia")
    elif DOGFIGHT and own_fleet_keys(st):
        # most of the hit is out: now only the air (the repository owner)
        dogfight(io, watch, mapdata, st, target)
    st.hit_sent = io.now()
    st.hits_sent += 1
    st.go_pending = False
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
            send_at(io, mapdata, st, target)
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


LIFT_BUTTON = (1862, 1022)     # screen: the bottom-right command button
LIFT_TRIES = 2                 # failed lifts of one building before giving it up


BUILDING_SPOTS = [(0, 40), (-50, 30), (50, 30), (0, 70), (-80, 55),
                  (80, 55), (0, 0)]  # screen pixels from a building's middle:
                               # its lower half first, where air hovering over
                               # it does not cover it (trial 26: Scouts were
                               # clicked instead of the Airport)


def pick_building(io, b):
    """Click a building until the game shows a building selected."""
    l, t, r, btm = live.GAME_AREA
    cam = look_at(io, b["x"], b["y"], wait=0.25)
    px, py = live.on_screen(b["x"], b["y"], cam)
    for dx, dy in BUILDING_SPOTS:
        x, y = px + dx, py + dy
        if not (l + 5 < x < r - 5 and t + 5 < y < btm - 5):
            continue
        io.click(x, y)
        io.sleep(0.12)
        if live.building_selected(io.card()):
            return True
    return False


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
    if not pick_building(io, b):
        io.log(f"flight: the {kind} was not found")
        return False
    # Lift Off: the button at the bottom right of the command card (the
    # "L" key alone did nothing in trials 24 and 25). A building in the
    # air shows Move as its first button, as units do: that is the check.
    lifted = False
    for attempt in range(2):
        if not live.building_selected(io.card()) and not pick_building(io, b):
            break                       # something else got picked
        io.click(*LIFT_BUTTON)
        io.sleep(0.1)
        if attempt:
            io.key("l")
        io.sleep(2.6)                   # it takes a moment to leave the ground
        if live.units_selected(io.card()):
            lifted = True
            break
    if not lifted:
        st.lift_fails[tile] = st.lift_fails.get(tile, 0) + 1
        io.shot("lift-failed")
        io.log(f"flight: the {kind} did not lift off (picture 'lift-failed')")
        return False
    city = place(mapdata, city_name)
    land = TAX_LAND.get(city_name)
    if land:
        # land it at its spot by the city (the repository owner, from a
        # replay: a building landed by Krakow), with the Land
        # button and a click on the ground there
        lx, ly = land[0] * 32 + 64, land[1] * 32 + 48   # the footprint's middle
        cam = look_at(io, *centred(lx, ly), wait=0.25)
        io.click(*LIFT_BUTTON)          # in the air it is the Land button
        io.sleep(0.2)
        io.click(*live.on_screen(lx, ly, cam))
        io.sleep(0.3)
    else:
        for _ in range(2):
            io.click(*live.minimap_point(city["x"], city["y"]), button="right")
            io.sleep(0.8)
    io.shot("flight-" + city_name.split()[0])
    if kind == "Barracks":
        st.flown.add(tile)
    io.log(f"flight: {kind} lifted and sent to "
           + (f"land by {city_name} at {land}" if land else city_name))
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
TAX_AFTER_HITS = 1             # tax efforts from the first hit on, when there
                               # is time (the repository owner, after
                               # a replay: Krakow by 1:49)
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
TAX_KINDS = ["Factory", "Starport"]  # (the Engineering Bays stay: they do
                               # the infantry upgrades, "@R upgrade")
KEEP_BUILDINGS = {(163, 99)}   # the barracks on Odessa: it taxes Odessa
TAX_TRIES = 3                  # buildings sent to one city in a game at most
# The repository owner's demonstration: the Vehicle Factory floats to
# Krakow and the Airport (starport) to Romania, and both stay floating
# over the beacon. The nearest of that kind is kept for its city.
TAX_BUILDING = {"Krakow 200": "Factory", "Romania 300": "Starport"}
TAKEN_ODDS = 3                 # our pixels to one enemy pixel at a city: just taken
TAX_LAND = {"Krakow 200": (134, 94)}   # tiles: where a strong Russia lands his
                               # buildings by Krakow (the repository owner)
FACTORY_REACH = 120            # seconds of flight: a factory this near is "nearby"


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


def kept_for_tax(mapdata, st):
    """The building of each tax city's own kind kept for it (the
    factory nearest Krakow, the starport nearest Romania), while that
    city has had none sent: tiles."""
    out = set()
    spare = spare_buildings(mapdata, st)
    for name, kind in TAX_BUILDING.items():
        if name in st.tax_sent:
            continue
        city = place(mapdata, name)
        mine = [b for b in spare if b["type"] == kind]
        if mine:
            b = min(mine, key=lambda b: float_time(b, city))
            out.add((b["x"] // 32, b["y"] // 32))
    return out


def not_kept(mapdata, st, choices):
    """Leave out the buildings kept for Krakow and Romania, unless
    nothing else is left."""
    kept = kept_for_tax(mapdata, st)
    others = [b for b in choices if (b["x"] // 32, b["y"] // 32) not in kept]
    return others or choices


def city_clear(hostile, ours, city):
    """True if a city is clear for a floating building: no enemies near
    it, or so few beside our own troops there that it has just been
    taken."""
    xy = (city["x"], city["y"])
    enemies = len(near(hostile, xy, TAX_ENEMY))
    return enemies < TAX_ENEMY_LEAST or \
        len(near(ours, xy, TAX_ENEMY)) >= TAKEN_ODDS * enemies


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


def send_guard(io, watch, mapdata, st, name, picture, why=""):
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
    io.log(f"tax: a detachment of {n} sent to {name} "
           + (why or "to secure it from the enemies there"))
    return n


COMMAND_CENTRES = [(157, 51), (209, 49)]   # tiles: Russia's two command centres
SCV_SPEED = 2.0                # tiles a real second, an SCV walking (guess)
SCV_TRAIN = 12                 # real seconds to make one
DEPOT_TRIES = 2                # depots tried at one city in a game at most
DEPOT_BUILD = 45               # real seconds to see whether the depot went up
DEPOT_SPOTS = [(0, 110), (110, 0), (-110, 0), (0, -110), (110, 110),
               (-110, 110)]    # screen pixels from the beacon to try


def select_building(io, b):
    """Click a building until the game shows it selected."""
    return pick_building(io, b)


SCV_WAIT = (0, 3)              # tiles from the command centre where a new
                               # SCV waits for its depot order
SUPPLY_WAIT = 180              # seconds an SCV waits for room in supply
SCV_RECHECK = 8                # real seconds before the SCV is looked for again
SCV_LOOKS = 2                  # looks for it before the try is given up
                               # (the repository owner, trial 31)
SCV_PICK = [(0, 0), (20, 0), (-20, 0), (0, 20), (0, -20), (30, 30), (-30, 30),
            (30, -30), (-30, -30), (45, 0), (-45, 0), (0, 45), (0, -45)]


def supply_full(io):
    """True when the supply display reads full (no SCV can be made)."""
    shot = getattr(io, "shot", None)
    pic = shot("supply", keep=False) if shot else None
    if pic is None:
        return False
    supply = numbers.read_supply(pic)
    return bool(supply) and supply[0] >= supply[1]


SCV_BUTTON = (1659, 845)       # the command card's first button: a centre's SCV
SCV_PRICE = 50


def start_scv(io):
    """With the command centre selected, start an SCV and check that it
    started: the minerals drop by its price (trial 38: the centre was
    clicked again and again and no SCV came; a click near it had picked
    another building, or S did nothing). S first, then the button
    itself. True if started, or if the minerals cannot be read."""
    before = read_money(io)
    io.key("s")                         # build an SCV
    io.sleep(0.15)
    if before is None:
        return True
    after = read_money(io)
    if after is None or before - after >= SCV_PRICE - 10:
        return True
    io.click(*SCV_BUTTON)               # the button, in case S did nothing
    io.sleep(0.15)
    after = read_money(io)
    return after is None or before - after >= SCV_PRICE - 10


def read_money(io):
    """The minerals at the top of the screen, or None if not read."""
    try:
        pic = io.shot("money", keep=False)
        return numbers.read_minerals(pic) if pic is not None else None
    except Exception:
        return None


def depot_at(io, watch, mapdata, st, name, ours, cc_tile=None,
             then_home=False):
    """With no factory or starport left to float, Russia makes an SCV at
    the nearest command centre and, as soon as it is out, orders it to
    build a supply depot next to the city's beacon (trial 31: not walked
    there first, then ordered). With `then_home` ("@R tax") it goes back
    to Moscow after. If the SCV is not seen by the centre at the second
    look, the try is over. Called on each round of the tax cities;
    returns 1 when it gave an order."""
    city = place(mapdata, name)
    cx, cy = city["x"], city["y"]
    if name in TAX_LAND:                # by the landing spot
        cx, cy = TAX_LAND[name][0] * 32 + 32, TAX_LAND[name][1] * 32 + 32
    job = st.depots.get(name)
    now = io.now()
    if job is not None and job["stage"] == "supply":
        if now - job["since"] > SUPPLY_WAIT:
            del st.depots[name]         # never room: the try is over
            io.log(f"tax: supply stayed full; no SCV for {name}")
            return 0
        if supply_full(io):
            return 0                    # still full: wait (a hit frees it)
        del st.depots[name]
        job = None
    if job is None:
        if st.depot_tries.get(name, 0) >= DEPOT_TRIES:
            return 0
        money = read_money(io)
        if money is not None and money < TAX_PRICE:
            # trial 37: the SCV was ordered with 0 minerals, never made,
            # and the try was lost; now it waits for the money
            if st.__dict__.setdefault("tax_broke", {}).get(name) is None:
                st.tax_broke[name] = now
                io.log(f"tax: {money} minerals, {TAX_PRICE} needed for "
                       f"{name}'s SCV and depot: waiting for the money")
            return 0
        st.__dict__.setdefault("tax_broke", {}).pop(name, None)
        if supply_full(io):             # full: no SCV can be made
            st.depots[name] = {"stage": "supply", "since": now}
            io.log(f"tax: supply is full: {name}'s SCV waits for room")
            return 0
        tiles = sorted(COMMAND_CENTRES, key=lambda t: (t[0] * 32 - cx) ** 2
                       + (t[1] * 32 - cy) ** 2)
        if cc_tile:
            tiles = [cc_tile] + [t for t in tiles if t != cc_tile]
        st.depot_tries[name] = st.depot_tries.get(name, 0) + 1
        b = None
        for tile in tiles:              # the other centre if one is not found
            c = next((c for c in mapdata["slots"][SLOT]["buildings"]
                      if c["type"] == "Command Center"
                      and (c["x"] // 32, c["y"] // 32) == tile), None)
            if c is not None and select_building(io, c):
                b = c
                break
        if b is None:
            io.log(f"tax: the command centre for {name}'s SCV was not found")
            return 0
        if not start_scv(io):
            io.shot("no-scv")
            io.log(f"tax: the command centre did not start an SCV for {name} "
                   f"(picture 'no-scv')")
            return 0
        # its rally point set on the screen, by the centre, with the same
        # camera it is picked with later (trial 33: set on the minimap, it
        # stood a tile or two off and was not found twice)
        wx, wy = b["x"] + SCV_WAIT[0] * 32, b["y"] + SCV_WAIT[1] * 32
        cam = look_at(io, b["x"], b["y"], wait=0.2)
        sx, sy = live.on_screen(wx, wy, cam)
        l, t, r, btm = live.GAME_AREA
        if l + 40 < sx < r - 40 and t + 40 < sy < btm - 40:
            io.click(sx, sy, button="right")
        else:
            io.click(*live.minimap_point(wx, wy), button="right")
        io.sleep(0.1)
        walk = ((b["x"] - cx) ** 2 + (b["y"] - cy) ** 2) ** 0.5 / 32 / SCV_SPEED
        st.depots[name] = {"stage": "training", "due": now + SCV_TRAIN + 2,
                           "wait": (wx, wy), "look": (b["x"], b["y"]),
                           "walk": walk, "looks": 0}
        io.log(f"tax: no factory or starport left: an SCV is being made for "
               f"a depot at {name}; it is ordered there once it is out")
        return 1
    if job["stage"] == "training":
        if now < job["due"]:
            return 0
        return depot_by_order(io, mapdata, st, name, cx, cy, job, then_home)
    if job["stage"] == "building" and now >= job["due"]:
        if near(ours, (cx, cy), TAX_HERE + 2):
            job["stage"] = "done"
            io.log(f"tax: a depot stands at {name}")
        else:
            del st.depots[name]
            io.log(f"tax: no depot to be seen at {name}")
    return 0


def depot_by_order(io, mapdata, st, name, cx, cy, job, then_home=True):
    """The new SCV, picked where it waits by the command centre, is
    ordered to build a depot next to the city's beacon. A spot is taken
    when the game leaves placing (the SCV's own buttons are back);
    otherwise the next spot is tried."""
    now = io.now()
    wx, wy = job["wait"]
    cam = look_at(io, *job.get("look", centred(wx, wy)), wait=0.2)
    sx, sy = live.on_screen(wx, wy, cam)
    picked = False
    for dx, dy in SCV_PICK:             # the SCV alone, by a click
        io.click(sx + dx, sy + dy)
        io.sleep(0.1)
        pic = io.shot("scv", keep=False)
        if not (live.units_selected(pic) and live.selected_count(pic) == 1):
            continue
        # only an Engineer (the SCV) opens the build menu with B: the
        # card's Move button goes (the repository owner's pictures); a
        # marine standing by the centre keeps it
        io.key("b")
        io.sleep(0.1)
        if not live.units_selected(io.shot("build-menu", keep=False)):
            picked = True
            break
        io.key("esc")
    if not picked:
        job["looks"] = job.get("looks", 0) + 1
        if job["looks"] >= SCV_LOOKS:
            del st.depots[name]
            io.log(f"tax: the SCV for {name} was not seen by the command "
                   f"centre at the second look; given up")
        else:
            job["due"] = now + SCV_RECHECK
            io.log(f"tax: the SCV for {name} not seen yet; looking again in "
                   f"{SCV_RECHECK} s")
        return 0
    cam = look_at(io, *centred(cx, cy), wait=0.2)
    bx, by = live.on_screen(cx, cy, cam)
    l, t, r, btm = live.GAME_AREA
    in_menu = True                      # B was pressed when it was picked
    for dx, dy in DEPOT_SPOTS:
        x, y = bx + dx, by + dy
        if not (l + 40 < x < r - 40 and t + 40 < y < btm - 40):
            continue
        if not in_menu:
            io.key("b")
            io.sleep(0.1)
        in_menu = False
        io.key("s")                     # a supply depot
        io.sleep(0.15)
        io.click(x, y)
        io.sleep(0.3)
        if live.units_selected(io.shot("placed", keep=False)):
            if then_home:
                io.key("m")             # then home to Moscow, queued
                io.sleep(0.05)
                mx, my = MOSCOW_CC
                io.click_with("shift", *live.minimap_point(mx * 32, my * 32))
                io.sleep(0.05)
            job.update(stage="building",
                       due=now + job.get("walk", 0) + DEPOT_BUILD)
            io.shot("depot-" + name.split()[0])
            io.log(f"tax: the new SCV is ordered to build a depot by "
                   f"{name}'s beacon" + ("; it goes back to Moscow after"
                                         if then_home else ""))
            return 1
        io.key("esc")                   # that spot was taken: the next
        io.sleep(0.1)
        if not live.units_selected(io.shot("after-esc", keep=False)):
            # Esc left the build menu up: once more, back to the
            # Engineer's own buttons, so the next B is "Build" and never
            # "Barracks" in the build menu
            io.key("esc")
            io.sleep(0.1)
    del st.depots[name]
    io.log(f"tax: no room for a depot by {name}'s beacon")
    return 0


def float_to(io, watch, mapdata, st, name, ours, to_arrive=None):
    """Float the best spare building to a tax city; with none left, an
    SCV builds a depot there. Returns 1 if it gave an order."""
    city = place(mapdata, name)
    clock = st.clock.time() if st.clock else io.now()
    choices = spare_buildings(mapdata, st)
    own = [b for b in choices if b["type"] == TAX_BUILDING.get(name)]
    if name == "Factory 7":
        # a starport that can arrive in time; with none, an SCV builds a
        # depot by the Heavy Industry there (the repository owner)
        ports = [b for b in choices if b["type"] == "Starport"
                 and float_time(b, city) <= (to_arrive or 1e9)]
        ports = not_kept(mapdata, st, ports) if ports else ports
        if not ports:
            return depot_at(io, watch, mapdata, st, name, ours)
        choices = ports
    elif to_arrive is not None:
        choices = [b for b in choices if float_time(b, city) <= to_arrive]
        choices = not_kept(mapdata, st, choices)
    elif own:
        # Krakow's factory, Romania's starport: the nearest of its kind
        b = min(own, key=lambda b: float_time(b, city))
        if name in TAX_LAND and float_time(b, city) > FACTORY_REACH:
            return depot_at(io, watch, mapdata, st, name, ours)
        choices = [b]
    elif name in TAX_LAND:
        # no factory left for Krakow: an SCV builds a depot there
        return depot_at(io, watch, mapdata, st, name, ours)
    elif "Factory 7" not in st.tax_sent:
        # keep the buildings that can reach Factory 7 in its window
        # for Factory 7, while there are others
        f7 = place(mapdata, "Factory 7")
        window = (300 - F7_ARRIVE + F7_SET_OFF) / COUNTDOWN_RATE
        others = [b for b in choices if float_time(b, f7) > window]
        if others:
            choices = others
        choices = not_kept(mapdata, st, choices)
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
        if st.lift_fails.get(tile, 0) < LIFT_TRIES:
            st.flights_done.discard(tile)   # still on the ground: again later
        return 0
    st.tax_sent[name] = (io.now(), tile, io.now() + float_time(b, city))
    if name == "Krakow 200":
        st.krakow_landed, st.land_tries = False, 0   # a new one to land
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
    if flight and near(ours, tax_spot(mapdata, name), TAX_HERE):
        return 0                        # and it is there
    if st.tax_tries.get(name, 0) >= TAX_TRIES:
        return 0
    hostile = watch.others(picture, TAX_HOSTILE) if picture is not None \
        else set()
    if not city_clear(hostile, ours, city):
        # not into the enemy (trial 23): the tax rounds send it once
        # the hit has cleared the city
        io.log(f"tax: {name} is not clear yet: its building waits")
        return 0
    io.log(f"tax: a building follows the hit to {name}")
    return float_to(io, watch, mapdata, st, name, ours)


def tax_spot(mapdata, name):
    """Where a tax city's building stands: its landing spot, or over the
    beacon."""
    if name in TAX_LAND:
        return TAX_LAND[name][0] * 32 + 64, TAX_LAND[name][1] * 32 + 48
    c = place(mapdata, name)
    return c["x"], c["y"]


LAND_TRIES = 4                 # landings tried at Krakow before giving up
LAND_CHECK_EVERY = 20          # seconds between looks at the Krakow building
LAND_SPOTS = [(0, 0), (0, 3), (3, 0), (-3, 0), (0, -3), (3, 3)]
                               # tiles from the landing spot, tried in turn


def corner_button(picture):
    """True if the bottom-right command button is there (yellow): Lift
    Off or Land, a building's; units show nothing there."""
    import numpy as np
    x, y = LIFT_BUTTON
    a = np.asarray(picture.convert("RGB").crop((x - 40, y - 40, x + 40, y + 40))
                   ).astype(int)
    return int(((a[..., 0] > 180) & (a[..., 1] > 150) & (a[..., 2] < 90)).sum()) > 300


def check_landed(io, mapdata, st):
    """Krakow's building must land (the repository owner). Once it should
    have arrived, look at its spot: still in the air (Move and the Land
    button), land it again, a little to one side if the spot was taken;
    on the ground (no Move, Lift Off there), done."""
    flight = st.tax_sent.get("Krakow 200")
    if not flight or st.krakow_landed or st.land_tries >= LAND_TRIES:
        return False
    now = io.now()
    if now < flight[2] + 5 or now - st.last_land_check < LAND_CHECK_EVERY:
        return False
    st.last_land_check = now
    lx, ly = tax_spot(mapdata, "Krakow 200")
    cam = look_at(io, *centred(lx, ly), wait=0.25)
    sx, sy = live.on_screen(lx, ly, cam)
    l, t, r, b = live.GAME_AREA
    for dx, dy in BUILDING_SPOTS:
        x, y = sx + dx, sy + dy
        if not (l + 5 < x < r - 5 and t + 5 < y < b - 5):
            continue
        io.click(x, y)
        io.sleep(0.12)
        pic = io.shot("land-check", keep=False)
        if not corner_button(pic):
            continue                    # a unit, or nothing: not it
        if live.units_selected(pic):    # Move and Land: still in the air
            ox, oy = LAND_SPOTS[st.land_tries % len(LAND_SPOTS)]
            st.land_tries += 1
            tx, ty = lx + ox * 32, ly + oy * 32
            cam = look_at(io, *centred(tx, ty), wait=0.25)
            io.click(*LIFT_BUTTON)      # Land
            io.sleep(0.2)
            io.click(*live.on_screen(tx, ty, cam))
            io.sleep(0.3)
            io.log(f"tax: the Krakow building was still in the air: landing "
                   f"it again (try {st.land_tries})")
            return True
        st.krakow_landed = True         # on the ground
        io.log("tax: the Krakow building has landed")
        return True
    return False


def busy(st):
    """No time for tax: a hit has been announced and goes soon."""
    return st.team is not None and st.team.announced is not None


def tax_rounds(io, watch, mapdata, st, picture):
    """Look after the tax cities: float a building over each that has
    none, if no enemies are near; send a detachment first if there are
    a few; leave it to the hits if there are many."""
    if st.clock is None or st.hits_sent < TAX_AFTER_HITS:
        return 0
    if busy(st):
        return 0                        # a hit is about to go: no time
    check_landed(io, mapdata, st)
    # Krakow and Romania now and then; Factory 7 on every pass, because
    # its moment (1:00 to 0:00 on the countdown) lasts only about 40
    # real seconds and must not be missed
    due = io.now() - st.last_tax >= TAX_EVERY
    if due:
        st.last_tax = io.now()
    clock = st.clock.time()
    ours = watch.units(picture)
    hostile = watch.others(picture, TAX_HOSTILE)
    sent = 0
    for name in TAX_CITIES:
        if name != "Factory 7" and not due:
            continue
        if name in st.tax_jobs:
            continue                    # an ally's "@R tax" sees to it
        city = place(mapdata, name)
        cx, cy = city["x"], city["y"]
        if st.depots.get(name, {}).get("stage") in ("supply", "training",
                                                     "building"):
            sent += depot_at(io, watch, mapdata, st, name, ours)
            continue                    # an SCV is seeing to it
        # (our troops standing there do not tax it: a building must
        # float over the beacon, so they do not stop one being sent)
        flight = st.tax_sent.get(name)
        if flight and io.now() < flight[2] + FLOAT_SLACK:
            continue                    # on its way
        if flight and near(ours, tax_spot(mapdata, name), TAX_HERE):
            continue                    # arrived and still there
        if st.tax_tries.get(name, 0) >= TAX_TRIES:
            continue                    # lost twice: no more buildings there
        if name == "Factory 7":
            # only once Belgrade is cleared: our troops there, or taken
            # (the repository owner)
            if name not in st.reached and \
                    len(near(ours, (cx, cy), TAX_ENEMY)) < MIN_FORWARD:
                continue
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
        if not city_clear(hostile, ours, city):
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
        b = min(not_kept(mapdata, st, others or choices),
                key=lambda b: float_time(b, city))
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


def road_start(st, name):
    """Where a hit that way starts: east is always Berlin, the Balkans
    always Romania (the repository owner)."""
    return south_next(st) if team_rules.front_of(name) == "balks" \
        else east_next(st)


def south_next(st):
    """Where a new hit to the Balkans is sent: always Romania, the way
    in. From Smolensk a straight march to Belgrade, Hungary or beyond
    goes through German Poland, which is the eastern front, not the
    Balkans (trial 21: "gone balks" at Frankfurt marched east). Once
    the hit reaches Romania it is carried on down the road
    (advance_front): Factory 7, Hungary, Munich, Frankfurt, Amsterdam."""
    return "Romania 300"


BALKANS_HOLD = 40              # our minimap pixels on the Balkan road: with
                               # this many there the next hit goes there too


def choose_target(io, watch, st, mapdata=None, battle=None):
    """Where the next hit should go.

    The general's choice comes first. Otherwise the plan by the clock:
    south when qororo98 and penny[eef] go south. Otherwise south if the
    Axis has grown in the Balkans since the start (Germany starts with
    troops there), and Berlin itself if not (never a city on the way)."""
    south = south_next(st)
    if watch is not None and mapdata is not None:
        # the owner (trial 41): no hit east while our troops are still in
        # the Balkans; the next hit follows them
        there = len(balkan_units(st, mapdata,
                                 watch.units(io.shot("choose", keep=False)),
                                 io.now()))
        if there >= BALKANS_HOLD:
            io.log(f"next target {south} (our troops are still in the "
                   f"Balkans, {there} pixels: no hit east meanwhile)")
            return south
    if st.advised and io.now() - st.advised[1] <= 40:
        name = road_start(st, st.advised[0])
        io.log(f"next target {name} (the general's choice of front)")
        return name
    if planned_front(io.now() - st.t0) == "south":
        io.log(f"next target {south} (the plan: south at this point in the "
               f"game, as qororo98 and penny[eef] do)")
        return south
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
            # nothing of ours forward any more: no front (trial 25: the
            # air and the next orders went to an old front, empty ground)
            self.front = None
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
STUCK_FORGET = 150             # seconds before such a spot is tried again: new
                               # troops appear at the factories every round
                               # (trial 33: their tanks and men never came)
SHRANK = 2                     # minimap pixels a body must lose to have moved


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
    if team_rules.front_of(battle.target) == "balks":
        # past Romania, where the hit goes on to: still the hit, not
        # idle men to fetch home (they were walked back to the mass)
        out |= near(pixels, BALKS_POINT, 14)
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


# The repository owner (recording 10e35650): the way from Odessa into
# Romania is a choke. Troops left standing in it, or in Romania, block
# the next hit behind them, and hits pile up there. So those troops
# always go on down the Balkan road (never back through the choke to
# the mass), and the choke is cleared before a new hit to the Balkans.
CHOKE = ("Odessa 200", "Romania 300")
CHOKE_WIDTH = 7                # minimap pixels either side of the way
CHOKE_EVERY = 10               # seconds between pushes through the choke
CHOKE_LEAST = 3                # minimap pixels: a body worth an order


def in_choke(mapdata, pixels):
    """Our pixels on the way from Odessa into Romania, or in Romania."""
    a, b = (live.to_drawn(place(mapdata, n)["x"], place(mapdata, n)["y"])
            for n in CHOKE)
    (ac, ar), (bc, br) = a, b
    dc, dr = bc - ac, br - ar
    length2 = float(dc * dc + dr * dr) or 1.0
    out = set()
    for c, r in pixels:
        f = min(1.0, max(0.0, ((c - ac) * dc + (r - ar) * dr) / length2))
        pc, pr = ac + f * dc, ar + f * dr
        if (c - pc) ** 2 + (r - pr) ** 2 <= CHOKE_WIDTH ** 2:
            out.add((c, r))
    return out


def beyond_choke(st, mapdata, hostile, ours):
    """Where troops in the choke go: on down the Balkan road past every
    city already taken; Romania itself while it is not. (Romania counts
    as taken once our troops stand there and see no enemy left: with
    none of ours there, the fog hides the enemy.)"""
    at = CHOKE[1]
    r = place(mapdata, at)
    if len(near(ours, (r["x"], r["y"]), 8)) >= MIN_FORWARD and \
            len(near(hostile, (r["x"], r["y"]), 8)) < CLEARED:
        st.reached.add(at)              # ours there, no enemy left: taken
    steps = 0
    while at in st.reached and at in NEXT and steps < 10:
        at, steps = NEXT[at], steps + 1
    return at


def clear_choke(io, watch, mapdata, st, still, picture, force=False):
    """Send the troops standing in the Odessa-Romania choke, or idle in
    Romania, on to the next stop of the Balkan road, so the way stays
    open and the next hit does not pile up behind them. Troops in a
    fight are left to it. Returns the orders given."""
    if not force and io.now() - st.last_choke < CHOKE_EVERY:
        return 0
    st.last_choke = io.now()
    hostile = watch.others(picture, HOSTILE)
    idle = in_choke(mapdata, still)
    idle -= guarding(st, mapdata, idle, io.now())
    if len(idle) < CHOKE_LEAST:
        return 0
    dest = beyond_choke(st, mapdata, hostile, watch.units(picture))
    d = place(mapdata, dest)
    groups = front_to_back([g for g in live.clusters(idle, 4, 4)
                            if len(g) >= CHOKE_LEAST
                            and not in_contact(g, hostile)],
                           (d["x"], d["y"]), lambda g: live.from_drawn(*g[0]))
    orders = 0
    for group in groups[:12]:
        if select_group(io, group, st, watch, margin=45):
            send_at(io, mapdata, st, dest)
            orders += 1
    if orders:
        io.log(f"  choke: {orders} groups standing between Odessa and "
               f"Romania sent on to {dest}")
    return orders


WALKING = 60                   # seconds a body sent to the mass is left to walk
WALK_LANE = 5                  # minimap pixels either side of its way to the mass
CROWD_BODY = 12                # minimap pixels: a crowd, boxed all over at once
CROWD_REACH = 7                # minimap pixels round a crowd that its boxes cover


FACTORY_EXIT = 6               # tiles from a factory toward the mass: its way out


def spawn_spot(st):
    """Where the next group brought in goes: its own spot on a grid 8
    tiles apart round the mass point, taking turns (the repository
    owner: each group its own spot, at least 8 tiles from the others;
    the grid sits between the barracks' rally spots)."""
    dx, dy = SPREAD_WIDE[st.spawn_next % len(SPREAD_WIDE)]
    st.spawn_next += 1
    return MASS[0] + dx * 32, MASS[1] + dy * 32


def to_mass(io, mapdata, xy, st=None):
    """Send what is selected to the mass: to its own spot there. New
    units at a factory first walk (no fighting) out from among the
    buildings, then go on, queued (trial 26: tanks at Factory 2 stood
    boxed in, called "stuck")."""
    dest = spawn_spot(st) if st is not None else MASS
    for name in SCOUT_FACTORIES:
        f = place(mapdata, name)
        if abs(xy[0] - f["x"]) <= 5 * 32 and abs(xy[1] - f["y"]) <= 5 * 32:
            out = toward((f["x"], f["y"]), MASS, FACTORY_EXIT)
            io.click(*live.minimap_point(*out), button="right")
            io.sleep(0.04)
            io.key("a")
            io.sleep(0.04)
            io.click_with("shift", *live.minimap_point(*dest))
            io.sleep(0.04)
            return
    attack_move(io, *dest)


def on_the_way(st, spot, mass):
    """True if a body stands on the way from where a body was sent to
    the mass lately, to the mass: troops walking there in a crowd look
    as if standing still, a second apart (trial 24: ordered again every
    ten seconds)."""
    (c, r), (mc, mr) = spot, mass
    for when, (oc, orow) in st.walking:
        dc, dr = mc - oc, mr - orow
        length2 = float(dc * dc + dr * dr) or 1.0
        f = ((c - oc) * dc + (r - orow) * dr) / length2
        if -0.1 <= f <= 1.0:
            pc, pr = oc + f * dc, orow + f * dr
            if (c - pc) ** 2 + (r - pr) ** 2 <= WALK_LANE ** 2:
                return True
    return False


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
    # in the Balkans they go on (advance_front with a Balkan hit, else
    # sweep_balkans), never home to the mass (trial 38)
    idle -= balkan_units(st, mapdata, idle)    # (guards: left out below too)
    idle -= guarding(st, mapdata, idle, io.now())
    idle -= near(idle, fleet_spot(), 6)  # the fleet waits there: not a body
    idle -= scout_spots(io, mapdata, st, idle)   # new Scouts: for the fleet
    idle -= in_choke(mapdata, idle)     # they go on, not back: clear_choke
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
    now = io.now()
    st.walking = [w for w in st.walking if now - w[0] < WALKING]
    swept = set()
    for group in bodies:
        if orders >= GATHER_PER_PASS:
            break
        cx = sum(p[0] for p in group) // len(group)
        cy = sum(p[1] for p in group) // len(group)
        if (cx, cy) in swept or on_the_way(st, (cx, cy), (mc, mr)):
            continue                    # sent lately and walking to the mass
        if len(group) >= CROWD_BODY:
            # a crowd (trial 24: seventy Siberians, seven a box): boxed
            # all over in one go, a dozen at a time
            x, y = live.from_drawn(cx, cy)
            ahead = reinforce_target(io, st)
            n, found = sweep_mass(io, watch, mapdata, st, ahead,
                                  centre=(x, y),
                                  dest=None if ahead else spawn_spot(st),
                                  radius=CROWD_REACH, least=GATHER_LEAST)
            if n:
                orders += n
                st.walking.append((io.now(), (cx, cy)))
                swept |= {(c, r) for c in range(cx - CROWD_REACH, cx + CROWD_REACH + 1)
                          for r in range(cy - CROWD_REACH, cy + CROWD_REACH + 1)}
            continue
        key = (cx // 4, cy // 4)
        # a place is tried again after a while: new troops appear at
        # the same spots all game
        if io.now() - tried.get(key, -1e9) < RETRY_IDLE:
            continue
        tried[key] = io.now()
        before = st.idle_sizes.get(key)
        st.idle_sizes[key] = len(group)
        if before is not None and len(group) <= before - SHRANK:
            # it got smaller since the last order: men are leaving it, a
            # dozen at a time (a big spawn takes many orders: trial 23)
            st.idle_orders[key] = 0
        if st.idle_orders.get(key, 0) >= STUCK_AFTER and \
                io.now() - st.idle_stuck.get(key, -1e9) > STUCK_FORGET:
            st.idle_orders[key] = 0     # long enough: tried afresh
        st.idle_orders[key] = st.idle_orders.get(key, 0) + 1
        if st.idle_orders[key] > STUCK_AFTER:
            continue                    # ordered three times and never moved
        if select_group(io, group, st, watch, margin=60):
            ahead = reinforce_target(io, st)
            if ahead:
                send_at(io, mapdata, st, ahead)     # straight to the hit
            else:
                to_mass(io, mapdata, live.from_drawn(cx, cy), st)
            orders += 1
            st.walking.append((io.now(), (cx, cy)))
            if st.idle_orders[key] == STUCK_AFTER:
                st.idle_stuck[key] = io.now()
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


BALKS_LEAST = 2                # minimap pixels: a small body in the Balkans is
                               # still sent on (trial 38: some were left)
SERBIA = "Factory 7"           # Belgrade
PAST_ROMANIA = 4               # our minimap pixels at BALKS_POINT: got past it


def balkan_units(st, mapdata, pixels, now=None):
    """Our pixels of the Balkan road: round Romania, past it
    (BALKS_POINT), in the choke and anywhere in the Balkans; not the
    mass, the Middle East spawn or a tax detachment."""
    r = place(mapdata, "Romania 300")
    out = near(pixels, (r["x"], r["y"]), 14) | near(pixels, BALKS_POINT, 14) \
        | in_balkans(pixels) | in_choke(mapdata, pixels)
    out -= at_mass(pixels) | near(pixels, MIDDLE_EAST, 8)
    if now is None:
        return out
    return out - guarding(st, mapdata, out, now)


def into_serbia(io, watch, mapdata, st, picture):
    """The repository owner (trial 38): once Romania has no enemy left
    and our troops have got past it (BALKS_POINT), with Serbia not yet
    taken, every man of the hit goes on into Serbia at once: moving or
    not, however few. True if they were sent."""
    battle = st.battle
    if battle is None or battle.target != "Romania 300" or \
            SERBIA in st.reached or picture is None:
        return False
    w = place(mapdata, "Romania 300")
    hostile = watch.others(picture, HOSTILE)
    if len(near(hostile, (w["x"], w["y"]), 8)) >= CLEARED:
        return False
    ours = watch.units(picture)
    if len(near(ours, BALKS_POINT, 9)) < PAST_ROMANIA:
        return False
    st.reached.add("Romania 300")
    st.outcomes.append(f"hit at Romania 300: through, sent on into {SERBIA}")
    io.log(f"Romania 300 clear and our troops past it: the whole hit goes "
           f"on into Serbia ({SERBIA})")
    st.battle = Battle(SERBIA, io.now())
    st.sent_at.append(SERBIA)
    st.last_advance = io.now()
    s = place(mapdata, SERBIA)
    men = balkan_units(st, mapdata, ours, io.now()) - near(ours, (s["x"], s["y"]), 6)
    orders = 0
    for group in front_to_back(live.clusters(men, 4, 4), (s["x"], s["y"]),
                               lambda g: live.from_drawn(*g[0]))[:30]:
        if len(group) >= BALKS_LEAST and \
                select_group(io, group, st, watch, margin=45):
            send_at(io, mapdata, st, SERBIA)
            orders += 1
    io.log(f"  {orders} groups sent on into Serbia")
    if getattr(st, "air_waits_serbia", False):
        st.air_waits_serbia = False
        if DOGFIGHT and own_fleet_keys(st) and not st.air_home:
            # now the air: from where it waits, with the army
            dogfight(io, watch, mapdata, st, SERBIA)
    return True


def balkan_objective(st):
    """Where men left on the Balkan road go next: the first stop of the
    road not yet taken (Romania, Belgrade, then on toward Amsterdam)."""
    name = "Romania 300"
    seen = set()
    while name in st.reached and name in NEXT and name not in seen:
        seen.add(name)
        name = NEXT[name]
    return name


BALKS_SWEEP_EVERY = 5          # seconds between sweeps of the Balkans for idle men


def sweep_balkans(io, watch, mapdata, st, still, picture, force=False):
    """The repository owner (trial 38): men of earlier hits idle in the
    Balkans (round BALKS_POINT, Romania, Serbia, Greece) are sent on to
    the next stop of the Balkan road, however few: at the start of every
    massing cycle, every few seconds during it, and before a new hit
    goes. While a Balkan hit is on, advance_front sends them with it.
    Returns the orders given."""
    if balkan_hit_on(st) or picture is None:
        return 0
    if not force and io.now() - st.last_balks_sweep < BALKS_SWEEP_EVERY:
        return 0
    st.last_balks_sweep = io.now()
    idle = balkan_units(st, mapdata, still, io.now())
    objective = balkan_objective(st)
    o = place(mapdata, objective)
    idle -= near(idle, (o["x"], o["y"]), 6)
    if len(idle) < BALKS_LEAST:
        return 0
    hostile = watch.others(picture, HOSTILE)
    orders = 0
    for group in front_to_back(live.clusters(idle, 4, 4), (o["x"], o["y"]),
                               lambda g: live.from_drawn(*g[0]))[:24]:
        if len(group) < BALKS_LEAST or in_contact(group, hostile):
            continue
        if select_group(io, group, st, watch, margin=45):
            send_at(io, mapdata, st, objective)
            orders += 1
    if orders:
        io.log(f"  {orders} idle groups left in the Balkans sent on to "
               f"{objective}")
    return orders


def in_contact(group, hostile, reach=4):
    return sum((c + i, r + j) in hostile for c, r in group
               for i in range(-reach, reach + 1)
               for j in range(-reach, reach + 1)) >= 6


def in_balkans(pixels):
    """Our minimap pixels in the Balkans (Greece, Serbia, Romania's south)."""
    x0, y0, x1, y1 = BALKS_AREA
    out = set()
    for c, r in pixels:
        x, y = live.from_drawn(c, r)
        if x0 <= x / 32 < x1 and y0 <= y / 32 < y1:
            out.add((c, r))
    return out


def balkan_hit_on(st):
    return st.battle is not None and \
        team_rules.front_of(st.battle.target) == "balks"


def advance_front(io, watch, mapdata, st, still, picture):
    """Keep the troops forward from standing idle.

    `still` is the set of our unit pixels that have not moved between
    two looks a second apart. Those forward of the mass that are not in
    contact with the enemy are idle. If the hit has taken its target
    they are sent on to the next objective; if they have stopped short
    of it they are sent at it again. Returns the orders given."""
    battle = st.battle
    balks = battle is not None and team_rules.front_of(battle.target) == "balks"
    every = ADVANCE_EVERY_BALKS if balks else ADVANCE_EVERY
    if battle is None or io.now() - st.last_advance < every:
        return 0
    w = place(mapdata, battle.target)
    if into_serbia(io, watch, mapdata, st, picture):
        return 1
    # only the troops of this hit: those around its target or its front.
    # Troops holding somewhere else, such as Berlin, are left alone.
    idle = forward_units(still, mapdata)
    mine = near(idle, (w["x"], w["y"]), 26)
    if battle.front:
        mine |= near(idle, battle.front, 14)
    if balks:
        mine |= near(idle, BALKS_POINT, 14)    # gone on past Romania
        # and anyone idle in the Balkans (trial 36: men left round Greece;
        # Greece is farther from Berlin than the mass, so they counted as
        # at home and were never sent on)
        mine |= in_balkans(still - at_mass(still) - near(still, MIDDLE_EAST, 8))
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
    if battle.target == "Romania 300":
        # a Romania hit goes on, queued, past it toward Serbia (BALKS_POINT):
        # there it has taken Romania (trial 36: never counted as there, the
        # men were sent back at Romania again and again and the hit stalled)
        at_target |= near(idle, BALKS_POINT, 9)
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
    # on the Balkan road the front moves first: the choke behind it
    # stays blocked until it does (trial 24)
    order = front_to_back if team_rules.front_of(objective) == "balks" \
        else back_to_front
    groups = order(live.clusters(idle, 4, 4), (o["x"], o["y"]),
                   lambda g: live.from_drawn(*g[0]))
    least = BALKS_LEAST if team_rules.front_of(objective) == "balks" else 4
    for group in groups[:24]:
        if len(group) < least or fighting(group):
            continue
        # a tight box: wide ones overlap and pick the same troops again
        if select_group(io, group, st, watch, margin=45):
            send_at(io, mapdata, st, objective)
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
# The fleet in a hit (the repository owner): stacked, over our own ground
# troops, away from too many marines (more than 3 to a Scout), pulled
# back to wait for the next hit once the hit fades.
AIR_LEAD = 14                  # tiles ahead of the mass where the fleet first goes
                               # (past the massing place, out of its boxes)
AIR_DANGER = 6                 # minimap pixels round the fleet's spot for enemy
AIR_ODDS = 3                   # enemy men to one Scout: too many
AIR_STEP = 4                   # tiles the fleet holds back each time it is too many


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
    # looked at again a moment later, and a picture kept (trial 34: 8
    # groups went west of Moscow at the end and nothing showed why)
    io.sleep(1.5)
    again = io.shot("intruders") if hasattr(io, "shot") else None
    if again is not None:
        if len(axis_at_home(watch, again)) - st.home_axis0 < INTRUDERS:
            io.log(f"Axis inside Russia? {len(inside)} pixels, gone a moment "
                   f"later: nothing sent")
            st.last_defence = io.now()
            return 0
    st.last_defence = io.now()
    x, y = middle(body)
    orders = 0
    for group in live.clusters(at_mass(still), *GROUP)[:6]:
        if len(group) >= 4 and select_group(io, group, st, watch):
            attack_move(io, x, y)
            orders += 1
    if own_fleet_keys(st):
        set_air_state(io, st, "fighting", "Axis inside Russia", target=(x, y))
    for key in own_fleet_keys(st):
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
        if battle is not None and st.air_keys and not st.air_home and \
                st.fleet_task is None and \
                io.now() - battle.sent_at >= HIT_SETTLE:
            park_fleet(io, st, "no troops of ours are forward any more")
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
        if own_fleet_keys(st):
            set_air_state(io, st, "parked", "the hit is being lost",
                          target=fleet_spot())
        for key in own_fleet_keys(st):         # the fleet, as one, to its spot
            io.key(key)
            io.sleep(0.05)
            io.click(*live.minimap_point(*fleet_spot()), button="right")
            io.sleep(0.04)
        st.air_home = True
        io.log(f"hit at {battle.target} is being lost: {orders} groups of "
               f"survivors and the air pulled back to the massing place")
        return orders
    if st.air_keys and not st.air_home and st.fleet_task is None and \
            io.now() - st.air_moved >= AIR_FOLLOW_EVERY:
        st.air_moved = io.now()
        steer_fleet(io, watch, mapdata, st, picture)
    return orders


def fleet_scouts(st):
    return sum(e["scouts"] for e in st.fleet) or len(st.air_keys) * 3


def toward(a, b, tiles):
    """The point `tiles` from a toward b (map pixels)."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    d = max((dx * dx + dy * dy) ** 0.5, 1.0)
    step = min(tiles * 32, d)
    return (a[0] + dx / d * step, a[1] + dy / d * step)


CELL_LEAST = 6                 # enemy-coloured pixels that make a patch
MAN_COLOUR = 150               # team-colour pixels one man shows (a guess, to tune)
AIR_DANGER_TILES = 7           # how near the fleet's spot enemy count (tiles)


def enemy_mask(picture):
    """Pixels of the game view in the enemy's team colours: Germany red
    and Italy blue (the bright, strong shades units wear; the grass,
    trees, blood and Russia's brown do not reach them)."""
    import numpy as np
    l, t, r, b = live.GAME_AREA
    a = np.asarray(picture.convert("RGB").crop((l, t, r, b))).astype(int)
    R, G, B = a[..., 0], a[..., 1], a[..., 2]
    # bright team red, not the darker red of blood and fire; strong blue.
    # Not yellow: Russia's own Scouts are gold on screen, and Spain is
    # seldom near Russia's fronts.
    red = (R > 200) & (G < 60) & (B < 60)
    blue = (B > 170) & (R < 50) & (G < 80)
    mask = red | blue
    mask[:200, :170] = False            # the kills list, top left
    return mask


def enemy_on_screen(picture, cx, cy, radius, skip=()):
    """Roughly how many enemy units the game screen shows within `radius`
    screen pixels of (cx, cy). The patches of their team colour are
    found (pixels joined, a few apart); each counts as one man, a big one
    (several men close together, or a building) as one per MAN_COLOUR
    pixels. Thin streaks, such as health bars, are left out."""
    m = enemy_mask(picture)
    l, t = live.GAME_AREA[:2]
    for x, y, r in skip:                # our own buildings: their red lamps
        y0, x0 = max(0, int(y - t - r)), max(0, int(x - l - r))
        m[y0:int(y - t + r), x0:int(x - l + r)] = False
    import numpy as np
    a = np.asarray(picture.convert("RGB")).astype(int)
    R, G, B = a[..., 0], a[..., 1], a[..., 2]
    grey = (np.abs(R - G) < 25) & (np.abs(G - B) < 25) & (R > 110)
    dark_red = (R > 70) & (R < 200) & (G < 50) & (B < 50) & (R > 2 * G + 30)
    n = 0
    for pixels, x, y in patches(m):
        if pixels < CELL_LEAST:
            continue
        if (x - cx) ** 2 + (y - cy) ** 2 > radius ** 2:
            continue
        if is_blood(grey, dark_red, x, y):
            continue
        n += max(1, round(pixels / MAN_COLOUR))
    return n


BLOOD_WINDOW = 24              # screen pixels round a red patch that are looked at
BLOOD_DARK = 300               # dark red pixels there: a splash of blood
BLOOD_GREY = 25                # but fewer metal-grey pixels than this (units have them)


def is_blood(grey, dark_red, x, y):
    """True if a bright red patch is blood on the ground, not an enemy:
    blood lies in a spread of darker red with no grey metal round it;
    units and their machines show grey (trials 24, 25: a trail of blood
    was counted as 57 enemy and the fleet held back)."""
    x, y, w = int(x), int(y), BLOOD_WINDOW
    box = (slice(max(0, y - w), y + w), slice(max(0, x - w), x + w))
    return int(dark_red[box].sum()) > BLOOD_DARK and \
        int(grey[box].sum()) < BLOOD_GREY


def patches(m, k=4):
    """The patches of a mask of the game view: (pixels, screen x, screen
    y) for each, pixels a few apart joined. One cell tall (a health bar,
    a streak) is left out."""
    import numpy as np
    from collections import deque
    l, t = live.GAME_AREA[:2]
    h, w = m.shape
    g = m[:h - h % k, :w - w % k].reshape(h // k, k, w // k, k)
    count = g.sum(axis=(1, 3))
    cells = count > 0
    seen = np.zeros_like(cells)
    out = []
    for j0, i0 in zip(*np.nonzero(cells)):
        if seen[j0, i0]:
            continue
        seen[j0, i0] = True
        todo, part = deque([(j0, i0)]), []
        while todo:
            j, i = todo.popleft()
            part.append((j, i))
            for dj in (-1, 0, 1):
                for di in (-1, 0, 1):
                    y, x = j + dj, i + di
                    if 0 <= y < cells.shape[0] and 0 <= x < cells.shape[1] \
                            and cells[y, x] and not seen[y, x]:
                        seen[y, x] = True
                        todo.append((y, x))
        ys = [p[0] for p in part]
        if max(ys) - min(ys) + 1 < 2:   # one cell tall: a bar, not a man
            continue
        y = t + (sum(ys) / len(ys) + 0.5) * k
        x = l + (sum(p[1] for p in part) / len(part) + 0.5) * k
        out.append((sum(int(count[p]) for p in part), x, y))
    return out


GOLD_LEAST = 12                # gold pixels that make a Scout's patch


def gold_mask(picture):
    """Pixels of the game view in the Scouts' gold (Russia's Scouts are
    gold on screen, with blue engine glow; nothing else of ours is)."""
    import numpy as np
    l, t, r, b = live.GAME_AREA
    a = np.asarray(picture.convert("RGB").crop((l, t, r, b))).astype(int)
    R, G, B = a[..., 0], a[..., 1], a[..., 2]
    m = (R > 170) & (G > 120) & (B < 90) & (R - G < 90) & (G - B > 60)
    m[:240, :400] = False               # the kills list, top left
    m[:40, 880:1240] = False            # the round countdown
    m[660:, :380] = False               # the yellow buttons over the minimap
    return m


def gold_on_screen(picture, cx, cy, radius):
    """Where gold Scouts show on the game screen within `radius` screen
    pixels of (cx, cy): their screen points, the nearest first."""
    out = [(x, y) for n, x, y in patches(gold_mask(picture))
           if n >= GOLD_LEAST and (x - cx) ** 2 + (y - cy) ** 2 <= radius ** 2]
    return sorted(out, key=lambda p: (p[0] - cx) ** 2 + (p[1] - cy) ** 2)


OWN_BUILDING = 90               # screen pixels round each of our buildings left out
_own_buildings = None


def enemy_near_fleet(io, spot):
    """Look at the game screen round a spot and count the enemy there.
    Russia's own buildings are left out (Terran buildings carry red
    lamps that look like Germany's colour)."""
    global _own_buildings
    if _own_buildings is None:
        side = load_map()["slots"][SLOT]
        _own_buildings = [(b["x"], b["y"]) for b in side["buildings"]] + \
            [tuple(p) for p in side["structures"]]
    cam = look_at(io, *centred(*spot), wait=0.2)
    pic = io.shot("fleet-check", keep=False)
    sx, sy = live.on_screen(spot[0], spot[1], cam)
    skip = [(*live.on_screen(x, y, cam), OWN_BUILDING)
            for x, y in _own_buildings]
    return enemy_on_screen(pic, sx, sy, AIR_DANGER_TILES * 32 * live.ZOOM,
                           skip), pic


def enemy_men_near(hostile, xy, radius=AIR_DANGER):
    """Roughly how many enemy stand within `radius` minimap pixels of a
    point: their pixels at the rate our own spread-out men show."""
    return len(near(hostile, xy, radius)) * SPREAD_MEN


HIT_SETTLE = 60                # seconds after a hit before its air may be parked


def fleet_tick(io, watch, mapdata, st):
    """Keep the fleet over the army now and then, also while a hit is
    being sent (the sweeps take a while)."""
    battle = st.battle
    if battle is None or not st.air_keys or st.air_home or \
            st.fleet_task is not None or \
            io.now() - st.air_moved < AIR_FOLLOW_EVERY:
        return
    picture = io.shot("watch", keep=False)
    battle.sample(io, watch, mapdata, picture)
    if battle.front:
        st.air_moved = io.now()
        steer_fleet(io, watch, mapdata, st, picture)


def park_fleet(io, st, why):
    """The fleet, as one, back to its spot by the mass, to wait for the
    next hit."""
    park = live.minimap_point(*fleet_spot())
    if own_fleet_keys(st):
        set_air_state(io, st, "parked", why, target=fleet_spot())
    for key in own_fleet_keys(st):
        io.key(key)
        io.sleep(0.05)
        io.click(*park, button="right")
        io.sleep(0.04)
    st.air_home = True
    st.fleet_spot = None
    io.log(f"{why}: the fleet pulled back to wait for the next hit")


def steer_fleet(io, watch, mapdata, st, picture):
    """Keep the fleet, as one stack, over our own army at the front.

    It hangs over the middle of our troops at the front, never ahead of
    them. Where there are more than three enemy (marines, mostly) to one
    Scout round that point, it holds further back over our army, toward
    the mass. Once the hit begins to fade (half its men gone) the fleet
    is pulled back to its spot to wait for the next hit."""
    if st.fleet_task is not None:
        return None                     # with an ally: "@R bring air" has it
    battle = st.battle
    army = near(forward_units(watch.units(picture), mapdata), battle.front, 14)
    if len(army) < 4:
        # nothing of ours there to cover: once the hit has had time to
        # get there, back to its spot, not left over empty ground. (It
        # is no longer parked just because the hit shrank: trial 26,
        # the air sat out the rest of the hit.)
        if io.now() - battle.sent_at >= HIT_SETTLE:
            park_fleet(io, st, "too few of our troops at the front to cover")
            return "parked"
        return None
    spot = middle(army)
    limit = AIR_ODDS * fleet_scouts(st)
    last = st.fleet_spot
    if last is not None and io.now() - st.fleet_looked < AIR_LOOK_EVERY and \
            max(abs(spot[0] - last[0]), abs(spot[1] - last[1])) < AIR_MOVE_LEAST * 32:
        return last                     # the army has not moved: nothing to do
    st.fleet_looked = io.now()
    # count the enemy on the game screen round where the fleet would go;
    # too many (more than three to a Scout): further back over our army
    for _ in range(4):
        seen, pic = enemy_near_fleet(io, spot)
        if seen <= limit:
            break
        st.fleet_checks += 1
        if st.fleet_checks % 5 == 1:     # now and then, for the record
            io.shot("fleet-too-many")
        io.log(f"fleet: about {seen} enemy near {place_name(mapdata, *spot)}"
               f" (limit {limit}): holding further back")
        spot = toward(spot, MASS, AIR_STEP)
    last = st.fleet_spot
    if last is not None and seen <= limit and \
            max(abs(spot[0] - last[0]), abs(spot[1] - last[1])) < AIR_MOVE_LEAST * 32:
        return spot                     # already there: no new order (each
                                        # one costs clicks; trial 29)
    st.fleet_spot = spot
    set_air_state(io, st, "with the army", "over our troops", target=spot)
    for key in st.air_keys:             # one stack, over our own troops
        io.key(key)
        io.sleep(0.05)
        attack_move(io, *spot)
    return spot


TARGET_NAMES = {"Berlin": "Berlin 1000", "Romania": "Romania 300",
                "Belgrade": "Factory 7", "Warsaw": "Warsaw 200",
                "Konigsberg": "Konigsberg 200", "Krakow": "Krakow 200"}
ENEMY_AT_MASS = 12             # Axis pixels at the mass that mean "defend"
AIR_FOLLOW_EVERY = 8           # seconds between looks at where the air should be
AIR_MOVE_LEAST = 3             # tiles the spot must move before a new order
AIR_LOOK_EVERY = 16            # seconds: the enemy round a still fleet is
                               # counted again this often
RECALL_COOLDOWN = 20           # seconds between recalls of the army
RECALL_AFTER_HIT = 45          # seconds: a hit just sent is not called back
ARRIVED_WITHIN = 6             # minimap pixels from a target that count as there


def recall(io, st, why):
    """Bring the number-key groups back to the massing place."""
    if io.now() - st.last_recall < RECALL_COOLDOWN:
        return False
    st.last_recall = io.now()
    for key in st.ground_keys:
        io.key(key)
        io.sleep(0.05)
        attack_move(io, *MASS)
    if own_fleet_keys(st):
        set_air_state(io, st, "parked", why, target=fleet_spot())
    for key in own_fleet_keys(st):             # the fleet, as one, to its spot
        io.key(key)
        io.sleep(0.05)
        attack_move(io, *fleet_spot())
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


def own_fleet_keys(st):
    """The fleet keys Russia may use for itself: none while the fleet is
    with an ally's air ("@R bring air"), until "@R return air"."""
    return [] if st.fleet_task is not None else list(st.air_keys)


def keys_for(st, group):
    """The keys the general's orders may use: the ground groups only.
    The fleet is steered by its own rules (parking, stacking over the
    army, "@R bring air"): in trial 24 the general's "9 move mass",
    every few seconds, undid them."""
    if group in ("ground", "all"):
        return list(st.ground_keys)
    return [group] if group in st.ground_keys else []


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


# The start of every game (the repository owner): Russia names itself
# to everyone, then opens the Messaging window (the button over the
# minimap with the radio waves), chooses "Send to allies" and accepts,
# so that what it types after goes to the allies only.
OPENING_LINE = "AF Russia AI v0.01"
MESSAGING_BUTTON = (225, 748)  # screen: the right of the two buttons over the minimap
ALLIES_CHOICE = (597, 314)     # the round button of "Send to allies"
ACCEPT_BUTTON = (778, 590)
CHOICE_RINGS = (575, 200, 620, 250)   # round button of "Send to player": blue ring
DIALOG_INSIDE = (1150, 440, 1350, 540)  # inside the window: dark blue
OPENING_TRIES = 2


def messaging_open(picture):
    """True if the Messaging window is on screen: the blue ring of its
    first choice, and its dark blue inside."""
    import numpy as np
    a = np.asarray(picture.convert("RGB")).astype(int)
    l, t, r, b = CHOICE_RINGS
    ring = a[t:b, l:r]
    blue = ((ring[..., 2] > 120) & (ring[..., 0] < 90)).sum()
    l, t, r, b = DIALOG_INSIDE
    R, G, B = a[t:b, l:r].reshape(-1, 3).mean(axis=0)
    return blue >= 80 and B > R + 15 and B > G + 10


def allies_chosen(picture):
    """True if "Send to allies" shows its yellow dot."""
    import numpy as np
    x, y = ALLIES_CHOICE
    a = np.asarray(picture.convert("RGB")).astype(int)[y - 6:y + 7, x - 6:x + 7]
    return int(((a[..., 0] > 180) & (a[..., 1] > 160) & (a[..., 2] < 120)).sum()) >= 40


def opening(io, st, line=None):
    """Before anything else: the name line to everyone, then allied chat
    set in the Messaging window. Returns True if allied chat was set."""
    line = line or OPENING_LINE
    io.key("enter")
    io.sleep(0.15)
    io.type_text(line)
    io.sleep(0.1)
    io.key("enter")
    io.sleep(0.2)
    io.log(f"chat to everyone: {line}")
    for _ in range(OPENING_TRIES):
        io.click(*MESSAGING_BUTTON)
        io.sleep(0.5)
        if not messaging_open(io.shot("messaging", keep=False)):
            io.key("esc")               # whatever opened instead
            io.sleep(0.2)
            continue
        io.click(*ALLIES_CHOICE)
        io.sleep(0.2)
        chosen = allies_chosen(io.shot("messaging"))
        io.click(*ACCEPT_BUTTON)
        io.sleep(0.3)
        if chosen:
            st.allied_chat = True
            io.log("chat: set to allies in the Messaging window")
            return True
    io.shot("messaging-failed")
    io.log("chat: the Messaging window could not be set to allies "
           "(picture 'messaging-failed'); Ctrl+Enter is used for the allies")
    return False


def say(io, st, text, force=False):
    """Type a line to the allies, not too often (announcements of hits
    always go)."""
    text = "".join(c for c in text if " " <= c <= "~")[:60].strip()
    if not text or (not force and io.now() - st.last_chat < CHAT_EVERY):
        return False
    st.last_chat = io.now()
    if st.allied_chat:
        io.key("enter")                 # set to allies at the start
    else:
        io.combo("ctrl", "enter")       # Ctrl+Enter: allies only
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
    # the general may say which way, never which city: east is Berlin,
    # the Balkans Romania (trial 26: "Warsaw" took the whole army there
    # after "gone east" was announced)
    name = road_start(st, name)
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
    need, readings, strength, massed = WANT_HIT, [], 0, 0
    capped, told = False, -99
    while io.now() - t0 < TRIAL_SECONDS:
        relocate_mass(io, watch, mapdata, st)
        collect_new_scouts(io, watch, mapdata, st)
        follow_ally_air(io, watch, mapdata, st)
        air_upkeep(io, watch, mapdata, st)
        orders, picture, still = gather_idle(io, watch, mapdata, st, tried)
        gathered += orders
        st.blind = 0 if live.minimap_showing(picture) else st.blind + 1
        if st.blind >= GAME_OVER_LOOKS:
            st.over = True
            io.log("the minimap has gone: the game seems to be over")
            break
        advance_front(io, watch, mapdata, st, still, picture)
        clear_choke(io, watch, mapdata, st, still, picture)
        # at the start of the cycle, and every few seconds: men of earlier
        # hits idle in the Balkans go on to the road's next stop first
        sweep_balkans(io, watch, mapdata, st, still, picture,
                      force=io.now() - began < 5)
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
        elif st.supply_seen:
            # unreadable this look: the last one, however old (trial 25:
            # with none, the count jumped from 101 to 272 men)
            supply = st.supply_seen[0]
        capped = bool(supply) and supply[0] >= supply[1] - SUPPLY_SLACK
        st.capped = capped
        # How many are there is judged at a glance, with no boxes drawn.
        ours = watch.units(picture)
        massed = men_at_mass(supply, rough, len(ours - mass_pixels))
        if capped and rough >= CAPPED_CROWD:
            # full supply and a real crowd at the mass: this is the army
            # (trial 26: just after a hit, supply was still full with
            # the army gone, and a hit of 22 men followed)
            massed = max(massed, MIN_HIT)
        if rough >= 20:
            st.men_per_pixel = min(6.0, max(0.3, massed / rough))
        # troops forward count toward the next hit only if it goes the
        # same way (trial 25: troops fighting near Konigsberg were counted
        # for a Balkans hit, which went with 28 men)
        reserve = st.reserve if battle and same_front(st, battle, io, t0) \
            else 0
        strength = st.strength = int(massed + reserve * SPREAD_MEN)
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
        tax_order_step(io, watch, mapdata, st, picture)
        upgrade_step(io, mapdata, st)
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
        if supply and need > MIN_HIT:
            # never wait for more than the supply limit can give: the men
            # away from the mass count against it (trial 26: 240 wanted,
            # 136 there, two minutes standing idle)
            can = int(SUPPLY_REACH * (supply[1] - max(0, supply[0] - massed)))
            need = max(MIN_HIT, min(need, can))
        st.need = need
        fresh = massed >= NEW_TROOPS
        ready = fresh and strength >= need
        if ready and battle and io.now() - getattr(st, "hit_sent", -1e9) \
                < HIT_GAP and battle.verdict()[0] not in ("losing", "arrived"):
            ready = False               # the last hit is still going in
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
        # the keys version: all through the massing, the mass goes on
        # keys a dozen at a time, left to right, each moved aside into
        # its place in a line (the repository owner's way)
        if keys_style():
            key_step(io, watch, mapdata, st,
                     target or st.planned_target or road_start(st, next_front_name(st, io, t0)))
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
            spread_at_mass(io, watch, mapdata, st)
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


def next_front(st, io, t0):
    """Which way the next hit is likely to go: where it is planned, else
    Russia's plan for this point of the game."""
    if st.planned_target:
        return team_rules.front_of(st.planned_target)
    seconds = st.clock.time() if st.clock else io.now() - t0
    return "balks" if planned_front(seconds) == "south" else "east"


def next_front_name(st, io, t0):
    return "Romania 300" if next_front(st, io, t0) == "balks" else "Berlin 1000"


def same_front(st, battle, io, t0):
    return team_rules.front_of(battle.target) == next_front(st, io, t0)


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
        if MASS != HOME_MASS:
            st.old_mass = MASS
            st.idle_orders.clear()
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
    if (city["x"], city["y"]) != MASS:
        st.old_mass = MASS              # the army there walks over as one
        st.idle_orders.clear()
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


def status_lines(io, mapdata, st):
    """"@R status": two chat lines, each at most 60 characters:
    "Pop 185/200. Mass: Smolensk." and "Plan: 120/140 men, east. Next
    hit est. 10:50." """
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
    when = team_rules.clock_text(at) if at is not None else "unknown"
    return [f"Pop {pop}. Mass: {mass_name(mapdata)}.",
            f"Plan: {plan}. Next hit est. {when}."]


def say_status(io, mapdata, st):
    for line in status_lines(io, mapdata, st):
        say(io, st, line, force=True)


def reset_orders(io, mapdata, st):
    """"@R reset": every order dropped, mass back at Smolensk, and the
    usual pattern again."""
    global MASS
    if MASS != HOME_MASS:
        st.old_mass = MASS
        st.idle_orders.clear()
    MASS = HOME_MASS
    st.planned_target = st.chosen_target = None
    st.go_pending = False               # (the air is not touched: a fleet
                                        # with an ally stays until "@R
                                        # return air")
    say(io, st, "reset: massing at Smolensk, usual plan", force=True)
    io.log("reset by the allies: massing at Smolensk, usual plan")


RELOCATE_SWEEPS = 4            # passes over the old massing place, at most


def relocate_mass(io, watch, mapdata, st):
    """The massing place has moved: the army standing at the old one is
    swept over to the new one as one body, pass after pass until the old
    place is about empty (not a few groups at a time by the idle pickup,
    which left some behind)."""
    old = st.old_mass
    if old is None:
        return 0
    st.old_mass = None
    orders, start = 0, None
    for _ in range(RELOCATE_SWEEPS):
        n, found = sweep_mass(io, watch, mapdata, st, None, centre=old,
                              dest=MASS)
        orders += n
        start = start or max(found, 1)
        if n == 0 or found < 0.1 * start:
            break
        io.sleep(1.0)
    io.log(f"the army at {place_name(mapdata, *old)} sent to the new massing "
           f"place, {place_name(mapdata, *MASS)}: {orders} groups")
    return orders


# ------------------------------------------------- "@R bring air"
# The repository owner: an ally (teal UK, orange Norway: Wraiths; purple
# France: Scouts) types "@R bring air", and Russia brings its whole
# fleet, by attack-move, to where that ally's air is thickest. Their air
# is their colour over water on the minimap (nothing else can be there);
# failing that, the bot looks for their colour on the move and checks it
# on the game screen. The way there keeps to friendly ground (where our
# side's units and buildings give sight), and where it cannot, passes
# where the fewest enemy buildings (turrets among them) show in the fog.
ALLY_SLOTS = {"teal": 2, "purple": 3, "orange": 4}
SIGHT = 8                      # minimap pixels of sight round our side's things
FOG_COST = 4                   # a step outside our sight costs this many
ENEMY_COST = 6                 # and this much more for each enemy pixel close by
ENEMY_NEAR = 4                 # minimap pixels: how close an enemy building counts
WAYPOINT_EVERY = 25            # minimap pixels between the stops of the way


def _land():
    import numpy as np
    from PIL import Image
    return np.asarray(Image.open(live.data_path("land.png")).convert("L")) > 127


ALLY_AIR = {"orange": ("Wraith", 5), "purple": ("Scout", 5),
            "teal": ("Wraith", 5)}   # the repository owner (trial 31): an air
                               # mass is 5 allied Wraiths or Scouts at least,
                               # all allies' together
# Allied planes on the game screen by their colour, when the model cannot
# count them (trial 31: twenty teal Wraiths, "? teal planes"). Teal only:
# purple is too near the ground's colours and orange the fires'.
AIR_COLOUR_PATCH = 6           # pixels of their colour that may be a plane
AIR_LOOKS_AT = 4               # places looked at for an ally's air at most
NEAR_LAST = 12                 # minimap pixels from where their air was last


def air_places(io, watch, slot):
    """Where an ally's colour shows on the minimap and may be their air:
    over the sea, and what moved between two looks a second apart
    (buildings do not move). Groups, the biggest first."""
    land = _land()
    a = watch.others(io.shot("ally-air", keep=False), [slot])
    sea = {p for p in a if 0 <= p[1] < land.shape[0] and 0 <= p[0] < land.shape[1]
           and not land[p[1], p[0]]}
    io.sleep(1.0)
    b = watch.others(io.shot("ally-air", keep=False), [slot])
    moved = (a ^ b) & b
    moved = {p for p in b if any((p[0] + i, p[1] + j) in moved
                                 for i in (-2, 0, 2) for j in (-2, 0, 2))}
    groups = [g for g in live.clusters(sea | moved, 12, 12) if len(g) >= 2]
    return sorted(groups, key=len, reverse=True)


def count_ally_air(io, st, picture, colour):
    """How many of the ally's Wraiths (orange, teal) or Scouts (purple)
    the game screen shows, or None when it cannot be counted (no API
    key)."""
    kind, _ = ALLY_AIR[colour]
    ears = st.ears if st is not None else None
    if ears is None or not hasattr(ears, "count_air"):
        return None
    return ears.count_air(picture, colour, kind)


def ally_air_by_colour(picture):
    """Allied planes on the game screen counted by colour alone: teal
    patches over the view (the kill list's corner left out).
    Rough, but never nothing when the sky is full of them."""
    import numpy as np
    if picture is None:
        return 0
    l, t, r, b = live.GAME_AREA
    a = np.asarray(picture.convert("RGB").crop((l, t, r, b))).astype(int)
    R, G, B = a[..., 0], a[..., 1], a[..., 2]
    teal = (G > 120) & (B > 100) & (R < 90) & (G - R > 60) & \
        (G - B > 8) & (G - B < 60)      # greener than the beacons' cyan
    teal[:240, :400] = False            # the kill list's corner
    return len([p for p in patches(teal) if p[0] >= AIR_COLOUR_PATCH])


def allied_air_at(io, st, picture, colour):
    """All allied Wraiths and Scouts the screen shows, counted by the
    model, or by their colour when it cannot (or sees fewer)."""
    n = count_ally_air(io, st, picture, colour)
    by_colour = ally_air_by_colour(picture)
    if n is None or by_colour > n:
        why = getattr(st.ears, "last_error", None) if st.ears else "no API key"
        io.log(f"bring air: the model counted "
               f"{'nothing' if n is None else n} ({why or 'no problem'}), "
               f"by colour {by_colour}")
        return by_colour
    return n


def find_ally_air(io, watch, colour, st=None, last=None, recount=False):
    """Where an ally's air is thickest: (map x, map y) or None. Places
    where their colour is over water or moving are looked at on the game
    screen, and their Wraiths (orange, teal) or Scouts (purple) counted
    there: a place with their air mass (orange 8 Wraiths, purple 11
    Scouts, teal 22 Wraiths) is taken at once, else the place with the
    most of them. Dropships and ground units are not their air (trial
    23). Near where their air was `last` seen, no count is needed."""
    slot = ALLY_SLOTS.get(colour)
    if slot is None:
        return None
    kind, mass = ALLY_AIR[colour]
    groups = air_places(io, watch, slot)
    can_count = st is not None and st.ears is not None and \
        hasattr(st.ears, "count_air") and \
        not getattr(st.ears, "dead", lambda: False)()
    if not can_count:
        # no way to count (no API key): their biggest group
        return middle(groups[0]) if groups else None
    if last is not None and not recount:
        lc, lr = live.to_drawn(*last)
        for g in groups:
            c, r = live.to_drawn(*middle(g))
            if abs(c - lc) + abs(r - lr) <= NEAR_LAST:
                return middle(g)
    best, best_n, counted = None, 0, False
    for g in groups[:AIR_LOOKS_AT]:
        x, y = middle(g)
        look_at(io, *centred(x, y), wait=0.3)
        pic = io.shot("ally-air")        # what was taken for their air
        n = count_ally_air(io, st, pic, colour)
        if n is None:
            continue                    # not counted: never taken on trust
                                        # (trial 25: a place with none)
        counted = True
        io.log(f"bring air: {n} {colour} {kind}s near "
               f"{place_name(load_map(), x, y)}")
        if n >= mass:
            return x, y
        if n > best_n:
            best, best_n = (x, y), n
    if counted and best is not None and best_n > 0:
        io.log(f"bring air: no {colour} air mass ({mass} {kind}s) found; "
               f"going to the most, {best_n}")
    return best


def air_route(watch, picture, start, goal):
    """The fleet's way from start to goal (map points), as stops a few
    tiles apart: cheap through friendly ground (within sight of our
    side's units and buildings), dearer through the fog, dearest near
    enemy buildings."""
    import heapq
    import numpy as np
    h, w = _land().shape
    friend = set(watch.units(picture)) | watch.others(picture, [2, 3, 4])
    try:
        rows, cols = np.nonzero(watch.buildings)
        friend |= set(zip(cols.tolist(), rows.tolist()))
    except (AttributeError, TypeError, ValueError):
        pass
    sight = np.zeros((h, w), dtype=bool)
    for c, r in friend:
        sight[max(0, r - SIGHT):r + SIGHT + 1, max(0, c - SIGHT):c + SIGHT + 1] = True
    enemy = np.zeros((h, w), dtype=np.int32)
    for c, r in watch.others(picture, HOSTILE):
        if 0 <= r < h and 0 <= c < w:
            enemy[max(0, r - ENEMY_NEAR):r + ENEMY_NEAR + 1,
                  max(0, c - ENEMY_NEAR):c + ENEMY_NEAR + 1] += 1
    cost = np.where(sight, 1, FOG_COST) + enemy * ENEMY_COST
    sc, sr = (int(v) for v in live.to_drawn(*start))
    gc, gr = (int(v) for v in live.to_drawn(*goal))
    sc, sr = min(max(sc, 0), w - 1), min(max(sr, 0), h - 1)
    gc, gr = min(max(gc, 0), w - 1), min(max(gr, 0), h - 1)
    best = {(sr, sc): 0}
    came = {}
    todo = [(0, sr, sc)]
    while todo:
        d, r, c = heapq.heappop(todo)
        if (r, c) == (gr, gc):
            break
        if d > best.get((r, c), 1e18):
            continue
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1),
                       (1, 1), (1, -1), (-1, 1), (-1, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < h and 0 <= nc < w:
                nd = d + int(cost[nr, nc]) * (1.4 if dr and dc else 1.0)
                if nd < best.get((nr, nc), 1e18):
                    best[(nr, nc)] = nd
                    came[(nr, nc)] = (r, c)
                    heapq.heappush(todo, (nd, nr, nc))
    path, at = [], (gr, gc)
    while at in came:
        path.append(at)
        at = came[at]
    path.reverse()
    stops = path[WAYPOINT_EVERY::WAYPOINT_EVERY]
    if not stops or stops[-1] != (gr, gc):
        stops.append((gr, gc))
    return [live.from_drawn(c, r) for r, c in stops]


def send_fleet(io, watch, st, start, goal):
    """Attack-move every fleet key from start to goal along the safe way:
    the first stop at once, the rest queued (Shift + click). Returns
    the stops."""
    stops = air_route(watch, io.shot("route", keep=False), start, goal)
    for key in st.air_keys:
        io.key(key)
        io.sleep(0.05)
        for k, stop in enumerate(stops):
            io.key("a")
            io.sleep(0.03)
            point = live.minimap_point(*stop)
            if k == 0:
                io.click(*point)
            else:
                io.click_with("shift", *point)   # queued: the next stop
            io.sleep(0.03)
    return stops


ALLY_AIR_CHECK = 8             # seconds between check-ups on the fleet with an ally
ALLY_AIR_MOVED = 6             # minimap pixels the ally's air must move to re-route
ALLY_AIR_RECOUNT = 3           # every third check-up their air is counted again


# The fleet record (the repository owner): at the ping, and at every
# check, the allies' air is written down: the game time, how many of
# which air units of which ally, and where (minimap and nearest place).
# Every 8 seconds Russia looks for it near the last record and follows
# 4 to 6 tiles behind if it roughly matches (within 30%). If it is not
# there, Russia searches at once (not on the timer), around the last
# record on the minimap and by moving the camera, without moving its
# own air; found, the air goes there and a new record is written; not
# found in 10 seconds, "Lost the fleet, still looking" (once): our air
# waits where it is and is searched for again at every check, until
# "@R return air" or until our own air is gone (trial 37).
FLEET_CHECK = 8                # seconds between checks while following
FLEET_MATCH = 0.3              # how far the count may drift and still match
FLEET_BEHIND = 5               # tiles behind the allies' air the fleet stays
FLEET_NEAR = 12                # minimap pixels from the record: "still there"
FLEET_SEARCH = 10              # seconds to search before "Lost the fleet"
                               # (the repository owner: 10, not 30)
SEARCH_RINGS = (10, 20, 32)    # tiles round the last record the camera sweeps
SEARCH_REACH = 40              # minimap pixels round the record searched for groups


def read_fleet(io, st, picture):
    """The allies' air on the screen: [{"owner", "kind", "count"}], or
    None if it cannot be read. The model reads owner and kind; without
    it, teal planes are counted by their colour."""
    if picture is None:
        return None
    ears = st.ears
    groups = None
    if ears is not None and hasattr(ears, "fleet_record"):
        groups = ears.fleet_record(picture)
    if groups is None:
        n = ally_air_by_colour(picture)
        groups = [{"owner": "teal", "kind": "Wraith", "count": n}] if n else []
        if ears is not None:
            io.log(f"bring air: the model could not read the fleet "
                   f"({getattr(ears, 'last_error', None) or 'no answer'}); "
                   f"by colour: {n} teal")
    return groups


def fleet_total(groups):
    return sum(g["count"] for g in groups or [])


def fleet_text(groups):
    if not groups:
        return "none"
    return ", ".join(f"{g['count']} {g['kind']}{'s' if g['count'] != 1 else ''}"
                     f" ({g['owner']})" for g in groups)


def fleet_matches(record, groups):
    """Roughly the same fleet: the total within 30% (units die or join),
    and the same main owner and kind."""
    if not groups or not record:
        return False
    old, new = fleet_total(record["groups"]), fleet_total(groups)
    if abs(new - old) > max(1, FLEET_MATCH * old):
        return False
    main = lambda gs: max(gs, key=lambda g: g["count"])
    a, b = main(record["groups"]), main(groups)
    return a["owner"] == b["owner"] and a["kind"] == b["kind"]


def write_record(io, st, mapdata, groups, xy, picture=True):
    """Write down the allies' fleet: time, units, position (with a
    picture kept at the ping and when it is found again)."""
    clock = team_rules.clock_text(st.clock.time()) if st.clock else \
        f"{io.now():.0f} s"
    c, r = live.to_drawn(*xy)
    rec = {"time": clock, "groups": groups, "xy": xy,
           "place": place_name(mapdata, *xy), "at": io.now()}
    if picture:
        io.shot("fleet-record")
    io.log("FLEET RECORD\n"
           f"* Time: {clock}\n"
           f"* Units: {fleet_total(groups)} in all: {fleet_text(groups)}\n"
           f"* Position: minimap ({int(c)}, {int(r)}), tile "
           f"({int(xy[0] // 32)}, {int(xy[1] // 32)}), near {rec['place']}")
    return rec


def behind(xy, came_from):
    """A point FLEET_BEHIND tiles back from xy toward came_from (where
    the allies' air came from, or our side)."""
    dx, dy = came_from[0] - xy[0], came_from[1] - xy[1]
    d = (dx * dx + dy * dy) ** 0.5
    if d < 1:
        return xy
    k = min(FLEET_BEHIND * 32, d) / d
    return (xy[0] + dx * k, xy[1] + dy * k)


def ally_groups_near(io, watch, xy, reach):
    """Places near xy where the allies' colours show on the minimap and
    may be air (over water or moving): their middles, nearest first."""
    c0, r0 = live.to_drawn(*xy)
    out = []
    for slot in sorted(set(ALLY_SLOTS.values())):
        for g in air_places(io, watch, slot):
            x, y = middle(g)
            c, r = live.to_drawn(x, y)
            d = abs(c - c0) + abs(r - r0)
            if d <= reach:
                out.append((d, (x, y)))
    return [p for _, p in sorted(out)]


def look_fleet(io, st, xy):
    """Look at a map point and read the allies' air there."""
    look_at(io, *centred(*xy), wait=0.3)
    return read_fleet(io, st, io.shot("fleet-look", keep=False))


def follow_to(io, watch, st, task, xy, came_from, route=False):
    """The fleet to a point behind the allies' air."""
    spot = behind(xy, came_from)
    set_air_state(io, st, "following", "the allies' air", target=spot)
    if route:
        send_fleet(io, watch, st, task["spot"], spot)   # by the safe way
    else:
        for key in st.air_keys:
            io.key(key)
            io.sleep(0.05)
            attack_move(io, *spot)
    task["spot"] = spot


def search_fleet(io, watch, mapdata, st, task):
    """The allies' air is not where it was: search at once, around the
    last record, on the minimap and by moving the camera, without
    moving our own air. True once found (the air goes there); after
    FLEET_SEARCH seconds (10), "Lost the fleet" and the air goes home."""
    record = task["record"]
    started = io.now()
    set_air_state(io, st, "searching", "the allies' air moved off")
    io.log(f"bring air: the fleet is not near {record['place']}: searching "
           f"(last seen {record['time']}: {fleet_text(record['groups'])})")
    looked = []

    def fresh(xy):
        return all(abs(xy[0] - p[0]) + abs(xy[1] - p[1]) > 6 * 32 for p in looked)
    rings = [(record["xy"][0] + math.cos(a) * t * 32,
              record["xy"][1] + math.sin(a) * t * 32)
             for t in SEARCH_RINGS for a in [k * math.pi / 4 for k in range(8)]]
    reach = SEARCH_REACH * (2 if task.get("lost") else 1)   # lost: wider
    while io.now() - started < FLEET_SEARCH:
        spots = [p for p in ally_groups_near(io, watch, record["xy"],
                                             reach) if fresh(p)]
        spots = spots[:2] or [p for p in rings if fresh(p)][:1]
        if not spots:
            break
        for xy in spots:
            if io.now() - started >= FLEET_SEARCH:
                break
            looked.append(xy)
            groups = look_fleet(io, st, xy)
            if fleet_matches(record, groups):
                if task.pop("lost", False):
                    say(io, st, "found your air again", force=True)
                task["record"] = write_record(io, st, mapdata, groups, xy)
                follow_to(io, watch, st, task, xy, record["xy"], route=True)
                io.log(f"bring air: the fleet found near "
                       f"{task['record']['place']} after "
                       f"{io.now() - started:.0f} s: our air follows")
                task["checked"] = io.now()
                return True
    # not found: the task stays (the repository owner, trial 37: the air
    # is checked on until "@R return air" or until our air is gone); our
    # air waits where it is and the next check searches again
    task["checked"] = io.now()
    if not task.get("lost"):
        task["lost"] = True
        say(io, st, "Lost the fleet, still looking", force=True)
    io.log(f"bring air: not found in {FLEET_SEARCH} s; looking again in "
           f"{FLEET_CHECK} s (until \"@R return air\")")
    return False


def follow_ally_air(io, watch, mapdata, st):
    """While the fleet is with an ally's air: every 8 seconds, look for
    their air near its last record; roughly the same there, follow 4 to
    6 tiles behind and write a new record; not there, search at once.
    Called from the massing loops, so the massing goes on in between."""
    ping_step(io, watch, mapdata, st)
    task = st.fleet_task
    if task is None or io.now() - task["checked"] < FLEET_CHECK:
        return False
    task["checked"] = io.now()
    if fleet_left(io, st) == 0:
        # the planes are gone: no more following, back to the mass cycle
        st.fleet_task = None
        st.air_home = True
        set_air_state(io, st, "parked", "every Scout lost")
        say(io, st, "my air is gone", force=True)
        io.log("bring air: the fleet has been lost")
        return False
    if task.get("mode") == "attack":
        return attack_ping_step(io, watch, mapdata, st, task)
    record = task.get("record")
    if record is None:
        return False
    # where the record was, or the nearest group of theirs close to it
    near_ = ally_groups_near(io, watch, record["xy"], FLEET_NEAR)
    xy = near_[0] if near_ else record["xy"]
    groups = look_fleet(io, st, xy)
    if not fleet_matches(record, groups):
        return search_fleet(io, watch, mapdata, st, task)
    task["record"] = write_record(io, st, mapdata, groups, xy, picture=False)
    c0, c1 = live.to_drawn(*record["xy"]), live.to_drawn(*xy)
    moved = abs(c0[0] - c1[0]) + abs(c0[1] - c1[1]) >= ALLY_AIR_MOVED
    came_from = record["xy"] if moved else task.get("from", fleet_spot())
    follow_to(io, watch, st, task, xy, came_from, route=moved)
    return True


# "@R bring air" (the repository owner): Russia asks for a ping on the
# map. At a yellow ping it looks at the ground there: the allies' air
# there, it follows it, attacking what is near, by a safe way; mostly
# enemy there, it attacks them, and brings the air back once the place
# is clear; nothing, it says it cannot find their air. Lost planes are
# no longer followed or checked on; the mass cycle goes on throughout.
PING_WAIT = 10                 # seconds to wait for the ping (the repository
                               # owner: then "can't find ping")
PING_LEAST = 24                # new yellow minimap pixels that make a ping
PING_ALLY_AIR = 5              # allied planes there (all allies' Wraiths and
                               # Scouts) that mean "follow them" (trial 31)
PING_ENEMY = 4                 # enemy there that mean "attack them"
PING_CLEAR = 1                 # enemy left there: cleared
PING_LOOK = 10                 # tiles round the ping looked at on the screen


def yellow_on_minimap(picture):
    """The drawn minimap's bright yellow pixels (Spain's colour, and a
    ping)."""
    import numpy as np
    d = live.DRAWN
    a = np.asarray(picture.convert("RGB")).astype(int)[
        d["top"]:d["top"] + d["height"], d["left"]:d["left"] + d["width"]]
    ys, xs = np.nonzero((a[..., 0] > 200) & (a[..., 1] > 200) & (a[..., 2] < 120))
    return set(zip(xs.tolist(), ys.tolist()))


def watch_for_ping(st, picture):
    """Called on every look while a ping is awaited: yellow on the
    minimap that was not there when Russia asked is the ping."""
    ask = st.air_ping
    if ask is None or ask.get("at") is not None or picture is None:
        return
    found = find_ping(picture, ask["base"], with_kind=True)
    now = st.clock.time() if st.clock else 0
    if found is None:
        if ask.get("bars") and now - ask["bars"][1] >= PING_SETTLE:
            ask["at"] = ask["bars"][0]  # the square never showed: the bars'
        return
    at, kind = found
    if kind == "square":
        ask["at"] = at                  # the square: exactly where it is
    elif not ask.get("bars"):
        ask["bars"] = (at, now)         # the bars: wait a moment for the square


PING_SIDE = (8, 45)            # minimap pixels: how wide the ping's square is
PING_HOLLOW = 0.6              # at most this share of its box is yellow
PING_EDGE = 0.8                # at least this share of it on the box's edge
PING_BAR = (7, 25)             # a bar: at most this thick, at least this long
PING_SETTLE = 2                # seconds to wait after the bars for the square


def find_ping(picture, base, with_kind=False):
    """Where a ping is on the minimap (map pixels), or None. A ping is a
    hollow yellow square (the repository owner's recording): new yellow,
    joined up, about as wide as tall, empty inside. Spain's units are
    yellow too but are dots and blobs; the lines a ping starts with sweep
    across the whole map and are not a square yet."""
    from collections import deque
    new = {p for p in yellow_on_minimap(picture)
           if not any((p[0] + i, p[1] + j) in base
                      for i in (-1, 0, 1) for j in (-1, 0, 1))}
    seen, best, bars = set(), None, []
    for p in new:
        if p in seen:
            continue
        part, todo = [], deque([p])
        seen.add(p)
        while todo:
            c, r = todo.popleft()
            part.append((c, r))
            for i in (-2, -1, 0, 1, 2):
                for j in (-2, -1, 0, 1, 2):
                    q = (c + i, r + j)
                    if q in new and q not in seen:
                        seen.add(q)
                        todo.append(q)
        xs, ys = [q[0] for q in part], [q[1] for q in part]
        w, h = max(xs) - min(xs) + 1, max(ys) - min(ys) + 1
        if min(w, h) <= PING_BAR[0] and max(w, h) >= PING_BAR[1]:
            # one of the four bars a ping starts with
            bars.append(("v" if h > w else "h", (min(xs) + max(xs)) / 2,
                         (min(ys) + max(ys)) / 2))
            continue
        if not (PING_SIDE[0] <= w <= PING_SIDE[1] and
                PING_SIDE[0] <= h <= PING_SIDE[1]):
            continue
        if max(w, h) > 1.5 * min(w, h) or len(part) > PING_HOLLOW * w * h:
            continue                    # not square, or filled in
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        edge = sum(1 for c, r in part if min(c - x0, x1 - c, r - y0, y1 - r) <= 5)
        if edge < PING_EDGE * len(part) or len(part) < PING_LEAST:
            continue                    # not an outline: units, not a ping
        if best is None or len(part) > best[0]:
            best = (len(part), ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2))
    if best:
        at = live.from_drawn(*best[1])
        return (at, "square") if with_kind else at
    # the start of a ping: two upright bars and two lying ones closing
    # in on it from all sides; it is between them
    ups = sorted(b[1] for b in bars if b[0] == "v")
    flats = sorted(b[2] for b in bars if b[0] == "h")
    if len(ups) >= 2 and len(flats) >= 2:
        at = live.from_drawn((ups[0] + ups[-1]) / 2, (flats[0] + flats[-1]) / 2)
        return (at, "bars") if with_kind else at
    return None


def fleet_left(io, st):
    """How many planes are left on the fleet keys (each key's Heavy
    Artillery not counted); None if it cannot be told."""
    left, read = 0, False
    entries = {e["key"]: e for e in st.fleet}
    for key in st.air_keys:
        io.key(key)
        io.sleep(0.06)
        pic = io.shot("fleet-count", keep=False)
        if pic is None:
            return None
        read = True
        units, scouts, _ = read_key(st, pic) if HA_BY_PICTURE else \
            (live.selected_count(pic), None, None)
        left += scouts if scouts is not None else \
            max(0, units - on_key(entries.get(key, {})))
    if read:
        air_stats(io, st).count(left, io.now())
    return left if read else None


def bring_air(io, watch, mapdata, st, colour):
    """"@R bring air": ask for a ping, and act on it (ping_step)."""
    if not st.air_keys:
        say(io, st, "I have no air", force=True)
        return False
    pic = io.shot("ping-ask", keep=False)
    st.air_ping = {"colour": colour, "since": io.now(), "at": None,
                   "base": yellow_on_minimap(pic) if pic is not None else set()}
    say(io, st, "ping the map", force=True)
    io.log(f"bring air: {colour} asked; waiting for a ping")
    return True


def ping_step(io, watch, mapdata, st):
    """Once the ping is seen, look at the ground there and decide."""
    ask = st.air_ping
    if ask is None:
        return
    if ask.get("at") is None:
        if io.now() - ask["since"] > PING_WAIT:
            st.air_ping = None
            say(io, st, "can't find ping", force=True)
        return
    st.air_ping = None
    at, colour = ask["at"], ask["colour"]
    cam = look_at(io, *centred(*at), wait=0.3)
    pic = io.shot("ping")
    sx, sy = live.on_screen(at[0], at[1], cam)
    allies = allied_air_at(io, st, pic, colour) if pic is not None else None
    enemies = enemy_on_screen(pic, sx, sy, PING_LOOK * 32 * live.ZOOM) \
        if pic is not None else 0
    io.log(f"bring air: ping near {place_name(mapdata, *at)}: "
           f"{allies if allies is not None else '?'} {colour} planes, "
           f"about {enemies} enemy")
    start = fleet_spot() if st.air_home or not st.battle or \
        not st.battle.front else st.battle.front
    if allies is not None and allies >= PING_ALLY_AIR:
        groups = read_fleet(io, st, pic) or \
            [{"owner": colour, "kind": ALLY_AIR[colour][0], "count": allies}]
        if fleet_total(groups) < PING_ALLY_AIR:
            groups = [{"owner": colour, "kind": ALLY_AIR[colour][0],
                       "count": allies}]
        near_ = ally_groups_near(io, watch, at, FLEET_NEAR)
        xy = near_[0] if near_ else at
        st.fleet_task = {"colour": colour, "spot": start, "since": io.now(),
                         "checked": io.now(), "mode": "follow", "from": start}
        st.fleet_task["record"] = write_record(io, st, mapdata, groups, xy)
        follow_to(io, watch, st, st.fleet_task, xy, start, route=True)
        st.air_home = False
        say(io, st, "following your air", force=True)
        return
    if enemies >= PING_ENEMY:
        send_fleet(io, watch, st, start, at)       # attack-move, safe way
        st.fleet_task = {"colour": colour, "spot": at, "since": io.now(),
                         "checked": io.now(), "mode": "attack"}
        set_air_state(io, st, "fighting", "at the ally's ping", target=at)
        st.air_home = False
        say(io, st, "attacking at your ping", force=True)
        return
    say(io, st, "I can't find your air", force=True)


def attack_ping_step(io, watch, mapdata, st, task):
    """The fleet attacking at a ping: once the place is clear, back it
    comes and the mass cycle has it again."""
    at = task["spot"]
    cam = look_at(io, *centred(*at), wait=0.2)
    pic = io.shot("ping-check", keep=False)
    if pic is None:
        return False
    sx, sy = live.on_screen(at[0], at[1], cam)
    if enemy_on_screen(pic, sx, sy, PING_LOOK * 32 * live.ZOOM) <= PING_CLEAR:
        st.fleet_task = None
        park_fleet(io, st, "the pinged place is clear")
        say(io, st, "area cleared, air coming back", force=True)
        return True
    return False


def return_air(io, mapdata, st):
    """"@R return air": the fleet comes back from the ally's air to its
    spot by the mass, and goes with Russia's hits again."""
    if st.fleet_task is None:
        say(io, st, "my air is already with me", force=True)
        return False
    st.fleet_task = None
    set_air_state(io, st, "parked", "@R return air", target=fleet_spot())
    for key in st.air_keys:
        io.key(key)
        io.sleep(0.05)
        attack_move(io, *fleet_spot())
    st.air_home = True                  # parked until the next hit sends it
    say(io, st, "air coming back", force=True)
    io.log("return air: the fleet called back to its spot")
    return True


# ------------------------------------------------- the air brain (plan step 1-2)
# docs/air-control-plan.md. One place knows what the fleet is doing
# (its state), counts every order it is given, how many Scouts are on
# its keys over time, and writes an air report to the log, to measure
# the air against the best Russia player in the replays (23 to 40
# orders a minute on the air key, moves followed by Hold).
AIR_STATES = ("parked", "travelling", "with the hit", "with the army",
              "following", "searching", "fighting")
AIR_REPORT_EVERY = 300         # seconds between air reports in the log
AIR_UPKEEP = 90                # seconds between looks at the keys and the fleet


class AirStats:
    def __init__(self, now):
        self.t0 = now
        self.orders = {}               # kind -> count
        self.times = []                # when each order was given
        self.counts = []               # (time, Scouts on the keys)
        self.state, self.since = "parked", now
        self.spent = {}                # state -> seconds
        self.target = None             # where the fleet was last sent
        self.seen = None               # (map point, time) the fleet was last seen
        self.fights = []               # (start, Scouts then, end, Scouts then)
        self.reported = now
        self.upkeeps = 0
        self.last_upkeep = now
        self.finds, self.find_time, self.find_misses = 0, 0.0, 0
        self.find_pic = None           # the picture of the last find
        self.scout_at = {}             # fleet key -> (a Scout's picture, of n)

    def order(self, kind, now):
        self.orders[kind] = self.orders.get(kind, 0) + 1
        self.times.append(now)

    def count(self, n, now):
        if n is not None:
            self.counts.append((now, n))


def air_stats(io, st):
    if getattr(st, "air", None) is None:
        st.air = AirStats(io.now())
    return st.air


def set_air_state(io, st, state, why="", target=None):
    """The fleet's state changes (one of AIR_STATES); the time spent in
    each is added up, and a fight's Scouts at its start and end kept."""
    a = air_stats(io, st)
    now = io.now()
    if target is not None:
        a.target = target
    if state == a.state:
        return
    a.spent[a.state] = a.spent.get(a.state, 0) + now - a.since
    n = a.counts[-1][1] if a.counts else None
    if state in ("fighting", "with the hit"):
        a.fights.append([now, n, None, None])
    elif a.state in ("fighting", "with the hit") and a.fights and \
            a.fights[-1][2] is None:
        a.fights[-1][2:] = [now, n]
    io.log(f"air: {a.state} -> {state}" + (f" ({why})" if why else ""))
    a.state, a.since = state, now


def air_report(io, st):
    """The air report: orders a minute and of what kind, Scouts on the
    keys and lost, time in each state, the fights."""
    a = air_stats(io, st)
    now = io.now()
    mins = max((now - a.t0) / 60, 1e-6)
    spent = dict(a.spent)
    spent[a.state] = spent.get(a.state, 0) + now - a.since
    total = sum(a.orders.values())
    holds = a.orders.get("hold", 0)
    lost = sum(max(0, n0 - n1) for (_, n0), (_, n1) in zip(a.counts, a.counts[1:]))
    lines = ["AIR REPORT",
             f"* Orders: {total} in {mins:.1f} min ({total / mins:.1f} a minute; "
             f"target 23 to 40 while fighting): "
             + ", ".join(f"{n} {k}" for k, n in sorted(a.orders.items())),
             f"* Holds after moves: {holds} of {a.orders.get('move', 0)} moves",
             f"* Fleet found by Ctrl+C on a Scout: {a.finds} times"
             + (f", {a.find_time / a.finds:.2f} s each" if a.finds else "")
             + (f"; {a.find_misses} times no Scout was seen where the view "
                f"landed" if a.find_misses else ""),
             "* Scouts on the keys: " + (
                 ", ".join(f"{(t - a.t0) / 60:.0f} min: {n}"
                           for t, n in a.counts[-8:]) or "not counted yet")
             + f"; lost about {lost}",
             "* Time: " + ", ".join(f"{k} {v / 60:.1f} min"
                                    for k, v in sorted(spent.items(),
                                                       key=lambda kv: -kv[1]))]
    for start, n0, end, n1 in a.fights[-6:]:
        lines.append(f"* Fight at {(start - a.t0) / 60:.1f} min: Scouts "
                     f"{n0 if n0 is not None else '?'} -> "
                     f"{n1 if n1 is not None else '(going on)'}")
    io.log("\n".join(lines))
    a.reported = now


def screen_to_map(sx, sy, camera):
    """The map point shown at a screen pixel (on_screen turned round)."""
    return (camera[0] + (sx - live.CENTRE[0]) / live.ZOOM,
            camera[1] + (sy - live.CENTRE[1]) / live.ZOOM)


# Where the fleet is, asked of the game itself (plan phase 1). The owner's
# recording for phase 0 showed two things. Pressing a fleet key twice
# moves the view to the average place of everything on the key, and the
# Heavy Artillery at Moscow pulls that eleven tiles off six Scouts and
# fifteen off four, to the screen's edge or past it. But one Scout picked
# by its small picture, then Ctrl+C, puts that Scout in the middle of the
# view (to half a tile). The Scout and the artillery are told apart by
# their pictures (no mistake in 564 of them).
CENTRED_AT = (966, 424)        # screen point Ctrl+C puts the picked unit on
FIND_GOLD = 200                # screen pixels round it a gold Scout must show
FIND_HOVER = 0.08              # seconds the mouse rests on the picture first
FIND_TRIES = 3                 # looks in a row without a Scout: the fleet is gone


def scout_pictures(pic):
    """(units selected, which of their small pictures are Scouts)."""
    n = live.frames_shown(pic)
    return n, (live.frames_like(pic, n, "scout") if n >= 2 else [])


def where_is_fleet(io, st, quiet=False):
    """The fleet's place (a map point), from the game: a fleet key, one
    Scout's small picture clicked, Ctrl+C, and the white box on the
    minimap read. None if no key shows a Scout, or none is seen where the
    view lands. Leaves one Scout selected: orders press the keys again.
    The picture taken once the view has jumped is kept (air_stats
    .find_pic): the Scout is in its middle, so the fight is read off it.
    Which small picture was a Scout is remembered for each key, so the
    key's pictures are only read again when that one fails."""
    a = air_stats(io, st)
    a.find_pic = None
    st.air_selected = False             # (one Scout is selected after this)
    t0 = io.now()
    for key in st.air_keys:
        mid = pic = None
        for attempt in (0, 1):
            io.key(key)
            # (the key's pictures are read every time, a moment after the
            # key: trial 42, the remembered picture was the gun's once the
            # number on the key had changed, and the look 0.05 s after the
            # key still showed the single unit of before, "no Scouts",
            # which ended a dogfight with seven Scouts alive)
            io.sleep(0.1)
            known = None
            remembered = False
            if known is None:
                look = io.shot("fleet-find", keep=False)
                if look is None:
                    return None
                n, scouts = scout_pictures(look)
                if not scouts:
                    a.scout_at.pop(key, None)
                    break               # its artillery alone, or nothing
                known = a.scout_at[key] = (scouts[0], n)
            x0, y0, x1, y1 = live.frame_box(*known)
            x, y = (x0 + x1) // 2, (y0 + y1) // 2
            if getattr(io, "hover", None) is not None:
                io.hover(x, y)
                io.sleep(FIND_HOVER)
            io.click(x, y)
            io.sleep(0.05)
            io.combo("ctrl", "c")
            io.sleep(0.1)
            pic = io.shot("fleet-found", keep=False)
            at = live.camera_from_minimap(pic) if pic is not None else None
            # (not the artillery: trial 41, the remembered picture had
            # become the gun's after Scouts died, the view went to Moscow,
            # where gold lamps passed for Scouts, and the air was "worked"
            # there for a minute)
            if at is not None and not live.gun_selected(pic) and \
                    gold_on_screen(pic, CENTRED_AT[0], CENTRED_AT[1], FIND_GOLD):
                mid = at
                break
            if remembered:
                # not a Scout in the middle: the remembered picture was
                # wrong (Scouts lost, the pictures moved up): read afresh
                a.scout_at.pop(key, None)
                continue
            if not a.find_misses:
                io.shot("fleet-not-centred")    # (kept once, to see why)
            a.find_misses += 1
            break
        if mid is None:
            continue
        took = io.now() - t0
        a.finds += 1
        a.find_time += took
        a.find_pic = pic
        moved = a.seen is None or \
            abs(mid[0] - a.seen[0][0]) + abs(mid[1] - a.seen[0][1]) > 8 * 32
        a.seen = (mid, io.now())
        if not quiet and (moved or a.finds <= 3):
            io.log(f"air: the fleet is at {int(mid[0] // 32)}, "
                   f"{int(mid[1] // 32)} (a Scout of key {key} centred; "
                   f"{took:.2f} s)")
        return mid
    return None


def view_centred_on(xy):
    """The camera (as live.on_screen takes it) of the view Ctrl+C gives
    with the unit at map point `xy` selected: that unit at CENTRED_AT."""
    return (xy[0] - (CENTRED_AT[0] - live.CENTRE[0]) / live.ZOOM,
            xy[1] - (CENTRED_AT[1] - live.CENTRE[1]) / live.ZOOM)


AA_KEEP = 8                    # tiles the fleet's hops keep from an Axis Missile
                               # Turret the map starts with (its reach is 7)
STRIKE_REACH = 7               # tiles from our army's front within which the
                               # fleet fights; what is farther is left alone
LOITER_BACK = 5                # tiles behind our army's front the fleet waits
LOITER_NEAR = 2                # tiles from that spot: near enough, no order
_turrets = None


def axis_turrets(mapdata):
    """The Missile Turrets the Axis starts with (map points). Some may be
    destroyed by now: then the fleet is only more careful than it need be."""
    global _turrets
    if _turrets is None:
        _turrets = [(b["x"], b["y"]) for slot in HOSTILE
                    for b in mapdata["slots"].get(str(slot), {}).get("buildings", [])
                    if b["type"] == "Missile Turret"]
    return _turrets


def off_turrets(spot, mapdata, keep=AA_KEEP):
    """A map point moved out of every Axis turret's reach (pushed straight
    out from the turret it is nearest to, a few times over)."""
    x, y = spot
    r = keep * 32
    for _ in range(3):
        near_ = [(tx, ty) for tx, ty in axis_turrets(mapdata)
                 if (x - tx) ** 2 + (y - ty) ** 2 < r * r]
        if not near_:
            break
        tx, ty = min(near_, key=lambda t: (x - t[0]) ** 2 + (y - t[1]) ** 2)
        d = ((x - tx) ** 2 + (y - ty) ** 2) ** 0.5 or 1.0
        x, y = tx + (x - tx) / d * (r + 16), ty + (y - ty) / d * (r + 16)
    return (x, y)


def locate_fleet(io, st):
    """Where the fleet really is: asked of the game (where_is_fleet);
    failing that, a look where it was last sent (or its parking spot),
    and the middle of the gold Scouts there."""
    found = where_is_fleet(io, st, quiet=True)
    if found is not None:
        return found
    a = air_stats(io, st)
    guess = a.target or st.fleet_spot or fleet_spot()
    cam = look_at(io, *centred(*guess), wait=0.2)
    pic = io.shot("fleet-where", keep=False)
    if pic is None:
        return None
    sx, sy = live.on_screen(guess[0], guess[1], cam)
    gold = gold_on_screen(pic, sx, sy, 900)
    if not gold:
        io.log(f"air: no Scouts to be seen near "
               f"{place_name(load_map(), *guess)}")
        return None
    mx = sum(p[0] for p in gold) / len(gold)
    my = sum(p[1] for p in gold) / len(gold)
    xy = screen_to_map(mx, my, cam)
    a.seen = (xy, io.now())
    return xy


def replace_ha(io, st, e):
    """A key without the Moscow Heavy Artillery gets it (Shift + key; the
    same gun is on every air key). Tried a few times, then left."""
    if e["key"] in st.ha_keys:          # keyed once: never picked again
        e["ha_dead"] = False
        return False
    tries = st.__dict__.setdefault("ha_tries", {})
    if tries.get(e["key"], 0) >= 3:
        return False
    tries[e["key"]] = tries.get(e["key"], 0) + 1
    if not pick_ha(io, st, *MOSCOW_HA):
        if tries[e["key"]] >= 3:
            io.log(f"air: the Moscow Heavy Artillery could not be picked for "
                   f"key {e['key']}: it goes on with its Scouts alone")
        return False
    add_to_key(io, st, e)
    e["ha"], e["ha_dead"] = MOSCOW_HA, False
    st.ha_keys.add(e["key"])
    io.log(f"air: key {e['key']} got the Moscow Heavy Artillery")
    return True


def air_upkeep(io, watch, mapdata, st):
    """Every AIR_UPKEEP seconds while the fleet is parked or with the
    army: the keys counted, the Heavy Artillery checked now and then,
    and the fleet looked for; the air report every 5 minutes."""
    a = air_stats(io, st)
    now = io.now()
    if now - a.reported >= AIR_REPORT_EVERY:
        air_report(io, st)
    if not st.fleet or now - a.last_upkeep < AIR_UPKEEP or \
            a.state not in ("parked", "with the army"):
        return False
    a.last_upkeep = now
    a.upkeeps += 1
    if choose_park(io, watch, mapdata, st, io.shot("watch", keep=False)) \
            and a.state == "parked":
        park_fleet(io, st, "to its new waiting spot")
    recount_fleet(io, st, force=True)  # also finds keys without their artillery
    for e in st.fleet:
        if e.get("ha_dead"):
            replace_ha(io, st, e)
    where = locate_fleet(io, st)
    if where is not None:
        io.log(f"air: the fleet is near {place_name(mapdata, *where)}")
    return True


# ------------------------------------------------- the dogfight (plan step 3)
# Once most of a hit has been sent, the bot works only the air (the
# repository owner: no taking turns with the ground). Built on the best
# Russia player's bursts in the replays: short bursts of a few orders
# 0.3 to 0.6 s apart, hops of 1 to 3 tiles round the edge of the enemy,
# over our own army (their bursts were 3 to 6 tiles from the ground's
# target), now and then Hold so the Scouts stop and shoot, and about one
# click in nine on an enemy to pick the target. The Scouts are counted
# every few seconds: losing them fast, the fleet steps back; losing half,
# it goes home.
DOGFIGHT = True                # the dogfight after each hit
DOGFIGHT_TIME = 60             # seconds the bot works the air at most
LOITER_LOOK = 1.5              # seconds between looks while there is nothing near
TICK = 0.12                    # seconds between orders within a burst
BURST = 6                      # orders in a burst, then a short pause
BURST_PAUSE = 1.0              # seconds of looking between bursts
HOP = 2                        # tiles a hop goes toward the enemy
STANDOFF = 3                   # tiles the Scouts keep from the nearest enemy
ENGAGE = 9                     # tiles round the fleet where enemies are fought
ANCHOR_REACH = 6               # tiles the fleet may go from over our army
HOLD_EVERY = 3                 # every third hop, then Hold (they stop and shoot)
TARGET_EVERY = 9               # every ninth order, a click on the enemy
COUNT_EVERY = 4                # seconds between counts of the Scouts
LOSING_FAST = 3                # Scouts lost between counts: step back
LOSING_HALF = 0.5              # share of the Scouts left: the fight is lost
QUIET_END = 6                  # looks with no enemy, once it has fought: done
LOST_SIGHT = 15                # seconds without seeing the fleet: done
SCOUT_SPEED = 3.5              # tiles a real second a Scout flies (a guess)
ENEMY_LEAST = 20               # enemy-colour pixels that make one enemy patch
# Cover (the repository owner): the Scouts fight only while enough of our
# ground army stands under them to protect them. Checked on the minimap
# with every count: our pixels round the fleet (less the Scouts' own
# few) against the enemy's there.
COVER_REACH = 7                # minimap pixels round the fleet (about 6 tiles)
COVER_LEAST = 6                # our ground pixels there at the least
COVER_ODDS = 0.5               # and at least half as many as the enemy's
COVER_FLEET = 4                # our pixels the Scouts themselves make there
COVER_THIN = 2                 # counts in a row without cover: home
FLEET_SEEN = 3                 # gold patches together that make the fleet
OWN_GOLD = 150                 # screen pixels round our buildings: their lamps


def own_buildings_on_screen(cam, reach=OWN_GOLD):
    """Our buildings' screen circles for a camera: their gold and red
    lamps are neither Scouts nor enemy."""
    global _own_buildings
    if _own_buildings is None:
        side = load_map()["slots"][SLOT]
        _own_buildings = [(b["x"], b["y"]) for b in side["buildings"]] + \
            [tuple(p) for p in side["structures"]]
    return [(*live.on_screen(x, y, cam), reach) for x, y in _own_buildings]


def sense_fight(picture, fleet_guess, skip=()):
    """On the screen: where the fleet is (the middle of the gold Scouts
    near where it should be), and the enemy patches (their middles).
    Screen points; the fleet None if no Scout is seen. Anything inside
    the `skip` circles (our buildings) is left out."""
    def free(p):
        return all((p[0] - x) ** 2 + (p[1] - y) ** 2 > r * r for x, y, r in skip)
    gold = [p for p in gold_on_screen(picture, fleet_guess[0], fleet_guess[1], 700)
            if free(p)]
    fleet = None
    for g in gold:
        # a fleet is several Scouts together; one gold patch alone may be
        # a walker's lights or a building's lamps (trial 33 pictures)
        near_ = [p for p in gold if (p[0] - g[0]) ** 2
                 + (p[1] - g[1]) ** 2 <= 250 ** 2]
        if len(near_) >= FLEET_SEEN:
            fleet = (sum(p[0] for p in near_) / len(near_),
                     sum(p[1] for p in near_) / len(near_))
            break
    enemies = [(x, y) for n, x, y in patches(enemy_mask(picture))
               if n >= ENEMY_LEAST and free((x, y))]
    return fleet, enemies


def army_anchor(watch, picture, target):
    """Over our own army: the middle of our units nearest the target,
    on the minimap (map point), or None."""
    ours = forward_units(watch.units(picture), load_map()) if watch else set()
    if not ours:
        return None
    tc, tr = live.to_drawn(*target)
    lead = min(ours, key=lambda p: (p[0] - tc) ** 2 + (p[1] - tr) ** 2)
    front = [p for p in ours if abs(p[0] - lead[0]) + abs(p[1] - lead[1]) <= 8]
    return middle(front)


def clamp_to(point, centre, reach):
    """A map point kept within `reach` tiles of centre."""
    dx, dy = point[0] - centre[0], point[1] - centre[1]
    d = (dx * dx + dy * dy) ** 0.5
    if d <= reach * 32:
        return point
    k = reach * 32 / d
    return (centre[0] + dx * k, centre[1] + dy * k)


def order_fleet(io, st, screen_point, hold=False):
    """Every fleet key: a right-click there (a move, or an attack if on
    an enemy), then Hold if asked. A point off the game area is clicked
    on the minimap instead (trial 35: squeezed onto the screen's edge, the
    hops went to its corner)."""
    l, t, r, b = live.GAME_AREA
    x, y = int(screen_point[0]), int(screen_point[1])
    if not (l + 20 < x < r - 20 and t + 20 < y < b - 20):
        cam = getattr(st, "dogfight_cam", None)
        if cam is not None:
            x, y = live.minimap_point(*screen_to_map(x, y, cam))
        else:
            x = min(max(x, l + 30), r - 30)
            y = min(max(y, t + 30), b - 30)
    # (one key alone would be pressed twice running, and the key of what
    # is selected already makes the game jump the view to it: once it is
    # selected it is not pressed again until something else was)
    single = len(st.air_keys) == 1
    for key in st.air_keys:
        if not (single and getattr(st, "air_selected", False)):
            io.key(key)
            io.sleep(0.02)
        io.click(x, y, button="right")
        if hold:
            io.sleep(0.12)
            io.key("h")
    st.air_selected = single
    io.sleep(0.02)


TARGET_PRIORITY = ("battlecruiser", "scv", "bunker")   # the repository
                               # owner: Russia's Scouts shoot Battlecruisers
                               # first, then SCVs by bunkers, then bunkers
TARGET_LOOK = 6                # seconds between the model's looks for them


FOCUS_MAX = 3                  # targets taken from one scan, one at a time
FOCUS_HOLD = 2.5               # seconds on a target with no hops, so the
                               # Scouts shoot it; then a hop back, then the
                               # next (the repository owner: no queueing)


def scan_targets(io, st, picture, fleet, cam):
    """The repository owner: the screen scanned for Battlecruisers, SCVs
    by bunkers and bunkers (the model points them out). All on the
    screen, as map points, Battlecruisers first, then SCVs, then bunkers,
    each kind the nearest first; [] if none; None if the model cannot be
    asked."""
    ears = st.ears
    if ears is None or not hasattr(ears, "find_targets"):
        return None
    return rank_targets(io, ears.find_targets(picture), fleet, cam, picture)


TARGET_REACH = 45              # screen pixels round a target looked at for its colour
TARGET_COLOUR = 6              # Axis-coloured pixels there that make it the enemy's


def axis_mask(picture):
    """The game view's pixels in the Axis team colours: red, blue and a
    pure yellow (Russia's gold Scouts are darker and redder)."""
    import numpy as np
    l, t, r, b = live.GAME_AREA
    a = np.asarray(picture.convert("RGB").crop((l, t, r, b))).astype(int)
    R, G, B = a[..., 0], a[..., 1], a[..., 2]
    yellow = (R > 225) & (G > 225) & (B < 110)
    m = enemy_mask(picture) | yellow
    m[:240, :400] = False               # the kills list
    m[:40, 880:1240] = False            # the round countdown
    return m


def enemy_target(picture, x, y, masks=None):
    """True if a target the model pointed at wears an Axis colour (red,
    blue, yellow) and more of it than Russia's brown (trial 37: the Scouts
    attacked one of our own bunkers). Without a picture: True."""
    if not hasattr(picture, "convert"):
        return True
    axis, own = masks if masks is not None else (axis_mask(picture),
                                                  own_mask(picture))
    l, t = live.GAME_AREA[:2]
    x0, y0 = int(max(0, x - l - TARGET_REACH)), int(max(0, y - t - TARGET_REACH))
    x1, y1 = int(x - l + TARGET_REACH), int(y - t + TARGET_REACH)
    theirs = int(axis[y0:y1, x0:x1].sum())
    ours = int(own[y0:y1, x0:x1].sum())
    return theirs >= TARGET_COLOUR and theirs > ours


def rank_targets(io, found, fleet, cam, picture=None):
    """The model's targets in the order they are shot (see scan_targets):
    only those wearing an Axis colour on the screen."""
    if found is None:
        return None
    rank = {k: i for i, k in enumerate(TARGET_PRIORITY + ("fighter",))}
    near_ = [f for f in found if f["kind"] in rank]   # anywhere on the screen
    if hasattr(picture, "convert") and near_:
        masks = (axis_mask(picture), own_mask(picture))
        ok = [f for f in near_ if enemy_target(picture, f["x"], f["y"], masks)]
        if len(ok) < len(near_):
            io.log(f"dogfight: {len(near_) - len(ok)} target(s) not in an "
                   f"Axis colour left alone (ours or an ally's)")
        near_ = ok
    near_.sort(key=lambda f: (rank[f["kind"]], (f["x"] - fleet[0]) ** 2
                              + (f["y"] - fleet[1]) ** 2))
    if near_:
        io.log("dogfight: targets seen: " + ", ".join(
            f"{sum(1 for f in near_ if f['kind'] == k)} {k}"
            for k in TARGET_PRIORITY + ("fighter",)
            if any(f["kind"] == k for f in near_)))
    return [{"kind": f["kind"], "xy": screen_to_map(f["x"], f["y"], cam)}
            for f in near_]


AIR_SUPERIOR = 2               # our Scouts to one enemy fighter: clearly more
AIR_TOO_MANY = 2               # enemy fighters to one of our Scouts: a large air


def air_first(io, targets, scouts, over_army):
    """The targets in the order they are shot, the enemy's fighters put
    in their place (the owner): attacked first when our Scouts are
    clearly more than they, or when they have come forward over our own
    army; left alone otherwise. With a large enemy air (two fighters to
    one of our Scouts) nothing is attacked: returns None, and the fleet
    keeps back."""
    fighters = [t for t in targets if t["kind"] == "fighter"]
    rest = [t for t in targets if t["kind"] != "fighter"]
    if not fighters:
        return rest
    scouts = max(scouts or 0, 1)
    if len(fighters) >= AIR_TOO_MANY * scouts:
        io.log(f"dogfight: {len(fighters)} enemy fighters to {scouts} "
               f"Scouts: a large air, the fleet keeps back")
        return None
    if scouts >= AIR_SUPERIOR * len(fighters):
        io.log(f"dogfight: {scouts} Scouts to {len(fighters)} enemy "
               f"fighters: they are attacked first")
        return fighters + rest
    if over_army:
        io.log(f"dogfight: {len(fighters)} enemy fighters have come over "
               f"our army: they are attacked first")
        return fighters + rest
    return rest


class Scanner:
    """The model's looks for targets, in the background: the fight goes on
    while it looks (trial 35: each look held the Scouts still 5 s)."""

    def __init__(self, ears):
        from concurrent.futures import ThreadPoolExecutor
        self.ears = ears
        self.pool = ThreadPoolExecutor(1) if ears is not None and \
            hasattr(ears, "find_targets") else None
        self.job = None

    def busy(self):
        return self.job is not None

    def start(self, picture, fleet, cam):
        if self.pool is None or self.job is not None:
            return False
        self.job = (self.pool.submit(self.ears.find_targets, picture), fleet,
                    cam, picture)
        return True

    def result(self, io):
        """The ranked targets once the look is done, else None."""
        if self.job is None or not self.job[0].done():
            return None
        future, fleet, cam, picture = self.job
        self.job = None
        try:
            found = future.result()
        except Exception:
            found = None
        return rank_targets(io, found, fleet, cam, picture) or []

    def close(self):
        if self.pool is not None:
            self.pool.shutdown(wait=False)


def attack_target(io, st, target, cam):
    """Every fleet key: an attack on one target (A, then a click on it).
    False if it is off the screen."""
    l, t, r, b = live.GAME_AREA
    x, y = live.on_screen(*target["xy"], cam)
    if not (l + 10 < x < r - 10 and t + 10 < y < b - 10):
        return False
    for key in st.air_keys:
        io.key(key)
        io.sleep(0.02)
        io.key("a")
        io.sleep(0.02)
        io.click(x, y)
        io.sleep(0.02)
    return True


def ground_cover(watch, picture, fleet_xy):
    """Our ground army under the fleet and the enemy there, as minimap
    pixels: (ours, theirs). None if it cannot be told."""
    if watch is None or picture is None:
        return None
    ours = len(near(watch.units(picture), fleet_xy, COVER_REACH))
    theirs = len(near(watch.others(picture, HOSTILE), fleet_xy, COVER_REACH))
    return max(0, ours - COVER_FLEET), theirs


HIT_GONE = 10                  # our minimap pixels forward of the mass, the
                               # Scouts' own left out: fewer, and the hit is gone
HIT_GONE_AFTER = 8             # seconds into a dogfight before that is judged
HIT_GONE_COUNTS = 2            # counts in a row


def hit_gone(watch, picture, mapdata, fleet_xy):
    """True when hardly any ground troops of ours are forward of the
    massing place any more (trial 40: the third hit was wiped out, supply
    194 to 25, and the fleet stayed out a minute over empty ground).
    None if it cannot be told."""
    if watch is None or picture is None:
        return None
    ours = forward_units(watch.units(picture), mapdata)
    return len(ours) - len(near(ours, fleet_xy, 3)) < HIT_GONE


def covered(cover):
    """Enough of our ground under the Scouts to protect them."""
    if cover is None:
        return True                     # cannot tell: carry on
    ours, theirs = cover
    return ours >= COVER_LEAST and ours >= COVER_ODDS * theirs


def dogfight(io, watch, mapdata, st, target):
    """Work the air alone, once most of the hit has been sent: the
    camera on the fleet, short bursts of hops round the edge of the
    enemy near it, kept over our own army; the Scouts counted every few
    seconds. Ends when the fight is over (no enemy for a while), the
    fleet is lost from sight, half the Scouts are gone, or after
    DOGFIGHT_TIME seconds. Returns how many orders it gave."""
    if not st.air_keys:
        return 0
    w = place(mapdata, target)
    goal = (w["x"], w["y"])
    a = air_stats(io, st)
    dest = a.target or toward(MASS, goal, AIR_LEAD)
    # where it set off from: where it was last seen, else its parking spot
    # (trial 34: looked for where it was going, it was not there yet, and
    # every dogfight ended at once, "the fleet is out of sight")
    origin = where_is_fleet(io, st) or \
        (a.seen[0] if a.seen and io.now() - a.seen[1] < 300 else fleet_spot())
    fleet_xy = origin
    set_air_state(io, st, "fighting", f"dogfight on the way to {target}",
                  target=fleet_xy)
    start = io.now()
    first = fleet_left(io, st) or 0
    last_count, last_n = io.now(), first
    orders = hops = burst = quiet = unseen = 0
    fought = False
    seen_at = io.now()                    # when the fleet was last seen
    last_scan, focus_until = -1e9, -1e9   # the scans for targets
    to_shoot, hop_back = [], False        # targets left from the last scan
    scanner = Scanner(st.ears)
    thin = 0                              # counts in a row without cover
    gone = 0                              # counts in a row with the hit gone
    kept_back = False                     # said once in the log
    why = "time is up"
    while io.now() - start < DOGFIGHT_TIME:
        # Every look asks the game where the fleet is (phase 2; trial 40:
        # looked for by its gold colour, it was "seen" where it was not,
        # and ordered to one spot for a minute). Ctrl+C puts a Scout in
        # the middle of the view, and the fight is read off that picture.
        found = where_is_fleet(io, st, quiet=True)
        if found is None:
            unseen += 1
            if unseen >= FIND_TRIES:
                why = "the fleet is out of sight (no Scout found on its keys)"
                break
            io.sleep(TICK)
            continue
        fleet_xy = found
        cam = view_centred_on(fleet_xy)
        st.dogfight_cam, st.dogfight_look = cam, None
        pic = a.find_pic or io.shot("dogfight", keep=False)
        if pic is None:
            break
        fleet, enemies = sense_fight(pic, CENTRED_AT,
                                     own_buildings_on_screen(cam))
        if fleet is None:
            fleet = CENTRED_AT          # (one or two Scouts: too few to be
                                        # told from lamps by their colour,
                                        # but one of them is there)
        unseen, seen_at = 0, io.now()
        fleet_xy = screen_to_map(fleet[0], fleet[1], cam)
        origin = fleet_xy                   # a later search starts here
        a.seen = (fleet_xy, io.now())
        anchor = army_anchor(watch, pic, goal) or fleet_xy
        # the Scouts counted every few seconds
        if io.now() - last_count >= COUNT_EVERY:
            # our ground under the Scouts: enough to protect them?
            # (judged once it has met the enemy: on the way out it may be
            # over empty ground behind the army)
            cover = ground_cover(watch, pic, fleet_xy) if fought else None
            thin = 0 if covered(cover) else thin + 1
            if thin >= COVER_THIN:
                why = (f"too little of our ground army under the Scouts "
                       f"({cover[0]} of ours to {cover[1]} enemy on the "
                       f"minimap)")
                st.fleet_task = None
                park_fleet(io, st, "dogfight without cover")
                io.log(f"dogfight: {why}: the fleet goes home")
                scanner.close()
                return orders
            # and is there still a hit to fly with? (also before the fleet
            # has met anyone)
            if io.now() - start >= HIT_GONE_AFTER and \
                    hit_gone(watch, pic, mapdata, fleet_xy):
                gone += 1
            else:
                gone = 0
            if gone >= HIT_GONE_COUNTS:
                st.fleet_task = None
                park_fleet(io, st, "the hit is gone")
                io.log("dogfight: hardly any ground troops of ours are "
                       "forward any more: the fleet goes home")
                scanner.close()
                return orders
            n = fleet_left(io, st)
            last_count = io.now()
            if n is not None:
                if first and n <= first * LOSING_HALF:
                    why = f"half the Scouts lost ({n} of {first} left)"
                    st.fleet_task = None
                    park_fleet(io, st, "dogfight lost")
                    io.log(f"dogfight: {why}: the fleet goes home")
                    scanner.close()
                    return orders
                if last_n - n >= LOSING_FAST:
                    back = toward(fleet_xy, MASS, HOP * 2)
                    order_fleet(io, st, live.on_screen(back[0], back[1], cam))
                    orders += 1
                    io.log(f"dogfight: {last_n - n} Scouts lost in "
                           f"{COUNT_EVERY} s: a step back")
                    io.sleep(BURST_PAUSE)
                last_n = n
        reach = ENGAGE * 32 * live.ZOOM
        close = sorted((e for e in enemies
                        if (e[0] - fleet[0]) ** 2 + (e[1] - fleet[1]) ** 2
                        <= reach ** 2),
                       key=lambda e: (e[0] - fleet[0]) ** 2 + (e[1] - fleet[1]) ** 2)
        if close and anchor != fleet_xy:
            # the enemy is fought where our army is, not beyond it
            reach = (STRIKE_REACH * 32) ** 2
            close = [e for e in close
                     if (screen_to_map(e[0], e[1], cam)[0] - anchor[0]) ** 2
                     + (screen_to_map(e[0], e[1], cam)[1] - anchor[1]) ** 2
                     <= reach]
        if not close:
            quiet += 1
            if fought and quiet >= QUIET_END:
                why = "no enemy left near the fleet"
                break
            # nothing near: the fleet waits slightly behind our army's
            # front (the owner), by a plain move, clear of the turrets
            wait_at = off_turrets(toward(anchor, MASS, LOITER_BACK)
                                  if anchor != fleet_xy else fleet_xy, mapdata)
            if (wait_at[0] - fleet_xy[0]) ** 2 + (wait_at[1] - fleet_xy[1]) ** 2 \
                    > (LOITER_NEAR * 32) ** 2:
                order_fleet(io, st, live.on_screen(wait_at[0], wait_at[1], cam))
                orders += 1
            hops += 1
            io.sleep(LOITER_LOOK)
            continue
        fought, quiet = True, 0
        e = close[0]
        e_xy = screen_to_map(e[0], e[1], cam)
        dist = ((e_xy[0] - fleet_xy[0]) ** 2 + (e_xy[1] - fleet_xy[1]) ** 2) ** 0.5 / 32
        if len(close) >= AIR_ODDS * max(last_n or first or 1, 1):
            # far too many near for the Scouts there are (the owner: three
            # to one of our Scouts is a large body; trial 41: seven Scouts
            # flew into the middle of Germany's army after a Battlecruiser
            # and all were lost in 27 s): no targets, the fleet keeps back
            # behind our front
            if not kept_back:
                kept_back = True
                io.log(f"dogfight: {len(close)} enemy near to "
                       f"{last_n or first} Scouts: the fleet keeps back")
            to_shoot, hop_back = [], False
            back = off_turrets(toward(fleet_xy, anchor if anchor != fleet_xy
                                      else MASS, HOP * 2), mapdata)
            order_fleet(io, st, live.on_screen(back[0], back[1], cam))
            orders += 1
            io.sleep(TICK)
            continue
        if io.now() < focus_until:
            io.sleep(TICK)                  # shooting what they were sent at
            continue
        if hop_back:
            # done with that target: a hop back, before the next one
            hop_back = False
            back = clamp_to(toward(fleet_xy, anchor if anchor != fleet_xy
                                   else MASS, HOP), anchor, ANCHOR_REACH)
            order_fleet(io, st, live.on_screen(back[0], back[1], cam))
            orders += 1
            io.sleep(TICK)
            continue
        if not to_shoot:
            got = scanner.result(io)
            if got:
                over_army = anchor != fleet_xy and \
                    (fleet_xy[0] - anchor[0]) ** 2 + (fleet_xy[1] - anchor[1]) ** 2 \
                    <= (ANCHOR_REACH * 32) ** 2
                # only what has come to our own army is attacked (trial 42:
                # fifteen Scouts sent at two fighters over Germany's army
                # lost nine in 13 s)
                reach = (STRIKE_REACH * 32) ** 2
                centre = anchor if anchor != fleet_xy else fleet_xy
                near_us = [t for t in got
                           if (t["xy"][0] - centre[0]) ** 2
                           + (t["xy"][1] - centre[1]) ** 2 <= reach]
                if len(near_us) < len(got):
                    io.log(f"dogfight: {len(got) - len(near_us)} target(s) "
                           f"beyond our army's front left alone")
                got = air_first(io, near_us, last_n or first, over_army)
                if got is None:
                    # a large enemy air: back behind our front, no target
                    back = off_turrets(toward(fleet_xy, anchor if anchor != fleet_xy
                                              else MASS, HOP * 2), mapdata)
                    order_fleet(io, st, live.on_screen(back[0], back[1], cam))
                    orders += 1
                    io.sleep(TICK)
                    continue
                to_shoot = got[:FOCUS_MAX]
            elif not scanner.busy() and io.now() - last_scan >= TARGET_LOOK:
                last_scan = io.now()
                scanner.start(pic, fleet, cam)   # looks while the fight goes on
        while to_shoot:
            # Battlecruisers, then SCVs by bunkers, then bunkers (the
            # repository owner): one at a time, a hop back in between
            aim = to_shoot.pop(0)
            if attack_target(io, st, aim, cam):
                orders += 1
                focus_until, hop_back = io.now() + FOCUS_HOLD, True
                io.log(f"dogfight: focus fire on a {aim['kind']}")
                break
        if hop_back:
            continue
        # none on the screen: on with the hops and Holds
        orders += 1
        if st.ears is None and orders % TARGET_EVERY == 0:
            order_fleet(io, st, e)          # no model to ask: the nearest
        else:
            if dist < STANDOFF:             # too close: a hop back
                spot = toward(fleet_xy, anchor if anchor != fleet_xy else MASS,
                              HOP)
            else:                           # to the edge of the enemy
                spot = toward(fleet_xy, e_xy, min(HOP, dist - STANDOFF))
            spot = off_turrets(clamp_to(spot, anchor, ANCHOR_REACH), mapdata)
            hops += 1
            order_fleet(io, st, live.on_screen(spot[0], spot[1], cam),
                        hold=hops % HOLD_EVERY == 0)
        io.sleep(TICK)                      # (the next look is the pause)
    scanner.close()
    io.log(f"dogfight: {orders} orders in {io.now() - start:.0f} s "
           f"({why})")
    if hit_gone(watch, io.shot("dogfight", keep=False), mapdata, fleet_xy):
        st.fleet_task = None            # nobody left to fly with: home
        park_fleet(io, st, "the hit is gone")
        return orders
    set_air_state(io, st, "with the army", f"dogfight over: {why}",
                  target=fleet_xy)
    return orders


class AirCounting:
    """The game's io, but every order given to the fleet's keys is
    counted for the air report: a fleet key pressed, then a click (a
    move, or an attack with A first), or H (Hold)."""

    def __init__(self, io, st):
        self.io, self.st = io, st
        self.selected, self.pending = False, None

    def __getattr__(self, name):
        return getattr(self.io, name)

    def key(self, name):
        self.io.key(name)
        if name in self.st.air_keys:
            self.selected, self.pending = True, None
        elif self.selected and name == "h":
            air_stats(self.io, self.st).order("hold", self.io.now())
        elif self.selected and name in ("a", "m"):
            self.pending = name
        elif self.selected and name not in ("esc",):
            self.selected = False

    def _clicked(self, button):
        if not self.selected:
            return
        a = air_stats(self.io, self.st)
        if button == "right" or self.pending == "m":
            a.order("move", self.io.now())
        elif self.pending == "a":
            a.order("attack", self.io.now())
        else:
            self.selected = False       # a plain click picks something else
        self.pending = None

    def click(self, x, y, button="left"):
        self.io.click(x, y, button=button)
        self._clicked(button)

    def click_with(self, held, x, y):
        self.io.click_with(held, x, y)
        self._clicked("left")           # a queued stop: A or M came first

    def combo(self, *keys):
        self.io.combo(*keys)
        self.selected = False

    def drag(self, *a, **k):
        self.io.drag(*a, **k)
        self.selected = False


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
    watch_for_ping(st, picture)
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
        said = text.split(":", 1)[-1].strip() if ":" in text else text
        if colour in ALLY_SLOTS and COMMANDS_ASKED.match(said):
            list_commands(io, st)       # read here too: one word is enough
    for order in ears.orders(now):
        st.team.heard(order, now)


# ------------------------------------------------- the allies' new orders
# "@R upgrade" (the repository owner): infantry weapons at one
# Engineering Bay, infantry armor at the other, when there is the money;
# if not, say so and do it once there is.
UPGRADE_COST = [100, 175, 250]  # minerals (and as much gas) for levels 1-3
GAS_FIELD = (1645, 10, 1760, 32)  # the gas figure at the top of the screen
UPGRADES = [("weapons", "w"), ("armor", "a")]   # the Engineering Bay's keys
UPGRADE_EVERY = 15             # seconds between looks at the money for them


def engineering_bays(mapdata):
    return [b for b in mapdata["slots"][SLOT]["buildings"]
            if b["type"] == "Engineering Bay"]


UPGRADE_TIME = 118              # seconds an upgrade takes before the next level


AUTO_UPGRADES = 2              # levels of infantry weapons and armor Russia
                               # takes by itself: the first in the game's
                               # first seconds, the second as soon as the
                               # first is done, about two minutes in (the
                               # best players' replays: at 0:01 to 0:06 and
                               # again at 1:37 to 2:18, in every game)


def upgrade_order(io, mapdata, st):
    """"@R upgrade": infantry weapons and armor, up to 3/3, each level
    as soon as the money allows; then "all upgrades completed"."""
    if st.upgrades_done:
        say(io, st, "all upgrades completed", force=True)
        return
    st.upgrade_asked = True
    st.upgrade_wanted = {name for name, _ in UPGRADES
                         if st.upgrade_level[name] < 3}
    st.last_upgrade_look = -1e9
    if not upgrade_step(io, mapdata, st):
        say(io, st, "I'll upgrade infantry when I have the resources",
            force=True)


def upgrade_step(io, mapdata, st):
    """Start what upgrades the money allows; True if any was started.
    The Engineering Bays are left alone once both are at 3."""
    if st.upgrades_done:
        return False
    if all(st.upgrade_level[n] >= 3 for n, _ in UPGRADES):
        if all(io.now() >= st.upgrade_next.get(n, 0) for n, _ in UPGRADES):
            st.upgrades_done = True     # the last levels have finished
            st.upgrade_wanted = set()
            say(io, st, "all upgrades completed", force=True)
        return False
    if not st.upgrade_wanted or \
            io.now() - st.last_upgrade_look < UPGRADE_EVERY:
        return False
    st.last_upgrade_look = io.now()
    ready = [name for name in st.upgrade_wanted
             if io.now() >= st.upgrade_next.get(name, -1e9)]
    if not ready:
        return False                    # both busy upgrading
    pic = io.shot("money", keep=False)
    money = numbers.read_minerals(pic)
    gas = numbers.read_text(pic, GAS_FIELD)
    gas = int(gas) if gas and gas.isdigit() else None
    bays = engineering_bays(mapdata)
    started = []
    for k, (name, key) in enumerate(UPGRADES):
        if name not in ready:
            continue
        cost = UPGRADE_COST[min(st.upgrade_level[name], 2)]
        if money is None or money - tax_reserve(st) < cost or \
                (gas is not None and gas < cost):
            continue
        # its own Engineering Bay first, the other if that does not take
        # it (trial 30: armor at the second bay never started)
        for bay in ([bays[k]] if k < len(bays) else []) + \
                [b for j, b in enumerate(bays) if j != k]:
            if not select_building(io, bay):
                continue
            io.key(key)                 # weapons (W) or armor (A)
            io.sleep(0.4)
            after = numbers.read_minerals(io.shot("money", keep=False))
            if after is not None and after > money - cost // 2:
                continue                # not taken here
            money = after if after is not None else money - cost
            if gas is not None:
                gas -= cost
            st.upgrade_level[name] += 1
            st.upgrade_next[name] = io.now() + UPGRADE_TIME
            if st.upgrade_level[name] >= (3 if st.upgrade_asked
                                          else AUTO_UPGRADES):
                st.upgrade_wanted.discard(name)
            started.append(f"{name} {st.upgrade_level[name]}")
            break
        else:
            io.log(f"upgrade: infantry {name} did not start")
    if started:
        if st.upgrade_asked:            # (said only when an ally asked)
            say(io, st, "upgrading infantry " + " and ".join(started),
                force=True)
        io.log(f"upgrade: infantry {' and '.join(started)} started")
    return bool(started)


# "@R tax <city>" (the repository owner): a one-time try at a city. With
# enemies there, a detachment of 8 to 12 secures it first. Then an SCV
# from Moscow's command centre builds a depot by the white beacon. Taken:
# the detachment walks back to within 6 tiles of the mass point and the
# SCV goes back to Moscow. Failed: said so, and not tried again until an
# ally asks again.
MOSCOW_CC = (209, 49)           # tiles: Moscow's command centre
ORDER_TAX_SECURE = 120          # seconds the detachment has to clear the city
ORDER_TAX_LEAST = 8             # men in the detachment at least
ORDER_TAX_CLEAR = 1             # enemy pixels by the city that mean it is not
                               # clear: any at all (the repository owner)
ORDER_TAX_HELD = 180            # seconds a strongly held city is waited for
                               # (the repository owner: 3 minutes)
BACK_NEAR = 6                   # tiles from the mass point it walks back to


TAX_GAS = 100                  # a supply depot costs 100 gas too on this map
TAX_PRICE = 150                # an SCV (50) and a supply depot (100)
TAX_MONEY_WAIT = 300           # seconds a tax order waits for that money
MARINE_PRICE = 50


def tax_reserve(st):
    """Minerals kept back for the "@R tax" jobs still to pay their SCV
    and depot: the marines never eat into it (trial 30: they did, and
    the SCV never came)."""
    return TAX_PRICE * sum(1 for j in st.tax_jobs.values()
                           if not j.get("paid"))


def tax_order(io, watch, mapdata, st, order):
    """"@R tax <city>": start the one try at it, if the money for its
    SCV and depot can be kept, with every other city asked for."""
    from bot import places
    name = places.resolve(mapdata, order.place.strip())
    if name is None:
        say(io, st, "I can't find that place", force=True)
        return
    city = place(mapdata, name)
    plain = places.plain(name)
    if not places.walkable(city["x"], city["y"]):
        say(io, st, f"I can't reach {plain}", force=True)
        return
    if name in st.tax_jobs:
        say(io, st, f"still taxing {plain}", force=True)
        return
    pic = io.shot("money", keep=False)
    money = numbers.read_minerals(pic)
    gas = numbers.read_text(pic, GAS_FIELD) if pic is not None else None
    gas = int(gas) if gas and gas.isdigit() else None
    need = tax_reserve(st) + TAX_PRICE
    gas_need = (len(st.tax_jobs) + 1) * TAX_GAS
    if gas is not None and gas < gas_need:
        say(io, st, f"not enough gas to tax {plain}: ask me next tax turn",
            force=True)
        io.log(f"{order.colour} said {order.said!r}: {gas} gas, {gas_need} "
               f"needed (a depot costs {TAX_GAS} gas on this map): not now")
        return
    if money is not None and money < need:
        say(io, st, f"not enough money to tax {plain}: ask me next tax turn",
            force=True)
        io.log(f"{order.colour} said {order.said!r}: {money} minerals, "
               f"{need} needed for every city asked: not now")
        return
    st.depots.pop(name, None)           # a fresh try
    st.depot_tries[name] = 0
    st.tax_jobs[name] = {"city": name, "stage": "secure", "since": io.now(),
                         "guard": False}
    say(io, st, f"taxing {plain}", force=True)
    io.log(f"{order.colour} said {order.said!r}: taxing {name} "
           f"({len(st.tax_jobs)} city(ies) being taxed, "
           f"{tax_reserve(st)} minerals kept for them)")


def tax_order_step(io, watch, mapdata, st, picture):
    """One step of every "@R tax" job, from the massing loop."""
    for name in list(st.tax_jobs):
        tax_job_step(io, watch, mapdata, st, picture, st.tax_jobs[name])


def tax_job_step(io, watch, mapdata, st, picture, job):
    name = job["city"]
    city = place(mapdata, name)
    xy = (city["x"], city["y"])
    ours = watch.units(picture)
    hostile = watch.others(picture, TAX_HOSTILE)
    if job["guard"]:
        st.guards[name] = io.now()      # the detachment stays, not gathered
    if job["stage"] in ("secure", "held"):
        if io.now() - job.get("looked", -1e9) < CITY_LOOK_EVERY:
            return
        job["looked"] = io.now()
        state, enemies = look_city(io, mapdata, name, ours, hostile)
        if state == "clear":
            # seen, and no enemy there: the SCV comes at once, and the
            # detachment (if any) goes back (the repository owner)
            job["stage"], job["since"] = "depot", io.now()
            release_guard(io, watch, mapdata, st, job)
            io.log(f"tax order: {name} seen clear: on to the depot")
            return
        if job["stage"] == "held":
            # trial 32: Warsaw held in strength; it waits for a hit
            if io.now() - job["since"] > ORDER_TAX_HELD:
                return tax_order_end(io, watch, mapdata, st, job, ok=False)
            return
        if enemies > TAX_HEAVY and not job["guard"]:
            hold_tax(io, st, job, name, enemies)   # too strong for a few men
        elif not job["guard"]:
            # not seen (no one of ours there), or a few enemy: a
            # detachment goes to look and to clear it
            n = send_guard(io, watch, mapdata, st, name, picture,
                           why="to look" if state == "unseen" else "")
            if n and n < ORDER_TAX_LEAST and state != "unseen":
                hold_tax(io, st, job, name, enemies, sent=n)
            elif n:
                job["guard"] = True
                job["since"] = io.now()     # its time counts from now
                st.guards[name] = io.now()
        elif io.now() - job["since"] > ORDER_TAX_SECURE:
            return tax_order_end(io, watch, mapdata, st, job, ok=False)
        return
    if job["stage"] == "depot":
        broke = st.__dict__.get("tax_broke", {}).get(name)
        if broke is not None and io.now() - broke > TAX_MONEY_WAIT:
            st.tax_broke.pop(name, None)
            return tax_order_end(io, watch, mapdata, st, job, ok=False)
        if job.get("started") and name not in st.depots and broke is None:
            return tax_order_end(io, watch, mapdata, st, job, ok=False)
        job["started"] = True
        depot_at(io, watch, mapdata, st, name, ours, cc_tile=MOSCOW_CC,
                 then_home=True)
        stage = st.depots.get(name, {}).get("stage")
        if stage == "done":
            # kept back until the depot stands (trial 37: let go once the
            # SCV was ordered, the marines spent it all and the depot
            # could not be paid: "Not enough minerals")
            job["paid"] = True
        if stage == "done":
            return tax_order_end(io, watch, mapdata, st, job, ok=True)
        if stage is None and name not in st.__dict__.get("tax_broke", {}):
            return tax_order_end(io, watch, mapdata, st, job, ok=False)


def release_guard(io, watch, mapdata, st, job):
    """The detachment walks back near the mass point: once the city is
    clear it is not needed there for the SCV (the repository owner)."""
    name = job["city"]
    if not job["guard"]:
        return
    job["guard"] = False
    city = place(mapdata, name)
    pic = io.shot("watch", keep=False)
    there = near(watch.units(pic), (city["x"], city["y"]), TAX_ENEMY + 4)
    back = (MASS[0] + BACK_NEAR // 2 * 32, MASS[1])   # within 6 tiles
    for group in live.clusters(there, 4, 4)[:3]:
        if len(group) >= 2 and select_group(io, group, st, watch, margin=45):
            attack_move(io, *back)
    st.guards.pop(name, None)


CITY_LOOK_EVERY = 6            # seconds between looks at a city being taxed
CITY_LOOK = 8                  # tiles round the beacon looked at on the screen


def look_city(io, mapdata, name, ours, hostile):
    """Is the city clear? "clear" when something of ours is there to see
    it and neither the minimap nor a look at the screen shows any enemy;
    "enemy" when enemies are known there; "unseen" when nothing of ours
    sees it (the minimap does not show enemies in the fog). Also the
    number of enemy minimap pixels there."""
    city = place(mapdata, name)
    xy = (city["x"], city["y"])
    mm = len(near(hostile, xy, TAX_ENEMY))
    if mm >= ORDER_TAX_CLEAR:
        return "enemy", mm
    if not near(ours, xy, TAX_ENEMY):
        return "unseen", 0
    cam = look_at(io, *centred(*xy), wait=0.2)
    pic = io.shot("city-" + name.split()[0], keep=False)
    if pic is None:
        return "unseen", 0
    sx, sy = live.on_screen(xy[0], xy[1], cam)
    e = enemy_on_screen(pic, sx, sy, CITY_LOOK * 32 * live.ZOOM)
    return ("clear", 0) if e == 0 else ("enemy", max(e, ORDER_TAX_CLEAR))


def hold_tax(io, st, job, name, enemies, sent=0):
    """The city is held too strongly for a detachment: the order waits
    (ORDER_TAX_HELD) for it to be cleared by a hit, and the ally is
    told."""
    from bot import places
    job["stage"], job["since"] = "held", io.now()
    say(io, st, f"Axis hold {places.plain(name)}: I'll tax it once it's clear",
        force=True)
    io.log(f"tax order: about {enemies} enemy pixels at {name}"
           + (f", only {sent} men to send" if sent else "")
           + f": waiting up to {ORDER_TAX_HELD} s for it to be cleared")


def tax_order_end(io, watch, mapdata, st, job, ok):
    """The try is over: the detachment walks back near the mass point."""
    from bot import places
    name = job["city"]
    st.tax_jobs.pop(name, None)
    release_guard(io, watch, mapdata, st, job)
    if ok:
        say(io, st, f"{places.plain(name)} taxed", force=True)
        io.log(f"tax order: {name} taken, a depot stands there")
    else:
        say(io, st, f"couldn't tax {places.plain(name)}", force=True)
        io.log(f"tax order: {name} could not be taken; not tried again "
               f"until an ally asks")


def build_id():
    """The commit the app was built from (written by the build), or
    "local"."""
    try:
        with open(live.data_path("build.txt")) as f:
            return f.read().strip()[:12] or "local"
    except OSError:
        return "local"


COMMANDS_ASKED = re.compile(r"\s*@(r|russ|russia)\s+(commands?|help)\b",
                            re.IGNORECASE)
COMMANDS_AGAIN = 30            # seconds before the list is typed again


def list_commands(io, st):
    """"@R commands": every order Russia takes, a line each (once, though
    the chat reader and the model may both pass it on)."""
    if io.now() - getattr(st, "commands_listed", -1e9) < COMMANDS_AGAIN:
        return False
    st.commands_listed = io.now()
    for line in team_rules.COMMANDS:
        say(io, st, line, force=True)
        io.sleep(0.3)
    io.log("commands: the list of orders typed to the allies")
    return True


def run(io, mapdata=None, general=None, save_lessons=None, ears=None):
    """Returns a short result for the log. `save_lessons` is called with
    the general's lessons for the next game, if it wrote any. `ears`
    reads the allies' chat (bot/team.py); without it Russia still
    announces its hits but cannot hear the answers."""
    mapdata = mapdata or load_map()
    io.log(f"build {build_id()}")       # which download this is
    side = mapdata["slots"][SLOT]
    first = io.shot("start")
    watch = live.Watch(first, side["structures"], side["units"])
    if not live.minimap_showing(first) or not watch.ok:
        io.log("The live game's minimap is not on screen. Nothing done.")
        return {"trained": 0, "gathered": 0, "hits": []}
    t0, st = io.now(), State()
    st.general, st.t0 = general, t0
    io = AirCounting(io, st)            # every order to the fleet counted
    air_stats(io, st)
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
        on_status=lambda: say_status(raw, mapdata, st),
        on_reset=lambda: reset_orders(raw, mapdata, st),
        on_bring_air=lambda o: bring_air(raw, st.watch, mapdata, st, o.colour),
        on_return_air=lambda: return_air(raw, mapdata, st),
        on_tax=lambda o: tax_order(raw, st.watch, mapdata, st, o),
        on_upgrade=lambda: upgrade_order(raw, mapdata, st),
        on_commands=lambda: list_commands(raw, st),
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
    st.watch = watch
    st.start_px = watch.units(first)
    since = lambda: f"{io.now() - t0:.0f} s"
    result = {"trained": 0, "gathered": 0, "hits": []}
    try:
        opening(raw, st)                    # name, and allied chat, first
        # infantry weapons and armor in the first seconds, as the best
        # players do in every replay (the next level follows by itself)
        st.upgrade_wanted = {name for name, _ in UPGRADES}
        upgrade_step(io, mapdata, st)
        key_moscow_ha(io, st)               # then at once the gun on 9, 0, 8
        consult(io, watch, mapdata, st)     # the general's say on the opening
        build_fleet(io, mapdata, st)        # before anything moves
        send_scout(io, mapdata, st)
        result["trained"] = train_everywhere(io, mapdata, st,
                                             check_supply=False)
        io.log(f"  ({since()} since start)")
        import random
        rush = random.random() < RUSH_ODDS
        if rush:
            # the first-minute variant of the first hit (the owner: about
            # 2 games in 15): no massing first, the starting army goes
            # straight in and the allies are told at once
            target = st.opening_target or TARGETS[0]
            io.log(f"first hit: the first-minute variant, at {target} "
                   f"(about 2 games in 15)")
            announce(f"gone {team_rules.front_of(target)}")
        result["gathered"] = first_orders(io, watch, mapdata, st, t0,
                                          rush=target if rush else None)
        io.log(f"  ({since()} since start)")
        if not rush:
            wait_for_mass(io, watch, mapdata, st, t0, WAVE_EARLIEST,
                          WAVE_LATEST)
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
        if st.air_keys:
            air_report(io, st)
    result.update({"targets": st.sent_at,
                   "units_per_box": round(st.selected / max(st.selections, 1), 1),
                   "keys": "".join(st.ground_keys + st.air_keys),
                   "boxes": st.boxes, "empty": st.empty})
    return result
