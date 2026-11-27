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
        self.targeting = False          # after U: the game asks for a target

    def now(self):
        return self.t

    def sleep(self, s):
        self.t += s

    def log(self, text):
        self.lines.append(text)

    def shot(self, label, keep=True):
        return label

    def card(self):
        return "blank" if self.targeting else self.selected

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
            self.targeting = False
        if name == "u" and self.selected == "units":
            self.targeting = True

    def click_with(self, held, x, y, button="left"):
        self.clicks.append((x, y, held))

    def drag(self, *box):
        self.selected = "units"

    def click(self, x, y, button="left"):
        self.clicks.append((x, y, button))
        self.t += 0.05
        if self.targeting:
            self.targeting = False      # the target is given
            return
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
    # (the checks added after trial 59, read off this small game's state)
    monkeypatch.setattr(live, "move_shown",
                        lambda card: card == "units" or card in game.up)
    monkeypatch.setattr(live, "building_card", lambda card: card in game.down)
    monkeypatch.setattr(live, "placing_shown", lambda card: card == "blank")
    monkeypatch.setattr(live, "build_menu_shown", lambda card: False)
    # the SCVs, the depots and the repair have their own tests (World,
    # below); in this small game they simply work
    monkeypatch.setattr(norway, "army_selected",
                        lambda io: norway.selected(io) or 1)

    def take(io, st):
        st.scv_count = 2
        io.log("norway: 2 SCVs below the Command Center, on key 9")
        return 2
    monkeypatch.setattr(norway, "take_scvs", take)
    monkeypatch.setattr(norway, "call_scvs", lambda io, st: st.scv_count)

    def depot(io, st):
        st.depots_placed += 1
        io.log(f"norway: supply depot {st.depots_placed} of {norway.DEPOTS} "
               f"ordered by Arkhangelsk")
        return "placed"
    monkeypatch.setattr(norway, "build_depot", depot)

    def repair(io, st):
        io.log("norway: an SCV goes to repair the Barracks")
        return True
    monkeypatch.setattr(norway, "repair_barracks", repair)
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
    # the SCVs on their key once the army has left, sent to Arkhangelsk,
    # ten depots there and the Barracks repaired
    order = [l for l in game.lines if l.startswith("norway:")]
    i_scv = next(i for i, l in enumerate(order) if "Command Center, on key 9" in l)
    i_spot = next(i for i, l in enumerate(order) if "attacks at Russian army-Finland" in l)
    i_walk = next(i for i, l in enumerate(order) if "walk to Arkhangelsk" in l)
    assert i_spot < i_scv < i_walk
    assert st.depots_placed == norway.DEPOTS and st.depots_ordered
    assert any("repair the Barracks" in l for l in game.lines)
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
    monkeypatch.setattr(trial.live, "building_card",
                        lambda card: card in game.down or card == "build-menu")
    game.card = lambda: next(reads, None) or real_card()
    norway.land(game, "Starport", [(4992, 176)], st)
    assert "Starport" not in st.landed or "Starport" in game.down


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


def test_the_starport_is_landed_once_after_the_attack(monkeypatch):
    """Trial 58: the landing is one step after Russia's Starport is gone,
    one click, then only a wait for it to come down."""
    game, m, watch, st = setup(monkeypatch)
    norway.opening(game, watch, m, st, "first")
    lines = [l for l in game.lines if l.startswith("norway:")]
    i_attack = next(i for i, l in enumerate(lines) if "attack Russia's Starport" in l)
    i_land = next(i for i, l in enumerate(lines) if "Starport landed" in l)
    assert i_attack < i_land


TINT = {"green": (28, 90, 20), "red": (100, 40, 25)}   # trial 54's real tints


def outline(colour):
    img = Image.new("RGB", (1920, 1080), (29, 34, 16))
    if colour:
        img.paste(TINT[colour], (900, 500, 940, 530))
    return img


def paint(img, centre, size, colour):
    """A footprint of `size` tiles drawn with its middle at `centre`."""
    tile = 32 * live.ZOOM
    w, h = size[0] * tile, size[1] * tile
    img.paste(TINT[colour], (int(centre[0] - w / 2), int(centre[1] - h / 2),
                             int(centre[0] + w / 2), int(centre[1] + h / 2)))
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


def test_an_scv_is_spotted_on_the_screen_and_the_view_read_from_the_minimap():
    """The owner (after trial 56): the SCVs are looked for on the game
    screen. The SCV in the owner's recording is spotted; the view is read
    from the minimap's white box, also with its top cut off at the map's
    edge."""
    pic = Image.open("tests/data/scv_on_grass.jpg")
    spots = norway.scv_spots(pic)
    assert spots and abs(spots[0][0] - 1235) < 40 and abs(spots[0][1] - 470) < 40
    cam = live.camera_from_minimap(pic)
    assert cam and abs(cam[0] / 32 - 181) < 2 and abs(cam[1] / 32 - 27) < 2
    cam = live.camera_from_minimap(Image.open("tests/data/minimap_top_edge.jpg"))
    assert cam and abs(cam[0] / 32 - 157) < 2


def test_the_starport_lands_on_the_box_the_owner_s_way():
    """The owner's recording: Land, then the mouse near the light green
    box's top-left corner. The game puts the footprint's top-left tile
    under the mouse (trials 56, 57), so the mouse goes on the box's
    top-left tile and the footprint lands on the box."""
    from PIL import ImageDraw
    tile = 32 * live.ZOOM
    box = (718, 287, int(718 + 4 * tile), int(287 + 3 * tile))

    def screen(at):
        img = outline(None)
        d = ImageDraw.Draw(img)
        d.rectangle(box, outline=(40, 200, 40), width=2)
        # the footprint's top-left corner on the tile under the mouse
        gx = 718 + ((at[0] - 718) // tile) * tile
        gy = 287 + ((at[1] - 287) // tile) * tile
        return paint(img, (gx + 2 * tile, gy + 1.5 * tile), (4, 3), "green")
    io = Hover(screen)
    mouse = norway.port_spot(io, 1008, 397)
    assert mouse and box[0] <= mouse[0] < box[0] + tile and \
        box[1] <= mouse[1] < box[1] + tile
    assert norway.port_spot(Hover(lambda at: outline(None)), 1008, 397) is None


def test_the_darker_scv_at_murmansk_is_spotted():
    """Trial 57: the SCV at Murmansk, darker orange (about (164, 100, 26)),
    was missed by the sweep."""
    spots = norway.scv_spots(Image.open("tests/data/scv_murmansk.jpg"))
    assert any(abs(x - 825) < 40 and abs(y - 110) < 40 for x, y in spots)


def test_the_scvs_in_an_army_key_are_told_by_their_wireframe():
    """Trial 58: the army's key held two SCVs (frames 2 and 7 of ten)
    among the marines."""
    pic = Image.open("tests/data/army_key_with_scvs.jpg")
    assert live.scv_frames(pic, 10) == [1, 6]


def test_russia_s_starport_is_looked_at_by_a_click_not_by_land(monkeypatch):
    """The owner (trial 58): one landing attempt only. Whether Russia's
    Starport still stands is seen by clicking it with ours selected: no
    Land button is pressed for that."""
    game, m, watch, st = setup(monkeypatch)
    game.hover = lambda x, y: None
    port = norway.russia_starport(m)
    game.up.add("Starport")
    game.on_key[norway.KEYS["Starport"]] = "Starport"
    standing = {"yes": True}
    real_click = game.click

    def click(x, y, button="left"):
        real_click(x, y, button)
        if (x, y) != trial.LIFT_BUTTON and standing["yes"]:
            game.selected = "russia"            # Russia's Starport picked
    game.click = click
    assert not norway.russia_port_gone(game, st, port)
    standing["yes"] = False
    game.selected = None
    assert norway.russia_port_gone(game, st, port)
    assert trial.LIFT_BUTTON not in [(c[0], c[1]) for c in game.clicks]


# ---------------------------------------------------------------------------
# After trial 59: the SCVs, the depots, the Dropship.
#
# What the recordings showed (docs/norway-notes.md): the new SCVs and the
# Dropship were swept onto the army's keys; "is this an SCV?" never said
# yes in a live game; units on the move show a white Move button; with two
# SCVs selected there are no Build buttons; the footprint of a building
# hangs from the tile under the mouse; and the Russia bot's camera puts
# things two tiles too high. The tests below use real pictures for what
# the bot reads, and a small model of the game (World) for what it does.

def hud(name):
    """A real picture of the bottom panel (cut at 560, 780) put back on a
    full screen."""
    import os
    img = Image.new("RGB", (1920, 1080), (0, 0, 0))
    img.paste(Image.open(os.path.join(os.path.dirname(__file__), "data",
                                      name)), (560, 780))
    return img


def card_of(img):
    """What the live bot's quick card look returns: the first button only."""
    return img.crop(live.CARD_CELL)


def test_the_scv_check_needs_the_whole_screen_and_says_so():
    """Trials 56 to 59: scv_selected was handed the quick card picture (the
    first button only), cut an empty piece out of it and said no every
    time, with an SCV selected too. With the whole screen it is right; with
    the small picture it must not pretend to know."""
    scv = hud("hud_scv_idle.jpg")
    assert live.scv_selected(scv)
    assert live.scv_selected(hud("hud_scv_moving.jpg"))
    assert not live.scv_selected(card_of(scv))          # cannot tell: no
    assert not live.scv_selected(hud("hud_two_scvs.jpg"))   # two: no Build buttons
    assert not live.scv_selected(hud("hud_build_menu.jpg"))
    assert not live.scv_selected(hud("hud_box_scvs.jpg"))


def test_a_white_move_button_is_still_move():
    """The game draws a unit's current order in white: an SCV on the move
    shows a white Move button. The check fitted on the yellow one says no
    (so a moving SCV, or a building flying somewhere, was not seen as
    selected); move_shown knows both, on the whole screen and on the quick
    card picture alike."""
    idle, moving = hud("hud_scv_idle.jpg"), hud("hud_scv_moving.jpg")
    assert live.units_selected(idle) and not live.units_selected(moving)
    for pic in (idle, moving, hud("hud_two_scvs.jpg"), hud("hud_box_scvs.jpg")):
        assert live.move_shown(pic) and live.move_shown(card_of(pic))
        assert not live.building_card(card_of(pic))
    for pic in (hud("hud_build_menu.jpg"), hud("hud_placing.jpg")):
        assert not live.move_shown(pic) and not live.move_shown(card_of(pic))


def test_the_build_menu_and_placing_are_told_apart():
    menu, placing = hud("hud_build_menu.jpg"), hud("hud_placing.jpg")
    assert live.build_menu_shown(card_of(menu))
    assert not live.build_menu_shown(card_of(placing))
    assert live.placing_shown(card_of(placing))
    assert not live.placing_shown(card_of(menu))
    assert not live.building_card(card_of(menu))        # not a building's card
    for name in ("hud_scv_idle.jpg", "hud_scv_moving.jpg", "hud_two_scvs.jpg"):
        assert not live.build_menu_shown(card_of(hud(name)))
        assert not live.placing_shown(card_of(hud(name)))


def test_scvs_and_the_dropship_are_told_by_their_pictures():
    """The army's box round the Command Center at 10 s (trial 59): eight
    selected, the SCVs third and seventh. The box round the Dropship: four,
    the Dropship second. Two SCVs alone (the owner's recording)."""
    box = hud("hud_box_scvs.jpg")
    assert live.frames_shown(box) == 8
    assert live.frames_like(box, 8, "scv") == [2, 6]
    assert live.frames_like(box, 8, "dropship") == []
    ship = hud("hud_box_dropship.jpg")
    assert live.frames_shown(ship) == 4
    assert live.frames_like(ship, 4, "dropship") == [1]
    assert live.frames_like(ship, 4, "scv") == []
    two = hud("hud_two_scvs.jpg")
    assert live.frames_shown(two) == 2 and live.frames_like(two, 2, "scv") == [0, 1]
    assert live.frames_shown(hud("hud_scv_idle.jpg")) == 0   # one unit: no frames


def test_the_view_after_a_minimap_click_is_known_to_the_tile():
    """45 different clicks on the minimap seen in the screen recordings of
    trials 51 to 59, with where the view's white box then stood (1,564
    frames): the model gives the box's place for every one."""
    import json
    import os
    pairs = json.load(open(os.path.join(os.path.dirname(__file__), "data",
                                        "minimap_clicks.json")))
    assert len(pairs) >= 40
    for px, py, col, row, left, top, frames in pairs:
        assert live.view_after_click(px, py) == (left, top), (px, py)
    # and back: the click that gives a wanted view
    for left in range(0, 228, 2):
        for top in range(0, 170, 2):
            assert live.view_after_click(*live.click_for_view(left, top)) == (left, top)
    # the Command Center at the start (trial 59: the bot clicked the
    # minimap at 115, 878 and the Command Center, tile 91, 54.5, stood at
    # screen 937, 615; the Russia bot's camera put it at 934, 448)
    view = live.view_after_click(115, 878)
    assert view == (78, 46)
    x, y = live.tile_xy(91, 54.5, view)
    assert abs(x - 937) <= 6 and abs(y - 615) <= 6


def test_a_depots_footprint_is_read_on_the_owner_s_pictures():
    """Four moments of the owner placing a depot: the footprint is found,
    green on three and red on the one that overlaps a depot, and the mouse
    is in the footprint's top-left tile each time (not in its middle)."""
    import json
    import os
    here = os.path.join(os.path.dirname(__file__), "data")
    meta = json.load(open(os.path.join(here, "depot_footprints.json")))
    colours = {}
    for name, info in meta.items():
        img = Image.new("RGB", (1920, 1080), (0, 0, 0))
        img.paste(Image.open(os.path.join(here, name)), tuple(info["at"]))
        mx, my = info["mouse"]
        fp = norway.footprint_at(img, mx + 72, my + 36, (3, 2))
        assert fp is not None, name
        assert abs((fp[2] - fp[0]) - 216) <= 2 and abs((fp[3] - fp[1]) - 144) <= 2
        assert -2 <= mx - fp[0] <= 74 and -2 <= my - fp[1] <= 74, (name, mx - fp[0], my - fp[1])
        colours[name] = "red" if fp[4] >= norway.OUTLINE_RED else "green"
    assert colours["depot_footprint_0239.jpg"] == "red"
    assert [c for n, c in colours.items() if "0239" not in n] == ["green"] * 3


class Snap:
    """What the World shows at one moment (stands in for a screenshot)."""
    def __init__(self, w):
        self.kinds = [w.units[i]["kind"] for i in w.sel]
        self.mode, self.mouse, self.view = w.mode, w.mouse, w.view
        self.building = w.building
        self.world = w
        if w.mode in ("placing", "unload", "repair"):
            self.card = "blank"
        elif w.mode == "menu":
            self.card = "menu"
        elif w.sel:
            self.card = "move"
        elif w.building:
            self.card = "building"
        else:
            self.card = None


class World:
    """A small model of the game for the SCVs, the depots and the
    Dropship: units with a kind and a tile, control groups, the selection
    (its pictures in the bottom panel can be clicked), the command card's
    modes, the view moved by clicks on the minimap exactly as the real one
    is, and buildings placed with the footprint hanging from the tile
    under the mouse. As in the real game: only one SCV alone gets a build
    menu, and an SCV that is building does not."""
    TILE = 72

    def __init__(self, units, blocked=()):
        self.t = 0.0
        self.units = [dict(kind=k, x=x, y=y, busy=0.0, inside=False)
                      for k, x, y in units]
        self.sel, self.building, self.mode = [], None, None
        self.groups, self.view, self.mouse = {}, (0, 0), (0, 0)
        self.depots, self.blocked = [], set(blocked)
        self.orders = []                # (what, unit indices, tile)
        self.loaded = 0
        self.refused = 0                # clicks to place a building on taken ground
        self.lines, self.keys, self.combos, self.clicks = [], [], [], []
        self.cc = None                  # the Command Center's tile, if it makes SCVs

    # -- time and the log
    def now(self):
        return self.t

    def sleep(self, s):
        self.t += s

    def log(self, text):
        self.lines.append(text)

    # -- eyes
    def shot(self, label, keep=True):
        return Snap(self)

    def card(self):
        return Snap(self)

    # -- helpers
    def kinds(self, key=None):
        idx = self.sel if key is None else self.groups.get(key, [])
        return sorted(self.units[i]["kind"] for i in idx)

    def _on_minimap(self, x, y):
        return 12 <= x <= 302 and 817 <= y <= 1036

    def _minimap_tile(self, x, y):
        return (2 * int((x - live.MM_X0) // live.MM_SX),
                2 * int((y - live.MM_Y0) // live.MM_SY))

    def _tile(self, x, y):
        return self.view[0] + x / self.TILE, self.view[1] + y / self.TILE

    def _frame(self, x, y):
        n = len(self.sel)
        if n < 2:
            return None
        for i in range(n):
            x0, y0, x1, y1 = live.frame_box(i, n)
            if x0 <= x <= x1 and y0 <= y <= y1:
                return i
        return None

    def _unit_at(self, x, y):
        tx, ty = self._tile(x, y)
        near = [(abs(u["x"] - tx) + abs(u["y"] - ty), u["kind"] != "dropship", i)
                for i, u in enumerate(self.units)
                if not u["inside"] and abs(u["x"] - tx) <= 0.6 and abs(u["y"] - ty) <= 0.6]
        return min(near)[2] if near else None

    def footprint(self, size):
        """(left, top, right, bottom, red pixels) of the footprint on the
        cursor, hanging from the tile under the mouse; None unless placing."""
        if self.mode != "placing":
            return None
        tx, ty = (int(v) for v in self._tile(*self.mouse))
        l, t = (tx - self.view[0]) * self.TILE, (ty - self.view[1]) * self.TILE
        return (l, t, l + size[0] * self.TILE, t + size[1] * self.TILE,
                self.TILE ** 2 * len(self._in_the_way(tx, ty, size)))

    def _in_the_way(self, tx, ty, size):
        tiles = {(tx + i, ty + j) for i in range(size[0]) for j in range(size[1])}
        taken = {(dx + i, dy + j) for dx, dy in self.depots
                 for i in range(3) for j in range(2)}
        return tiles & (self.blocked | taken)

    # -- hands
    def hover(self, x, y):
        self.mouse = (x, y)

    def drag(self, x0, y0, x1, y1):
        a, z = self._tile(x0, y0), self._tile(x1, y1)
        self.sel = [i for i, u in enumerate(self.units) if not u["inside"]
                    and a[0] <= u["x"] <= z[0] and a[1] <= u["y"] <= z[1]]
        self.building, self.mode = None, None
        self.t += 0.1

    def click(self, x, y, button="left"):
        self.clicks.append((x, y, button))
        self.mouse = (x, y)
        self.t += 0.05
        if button == "right":
            if not self.sel:
                return
            if self._on_minimap(x, y):
                self.orders.append(("move", tuple(self.sel), self._minimap_tile(x, y)))
                return
            i = self._unit_at(x, y)
            if i is not None and self.units[i]["kind"] == "dropship":
                tx, ty = self.units[i]["x"], self.units[i]["y"]
                for j in list(self.sel):    # the men beside it walk in
                    u = self.units[j]
                    if u["kind"] == "marine" and abs(u["x"] - tx) <= 6 and abs(u["y"] - ty) <= 6:
                        u["inside"] = True
                        self.loaded += 1
                return
            self.orders.append(("move", tuple(self.sel), self._tile(x, y)))
            return
        if self._on_minimap(x, y):
            assert self.mode != "placing", "a click on the minimap while placing"
            if self.mode == "unload":
                self.orders.append(("unload", tuple(self.sel), self._minimap_tile(x, y)))
                self.mode = None
            else:
                self.view = live.view_after_click(x, y)
            return
        if y > 760:                         # the bottom panel
            i = self._frame(x, y)
            if i is not None:
                self.sel, self.mode = [self.sel[i]], None
            return
        if self.mode == "placing":
            tx, ty = (int(v) for v in self._tile(x, y))
            if self._in_the_way(tx, ty, (3, 2)):
                self.refused += 1
                return                      # refused: still placing
            self.depots.append((tx, ty))
            self.orders.append(("depot", tuple(self.sel), (tx, ty)))
            self.units[self.sel[0]]["busy"] = self.t + 14.0   # walks, then builds
            self.mode = None
            return
        if self.mode == "repair":
            self.orders.append(("repair", tuple(self.sel), self._tile(x, y)))
            self.mode = None
            return
        i = self._unit_at(x, y)
        if i is not None:
            self.sel, self.building, self.mode = [i], None, None
        elif self.cc and abs(self._tile(x, y)[0] - self.cc[0]) <= 2 \
                and abs(self._tile(x, y)[1] - self.cc[1]) <= 1.5:
            self.sel, self.building, self.mode = [], "Command Center", None

    def click_with(self, held, x, y, button="left"):
        self.clicks.append((x, y, held))
        self.t += 0.1
        i = self._frame(x, y)
        if i is None:
            return
        if held == "shift":
            del self.sel[i]
        elif held == "ctrl":
            kind = self.units[self.sel[i]]["kind"]
            self.sel = [j for j in self.sel if self.units[j]["kind"] == kind]

    def key(self, name):
        self.keys.append(name)
        self.t += 0.05
        if name.isdigit():
            self.sel = [i for i in self.groups.get(name, [])]
            self.building, self.mode = None, None
        elif name == "esc":
            self.mode = {"placing": "menu"}.get(self.mode)
        elif name == "b":
            if self.mode is None and len(self.sel) == 1 and \
                    self.units[self.sel[0]]["kind"] == "scv" and \
                    self.units[self.sel[0]]["busy"] <= self.t:
                self.mode = "menu"
        elif name == "s":
            if self.mode == "menu":
                self.mode = "placing"
            elif self.building == "Command Center":
                self.units.append(dict(kind="scv", x=norway.CC_EXIT[0] + 0.6 * len(self.units) % 2,
                                       y=norway.CC_EXIT[1], busy=0.0, inside=False))
        elif name == "u":
            if self.mode is None and self.loaded and \
                    [self.units[i]["kind"] for i in self.sel] == ["dropship"]:
                self.mode = "unload"
        elif name == "r":
            if self.mode is None and len(self.sel) == 1 and \
                    self.units[self.sel[0]]["kind"] == "scv":
                self.mode = "repair"

    def combo(self, held, name):
        self.combos.append((held, name))
        self.t += 0.1
        if held == "ctrl" and name.isdigit():
            self.groups[name] = list(self.sel)
        elif held == "shift" and name.isdigit():
            self.groups[name] = self.groups.get(name, []) + \
                [i for i in self.sel if i not in self.groups.get(name, [])]


def eyes_on(monkeypatch):
    """The bot's ways of reading the screen, pointed at a World's Snap."""
    monkeypatch.setattr(live, "move_shown", lambda s: s.card == "move")
    monkeypatch.setattr(live, "build_menu_shown", lambda s: s.card == "menu")
    monkeypatch.setattr(live, "placing_shown", lambda s: s.card == "blank")
    monkeypatch.setattr(live, "building_card", lambda s: s.card == "building")
    monkeypatch.setattr(live, "frames_shown",
                        lambda s: len(s.kinds) if len(s.kinds) >= 2 else 0)
    monkeypatch.setattr(live, "frames_like",
                        lambda s, n, kind: [i for i, k in enumerate(s.kinds) if k == kind])
    monkeypatch.setattr(live, "scv_selected",
                        lambda s: s.kinds == ["scv"] and s.card == "move")
    monkeypatch.setattr(live, "attack_shown",
                        lambda s: bool(s.kinds) and "dropship" not in s.kinds)
    monkeypatch.setattr(norway, "footprint_at",
                        lambda s, sx, sy, size: s.world.footprint(size))
    monkeypatch.setattr(trial, "pick_building", lambda io, b: False)


OSLO = [("marine", 87.0, 56.3), ("marine", 87.8, 56.5), ("marine", 88.5, 56.2),
        ("marine", 98.4, 54.4), ("scv", 89.6, 56.4), ("scv", 91.7, 56.4)]


def test_scvs_and_the_dropship_are_taken_out_of_an_army_box(monkeypatch):
    """Trials 51 to 59: the army's box round the Command Center put the
    new SCVs on army key 2, and the box round the Dropship took it off
    its way to Shetland. They are taken out of the selection before the
    key is pressed; the marines stay."""
    eyes_on(monkeypatch)
    w = World(OSLO + [("dropship", 88.0, 55.0)])
    w.view = (78, 46)
    w.drag(300, 500, 1700, 800)
    assert sorted(w.kinds()) == ["dropship"] + ["marine"] * 4 + ["scv"] * 2
    assert norway.army_selected(w) == 4
    assert w.kinds() == ["marine"] * 4
    assert any("taken out of an army box" in l for l in w.lines)
    # an SCV alone in a box is not for the army at all, nor the Dropship
    w.sel = [4]
    assert norway.army_selected(w) == 0
    w.sel = [6]
    assert norway.army_selected(w) == 0
    w.sel = [0]
    assert norway.army_selected(w) == 1
    # and a box of marines costs no clicks
    w.sel, n = [0, 1, 2], len(w.clicks)
    assert norway.army_selected(w) == 3 and len(w.clicks) == n


def test_the_scvs_are_taken_below_the_command_center_onto_their_key(monkeypatch):
    """The SCVs wait below the Command Center; once the army has left they
    are boxed there, told by their pictures, proved by B on one of them
    (two together show no Build buttons), put on key 9 and sent to
    Arkhangelsk. A marine left standing there is not taken along."""
    eyes_on(monkeypatch)
    w = World([("marine", 89.0, 56.9), ("scv", 89.6, 56.4), ("scv", 91.7, 56.4),
               ("marine", 120.0, 20.0)])
    st = norway.State()
    assert norway.take_scvs(w, st) == 2 and st.scv_count == 2
    assert w.kinds("9") == ["scv", "scv"]
    assert "b" in w.keys and w.mode is None          # proved, and the menu closed
    assert norway.send_scvs(w, st) and st.scvs_sent is not None
    what, who, where = w.orders[-1]
    assert what == "move" and sorted(w.units[i]["kind"] for i in who) == ["scv", "scv"]
    assert abs(where[0] - norway.DEPOTS_AT[0]) <= 2 and abs(where[1] - norway.DEPOTS_AT[1]) <= 2
    # nothing there: nothing taken, the key untouched
    w2, st2 = World([("marine", 89.0, 56.9)]), norway.State()
    assert norway.take_scvs(w2, st2) == 0 and "9" not in w2.groups


def test_scvs_on_an_army_key_are_moved_to_their_own_never_dropped(monkeypatch):
    """Trial 59: found on army key 2, the SCVs were taken out of it without
    having got onto key 9, and were on no key after. Now they go onto
    their key first; if that cannot be proved they stay where they are."""
    eyes_on(monkeypatch)
    w = World(OSLO)
    w.groups = {"1": [0, 1], "2": [2, 4, 3, 5]}
    st = norway.State()
    st.army_keys = ["1", "2"]
    assert norway.scvs_from_army(w, st) == 2
    assert w.kinds("9") == ["scv", "scv"]
    assert w.kinds("2") == ["marine", "marine"] and w.kinds("1") == ["marine"] * 2
    # the proof fails: nothing is taken out of the army key
    w = World(OSLO)
    w.groups = {"2": [2, 4, 3, 5]}
    st = norway.State()
    st.army_keys = ["2"]
    monkeypatch.setattr(norway, "proved_scv", lambda io: False)
    assert norway.scvs_from_army(w, st) == 0 and st.scv_count == 0
    assert w.kinds("2") == ["marine", "marine", "scv", "scv"]


def depot_world():
    w = World([("scv", 196.0, 20.0), ("scv", 196.5, 20.5)],
              blocked={(x, y) for x in (198, 199, 200) for y in (19, 20)} |   # Russia's depot
                      {(201, 14), (202, 15)})                                # something in the way
    w.groups["9"] = [0, 1]
    st = norway.State()
    st.scv_count, st.scvs_sent = 2, 0.0
    return w, st


def test_ten_depots_by_arkhangelsk_one_scv_an_order(monkeypatch):
    """The owner's way: one SCV selected (with two there is no build
    menu), B, S, and a click where the footprint shows green. Ten depots,
    each on its own free ground, the two SCVs by turns, and an SCV is left
    alone until its depot is up."""
    eyes_on(monkeypatch)
    w, st = depot_world()
    results = []
    while st.depots_placed < norway.DEPOTS and w.t < 400:
        results.append(norway.build_depot(w, st))
        w.sleep(norway.DEPOT_EVERY)
    assert st.depots_placed == 10 and len(w.depots) == 10
    assert len(set(w.depots)) == 10
    for dx, dy in w.depots:                 # none on taken ground
        assert not {(dx + i, dy + j) for i in range(3) for j in range(2)} & w.blocked
    spots = [tile for view, tile in norway.depot_spots()]
    assert set(w.depots) <= set(spots) and (201, 14) not in w.depots
    assert w.refused == 0                   # red was read, never clicked on
    orders = [o for o in w.orders if o[0] == "depot"]
    assert all(len(who) == 1 for what, who, where in orders)     # one SCV an order
    assert {who[0] for what, who, where in orders} == {0, 1}     # by turns
    assert "wait" in results                                     # both were busy at times
    # an order to an SCV only once its last depot is up (about 12.5 s)
    times = {0: [], 1: []}
    t = 0.0
    w2, st2 = depot_world()
    while st2.depots_placed < 4:
        before = len(w2.orders)
        norway.build_depot(w2, st2)
        if len(w2.orders) > before:
            times[w2.orders[-1][1][0]].append(w2.t)
        w2.sleep(norway.DEPOT_EVERY)
    for i in times:
        assert all(b - a >= 12.5 for a, b in zip(times[i], times[i][1:]))


def test_a_depot_is_never_clicked_onto_red_or_unseen_ground(monkeypatch):
    eyes_on(monkeypatch)
    w, st = depot_world()
    w.blocked |= {(x, y) for x in range(190, 215) for y in range(8, 30)}   # all of it
    n = len(w.clicks)
    assert norway.build_depot(w, st) == "failed"
    assert not w.depots and st.depots_placed == 0
    assert w.refused == 0                                    # no click on red
    assert w.mode is None                                    # and out of placing
    # no SCV on the key: said so, nothing pressed for a depot
    w, st = depot_world()
    w.groups["9"] = []
    assert norway.build_depot(w, st) == "no-scv" and "b" not in w.keys


def test_one_scv_repairs_the_barracks_where_it_landed(monkeypatch):
    eyes_on(monkeypatch)
    w, st = depot_world()
    st.at["Barracks"] = (147.0, 37.5)
    assert norway.repair_barracks(w, st)
    what, who, where = w.orders[-1]
    assert what == "repair" and len(who) == 1
    assert abs(where[0] - 147.0) <= 0.6 and abs(where[1] - 37.5) <= 0.6
    assert max(st.scv_busy) > w.t                 # it is left alone for a while
    assert norway.free_scv(st, w.t) is not None   # the other builds on


def test_the_dropship_takes_the_men_beside_it_to_shetland(monkeypatch):
    """Trials 51 to 59: the clicks meant for the Dropship fell two tiles
    above it, so nobody boarded, U did nothing, the click on the minimap
    only moved the view, and the army's box then took the Dropship to
    Finland. With the exact view the men board, the Dropship alone is
    selected, U asks for a target and Shetland is given on the minimap."""
    eyes_on(monkeypatch)
    m = trial.load_map()
    d = next(a for a in m["slots"]["4"]["air"] if a["type"] == "Dropship")
    tx, ty = d["x"] / 32, d["y"] / 32
    w = World([("dropship", tx, ty), ("marine", tx - 1.1, ty - 0.6),
               ("marine", tx - 1.1, ty + 0.3), ("marine", tx + 9.0, ty + 1.0)])
    assert norway.drop_on_shetland(w, m)
    assert w.loaded == 2 and not w.units[3]["inside"]
    what, who, where = w.orders[-1]
    assert what == "unload" and [w.units[i]["kind"] for i in who] == ["dropship"]
    sx, sy = norway.SHETLAND[0] / 32, norway.SHETLAND[1] / 32
    assert abs(where[0] - sx) <= 2 and abs(where[1] - sy) <= 2
    # nobody near to board: no order, and it says so
    w = World([("dropship", tx, ty)])
    assert not norway.drop_on_shetland(w, m)
    assert not w.orders and any("was not sent to Shetland" in l for l in w.lines)


def test_two_scvs_are_ordered_with_no_rally_and_made_again_if_lost(monkeypatch):
    eyes_on(monkeypatch)
    m = trial.load_map()
    cc = norway.norway_buildings(m)["Command Center"]
    w = World([])
    w.cc = (cc["x"] / 32, cc["y"] / 32)
    st = norway.State()
    assert norway.make_scvs(w, m, st)
    assert w.keys[-2:] == ["s", "s"] and "r" not in w.keys       # no rally
    assert sum(u["kind"] == "scv" for u in w.units) == 2
    assert st.scvs_made is not None
    # they stand below the Command Center: found there
    w.sleep(8)
    assert norway.get_scvs(w, m, st) == 2 and w.kinds("9") == ["scv", "scv"]
    assert any("walk to Arkhangelsk" in l for l in w.lines)
    # lost (none there, none on an army key): the second try makes two more
    w = World([])
    w.cc = (cc["x"] / 32, cc["y"] / 32)
    st = norway.State()
    st.scvs_made = 0.0
    assert norway.get_scvs(w, m, st) == 0 and not st.scvs_remade
    assert norway.get_scvs(w, m, st) == 0 and st.scvs_remade
    w.sleep(8)
    assert norway.get_scvs(w, m, st) == 2


def test_a_footprint_hangs_from_the_tile_under_the_mouse(monkeypatch):
    """Landing the Barracks or the Command Center: the mouse starts on the
    footprint's top-left tile, and the colour is read where the click goes
    (before, the mouse was moved once more after the last look)."""
    tile = 72

    class Land:
        def __init__(self, red_tiles=()):
            self.at, self.lines, self.hovers = (0, 0), [], []
            self.red = set(red_tiles)

        def hover(self, x, y):
            self.at = (x, y)
            self.hovers.append((x, y))

        def sleep(self, s):
            pass

        def log(self, text):
            self.lines.append(text)

        def shot(self, label, keep=True):
            img = Image.new("RGB", (1920, 1080), (29, 34, 16))
            gx, gy = self.at[0] // tile, self.at[1] // tile
            for i in range(4):
                for j in range(3):
                    c = TINT["red" if (gx + i, gy + j) in self.red else "green"]
                    img.paste(c, ((gx + i) * tile, (gy + j) * tile,
                                  (gx + i + 1) * tile, (gy + j + 1) * tile))
            return img
    io = Land()
    cx, cy = 10 * tile + 144, 5 * tile + 108       # a footprint on tiles 10..13, 5..7
    mouse = norway.green_spot(io, cx, cy, "land-barracks")
    assert mouse is not None and mouse[0] // tile == 10 and mouse[1] // tile == 5
    assert len(io.hovers) == 1                     # right the first time
    # red there: the spot is moved a tile at a time until green, and the
    # click goes where green was read
    io = Land(red_tiles={(13, 5), (13, 6), (13, 7)})
    mouse = norway.green_spot(io, cx, cy, "land-barracks")
    assert mouse is not None and mouse == io.hovers[-1]
    gx, gy = mouse[0] // tile, mouse[1] // tile
    assert not {(gx + i, gy + j) for i in range(4) for j in range(3)} & io.red
    # red all round, or no footprint to be seen: never a click
    io = Land(red_tiles={(x, y) for x in range(0, 27) for y in range(0, 15)})
    assert norway.green_spot(io, cx, cy, "land-barracks") is None

    class Blind(Land):
        def shot(self, label, keep=True):
            return Image.new("RGB", (1920, 1080), (29, 34, 16))
    assert norway.green_spot(Blind(), cx, cy, "land-barracks") is None


def test_a_lost_scv_found_by_the_sweep_is_proved_by_b(monkeypatch):
    """Trial 59: the sweep clicked right on an SCV ten times and the check
    said no each time. Now the game itself is asked: B, and a build menu."""
    eyes_on(monkeypatch)
    w = World([("marine", 133.0, 10.0), ("scv", 136.0, 11.0)])
    w.view = (120, 5)
    st = norway.State()
    spots = [tuple(int(v) for v in live.tile_xy(133.0, 10.0, w.view)),
             tuple(int(v) for v in live.tile_xy(136.0, 11.0, w.view))]
    monkeypatch.setattr(norway, "scv_spots", lambda pic: spots)
    assert norway.probe_scvs(w, st) == 1
    assert w.kinds("9") == ["scv"] and st.scv_count == 1


def test_a_dropship_alone_is_told_by_its_missing_attack_button():
    """One unit alone shows no small pictures: an SCV is told by its Build
    button, the Dropship by having no Attack button (marines and SCVs do)."""
    assert not live.attack_shown(hud("hud_dropship.jpg"))
    assert live.move_shown(hud("hud_dropship.jpg"))
    for name in ("hud_marine.jpg", "hud_scv_idle.jpg", "hud_scv_moving.jpg",
                 "hud_box_scvs.jpg", "hud_two_scvs.jpg"):
        assert live.attack_shown(hud(name)), name
    assert not live.attack_shown(card_of(hud("hud_marine.jpg")))   # needs the whole screen


def test_one_scv_first_the_other_added_to_the_key_later(monkeypatch):
    """If only one SCV stands below the Command Center at the first look
    (the other comes out later), it goes on the key and off to
    Arkhangelsk; the other is added to the key at the next look."""
    eyes_on(monkeypatch)
    m = trial.load_map()
    w = World([("scv", 91.7, 56.4)])
    st = norway.State()
    st.scvs_made = 0.0
    assert norway.get_scvs(w, m, st) == 1 and w.kinds("9") == ["scv"]
    w.units[0]["x"], w.units[0]["y"] = 120.0, 30.0       # it walked off
    w.units.append(dict(kind="scv", x=89.6, y=56.4, busy=0.0, inside=False))
    assert norway.get_scvs(w, m, st) == 2 and w.kinds("9") == ["scv", "scv"]
    assert ("shift", "9") in w.combos
    moves = [o for o in w.orders if o[0] == "move"]
    assert len(moves[-1][1]) == 2                        # both sent on
    # with one on the key and nothing more to find: no new SCVs are made
    w = World([("scv", 91.7, 56.4)])
    st = norway.State()
    st.scvs_made = 0.0
    assert norway.get_scvs(w, m, st) == 1
    w.units[0]["x"] = 120.0
    assert norway.get_scvs(w, m, st) == 1 and not st.scvs_remade


def test_the_attack_on_the_finland_spot_goes_out_when_it_is_due(monkeypatch):
    """The opening before it got about two seconds shorter (one exact
    click for a building, the Shetland drop). With a look at Finland only
    every three seconds, the attack on the Finland spot could then go out
    up to three seconds late; it goes out the moment it is due."""
    game, m, watch, st = setup(monkeypatch)
    times = {}
    real_log = game.log

    def log(text):
        real_log(text)
        for word, name in (("moves to Kiruna", "kiruna"),
                           ("Barracks lifted", "lifted"),
                           ("attacks at Russian army-Finland", "spot")):
            if word in text and name not in times:
                times[name] = game.t
    game.log = log
    # the lifts end a moment before the attack is due
    real_sleep = game.sleep
    norway.opening(game, watch, m, st, "first")
    due = max(times["lifted"], st_due(times))
    assert times["spot"] - due <= 1.0


def st_due(times):
    # the gather order is logged just after it is given
    return times["kiruna"] + norway.ARMY_STAGES[1][2]


class Still:
    """A game that shows one real picture whatever is done: for where the
    bot clicks when it reads that picture."""
    def __init__(self, picture):
        self.picture, self.clicks, self.lines, self.t = picture, [], [], 0.0

    def shot(self, label, keep=True):
        return self.picture

    def card(self):
        return self.picture.crop(live.CARD_CELL)

    def hover(self, x, y):
        pass

    def sleep(self, s):
        self.t += s

    def log(self, text):
        self.lines.append(text)

    def click(self, x, y, button="left"):
        self.clicks.append((x, y, button))

    def click_with(self, held, x, y, button="left"):
        self.clicks.append((x, y, held))


def test_on_the_real_box_round_the_command_center_the_scvs_pictures_are_clicked():
    """The army's box round the Command Center in trial 59 (the real
    picture): eight selected, the SCVs third and seventh. Their pictures
    are Shift+clicked, the seventh first and then the third where it then
    stands among seven; six marines are left for the key."""
    io = Still(hud("hud_box_scvs.jpg"))
    assert norway.army_selected(io) == 6
    seventh = live.frame_box(6, 8)
    third = live.frame_box(2, 7)
    mid = lambda b: ((b[0] + b[2]) // 2, (b[1] + b[3]) // 2)
    assert io.clicks == [(*mid(seventh), "shift"), (*mid(third), "shift")]
    # the Dropship in the box that was dragged round it
    io = Still(hud("hud_box_dropship.jpg"))
    assert norway.army_selected(io) == 3
    assert io.clicks == [(*mid(live.frame_box(1, 4)), "shift")]
    # one marine, an SCV, the Dropship, each alone
    assert norway.army_selected(Still(hud("hud_marine.jpg"))) == 1
    assert norway.army_selected(Still(hud("hud_scv_idle.jpg"))) == 0
    assert norway.army_selected(Still(hud("hud_dropship.jpg"))) == 0
    # two SCVs alone, read off the real picture: both are SCVs
    assert norway.scvs_selected(Still(hud("hud_two_scvs.jpg"))) == 2
    assert norway.scvs_selected(Still(hud("hud_scv_moving.jpg"))) == 1
    assert norway.scvs_selected(Still(hud("hud_marine.jpg"))) == 0
