import os

import numpy as np
from PIL import Image

from bot import trial
from eyes import live

DATA = os.path.join(os.path.dirname(__file__), "data")
CARDS = {k: Image.open(os.path.join(DATA, f)) for k, f in
         [("barracks", "card_barracks.png"), ("units", "card_units.png")]}
GREEN = (41, 235, 51)
SPEED = 95.0          # map pixels a marine walks per second


def screen(card):
    """A 1920 x 1080 screen with a real minimap and command card pasted in."""
    s = Image.new("RGB", (1920, 1080))
    s.paste(Image.open(os.path.join(DATA, "live_minimap.png")), (0, 780))
    if card:
        s.paste(CARDS[card], (1560, 760))
    return s


class FakeGame:
    """Pretends to be the game.

    It draws a minimap with our buildings and units in green, the way
    the real one does. Things appear on screen `error` pixels away from
    where the bot's arithmetic says. A click near a barracks selects
    it; a box selects up to 12 units inside it; ordered units walk to
    where they were sent at a marine's pace and form up around it.
    Every input and every look at the screen costs time.
    """

    def __init__(self, mapdata, error=(40, 80), showing=True):
        side = mapdata["slots"][trial.SLOT]
        self.barracks = trial.barracks_of(mapdata)
        self.structures = side["structures"]
        # each unit: where it was, where it is going, when it set off
        self.units = [{"from": tuple(u), "to": tuple(u), "t": 0.0}
                      for u in side["units"]]
        self.error, self.showing = error, showing
        self.camera, self.selected, self.attack = None, None, False
        self.m_on_barracks = self.m_elsewhere = self.rallies = 0
        self.time, self.inputs, self.arrivals = 0.0, 0, {}
        self.groups, self.key_orders = {}, 0
        self.lifted, self.flights = False, []
        self.starports = [b for b in side["buildings"] if b["type"] == "Starport"]
        self.money, self.spawned_at, self.last_key = 1000, None, None

    def alive(self):
        """Units that exist now. Also runs the map's Middle East event:
        the first unit to arrive there brings 32 marines and 4,000."""
        now = [u for u in self.units if u.get("born", 0) <= self.time]
        if self.spawned_at is None and any(
                near(self.where(u), trial.MIDDLE_EAST, 7) for u in now):
            self.spawned_at = self.time
            self.money += 4000
            x, y = trial.MIDDLE_EAST
            for k in range(32):
                p = (x + (k % 8 - 4) * 26, y + (k // 8 - 2) * 26)
                self.units.append({"from": p, "to": p, "t": self.time,
                                   "spawn": True})
            now = [u for u in self.units if u.get("born", 0) <= self.time]
        return now

    def send(self, units, mx, my):
        key = (round(mx), round(my))
        for u in units:                  # they form up around the point
            k = self.arrivals[key] = self.arrivals.get(key, 0) + 1
            u["from"], u["t"] = self.where(u), self.time
            u["to"] = (mx + (k % 14 - 7) * 26, my + (k // 14 - 6) * 26)

    def where(self, u):
        (x0, y0), (x1, y1) = u["from"], u["to"]
        d = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
        f = 1.0 if d == 0 else min(1.0, (self.time - u["t"]) * SPEED / d)
        return x0 + (x1 - x0) * f, y0 + (y1 - y0) * f

    def _screen(self, x, y):
        px, py = live.on_screen(x, y, self.camera)
        return px + self.error[0], py + self.error[1]

    def click(self, x, y, button="left"):
        self.inputs += 1
        self.time += 0.07
        m = live.MINIMAP
        on_map = m["left"] <= x < m["left"] + m["width"] and y >= m["top"]
        mx = (x - m["left"] + 0.5) / m["width"] * live.MAP_PX[0]
        my = (y - m["top"] + 0.5) / m["height"] * live.MAP_PX[1]
        if button == "right":
            if self.selected in ("barracks", "starport") and on_map and self.lifted:
                self.flights.append((self.selected, mx, my))
            elif self.selected == "barracks" and on_map:
                self.rallies += 1
            elif isinstance(self.selected, list) and on_map:
                self.send(self.selected, mx, my)         # a plain move
            return
        if on_map:
            if self.attack and isinstance(self.selected, list):
                self.send(self.selected, mx, my)
                if self.last_key and self.last_key.isdigit():
                    self.key_orders += 1
            else:
                self.camera = live.camera_after_click(x, y)
            self.attack = False
            return
        self.selected, self.lifted = None, False
        for b in self.barracks:
            px, py = self._screen(b["x"], b["y"])
            if abs(x - px) < 130 and abs(y - py) < 95:
                self.selected = "barracks"
        for b in self.starports:
            px, py = self._screen(b["x"], b["y"])
            if abs(x - px) < 130 and abs(y - py) < 95:
                self.selected = "starport"

    def drag(self, x0, y0, x1, y1):
        self.inputs += 1
        self.time += 0.33
        assert 0 <= x0 < x1 <= 1920 and 40 <= y0 < y1 <= 760
        inside = [u for u in self.alive()
                  if x0 <= self._screen(*self.where(u))[0] <= x1
                  and y0 <= self._screen(*self.where(u))[1] <= y1]
        self.selected = inside[:12] or None

    def key(self, name):
        self.inputs += 1
        self.time += 0.05
        if name == "m":
            if self.selected == "barracks":
                self.m_on_barracks += 1
                if self.money >= 50:             # a marine, out in 15 s
                    self.money -= 50
                    k = self.arrivals["new"] = self.arrivals.get("new", 0) + 1
                    p = (trial.MASS[0] + (k % 12 - 6) * 26,
                         trial.MASS[1] + (k // 12 % 10 - 5) * 26)
                    self.units.append({"from": p, "to": p, "t": 0,
                                       "born": self.time + 15 + 25})
            else:
                self.m_elsewhere += 1
        if name == "l":
            assert self.selected in ("barracks", "starport")   # only buildings
            self.lifted = True
        if name == "a":
            assert isinstance(self.selected, list)   # never A on nothing
            self.attack = True
        if name.isdigit() and name in self.groups:
            self.selected = [u for u in self.groups[name]]
        if name != "a":
            self.last_key = name

    def combo(self, held, name):
        self.inputs += 1
        self.time += 0.15
        assert held == "ctrl" and isinstance(self.selected, list)
        self.groups[name] = list(self.selected)

    def sleep(self, s):
        self.time += s

    def card(self):
        self.time += 0.01
        if self.selected == "starport":              # some other button
            return Image.new("RGB", (92, 90), (200, 190, 40))
        card = "barracks" if self.selected == "barracks" else \
            "units" if self.selected else None
        if not self.showing or not card:
            return Image.open(live.data_path("blank_card.png"))
        return live.card_cell(screen(card))

    def now(self):
        return self.time

    def shot(self, label, keep=True):
        self.time += 0.06
        if not self.showing:
            return Image.new("RGB", (1920, 1080))
        a = np.zeros((1080, 1920, 3), dtype=np.uint8)
        m, d = live.MINIMAP, live.DRAWN
        a[m["top"] - 1, m["left"]:m["left"] + m["width"]] = (193, 212, 197)

        def block(x, y, w, h):
            c, r = live.to_drawn(x, y)
            a[d["top"] + r - h // 2:d["top"] + r + h - h // 2,
              d["left"] + c - w // 2:d["left"] + c + w - w // 2] = GREEN
        for x, y in self.structures:
            block(x, y, 5, 4)
        for u in self.alive():
            block(*self.where(u), 3, 3)
        s = Image.fromarray(a)
        card = "barracks" if self.selected == "barracks" else \
            "units" if self.selected else None
        if card:
            s.paste(CARDS[card], (1560, 760))
        return s

    def log(self, text, quiet=False):
        pass


def near(p, point, tiles):
    return abs(p[0] - point[0]) < tiles * 32 and abs(p[1] - point[1]) < tiles * 32


def test_reads_the_real_pictures():
    assert live.minimap_showing(screen("units"))
    assert not live.minimap_showing(Image.new("RGB", (1920, 1080)))
    assert live.barracks_selected(screen("barracks"))
    assert not live.barracks_selected(screen("units"))
    assert live.units_selected(screen("units"))
    assert not live.units_selected(screen("barracks"))
    assert not live.units_selected(screen(None))
    blank = Image.open(live.data_path("blank_card.png"))
    assert not live.building_selected(blank)
    assert not live.building_selected(screen("units"))
    assert live.building_selected(screen("barracks"))
    assert trial.round_timer(0) == "5:00" and trial.round_timer(180) == "2:00"
    assert trial.round_timer(310) == "4:50"


def test_map_data():
    m = trial.load_map()
    assert len(trial.barracks_of(m)) == 8
    assert len(m["slots"]["5"]["units"]) == 175
    w = trial.place(m, trial.TARGETS[0])
    assert (w["x"] // 32, w["y"] // 32) == (100, 89)        # Berlin
    x, y = live.minimap_point(w["x"], w["y"])
    assert 13 < x < 302 and 817 < y < 1033


def test_camera_stays_on_the_map():
    cam = live.camera_after_click(*live.minimap_point(6650, 100))
    assert cam[1] == 1080 / live.ZOOM / 2          # held at the top edge
    assert live.on_screen(6650, 100, cam)[1] < live.CENTRE[1]


def test_watch_sees_units_and_not_buildings():
    m = trial.load_map()
    g = FakeGame(m)
    side = m["slots"]["5"]
    watch = live.Watch(g.shot("start"), side["structures"], side["units"])
    assert watch.ok
    assert len(trial.at_mass(watch.units(g.shot("x")))) < 60
    for u in g.units[:100]:                         # walk 100 units over
        u["to"] = (trial.MASS[0] + g.units.index(u) % 10 * 26,
                   trial.MASS[1] + g.units.index(u) // 10 * 26)
    g.time = 100
    assert len(trial.at_mass(watch.units(g.shot("x")))) > 60
    g.units = []                                    # nobody left at all
    ghosts = watch.units(g.shot("x"))               # buildings showing through
    assert len(ghosts) < 400                        # where units once stood
    watch.forget(ghosts)                            # a box there came up empty
    assert len(watch.units(g.shot("x"))) == 0


def test_opening_masses_fast_and_hits_berlin():
    m = trial.load_map()
    w = trial.place(m, trial.TARGETS[0])
    for error in [(0, 0), (40, 80), (-60, 10), (70, -60)]:
        g = FakeGame(m, error=error)
        seen = {}
        real_hit = trial.hit

        def hit(io, *a, **k):                       # note the mass as it leaves
            if not seen:
                seen["n"] = sum(near(io.where(u), trial.MASS, 14)
                                for u in io.alive())
                seen["t"] = io.time
            out = real_hit(io, *a, **k)
            if not hasattr(io, "time_first_hit_done"):
                io.time_first_hit_done = io.time
            return out
        trial.hit = hit
        try:
            result = trial.run(g, m)
        finally:
            trial.hit = real_hit
        assert result["trained"] >= 7, error
        assert g.m_elsewhere == 0                   # never M on something else
        # the scout reached the Middle East early, and the event fired
        assert g.spawned_at is not None and g.spawned_at < 40, error
        # eight ground groups on number keys, and they were used to hit
        assert len(g.groups) >= 8 and g.key_orders >= 8, (error, result)
        # most of the starting army is massed when the first hit goes
        assert seen["t"] <= 100, (error, seen)
        assert result["hits"][0] and g.time_first_hit_done <= 110, \
            (error, g.time_first_hit_done)
        assert seen["n"] >= 0.7 * 175, (error, seen)
        # in the end most of everything, Middle East marines included,
        # has been sent at a target, spread along its front
        alive = g.alive()
        spots = [trial.place(m, n) for n in set(trial.TARGETS)]
        sent = [u for u in alive
                if any(near(u["to"], (p["x"], p["y"]), 20) for p in spots)]
        assert len(sent) >= 0.7 * len(alive), (error, len(sent), len(alive))
        assert sum(1 for u in sent if u.get("spawn")) >= 20, error
        at_berlin = [u for u in sent if near(u["to"], (w["x"], w["y"]), 20)]
        assert len(at_berlin) >= 150                # the first hit: Berlin
        assert len({round(u["to"][1] / 64) for u in at_berlin}) >= 6   # a wall
        # the Smolensk barracks was flown to Warsaw after the first hit
        warsaw = trial.place(m, "Warsaw 200")
        kinds = {k: (x, y) for k, x, y in g.flights}
        assert near(kinds["barracks"], (warsaw["x"], warsaw["y"]), 3), error
        # with no Axis to be seen, every hit went to Berlin
        assert set(result["targets"]) == {"Berlin 1000"}
        # later hits found the newly trained marines
        assert sum(1 for h in result["hits"][1:] if h) >= 1, (error, result)
        # few boxes come up empty
        assert result["empty"] <= 0.3 * result["boxes"], (error, result)


def test_opening_does_nothing_without_the_game_screen():
    m = trial.load_map()
    g = FakeGame(m, showing=False)
    assert trial.run(g, m) == {"trained": 0, "gathered": 0, "hits": []}
    assert g.inputs == 0


def test_wave_goes_back_to_front():
    berlin = trial.place(trial.load_map(), "Berlin 1000")
    groups = [(150, 70), (170, 70), (160, 72)]      # minimap pixels
    ordered = trial.back_to_front(groups, (berlin["x"], berlin["y"]),
                                  lambda p: live.from_drawn(*p))
    assert [p[0] for p in ordered] == [170, 160, 150]   # east goes first


class OneShot:
    """Just enough of the game for choosing a target: one picture."""
    def __init__(self, picture):
        self.picture, self.lines = picture, []

    def shot(self, label, keep=True):
        return self.picture

    def log(self, text, quiet=False):
        self.lines.append(text)


def real_game_screen():
    """A screen with the minimap of a real seven-player game pasted in:
    Russia green, everyone else in their own colour, Germany in Hungary
    and Romania."""
    s = Image.new("RGB", (1920, 1080))
    s.paste(Image.open(os.path.join(DATA, "real_minimap.png")), (0, 780))
    return s


def test_sees_other_players_on_a_real_minimap():
    m = trial.load_map()
    side = m["slots"]["5"]
    s = real_game_screen()
    watch = live.Watch(s, side["structures"], side["units"])
    assert watch.ok

    def centre(slot):
        px = watch.others(s, [slot])
        xs = [live.from_drawn(c, r)[0] / 32 for c, r in px]
        ys = [live.from_drawn(c, r)[1] / 32 for c, r in px]
        return sum(xs) / len(xs), sum(ys) / len(ys)
    assert centre(7)[0] < 50 and centre(7)[1] > 140      # Spain: south-west
    assert centre(4)[1] < 50                             # Norway: north
    assert 95 < centre(0)[0] < 130                       # Germany: middle
    assert centre(1)[1] > centre(0)[1] + 30              # Italy: south of it
    assert len(trial.at_mass(watch.others(s, trial.AXIS))) == 0


def test_target_follows_the_axis_in_the_balkans():
    m = trial.load_map()
    side = m["slots"]["5"]
    s = real_game_screen()
    watch = live.Watch(s, side["structures"], side["units"])
    seen = trial.axis_in(watch, s, trial.BALKANS)
    assert seen > 100                                    # Germany is there
    st = trial.State()
    st.balkan_start = seen - 80                          # 80 more than at the start
    assert trial.choose_target(OneShot(s), watch, st) == "Romania 300"
    st.sent_at.append("Romania 300")
    assert trial.choose_target(OneShot(s), watch, st) == "Factory 7"
    st.balkan_start = seen                               # no more than at the start
    assert trial.choose_target(OneShot(s), watch, st) == "Berlin 1000"
    g = FakeGame(m)                                      # nobody else in sight
    quiet = g.shot("x")
    watch2 = live.Watch(quiet, side["structures"], side["units"])
    assert trial.choose_target(OneShot(quiet), watch2, trial.State()) \
        == "Berlin 1000"


def test_romania_flight_follows_the_first_romania_hit():
    m = trial.load_map()
    g = FakeGame(m)
    g.camera = (0, 0)
    st = trial.State()
    trial.flights_after(g, m, st, "Romania 300")
    romania = trial.place(m, "Romania 300")
    assert g.flights and g.flights[0][0] == "starport"
    assert near(g.flights[0][1:], (romania["x"], romania["y"]), 3)
    trial.flights_after(g, m, st, "Romania 300")         # only once
    assert len(g.flights) == 1


def supply_screen(name):
    s = Image.new("RGB", (1920, 1080))
    s.paste(Image.open(os.path.join(DATA, name)), (1780, 0))
    return s


def test_reads_the_supply_number():
    from eyes import numbers
    assert numbers.read_supply(supply_screen("supply_153.png")) == (153, 200)
    assert numbers.read_supply(supply_screen("supply_200.png")) == (200, 200)
    assert numbers.read_supply(supply_screen("supply_212.png")) == (212, 200)
    assert numbers.read_supply(Image.new("RGB", (1920, 1080))) is None


def test_does_not_train_at_the_supply_limit():
    m = trial.load_map()
    for name, expect_training in [("supply_200.png", False),
                                  ("supply_212.png", False),
                                  ("supply_153.png", True)]:
        g = FakeGame(m)
        real_shot = g.shot

        def shot(label, keep=True, _name=name, _real=real_shot):
            s = _real(label, keep)
            s.paste(Image.open(os.path.join(DATA, _name)), (1780, 0))
            return s
        g.shot = shot
        st = trial.State()
        found = trial.train_everywhere(g, m, st)
        assert (g.m_on_barracks > 0) == expect_training, name
        assert st.capped == (not expect_training)
        assert (found > 0) == expect_training


def test_battle_verdict():
    b = trial.Battle("Berlin 1000", 0)
    assert b.verdict()[0] == "unclear"
    # samples: (seconds, our forward pixels, Axis at the front, tiles short)
    b.samples = [(5, 200, 0, 50), (30, 180, 10, 25), (60, 40, 12, 24)]
    assert b.verdict()[0] == "losing"         # most of the hit is gone
    b.samples = [(5, 200, 0, 50), (30, 190, 10, 25), (60, 180, 12, 24)]
    assert b.verdict()[0] == "stalled"        # alive, but not getting closer
    b.samples = [(5, 200, 0, 50), (30, 190, 10, 30), (60, 180, 2, 12)]
    assert b.verdict()[0] == "advancing"
    b.arrived = True
    assert b.verdict()[0] == "arrived"


def test_finds_the_front_on_a_real_minimap():
    """In this picture the army has stalled around Warsaw and
    Konigsberg, a long way short of Berlin."""
    m = trial.load_map()
    side = m["slots"]["5"]
    s = Image.new("RGB", (1920, 1080))
    s.paste(Image.open(os.path.join(DATA, "stalled_minimap.png")), (0, 780))
    watch = live.Watch(real_start_screen(), side["structures"], side["units"])
    x, y, ours, axis = trial.find_front(watch, s, m, "Berlin 1000")
    assert 115 < x / 32 < 140 and 65 < y / 32 < 95      # the eastern front
    assert ours > 100
    berlin = trial.place(m, "Berlin 1000")
    assert abs(x - berlin["x"]) / 32 > 15               # not Berlin
    b = trial.Battle("Berlin 1000", 0)
    b.front = (x, y)
    b.samples = [(5, ours, 0, 24), (30, ours, 8, 24), (60, ours, 8, 24)]
    st = trial.State()
    g = OneShot(s)
    g.now = lambda: 100
    target = trial.choose_target(g, watch, st, m, b)
    assert target in trial.EAST_FRONT                   # break the line there


def real_start_screen():
    s = Image.new("RGB", (1920, 1080))
    s.paste(Image.open(os.path.join(DATA, "start_minimap.png")), (0, 780))
    return s
