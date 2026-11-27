"""Norway (slot 4, orange), version 0.01: the opening.

Built from the sample games (docs/norway-notes.md) and the repository
owner's rules for the first minutes:

- the opening line "AF Norway AI v0.01" to everyone, then allied chat;
- the starting Dropship drops on Shetland at once;
- two SCVs, rallied to the far north-east, where they build the supply
  depots (for safety);
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
OPENING_TIME = 300             # real seconds the opening is played at most

T = 32                         # map pixels a tile
SHETLAND = (64 * T + 6 * T, 33 * T + 4 * T)     # the middle of Shetland 300
KIRUNA_LAND = [(139, 8), (130, 1), (128, 2), (126, 2), (133, 3)]   # Command Center (tiles,
                               # top left), the sample games' spots by Kiruna
DEPOTS_AT = (200, 18)          # tiles: by Arkhangelsk, where the repository
                               # owner built them (for safety; trial 40)
# where the owner put their depots by Arkhangelsk (their recording:
# tiles 184-209, 13-27), a depot's width (3 tiles) and more apart
DEPOT_TILES = [(199, 20), (195, 20), (203, 20), (199, 16), (195, 16),
               (203, 16), (207, 20), (207, 24), (199, 24), (203, 24),
               (195, 24), (207, 16)]
DEPOTS = 10                    # the owner: ten depots by Arkhangelsk
SCV_WAIT = (126, 17)           # tiles: where the new SCVs wait (the owner's
                               # recording: the Norwegian military camp; trial
                               # 53, sent straight on through Finland they were
                               # lost to the Germans and never arrived)
SCV_REMAKE_WAIT = 45           # seconds for two new SCVs to come out and
                               # walk to Kiruna
SCV_OUT = 30                   # seconds the Command Center's lift waits for them
SCV_TRIES = 12                 # looks for the SCVs before giving up
SCV_WALK = 25                  # seconds they are given to reach Arkhangelsk
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
DEPOT_FIRST = 60               # seconds before the SCVs are looked for at the depots
BUSY_UNTIL = 100               # seconds: the Command Center and the depots wait
                               # for Finland till then (trial 48: they took the
                               # bot away from the fight at 45 and 63 s)
DEPOT_EVERY = 14                # seconds between depots (one an order) (trial 42: every 3 s, the
                               # camera sat on empty ground by Arkhangelsk)
DEPOT_LOOKS = 30               # tries before the depots are given up
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
SCV_KEY = "9"                  # the two SCVs, once found at the camp
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
        self.depots_ordered = False
        self.scvs_at = None
        self.cc_lifted = False
        self.army_keys = []
        self.stage = 0
        self.stage_at = -1e9
        self.last_clean = -1e9
        self.army_px = 0
        self.targets = None            # Germany's buildings in Finland left
        self.barracks_in = False
        self.land_tried = set()
        self.shetland_lifts = False
        self.barracks_over = False
        self.barracks_land_at = -1e9
        self.port_cleared = False
        self.port_gone = False
        self.repaired = 0
        self.last_repair = -1e9
        self.chain, self.chain_at = [], -1e9
        self.depot_look = -1e9
        self.depot_looks = 0
        self.depot_next = 0
        self.depots_placed = 0
        self.scvs_sent = 0
        self.scvs_look = -1e9
        self.scvs_tries = 0
        self.scvs_keyed = False
        self.scvs_remade = 0
        self.sweep_speed = SWEEP_SPEED
        self.army_checked = False
        self.port_clicked = 0
        self.cc_home = None
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
    if b is None or not trial.pick_building(io, b):
        io.log(f"norway: the {kind} was not found")
        return False
    io.sleep(0.2)
    if live.units_selected(io.card()):
        # something in the air is selected, not this building on the ground
        # (trial 50: a floating Starport, whose bottom-right button is Land)
        clear_modes(io)
        io.log(f"norway: the {kind} was not picked (something else was)")
        return False
    io.click(*trial.LIFT_BUTTON)
    io.sleep(0.15)
    io.key("l")                         # (the button, and its key, in case)
    io.sleep(0.4)
    if not live.units_selected(io.card()):      # a lifted building shows Move
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
    """Move the mouse until the footprint's middle is on (cx, cy): hover,
    find the footprint in the picture, move the mouse by what it is off,
    and again. (mouse point, footprint) or (None, None) if none is seen."""
    tile = 32 * live.ZOOM
    mx, my = cx, cy
    fp = None
    for _ in range(ALIGN_TRIES):
        io.hover(int(mx), int(my))
        io.sleep(0.15)
        fp = footprint_at(io.shot(label, keep=False), cx, cy, size)
        if fp is None:
            return None, None
        ox = cx - (fp[0] + fp[2]) / 2
        oy = cy - (fp[1] + fp[3]) / 2
        if abs(ox) <= tile / 3 and abs(oy) <= tile / 3:
            return (int(mx), int(my)), fp
        mx, my = mx + ox, my + oy
    return (int(mx), int(my)), fp      # the last move is not checked


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
    if not live.building_selected(io.card()):
        return False
    io.sleep(0.25)
    return live.building_selected(io.card())


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
        if not live.units_selected(io.card()):
            return False                # the key does not hold it in the air
        cam = trial.look_at(io, *trial.centred(x, y), wait=0.25)
        sx, sy = live.on_screen(x, y, cam)
        if not (l + 40 < sx < r - 40 and t + 40 < sy < b - 40):
            continue
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
        st.land_tried.add(kind)
        io.sleep(0.3)
        io.key("esc")                   # out of placing if the spot was refused
        io.sleep(0.1)
        if is_down(io, key):
            st.landed.add(kind)
            io.log(f"norway: {kind} landed by {x // T}, {y // T}")
            return True
        # landing takes a moment: the building still shows Move while it
        # comes down, so look again before the next spot
        io.sleep(2.5)
        if is_down(io, key):
            st.landed.add(kind)
            io.log(f"norway: {kind} landed by {x // T}, {y // T}")
            return True
    return False


REPAIR_TRIES = 3
REPAIR_EVERY = 12


def repair_barracks(io, st):
    """One SCV repairs the Barracks by the Heavy Industry: the SCVs on
    their key, the first of them picked from the selection, R, then a
    click on the Barracks. True if the order was given."""
    if not pick_scvs(io, st):
        io.log("norway: no SCV found to repair the Barracks")
        return False
    n = selected(io)
    if n > 1:                           # just one of them
        frame_click(io, 0, n)
    bx, by = BARRACKS_SPOT
    cam = trial.look_at(io, *trial.centred(bx, by), wait=0.3)
    io.key("r")                         # repair
    io.sleep(0.08)
    io.click(*live.on_screen(bx, by, cam))
    io.sleep(0.05)
    io.log("norway: an SCV goes to repair the Barracks")
    return True


def drop_on_shetland(io, mapdata):
    """The starting Dropship (with its men aboard) unloads on Shetland:
    picked where it stands, U, then a click on Shetland."""
    d = next((a for a in mapdata["slots"][SLOT]["air"]
              if a["type"] == "Dropship"), None)
    if d is None:
        return False
    # the men standing by it board it first (it starts empty; the
    # repository owner boxed the few beside it and right-clicked it)
    cam = trial.look_at(io, *trial.centred(d["x"], d["y"]), wait=0.2)
    l, t, r, b = live.GAME_AREA
    x0, y0, x1, y1 = LOAD_BOX
    a = live.on_screen(d["x"] + x0 * T, d["y"] + y0 * T, cam)
    z = live.on_screen(d["x"] + x1 * T, d["y"] + y1 * T, cam)
    box = (max(l + 3, a[0]), max(t + 3, a[1]), min(r - 3, z[0]), min(b - 3, z[1]))
    if box[2] - box[0] > 20 and box[3] - box[1] > 20:
        io.drag(*box)
        io.sleep(0.1)
        io.click(*live.on_screen(d["x"], d["y"], cam), button="right")
        io.sleep(1.5)                   # they walk in
    if trial.click_unit(io, d["x"], d["y"]) is None:
        io.log("norway: the Dropship was not found")
        return False
    io.key("u")                         # unload, there
    io.sleep(0.05)
    io.click(*live.minimap_point(*SHETLAND))
    io.sleep(0.05)
    io.log("norway: the Dropship goes to unload on Shetland")
    return True


def make_scvs(io, mapdata, st=None):
    """Two SCVs at the Command Center, rallied to the Norwegian camp."""
    cc = norway_buildings(mapdata)["Command Center"]
    if st is not None:
        st.cc_home = (cc["x"], cc["y"] + 3 * T)   # where they come out
    if not trial.pick_building(io, cc):
        io.log("norway: the Command Center was not found")
        return False
    io.key("s")
    io.sleep(0.05)
    io.key("s")
    io.sleep(0.05)
    io.key("r")                         # rally, the owner's way: R, then
    io.sleep(0.05)                      # a click on the minimap
    io.click(*live.minimap_point(SCV_WAIT[0] * T, SCV_WAIT[1] * T))
    io.sleep(0.05)
    io.log("norway: 2 SCVs ordered, rallied to the Norwegian military camp "
           "(they go on to Arkhangelsk once Finland is clear)")
    return True


# Looking for the SCVs by moving the game screen with the arrow keys (the
# owner, after trial 56), not by jumping about with the minimap: a sweep
# over Kiruna, the Norwegian camp and Murmansk. Where the view is, is read
# from the minimap's white box after each move.
SWEEP_VIEWS = [(133, 10), (155, 10), (155, 20), (133, 20), (200, 18)]
                               # tiles: view middles (Kiruna, Murmansk, the
                               # camp, then Arkhangelsk, where the owner's
                               # SCVs were by 68 s)
SWEEP_NEAR = (3, 2)            # tiles: a view this close is close enough
SWEEP_SPEED = 15.0             # tiles a second an arrow key scrolls (first guess;
                               # measured as it goes)
SWEEP_MOVES = 8                # moves at most to reach one view
SWEEP_HOLD = 1.5               # seconds an arrow is held at most at once
PROBES = 10                     # spots clicked at most in one view
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
    """Click each spot on the screen that may be an SCV; each that shows
    the Build button joins the SCVs on SCV_KEY. How many were found."""
    found = 0
    spots = scv_spots(io.shot("scv-look", keep=False))[:PROBES]
    for x, y in spots:
        io.click(x, y)
        io.sleep(0.15)
        if not live.scv_selected(io.card()):
            continue
        if st.scvs_keyed:               # add it to the ones on the key
            io.key(SCV_KEY)
            io.sleep(0.1)
            io.click_with("shift", x, y)
            io.sleep(0.1)
        io.combo("ctrl", SCV_KEY)
        io.sleep(0.05)
        st.scvs_keyed = True
        found += 1
        io.log(f"norway: sweep: an SCV at screen {x}, {y}, put on key "
               f"{SCV_KEY}")
    return found


def sweep_for_scvs(io, st):
    """Move the screen over Kiruna, the Norwegian camp and Murmansk with
    the arrow keys and look for our SCVs on it. True if any were found
    (they are then on SCV_KEY)."""
    clear_modes(io)
    total = 0
    for tx, ty in SWEEP_VIEWS:
        if not scroll_to(io, st, tx, ty):
            continue
        total += probe_scvs(io, st)
        if total >= 2:
            break
    if total:
        io.log(f"norway: sweep found {total} SCV(s)")
    return total > 0


FRAME_HOVER = 0.15             # seconds the mouse rests on a picture in the
                               # selection before it is clicked (trial 59: a
                               # click at once only brought up its tooltip)


def frame_click(io, i, n, held=None):
    """Click the i-th of n pictures in the selection card: the mouse is put
    on it first and left there a moment, then clicked (with Ctrl: every
    unit of that kind in the selection; with Shift: that one dropped)."""
    x0, y0, x1, y1 = live.frame_box(i, n)
    x, y = (x0 + x1) // 2, (y0 + y1) // 2
    if getattr(io, "hover", None) is not None:
        io.hover(x, y)
        io.sleep(FRAME_HOVER)
    if held:
        io.click_with(held, x, y)
    else:
        io.click(x, y)
    io.sleep(0.15)


def scvs_from_army(io, st):
    """The SCVs boxed into the army keys with the marines (trial 58: both
    were there; the army's boxes by the Command Center took them at
    18 s): Ctrl+click on an SCV's picture in the key's selection picks
    every SCV in it, they go on SCV_KEY, then each is dropped from the
    army key with Shift+click. How many were found."""
    found = 0
    for key in st.army_keys:
        clear_modes(io)
        io.key(key)
        io.sleep(0.2)
        try:
            pic = io.shot("army-key", keep=False)
            n = live.selected_count(pic)
            idx = live.scv_frames(pic, n) if n > 1 else []
        except Exception:
            continue
        if not idx:
            continue
        frame_click(io, idx[0], n, held="ctrl")     # all the SCVs in it
        if not live.scv_selected(io.card()):
            io.shot("army-key-scv")
            io.log(f"norway: the SCVs on army key {key} could not be picked "
                   f"(picture 'army-key-scv')")
            continue
        io.combo("shift" if st.scvs_keyed else "ctrl", SCV_KEY)
        io.sleep(0.05)
        st.scvs_keyed = True
        found += len(idx)
        io.key(key)                     # and out of the army key
        io.sleep(0.2)
        m = n
        for i in sorted(idx, reverse=True):
            frame_click(io, i, m, held="shift")
            m -= 1
        io.combo("ctrl", key)
        io.sleep(0.05)
        io.log(f"norway: {len(idx)} SCV(s) found on army key {key}, put on "
               f"key {SCV_KEY} and taken out of key {key}")
    return found


def pick_scvs(io, st):
    """The SCVs selected: by their key once they have one, else looked for
    by sweeping the screen over Kiruna, the camp and Murmansk. True if
    SCVs are selected."""
    if st.scvs_keyed:
        io.key(SCV_KEY)
        io.sleep(0.15)
        if live.scv_selected(io.card()):
            return True
    if not st.army_checked:
        st.army_checked = True
        if scvs_from_army(io, st):
            io.key(SCV_KEY)
            io.sleep(0.15)
            if live.scv_selected(io.card()):
                return True
    if sweep_for_scvs(io, st):
        io.key(SCV_KEY)
        io.sleep(0.15)
        return live.scv_selected(io.card())
    return False


def DEPOTS_XY():
    return DEPOTS_AT[0] * T, DEPOTS_AT[1] * T


def remake_scvs(io, mapdata, st):
    """Two new SCVs at the Command Center (still at home), no rally: they
    stay by it until they are found, keyed and sent."""
    cc = norway_buildings(mapdata)["Command Center"]
    clear_modes(io)
    if not trial.pick_building(io, cc):
        io.log("norway: the Command Center was not found for new SCVs")
        return False
    io.key("s")
    io.sleep(0.05)
    io.key("s")
    io.sleep(0.05)
    io.key("r")                         # rallied by Kiruna, where the
    io.sleep(0.05)                      # sweep looks
    io.click(*live.minimap_point(SWEEP_VIEWS[0][0] * T, SWEEP_VIEWS[0][1] * T))
    io.sleep(0.05)
    st.cc_home = (cc["x"], cc["y"] + 3 * T)
    io.log("norway: no SCV found: the Command Center makes two more, "
           "rallied by Kiruna (its lift waits for them)")
    return True


def send_scvs(io, st):
    """Once Finland is clear: the SCVs (waiting by the Norwegian camp)
    are sent on to Arkhangelsk. True if they were."""
    if not pick_scvs(io, st):
        io.log("norway: no SCV by the Norwegian camp or the Command Center")
        return False
    io.click(*live.minimap_point(*DEPOTS_XY()), button="right")
    io.sleep(0.05)
    io.log("norway: the SCVs go on to Arkhangelsk")
    return True


def build_depots(io, st):
    """One supply depot by Arkhangelsk, the repository owner's way (their
    recording): the SCVs boxed where they stand, B, S, and a click on the
    next free spot; one depot an order (trial 52: four queued with Shift
    in one order, none was built, and the click had picked marines). True
    if a depot was placed."""
    x0, y0 = DEPOTS_XY()
    if not pick_scvs(io, st):
        io.log("norway: no SCV found for the depots")
        return False
    n = selected(io)
    if n > 1:                           # one SCV an order, by turns, so a
        frame_click(io, st.depot_next % n, n)   # depot going up is not left
    cam = trial.look_at(io, *trial.centred(x0, y0), wait=0.3)
    l, t, r, b = live.GAME_AREA
    io.key("b")                         # only SCVs have a build menu on B:
    io.sleep(0.12)                      # the Move button goes
    if live.units_selected(io.card()):
        clear_modes(io)
        io.log("norway: what stands at the depots' place is not an SCV")
        return False
    io.key("s")
    io.sleep(0.15)
    for _ in range(len(DEPOT_TILES)):
        tx, ty = DEPOT_TILES[st.depot_next % len(DEPOT_TILES)]
        st.depot_next += 1
        px, py = live.on_screen(tx * T + T, ty * T + T // 2, cam)
        if not (l + 30 < px < r - 30 and t + 30 < py < b - 30):
            continue
        spot = green_spot(io, px, py, "depot")
        if spot is None:
            continue                    # red all round: the next spot
        io.click(*spot)
        io.sleep(0.25)
        if live.units_selected(io.card()):      # placed: the SCV's own buttons
            st.depots_placed += 1
            io.log(f"norway: supply depot {st.depots_placed} of {DEPOTS} "
                   f"ordered by Arkhangelsk ({tx}, {ty})")
            return True
        # refused (taken, or not ground): still placing, try the next spot
    clear_modes(io)
    return False


def selected(io):
    """How many units are selected now (0 if it cannot be read)."""
    try:
        return live.selected_count(io.shot("count", keep=False))
    except Exception:
        return 0


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
    l, t, r, b = live.GAME_AREA
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    cam = trial.look_at(io, *trial.centred(cx, cy), wait=0.2)
    a = live.on_screen(min(xs) - 2 * T, min(ys) - 2 * T, cam)
    z = live.on_screen(max(xs) + 2 * T, max(ys) + 2 * T, cam)
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
        n = selected(io) or 1
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
    for n, key in enumerate(st.army_keys):
        io.key(key)
        io.sleep(0.05)
        # (two groups, the keys taking turns: trial 52, one turret a key
        # left the smallest key alone on the farthest turret till 69 s)
        start = (n % 2) * (len(chain) // 2) if split else 0
        mine = chain[start:] + chain[:start]
        for i, (kind, x, y) in enumerate(mine):
            point = live.minimap_point(x, y)
            if i == 0:
                io.key("a")
                io.sleep(0.03)
                io.click(*point)
            else:
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
    if not live.units_selected(io.card()):
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
    if not live.units_selected(io.card()):
        return False
    cam = trial.look_at(io, *trial.centred(port["x"], port["y"]), wait=0.25)
    io.click(*live.on_screen(port["x"], port["y"], cam))
    io.sleep(0.2)
    card = io.card()
    return live.units_selected(card)            # still ours: nothing there


def port_gone(io, st, port):
    """True once Russia's Starport is destroyed: with ours held over its
    spot to land, the game draws the light green box where the Control
    Tower would join (the owner's recording); while Russia's stands, it
    does not. Without a way to hover (tests): True."""
    if getattr(io, "hover", None) is None:
        return True
    key = KEYS["Starport"]
    clear_modes(io)
    io.key(key)
    io.sleep(0.15)
    if not live.units_selected(io.card()):
        return False                    # ours is not in the air on its key
    cam = trial.look_at(io, *trial.centred(port["x"], port["y"]), wait=0.25)
    sx, sy = live.on_screen(port["x"], port["y"], cam)
    io.click(*LAND_BUTTON)
    io.sleep(0.15)
    io.hover(int(sx), int(sy))
    io.sleep(0.15)
    try:
        box = tower_box(io.shot("port-check", keep=False), sx, sy)
    except Exception:
        box = None
    clear_modes(io)
    return box is not None


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


def opening(io, watch, mapdata, st, first):
    """The whole opening, in the owner's order, until the Barracks and the
    Starport are down or OPENING_TIME is up."""
    t0 = io.now()
    trial.opening(io, st, line=OPENING_LINE)
    make_scvs(io, mapdata, st)          # first, as the owner (at 2 s)
    drop_on_shetland(io, mapdata)       # the owner: by 8 s
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
        if st.finland_clear and not st.shetland_lifts:
            st.shetland_lifts = True
            lift(io, mapdata, st, "Factory", SHETLAND)
            lift(io, mapdata, st, "Engineering Bay", SHETLAND)
        # the Command Center goes once its two SCVs are out, and not in the
        # middle of the army's stages (trial 44: its lift pushed the attack
        # on Finland back)
        waiting_scvs = st.scvs_remade and io.now() - st.scvs_remade < SCV_OUT
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
            land(io, "Command Center",
                 [(x * T + 2 * T, y * T + int(1.5 * T)) for x, y in KIRUNA_LAND],
                 st)
        # Finland: attack until no red is left (first: the opening's race)
        if not st.finland_clear and io.now() - st.last_look >= LOOK_EVERY:
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
        # the SCVs to Arkhangelsk (trials 55, 56: the two made at the start
        # were never found again; then the Command Center, still at home,
        # makes two more, and its lift waits until they are out and keyed)
        if st.finland_clear and not st.scvs_sent and \
                io.now() - st.scvs_look >= 6 and \
                (not st.scvs_remade or io.now() - st.scvs_remade >= SCV_REMAKE_WAIT):
            st.scvs_look = io.now()
            st.scvs_tries += 1
            if send_scvs(io, st):
                st.scvs_sent = io.now()
            elif not st.scvs_remade and not st.cc_lifted:
                st.scvs_remade = io.now()
                remake_scvs(io, mapdata, st)
            elif st.scvs_tries >= SCV_TRIES:
                st.scvs_sent = io.now()     # given up: the log says so
        if not st.depots_ordered and io.now() - t0 >= DEPOT_FIRST and \
                st.scvs_sent and io.now() - st.scvs_sent >= SCV_WALK and \
                io.now() - st.depot_look >= DEPOT_EVERY:
            st.depot_look = io.now()
            st.depot_looks += 1
            build_depots(io, st)
            st.depots_ordered = st.depots_placed >= DEPOTS or \
                st.depot_looks >= DEPOT_LOOKS
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
        # an SCV comes and repairs the Barracks (the owner, trial 50)
        if "Barracks" in st.landed and st.repaired < REPAIR_TRIES and \
                io.now() - st.last_repair >= REPAIR_EVERY:
            st.last_repair = io.now()
            if repair_barracks(io, st):
                st.repaired = REPAIR_TRIES
            else:
                st.repaired += 1
        cc_done = "Command Center" in st.landed or \
            (st.cc_lifted and "Command Center" not in st.lifted)
        if {"Barracks", "Starport"} <= st.landed and cc_done and \
                st.depots_ordered:
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
