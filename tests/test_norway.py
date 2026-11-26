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
        if held == "ctrl" and name in norway.KEYS.values() and self.selected:
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


def test_the_barracks_lands_by_3_25_even_if_finland_is_not_cleared(monkeypatch):
    game, m, watch, st = setup(monkeypatch, red_looks=10 ** 6)
    monkeypatch.setattr(norway, "OPENING_TIME", 120)
    norway.opening(game, watch, m, st, "first")
    assert not st.finland_clear
    assert "Barracks" in st.landed
    landed = next(l for l in game.lines if "Barracks down" in l)
    left = int(landed.split("countdown ")[1].split(";")[0].replace(":", ""))
    assert 325 <= left <= 350           # 3:25 to 3:50 on the countdown
    assert "Starport" not in st.landed  # Russia's is attacked only after Finland


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
