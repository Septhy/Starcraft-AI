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
KIRUNA_LAND = [(130, 1), (128, 2), (126, 2), (133, 3)]   # Command Center (tiles,
                               # top left), the sample games' spots by Kiruna
DEPOTS_AT = (200, 18)          # tiles: by Arkhangelsk, where the repository
                               # owner built them (for safety; trial 40)
DEPOT_SPOTS = [(0, 0), (3, 0), (6, 0), (0, 3), (3, 3), (6, 3), (0, 6), (3, 6)]
DEPOTS = 4                     # depots the two SCVs build in the opening
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
    ((147, 31), False, 8),
    ((140, 39), True, 2),      # the east bunker
    ((134, 36), True, 4),      # the west bunker
    ((136, 38), True, 4),      # Helsinki (owner: attacked 41-44 s)
]
CLEAN_EVERY = 4                # seconds between attacks on the red that is left
                               # (the owner: boxes and attacks every 1-2 s)
ARMY_BOXES = 16                # boxes at most to key the army (each ~1 s;
                               # trial 43: 10 left Narvik's men unkeyed)
GROUP_W, GROUP_H = 20, 8       # tiles: a box's patch of ground (the screen
                               # shows about 26 by 10 tiles)
DEPOT_FIRST = 60               # seconds before the SCVs are looked for at the depots
DEPOT_EVERY = 12               # seconds between looks (trial 42: every 3 s, the
                               # camera sat on empty ground by Arkhangelsk)
DEPOT_LOOKS = 5                # looks before the depots are given up
LOAD_BOX = (-4, -5, 3, 2)      # tiles round the Dropship whose men board it
BARRACKS_WAIT = (127 * T, 22 * T)  # where the Barracks floats till the army
                               # has taken the Finland spot: the Norwegian camp
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
RETRY_PORT = 8                 # real seconds between attacks on Russia's Starport


def norway_buildings(mapdata):
    return {b["type"]: b for b in mapdata["slots"][SLOT]["buildings"]
            if b["type"] not in ("Bunker", "Missile Turret", "Supply Depot")}


def russia_starport(mapdata):
    """Russia's Starport at Murmansk (its Control Tower beside it)."""
    return next(b for b in mapdata["slots"]["5"]["buildings"]
                if b["type"] == "Starport" and b["y"] < 10 * T)


def heavy_industry(mapdata):
    """The Heavy Industry: the middle of the map's "Factory 10" place."""
    p = trial.place(mapdata, "Factory 10")
    return p["x"], p["y"]


def barracks_spots(mapdata):
    """Where the Barracks lands, next to the Heavy Industry: its left,
    right, below, above (map pixels of the Barracks' middle)."""
    x, y = heavy_industry(mapdata)
    # first where the repository owner landed it: just north of it
    return [(x - int(1.5 * T), y - int(4.5 * T)), (x, y - 5 * T),
            (x - 5 * T, y), (x + 5 * T, y), (x, y + 4 * T),
            (x - 5 * T, y + 3 * T), (x + 5 * T, y + 3 * T)]


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
        self.depot_look = -1e9
        self.depot_looks = 0
        self.army_held = {}
        # what the Russia bot's box helpers keep count of
        self.boxes = self.empty = self.empty_skipped = 0
        self.scout_frame = None


def lift(io, mapdata, st, kind, dest=None, key=None):
    """Lift one of Norway's buildings (picked where it stands at the
    start), put it on a key if asked, and float it to a map point.
    True if it went up."""
    b = norway_buildings(mapdata).get(kind)
    if b is None or not trial.pick_building(io, b):
        io.log(f"norway: the {kind} was not found")
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


def dest_name(mapdata, xy):
    return trial.place_name(mapdata, *xy) if xy else "-"


def land(io, kind, spots, st):
    """Land a lifted building (on its key) at the first of `spots` (map
    pixels of its middle) the game takes. True if it is down: once it
    has landed the key shows a building, not Move."""
    key = KEYS[kind]
    l, t, r, b = live.GAME_AREA
    for x, y in spots:
        io.key(key)
        io.sleep(0.1)
        if live.building_selected(io.card()):
            st.landed.add(kind)
            return True                 # down already
        cam = trial.look_at(io, *trial.centred(x, y), wait=0.25)
        sx, sy = live.on_screen(x, y, cam)
        if not (l + 40 < sx < r - 40 and t + 40 < sy < b - 40):
            continue
        io.click(*LAND_BUTTON)
        io.sleep(0.15)
        io.click(sx, sy)
        io.sleep(0.3)
        io.key("esc")                   # out of placing if the spot was refused
        io.sleep(0.1)
        io.key(key)
        io.sleep(0.1)
        if live.building_selected(io.card()):
            st.landed.add(kind)
            io.log(f"norway: {kind} landed by {x // T}, {y // T}")
            return True
        # landing takes a moment: the building still shows Move while it
        # comes down, so look again before the next spot
        io.sleep(2.5)
        io.key(key)
        io.sleep(0.1)
        if live.building_selected(io.card()):
            st.landed.add(kind)
            io.log(f"norway: {kind} landed by {x // T}, {y // T}")
            return True
    return False


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


def make_scvs(io, mapdata):
    """Two SCVs at the Command Center, rallied to the far north-east."""
    cc = norway_buildings(mapdata)["Command Center"]
    if not trial.pick_building(io, cc):
        io.log("norway: the Command Center was not found")
        return False
    io.key("s")
    io.sleep(0.05)
    io.key("s")
    io.sleep(0.05)
    io.click(*live.minimap_point(DEPOTS_AT[0] * T, DEPOTS_AT[1] * T),
             button="right")
    io.sleep(0.05)
    io.log("norway: 2 SCVs ordered, rallied to the far north-east")
    return True


def build_depots(io, st):
    """The SCVs, standing at their rally point in the far north-east,
    build the depots there (B, S, then Shift + clicks, queued)."""
    x0, y0 = DEPOTS_AT[0] * T, DEPOTS_AT[1] * T
    cam = trial.look_at(io, *trial.centred(x0, y0), wait=0.3)
    sx, sy = live.on_screen(x0, y0, cam)
    for dx, dy in trial.SCV_PICK:
        io.click(sx + dx, sy + dy)
        io.sleep(0.1)
        if live.units_selected(io.card()):
            break
    else:
        io.log("norway: no SCV at the depots' place yet")
        return False
    io.key("b")
    io.sleep(0.1)
    io.key("s")
    io.sleep(0.15)
    for i, (dx, dy) in enumerate(DEPOT_SPOTS[:DEPOTS]):
        px, py = live.on_screen(x0 + dx * T, y0 + dy * T, cam)
        if i == 0:
            io.click(px, py)
        else:
            io.key("b")
            io.sleep(0.05)
            io.key("s")
            io.sleep(0.1)
            io.click_with("shift", px, py)
        io.sleep(0.15)
    io.key("esc")
    io.log(f"norway: {DEPOTS} supply depots ordered in the far north-east")
    return True


def selected(io):
    """How many units are selected now (0 if it cannot be read)."""
    try:
        return live.selected_count(io.shot("count", keep=False))
    except Exception:
        return 0


def start_groups(mapdata):
    """Norway's starting troops by the map (trial 45: men beside a bunker
    are hidden on the minimap by the building, so Sweden's (105, 66) and
    Kiruna's (141, 8) were never boxed): grouped into screen-sized
    patches of ground, the biggest first. Map pixels."""
    from collections import defaultdict
    cells = defaultdict(list)
    for x, y in mapdata["slots"][SLOT]["units"]:
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
            and t <= live.from_drawn(*p)[1] / T < b}
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
            io.click(*live.minimap_point(hx - int(1.5 * T), hy - int(4.5 * T)),
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


def clear_buildings(io, watch, mapdata, st, picture):
    """Germany's buildings in Finland, one at a time, the nearest to our
    army first: the camera on it; no red left there, it is crossed off;
    else every army key attacks it (A, then a click on it). Returns the
    orders given, or None once none is left (the minimap then decides)."""
    if st.targets is None:
        st.targets = german_buildings(mapdata)
    ours = trial.near(watch.units(picture), heavy_industry(mapdata), 16)
    ax, ay = live.from_drawn(sum(p[0] for p in ours) / len(ours),
                             sum(p[1] for p in ours) / len(ours)) \
        if ours else heavy_industry(mapdata)
    st.targets.sort(key=lambda b: (b[1] - ax) ** 2 + (b[2] - ay) ** 2)
    for _ in range(3):                  # a few crossed off a look at most
        if not st.targets:
            return None
        kind, x, y = st.targets[0]
        # gone when the minimap shows no red on it any more (trial 46: the
        # screen's bright team red was too little on Germany's buildings,
        # three were crossed off in one second while still standing)
        try:
            on_map = len(trial.near(watch.others(picture, RED), (x, y),
                                    GONE_REACH))
        except Exception:
            on_map = 1
        cam = trial.look_at(io, *trial.centred(x, y), wait=0.25)
        sx, sy = live.on_screen(x, y, cam)
        if on_map == 0:
            st.targets.pop(0)
            io.log(f"norway: Germany's {kind} at {x // T}, {y // T} is gone "
                   f"({len(st.targets)} left)")
            continue
        for key in st.army_keys:
            io.key(key)
            io.sleep(0.05)
            io.key("a")
            io.sleep(0.04)
            io.click(sx, sy)
            io.sleep(0.05)
        io.log(f"norway: the army attacks Germany's {kind} at {x // T}, "
               f"{y // T} ({len(st.targets)} left)")
        return len(st.army_keys)
    return 0


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
    x, y = heavy_industry(mapdata)
    there = trial.near(watch.units(picture), (x, y), 6)
    moved = 0
    for group in live.clusters(there, 4, 4)[:4]:
        if trial.select_group(io, group, st, watch, margin=45):
            io.click(*live.minimap_point(x + OUT_OF_WAY * T, y - OUT_OF_WAY * T),
                     button="right")
            io.sleep(0.05)
            moved += 1
    return moved


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
    make_scvs(io, mapdata)              # first, as the owner (at 2 s)
    drop_on_shetland(io, mapdata)       # the owner: by 8 s
    # the army keyed and sent to Kiruna before the lifts, so it walks while
    # the buildings go up (trial 44: keyed after them, it set off at 26 s
    # and reached Finland 7 s behind the owner)
    key_army(io, watch, mapdata, st, io.shot("watch", keep=False) or first)
    army_into_finland(io, watch, mapdata, st, first)
    lift(io, mapdata, st, "Factory", SHETLAND)
    lift(io, mapdata, st, "Engineering Bay", SHETLAND)
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
        # the Command Center goes once its two SCVs are out, and not in the
        # middle of the army's stages (trial 44: its lift pushed the attack
        # on Finland back)
        if not st.cc_lifted and io.now() - t0 >= 32 and \
                st.stage >= len(ARMY_STAGES):
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
                io.log(f"norway: Finland cleared of Germany's buildings "
                       f"(countdown {trial.round_timer(st.clock.time()) if st.clock else '?'})")
            else:
                army_into_finland(io, watch, mapdata, st, picture)
        if not st.depots_ordered and io.now() - t0 >= DEPOT_FIRST and \
                io.now() - st.depot_look >= DEPOT_EVERY:
            st.depot_look = io.now()
            st.depot_looks += 1
            st.depots_ordered = build_depots(io, st) or \
                st.depot_looks >= DEPOT_LOOKS
        # the Barracks: down by the Heavy Industry before 3:25
        if "Barracks" in st.lifted and "Barracks" not in st.landed and \
                st.finland_clear and st.port_tries >= 1:
            clear_landing(io, watch, mapdata, st, picture)
            io.sleep(1.0)
            if land(io, "Barracks", barracks_spots(mapdata), st):
                io.log(f"norway: Barracks down by the Heavy Industry "
                       f"(countdown {trial.round_timer(st.clock.time()) if st.clock else '?'}; "
                       f"the owner: before 3:25)")
        # Murmansk: Russia's Starport destroyed, then ours lands there
        if st.finland_clear and "Starport" not in st.landed and \
                io.now() - st.last_port >= RETRY_PORT:
            st.last_port = io.now()
            if land(io, "Starport", [(port["x"], port["y"])], st):
                io.log("norway: Starport landed at Murmansk on the Control "
                       "Tower")
            else:
                st.port_tries += 1
                n = attack_russian_starport(io, watch, mapdata, st, picture)
                if n:
                    io.log(f"norway: {n} groups of marines attack Russia's "
                           f"Starport at Murmansk")
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
