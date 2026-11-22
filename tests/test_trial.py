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
            if self.selected == "barracks" and on_map:
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
        self.selected = None
        for b in self.barracks:
            px, py = self._screen(b["x"], b["y"])
            if abs(x - px) < 130 and abs(y - py) < 95:
                self.selected = "barracks"

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


def test_map_data():
    m = trial.load_map()
    assert len(trial.barracks_of(m)) == 8
    assert len(m["slots"]["5"]["units"]) == 175
    w = trial.place(m, trial.TARGET)
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
    w = trial.place(m, trial.TARGET)
    for error in [(0, 0), (40, 80), (-60, 10), (70, -60)]:
        g = FakeGame(m, error=error)
        seen = {}
        real_hit = trial.hit

        def hit(io, *a, **k):                       # note the mass as it leaves
            if not seen:
                seen["n"] = sum(near(io.where(u), trial.MASS, 14)
                                for u in io.alive())
                seen["t"] = io.time
            return real_hit(io, *a, **k)
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
        assert seen["t"] <= 110, (error, seen)
        assert seen["n"] >= 0.7 * 175, (error, seen)
        # in the end most of everything, Middle East marines included,
        # has been sent at Berlin, spread along its front
        alive = g.alive()
        at_berlin = [u for u in alive if near(u["to"], (w["x"], w["y"]), 20)]
        assert len(at_berlin) >= 0.7 * len(alive), (error, len(at_berlin))
        spawned = [u for u in at_berlin if u.get("spawn")]
        assert len(spawned) >= 20, (error, len(spawned))
        ys = {round(u["to"][1] / 64) for u in at_berlin}
        assert len(ys) >= 6                         # a wall, not one point
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
    berlin_x = trial.place(trial.load_map(), trial.TARGET)["x"]
    assert berlin_x < trial.MASS[0]                 # Berlin is to the west
    groups = [[(150, 70)], [(170, 70), (172, 71)], [(160, 72)]]
    ordered = trial.back_to_front(groups, berlin_x)
    assert [g[0][0] for g in ordered] == [170, 160, 150]   # east goes first
