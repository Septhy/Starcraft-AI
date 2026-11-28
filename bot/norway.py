"""Norway (slot 4, orange), version 0.01: the opening.

Built from the sample games (docs/norway-notes.md) and the repository
owner's rules for the first minutes:

- the opening line "AF Norway AI v0.01" to everyone, then allied chat;
- the starting Dropship drops on Shetland at once;
- two SCVs, which wait below the Command Center, are put on key 9 once
  the army has left, and walk to Arkhangelsk in the far north-east, where
  they build ten supply depots (for safety);
- the Factory and the Engineering Bay lifted and floated over Shetland;
- the Starport lifted and flown to Murmansk; the Barracks lifted and
  flown to Finland; the Command Center lifted (once its SCVs are out)
  and landed at Kiruna;
- every starting trooper is put on keys 1 to 5, gathered at Kiruna, and
  attack-moved at the "Russian army-Finland" spot, Factory 10 and
  Helsinki in turn, then at whatever red (Germany) is left in Finland,
  one order a key about every ten seconds;
- the Barracks floats over Finland, by the Heavy Industry (the "Factory
  10" building), well before 3:25 on the round countdown, and lands just
  north of it once Finland is clear and the army has gone on to
  Murmansk (the repository owner's recording: about 2:23): it taxes
  Helsinki and Factory 10;
- then the marines destroy Russia's Starport at Murmansk and Norway's
  Starport lands in its place, taking its Control Tower (if Russia has
  moved it away, Norway's simply lands).

The camera, clicks, building picks, chat and minimap reading are the
Russia bot's (bot/trial.py); nothing of Russia's play is changed.
"""
from eyes import live
from bot import team as team_rules
from bot import trial

SLOT = "4"
OPENING_LINE = "AF Norway AI v0.01"
OPENING_TIME = 900             # real seconds the opening is played at most

T = 32                         # map pixels a tile
SHETLAND = (int(64.3 * T), int(31.5 * T))   # the beacon on Shetland's island
                               # (the owner's recording: where they unloaded.
                               # Trial 60: the middle of the place "Shetland
                               # 300" is open sea, six tiles east of the
                               # island; the Dropship hung there and nobody
                               # got out)
SHETLAND_BOX = (58.5, 28.5, 68.5, 35.5)    # tiles: the island, boxed for its men
SHETLAND_OWNER = "6"           # the slot whose depot and turret stand there
SHETLAND_REACH = 8             # tiles from the beacon its buildings are within
SHETLAND_ATTACKS = 2
SHETLAND_EVERY = 40            # seconds between them
SHETLAND_FLIGHT = 20           # seconds the Dropship needs to get there
KIRUNA_LAND = [(139, 8), (130, 1), (128, 2), (126, 2), (133, 3)]   # Command Center (tiles,
                               # top left), the sample games' spots by Kiruna
DEPOTS_AT = (196, 20)          # tiles: by Arkhangelsk, where the repository
                               # owner built theirs (for safety; trial 40): where
                               # the SCVs walk to, beside the depots' ground
# Where the depots go (a depot's top-left tile, 3 by 2 tiles), by the view
# they are placed from (the screen's top-left tile; rows that would lie
# under the bottom panel need the second view). West of Arkhangelsk's own
# place (tiles 208 to 220, which Russia taxes) and round Russia's two
# depots there, as the owner's were (their recording: about 198 to 207,
# 14 to 27); a tile's gap between them so the SCVs can walk through.
DEPOT_FIELD = [
    ((188, 10), [(201, 14), (197, 14), (205, 14), (201, 11), (197, 11),
                 (205, 11), (201, 17), (205, 17), (197, 17)]),
    ((188, 20), [(202, 22), (198, 22), (202, 25), (198, 25), (206, 25),
                 (206, 22), (198, 28), (202, 28)]),
]
DEPOT_SIZE = (3, 2)            # tiles
DEPOTS = 12                    # the owner (after trial 60): twelve depots
SCVS = 4                       # SCVs made for them (trial 60: two SCVs placed
                               # two depots every 21 s; the owner: faster)
SCV_KEY = "9"                  # the SCVs, from the moment they are found
CC_EXIT = (90.7, 56.4)         # tile point below the Command Center where new
                               # SCVs come out and stand (trials 51-59: both
                               # within a tile of it at 10 and at 18 s)
SCV_BOX = (-3.9, -1.7, 4.3, 2.6)   # tiles round it boxed to take them
SCV_OUT = 12                   # seconds from the order until both are out (the
                               # recordings: about 2.5 s an SCV)
SCV_RETRY = 8                  # seconds between tries to get hold of them
SCV_TRIES = 8                  # tries before the depots are given up
SCV_SLACK = 2.5                # seconds the army must not need the bot for
SCV_WALK = 40                  # seconds from Oslo to Arkhangelsk (the owner's
                               # recording: about 3.6 tiles a second)
SCV_REMADE_WAIT = 12           # seconds the Command Center's lift waits for
                               # two new SCVs if the first were lost
SWEEPS = 2                     # sweeps of the screen for lost SCVs, at most
DEPOT_BUILD = 14               # seconds an SCV is left alone after a depot
                               # order: a few to walk, about 12.5 to build (the
                               # owner's recording: 18 of 250 hit points a second)
FIRST_WALK = 8                 # seconds more after an SCV's first order (it
                               # may still be on its way to Arkhangelsk)
NO_MONEY_WAIT = 6              # seconds before the next try when the depot
                               # could not be picked (100 minerals each)
SCV_BUSY = 2                   # seconds an SCV that showed no build menu (it is
                               # building) is left alone
DEPOT_FAILS = 12               # depot orders that failed in a row: given up
FINLAND = (125, 15, 150, 50)   # tiles: where Germany's buildings in Finland stand
NORTH_ARMY = (95, 0, 160, 33)  # tiles: our starting troops in the north
# The repository owner's way into Finland (their recording, trial 40):
# every starting trooper, Oslo's and Sweden's too, on keys 1 to 5 in the
# first seconds; all gathered at Kiruna; then attack-moved at the
# "Russian army-Finland" spot, then Factory 10, then Helsinki, one order
# a key about every ten seconds; Finland was clear at about 3:28.
ARMY_AREA = (80, 0, 160, 70)   # tiles: where the starting troops stand
ARMY_KEYS = ["1", "2", "3", "4", "5"]
ARMY_STAGES = [                # (tiles, attack?, seconds after the last)
    ((143, 16), False, 0),     # gather at Kiruna
    ((147, 30), True, 5),      # the "Russian army-Finland" spot (owner: 30 s)
    # the owner (trial 47): a wider flank, the marines moved to (147, 31)
    # just 2 s before they attack Germany's bunkers
    ((147, 31), False, 6),     # (trial 51: 8 s, too slow)
    # the owner (trial 49): then further in before the bunkers
    ((143, 34), False, 2),
    ((140, 39), True, 2),      # the east bunker
    ((134, 36), True, 3),      # the west bunker; once the bunkers are down,
                               # straight on to the turrets (clear_buildings)
]
CLEAN_EVERY = 4                # seconds between attacks on the red that is left
                               # (the owner: boxes and attacks every 1-2 s)
ARMY_BOXES = 16                # boxes at most to key the army (each ~1 s;
                               # trial 43: 10 left Narvik's men unkeyed)
GROUP_W, GROUP_H = 20, 8       # tiles: a box's patch of ground (the screen
                               # shows about 26 by 10 tiles)
BUSY_UNTIL = 100               # seconds: the Command Center and the depots wait
                               # for Finland till then (trial 48: they took the
                               # bot away from the fight at 45 and 63 s)
DEPOT_EVERY = 4                # seconds between looks at the depots (an order
                               # goes out when an SCV is free; trial 42: every
                               # 3 s the camera sat on empty ground there)
LOAD_BOX = (-4, -5, 3, 2)      # tiles round the Dropship whose men board it
BARRACKS_WAIT = (127 * T, 22 * T)  # where the Barracks floats till the army
                               # has taken the Finland spot: the Norwegian camp
BARRACKS_SPOT = (149 * T, 39 * T)  # where it floats and lands (the owner,
                               # trial 52: just land it at 149, 39, one click)
BARRACKS_RETRY = 20            # seconds before a landing is tried again
BARRACKS_NEAR = (143 * T, 28 * T)  # where it waits over Finland while the
                               # bunkers stand (trial 52: at 139, 33 the west
                               # bunker shot it down to 60 of 1000)
BARRACKS_IN_AT = 2             # the stage (the attack on the Finland spot) at
                               # which it flies in over Finland (trial 47: at
                               # the move to Helsinki it came too late)
RED = [0]                      # Germany
CLEAR_LOOKS = 2                # looks in a row with no red in Finland: cleared
BARRACKS_BY = 3 * 60 + 25      # the countdown (3:25) by which the Barracks is down
OUT_OF_WAY = 7                 # tiles our men step away from the landing spot
LAND_BUTTON = trial.LIFT_BUTTON  # a lifted building's bottom-right button: Land
KEYS = {"Barracks": "6", "Starport": "7", "Command Center": "8"}
LOOK_EVERY = 3                 # real seconds between looks at Finland
PORT_ASIDE = (148 * T, 16 * T)  # where the army steps to, off the Starport's spot
PORT_WALK = 4                  # seconds it is given to get there
RETRY_PORT = 8                 # real seconds between attacks on Russia's Starport


def norway_buildings(mapdata):
    return {b["type"]: b for b in mapdata["slots"][SLOT]["buildings"]
            if b["type"] not in ("Bunker", "Missile Turret", "Supply Depot")}


PORT_SHIFT = (0, 0)            # tiles off the map entry. Trial 55: the shift of
                               # -3 (from trial 54) aimed at empty ground; the
                               # owner's recording attacks (156, 4), the entry


def russia_starport(mapdata):
    """Russia's Starport at Murmansk (its Control Tower on its right):
    where it stands, a copy of the map's entry."""
    b = next(b for b in mapdata["slots"]["5"]["buildings"]
             if b["type"] == "Starport" and b["y"] < 10 * T)
    return dict(b, x=b["x"] + PORT_SHIFT[0] * T, y=b["y"] + PORT_SHIFT[1] * T)


def heavy_industry(mapdata):
    """The Heavy Industry: the middle of the map's "Factory 10" place."""
    p = trial.place(mapdata, "Factory 10")
    return p["x"], p["y"]


def barracks_spots(mapdata):
    """Where the Barracks lands: the owner (trial 52), just (149, 39), one
    landing click (map pixels of its middle)."""
    return [BARRACKS_SPOT]


def countdown(st):
    """Seconds left on the round countdown (5:00 at the start)."""
    if st.clock is None:
        return None
    return 300 - int(st.clock.time() * trial.COUNTDOWN_RATE) % 300


class State:
    def __init__(self):
        self.allied_chat = False
        self.last_chat = -1e9
        self.clock = None
        self.lifted = {}            # building -> when it was lifted
        self.landed = set()
        self.finland_clear = False
        self.clear_looks = 0
        self.last_look = -1e9
        self.port_tries = 0
        self.last_port = -1e9
        self.depots_ordered = False     # the depots are done with (or given up)
        self.cc_lifted = False
        self.army_keys = []
        self.stage = 0
        self.stage_at = -1e9
        self.last_clean = -1e9
        self.army_px = 0
        self.targets = None            # Germany's buildings in Finland left
        self.barracks_in = False
        self.land_tried = set()
        self.land_clicked = {}          # building -> when it was told to land
        self.cc_look = -1e9
        self.shetland_lifts = False
        self.barracks_over = False
        self.barracks_land_at = -1e9
        self.port_cleared = False
        self.port_gone = False
        self.repaired = 0
        self.last_repair = -1e9
        self.chain, self.chain_at = [], -1e9
        self.depot_look = -1e9
        self.depot_fails = 0
        self.depot_done = set()         # depot spots tried (indices)
        self.depot_built = set()        # depot spots a depot was ordered on
        self.depots_placed = 0
        self.scvs_made = None           # when the SCVs were ordered
        self.scvs_remade = 0
        self.scv_count = 0              # SCVs on SCV_KEY
        self.scv_tries = 0
        self.scv_look = -1e9
        self.scvs_sent = None           # when they set off for Arkhangelsk
        self.scv_busy = [0.0] * SCVS    # until when each SCV is left alone
        self.scv_orders = [0] * SCVS    # depot orders each SCV has had
        self.no_menu_shown = False
        self.sweeps = 0
        self.sweep_speed = SWEEP_SPEED
        self.port_clicked = 0
        self.extras = True              # the Dropships and the mines
        self.shetland_attacks = 0
        self.ship_stage, self.ship_next = "wait", -1e9
        self.ship_tries, self.ship_clear_at = 0, -1e9
        self.drop_stage, self.drop_next = "wait", -1e9
        self.drop_key = self.vulture_key = None
        self.drop_ordered = self.drop_count = self.drop_looks = 0
        self.drop_boardings = 0
        self.drop_quiet = 0
        self.drop_room, self.men_left = [], None
        self.drop_board_at, self.drop_boardable = -1e9, True
        self.mine_stage, self.mine_next = "wait", -1e9
        self.mine_round = self.spawn_tries = self.vulture_count = 0
        self.at = {}                    # building -> tile where it landed
        self.army_held = {}
        # what the Russia bot's box helpers keep count of
        self.boxes = self.empty = self.empty_skipped = 0
        self.scout_frame = None


def lift(io, mapdata, st, kind, dest=None, key=None):
    """Lift one of Norway's buildings (picked where it stands at the
    start), put it on a key if asked, and float it to a map point.
    True if it went up."""
    b = norway_buildings(mapdata).get(kind)
    clear_modes(io)
    if b is None or not pick(io, b):
        io.log(f"norway: the {kind} was not found")
        return False
    io.sleep(0.2)
    if live.move_shown(io.card()):
        # something in the air is selected, not this building on the ground
        # (trial 50: a floating Starport, whose bottom-right button is Land)
        clear_modes(io)
        io.log(f"norway: the {kind} was not picked (something else was)")
        return False
    io.click(*trial.LIFT_BUTTON)
    io.sleep(0.15)
    io.key("l")                         # (the button, and its key, in case)
    io.sleep(0.4)
    if not live.move_shown(io.card()):  # a lifted building shows Move
        io.log(f"norway: the {kind} did not lift")
        return False
    if key:
        io.combo("ctrl", key)
        io.sleep(0.04)
    if dest:
        io.click(*live.minimap_point(*dest), button="right")
        io.sleep(0.05)
    st.lifted[kind] = io.now()
    io.log(f"norway: {kind} lifted" + (f", flying to {dest_name(mapdata, dest)}"
                                       if dest else ""))
    return True


# The landing (or building) footprint: a see-through green tint where the
# ground is free, red where something is in the way (the owner, trial 53).
# Measured in trial 54: green about (28, 90, 20), red about (100, 40, 25),
# grass (29, 34, 16). The bot hovers over a spot, looks, and moves the
# spot a tile at a time until no square is red. It never clicks without
# having seen the footprint (trial 54: unseen, it clicked on red).
FOOTPRINT = {"Barracks": (4, 3), "Starport": (4, 3), "Factory": (4, 3),
             "Command": (4, 3), "Engineering": (4, 3), "depot": (3, 2)}
OUTLINE_RED = 300              # red pixels: a square is red, do not land
NUDGES = [(0, 0), (1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, 1), (1, -1),
          (-1, -1), (2, 0), (-2, 0), (0, 2), (0, -2), (2, 2), (-2, 2), (2, -2),
          (-2, -2)]            # tiles the spot is moved by, nearest first
# The Starport (the owner): its footprint must sit exactly on the Control
# Tower's light green box, or the tower is not taken. So it is never moved
# off the spot found from the box.
EXACT_KINDS = ("Starport",)
PORT_MOUSE = (156, 5)          # tile the mouse is put on to land the Starport
                               # (the owner, after trial 56: "put the mouse
                               # cursor exactly on (156, 5)"); it is not moved


def footprint_size(label):
    for name, size in FOOTPRINT.items():
        if name.lower() in label.lower():
            return size
    return (4, 3)


FOOTPRINT_SEEN = 0.5           # share of a footprint-sized box tinted: it is there
ALIGN_TRIES = 3                # mouse corrections to bring the footprint onto a spot


def tints(a):
    """Masks of the footprint's green and red tint in an RGB array (the
    box's bright green lines, G over 145, are left out)."""
    R, G, B = a[..., 0], a[..., 1], a[..., 2]
    green = (G > 70) & (G < 145) & (G > R + 35) & (G > B + 45)
    red = (R > 70) & (G * 100 < R * 55) & (B * 100 < R * 50)
    return green, red


def footprint_at(picture, sx, sy, size=(4, 3)):
    """Where the game draws the footprint near a screen point: (left, top,
    right, bottom, red pixels inside), or None. Trial 56: the footprint is
    not centred on the mouse (it stood 2 tiles right and 1 down of it), so
    it is found in the picture: the footprint-sized box with the most tint."""
    import numpy as np
    tile = 32 * live.ZOOM
    w, h = int(size[0] * tile), int(size[1] * tile)
    l, t, r, b = live.GAME_AREA
    x0, y0 = max(l, int(sx - w - 2 * tile)), max(t, int(sy - h - 2 * tile))
    x1, y1 = min(r, int(sx + w + 2 * tile)), min(b, int(sy + h + 2 * tile))
    if x1 - x0 <= w or y1 - y0 <= h:
        return None
    a = np.asarray(picture.convert("RGB").crop((x0, y0, x1, y1))).astype(int)
    green, red = tints(a)
    m = (green | red).astype(np.int64)
    I = np.pad(m.cumsum(0).cumsum(1), ((1, 0), (1, 0)))
    sums = I[h:, w:] - I[:-h, w:] - I[h:, :-w] + I[:-h, :-w]
    j, i = np.unravel_index(int(sums.argmax()), sums.shape)
    if sums[j, i] < FOOTPRINT_SEEN * w * h:
        return None
    reds = int(red[j:j + h, i:i + w].sum())
    return (x0 + int(i), y0 + int(j), x0 + int(i) + w, y0 + int(j) + h, reds)


def outline_colour(picture, sx, sy, size=(4, 3)):
    """"green" (no square red), "red" (some square red) or None (no
    footprint seen) for the footprint drawn near a screen point."""
    fp = footprint_at(picture, sx, sy, size)
    if fp is None:
        return None
    return "red" if fp[4] >= OUTLINE_RED else "green"


def aligned(io, cx, cy, label, size):
    """Move the mouse until the footprint's middle is within half a tile
    of (cx, cy). The game hangs the footprint from the tile under the
    mouse (its top-left tile), so the mouse starts on that tile; if the
    footprint is read elsewhere the mouse is moved by what it is off and
    it is read again. (mouse point, footprint read at that point), or
    (None, None) if none is seen or it will not settle."""
    tile = 32 * live.ZOOM
    mx = cx - (size[0] - 1) * tile / 2
    my = cy - (size[1] - 1) * tile / 2
    for _ in range(ALIGN_TRIES):
        io.hover(int(mx), int(my))
        io.sleep(0.15)
        fp = footprint_at(io.shot(label, keep=False), cx, cy, size)
        if fp is None:
            return None, None
        ox = cx - (fp[0] + fp[2]) / 2
        oy = cy - (fp[1] + fp[3]) / 2
        if abs(ox) <= tile / 2 + 2 and abs(oy) <= tile / 2 + 2:
            return (int(mx), int(my)), fp
        mx, my = mx + ox, my + oy
    return None, None


def green_spot(io, sx, sy, label, nudges=None, fixed=False):
    """With a building's footprint on the cursor (placing or landing):
    bring the footprint onto the spot and the spots round it, a tile at a
    time, until it shows no red square. The mouse point to click, or None
    (red all round, or no footprint seen: never click blind). Without a
    way to hover (tests), the spot itself."""
    if getattr(io, "hover", None) is None:
        return sx, sy
    l, t, r, b = live.GAME_AREA
    tile = 32 * live.ZOOM
    size = footprint_size(label)
    seen = []
    for dx, dy in nudges or NUDGES:
        x, y = sx + dx * tile, sy + dy * tile
        if not (l + 40 < x < r - 40 and t + 40 < y < b - 40):
            continue
        try:
            if fixed:                   # the mouse stays where it is put
                io.hover(int(x), int(y))
                io.sleep(0.15)
                mouse = (int(x), int(y))
                fp = footprint_at(io.shot(label, keep=False), x, y, size)
            else:
                mouse, fp = aligned(io, x, y, label, size)
        except Exception:
            return None
        colour = None if fp is None else (
            "red" if fp[4] >= OUTLINE_RED else "green")
        seen.append(colour)
        if colour == "green":
            if (dx, dy) != (0, 0):
                io.log(f"norway: {label}: red where aimed, green {dx}, {dy} "
                       f"tiles off: landing there")
            if mouse != (int(x), int(y)):
                io.log(f"norway: {label}: the mouse at {mouse} puts the "
                       f"footprint on the spot")
            return mouse
        if colour is None and (dx, dy) == (0, 0):
            break                       # no footprint seen: do not click
    io.shot(label + "-red")
    if seen and seen[0] is None:
        io.log(f"norway: {label}: no footprint seen under the cursor, not "
               f"clicking (picture '{label}-red')")
    else:
        io.log(f"norway: {label}: the footprint stayed red round the spot "
               f"(picture '{label}-red')")
    return None


# Where the Starport must land to take the Control Tower: the game draws a
# thin bright green box there, 4 x 3 tiles (the owner's recording; line
# colour about (30, 150, 30) to (60, 240, 70)). The Starport's tinted
# footprint is lined up with it: the click is the box's middle.
TOWER_LOOK = 6                 # tiles round the spot the box is looked for in
TOWER_SIZE = (4, 3)            # tiles: the box is a Starport's size
TOWER_SLACK = 0.5              # tiles the box's size may be off by


def tower_box(picture, sx, sy):
    """The bright green box near the screen point: (left, top, right,
    bottom) in screen pixels, or None."""
    import numpy as np
    tile = 32 * live.ZOOM
    half = TOWER_LOOK * tile
    l, t, r, b = live.GAME_AREA
    x0, y0 = max(l, int(sx - half)), max(t, int(sy - half))
    x1, y1 = min(r, int(sx + half)), min(b, int(sy + half))
    a = np.asarray(picture.convert("RGB").crop((x0, y0, x1, y1))).astype(int)
    R, G, B = a[..., 0], a[..., 1], a[..., 2]
    line = (G > 140) & (G > R + 80) & (G > B + 80)
    def lines(counts, length, want, centre):
        """The pair of long lines `want` tiles apart nearest `centre`."""
        idx = np.nonzero(counts >= length)[0]
        runs = []
        for i in idx:                   # neighbouring pixels: one line
            if runs and i - runs[-1][-1] <= 3:
                runs[-1].append(int(i))
            else:
                runs.append([int(i)])
        ends = [(run[0], run[-1]) for run in runs]
        best = None
        for i, (a0, _) in enumerate(ends):
            for _, b1 in ends[i + 1:]:
                if abs((b1 - a0) / tile - want) <= TOWER_SLACK:
                    d = abs((a0 + b1) / 2 - centre)
                    if best is None or d < best[0]:
                        best = (d, a0, b1)
        return best

    rows = lines(line.sum(axis=1), 1.5 * tile, TOWER_SIZE[1], sy - y0)
    cols = lines(line.sum(axis=0), 1.0 * tile, TOWER_SIZE[0], sx - x0)
    if rows is None or cols is None:
        return None
    return (x0 + cols[1], y0 + rows[1], x0 + cols[2], y0 + rows[2])


def port_spot(io, sx, sy, quiet=False):
    """The Starport on the light green box, the owner's way (their
    recording: Land, then a click with the mouse near the box's top-left
    corner). The game puts a landing building's top-left tile under the
    mouse (trials 56, 57: with the mouse on the box's middle, or on
    (156, 5), the footprint stood 2 tiles right of the box). So the mouse
    goes on the box's top-left tile, and is moved once more if the
    footprint is still off. The mouse point, "red" if the footprint there
    shows red, or None if no box is seen."""
    if getattr(io, "hover", None) is None:
        return None
    tile = 32 * live.ZOOM
    io.hover(int(sx), int(sy))
    io.sleep(0.15)
    try:
        box = tower_box(io.shot("land-tower", keep=False), sx, sy)
    except Exception:
        box = None
    if box is None:
        if not quiet:
            io.log("norway: land-starport: no light green box seen, the "
                   f"mouse goes on {PORT_MOUSE}")
        return None
    mx, my = box[0] + tile / 2, box[1] + tile / 2
    fp = None
    for _ in range(ALIGN_TRIES):
        io.hover(int(mx), int(my))
        io.sleep(0.15)
        fp = footprint_at(io.shot("land-starport", keep=False),
                          (box[0] + box[2]) / 2, (box[1] + box[3]) / 2)
        if fp is None:
            break
        ox, oy = box[0] - fp[0], box[1] - fp[1]
        if abs(ox) <= tile / 3 and abs(oy) <= tile / 3:
            break
        mx, my = mx + ox, my + oy
    if fp is not None and fp[4] >= OUTLINE_RED:
        io.shot("land-starport-red")
        io.log("norway: land-starport: on the light green box, but red "
               "shows (picture 'land-starport-red')")
        return "red"
    io.log(f"norway: land-starport: the mouse at {int(mx)}, {int(my)} puts "
           f"the Starport on the light green box")
    return int(mx), int(my)


def tower_spot(io, sx, sy, label):
    """The Starport hovered over Russia's spot: if the tower's light green
    box shows, the screen point that puts the Starport's footprint level
    with it; else the spot itself."""
    hover = getattr(io, "hover", None)
    if hover is None:
        return sx, sy
    hover(int(sx), int(sy))
    io.sleep(0.12)
    try:
        box = tower_box(io.shot(label, keep=False), sx, sy)
    except Exception:
        return sx, sy
    if box is None:
        io.log(f"norway: {label}: no light green box seen, "
               f"landing on Russia's Starport's spot")
        return sx, sy
    x, y = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
    io.log(f"norway: {label}: lined up on the light green box "
           f"({int(x - sx)}, {int(y - sy)} px off Russia's Starport's spot)")
    return int(x), int(y)


def clear_modes(io):
    """Out of any placing or targeting mode (Esc twice)."""
    io.key("esc")
    io.sleep(0.08)
    io.key("esc")
    io.sleep(0.08)


def is_down(io, key):
    """True if the building on `key` has landed: pressed, and read twice a
    moment apart, its card shows a building's buttons, not Move (trial 50:
    one quick read still showed the SCV's build menu)."""
    io.key(key)
    io.sleep(0.25)
    if not live.building_card(io.card()):
        return False
    io.sleep(0.25)
    return live.building_card(io.card())


BUILDING_SPEED = 0.75          # tiles a second a lifted building flies (trial
                               # 60: the Command Center, 68 tiles in about 90 s)
LAND_SETTLE = 15               # seconds after a landing click before another
LAND_SLACK = 15                # seconds past its flight time before another
LAND_LOOK = 5                  # seconds between looks whether it is down


def cc_due(mapdata, st):
    """When the Command Center, told to land by Kiruna, should be down at
    the latest (its flight from home, and some slack)."""
    cc = norway_buildings(mapdata).get("Command Center")
    if cc is None or "Command Center" not in st.lifted:
        return -1e9
    tx, ty = KIRUNA_LAND[0]
    d = ((cc["x"] / T - tx) ** 2 + (cc["y"] / T - ty) ** 2) ** 0.5
    return st.lifted["Command Center"] + d / BUILDING_SPEED + LAND_SLACK


def dest_name(mapdata, xy):
    return trial.place_name(mapdata, *xy) if xy else "-"


def land(io, kind, spots, st):
    """Land a lifted building (on its key) at the first of `spots` (map
    pixels of its middle) the game takes. True if it is down: once it
    has landed the key shows a building, not Move."""
    key = KEYS[kind]
    l, t, r, b = live.GAME_AREA
    clear_modes(io)
    for x, y in spots:
        if kind in st.land_tried and is_down(io, key):
            st.landed.add(kind)
            return True                 # down already (from an earlier try)
        io.key(key)
        io.sleep(0.15)
        if not live.move_shown(io.card()):
            return False                # the key does not hold it in the air
        cam = trial.look_at(io, *trial.centred(x, y), wait=0.25)
        sx, sy = live.on_screen(x, y, cam)
        if not (l + 40 < sx < r - 40 and t + 40 < sy < b - 40):
            continue
        # (where the screen really is, to note where it lands)
        view = live.view_after_click(*live.minimap_point(*trial.centred(x, y)))
        io.click(*LAND_BUTTON)
        io.sleep(0.15)
        exact = kind in EXACT_KINDS
        spot = port_spot(io, sx, sy) if exact else None
        if spot is None:
            spot = green_spot(io, sx, sy, "land-" + kind.split()[0].lower(),
                              nudges=[(0, 0)] if exact else None, fixed=exact)
        elif spot == "red":
            spot = None
        if spot is None:
            clear_modes(io)
            continue
        io.click(*spot)
        io.sleep(0.3)
        if live.placing_shown(io.card()):
            clear_modes(io)             # refused there: the next spot
            continue
        st.land_tried.add(kind)
        st.land_clicked[kind] = io.now()
        # where it comes down, for later (the repair): the footprint hangs
        # from the tile under the mouse, and this is its middle
        size = footprint_size("land-" + kind)
        st.at[kind] = (view[0] + spot[0] // live.TILE_PX + size[0] / 2,
                       view[1] + spot[1] // live.TILE_PX + size[1] / 2)
        io.log(f"norway: {kind} told to land by {x // T}, {y // T} (one "
               f"click; it comes down when it gets there)")
        # One accepted click is the whole landing (the owner, trial 60:
        # the Command Center, still a minute's flight away, was given a
        # new spot every few seconds and came down a minute late). The
        # building flies there and lands; the caller only looks, later,
        # whether it is down.
        if is_down(io, key):
            st.landed.add(kind)
            io.log(f"norway: {kind} landed by {x // T}, {y // T}")
            return True
        return False
    return False


# ------------------------------------------------------------ the exact view
# (After trial 59.) Where a click on the minimap really puts the screen is
# known to the tile (live.view_after_click). Norway uses it wherever one
# thing has to be clicked or a building put on a chosen tile; the Russia
# bot's camera helpers stay as they are for its own play.
FREE_MIDDLE = (960, 400)       # the middle of the screen that is free of panels


def look(io, tx, ty, at=FREE_MIDDLE, wait=0.25):
    """Move the view so that tile point (tx, ty) comes near screen point
    `at` (the view moves in steps of two tiles, so within a tile of it).
    The view (left, top) in tiles, for live.tile_xy."""
    px, py = live.click_for_view(tx - at[0] / live.TILE_PX,
                                 ty - at[1] / live.TILE_PX)
    io.click(px, py)
    io.sleep(wait)
    return live.view_after_click(px, py)


def look_at_view(io, view, wait=0.25):
    """Move the view to a known top-left tile."""
    io.click(*live.click_for_view(*view))
    io.sleep(wait)
    return live.view_after_click(*live.click_for_view(*view))


def on_view(tx, ty, view):
    """Screen pixel (whole numbers) of a tile point in a view."""
    x, y = live.tile_xy(tx, ty, view)
    return int(round(x)), int(round(y))


def in_free_area(x, y, margin=30):
    l, t, r, b = live.GAME_AREA
    return l + margin < x < r - margin and t + margin < y < b - margin


def pick(io, b):
    """Click one of our buildings where it stands, with the exact view
    (one click); if that does not show a building's buttons, the Russia
    bot's way (several tries round where it thinks the building is)."""
    tx, ty = b["x"] / T, b["y"] / T
    view = look(io, tx, ty)
    x, y = on_view(tx, ty, view)
    if in_free_area(x, y, 5):
        io.click(x, y)
        io.sleep(0.12)
        if live.building_card(io.card()):
            return True
    return trial.pick_building(io, b)


# ------------------------------------------------------- the Shetland drop
LOAD_WAIT = 1.0                # seconds the men are given to walk in
UNLOAD_TRIES = 2


def drop_on_shetland(io, mapdata):
    """The starting Dropship takes the men beside it and unloads them on
    Shetland: the men boxed and right-clicked onto it, the Dropship clicked,
    U, then a click on Shetland on the minimap.

    Trials 51 to 59 (found in the recordings): the right-click and the
    click were aimed with the Russia bot's camera, two tiles above the
    Dropship, so nobody boarded, the Dropship was never picked on its own,
    U did nothing, and the click on the minimap only moved the view. Then
    the army's box took the Dropship along to Finland."""
    d = next((a for a in mapdata["slots"][SLOT]["air"]
              if a["type"] == "Dropship"), None)
    if d is None:
        return False
    tx, ty = d["x"] / T, d["y"] / T
    view = look(io, tx, ty, wait=0.2)
    l, t, r, b = live.GAME_AREA
    x0, y0, x1, y1 = LOAD_BOX
    a = on_view(tx + x0, ty + y0, view)
    z = on_view(tx + x1, ty + y1, view)
    box = (max(l + 3, a[0]), max(t + 3, a[1]), min(r - 3, z[0]), min(b - 3, z[1]))
    ship = on_view(tx, ty, view)
    if box[2] - box[0] > 20 and box[3] - box[1] > 20:
        io.drag(*box)
        io.sleep(0.1)
        io.click(*ship, button="right")     # the men walk in
        io.sleep(LOAD_WAIT)
    for attempt in range(UNLOAD_TRIES):
        io.click(*ship)                     # the Dropship alone
        io.sleep(0.12)
        if not live.move_shown(io.card()):
            io.sleep(0.4)
            continue
        io.key("u")                         # unload: a target is asked for
        io.sleep(0.12)                      # (only Cancel shows) if anyone
        if live.placing_shown(io.card()):   # is aboard
            io.click(*live.mm_point(SHETLAND[0] / T, SHETLAND[1] / T))
            io.sleep(0.05)
            io.log("norway: the Dropship goes to unload on Shetland")
            return True
        io.sleep(0.5)                       # nobody aboard yet: once more
    clear_modes(io)
    io.log("norway: the Dropship was not sent to Shetland (it was not "
           "picked, or nobody had boarded)")
    return False


def shetland_buildings(mapdata):
    """The enemy's buildings on Shetland's island (tile points), those
    that shoot first."""
    bx, by = SHETLAND[0] / T, SHETLAND[1] / T
    out = [(b["type"], b["x"] / T, b["y"] / T)
           for b in mapdata["slots"].get(SHETLAND_OWNER, {}).get("buildings", [])
           if abs(b["x"] / T - bx) <= SHETLAND_REACH and
           abs(b["y"] / T - by) <= SHETLAND_REACH]
    out.sort(key=lambda b: b[0] not in FIRST_KINDS)
    return out


def attack_on_shetland(io, mapdata):
    """The men dropped on Shetland attack its buildings in turn (the
    owner's game: the island's turret and depot were down before their
    Factory floated in). The island is boxed, then A and a click on each
    building, the later ones queued with Shift. True if ordered."""
    targets = shetland_buildings(mapdata)
    if not targets:
        return False
    clear_modes(io)
    view = look(io, SHETLAND[0] / T, SHETLAND[1] / T)
    x0, y0, x1, y1 = SHETLAND_BOX
    a, z = on_view(x0, y0, view), on_view(x1, y1, view)
    l, t, r, b = live.GAME_AREA
    io.drag(max(l + 4, a[0]), max(t + 4, a[1]), min(r - 4, z[0]), min(b - 4, z[1]))
    io.sleep(0.15)
    if not live.move_shown(io.card()):
        io.shot("shetland-nobody")
        io.log("norway: nobody of ours seen on Shetland (picture "
               "'shetland-nobody')")
        return False
    first = True
    for kind, tx, ty in targets:
        x, y = on_view(tx, ty, view)
        if not in_free_area(x, y, 5):
            continue
        if first:
            io.key("a")
            io.sleep(0.05)
            io.click(x, y)
        else:
            io.combo("shift", "a")
            io.sleep(0.05)
            io.click_with("shift", x, y)
        io.sleep(0.08)
        first = False
    io.log("norway: the men on Shetland attack " +
           ", ".join(f"{k} {int(x)},{int(y)}" for k, x, y in targets))
    return True


# Shetland after Finland (the owner, after trial 61: every marine goes to
# Finland first). The Dropship has not moved from where it starts. Once
# Finland is clear it is picked there, put on a key and flown to a spot
# beside the army's waiting place; when Russia's Starport is down the
# army's smallest key walks into it, it unloads on Shetland's beacon, and
# the men attack the island's turret and depot (as in the owner's game).
SHIP_KEY = "0"
SHIP_PICKUP = (151.0, 18.5)    # tile point it waits at, beside the army
SHIP_FLIGHT = 20               # seconds from Oslo to there
SHIP_BOARD = 6                 # seconds the men are given to walk in
SHIP_TRIES = 3                 # boardings tried
SHIP_LATEST = 45               # seconds after Finland it goes even if
                               # Russia's Starport still stands
SHETLAND_TRIP = 26             # seconds from there to Shetland


def call_ship(io, mapdata, st):
    """The Dropship, picked where it starts, onto its key and off to the
    pick-up spot. True if it went."""
    d = next((a for a in mapdata["slots"][SLOT]["air"]
              if a["type"] == "Dropship"), None)
    if d is None:
        return False
    clear_modes(io)
    tx, ty = d["x"] / T, d["y"] / T
    view = look(io, tx, ty, wait=0.2)
    io.click(*on_view(tx, ty, view))
    io.sleep(0.12)
    if not live.move_shown(io.card()):
        io.shot("no-dropship")
        io.log("norway: the Dropship was not found where it starts (picture "
               "'no-dropship'): no drop on Shetland")
        return False
    io.combo("ctrl", SHIP_KEY)
    io.sleep(0.05)
    io.click(*live.mm_point(*SHIP_PICKUP), button="right")
    io.sleep(0.05)
    io.log(f"norway: the Dropship (key {SHIP_KEY}) flies to the army for "
           f"the men for Shetland")
    return True


def shetland_step(io, mapdata, st):
    """One step of taking Shetland after Finland. Each call does one
    short thing or nothing."""
    now = io.now()
    if not st.finland_clear or st.ship_stage == "done":
        return
    if st.ship_stage == "wait":
        st.ship_clear_at = now
        st.ship_stage = "flying" if call_ship(io, mapdata, st) else "done"
        st.ship_next = now + SHIP_FLIGHT
    elif st.ship_stage == "flying" and now >= st.ship_next and \
            (st.port_gone or now - st.ship_clear_at >= SHIP_LATEST):
        if not st.army_keys:
            st.ship_stage = "done"
            return
        # the key with the most men (eight get in). Trial 62: the smallest
        # key held two men; and the click, aimed at where the Dropship had
        # been sent, fell a tile beside it, so nobody got in, three times
        keys = sorted(st.army_keys, key=lambda k: -st.army_held.get(k, 12))
        key = keys[st.ship_tries % len(keys)]
        st.ship_tries += 1

        def ship():
            io.key(SHIP_KEY)
            io.sleep(0.15)
            return live.move_shown(io.card())
        sent = men_into(io, key, ship)
        st.ship_stage, st.ship_next = "boarding", io.now() + SHIP_BOARD
        if sent:
            io.log(f"norway: the men on key {key} board the Dropship for "
                   f"Shetland")
    elif st.ship_stage == "boarding" and now >= st.ship_next:
        clear_modes(io)
        io.key(SHIP_KEY)
        io.sleep(0.15)
        if live.move_shown(io.card()) and someone_aboard(io):
            # the unload is given on the game screen, on the island's
            # beacon (the owner, after trial 62: the minimap is too coarse
            # for an island this small). The view first: with U asked, a
            # click on the minimap would be the target
            view = look(io, SHETLAND[0] / T, SHETLAND[1] / T)
            io.key("u")
            io.sleep(0.15)
            if live.placing_shown(io.card()):
                io.click(*on_view(SHETLAND[0] / T, SHETLAND[1] / T, view))
                io.sleep(0.05)
                io.log("norway: the Dropship goes to unload on Shetland's "
                       "beacon (a click on the island on the screen)")
                st.ship_stage, st.ship_next = "over", io.now() + SHETLAND_TRIP
                return
        clear_modes(io)
        if st.ship_tries >= SHIP_TRIES:
            io.shot("nobody-aboard")
            io.log("norway: nobody got aboard the Dropship (picture "
                   "'nobody-aboard'): no drop on Shetland")
            st.ship_stage = "done"
        else:
            st.ship_stage = "flying"        # once more
    elif st.ship_stage == "over" and now >= st.ship_next:
        st.shetland_attacks += 1
        attack_on_shetland(io, mapdata)
        st.ship_next = io.now() + SHETLAND_EVERY
        if st.shetland_attacks >= SHETLAND_ATTACKS:
            st.ship_stage = "done"


# ----------------------------------------------------------------- the SCVs
# What went wrong before (trials 51 to 59, found in the recordings):
# - the two new SCVs come out of the Command Center at about 7 and 10 s,
#   just as the army's box is dragged round it, so they went on army key 2
#   and marched to Finland and Murmansk with the marines;
# - from trial 56 on, "is this an SCV?" looked for the Build button in a
#   picture that held the first command button only, so it said no every
#   time, also with an SCV selected (trial 59: ten times);
# - units on the move show a white Move button, which the check fitted on
#   the yellow one does not know;
# - with two SCVs selected the game shows no Build buttons at all (the
#   owner's recording): a building can only be ordered with one selected.
# Now: SCVs (and the Dropship) are taken out of every army box by their
# picture in the selection; the SCVs wait below the Command Center, are
# boxed there once the army has left, told by their pictures, proved by B
# (only an SCV, alone, gets a build menu), put on key 9 and sent to
# Arkhangelsk. From then on they are only ever called by that key, and
# every order goes to one of them, picked by its picture.
FRAME_HOVER = 0.08             # seconds the mouse rests on a picture in the
                               # selection before it is clicked


def frame_click(io, i, n, held=None, rest=FRAME_HOVER):
    """Click the i-th of n pictures in the selection card (with Ctrl: every
    unit of that kind in the selection; with Shift: that one dropped;
    plain: that one alone)."""
    x0, y0, x1, y1 = live.frame_box(i, n)
    x, y = (x0 + x1) // 2, (y0 + y1) // 2
    if getattr(io, "hover", None) is not None and rest:
        io.hover(x, y)
        io.sleep(rest)
    if held:
        io.click_with(held, x, y)
    else:
        io.click(x, y)
    io.sleep(0.12)


NOT_ARMY = ("scv", "dropship")  # kinds an army key must not hold


def army_only(io, pic, n):
    """SCVs and the Dropship in a selection meant for an army key are
    taken out (Shift+click on each one's picture, from the last). Returns
    how many units stay selected, and whether any were taken out."""
    if n < 2:
        return n, False
    odd = sorted({i for kind in NOT_ARMY
                  for i in live.frames_like(pic, n, kind)}, reverse=True)
    m = n
    for i in odd:
        if m < 2:
            break                       # one left: its picture is not shown
        frame_click(io, i, m, held="shift")
        m -= 1
    if odd and len(odd) >= n:
        m = 0                           # nothing but SCVs and the Dropship
    return m, bool(odd)


def proved_scv(io):
    """With one unit selected: B. Only an SCV shows a build menu then (Esc
    closes it again). True if it did."""
    io.key("b")
    io.sleep(0.15)
    card = io.card()
    if live.build_menu_shown(card):
        io.key("esc")
        io.sleep(0.1)
        return True
    if not live.move_shown(card) and not live.placing_shown(card):
        io.key("esc")                   # something else came up: away with it
        io.sleep(0.1)
    return False


def scvs_selected(io, label="scvs"):
    """Whatever is selected, cut down to its SCVs by their pictures: with
    others among them, Ctrl+click on an SCV's picture picks every SCV of
    the selection. How many SCVs are selected after (0: none; then the
    selection is whatever it was)."""
    if not live.move_shown(io.card()):
        return 0
    pic = io.shot(label, keep=False)
    n = live.frames_shown(pic)
    if n < 2:                           # one unit: an SCV has the Build button
        return 1 if live.scv_selected(pic) else 0
    idx = live.frames_like(pic, n, "scv")
    if not idx:
        return 0
    if len(idx) == n:
        return n
    frame_click(io, idx[0], n, held="ctrl")
    pic = io.shot(label, keep=False)
    m = live.frames_shown(pic)
    if m < 2:
        return 1 if live.scv_selected(pic) else 0
    return m if len(live.frames_like(pic, m, "scv")) == m else 0


def key_scvs(io, st, n, where):
    """The SCVs now selected (n of them, told by their pictures) go on
    SCV_KEY, proved by B on one of them. How many the key holds after."""
    if n == 1 and not proved_scv(io):
        io.log(f"norway: what was taken for an SCV {where} showed no build "
               f"menu: left alone")
        return 0
    io.combo("shift" if st.scv_count else "ctrl", SCV_KEY)
    io.sleep(0.05)
    if n >= 2:                          # the proof needs one alone
        frame_click(io, 0, n)
        if not proved_scv(io):
            st.scv_count = 0            # the key is not to be trusted
            io.shot("not-scvs")
            io.log(f"norway: what was taken for SCVs {where} showed no build "
                   f"menu (picture 'not-scvs'): key {SCV_KEY} is not used")
            return 0
    st.scv_count += n
    io.log(f"norway: {n} SCV{'s' if n > 1 else ''} {where}, on key {SCV_KEY}"
           + (f" ({st.scv_count} in all)" if st.scv_count > n else ""))
    return n


def make_scvs(io, mapdata, st=None):
    """Two SCVs at the Command Center. No rally point: they come out below
    it and wait there, a known place, until they are put on their key."""
    cc = norway_buildings(mapdata)["Command Center"]
    if st is not None:
        st.scvs_made = io.now()         # (also if it fails: they are then
    if not pick(io, cc):                # looked for, and made again)
        io.log("norway: the Command Center was not found")
        return False
    for _ in range(SCVS):
        io.key("s")
        io.sleep(0.05)
    io.log(f"norway: {SCVS} SCVs ordered at the Command Center (they wait "
           f"below it and go on key {SCV_KEY} once the army has left)")
    return True


def take_scvs(io, st):
    """The new SCVs, standing below the Command Center, are boxed there
    and put on SCV_KEY. How many were taken."""
    clear_modes(io)
    view = look(io, *CC_EXIT)
    x0, y0, x1, y1 = SCV_BOX
    a = on_view(CC_EXIT[0] + x0, CC_EXIT[1] + y0, view)
    z = on_view(CC_EXIT[0] + x1, CC_EXIT[1] + y1, view)
    l, t, r, b = live.GAME_AREA
    io.drag(max(l + 4, a[0]), max(t + 4, a[1]), min(r - 4, z[0]), min(b - 4, z[1]))
    io.sleep(0.15)
    n = scvs_selected(io, "scvs-cc")
    if not n:
        io.shot("no-scvs-below-cc")     # (kept, to see why)
        io.log("norway: no SCV seen below the Command Center (picture "
               "'no-scvs-below-cc')")
        return 0
    return key_scvs(io, st, n, "below the Command Center")


def scvs_from_army(io, st):
    """SCVs that got onto an army key all the same: found by their
    pictures in the key's selection, put on SCV_KEY, and only then taken
    out of the army key (trial 59: they were taken out without having got
    onto their own key, and were on none after). How many were found."""
    found = 0
    for key in st.army_keys:
        clear_modes(io)
        io.key(key)
        io.sleep(0.2)
        pic = io.shot("army-key", keep=False)
        n = live.frames_shown(pic)
        if n < 2 or not live.frames_like(pic, n, "scv"):
            continue
        k = scvs_selected(io, "army-key")
        if not k or not key_scvs(io, st, k, f"on army key {key}"):
            continue
        found += k
        io.key(key)                     # and now out of the army key
        io.sleep(0.2)
        pic = io.shot("army-key", keep=False)
        left, changed = army_only(io, pic, live.frames_shown(pic))
        if changed and left:
            io.combo("ctrl", key)
            io.sleep(0.05)
    return found


def call_scvs(io, st):
    """Press the SCVs' key. How many SCVs it selects (told by their
    pictures; one alone by its Build button): 0 if it holds none."""
    io.key(SCV_KEY)
    io.sleep(0.2)
    if not live.move_shown(io.card()):
        return 0
    pic = io.shot("scvs", keep=False)
    n = live.frames_shown(pic)
    if n < 2:
        return 1 if live.scv_selected(pic) else 0
    return n if len(live.frames_like(pic, n, "scv")) == n else 0


def one_scv(io, st, i):
    """One SCV selected: the key, then (with several on it) the i-th one's
    picture. The number of SCVs on the key, 0 if none."""
    n = call_scvs(io, st)
    if n >= 2:
        frame_click(io, i % n, n)
    st.scv_count = n
    return n


def send_scvs(io, st):
    """The SCVs on their key walk to Arkhangelsk: one order on the
    minimap (the game finds the way, north of Finland and round the White
    Sea, as the owner sent theirs)."""
    if not call_scvs(io, st):
        io.log(f"norway: key {SCV_KEY} holds no SCV")
        st.scv_count = 0
        return False
    io.click(*live.mm_point(*DEPOTS_AT), button="right")
    io.sleep(0.05)
    st.scvs_sent = io.now()
    io.log("norway: the SCVs walk to Arkhangelsk")
    return True


def remake_scvs(io, mapdata, st):
    """Two new SCVs at the Command Center (still at home): they wait below
    it like the first."""
    cc = norway_buildings(mapdata)["Command Center"]
    clear_modes(io)
    if not pick(io, cc):
        io.log("norway: the Command Center was not found for new SCVs")
        return False
    io.key("s")
    io.sleep(0.05)
    io.key("s")
    io.sleep(0.05)
    st.scvs_made = st.scvs_remade = io.now()
    io.log("norway: no SCV found: the Command Center makes two more (its "
           "lift waits for them)")
    return True


# Looking for lost SCVs by moving the game screen with the arrow keys (the
# owner, after trial 56): the last resort. Where the view is, is read from
# the minimap's white box after each move (to two tiles).
SWEEP_VIEWS = [(133, 10), (155, 10), (155, 20), (133, 20), (200, 18)]
                               # tiles: view middles (Kiruna, Murmansk, the
                               # camp, then Arkhangelsk)
SWEEP_NEAR = (3, 2)            # tiles: a view this close is close enough
SWEEP_SPEED = 15.0             # tiles a second an arrow key scrolls (first guess;
                               # measured as it goes)
SWEEP_MOVES = 8                # moves at most to reach one view
SWEEP_HOLD = 1.5               # seconds an arrow is held at most at once
PROBES = 6                     # spots clicked at most in one view
SCV_CELL = 24                  # screen pixels: the grid SCVs are looked for in
SCV_ORANGE = 30                # orange pixels in a cell (trial 57: the SCV at
                               # Murmansk was darker, about (164, 100, 26))
SCV_PALE = (100, 500)          # pale pixels round it (more: a building)


def scv_spots(picture):
    """Screen points that may be one of our SCVs: its yellow-orange
    patches (about (213, 129, 29)) beside its pale blue-white body; our
    marines are a darker red-orange and have no pale body. Buildings with
    much pale metal are left out. Most orange first."""
    import numpy as np
    l, t, r, b = live.GAME_AREA
    a = np.asarray(picture.convert("RGB").crop((l, t, r, b))).astype(int)
    R, G, B = a[..., 0], a[..., 1], a[..., 2]
    orange = (R > 140) & (G > 70) & (G < 165) & (B < 70) & (R - G > 45)
    pale = (np.minimum(np.minimum(R, G), B) > 140) & (B >= R - 25)
    c = SCV_CELL
    h, w = orange.shape[0] // c, orange.shape[1] // c
    o = orange[:h * c, :w * c].reshape(h, c, w, c).sum((1, 3))
    p = pale[:h * c, :w * c].reshape(h, c, w, c).sum((1, 3))
    pp = np.pad(p, 1)
    p3 = sum(pp[dy:dy + h, dx:dx + w] for dy in range(3) for dx in range(3))
    op = np.pad(o, 1)
    o3max = np.max([op[dy:dy + h, dx:dx + w] for dy in range(3)
                    for dx in range(3)], axis=0)
    spots = []
    for j in range(h):
        for i in range(w):
            if o[j, i] >= SCV_ORANGE and SCV_PALE[0] <= p3[j, i] <= SCV_PALE[1] \
                    and o[j, i] == o3max[j, i]:
                spots.append((int(o[j, i]), l + i * c + c // 2, t + j * c + c // 2))
    spots.sort(reverse=True)
    return [(x, y) for _, x, y in spots]


def view_now(io):
    try:
        return live.camera_from_minimap(io.shot("sweep", keep=False))
    except Exception:
        return None


def scroll_to(io, st, tx, ty):
    """Move the screen with the arrow keys until the view's middle is near
    tile (tx, ty). True if it got there."""
    hold = getattr(io, "hold_key", None)
    if hold is None:
        return False
    for _ in range(SWEEP_MOVES):
        cam = view_now(io)
        if cam is None:
            io.log("norway: sweep: the view cannot be read from the minimap")
            return False
        dx, dy = tx - cam[0] / T, ty - cam[1] / T
        if abs(dx) <= SWEEP_NEAR[0] and abs(dy) <= SWEEP_NEAR[1]:
            return True
        for d, plus, minus in ((dx, "right", "left"), (dy, "down", "up")):
            if abs(d) > 1:
                secs = min(SWEEP_HOLD, abs(d) / st.sweep_speed)
                hold(plus if d > 0 else minus, secs)
                io.sleep(0.1)
                after = view_now(io)
                if after is not None:
                    i = 0 if plus == "right" else 1
                    moved = abs(after[i] - cam[i]) / T
                    if moved >= 1:
                        st.sweep_speed = max(3.0, min(60.0, moved / secs))
                    cam = after
    return False


def probe_scvs(io, st):
    """Click each spot on the screen that may be an SCV. Whether it is one
    is asked of the game itself: B, and a build menu shows only for an
    SCV (trials 57 to 59: the check used then never said yes). Each one
    found goes on SCV_KEY. How many were found."""
    found = 0
    for x, y in scv_spots(io.shot("scv-look", keep=False))[:PROBES]:
        io.click(x, y)
        io.sleep(0.12)
        if not live.move_shown(io.card()):
            continue
        if key_scvs(io, st, 1, f"at screen {x}, {y} (sweep)"):
            found += 1
            if st.scv_count >= 2:
                break
    return found


def sweep_for_scvs(io, st):
    """Move the screen over Kiruna, Murmansk, the Norwegian camp and
    Arkhangelsk with the arrow keys and look for our SCVs on it. How many
    were found (they are then on SCV_KEY)."""
    clear_modes(io)
    total = 0
    for tx, ty in SWEEP_VIEWS:
        if not scroll_to(io, st, tx, ty):
            continue
        total += probe_scvs(io, st)
        if st.scv_count >= 2:
            break
    if total:
        io.log(f"norway: sweep found {total} SCV(s)")
    return total


def get_scvs(io, mapdata, st):
    """One try at getting the SCVs onto their key and on their way: below
    the Command Center; from the second try on the army's keys too; then,
    with the Command Center still at home, two new ones; after Finland a
    sweep of the screen. With one SCV on the key already, only the place
    below the Command Center is looked at for the other. How many are on
    the key."""
    st.scv_tries += 1
    had = st.scv_count
    n = take_scvs(io, st)
    if not n and not had and st.scv_tries >= 2:
        n = scvs_from_army(io, st)
    if not n and not had and st.finland_clear and st.scv_tries >= 3 and \
            st.sweeps < SWEEPS:
        st.sweeps += 1
        n = sweep_for_scvs(io, st)
    if n:
        send_scvs(io, st)
        return st.scv_count
    if had:
        return had                      # one is on its way: that will do
    if st.scv_tries >= 2 and not st.scvs_remade and \
            "Command Center" not in st.lifted:
        remake_scvs(io, mapdata, st)
    elif st.scv_tries >= SCV_TRIES:
        io.log("norway: no SCV was found: no depots, no repair")
    return 0


# ------------------------------------------------------- the supply depots
def depot_spots():
    """Every depot spot in turn: (view, top-left tile)."""
    return [(view, tile) for view, tiles in DEPOT_FIELD for tile in tiles]


def free_scv(st, now):
    """The SCV (0 or 1) that has been free the longest, or None."""
    n = max(1, min(st.scv_count, len(st.scv_busy)))
    i = min(range(n), key=lambda k: st.scv_busy[k])
    return i if st.scv_busy[i] <= now else None


def footprint_on(io, view, tile, size, label):
    """With a building on the cursor: put its footprint on a tile (its
    top-left) and read it. The game hangs the footprint from the tile
    under the mouse (the owner's recording, and trials 56 to 59), so the
    mouse goes to that tile's middle; if the footprint is read elsewhere,
    the mouse is moved by what it is off, once. Returns (mouse, colour):
    colour "green", "red", or None if no footprint is seen there."""
    tile_px = live.TILE_PX
    want = live.tile_xy(tile[0], tile[1], view)         # its top-left corner
    mid = (want[0] + size[0] * tile_px / 2, want[1] + size[1] * tile_px / 2)
    mx, my = want[0] + tile_px / 2, want[1] + tile_px / 2
    for _ in range(2):
        io.hover(int(mx), int(my))
        io.sleep(0.15)
        fp = footprint_at(io.shot(label, keep=False), mid[0], mid[1], size)
        if fp is None:
            return (int(mx), int(my)), None
        ox, oy = want[0] - fp[0], want[1] - fp[1]
        if abs(ox) <= tile_px / 2 and abs(oy) <= tile_px / 2:
            return (int(mx), int(my)), "red" if fp[4] >= OUTLINE_RED else "green"
        mx, my = mx + ox, my + oy
    return (int(mx), int(my)), None


def build_depot(io, st):
    """One supply depot by Arkhangelsk, the owner's way (their recording):
    one SCV selected, B, S, and a click where the depot's footprint shows
    green. Returns "placed", "wait" (no SCV free just now), "no-scv" (the
    key holds none), "no-money" (the depot could not be picked) or
    "failed"."""
    now = io.now()
    i = free_scv(st, now)
    if i is None:
        return "wait"
    spots = depot_spots()
    todo = [k for k in range(len(spots)) if k not in st.depot_done]
    if not todo:
        st.depot_done = set(st.depot_built)     # every spot tried: once more
        todo = [k for k in range(len(spots)) if k not in st.depot_done]
        if not todo:
            return "failed"
    clear_modes(io)
    if not one_scv(io, st, i):
        io.log(f"norway: key {SCV_KEY} holds no SCV for the depots")
        return "no-scv"
    view = look_at_view(io, spots[todo[0]][0])
    io.key("b")                         # the build menu: only an SCV, alone,
    io.sleep(0.15)                      # and not in the middle of building
    card = io.card()
    if not live.build_menu_shown(card):
        if not st.no_menu_shown:
            st.no_menu_shown = True
            io.shot("no-build-menu")    # (kept once, to see why)
        if not live.move_shown(card):
            clear_modes(io)             # (nothing to close while its own
        st.scv_busy[i] = now + SCV_BUSY  # buttons show: it is building)
        return "wait"
    io.key("s")                         # a supply depot: its footprint is on
    io.sleep(0.15)                      # the cursor, only Cancel shows
    if not live.placing_shown(io.card()):
        clear_modes(io)
        io.log("norway: the depot could not be picked from the build menu "
               "(no money for one?)")
        return "no-money"
    hover = getattr(io, "hover", None) is not None
    for k in todo:
        if spots[k][0] != view:
            continue                    # another view's: next time
        tile = spots[k][1]
        if hover:
            mouse, colour = footprint_on(io, view, tile, DEPOT_SIZE, "depot")
        else:                           # (tests without eyes)
            mouse, colour = on_view(tile[0] + 0.5, tile[1] + 0.5, view), "green"
        if colour is None:
            io.shot("depot-unseen")
            io.log("norway: no depot footprint seen under the cursor "
                   "(picture 'depot-unseen'): not clicking")
            break
        st.depot_done.add(k)
        if colour == "red":
            continue                    # something is in the way: the next
        io.click(*mouse)
        io.sleep(0.3)
        card = io.card()
        if live.move_shown(card):       # placed: the SCV's own buttons again
            st.depot_built.add(k)
            st.depots_placed += 1
            st.scv_busy[i] = io.now() + DEPOT_BUILD + \
                (0 if st.scv_orders[i] else FIRST_WALK)
            st.scv_orders[i] += 1
            io.log(f"norway: supply depot {st.depots_placed} of {DEPOTS} "
                   f"ordered by Arkhangelsk ({tile[0]}, {tile[1]})")
            return "placed"
        if not live.placing_shown(card):
            break                       # neither placed nor placing: stop
        # refused (still placing): the next spot
    clear_modes(io)
    return "failed"


REPAIR_TRIES = 3
REPAIR_EVERY = 12
REPAIR_TIME = 45               # seconds the repairing SCV is left alone


def repair_barracks(io, st):
    """One SCV repairs the Barracks by the Heavy Industry: one SCV alone
    (by its picture), R, then a click on the Barracks where it landed.
    True if the order was given."""
    now = io.now()
    i = free_scv(st, now)
    if i is None:
        return False
    clear_modes(io)
    if not one_scv(io, st, i):
        io.log("norway: no SCV on its key to repair the Barracks")
        return False
    bx, by = st.at.get("Barracks", (BARRACKS_SPOT[0] / T, BARRACKS_SPOT[1] / T))
    view = look(io, bx, by)
    io.key("r")                         # repair
    io.sleep(0.1)
    io.click(*on_view(bx, by, view))
    io.sleep(0.05)
    st.scv_busy[i] = now + REPAIR_TIME
    io.log("norway: an SCV goes to repair the Barracks")
    return True


# ------------------------------------------- after the opening (trial 60 on)
# The owner, after trial 60: from the first tax (the countdown at 2:00) ten
# Dropships are made at the Starport and loaded with our men; when the
# reinforcements come (the countdown near 1:00) five Vultures go and lay
# mines at Oslo. How the owner did both is in their recording: D at the
# Starport, with a rally point, ten in four goes between 123 and 164 s;
# the Vultures picked out of the new troops by the Norwegian camp, then I
# and a click for each mine round Oslo's beacon.
SPARE_KEYS = ["5", "4", "6", "8"]  # number keys that may be free: the
                               # army's last ones if it did not need them,
                               # then the Barracks' and the Command Center's
                               # once they are down (0 is the Dropship's)
TAX_AT = 180                   # game seconds: the first tax (countdown 2:00)
SPAWN_AT = 250                 # game seconds: the reinforcements are out
                               # (trial 60: the supply jumped at about 240)
DROPSHIPS = 10                 # the owner: nine to twelve
DROP_BATCH = 5                 # a Starport's queue
DROP_EVERY = 30                # seconds between looks at the Dropships: one
                               # takes about 31 s and 300 minerals (trial 62:
                               # two were out 72 s after five were ordered)
DROP_ENOUGH = 9                # with this many out no more are ordered (the
                               # queue still holds some: nine to twelve)
DROP_LOOKS = 40                # looks at most (twenty minutes)
CENTRED_AT = trial.CENTRED_AT  # where Ctrl+C puts the selected unit
DROP_RALLY = (155.5, 10.5)     # tile point they gather at: below the
                               # Starport, clear of the army's waiting place
                               # (a selection is twelve units at most, so the
                               # box there should hold Dropships only)
DROP_BOX = 3.0                 # tiles round it boxed to take them
DROP_SEATS = 8                 # marines a Dropship holds
LOAD_STEP = 6                  # seconds between two boardings (the men of the
                               # last one must be in, or they turn round)
VULTURES = 5
SPAWN_VIEW = (127.5, 20.0)     # tile point the new troops stand round, by the
                               # Norwegian camp (trial 62: the Vultures in a
                               # ring of marines at 124 to 131, 17 to 23; the
                               # view was eight tiles west of them and they
                               # lay half under the bottom panel)
SPAWN_BOXES = sorted(((dx, dy) for dy in (-4.8, -2.4, 0, 2.4)
                      for dx in (-6, -3, 0, 3, 6)),
                     key=lambda d: abs(d[0]) + abs(d[1]))
SPAWN_BOX = (3, 2.4)           # tiles: one small box over the new troops (a
                               # selection is twelve units at most), the
                               # middle ones first
SPAWN_TRIES = 3                # looks for the Vultures before giving up
SPAWN_RETRY = 10               # seconds between them
OSLO_VIEW = (88.5, 50.0)       # tile point looked at for the mines
OSLO_MINES = [                 # tile points round Oslo's beacon (the first
    (87.9, 51.3), (86.1, 49.2), (89.3, 49.5), (86.8, 48.1), (88.2, 47.5),
    (87.6, 52.1), (86.8, 50.4), (88.5, 51.6), (86.3, 52.5), (90.7, 50.6),
    (89.9, 51.3), (88.3, 49.7), (90.9, 48.5), (85.4, 50.9), (89.6, 52.6),
]                              # nine are the owner's own clicks)
MINE_ROUNDS = 3                # a Vulture carries three mines
MINE_TRAVEL = 18               # seconds from the camp to Oslo
MINE_EVERY = 5                 # seconds between a Vulture's mines once there


def game_seconds(io, st, t0):
    """Game seconds since the start (the countdown's seconds): from the
    clock read off the screen, else from the time played."""
    real = st.clock.time() if st.clock is not None else io.now() - t0
    return real * trial.COUNTDOWN_RATE


def spare_key(st, taken=()):
    """A number key nothing of ours is on."""
    held = {KEYS[b]: b for b in KEYS}
    for k in SPARE_KEYS:
        if k in st.army_keys or k in taken:
            continue
        if k in held and held[k] not in st.landed:
            continue                    # still needed to land it
        return k
    return None


def kind_selected(io, kind, label):
    """Whatever is selected, cut down to its units of one kind by their
    pictures (Ctrl+click on one picks every one of them in the selection).
    How many are selected after; 0 if none (a single unit cannot be told:
    it shows no small picture)."""
    if not live.move_shown(io.card()):
        return 0
    pic = io.shot(label, keep=False)
    n = live.frames_shown(pic)
    if n < 2:
        return 0
    idx = live.frames_like(pic, n, kind)
    if not idx:
        return 0
    if len(idx) == n:
        return n
    frame_click(io, idx[0], n, held="ctrl")
    pic = io.shot(label, keep=False)
    m = live.frames_shown(pic)
    if m < 2:
        return 1 if len(idx) == 1 else 0
    return m if len(live.frames_like(pic, m, kind)) == m else 0


def order_dropships(io, st, n, quiet=False):
    """n Dropships at the Starport (on its key), gathering at DROP_RALLY.
    How many were ordered."""
    clear_modes(io)
    io.key(KEYS["Starport"])
    io.sleep(0.2)
    if not live.building_card(io.card()):
        io.log("norway: the Starport's key does not show its buttons: no "
               "Dropships ordered")
        return 0
    io.key("r")                         # the rally point (the owner's way),
    io.sleep(0.1)                       # first, so that all of them go there
    io.click(*live.mm_point(*DROP_RALLY))
    io.sleep(0.1)
    for _ in range(n):
        io.key("d")
        io.sleep(0.08)
    clear_modes(io)
    st.drop_ordered += n
    if not quiet:
        io.log(f"norway: {n} Dropships ordered at the Starport (its queue "
               f"is filled again every {DROP_EVERY} s until there are "
               f"{DROP_ENOUGH})")
    return n


def gather_dropships(io, st):
    """The Dropships at their rally point boxed and added to their key
    (those keyed before stay on it wherever they are). How many the key
    holds."""
    clear_modes(io)
    view = look(io, *DROP_RALLY)
    a = on_view(DROP_RALLY[0] - DROP_BOX, DROP_RALLY[1] - DROP_BOX, view)
    z = on_view(DROP_RALLY[0] + DROP_BOX, DROP_RALLY[1] + DROP_BOX, view)
    l, t, r, b = live.GAME_AREA
    io.drag(max(l + 4, a[0]), max(t + 4, a[1]), min(r - 4, z[0]), min(b - 4, z[1]))
    io.sleep(0.15)
    pic = io.shot("dropships", keep=False)
    n = live.frames_shown(pic)
    if n >= 2:
        got = kind_selected(io, "dropship", "dropships")
    else:                               # one unit alone: a Dropship has no
        got = 1 if live.move_shown(io.card()) and \
            not live.attack_shown(pic) else 0      # Attack button
    if got:
        io.combo("shift" if st.drop_count else "ctrl", st.drop_key)
        io.sleep(0.05)
    io.key(st.drop_key)                 # what the key holds now
    io.sleep(0.2)
    if not live.move_shown(io.card()):
        st.drop_count = 0
        return 0
    m = live.frames_shown(io.shot("dropships", keep=False))
    st.drop_count = m if m >= 2 else 1
    return st.drop_count


def one_dropship(io, st, i):
    """Dropship i of the key selected alone. False if the key does not
    hold that many."""
    io.key(st.drop_key)
    io.sleep(0.2)
    if not live.move_shown(io.card()):
        return False
    n = live.frames_shown(io.shot("dropships", keep=False))
    if n >= 2:
        if i >= n:
            return False
        frame_click(io, i, n)
    elif i:
        return False
    return True


def centre_on_selected(io):
    """Ctrl+C: the game puts the selected unit in the middle of the view
    (the owner's recording for Russia's air: to half a tile). The screen
    point it is then at."""
    io.combo("ctrl", "c")
    io.sleep(0.15)
    return CENTRED_AT


def someone_aboard(io):
    """With one Dropship selected: U asks for a target only if someone is
    aboard. Left out of that mode again."""
    io.key("u")
    io.sleep(0.15)
    loaded = live.placing_shown(io.card())
    clear_modes(io)
    return loaded


def men_into(io, key, ship):
    """The men on an army key walk into the Dropship that `ship()` selects
    alone: the Dropship centred with Ctrl+C, then the key, and a
    right-click on the middle of the view, where it is (trial 62: aimed
    by where it had been sent, the click fell a tile beside it and nobody
    got in). False if the key has no men left on the ground."""
    clear_modes(io)
    if not ship():
        return False
    at = centre_on_selected(io)
    io.key(key)
    io.sleep(0.12)
    if not live.move_shown(io.card()):
        return False                    # all of them are aboard already
    io.click(at[0], at[1], button="right")
    io.sleep(0.06)
    return True


def next_boarding(io, st):
    """The next Dropship with room gets the men of the next army key that
    still has some on the ground (kept count of: eight seats a Dropship,
    each key's men as they were keyed; fewer after losses only means a
    Dropship is counted full a little early). True if men were sent;
    False when no Dropship has room or no men are left."""
    n = st.drop_count
    while len(st.drop_room) < n:
        st.drop_room.append(DROP_SEATS)
    if st.men_left is None:
        st.men_left = {k: st.army_held.get(k) or 12 for k in st.army_keys}
    for i in range(n):
        if st.drop_room[i] <= 0:
            continue
        for key in st.army_keys:
            if st.men_left.get(key, 0) <= 0:
                continue
            if not men_into(io, key, lambda i=i: one_dropship(io, st, i)):
                st.men_left[key] = 0    # nobody of that key on the ground
                continue
            took = min(st.men_left[key], st.drop_room[i])
            st.men_left[key] -= took
            st.drop_room[i] -= took
            st.drop_boardings += 1
            io.log(f"norway: the men on key {key} board Dropship "
                   f"{i + 1} of {n}")
            return True
        return False                    # nobody left on the ground
    return False


def loaded_dropships(io, st):
    """How many Dropships have someone aboard."""
    full = 0
    for i in range(st.drop_count):
        clear_modes(io)
        if not one_dropship(io, st, i):
            break
        full += bool(someone_aboard(io))
    clear_modes(io)
    return full


def dropships_step(io, mapdata, st, t0):
    """One step of the Dropships, from the first tax on: every DROP_EVERY
    seconds those that are out are counted at their rally point and the
    Starport's queue is filled again, until there are enough; between
    those looks the men board the empty ones, one Dropship at a time.
    Each call does one short thing or nothing."""
    now = io.now()
    if st.drop_stage == "done":
        return
    if st.drop_stage == "wait":
        if "Starport" not in st.landed or game_seconds(io, st, t0) < TAX_AT:
            return
        st.drop_key = spare_key(st)
        if st.drop_key is None or not order_dropships(io, st, DROP_BATCH):
            st.drop_stage = "done"
            io.log("norway: no Dropships (no free key, or no Starport)")
            return
        st.drop_stage, st.drop_next = "making", now + DROP_EVERY + 4
        return
    if now >= st.drop_next and st.drop_stage == "making":
        st.drop_looks += 1
        before = st.drop_count
        n = gather_dropships(io, st)
        if n != before:
            io.log(f"norway: {n} Dropships out, on key {st.drop_key}")
        st.drop_boardable = True            # (new ones may be out)
        if n < DROP_ENOUGH - 1 and st.drop_looks < DROP_LOOKS:
            # (the queue holds five: with seven out and three more asked
            # for there are twelve at most in the end)
            order_dropships(io, st, min(DROP_BATCH, DROPSHIPS - n), quiet=True)
        elif n < DROP_ENOUGH and st.drop_looks < DROP_LOOKS:
            if n == before:             # eight, and none came: one more
                order_dropships(io, st, 1, quiet=True)
        else:
            st.drop_stage = "loading"
            io.log(f"norway: {n} Dropships: no more are ordered")
        st.drop_next = io.now() + DROP_EVERY
        st.drop_board_at = io.now() + 1
        return
    if st.drop_count and now >= st.drop_board_at and st.drop_boardable:
        st.drop_board_at = now + LOAD_STEP
        if not next_boarding(io, st):
            st.drop_boardable = False       # all full, or no men left: until
        return                              # the next look
    if now >= st.drop_next and st.drop_stage == "loading":
        # the last ones still come out of the Starport: onto the key too
        before = st.drop_count
        n = gather_dropships(io, st)
        st.drop_next = io.now() + DROP_EVERY
        if n != before:
            io.log(f"norway: {n} Dropships out, on key {st.drop_key}")
            st.drop_boardable, st.drop_quiet = True, 0
            return
        st.drop_quiet += 1
        if st.drop_quiet >= 2 and not st.drop_boardable:
            full = loaded_dropships(io, st)
            io.log(f"norway: {full} of {st.drop_count} Dropships have men "
                   f"aboard")
            st.drop_stage = "done"


def take_vultures(io, st):
    """Vultures among the new troops by the camp, onto their key. Small
    boxes over the troops until one holds a Vulture (told by its
    picture); that one is picked alone and centred with Ctrl+C, and
    Ctrl+click on it selects every Vulture on the screen. No more than
    five stay on the key. How many it holds."""
    clear_modes(io)
    view = look(io, *SPAWN_VIEW)
    w, h = SPAWN_BOX
    found = False
    for dx, dy in SPAWN_BOXES:
        cx, cy = SPAWN_VIEW[0] + dx, SPAWN_VIEW[1] + dy
        a = on_view(cx - w / 2, cy - h / 2, view)
        z = on_view(cx + w / 2, cy + h / 2, view)
        if not (in_free_area(*a, margin=4) and in_free_area(*z, margin=4)):
            continue
        io.drag(a[0], a[1], z[0], z[1])
        io.sleep(0.15)
        pic = io.shot("vultures", keep=False)
        n = live.frames_shown(pic)
        idx = live.frames_like(pic, n, "vulture") if n >= 2 else []
        if idx:
            frame_click(io, idx[0], n)      # that Vulture alone
            found = True
            break
    if not found:
        return 0
    at = centre_on_selected(io)
    io.click_with("ctrl", at[0], at[1])     # every Vulture on the screen
    io.sleep(0.15)
    pic = io.shot("vultures", keep=False)
    n = live.frames_shown(pic)
    if n >= 2:
        odd = [i for i in range(n) if i not in live.frames_like(pic, n, "vulture")]
        if odd:
            return 0                    # (something else was under the click)
        while n > VULTURES:
            frame_click(io, n - 1, n, held="shift")
            n -= 1
    else:
        n = 1                           # only the one there is
    io.combo("ctrl", st.vulture_key)
    io.sleep(0.05)
    st.vulture_count = n
    return n


def one_vulture(io, st, i):
    """Vulture i of the key selected alone; how many the key holds (0:
    none, or not that many)."""
    io.key(st.vulture_key)
    io.sleep(0.2)
    if not live.move_shown(io.card()):
        return 0
    n = live.frames_shown(io.shot("vultures", keep=False))
    if n >= 2:
        if i >= n:
            return 0
        frame_click(io, i, n)
        return n
    return 1 if i == 0 else 0


def lay_mines(io, st, round_no):
    """Each Vulture lays one mine at a spot of its own by Oslo (I, then a
    click: it drives there and lays it). How many orders were taken."""
    clear_modes(io)
    given = 0
    for i in range(st.vulture_count):
        if not one_vulture(io, st, i):
            break
        # (the view after the key, and before I: a click on the minimap
        # with a mine on the cursor would lay it there)
        view = look(io, *OSLO_VIEW, wait=0.12)
        io.key("i")
        io.sleep(0.12)
        if not live.placing_shown(io.card()):
            clear_modes(io)             # no mine left, or not a Vulture
            continue
        spot = OSLO_MINES[(round_no * VULTURES + i) % len(OSLO_MINES)]
        io.click(*on_view(*spot, view))
        io.sleep(0.08)
        given += 1
    clear_modes(io)
    return given


def vultures_step(io, mapdata, st, t0):
    """One step of the mines at Oslo: once the reinforcements are out,
    five Vultures on a key, then three rounds of mines."""
    now = io.now()
    if st.mine_stage == "wait":
        if game_seconds(io, st, t0) < SPAWN_AT or now < st.mine_next:
            return
        st.vulture_key = st.vulture_key or spare_key(st, (st.drop_key,))
        if st.vulture_key is None:
            st.mine_stage = "done"
            io.log("norway: no free key for the Vultures")
            return
        st.spawn_tries += 1
        n = take_vultures(io, st)
        if not n:
            io.shot("no-vultures")
            if st.spawn_tries >= SPAWN_TRIES:
                st.mine_stage = "done"
                io.log("norway: no Vultures found among the new troops "
                       "(picture 'no-vultures'): no mines")
            st.mine_next = now + SPAWN_RETRY
            return
        io.log(f"norway: {n} Vultures on key {st.vulture_key} go to lay "
               f"mines at Oslo")
        given = lay_mines(io, st, 0)
        st.mine_round, st.mine_stage = 1, "mines"
        st.mine_next = io.now() + MINE_TRAVEL
        if not given:
            st.mine_stage = "done"
            io.log("norway: the Vultures took no mine order (no mines?)")
    elif st.mine_stage == "mines" and now >= st.mine_next:
        given = lay_mines(io, st, st.mine_round)
        st.mine_round += 1
        st.mine_next = io.now() + MINE_EVERY
        if st.mine_round >= MINE_ROUNDS or not given:
            st.mine_stage = "done"
            io.log(f"norway: the mines at Oslo are ordered "
                   f"({st.mine_round} rounds)")


def selected(io):
    """How many units are selected now (0 if it cannot be read)."""
    try:
        return live.selected_count(io.shot("count", keep=False))
    except Exception:
        return 0


def army_selected(io):
    """A box meant for an army key: the SCVs and the Dropship in it are
    taken out of the selection first (trials 51 to 59: the box round the
    Command Center put the new SCVs on key 2, and the one round the
    Dropship took it off its way to Shetland). How many units are left
    selected for the key (0: none)."""
    try:
        pic = io.shot("count", keep=False)
        n = live.frames_shown(pic)
    except Exception:
        return selected(io) or 1
    if n < 2:                           # one unit alone: an SCV (it has the
        try:                            # Build button) or the Dropship (it
            return 0 if live.scv_selected(pic) or \
                not live.attack_shown(pic) else 1   # has no Attack) is not
        except Exception:               # for the army
            return 1
    left, changed = army_only(io, pic, n)
    if changed:
        io.log(f"norway: {n - left} SCV/Dropship taken out of an army box "
               f"({left} marines left in it)")
    return left


DENMARK = (80, 60, 95, 75)      # tiles: Denmark's marines stay out of it


def in_denmark(x, y):
    l, t, r, b = DENMARK
    return l <= x / T < r and t <= y / T < b


def start_groups(mapdata):
    """Norway's starting troops by the map (trial 45: men beside a bunker
    are hidden on the minimap by the building, so Sweden's (105, 66) and
    Kiruna's (141, 8) were never boxed): grouped into screen-sized
    patches of ground, the biggest first. Map pixels."""
    from collections import defaultdict
    cells = defaultdict(list)
    for x, y in mapdata["slots"][SLOT]["units"]:
        if in_denmark(x, y):
            continue                    # left at home (the owner, trial 51)
        cells[(x // (GROUP_W * T), y // (GROUP_H * T))].append((x, y))
    return sorted(cells.values(), key=len, reverse=True)


def box_start_group(io, pts):
    """Box the ground round some starting troops (the camera on them).
    True if the game shows units selected."""
    # (with the exact view. Trials 60 and 61: drawn with the Russia bot's
    # camera the boxes lay two tiles too high; the one for Sweden's four
    # men at 104, 66 covered rows 61.5 to 65.6 and held nobody, twice, and
    # one man at 103, 15 was missed the same way)
    l, t, r, b = live.GAME_AREA
    xs, ys = [p[0] / T for p in pts], [p[1] / T for p in pts]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    view = look(io, cx, cy, wait=0.2)
    a = on_view(min(xs) - 2, min(ys) - 2, view)
    z = on_view(max(xs) + 2, max(ys) + 2, view)
    box = (max(l + 4, a[0]), max(t + 4, a[1]), min(r - 4, z[0]), min(b - 4, z[1]))
    if box[2] - box[0] < 30 or box[3] - box[1] < 30:
        return False
    io.drag(*box)
    io.sleep(0.08)
    return live.units_selected(io.card())


def key_army(io, watch, mapdata, st, picture):
    """Every starting trooper on the army keys, 1 to 5 (the repository
    owner's way): box after box, each added to the key with Shift until
    it holds a dozen (trial 41: one box a key left most of the army
    unkeyed). How many each key holds goes to the log."""
    ours = watch.units(picture)
    l, t, r, b = ARMY_AREA
    mine = {p for p in ours
            if l <= live.from_drawn(*p)[0] / T < r
            and t <= live.from_drawn(*p)[1] / T < b
            and not in_denmark(*live.from_drawn(*p))}
    st.army_px = len(mine)
    groups = sorted((g for g in live.clusters(mine, 6, 6) if len(g) >= 3),
                    key=len, reverse=True)
    # one from each place first (Oslo, Sweden, Narvik, the partisans,
    # Kiruna), so no place is left out when the boxes run short
    firsts, rest, seen = [], [], set()
    for g in groups:
        x, y = live.from_drawn(*g[0])
        where = (int(x // (12 * T)), int(y // (12 * T)))
        (rest if where in seen else firsts).append(g)
        seen.add(where)
    groups = (firsts + rest)[:ARMY_BOXES]
    held = {}                           # key -> men on it
    # first every place where troops start, from the map (none missed),
    # then whatever the minimap shows besides, while boxes are left
    jobs = [("map", g) for g in start_groups(mapdata)] + \
        [("minimap", g) for g in groups]
    for kind, group in jobs[:ARMY_BOXES]:
        ok = box_start_group(io, group) if kind == "map" else \
            trial.select_group(io, group, st, watch, margin=60)
        if not ok:
            continue
        n = army_selected(io)
        if not n:
            continue                    # nothing for the army in this box
        key = next((k for k in st.army_keys if held[k] + n <= 12), None)
        if key is None:
            if len(st.army_keys) >= len(ARMY_KEYS):
                break
            key = ARMY_KEYS[len(st.army_keys)]
            st.army_keys.append(key)
            held[key] = 0
            io.combo("ctrl", key)
        else:
            io.combo("shift", key)
        io.sleep(0.04)
        # and off to Kiruna at once, while the rest are keyed (the owner,
        # trial 48)
        kx, ky = ARMY_STAGES[0][0]
        io.click(*live.minimap_point(kx * T, ky * T), button="right")
        io.sleep(0.03)
        held[key] += n
    st.army_held = held
    io.log("norway: the army on keys " + (", ".join(
        f"{k}: {held[k]}" for k in st.army_keys) or "(none)") + " men")
    return len(st.army_keys)


def army_counts(io, st):
    """Men left on each army key, pressed one by one."""
    out = {}
    for key in st.army_keys:
        io.key(key)
        io.sleep(0.15)                  # (0.06 read 0 while they lived)
        out[key] = selected(io)
    return out


def army_at(watch, picture, xy, reach=10):
    """Our minimap pixels near a map point."""
    return len(trial.near(watch.units(picture), xy, reach))


def order_army(io, st, xy, attack=True):
    """Every army key: an attack-move (or a move) to a map point."""
    for key in st.army_keys:
        io.key(key)
        io.sleep(0.05)
        if attack:
            trial.attack_move(io, *xy)
        else:
            io.click(*live.minimap_point(*xy), button="right")
            io.sleep(0.04)
    return len(st.army_keys)


def army_into_finland(io, watch, mapdata, st, picture):
    """The stages in turn (Kiruna, the Finland spot, Factory 10,
    Helsinki), one order a key each; then every CLEAN_EVERY seconds an
    attack-move at the biggest red that is left in Finland."""
    now = io.now()
    if st.stage < len(ARMY_STAGES):
        xy, attack, wait = ARMY_STAGES[st.stage]
        if now - st.stage_at < wait:
            return 0
        # (trial 42: waiting for most of the army at Kiruna held the
        # attack back 45 s; the owner attacked 5 s after the gather order
        # and the stragglers caught up)
        st.stage, st.stage_at = st.stage + 1, now
        if st.stage == BARRACKS_IN_AT and "Barracks" in st.lifted and \
                not st.barracks_in:
            # the Barracks flies in over Finland now (the owner, trial 46:
            # much sooner; it floats slowly, ~20 s across, and must be
            # over Helsinki and Factory 10 before 3:25)
            st.barracks_in = True
            hx, hy = heavy_industry(mapdata)
            io.key(KEYS["Barracks"])
            io.sleep(0.05)
            io.click(*live.minimap_point(*BARRACKS_NEAR),
                     button="right")
            io.sleep(0.05)
            io.log("norway: the Barracks flies in over Finland (by the Heavy "
                   "Industry)")
        n = order_army(io, st, (xy[0] * T, xy[1] * T), attack)
        io.log(f"norway: the army {'attacks at' if attack else 'moves to'} "
               f"{trial.place_name(mapdata, xy[0] * T, xy[1] * T)} "
               f"({xy[0]}, {xy[1]})")
        finland_picture(io, mapdata, f"stage{st.stage}")
        return n
    if now - st.last_clean < CLEAN_EVERY:
        return 0
    st.last_clean = now
    n = clear_buildings(io, watch, mapdata, st, picture)
    if n is not None:
        return n
    red = finland_red(watch, picture)
    if not red:
        return 0
    body = max(live.clusters(red, 4, 4), key=len)
    xy = live.from_drawn(sum(p[0] for p in body) / len(body),
                         sum(p[1] for p in body) / len(body))
    counts = army_counts(io, st)
    ours = trial.near(watch.units(picture), xy, 14)
    army_xy = live.from_drawn(sum(p[0] for p in ours) / len(ours),
                              sum(p[1] for p in ours) / len(ours)) \
        if ours else None
    n = attack_on_screen(io, st, xy, army_xy)
    if not n:
        n = order_army(io, st, xy)
    io.log(f"norway: {len(red)} red pixels left in Finland; the army "
           f"({sum(counts.values())} men on the keys) attacks the biggest, by "
           f"{trial.place_name(mapdata, *xy)} ({int(xy[0] // T)}, {int(xy[1] // T)})")
    finland_picture(io, mapdata, "clean")
    return n


def german_buildings(mapdata):
    """Germany's buildings in Finland by the map: depots, the Barracks,
    bunkers and the missile turrets (the owner, trial 45: the turrets
    too must be gone by 3:25). Map pixels with their kind."""
    l, t, r, b = FINLAND
    return [(bd["type"], bd["x"], bd["y"]) for bd in mapdata["slots"]["0"]["buildings"]
            if l <= bd["x"] / T < r and t <= bd["y"] / T < b]


GONE_LEAST = 8                 # red screen pixels round a building: still there
GONE_REACH = 2                 # minimap pixels round a building looked at for red
BUILDING_REACH = 55            # screen pixels round its middle looked at


def red_near(picture, sx, sy, reach=BUILDING_REACH):
    m = trial.enemy_mask(picture)
    l, t = live.GAME_AREA[:2]
    y0, x0 = max(0, int(sy - t - reach)), max(0, int(sx - l - reach))
    return int(m[y0:int(sy - t + reach), x0:int(sx - l + reach)].sum())


CHAIN_REFRESH = 6              # seconds before the same chain of attacks is given again
CHAIN_LONGEST = 4              # buildings a chain holds: the four turrets (trial 49: five a key, four
                               # keys, took 6 s to give)
FIRST_KINDS = ("Bunker", "Missile Turret")   # the owner: bunkers, then at once
                               # every turret, before anything else


def clear_buildings(io, watch, mapdata, st, picture):
    """Germany's buildings in Finland, all of them in one go: every army
    key attack-moves on the nearest, then (Shift) the next nearest from
    there, and so on, so the army goes on from one to the next by itself
    (trial 48: one order at a time, the army stood 6 to 13 s between
    buildings while the bot did other things). A building is crossed off
    once the minimap shows no red on it. The chain is given again when
    the first of it is gone, or every CHAIN_REFRESH seconds. Returns the
    orders given, or None once none is left."""
    if st.targets is None:
        st.targets = german_buildings(mapdata)
    left = []
    for kind, x, y in st.targets:
        try:
            on_map = len(trial.near(watch.others(picture, RED), (x, y),
                                    GONE_REACH))
        except Exception:
            on_map = 1
        if on_map == 0:
            io.log(f"norway: Germany's {kind} at {x // T}, {y // T} is gone")
        else:
            left.append((kind, x, y))
    st.targets = left
    if not any(k == "Bunker" for k, x, y in left) and st.barracks_in and \
            not st.barracks_over:
        # the bunkers are down: the Barracks moves over (139, 33) at once
        st.barracks_over = True
        io.key(KEYS["Barracks"])
        io.sleep(0.05)
        io.click(*live.minimap_point(*BARRACKS_SPOT), button="right")
        io.sleep(0.05)
        io.log("norway: the bunkers are down: the Barracks moves over "
               f"{BARRACKS_SPOT[0] // T}, {BARRACKS_SPOT[1] // T}")
    if not left:
        return None
    ours = trial.near(watch.units(picture), heavy_industry(mapdata), 16)
    ax, ay = live.from_drawn(sum(p[0] for p in ours) / len(ours),
                             sum(p[1] for p in ours) / len(ours)) \
        if ours else heavy_industry(mapdata)
    first = [b for b in left if b[0] in FIRST_KINDS]
    todo = first or list(left)
    chain, here = [], (ax, ay)
    while todo and len(chain) < CHAIN_LONGEST:   # the nearest from where it stands
        nxt = min(todo, key=lambda b: (b[1] - here[0]) ** 2 + (b[2] - here[1]) ** 2)
        todo.remove(nxt)
        chain.append(nxt)
        here = nxt[1:]
    if st.chain and st.chain[0] == chain[0] and \
            io.now() - st.chain_at < CHAIN_REFRESH:
        return 0                        # still on its way along the chain
    st.chain, st.chain_at = chain, io.now()
    # with the bunkers down nothing there shoots back at men on foot: the
    # keys share the turrets out, each starting on a different one, so they
    # fall together (the owner, trial 51: all of Finland by about 63 s, or
    # the German army comes); while a bunker stands, all on the same one
    split = not any(k == "Bunker" for k, x, y in left)
    # Every key gets its first target before any key gets the rest
    # (trial 61: a key's whole chain took 1.2 s to give, so the second
    # and third keys set off for the bunker 1.2 and 2.4 s after the
    # first, and the army went in piece by piece)
    for queued in (False, True):
        for n, key in enumerate(st.army_keys):
            # (two groups, the keys taking turns: trial 52, one turret a
            # key left the smallest key alone on the farthest turret till
            # 69 s)
            start = (n % 2) * (len(chain) // 2) if split else 0
            mine = chain[start:] + chain[:start]
            if queued and len(mine) < 2:
                continue
            io.key(key)
            io.sleep(0.05)
            for i, (kind, x, y) in enumerate(mine):
                point = live.minimap_point(x, y)
                if i == 0 and not queued:
                    io.key("a")
                    io.sleep(0.03)
                    io.click(*point)
                elif i and queued:
                    io.combo("shift", "a")
                    io.sleep(0.03)
                    io.click_with("shift", *point)
                io.sleep(0.03)
    io.log("norway: the army attacks Germany's buildings in turn: " + ", ".join(
        f"{k} {x // T},{y // T}" for k, x, y in chain))
    return len(st.army_keys)


def attack_on_screen(io, st, xy, army_xy=None):
    """The camera on the red that is left: each army key attacks one of
    the red buildings seen there (A, then a click on it), the keys shared
    out over them, as the repository owner did (trial 40). Returns the
    orders given (0 if no red shows on the screen)."""
    cam = trial.look_at(io, *trial.centred(*xy), wait=0.25)
    pic = io.shot("finland-red", keep=False)
    try:
        spots = [(x, y) for n, x, y in trial.patches(trial.enemy_mask(pic))
                 if n >= trial.CELL_LEAST]
    except Exception:
        return 0
    if not spots:
        return 0
    sx, sy = live.on_screen(*xy, cam)
    # the army together on one building at a time (trial 43: shared out
    # over several, it was cut down piece by piece; the owner kept it
    # together): the red nearest our own men on the screen
    # (where our men are comes from the minimap: the screen check for our
    # own colour is Russia's brown, not Norway's orange)
    ox, oy = live.on_screen(*army_xy, cam) if army_xy else (sx, sy)
    spots.sort(key=lambda p: (p[0] - ox) ** 2 + (p[1] - oy) ** 2)
    for key in st.army_keys:
        x, y = spots[0]
        io.key(key)
        io.sleep(0.05)
        io.key("a")
        io.sleep(0.04)
        io.click(x, y)
        io.sleep(0.05)
    return len(st.army_keys)


def finland_picture(io, mapdata, label):
    """A picture of Finland kept for the log (what the army is doing)."""
    x, y = heavy_industry(mapdata)
    trial.look_at(io, *trial.centred(x - 3 * T, y), wait=0.3)
    io.shot("finland-" + label)


def finland_red(watch, picture):
    """Red (Germany) minimap pixels in Finland."""
    l, t, r, b = FINLAND
    return {p for p in watch.others(picture, RED)
            if l <= live.from_drawn(*p)[0] / T < r
            and t <= live.from_drawn(*p)[1] / T < b}


def clear_landing(io, watch, mapdata, st, picture):
    """Our men standing where the Barracks lands step aside first."""
    x, y = BARRACKS_SPOT
    there = trial.near(watch.units(picture), (x, y), 6)
    moved = 0
    for group in live.clusters(there, 4, 4)[:4]:
        if trial.select_group(io, group, st, watch, margin=45):
            io.click(*live.minimap_point(x + OUT_OF_WAY * T, y - OUT_OF_WAY * T),
                     button="right")
            io.sleep(0.05)
            moved += 1
    return moved


PORT_DOWN = 5                  # seconds after the landing click before looking
PORT_GIVE_UP = 30              # seconds: not down by then, it is tried again


def try_land_port(io, st):
    """Ours held over Russia's Starport's spot in Land mode: with the light
    green box showing (Russia's is gone), it is put on the box and clicked
    once. "clicked", "red" (box seen, something of ours in the way) or
    "none" (no box: Russia's still stands, or ours is not in the air)."""
    key = KEYS["Starport"]
    clear_modes(io)
    io.key(key)
    io.sleep(0.15)
    if not live.move_shown(io.card()):
        return "none"
    x, y = PORT_MOUSE[0] * T + T // 2, PORT_MOUSE[1] * T + T // 2
    cam = trial.look_at(io, *trial.centred(x, y), wait=0.25)
    sx, sy = live.on_screen(x, y, cam)
    io.click(*LAND_BUTTON)
    io.sleep(0.15)
    if getattr(io, "hover", None) is None:       # tests: no eyes
        io.click(sx, sy)
        st.land_tried.add("Starport")
        return "clicked"
    spot = port_spot(io, sx, sy, quiet=True)
    if spot is None or spot == "red":
        clear_modes(io)
        return "none" if spot is None else "red"
    io.click(*spot)                     # once; no Esc after (it is landing)
    st.land_tried.add("Starport")
    io.log("norway: Starport landing on the light green box (one click)")
    return "clicked"


def russia_port_gone(io, st, port):
    """True once Russia's Starport is destroyed, seen without pressing
    Land: ours (in the air, on its key) is selected, then Russia's spot is
    clicked. If Russia's stands, the click selects it (a card with no
    buttons); if it is gone, ours stays selected (Move shows). Without
    eyes (tests): True."""
    if getattr(io, "hover", None) is None:
        return True
    clear_modes(io)
    io.key(KEYS["Starport"])
    io.sleep(0.15)
    if not live.move_shown(io.card()):
        return False
    # (the exact view: Russia's Starport itself is clicked, not the ground
    # two tiles above it)
    tx, ty = port["x"] / T, port["y"] / T
    view = look(io, tx, ty)
    io.click(*on_view(tx, ty, view))
    io.sleep(0.2)
    return live.move_shown(io.card())   # still ours: nothing stands there


def attack_russian_starport(io, watch, mapdata, st, picture):
    """Right after Finland: every army key attacks Russia's Starport at
    Murmansk (A, then a click on it), as the repository owner did."""
    port = russia_starport(mapdata)
    if not st.army_keys:
        return 0
    cam = trial.look_at(io, *trial.centred(port["x"], port["y"]), wait=0.2)
    sx, sy = live.on_screen(port["x"], port["y"], cam)
    for key in st.army_keys:
        io.key(key)
        io.sleep(0.05)
        io.key("a")
        io.sleep(0.04)
        io.click(sx, sy)
        io.sleep(0.05)
    return len(st.army_keys)


def army_slack(io, st):
    """Seconds until the army's next order is due: time the bot may spend
    elsewhere without holding the attack on Finland back."""
    if st.finland_clear:
        return 99.0
    due = st.last_look + LOOK_EVERY
    if st.stage < len(ARMY_STAGES):
        due = max(due, st.stage_at + ARMY_STAGES[st.stage][2])
    return due - io.now()


def opening(io, watch, mapdata, st, first):
    """The whole opening, in the owner's order, until the Barracks and the
    Starport are down or OPENING_TIME is up."""
    t0 = io.now()
    trial.opening(io, st, line=OPENING_LINE)
    make_scvs(io, mapdata, st)          # first, as the owner (at 2 s)
    # (no drop on Shetland now: the owner, after trial 61: every marine
    # to Finland first, Shetland after it)
    # the army keyed and sent to Kiruna before the lifts, so it walks while
    # the buildings go up (trial 44: keyed after them, it set off at 26 s
    # and reached Finland 7 s behind the owner)
    key_army(io, watch, mapdata, st, io.shot("watch", keep=False) or first)
    army_into_finland(io, watch, mapdata, st, first)
    # (the Factory and the Engineering Bay go to Shetland once Finland is
    # clear: trial 51, their lifts held the attack back 5 s; trial 52, just
    # after the stages they held the turret attacks back 5 s)
    port = russia_starport(mapdata)
    lift(io, mapdata, st, "Starport", (port["x"], port["y"] + 8 * T),
         key=KEYS["Starport"])
    # the Barracks waits out of the Germans' reach, by the Norwegian
    # military camp, as the owner's did (trial 44: floated over the Heavy
    # Industry at once, it was shot by the bunkers and turrets); it flies
    # in to land once Finland is clear
    lift(io, mapdata, st, "Barracks", BARRACKS_WAIT, key=KEYS["Barracks"])
    while io.now() - t0 < OPENING_TIME:
        picture = io.shot("watch", keep=False)
        if st.clock is not None:
            st.clock.update(picture)
        left = countdown(st)
        # Shetland: the men dropped there are sent at its turret and depot
        # (twice: the second for what the first left), once Finland is clear
        shetland_step(io, mapdata, st)
        if st.finland_clear and not st.shetland_lifts:
            st.shetland_lifts = True
            lift(io, mapdata, st, "Factory", SHETLAND)
            lift(io, mapdata, st, "Engineering Bay", SHETLAND)
        # the Command Center goes once its two SCVs are out, and not in the
        # middle of the army's stages (trial 44: its lift pushed the attack
        # on Finland back)
        waiting_scvs = st.scvs_remade and not st.scv_count and \
            io.now() - st.scvs_remade < SCV_REMADE_WAIT
        if not st.cc_lifted and io.now() - t0 >= 32 and not waiting_scvs and \
                st.stage >= len(ARMY_STAGES) and \
                (st.finland_clear or io.now() - t0 >= BUSY_UNTIL):
            st.cc_lifted = lift(io, mapdata, st, "Command Center",
                                (KIRUNA_LAND[0][0] * T, KIRUNA_LAND[0][1] * T),
                                key=KEYS["Command Center"]) or \
                io.now() - t0 > 60
        if "Command Center" in st.lifted and \
                "Command Center" not in st.landed and \
                io.now() - st.lifted.get("Command Center", 1e9) > 25:
            clicked = st.land_clicked.get("Command Center")
            if clicked is None or io.now() >= max(clicked + LAND_SETTLE,
                                                  cc_due(mapdata, st)):
                # (again only if it did not come down long after it should
                # have got there)
                land(io, "Command Center",
                     [(x * T + 2 * T, y * T + int(1.5 * T))
                      for x, y in KIRUNA_LAND], st)
                st.cc_look = io.now()
            elif io.now() - st.cc_look >= LAND_LOOK:
                st.cc_look = io.now()
                clear_modes(io)
                if is_down(io, KEYS["Command Center"]):
                    st.landed.add("Command Center")
                    io.log("norway: Command Center landed by Kiruna")
        # Finland: attack until no red is left (first: the opening's race).
        # A look every LOOK_EVERY seconds; and the moment the attack on the
        # Finland spot is due (the opening before it is now about two
        # seconds shorter: with looks three seconds apart the order could
        # have gone out up to three seconds late)
        spot_due = st.stage == 1 and \
            io.now() - st.stage_at >= ARMY_STAGES[1][2]
        if not st.finland_clear and \
                (io.now() - st.last_look >= LOOK_EVERY or spot_due):
            st.last_look = io.now()
            red = finland_red(watch, picture)
            st.clear_looks = 0 if red else st.clear_looks + 1
            if st.clear_looks >= CLEAR_LOOKS and st.stage >= len(ARMY_STAGES) \
                    and not st.targets:
                st.finland_clear = True
                if st.barracks_in and not st.barracks_over:
                    st.barracks_over = True
                    io.key(KEYS["Barracks"])
                    io.sleep(0.05)
                    io.click(*live.minimap_point(*BARRACKS_SPOT), button="right")
                    io.log("norway: Finland is clear: the Barracks moves over "
                           f"{BARRACKS_SPOT[0] // T}, {BARRACKS_SPOT[1] // T}")
                io.log(f"norway: Finland cleared of Germany's buildings "
                       f"(countdown {trial.round_timer(st.clock.time()) if st.clock else '?'})")
            else:
                army_into_finland(io, watch, mapdata, st, picture)
        # the SCVs: onto their key below the Command Center once the army
        # has left it, and off to Arkhangelsk; only while the army does not
        # need the bot (the first try falls in the six seconds after the
        # attack on the Finland spot)
        now = io.now()
        if st.scv_count < 2 and st.scvs_made is not None and \
                st.scv_tries < (3 if st.scv_count else SCV_TRIES) and \
                st.stage >= 2 and now - st.scvs_made >= SCV_OUT and \
                now - st.scv_look >= SCV_RETRY and army_slack(io, st) >= SCV_SLACK:
            st.scv_look = now
            get_scvs(io, mapdata, st)
        # ten depots by Arkhangelsk, one order at a time to whichever SCV
        # is free (the owner's way: one SCV, B, S, a click on green)
        now = io.now()
        if not st.depots_ordered and st.scv_count and \
                st.scvs_sent is not None and now - st.scvs_sent >= SCV_WALK and \
                (st.finland_clear or now - t0 >= BUSY_UNTIL) and \
                now - st.depot_look >= DEPOT_EVERY:
            st.depot_look = now
            result = build_depot(io, st)
            if result == "placed":
                st.depot_fails = 0
                st.depot_look = now - DEPOT_EVERY   # the next SCV at once
            elif result == "failed":
                st.depot_fails += 1
            elif result == "no-money":  # wait for the next payday
                st.depot_look = now + NO_MONEY_WAIT - DEPOT_EVERY
            elif result == "no-scv":
                st.depot_fails += 3     # the SCVs are gone: soon given up
            st.depots_ordered = st.depots_placed >= DEPOTS or \
                st.depot_fails >= DEPOT_FAILS
            if st.depots_ordered:
                io.log(f"norway: {st.depots_placed} of {DEPOTS} supply depots "
                       f"ordered by Arkhangelsk" +
                       ("" if st.depots_placed >= DEPOTS else " (given up)"))
        # the Barracks: down by the Heavy Industry before 3:25
        if "Barracks" in st.lifted and "Barracks" not in st.landed and \
                st.finland_clear and st.port_tries >= 1 and \
                io.now() - st.barracks_land_at >= BARRACKS_RETRY:
            st.barracks_land_at = io.now()      # one landing click, then wait
            clear_landing(io, watch, mapdata, st, picture)
            io.sleep(1.0)
            if land(io, "Barracks", barracks_spots(mapdata), st):
                io.log(f"norway: Barracks down by the Heavy Industry "
                       f"(countdown {trial.round_timer(st.clock.time()) if st.clock else '?'}; "
                       f"the owner: before 3:25)")
        # Murmansk: Russia's Starport destroyed, then ours lands there.
        # One step (trial 58): while the marines attack, the bot holds ours
        # over the spot in Land mode now and then; once the light green box
        # shows (Russia's is gone) it lands at once, the owner's way. After
        # the click it only waits for it to come down.
        if st.port_clicked and "Starport" not in st.landed:
            if io.now() - st.port_clicked >= PORT_DOWN and \
                    io.now() - st.last_port >= 4:
                st.last_port = io.now()
                clear_modes(io)
                if is_down(io, KEYS["Starport"]):
                    st.landed.add("Starport")
                    io.log("norway: Starport landed at Murmansk on the "
                           "Control Tower")
                elif io.now() - st.port_clicked > PORT_GIVE_UP:
                    st.port_clicked = 0     # it did not come down: again
        elif st.finland_clear and "Starport" not in st.landed and \
                io.now() - st.last_port >= RETRY_PORT:
            st.last_port = io.now()
            if not st.port_gone:
                # the owner (trial 58): no Land tries while Russia's stands;
                # it is looked at by a click instead
                if st.port_tries and russia_port_gone(io, st, port):
                    st.port_gone = True
                    io.log("norway: Russia's Starport is destroyed")
                    order_army(io, st, PORT_ASIDE, attack=False)
                    st.last_port = io.now() - RETRY_PORT + PORT_WALK
                    io.log("norway: the army steps off Russia's Starport's spot")
                else:
                    st.port_tries += 1
                    n = attack_russian_starport(io, watch, mapdata, st, picture)
                    if n:
                        io.log(f"norway: {n} groups of marines attack "
                               f"Russia's Starport at Murmansk")
            else:
                result = try_land_port(io, st)
                if result == "clicked":
                    st.port_clicked = io.now()
                elif result == "red":       # something of ours still there
                    order_army(io, st, PORT_ASIDE, attack=False)
                    st.last_port = io.now() - RETRY_PORT + PORT_WALK
                    io.log("norway: the army steps off Russia's Starport's "
                           "spot again")
        # an SCV comes and repairs the Barracks (the owner, trial 50), once
        # the SCVs have reached Arkhangelsk and one of them is free
        if "Barracks" in st.landed and st.repaired < REPAIR_TRIES and \
                st.scv_count and st.scvs_sent is not None and \
                io.now() - st.scvs_sent >= SCV_WALK and \
                io.now() - st.last_repair >= REPAIR_EVERY and \
                free_scv(st, io.now()) is not None:
            st.last_repair = io.now()
            if repair_barracks(io, st):
                st.repaired = REPAIR_TRIES
            else:
                st.repaired += 1
        cc_done = "Command Center" in st.landed or \
            (st.cc_lifted and "Command Center" not in st.lifted)
        if st.extras:
            dropships_step(io, mapdata, st, t0)
            vultures_step(io, mapdata, st, t0)
        extras_done = not st.extras or \
            (st.drop_stage == "done" and st.mine_stage == "done" and
             st.ship_stage == "done")
        if {"Barracks", "Starport"} <= st.landed and cc_done and \
                st.depots_ordered and extras_done:
            break
        io.sleep(0.5)
    io.log(f"norway: opening over after {io.now() - t0:.0f} s; landed: "
           f"{', '.join(sorted(st.landed)) or 'nothing'}")


def run(io, mapdata=None, general=None, save_lessons=None, ears=None):
    """Norway's game: for now (v0.01) the opening only."""
    mapdata = mapdata or trial.load_map()
    io.log(f"build {trial.build_id()} (Norway)")
    side = mapdata["slots"][SLOT]
    first = io.shot("start")
    watch = live.Watch(first, side["structures"], side["units"])
    if not live.minimap_showing(first) or not watch.ok:
        io.log("The live game's minimap is not on screen. Nothing done.")
        return {"norway": "no minimap"}
    st = State()
    st.clock = team_rules.GameClock(io.now)
    st.clock.update(first)
    opening(io, watch, mapdata, st, first)
    for kind in ("Barracks", "Starport", "Command Center"):
        if kind in st.lifted:
            io.key(KEYS[kind])
            io.sleep(0.2)
            io.shot("at-" + kind.split()[0].lower())
    return {"norway": "opening", "lifted": sorted(st.lifted),
            "landed": sorted(st.landed), "finland_clear": st.finland_clear}
