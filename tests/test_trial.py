import os

import numpy as np
from PIL import Image

from bot import trial
from eyes import live

DATA = os.path.join(os.path.dirname(__file__), "data")
CARDS = {k: Image.open(os.path.join(DATA, f)) for k, f in
         [("barracks", "card_barracks.png"), ("units", "card_units.png")]}
MESSAGING = Image.open(os.path.join(DATA, "messaging_open.png")).convert("RGB")
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
        # buildings that may be floated (shown as "starport" when picked)
        self.starports = [b for b in side["buildings"] if b["type"] in
                          ("Starport", "Factory", "Engineering Bay")]
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
            elif isinstance(self.selected, list):
                self.point_orders = getattr(self, "point_orders", []) + [
                    ("attack", round(x), round(y))]
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
        if isinstance(self.selected, list) and (
                button == "right" or getattr(self, "yamato", False)):
            self.point_orders = getattr(self, "point_orders", []) + [
                ("yamato" if getattr(self, "yamato", False) else "attack",
                 round(x), round(y))]
            self.yamato = False
            return
        if (x, y) == trial.LIFT_BUTTON and self.selected == "starport":
            self.lifted = True                  # Lift Off clicked
            return
        if getattr(self, "messaging", False):     # the Messaging window
            if (x, y) == trial.ACCEPT_BUTTON:
                self.messaging, self.allied = False, True
            return
        if (x, y) == trial.MESSAGING_BUTTON:
            self.messaging = True
            return
        self.selected, self.lifted = None, False
        hit = [u for u in self.alive()
               if abs(self._screen(*self.where(u))[0] - x) < 20
               and abs(self._screen(*self.where(u))[1] - y) < 20]
        if hit:                                     # a unit clicked on
            self.selected = hit[:1]
        for b in self.barracks:
            px, py = self._screen(b["x"], b["y"])
            if abs(x - px) < 130 and abs(y - py) < 95:
                self.selected = "barracks"
        for b in self.starports:
            px, py = self._screen(b["x"], b["y"])
            if abs(x - px) < 130 and abs(y - py) < 95:
                self.selected = "starport"

    def click_with(self, held, x, y):
        self.click(x, y)

    def drag(self, x0, y0, x1, y1):
        self.inputs += 1
        self.time += 0.33
        assert 0 <= x0 < x1 <= 1920 and 40 <= y0 < y1 <= 760
        inside = [u for u in self.alive()
                  # a box picks up a man who only overlaps its edge
                  if x0 - 15 <= self._screen(*self.where(u))[0] <= x1 + 15
                  and y0 - 15 <= self._screen(*self.where(u))[1] <= y1 + 15]
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
            assert self.selected == "starport"   # never a barracks
            self.lifted = True
        if name == "a":
            assert isinstance(self.selected, list)   # never A on nothing
            self.attack = True
        if name == "enter":
            self.chat_open = not getattr(self, "chat_open", False)
        if name == "h" and isinstance(self.selected, list):
            for u in self.selected:
                u["from"] = u["to"] = self.where(u)
                u["held"] = True
        if name == "y":
            self.yamato = True
        if name.isdigit() and name in self.groups:
            self.selected = [u for u in self.groups[name]]
        if name != "a":
            self.last_key = name

    def combo(self, held, name):
        self.inputs += 1
        self.time += 0.15
        if held == "ctrl" and name == "enter":
            self.chat_open = True
            return
        if held == "shift" and name.isdigit():      # add to a key
            assert isinstance(self.selected, list)
            self.groups[name] = self.groups.get(name, []) + [
                u for u in self.selected if u not in self.groups.get(name, [])]
            return
        assert held == "ctrl" and isinstance(self.selected, list)
        self.groups[name] = list(self.selected)

    def type_text(self, text):
        assert getattr(self, "chat_open", False)     # only into the chat box
        self.typed = getattr(self, "typed", []) + [text]

    def sleep(self, s):
        self.time += s

    def card(self):
        self.time += 0.01
        if self.selected == "starport" and self.lifted:   # in the air: Move
            return live.card_cell(screen("units"))
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
        # the bottom panel: one framed picture per selected unit
        if isinstance(self.selected, list) and len(self.selected) > 1:
            for k in range(len(self.selected)):
                x = live.SLOT_ORIGIN[0] + (k % 6) * live.SLOT_STEP[0]
                y = live.SLOT_ORIGIN[1] + (k // 6) * live.SLOT_STEP[1]
                size = live.SLOT_SIZE
                a[y:y + 4, x:x + size] = (0, 60, 200)
                a[y + size - 4:y + size, x:x + size] = (0, 60, 200)
                a[y:y + size, x:x + 4] = (0, 60, 200)
                a[y:y + size, x + size - 4:x + size] = (0, 60, 200)
        s = Image.fromarray(a)
        card = "barracks" if self.selected == "barracks" else \
            "units" if self.selected else None
        if card:
            s.paste(CARDS[card], (1560, 760))
        if getattr(self, "messaging", False):
            s.paste(MESSAGING, (550, 85))
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
    # the countdown runs 1.488 game seconds to a real one (trial 18:
    # bottom clock 05:21 with the countdown at 2:01, 12:35 with 1:16)
    assert trial.round_timer(0) == "5:00"
    assert trial.round_timer(321) in ("1:59", "2:00", "2:01", "2:02", "2:03")
    assert trial.round_timer(755) in ("1:15", "1:16", "1:17")
    assert abs(trial.until_tax(0) - 121) < 1          # 3:00 of countdown
    assert trial.until_tax(122) > 190                 # just paid: next round


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


def test_opening_masses_fast_and_hits_berlin(monkeypatch):
    # the fake game draws no Scouts: the dogfight would only look for
    # them and shift the end of the game (tested on its own instead)
    monkeypatch.setattr(trial, "DOGFIGHT", False)
    m = trial.load_map()
    w = trial.place(m, trial.TARGETS[0])
    for error in [(0, 0), (40, 80), (-60, 10), (70, -60)]:
        g = FakeGame(m, error=error)
        seen = {}
        real_hit = trial.hit
        went = {}                                   # every place each man was sent
        real_send = g.send

        def send(units, mx, my, real_send=real_send, went=went):
            for u in units:
                went.setdefault(id(u), []).append((mx, my))
            real_send(units, mx, my)
        g.send = send

        def hit(io, *a, **k):                       # note the mass as it leaves
            if not seen:
                seen["n"] = sum(near(io.where(u), trial.MASS, 14)
                                for u in io.alive())
                seen["t"] = io.time
            out = real_hit(io, *a, **k)
            game = io
            while hasattr(game, "io"):              # under the wrappers
                game = game.io
            if not hasattr(game, "time_first_hit_done"):
                game.time_first_hit_done = game.time
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
        # (the massing place is a little wider since the mass is spread out)
        assert result["hits"][0] and g.time_first_hit_done <= 120, \
            (error, g.time_first_hit_done)
        assert seen["n"] >= 0.7 * 175, (error, seen)
        # in the end most of everything, Middle East marines included,
        # has been sent at a target, spread along its front
        alive = g.alive()
        spots = [trial.place(m, n)
                 for n in set(trial.TARGETS) | set(trial.NEXT.values())]
        spots.append({"x": trial.BALKS_POINT[0], "y": trial.BALKS_POINT[1]})
        sent = [u for u in alive
                if any(near(u["to"], (p["x"], p["y"]), 20) for p in spots)]
        # (not everything: men who are too few for another hit are held
        # back, and the game may end with a new mass gathering)
        assert len(sent) >= 0.5 * len(alive), (error, len(sent), len(alive))
        # its boxes pick up close to the twelve a selection can hold
        # (7.0: a full box's far half is no longer boxed again at once,
        # when it mostly picked up the same men again, trial 34)
        assert result["units_per_box"] >= 7.0, (error, result)
        # the Middle East marines reached the massing place, whether or
        # not they were in time for a hit
        spawned = [u for u in alive if u.get("spawn")]
        # (the mass is spread out up to 12 tiles from the point)
        assert sum(near(u["to"], trial.MASS, 18) or u in sent
                   for u in spawned) >= 20, error
        # the first hit: Berlin (and, Berlin being undefended here, on
        # down the road to Paris and Madrid)
        beyond = [trial.place(m, n) for n in ("Berlin 1000", "Paris 500",
                                              "Madrid 1000")]
        # (men sent on to the Balkans later count too: where they went)
        at_berlin = [u for u in alive if any(
            near(xy, (p["x"], p["y"]), 20) for p in beyond
            for xy in went.get(id(u), []))]
        assert len(at_berlin) >= 80
        assert len({round(xy[1] / 64) for u in at_berlin
                    for xy in went[id(u)]}) >= 4                   # a wall
        # a spare building (never a barracks) was flown to Warsaw after
        # the first hit
        warsaw = trial.place(m, "Warsaw 200")
        assert any(near((x, y), (warsaw["x"], warsaw["y"]), 3)
                   for k, x, y in g.flights), error
        assert all(k != "barracks" for k, x, y in g.flights)
        # the first hits go north; from about 3:30 the plan turns south
        assert result["targets"][0] == "Berlin 1000"
        # every hit after the first was at least the minimum size
        assert all(h == 0 or h >= 8 for h in result["hits"][1:]), result
        # (a later hit goes only if enough men gather for one; when
        # they do not, they are held, which is what should happen)
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

    def now(self):
        return 100.0                # early in the game: the plan says north

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
    # a new Balkans hit always goes in through Romania, even after one
    # went there (trial 21); it is carried on down the road from there
    assert trial.choose_target(OneShot(s), watch, st) == "Romania 300"
    st.balkan_start = seen                               # no more than at the start
    assert trial.choose_target(OneShot(s), watch, st) == "Berlin 1000"
    g = FakeGame(m)                                      # nobody else in sight
    quiet = g.shot("x")
    watch2 = live.Watch(quiet, side["structures"], side["units"])
    assert trial.choose_target(OneShot(quiet), watch2, trial.State()) \
        == "Berlin 1000"


def test_a_building_floats_to_romania():
    m = trial.load_map()
    g = FakeGame(m)
    g.camera = (0, 0)
    st = trial.State()
    trial.fly_building(g, m, st, "Starport", (190, 110), "Romania 300")
    st.flights_done.add((190, 110))
    romania = trial.place(m, "Romania 300")
    assert g.flights and g.flights[0][0] == "starport"
    assert near(g.flights[0][1:], (romania["x"], romania["y"]), 3)
    assert g.time > 2.5                                  # it waited for lift-off
    sent = len(g.flights)                                # the order is said twice
    trial.flights_after(g, m, st, "Romania 300")         # only once
    assert len(g.flights) == sent


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
    # east is always Berlin, the Balkans always Romania (the repository
    # owner, trial 26: "Warsaw" took the whole army there)
    assert target in ("Berlin 1000", "Romania 300")


def real_start_screen():
    s = Image.new("RGB", (1920, 1080))
    s.paste(Image.open(os.path.join(DATA, "start_minimap.png")), (0, 780))
    return s


def test_the_plan_alternates_fronts_like_the_players_studied():
    assert trial.planned_front(60) == "north"
    assert trial.planned_front(4 * 60) == "south"
    assert trial.planned_front(9 * 60) == "north"
    assert trial.planned_front(13 * 60) == "south"
    # past the studied part of the game it keeps alternating
    late = [trial.planned_front(1260 + 270 * k + 10) for k in range(4)]
    assert late == ["south", "north", "south", "north"]


def stand_at(units, spot, per_row=14):
    for k, u in enumerate(units):
        p = (spot["x"] + (k % per_row - per_row // 2) * 30,
             spot["y"] + (k // per_row - 5) * 30)
        u["from"] = u["to"] = p


def looks(g, watch, m, st, times):
    orders = 0
    for _ in range(times):                          # a few looks, 6 s apart
        a = watch.units(g.shot("a"))
        g.time += 1
        still = a & watch.units(g.shot("b"))
        orders += trial.advance_front(g, watch, m, st, still, g.shot("c"))
        g.time += 6
    return orders


def test_a_hit_that_took_its_target_goes_on_but_a_handful_holds():
    """A whole hit standing idle at Romania goes on to Belgrade. A few
    troops standing somewhere are not a hit: they hold, in reserve."""
    m = trial.load_map()
    side = m["slots"]["5"]
    romania, berlin = trial.place(m, "Romania 300"), trial.place(m, "Berlin 1000")
    road = ("Factory 7", "Hungary 200", "Munich 200", "Frankfurt 200",
            "Amsterdam 100", "Paris 500", "Madrid 1000")
    onward = [trial.place(m, n) for n in road]

    # a handful: 30 men at Romania
    g = FakeGame(m)
    watch = live.Watch(g.shot("start"), side["structures"], side["units"])
    stand_at(g.units[:30], romania)
    g.camera = live.camera_after_click(*live.minimap_point(*trial.MASS))
    st = trial.State()
    st.battle = trial.Battle("Romania 300", 0)
    assert looks(g, watch, m, st, 3) == 0
    assert st.battle.target == "Romania 300"
    assert all(near(u["to"], (romania["x"], romania["y"]), 12)
               for u in g.units[:30])
    assert 0 < st.reserve < trial.MIN_HIT           # counted as a reserve

    # a whole hit: 170 men at Romania
    g = FakeGame(m)
    watch = live.Watch(g.shot("start"), side["structures"], side["units"])
    there = g.units[:170]
    stand_at(there, romania)
    g.camera = live.camera_after_click(*live.minimap_point(*trial.MASS))
    st = trial.State()
    st.battle = trial.Battle("Romania 300", 0)
    assert looks(g, watch, m, st, 6) >= 4
    assert "Factory 7" in st.sent_at                # the watch moves on too
    assert st.battle.target in road
    moved = sum(any(near(u["to"], (p["x"], p["y"]), 12) for p in onward)
                for u in there)
    assert moved >= 100, moved


def test_the_road_south_leads_to_belgrade_and_on_to_the_netherlands():
    m = trial.load_map()
    road, at = [], "Romania 300"
    while at in trial.NEXT:
        at = trial.NEXT[at]
        road.append(at)
        trial.place(m, at)                          # every stop is on the map
    # Romania, Belgrade (Factory 7), Hungary, Munich, Frankfurt, the
    # Netherlands, and only then Paris and Madrid
    assert road == ["Factory 7", "Hungary 200", "Munich 200",
                    "Frankfurt 200", "Amsterdam 100", "Paris 500",
                    "Madrid 1000"]
    assert trial.NEXT["Warsaw 200"] == "Berlin 1000"


def test_no_hit_below_the_minimum_even_if_the_general_asks():
    """With few men at the massing place and none forward, there is no
    hit, whatever the general says: they are kept in reserve."""
    m = trial.load_map()
    side = m["slots"]["5"]
    g = FakeGame(m)
    watch = live.Watch(g.shot("start"), side["structures"], side["units"])
    for k, u in enumerate(g.units):                 # 60 at the mass, rest far off
        if k < 60:
            p = (trial.MASS[0] + (k % 10 - 5) * 28, trial.MASS[1] + (k // 10 - 3) * 28)
        else:
            p = (7000 + (k % 10) * 30, 600 + (k // 10) * 30)   # at home, far east
        u["from"] = u["to"] = p
    g.camera = live.camera_after_click(*live.minimap_point(*trial.MASS))
    st = trial.State()
    st.hit_wanted = True
    real = trial.gather_idle
    trial.gather_idle = lambda io, w, md, s, tried: (0, io.shot("x"), set())
    old_limit = trial.TRIAL_SECONDS
    trial.TRIAL_SECONDS = 20
    try:
        strength, went = trial.build_big_mass(g, watch, m, st, 0.0)
    finally:
        trial.gather_idle, trial.TRIAL_SECONDS = real, old_limit
    assert strength < trial.MIN_HIT and not went    # too few
    assert not st.hit_wanted                        # the request was dropped


def panel_screen(name):
    """A screen with a real bottom panel pasted in."""
    s = Image.new("RGB", (1920, 1080))
    s.paste(Image.open(os.path.join(DATA, name)), (560, 780))
    return s


def test_reads_how_many_units_are_selected():
    assert live.selected_count(panel_screen("panel_12.png")) == 12
    assert live.selected_count(panel_screen("panel_9.png")) == 9
    assert live.selected_count(panel_screen("panel_3.png")) == 3
    assert live.selected_count(Image.new("RGB", (1920, 1080))) == 0
    assert live.selected_count(screen("units")) == 1      # one unit alone
    assert live.selected_count(screen("barracks")) == 0   # a building


def test_men_at_the_mass_are_judged_at_a_glance():
    """No boxes: from the supply figure and where our pixels are."""
    # a packed crowd of few pixels is still seen as most of the army
    assert trial.men_at_mass((204, 200), 57, 150) >= 140
    # nearly everyone is away: few at the mass, however high the supply
    assert trial.men_at_mass((190, 200), 5, 300) <= 20
    # never more than Russia has (trial 17: "240 men" with supply 136)
    assert trial.men_at_mass((136, 200), 240, 248) <= 136
    assert 40 <= trial.men_at_mass((136, 200), 240, 248) <= 100
    # no supply figure to read: the pixels are all there is
    assert trial.men_at_mass(None, 90, 10) == 90


class StubIO:
    """Records what the bot presses; time stands still unless moved."""
    def __init__(self):
        self.t, self.keys, self.clicks, self.lines = 100.0, [], [], []
        self.combos = []
    def combo(self, held, name): self.combos.append((held, name))
    def click_with(self, held, x, y): self.clicks.append((x, y, held))
    def now(self): return self.t
    def sleep(self, s): pass
    def key(self, name): self.keys.append(name)
    def click(self, x, y, button="left"): self.clicks.append((x, y, button))
    def log(self, text): self.lines.append(text)


class StubWatch:
    def __init__(self, ours, axis):
        self.ours, self.axis = set(ours), set(axis)
    def units(self, picture): return set(self.ours)
    def others(self, picture, slots): return set(self.axis)
    def forget(self, pixels): pass


def blob(map_xy, n=5):
    c, r = live.to_drawn(*map_xy)
    c, r = int(c), int(r)
    return {(c + i, r + j) for i in range(n) for j in range(n)}


def test_a_losing_hit_is_broken_off_and_the_fleet_stays_over_our_army(monkeypatch):
    m = trial.load_map()
    w = trial.place(m, "Warsaw 200")
    front = (w["x"], w["y"])
    monkeypatch.setattr(trial, "select_group", lambda *a, **k: True)
    home = live.minimap_point(*trial.MASS)

    # going well: the fleet, one stack, over the middle of our own troops
    # at the front, not over the enemy
    monkeypatch.setattr(trial, "enemy_near_fleet", lambda io_, spot: (0, None))
    st, io = trial.State(), StubIO()
    st.air_keys = ["9", "0"]
    st.battle = trial.Battle("Berlin 1000", 0)
    st.battle.front = front
    st.battle.samples = [(10, 100, 8, 20), (40, 90, 8, 14)]
    enemy = (front[0] - 5 * 32, front[1])
    watch = StubWatch(blob(front), blob(enemy))
    assert trial.fight(io, watch, m, st, None) == 0
    assert io.keys == ["9", "a", "0", "a"]
    ox, oy = live.minimap_point(*trial.middle(blob(front)))
    assert all(abs(x - ox) <= 1 and abs(y - oy) <= 1 and b == "left"
               for x, y, b in io.clicks), io.clicks
    assert not st.battle.retreated

    # losing (under a third of its peak left): everyone walks home, once
    st.battle.samples.append((70, 20, 30, 14))
    io = StubIO()
    assert trial.fight(io, watch, m, st, None) >= 1
    assert st.battle.retreated and st.air_home
    # the ground walks to the mass, the fleet to its own spot by it
    park = live.minimap_point(*trial.fleet_spot())
    assert io.clicks and all(c in ((*home, "right"), (*park, "right"))
                             for c in io.clicks)
    assert (*park, "right") in io.clicks
    assert "a" not in io.keys                   # a walk, not an attack
    io = StubIO()
    assert trial.fight(io, watch, m, st, None) == 0 and not io.clicks


def test_troops_at_the_mass_meet_an_enemy_inside_russia(monkeypatch):
    m = trial.load_map()
    monkeypatch.setattr(trial, "select_group", lambda *a, **k: True)
    st, io = trial.State(), StubIO()
    st.air_keys = ["9"]
    mass = blob(trial.MASS, 6)
    inside = (200 * 32, 60 * 32)                # deep in Russia
    # a few dots, the enemy in his own country, or enemy that was always
    # near Odessa and Romania and only now shows: nothing
    for axis in (blob(inside, 2), blob((100 * 32, 80 * 32), 6),
                 blob((164 * 32, 104 * 32), 6), blob((158 * 32, 118 * 32), 6)):
        assert trial.defend_home(io, StubWatch(mass, axis), m, st, None,
                                 mass) == 0
    watch = StubWatch(mass, blob(inside, 5))
    assert trial.defend_home(io, watch, m, st, None, mass) >= 2
    ix, iy = live.minimap_point(*trial.middle(blob(inside, 5)))
    assert all(abs(x - ix) <= 1 and abs(y - iy) <= 1 for x, y, b in io.clicks)
    assert any("inside Russia" in line for line in io.lines)
    # not again straight away
    assert trial.defend_home(io, watch, m, st, None, mass) == 0


def test_at_full_supply_a_lost_hit_does_not_stop_the_next(monkeypatch):
    """Trial 19: the first hit was lost, so the bot wanted 240 for the
    next; supply was full at 235 with about 170 at the mass, and it
    never hit again. At full supply the least hit must be enough."""
    m = trial.load_map()
    side = m["slots"]["5"]
    g = FakeGame(m)
    watch = live.Watch(g.shot("start"), side["structures"], side["units"])
    st = trial.State()
    battle = trial.Battle("Berlin 1000", 0)
    battle.samples = [(10, 200, 5, 30), (60, 20, 5, 30)]    # losing
    st.battle = battle
    monkeypatch.setattr(trial.Battle, "sample", lambda *a, **k: None)
    monkeypatch.setattr(trial, "gather_idle",
                        lambda io, w, md, s, tried: (0, io.shot("x"), set()))
    monkeypatch.setattr(trial.numbers, "read_supply", lambda p: (235, 200))
    monkeypatch.setattr(trial, "men_at_mass", lambda *a: 170)
    monkeypatch.setattr(trial, "advance_front", lambda *a, **k: 0)
    monkeypatch.setattr(trial, "fight", lambda *a, **k: 0)
    monkeypatch.setattr(trial, "defend_home", lambda *a, **k: 0)
    monkeypatch.setattr(trial, "choose_target", lambda *a, **k: "Berlin 1000")
    assert battle.verdict()[0] == "losing"
    strength, went = trial.build_big_mass(g, watch, m, st, 0.0, battle)
    assert went and strength >= trial.MIN_HIT and st.need == trial.MIN_HIT


def test_a_hit_leaves_nobody_at_the_massing_place():
    """Trials 20 and 21: about a third of every hit stayed at the
    massing place. Packed men under a box are more than the twelve the
    game picks; a full box must not count its ground as done."""
    m = trial.load_map()
    side = m["slots"]["5"]
    g = FakeGame(m)
    watch = live.Watch(g.shot("start"), side["structures"], side["units"])
    for k, u in enumerate(g.units):
        if k < 170:                                 # packed tight at the mass
            p = (trial.MASS[0] + (k % 17 - 8) * 14,
                 trial.MASS[1] + (k // 17 - 5) * 14)
        else:
            p = (7000 + (k % 10) * 30, 600 + (k // 10) * 30)
        u["from"] = u["to"] = p
    st = trial.State()
    st.men_per_pixel = 0.4                          # the glance thinks them spread out
    st.ground_keys, st.rekey = [], 8
    trial.hit(g, watch, m, st, "Berlin 1000", use_keys=False)
    left = [u for u in g.units[:170] if near(u["to"], trial.MASS, 14)]
    assert len(left) <= 0.1 * 170, len(left)


def test_after_berlin_is_cleared_the_army_goes_on_to_paris_then_madrid(monkeypatch):
    m = trial.load_map()
    side = m["slots"]["5"]
    berlin, paris = trial.place(m, "Berlin 1000"), trial.place(m, "Paris 500")
    assert trial.NEXT["Berlin 1000"] == "Paris 500"
    assert trial.NEXT["Paris 500"] == "Madrid 1000"
    # a whole hit standing at Berlin, nothing of the enemy left: on to Paris
    g = FakeGame(m)
    watch = live.Watch(g.shot("start"), side["structures"], side["units"])
    there = g.units[:170]
    stand_at(there, berlin)
    g.camera = live.camera_after_click(*live.minimap_point(*trial.MASS))
    monkeypatch.setattr(watch, "others", lambda pic, slots: set())
    st = trial.State()
    st.battle = trial.Battle("Berlin 1000", 0)
    assert looks(g, watch, m, st, 15) >= 4
    assert "Berlin 1000" in st.reached and "Paris 500" in st.sent_at
    madrid = trial.place(m, "Madrid 1000")
    # nothing defends Paris here either, so they go on to Madrid too
    moved = sum(near(u["to"], (paris["x"], paris["y"]), 12)
                or near(u["to"], (madrid["x"], madrid["y"]), 16) for u in there)
    assert moved >= 100, moved
    # new hits to the east always go to Berlin first, even once Berlin
    # and Paris are taken: Paris and Madrid are only reached through it
    st2 = trial.State()
    assert trial.east_next(st2) == "Berlin 1000"
    st2.reached |= {"Warsaw 200", "Berlin 1000", "Paris 500"}
    assert trial.east_next(st2) == "Berlin 1000"
    st2.advised = ("Warsaw", 0.0)                   # Warsaw is taken: Berlin
    io = StubIO()
    io.t = 1.0
    st2.advised = ("Warsaw 200", 0.0)
    assert trial.choose_target(io, None, st2) == "Berlin 1000"
    st2.advised = ("Berlin 1000", 0.0)
    assert trial.choose_target(io, None, st2) == "Berlin 1000"


def test_berlin_reached_but_not_cleared_is_cleared_first(monkeypatch):
    m = trial.load_map()
    side = m["slots"]["5"]
    berlin = trial.place(m, "Berlin 1000")
    g = FakeGame(m)
    watch = live.Watch(g.shot("start"), side["structures"], side["units"])
    stand_at(g.units[:170], berlin)
    g.camera = live.camera_after_click(*live.minimap_point(*trial.MASS))
    c, r = live.to_drawn(berlin["x"], berlin["y"])
    enemy = {(int(c) + i, int(r) + j) for i in range(-3, 4) for j in range(-3, 4)}
    monkeypatch.setattr(watch, "others", lambda pic, slots: set(enemy))
    st = trial.State()
    st.battle = trial.Battle("Berlin 1000", 0)
    looks(g, watch, m, st, 4)
    assert st.battle.target == "Berlin 1000" and st.battle.clearing
    assert "Paris 500" not in st.sent_at


def test_a_balkans_hit_reaches_paris_only_through_the_netherlands():
    st = trial.State()
    st.reached |= {"Romania 300", "Factory 7", "Hungary 200", "Munich 200",
                   "Frankfurt 200"}
    assert trial.south_next(st) == "Romania 300"    # new hits start at Romania
    assert "Amsterdam 100" not in trial.taken_on_the_way(st, "Paris 500")
    st.reached.add("Amsterdam 100")
    assert "Amsterdam 100" in trial.taken_on_the_way(st, "Paris 500")
    # Paris comes from Berlin or from Amsterdam, nowhere else
    assert sorted(k for k, v in trial.NEXT.items() if v == "Paris 500") \
        == ["Amsterdam 100", "Berlin 1000"]


def test_the_fleet_is_scouts_and_one_heavy_artillery_on_its_own_key():
    """Scouts and a Heavy Artillery, added with Shift + key; never the
    Battlecruisers. A full key goes on to the next."""
    m = trial.load_map()
    g = FakeGame(m)
    st = trial.State()
    added = trial.build_fleet(g, m, st)
    scouts = [a for a in m["slots"]["5"]["air"] if a["type"] == "Scout"]
    assert added == len(scouts) == 6
    assert st.air_keys == ["9"] and st.fleet[0]["scouts"] == 6
    ha = st.fleet[0]["ha"]
    assert ha in trial.HEAVY_ARTILLERY
    group = g.groups["9"]
    assert len(group) == 7                          # 6 Scouts + the artillery
    ships = [(a["x"], a["y"]) for a in m["slots"]["5"]["air"]
             if a["type"] == "Battlecruiser"]
    assert not any(u["from"] in ships for u in group)
    # a full key: the next Scouts go on the next key, with its artillery
    st.fleet[0]["scouts"] = trial.FLEET_SIZE
    s = scouts[0]
    assert trial.add_to_fleet(g, st, s["x"], s["y"])
    assert st.air_keys == ["9", "0"] and st.fleet[1]["scouts"] == 1
    assert st.fleet[1]["ha"] != ha


def fleet_state(scouts=6):
    st = trial.State()
    st.fleet = [{"key": "9", "scouts": scouts, "ha": trial.HEAVY_ARTILLERY[0]}]
    st.air_keys = ["9"]
    st.ground_keys = list("12345678")
    return st


def fake_new_keys(monkeypatch):
    def open_key(io, st):
        if len(st.fleet) >= len(trial.AIR_KEYS):
            return False
        key = trial.AIR_KEYS[len(st.fleet)]
        st.fleet.append({"key": key, "scouts": 0, "ha": None})
        st.air_keys.append(key)
        if key in st.ground_keys:
            st.ground_keys.remove(key)
        return True
    monkeypatch.setattr(trial, "open_fleet_key", open_key)


def test_new_scouts_from_the_factories_go_on_the_fleet_keys(monkeypatch):
    from bot import team
    m = trial.load_map()
    fake_new_keys(monkeypatch)
    io = StubIO()
    io.shot = lambda label, keep=True: None
    st = fleet_state(6)
    st.clock = team.GameClock(io.now)
    looked = []
    monkeypatch.setattr(trial, "scouts_on_top",
                        lambda io_, st_, x, y, every=True: looked.append((x, y)) or 2)
    monkeypatch.setattr(trial, "picked_are_scouts", lambda io_, st_, n: True)
    monkeypatch.setattr(trial, "trim_selection", lambda io_, keep: 1 / 0)
    # just before the first tax: nothing
    st.clock.value = (trial.TAX_MARK + 1) / trial.COUNTDOWN_RATE
    assert trial.collect_new_scouts(io, None, m, st) == 0
    # just after it: two from each factory; a pair that does not fit
    # starts the next key rather than being split
    st.clock.value = (trial.TAX_MARK + 5) / trial.COUNTDOWN_RATE
    assert trial.collect_new_scouts(io, None, m, st) == 6
    # each factory once, the third again after starting the new key
    assert len(looked) == 4 and len(set(looked)) == 3
    assert [f["scouts"] for f in st.fleet] == [10, 2]
    assert st.air_keys == ["9", "0"]
    assert ("shift", "9") in io.combos and ("shift", "0") in io.combos
    # not again in the same round; again in the next
    assert trial.collect_new_scouts(io, None, m, st) == 0
    st.clock.value = (trial.TAX_MARK + 305) / trial.COUNTDOWN_RATE
    assert trial.collect_new_scouts(io, None, m, st) == 6
    assert [f["scouts"] for f in st.fleet] == [10, 8]


def test_a_factory_with_nothing_on_top_is_tried_a_few_times(monkeypatch):
    from bot import team
    m = trial.load_map()
    io = StubIO()
    st = fleet_state(6)
    st.clock = team.GameClock(io.now)
    tries = []
    monkeypatch.setattr(trial, "scouts_on_top",
                        lambda io_, st_, x, y, every=True: (tries.append(1), 0)[1])
    st.clock.value = (trial.TAX_MARK + 5) / trial.COUNTDOWN_RATE
    for _ in range(6):
        trial.collect_new_scouts(io, None, m, st)
    assert len(tries) == 3 * trial.SCOUT_TRIES      # then left alone


def test_what_is_not_a_scout_is_not_put_on_the_fleet(monkeypatch):
    m = trial.load_map()
    io = StubIO()
    io.shot = lambda label, keep=True: None
    st = fleet_state(6)
    monkeypatch.setattr(trial, "picked_are_scouts", lambda io_, st_, n: False)
    assert trial.add_selected_scouts(io, st, lambda: 2) == 0
    assert st.fleet[0]["scouts"] == 6 and not io.combos
    assert any("not all Scouts" in line for line in io.lines)


def test_scouts_are_told_from_other_units_by_their_panel_pictures():
    """What a Scout looks like is learnt from Russia's own Scouts at the
    start; a group with anything else in it is refused."""
    import numpy as np
    from PIL import Image
    st = trial.State()
    scout = Image.new("RGB", (1920, 1080), (10, 10, 10))
    for i in range(3):                              # three framed Scouts
        x0, y0, x1, y1 = trial._frame_box(i, 3)
        scout.paste((40, 200, 40), (x0 + 10, y0 + 10, x1 - 10, y1 - 30))
    st.scout_frame = trial._crop(scout, trial._frame_box(0, 3))
    io = StubIO()
    io.shot = lambda label, keep=True: scout
    assert trial.picked_are_scouts(io, st, 3)
    mixed = scout.copy()                            # the third is something else
    x0, y0, x1, y1 = trial._frame_box(2, 3)
    mixed.paste((10, 10, 10), (x0 + 4, y0 + 4, x1 - 4, y1 - 4))
    mixed.paste((200, 200, 200), (x0 + 30, y0 + 10, x1 - 10, y1 - 10))
    io.shot = lambda label, keep=True: mixed
    assert not trial.picked_are_scouts(io, st, 3)
    # one alone: the big picture and name
    one = Image.new("RGB", (1920, 1080), (10, 10, 10))
    one.paste((40, 200, 40), (620, 890, 760, 1000))
    st.scout_one = trial._crop(one, trial.PANEL_ONE)
    io.shot = lambda label, keep=True: one
    assert trial.picked_are_scouts(io, st, 1)
    other = Image.new("RGB", (1920, 1080), (10, 10, 10))
    other.paste((120, 60, 60), (800, 890, 1100, 1040))
    io.shot = lambda label, keep=True: other
    assert not trial.picked_are_scouts(io, st, 1)


def test_twelve_scouts_at_moscow_fill_a_key_and_the_rest_join_another(monkeypatch):
    from bot import team
    m = trial.load_map()
    fake_new_keys(monkeypatch)
    io = StubIO()
    st = fleet_state(6)
    st.clock = team.GameClock(io.now)
    st.clock.value = (trial.MOSCOW_AIR[0] + 5) / trial.COUNTDOWN_RATE
    st.scouts_done |= {(k, n) for k in range(20) for n in trial.SCOUT_FACTORIES}
    picks = iter([12, 12, 1, 0])                    # what each look picks up
    monkeypatch.setattr(trial, "scouts_on_top",
                        lambda io_, st_, x, y, every=True: next(picks))
    monkeypatch.setattr(trial, "picked_are_scouts", lambda io_, st_, n: True)
    monkeypatch.setattr(trial, "trim_selection", lambda io_, keep: keep)
    assert trial.collect_new_scouts(io, None, m, st) == 12
    # eleven start key 0; the twelfth goes on key 9, which had room
    assert [f["scouts"] for f in st.fleet] == [7, 11]
    assert st.air_keys == ["9", "0"]
    assert trial.MOSCOW_AIR[0] in st.moscow_done


def test_new_scouts_are_kept_out_of_the_mass_while_they_are_fetched():
    from bot import team
    m = trial.load_map()
    io = StubIO()
    st = fleet_state()
    st.clock = team.GameClock(io.now)
    f = trial.place(m, "Factory 1")
    there = blob((f["x"], f["y"]), 2)
    st.clock.value = (trial.TAX_MARK + 10) / trial.COUNTDOWN_RATE
    assert trial.scout_spots(io, m, st, there) == there
    # later in the round: still kept while its Scouts are not on a key
    st.clock.value = (trial.TAX_MARK + 100) / trial.COUNTDOWN_RATE
    assert trial.scout_spots(io, m, st, there) == there
    st.scouts_done.add((0, "Factory 1"))
    assert trial.scout_spots(io, m, st, there) == set()


def test_the_fleet_keeps_back_from_more_than_three_enemy_to_a_scout(monkeypatch):
    m = trial.load_map()
    w = trial.place(m, "Warsaw 200")
    front = (w["x"], w["y"])
    st, io = trial.State(), StubIO()
    st.fleet = [{"key": "9", "scouts": 6, "ha": None}]
    st.air_keys = ["9"]
    st.battle = trial.Battle("Berlin 1000", 0)
    st.battle.front = front
    st.battle.samples = [(10, 100, 8, 20), (40, 90, 8, 14)]
    ours = blob(front, 5)
    io.shot = lambda label, keep=True: None
    d = lambda p, q: ((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2) ** 0.5
    # the game screen shows 15 enemy round the army: under 3 to a Scout
    monkeypatch.setattr(trial, "enemy_near_fleet", lambda io_, spot: (15, None))
    spot = trial.steer_fleet(io, StubWatch(ours, set()), m, st, None)
    assert spot == trial.middle(ours)
    # 30 enemy round the front, none further back: held back toward the
    # mass, over our own side
    monkeypatch.setattr(trial, "enemy_near_fleet", lambda io_, spot: (
        30 if d(spot, trial.middle(ours)) < 2 * 32 else 4, None))
    io.t += trial.AIR_LOOK_EVERY                    # time to count again
    spot = trial.steer_fleet(io, StubWatch(ours, set()), m, st, None)
    assert d(spot, trial.MASS) < d(trial.middle(ours), trial.MASS)
    assert any("holding further back" in line for line in io.lines)


def test_enemy_are_counted_on_the_game_screen_near_the_fleet():
    from PIL import Image
    pic = Image.new("RGB", (1920, 1080), (30, 50, 25))      # grass
    for k in range(10):                                     # ten red men
        x, y = 700 + (k % 5) * 60, 300 + (k // 5) * 60
        pic.paste((210, 30, 30), (x, y, x + 13, y + 13))
    pic.paste((205, 190, 40), (900, 500, 960, 503))         # a health bar
    pic.paste((210, 30, 30), (20, 20, 60, 60))              # the kills list
    pic.paste((200, 40, 40), (1700, 600, 1713, 613))        # far away
    pic.paste((140, 70, 30), (800, 450, 813, 463))          # Russia's brown
    n = trial.enemy_on_screen(pic, 820, 330, 300)
    assert 8 <= n <= 12, n
    assert trial.enemy_on_screen(pic, 1500, 200, 150) == 0


def test_the_fleet_stays_over_a_shrinking_hit_and_parks_when_it_is_over(monkeypatch):
    """Trial 26: parked as soon as the hit shrank, the air sat out the
    rest of it. It stays while our troops are at the front; it parks
    once none are, after the hit has had time to get there."""
    m = trial.load_map()
    monkeypatch.setattr(trial, "enemy_near_fleet", lambda io_, spot: (0, None))
    w = trial.place(m, "Warsaw 200")
    front = (w["x"], w["y"])
    st, io = trial.State(), StubIO()
    st.fleet = [{"key": "9", "scouts": 6, "ha": None}]
    st.air_keys = ["9"]
    st.battle = trial.Battle("Berlin 1000", io.t - 100)
    st.battle.front = front
    st.battle.samples = [(10, 100, 8, 20), (40, 45, 8, 14)]   # shrinking
    trial.fight(io, StubWatch(blob(front), set()), m, st, None)
    park = live.minimap_point(*trial.fleet_spot())
    assert not st.air_home and (*park, "right") not in io.clicks
    assert "9" in io.keys and "a" in io.keys            # steered over the army
    # no troops of ours left at the front: parked
    io2 = StubIO()
    io2.t = io.t + 10
    st.air_moved = -1e9
    trial.fight(io2, StubWatch(set(), set()), m, st, None)
    assert st.air_home and (*park, "right") in io2.clicks
    # just after a hit is sent, before the troops get there: not parked
    st3, io3 = trial.State(), StubIO()
    st3.air_keys = ["9"]
    st3.battle = trial.Battle("Berlin 1000", io3.t - 5)
    trial.fight(io3, StubWatch(set(), set()), m, st3, None)
    assert not st3.air_home and io3.clicks == []


def test_our_own_buildings_red_lamps_are_not_counted_as_enemy():
    from PIL import Image
    pic = Image.new("RGB", (1920, 1080), (30, 50, 25))
    pic.paste((230, 20, 20), (800, 400, 813, 413))          # a lamp on our depot
    pic.paste((230, 20, 20), (1000, 400, 1013, 413))        # an enemy man
    assert trial.enemy_on_screen(pic, 900, 400, 400) == 2
    assert trial.enemy_on_screen(pic, 900, 400, 400,
                                 skip=[(806, 406, 40)]) == 1
    # blood and fire are darker than team red; gold Scouts are not counted
    pic2 = Image.new("RGB", (1920, 1080), (30, 50, 25))
    pic2.paste((150, 10, 10), (800, 400, 830, 430))         # blood
    pic2.paste((230, 200, 40), (900, 400, 930, 430))        # a gold Scout
    assert trial.enemy_on_screen(pic2, 900, 400, 400) == 0


def test_a_stuck_spot_is_tried_again_later(monkeypatch):
    """Trial 33: once a spot by a factory was "stuck", the tanks and men
    the factory made there every round were never brought to the mass."""
    m = trial.load_map()
    st, io = trial.State(), StubIO()
    io.shot = lambda label, keep=True: None
    f = trial.place(m, "Factory 1")
    body = blob((f["x"] + 20 * 32, f["y"] + 20 * 32), 3)
    watch = StubWatch(body, set())
    sent = []
    monkeypatch.setattr(trial, "select_group", lambda *a, **k: True)
    monkeypatch.setattr(trial, "to_mass", lambda *a, **k: sent.append(1))
    monkeypatch.setattr(trial, "reinforce_target", lambda io_, st_: None)
    monkeypatch.setattr(trial, "scout_spots", lambda *a: set())
    tried = {}
    for _ in range(trial.STUCK_AFTER + 2):
        io.t += trial.RETRY_IDLE + 1
        trial.gather_idle(io, watch, m, st, tried)
    assert len(sent) == trial.STUCK_AFTER           # then left alone
    io.t += trial.STUCK_FORGET + 1
    trial.gather_idle(io, watch, m, st, tried)
    assert len(sent) == trial.STUCK_AFTER + 1       # tried afresh


def test_an_enemy_inside_russia_gone_a_moment_later_sends_nothing(monkeypatch):
    """Trial 34: 8 groups went west of Moscow at the end of the game.
    The enemy is looked at again before anyone is sent."""
    m = trial.load_map()
    st, io = trial.State(), StubIO()
    looks = iter([{(150, 50 + i % 3) for i in range(40)} | {(150 + i // 3, 50) for i in range(40)}, set()])
    seen = next(looks)
    monkeypatch.setattr(trial, "axis_at_home", lambda w, pic: seen if pic == "first" else set())
    io.shot = lambda label, keep=True: "again"
    sent = []
    monkeypatch.setattr(trial, "select_group", lambda *a, **k: sent.append(1) or True)
    assert trial.defend_home(io, StubWatch(set(), set()), m, st, "first", set()) == 0
    assert sent == [] and any("gone a moment later" in l for l in io.lines)


def test_a_hits_boxes_are_mapped_out_first_and_never_overlap():
    """The repository owner: for a hit, every box of a view is planned
    before any is drawn, back to front, no two on the same ground."""
    m = trial.load_map()
    w = trial.place(m, "Berlin 1000")
    view = blob(trial.MASS, 8)
    plan = trial.plan_boxes(view, (w["x"], w["y"]), trial.back_to_front, 6)
    assert sum(len(c) for c in plan) == len(view)
    assert len({p for c in plan for p in c}) == len(view)       # no overlap
    tc, tr = live.to_drawn(w["x"], w["y"])
    d = lambda p: (p[0] - tc) ** 2 + (p[1] - tr) ** 2
    assert d(plan[0][0]) >= d(plan[-1][0])                      # back first


def test_a_hit_sweep_draws_the_planned_boxes_in_order(monkeypatch):
    m = trial.load_map()
    st, io = trial.State(), StubIO()
    io.shot = lambda label, keep=True: None
    st.box_px = 6
    monkeypatch.setattr(trial, "look_at", lambda io_, x, y, wait=0: (x, y))
    drawn = []

    def select(io_, st_, seed, pool, cam):
        chunk = pool[:6]
        drawn.append(set(chunk))
        return chunk, 10
    monkeypatch.setattr(trial, "select_full", select)
    monkeypatch.setattr(trial, "send_at", lambda *a, **k: None)
    watch = StubWatch(blob(trial.MASS, 8), set())
    n, found = trial.sweep_mass(io, watch, m, st, "Berlin 1000", settle=0,
                                plan_first=True)
    assert n == len(drawn) and n >= 4
    for i, a in enumerate(drawn):                # never the same ground twice
        for b in drawn[:i]:
            assert not (a & b)
    assert any("boxes mapped out for this view" in l for l in io.lines)
