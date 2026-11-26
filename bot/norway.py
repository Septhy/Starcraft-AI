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
- the starting army attacks Finland until every red (Germany) building
  there is destroyed;
- the Barracks lands next to the Heavy Industry (the "Factory 10"
  building), our men moved out of the way first, before 3:25 on the
  round countdown: it taxes Helsinki and Factory 10;
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
DEPOTS_AT = (183, 24)          # tiles: the far north-east, where the samples
                               # built their depots (for safety)
DEPOT_SPOTS = [(0, 0), (3, 0), (6, 0), (0, 3), (3, 3), (6, 3), (0, 6), (3, 6)]
DEPOTS = 4                     # depots the two SCVs build in the opening
FINLAND = (125, 15, 150, 50)   # tiles: where Germany's buildings in Finland stand
NORTH_ARMY = (95, 0, 160, 33)  # tiles: our starting troops in the north
RED = [0]                      # Germany
CLEAR_LOOKS = 2                # looks in a row with no red in Finland: cleared
BARRACKS_BY = 3 * 60 + 25      # the countdown (3:25) by which the Barracks is down
BARRACKS_GO = 3 * 60 + 50      # the countdown when it lands even if not cleared
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
    return [(x - 5 * T, y), (x + 5 * T, y), (x, y + 4 * T), (x, y - 4 * T),
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


def army_into_finland(io, watch, mapdata, st, picture):
    """Our troops in the north attack-move at Germany's buildings in
    Finland: at the red that is left, else at Factory 10."""
    ours = watch.units(picture)
    l, t, r, b = NORTH_ARMY
    north = {p for p in ours
             if l <= live.from_drawn(*p)[0] / T < r
             and t <= live.from_drawn(*p)[1] / T < b}
    red = finland_red(watch, picture)
    if red:
        target = live.from_drawn(*min(red, key=lambda p: p[1]))
    else:
        target = heavy_industry(mapdata)
    sent = 0
    for group in live.clusters(north, 6, 6)[:6]:
        if len(group) >= 2 and trial.select_group(io, group, st, watch,
                                                  margin=60):
            trial.attack_move(io, *target)
            sent += 1
    return sent


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
    """The marines in Finland attack Russia's Starport at Murmansk (A,
    then a click on it)."""
    port = russia_starport(mapdata)
    ours = trial.near(watch.units(picture), heavy_industry(mapdata), 16)
    groups = [g for g in live.clusters(ours, 6, 6) if len(g) >= 2][:4]
    if not groups:
        return 0
    sent = 0
    for group in groups:
        if not trial.select_group(io, group, st, watch, margin=60):
            continue
        cam = trial.look_at(io, *trial.centred(port["x"], port["y"]), wait=0.2)
        io.key("a")
        io.sleep(0.04)
        io.click(*live.on_screen(port["x"], port["y"], cam))
        io.sleep(0.05)
        sent += 1
    return sent


def opening(io, watch, mapdata, st, first):
    """The whole opening, in the owner's order, until the Barracks and the
    Starport are down or OPENING_TIME is up."""
    t0 = io.now()
    trial.opening(io, st, line=OPENING_LINE)
    drop_on_shetland(io, mapdata)
    make_scvs(io, mapdata)
    lift(io, mapdata, st, "Factory", SHETLAND)
    lift(io, mapdata, st, "Engineering Bay", SHETLAND)
    port = russia_starport(mapdata)
    lift(io, mapdata, st, "Starport", (port["x"], port["y"] + 8 * T),
         key=KEYS["Starport"])
    hx, hy = heavy_industry(mapdata)
    lift(io, mapdata, st, "Barracks", (hx - 8 * T, hy), key=KEYS["Barracks"])
    army_into_finland(io, watch, mapdata, st, first)
    while io.now() - t0 < OPENING_TIME:
        picture = io.shot("watch", keep=False)
        if st.clock is not None:
            st.clock.update(picture)
        left = countdown(st)
        # the Command Center goes once its two SCVs are out (about 30 s)
        if not st.cc_lifted and io.now() - t0 >= 32:
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
        if not st.depots_ordered and io.now() - t0 >= 55:
            st.depots_ordered = build_depots(io, st) or io.now() - t0 > 120
        # Finland: attack until no red is left
        if not st.finland_clear and io.now() - st.last_look >= LOOK_EVERY:
            st.last_look = io.now()
            red = finland_red(watch, picture)
            st.clear_looks = 0 if red else st.clear_looks + 1
            if st.clear_looks >= CLEAR_LOOKS:
                st.finland_clear = True
                io.log(f"norway: Finland cleared of Germany's buildings "
                       f"(countdown {trial.round_timer(st.clock.time()) if st.clock else '?'})")
            else:
                army_into_finland(io, watch, mapdata, st, picture)
        # the Barracks: down by the Heavy Industry before 3:25
        late = left is not None and left <= BARRACKS_GO
        if "Barracks" in st.lifted and "Barracks" not in st.landed and \
                (st.finland_clear or late):
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
