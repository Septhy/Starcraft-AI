"""Norway v0.01: the opening (bot/norway.py)."""
from bot import norway, trial
from eyes import live
from tests.test_trial import blob
from PIL import Image


class Clock:
    def __init__(self, io):
        self.io = io

    def update(self, picture):
        pass

    def time(self):
        return self.io.t                # game seconds = real seconds here


class Game:
    """Norway's buildings as the opening sees them: picked, lifted (they
    then show Move), put on keys, landed; Russia's Starport at Murmansk
    standing until the marines attack it; red in Finland until the army
    has attacked a few times."""

    def __init__(self, port_blocks=True, red_looks=3):
        self.t = 0.0
        self.keys, self.clicks, self.combos, self.lines = [], [], [], []
        self.selected = None            # a building kind, "units" or None
        self.up, self.down, self.on_key = set(), set(), {}
        self.placing = False
        self.port_blocks = port_blocks
        self.port_attacked = 0
        self.red_looks = red_looks
        self.attacks = 0

    def now(self):
        return self.t

    def sleep(self, s):
        self.t += s

    def log(self, text):
        self.lines.append(text)

    def shot(self, label, keep=True):
        return label

    def card(self):
        return self.selected

    def type_text(self, text):
        self.lines.append(f"typed {text}")

    def combo(self, held, name):
        self.combos.append((held, name))
        if held == "ctrl" and name.isdigit() and self.selected:
            self.on_key[name] = self.selected

    def key(self, name):
        self.keys.append(name)
        self.t += 0.05
        if name in self.on_key:
            self.selected = self.on_key[name]
        if name == "esc":
            self.placing = False

    def click_with(self, held, x, y):
        self.clicks.append((x, y, held))

    def drag(self, *box):
        self.selected = "units"

    def click(self, x, y, button="left"):
        self.clicks.append((x, y, button))
        self.t += 0.05
        if (x, y) == trial.LIFT_BUTTON and self.selected in self.up:
            self.placing = True         # Land: a spot is clicked next
            return
        if (x, y) == trial.LIFT_BUTTON and self.selected and \
                self.selected != "units":
            self.up.add(self.selected)
            return
        if self.placing and button == "left":
            self.placing = False
            if self.selected == "Starport" and self.port_blocks:
                return                  # Russia's Starport is still there
            self.up.discard(self.selected)
            self.down.add(self.selected)


def setup(monkeypatch, **kw):
    game = Game(**kw)
    m = trial.load_map()

    def pick(io, b):
        io.selected = b["type"]
        return True
    monkeypatch.setattr(trial, "pick_building", pick)
    monkeypatch.setattr(trial, "click_unit", lambda io, x, y, movable=True: (1, 1))
    monkeypatch.setattr(trial, "look_at", lambda io, x, y, wait=0: (x, y))
    monkeypatch.setattr(trial, "opening", lambda io, st, line=None:
                        io.lines.append(f"chat to everyone: {line}"))

    def select(io, pixels, st, watch=None, margin=None, air=False):
        io.selected = "units"
        return True
    monkeypatch.setattr(trial, "select_group", select)

    def attack_move(io, x, y):
        io.attacks += 1
    monkeypatch.setattr(trial, "attack_move", attack_move)
    monkeypatch.setattr(live, "units_selected",
                        lambda card: card == "units" or card in game.up)
    monkeypatch.setattr(live, "building_selected",
                        lambda card: card in game.down)
    real_key = game.key

    def key(name):
        real_key(name)
        if name == "a" and game.selected == "units":
            game.port_attacked += 1
            if game.port_attacked >= 2:
                game.port_blocks = False    # destroyed
    game.key = key
    ours = blob(norway.heavy_industry(m), 3) | \
        blob((120 * 32, 20 * 32), 3)       # troops in the north
    red = blob((143 * 32, 31 * 32), 2)       # Germany's Barracks in Finland

    class Watch:
        def units(self, picture):
            return set(ours)

        def others(self, picture, slots):
            if slots == norway.RED and game.attacks < game.red_looks:
                return set(red)
            return set()

        def forget(self, pixels):
            pass
    monkeypatch.setattr(norway, "red_near", lambda pic, sx, sy, reach=0:
                        20 if game.attacks < game.red_looks else 0)
    st = norway.State()
    st.clock = Clock(game)
    return game, m, Watch(), st


def test_the_opening_in_the_owner_s_order(monkeypatch):
    game, m, watch, st = setup(monkeypatch)
    norway.opening(game, watch, m, st, "first")
    said = [l for l in game.lines if l.startswith("chat to everyone")]
    assert said == ["chat to everyone: AF Norway AI v0.01"]
    # Shetland drop, SCVs, and every building lifted, keyed where it is landed
    assert any("Dropship goes to unload on Shetland" in l for l in game.lines)
    assert any("2 SCVs ordered" in l for l in game.lines)
    assert {"Factory", "Engineering Bay", "Starport", "Barracks",
            "Command Center"} <= set(st.lifted)
    assert game.on_key["6"] == "Barracks" and game.on_key["7"] == "Starport"
    # Finland cleared, then the Barracks down, before Russia's Starport is hit
    assert st.finland_clear and "Barracks" in st.landed
    order = [l for l in game.lines if l.startswith("norway:")]
    i_clear = next(i for i, l in enumerate(order) if "Finland cleared" in l)
    i_port = next(i for i, l in enumerate(order) if "attack Russia's Starport" in l)
    assert i_clear < i_port
    # the marines destroyed it: Norway's Starport lands at Murmansk
    assert "Starport" in st.landed
    assert any("Starport landed at Murmansk" in l for l in game.lines)


def test_with_russia_s_starport_gone_norway_s_simply_lands(monkeypatch):
    """As the owner: the army goes at Russia's Starport first (one attack,
    at an empty spot if it has gone), then Norway's lands there."""
    game, m, watch, st = setup(monkeypatch, port_blocks=False)
    norway.opening(game, watch, m, st, "first")
    assert "Starport" in st.landed
    attacks = [l for l in game.lines if "attack Russia's Starport" in l]
    assert len(attacks) == 1


def test_with_finland_not_cleared_the_barracks_keeps_floating_over_it(monkeypatch):
    """The repository owner's recording (trial 40): the Barracks floats
    over Finland early and lands only once Finland is clear and the army
    has gone on to Murmansk."""
    game, m, watch, st = setup(monkeypatch, red_looks=10 ** 6)
    monkeypatch.setattr(norway, "OPENING_TIME", 120)
    norway.opening(game, watch, m, st, "first")
    assert not st.finland_clear
    assert "Barracks" in st.lifted and "Barracks" not in st.landed
    assert "Starport" not in st.landed  # Russia's is attacked only after Finland


def test_the_army_is_keyed_gathered_then_sent_in_stages(monkeypatch):
    """Trial 40, the repository owner's way: troops on keys, gathered at
    Kiruna, then the Finland spot, Factory 10, Helsinki, one order a key
    about every ten seconds, never a stream of boxes."""
    game, m, watch, st = setup(monkeypatch)
    norway.opening(game, watch, m, st, "first")
    assert st.army_keys and st.army_keys[0] == "1"
    stages = [l for l in game.lines if l.startswith("norway: the army ")]
    names = [s for s in stages if "attacks at " in s or "moves to " in s]
    spots = [s.rsplit("(", 1)[1].rstrip(")") for s in names]
    # trial 47: the flank at (147, 31) just before the bunkers
    # trial 49: then further in (143, 34), the bunkers, then the turrets
    assert spots == ["143, 16", "147, 30", "147, 31", "143, 34", "140, 39",
                     "134, 36"]
    assert all("moves to" in names[i] for i in (0, 2, 3))
    assert all("attacks" in n for n in names[4:])
    landed = next(l for l in game.lines if "Barracks landed by" in l)
    assert landed.endswith("149, 39")      # the owner, trial 52


def test_the_barracks_lands_at_149_39_only():
    """The owner (trial 52): just land it at (149, 39), no clicking on
    one spot after another."""
    m = trial.load_map()
    assert norway.barracks_spots(m) == [norway.BARRACKS_SPOT]
    assert (norway.BARRACKS_SPOT[0] // 32, norway.BARRACKS_SPOT[1] // 32) == (149, 39)
    port = norway.russia_starport(m)
    assert (port["x"] // 32, port["y"] // 32) == (156, 5)   # the owner attacks (156, 4)


def test_the_app_can_play_either_country(tmp_path, monkeypatch):
    from bot import memory
    monkeypatch.setenv("STARCRAFT_BOT_HOME", str(tmp_path))
    assert memory.load_country() == "Russia"
    memory.save_country("Norway")
    assert memory.load_country() == "Norway"
    memory.save_country("Atlantis")
    assert memory.load_country() == "Russia"


def test_every_key_the_bots_press_can_be_pressed():
    """Trial 39: Norway pressed U (unload) and the input layer had no U:
    the game stopped at once. Every key named in the bots must exist."""
    import pathlib
    import re
    root = pathlib.Path(__file__).resolve().parent.parent
    src = (root / "hands" / "win.py").read_text()
    start = src.index("SCAN = {")
    end = src.index("\n", src.index('SCAN.update(dict(zip("zxcvbnm"')) + 1
    ns = {}
    exec(src[start:end], ns)
    scan = ns["SCAN"]
    used = set()
    for name in ("trial.py", "norway.py"):
        code = (root / "bot" / name).read_text()
        used |= set(re.findall(r'\.key\("([^"]+)"\)', code))
        used |= {k for pair in re.findall(r'\.combo\("([^"]+)", "([^"]+)"\)', code)
                 for k in pair}
        used |= set(re.findall(r'click_with\("([^"]+)"', code))
    used |= set(norway.KEYS.values()) | set(trial.AIR_KEYS)
    missing = sorted(k for k in used if k not in scan)
    assert not missing, missing


def test_each_army_key_is_filled_box_after_box_up_to_a_dozen(monkeypatch):
    """Trial 41: one box a key left most of the army unkeyed. Boxes are
    added to a key with Shift until it holds a dozen, then the next key."""
    game, m, watch, st = setup(monkeypatch)
    blobs = [blob((x * 32, y * 32), 3) for x, y in
             [(100, 60), (110, 62), (118, 20), (105, 10), (140, 14), (90, 50)]]

    class W:
        def units(self, picture):
            return set().union(*blobs)

        def others(self, picture, slots):
            return set()

        def forget(self, pixels):
            pass
    sizes = iter([5, 6, 4, 7, 3, 2] + [1] * 200)
    monkeypatch.setattr(norway, "selected", lambda io: next(sizes))
    norway.key_army(game, W(), m, st, "first")
    assert len(st.army_keys) >= 2
    assert all(n <= 12 for n in st.army_held.values())
    assert st.army_held["1"] >= 11            # filled before the next key
    for k in st.army_keys:                    # made once, then added to
        assert game.combos.count(("ctrl", k)) == 1
    assert ("shift", "1") in game.combos


def test_the_army_attacks_one_building_together(monkeypatch):
    """Trial 43: shared out over several red buildings the army was cut
    down piece by piece. Every key attacks the red nearest our men."""
    game, m, watch, st = setup(monkeypatch)
    st.army_keys = ["1", "2", "3"]
    cam = (4000, 1000)
    monkeypatch.setattr(trial, "look_at", lambda io, x, y, wait=0: cam)
    monkeypatch.setattr(trial, "enemy_mask", lambda pic: "mask")
    far, near_ = (1500, 200), (900, 450)
    monkeypatch.setattr(trial, "patches",
                        lambda mask: [(40, *far), (40, *near_), (40, 300, 300)])
    army = trial.screen_to_map(850, 500, cam)
    assert norway.attack_on_screen(game, st, (4100, 1100), army) == 3
    lefts = [(x, y) for x, y, b in game.clicks if b == "left"]
    assert lefts[-3:] == [near_] * 3
    assert game.keys.count("a") >= 3


def test_every_starting_group_is_boxed_from_the_map(monkeypatch):
    """Trial 45: men beside a bunker are hidden on the minimap by the
    building, so Sweden's (105, 66) and Kiruna's (141, 8) were never
    boxed. Every place where the map starts Norway's troops is boxed."""
    game, m, watch, st = setup(monkeypatch)
    groups = norway.start_groups(m)
    tiles = {(x // 32, y // 32) for g in groups for x, y in g}
    assert (105, 66) in tiles and (141, 7) in tiles
    units = m["slots"]["4"]["units"]
    home = [u for u in units if norway.in_denmark(*u)]
    assert home                            # Denmark's marines (trial 51)...
    assert sum(len(g) for g in groups) == len(units) - len(home)
    assert not any(norway.in_denmark(*p) for g in groups for p in g)  # ...left
    boxed = []
    monkeypatch.setattr(norway, "box_start_group",
                        lambda io, pts: boxed.append(pts) or True)
    monkeypatch.setattr(norway, "selected", lambda io: 2)
    norway.key_army(game, watch, m, st, "first")
    for g in groups:                       # every group, while boxes last
        if len(boxed) < norway.ARMY_BOXES:
            assert g in boxed


def test_germany_s_buildings_are_cleared_one_by_one_turrets_too(monkeypatch):
    """The owner (trial 45): the turrets too must go by 3:25. Each of
    Germany's buildings in Finland is attacked by every key until no red
    is left there, then the next."""
    game, m, watch, st = setup(monkeypatch)
    st.army_keys = ["1", "2"]
    kinds = [k for k, x, y in norway.german_buildings(m)]
    assert kinds.count("Missile Turret") == 4 and "Bunker" in kinds
    standing = {"on": True}
    buildings = norway.german_buildings(m)

    class W:
        def units(self, picture):
            return blob(norway.heavy_industry(m), 3)

        def others(self, picture, slots):
            out = set()
            for k, x, y in buildings:
                if standing["on"] or (x, y) != first_xy[0]:
                    out |= blob((x, y), 2)
            return out

        def forget(self, pixels):
            pass
    first_xy = [None]
    w = W()
    # trial 46: gone is told by the minimap, not the screen's red
    monkeypatch.setattr(norway, "red_near", lambda *a, **k: 0)
    st.targets = norway.german_buildings(m)
    hx, hy = norway.heavy_industry(m)
    st.targets.sort(key=lambda b: (b[1] - hx) ** 2 + (b[2] - hy) ** 2)
    first_xy[0] = st.targets[0][1:]
    assert norway.clear_buildings(game, w, m, st, "pic") == 2
    first = st.targets[0]
    assert first[1:] == first_xy[0]       # still there: attacked, not crossed off
    standing["on"] = False                # it falls
    norway.clear_buildings(game, w, m, st, "pic")
    assert first not in st.targets
    assert any("is gone" in l for l in game.lines)


def test_the_barracks_waits_out_of_reach_and_the_army_goes_first(monkeypatch):
    """Trial 44: floated straight over the Heavy Industry, the Barracks
    was shot up; it waits by the Norwegian military camp until Finland is
    clear. And the army is keyed and on its way before the lifts."""
    game, m, watch, st = setup(monkeypatch)
    norway.opening(game, watch, m, st, "first")
    lines = [l for l in game.lines if l.startswith("norway:")]
    lifted = next(l for l in lines if l.startswith("norway: Barracks lifted"))
    wx, wy = norway.BARRACKS_WAIT
    assert trial.place_name(m, wx, wy) in lifted
    hx, hy = norway.heavy_industry(m)
    assert ((wx - hx) ** 2 + (wy - hy) ** 2) ** 0.5 >= 10 * 32
    i_army = next(i for i, l in enumerate(lines) if "moves to Kiruna" in l)
    i_lift = next(i for i, l in enumerate(lines) if "Factory lifted" in l)
    assert i_army < i_lift


def test_the_barracks_flies_in_as_the_army_attacks_the_finland_spot(monkeypatch):
    """The owner (trials 46, 47): the Barracks must reach Helsinki much
    sooner. It flies in over Finland as the army attacks the Finland
    spot, long before Finland is clear."""
    game, m, watch, st = setup(monkeypatch)
    norway.opening(game, watch, m, st, "first")
    lines = [l for l in game.lines if l.startswith("norway:")]
    i_in = next(i for i, l in enumerate(lines) if "Barracks flies in" in l)
    i_move = next(i for i, l in enumerate(lines)
                  if "attacks at Russian army-Finland" in l)
    i_clear = next(i for i, l in enumerate(lines) if "Finland cleared" in l)
    assert i_in <= i_move + 1 and i_in < i_clear


def test_each_box_sets_off_for_kiruna_as_it_is_keyed(monkeypatch):
    """The owner (trial 48): the men move up to Kiruna while the rest are
    being keyed, not after."""
    game, m, watch, st = setup(monkeypatch)
    monkeypatch.setattr(norway, "box_start_group", lambda io, pts: True)
    monkeypatch.setattr(norway, "selected", lambda io: 3)
    norway.key_army(game, watch, m, st, "first")
    kiruna = trial.live.minimap_point(143 * 32, 16 * 32)
    rights = [c for c in game.clicks if c[2] == "right" and c[:2] == kiruna]
    assert len(rights) >= len(st.army_keys) and len(rights) >= 4


def test_germany_s_buildings_are_attacked_in_one_chain(monkeypatch):
    """Trial 48: one order at a time, the army stood 6 to 13 s between
    buildings. Every key gets the whole chain at once (Shift), nearest
    first, and it is not given again while the army is on its way."""
    game, m, watch, st = setup(monkeypatch)
    st.army_keys = ["1", "2"]
    buildings = norway.german_buildings(m)

    class W:
        def units(self, picture):
            return blob(norway.heavy_industry(m), 3)

        def others(self, picture, slots):
            out = set()
            for k, x, y in buildings:
                out |= blob((x, y), 2)
            return out
    assert norway.clear_buildings(game, W(), m, st, "pic") == 2
    queued = [c for c in game.clicks if c[2] == "shift"]
    n = norway.CHAIN_LONGEST
    assert len(queued) == 2 * (n - 1)
    assert game.combos.count(("shift", "a")) == 2 * (n - 1)
    # trial 49: the bunkers and the turrets before anything else
    assert all(k in norway.FIRST_KINDS for k, x, y in st.chain)
    game.t += 2
    assert norway.clear_buildings(game, W(), m, st, "pic") == 0   # on its way


def test_a_quick_wrong_read_never_counts_as_landed(monkeypatch):
    """Trial 50: right after the depots, the Starport's key was read too
    soon (the SCV's build menu still showed) and it counted as landed;
    its landing was never tried and the Barracks never came down. A
    building counts as down only after a landing was tried and two reads
    agree."""
    game, m, watch, st = setup(monkeypatch)
    game.up.add("Starport")
    game.on_key["7"] = "Starport"
    reads = iter(["build-menu"] + [None] * 50)
    real_card = game.card
    monkeypatch.setattr(trial.live, "building_selected",
                        lambda card: card in game.down or card == "build-menu")
    game.card = lambda: next(reads, None) or real_card()
    norway.land(game, "Starport", [(4992, 176)], st)
    assert "Starport" not in st.landed or "Starport" in game.down


def test_an_scv_repairs_the_barracks_once_it_is_down(monkeypatch):
    """The owner (trial 50): after Finland, an SCV comes and repairs the
    Barracks in Helsinki (R, then a click on it)."""
    game, m, watch, st = setup(monkeypatch)
    monkeypatch.setattr(live, "scv_selected", lambda card: True)
    assert norway.repair_barracks(game, st)
    assert ("ctrl", norway.SCV_KEY) in game.combos     # found once, then keyed
    assert "r" in game.keys
    assert any("repair the Barracks" in l for l in game.lines)


def test_with_the_bunkers_down_the_keys_share_the_turrets_out(monkeypatch):
    """The owner (trial 51): all of Finland by about 63 s or the German
    army comes. Turrets do not shoot men on foot: with the bunkers down,
    the keys split into two groups at the two ends of the turrets."""
    game, m, watch, st = setup(monkeypatch)
    st.army_keys = ["1", "2", "3", "4"]
    turrets = [b for b in norway.german_buildings(m) if b[0] == "Missile Turret"]

    class W:
        def units(self, picture):
            return blob(norway.heavy_industry(m), 3)

        def others(self, picture, slots):
            out = set()
            for k, x, y in turrets:
                out |= blob((x, y), 2)
            return out
    st.targets = list(turrets)
    norway.clear_buildings(game, W(), m, st, "pic")
    firsts = []
    plain = [c for c in game.clicks if c[2] == "left"]
    firsts = plain[-4:]
    # (trial 52: two groups, the keys taking turns, not one turret a key)
    assert len(set(firsts)) == 2 and firsts[0] == firsts[2] \
        and firsts[1] == firsts[3]


def test_the_barracks_waits_out_of_the_bunkers_reach_then_moves_over(monkeypatch):
    """Trial 52: floated straight to (139, 33) at 25 s, the Barracks was
    shot down to 60 of 1000 by the west bunker. It waits out of reach and
    moves over (139, 33) once the bunkers are down."""
    nx, ny = norway.BARRACKS_NEAR
    for k, x, y in norway.german_buildings(trial.load_map()):
        if k == "Bunker":
            assert ((x - nx) ** 2 + (y - ny) ** 2) ** 0.5 >= 9 * 32
    game, m, watch, st = setup(monkeypatch)
    norway.opening(game, watch, m, st, "first")
    lines = [l for l in game.lines if l.startswith("norway:")]
    i_in = next(i for i, l in enumerate(lines) if "Barracks flies in" in l)
    i_over = next(i for i, l in enumerate(lines) if "Barracks moves over" in l)
    assert i_in < i_over
    i_lift = next(i for i, l in enumerate(lines) if "Factory lifted" in l)
    i_clear = next(i for i, l in enumerate(lines) if "Finland cleared" in l)
    assert i_lift > i_clear               # the Shetland lifts after Finland


def test_depots_one_at_a_time_ten_by_arkhangelsk(monkeypatch):
    """The owner (trial 52): ten depots by Arkhangelsk, as in their
    recording: the SCVs boxed, B, S, a click on a free spot, one depot an
    order (four queued in one order were never built)."""
    game, m, watch, st = setup(monkeypatch)
    reads = []

    def units(card):
        # after the box: units; after B: the build menu; after the click:
        # the SCV's own buttons again
        return reads.pop(0) if reads else True
    monkeypatch.setattr(trial.live, "units_selected", units)
    monkeypatch.setattr(live, "scv_selected", lambda card: True)
    for _ in range(norway.DEPOTS):
        reads[:] = [False, True]
        assert norway.build_depots(game, st)
    assert st.depots_placed == norway.DEPOTS == 10
    assert not any(c[2] == "shift" for c in game.clicks)     # never queued
    tiles = norway.DEPOT_TILES[:10]
    assert len(set(tiles)) == 10
    for (ax, ay) in tiles:                # a depot's width apart
        for (bx, by) in tiles:
            if (ax, ay) != (bx, by):
                assert abs(ax - bx) >= 3 or abs(ay - by) >= 3
    # what stands there is not an SCV (B leaves Move): no depot
    reads[:] = [True]
    assert not norway.build_depots(game, st)
    # no SCV anywhere (trial 55: two marines left selected were taken
    # for SCVs): no depot, nothing pressed for one
    monkeypatch.setattr(live, "scv_selected", lambda card: False)
    st.scvs_keyed = False
    assert not norway.build_depots(game, st)


def test_the_army_steps_off_the_starport_spot_before_it_lands(monkeypatch):
    """Trial 52: our marines stood on Russia's Starport's spot: "You can't
    land there". After the attack the army steps aside, then it lands."""
    game, m, watch, st = setup(monkeypatch)
    norway.opening(game, watch, m, st, "first")
    lines = [l for l in game.lines if l.startswith("norway:")]
    i_attack = next(i for i, l in enumerate(lines) if "attack Russia's Starport" in l)
    i_aside = next(i for i, l in enumerate(lines) if "steps off" in l)
    i_land = next(i for i, l in enumerate(lines) if "Starport landed" in l)
    assert i_attack < i_aside < i_land


def outline(colour):
    img = Image.new("RGB", (1920, 1080), (40, 40, 40))
    if colour:
        px = {"green": (20, 220, 20), "red": (220, 20, 20)}[colour]
        img.paste(px, (900, 500, 940, 530))
    return img


class Hover:
    """A screen whose outline colour depends on where the mouse is."""
    def __init__(self, colour_at):
        self.colour_at, self.at, self.lines = colour_at, None, []

    def hover(self, x, y):
        self.at = (x, y)

    def sleep(self, s):
        pass

    def log(self, text):
        self.lines.append(text)

    def shot(self, label, keep=True):
        return self.colour_at(self.at)


def test_a_red_outline_is_moved_a_tile_until_green():
    sx, sy = 920, 515
    io = Hover(lambda at: outline("green" if at != (sx, sy) else "red"))
    img_at = {}

    def colour(at):
        img = outline(None)
        c = "red" if at == (sx, sy) else "green"
        tile = 32 * live.ZOOM            # a depot's 3 x 2 footprint
        img.paste({"green": (20, 220, 20), "red": (220, 20, 20)}[c],
                  (int(at[0] - 1.5 * tile), int(at[1] - tile),
                   int(at[0] + 1.5 * tile), int(at[1] + tile)))
        return img
    io.colour_at = colour
    spot = norway.green_spot(io, sx, sy, "depot")
    assert spot != (sx, sy) and spot is not None
    assert any("green" in l for l in io.lines)


def test_all_red_is_never_clicked_and_no_outline_clicks_as_before():
    def red(at):
        img = outline(None)
        img.paste((220, 20, 20), (at[0] - 20, at[1] - 15, at[0] + 20, at[1] + 15))
        return img
    assert norway.green_spot(Hover(red), 920, 515, "depot") is None
    # no footprint seen: never clicked blind (trial 54)
    assert norway.green_spot(Hover(lambda at: outline(None)), 920, 515,
                             "depot") is None

    class NoHover:
        pass
    assert norway.green_spot(NoHover(), 920, 515, "x") == (920, 515)


def test_one_red_square_is_red_and_the_starport_is_never_moved():
    def part_red(at):
        img = outline(None)
        img.paste((20, 220, 20), (at[0] - 40, at[1] - 30, at[0] + 40, at[1] + 30))
        img.paste((220, 20, 20), (at[0] - 40, at[1] - 30, at[0] - 10, at[1] - 10))
        return img
    io = Hover(part_red)
    seen = []
    io.hover = lambda x, y: (seen.append((x, y)), setattr(io, "at", (x, y)))
    assert norway.green_spot(io, 920, 515, "land-starport",
                             nudges=[(0, 0)]) is None
    assert seen == [(920, 515)]            # never moved off the spot


def test_the_real_dim_tints_of_trial_54_are_read():
    """Trial 54: the footprint is a see-through tint, green about
    (28, 90, 20), red about (100, 40, 25), on grass (29, 34, 16)."""
    tile = int(32 * live.ZOOM)
    img = Image.new("RGB", (1920, 1080), (29, 34, 16))
    img.paste((28, 90, 20), (800, 300, 800 + 4 * tile, 300 + 3 * tile))
    cx, cy = 800 + 2 * tile, 300 + 1.5 * tile
    assert norway.outline_colour(img, cx, cy) == "green"
    img.paste((100, 40, 25), (800, 300, 800 + tile, 300 + tile))
    assert norway.outline_colour(img, cx, cy) == "red"
    assert norway.outline_colour(Image.new("RGB", (1920, 1080), (29, 34, 16)),
                                 cx, cy) is None
    fire = Image.new("RGB", (1920, 1080), (29, 34, 16))
    fire.paste((28, 90, 20), (800, 300, 800 + 4 * tile, 300 + 3 * tile))
    fire.paste((250, 160, 40), (800, 300, 800 + tile, 300 + tile))  # flames
    assert norway.outline_colour(fire, cx, cy) == "green"


def test_the_starport_lands_in_the_middle_of_the_light_green_box():
    """The owner's recording: a thin bright green box, a Starport's size,
    shows where it must land to take the Control Tower; the Starport's
    footprint is centred on it."""
    from PIL import ImageDraw
    tile = 32 * live.ZOOM
    box = (826, 196, int(826 + 4 * tile), int(196 + 3 * tile))

    def screen(at):
        img = outline(None)
        d = ImageDraw.Draw(img)
        d.rectangle(box, outline=(40, 200, 40), width=2)
        d.line((300, 630, 1500, 630), fill=(40, 200, 40), width=3)  # chat text
        return img
    io = Hover(screen)
    got = norway.tower_spot(io, 1081, 300, "land-tower")
    assert got == ((box[0] + box[2]) // 2, (box[1] + box[3]) // 2) or \
        max(abs(got[0] - (box[0] + box[2]) / 2), abs(got[1] - (box[1] + box[3]) / 2)) <= 2
    io = Hover(lambda at: outline(None))
    assert norway.tower_spot(io, 900, 500, "land-tower") == (900, 500)


def real(name):
    """A real picture (cut to the game area at 640, 40) put back on a
    full screen."""
    import os
    img = Image.new("RGB", (1920, 1080), (0, 0, 0))
    img.paste(Image.open(os.path.join(os.path.dirname(__file__), "data",
                                      name)), (640, 40))
    return img


def test_real_pictures_box_and_red_footprints():
    box = norway.tower_box(real("starport_box.jpg"), 1081, 300)
    assert box and abs(box[0] - 826) <= 3 and abs(box[2] - 1117) <= 3 and \
        abs(box[1] - 196) <= 3 and abs(box[3] - 415) <= 3
    # trial 54: both landings were over red; read as red, never clicked
    assert norway.outline_colour(real("starport_red.jpg"), 1081, 397) == "red"
    assert norway.outline_colour(real("barracks_red.jpg"), 1080, 470) == "red"
    assert norway.tower_box(real("starport_red.jpg"), 1081, 397) is None


def test_an_scv_is_told_by_its_build_button_not_by_move():
    assert live.scv_selected(real("scv_card.jpg"))
    assert not live.scv_selected(real("marines_card.jpg"))


def test_the_scvs_are_rallied_the_owner_s_way(monkeypatch):
    game, m, watch, st = setup(monkeypatch)
    norway.make_scvs(game, m, st)
    assert game.keys[:3] == ["s", "s", "r"]
    assert game.clicks[-1][2] == "left"          # R, then a click on the minimap
    assert st.cc_home
