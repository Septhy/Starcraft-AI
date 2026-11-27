"""Norway v0.01: the opening (bot/norway.py)."""
from bot import norway, trial
from eyes import live
from tests.test_trial import blob


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
    game, m, watch, st = setup(monkeypatch, port_blocks=False)
    norway.opening(game, watch, m, st, "first")
    assert "Starport" in st.landed
    assert not any("attack Russia's Starport" in l for l in game.lines)


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
    assert [s.replace("attacks at ", "@").replace("moves to ", "@").split("@")[1]
            .split(" (")[0] for s in names] == \
        ["Kiruna 200", "Russian army-Finland", "Helsinki 400", "Helsinki 400"]
    assert "moves to" in names[0] and "moves to" in names[2]
    assert "attacks" in names[3]
    landed = next(l for l in game.lines if "Barracks landed by" in l)
    assert landed.endswith("138, 30") or "138, 29" in landed


def test_the_barracks_spots_are_next_to_the_heavy_industry():
    m = trial.load_map()
    hx, hy = norway.heavy_industry(m)
    for x, y in norway.barracks_spots(m):
        assert abs(x - hx) <= 6 * 32 and abs(y - hy) <= 5 * 32
    port = norway.russia_starport(m)
    assert (port["x"] // 32, port["y"] // 32) == (156, 5)


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
    sizes = iter([5, 6, 4, 7, 3, 2] + [1] * 50)
    monkeypatch.setattr(norway, "selected", lambda io: next(sizes))
    norway.key_army(game, W(), m, st, "first")
    assert len(st.army_keys) >= 2
    assert all(n <= 12 for n in st.army_held.values())
    assert st.army_held["1"] >= 11            # filled before the next key
    for k in st.army_keys:                    # made once, then added to
        assert game.combos.count(("ctrl", k)) == 1
    assert ("shift", "1") in game.combos
