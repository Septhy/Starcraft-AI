import os

from PIL import Image

from bot import trial
from eyes import live

DATA = os.path.join(os.path.dirname(__file__), "data")


def screen(card):
    """A 1920 x 1080 screen with a real minimap and command card pasted in."""
    s = Image.new("RGB", (1920, 1080))
    s.paste(Image.open(os.path.join(DATA, "live_minimap.png")), (0, 780))
    if card:
        s.paste(Image.open(os.path.join(DATA, card)), (1560, 760))
    return s


class FakeGame:
    """Pretends to be the game. Things appear on screen `error` pixels
    away from where the bot's arithmetic says. A click near a barracks
    selects it; a box selects up to 12 units inside it; an attack-move
    sends the selected units to the clicked map point at once."""

    def __init__(self, mapdata, error=(40, 80), showing=True):
        self.barracks = trial.barracks_of(mapdata)
        self.units = [list(u) for u in mapdata["slots"][trial.SLOT]["units"]]
        self.error, self.showing = error, showing
        self.camera, self.selected, self.attack = None, None, False
        self.m_on_barracks = self.m_elsewhere = self.rallies = 0
        self.time, self.inputs = 0.0, 0

    def _screen(self, x, y):
        px, py = live.on_screen(x, y, self.camera)
        return px + self.error[0], py + self.error[1]

    def click(self, x, y, button="left"):
        self.inputs += 1
        m = live.MINIMAP
        on_map = m["left"] <= x < m["left"] + m["width"] and y >= m["top"]
        if button == "right":
            if self.selected == "barracks" and on_map:
                self.rallies += 1
            return
        if on_map:
            mx = (x - m["left"] + 0.5) / m["width"] * live.MAP_PX[0]
            my = (y - m["top"] + 0.5) / m["height"] * live.MAP_PX[1]
            if self.attack and isinstance(self.selected, list):
                for u in self.selected:      # they stand around the point
                    k = self.units.index(u)
                    u[0] = mx + (k % 14 - 7) * 40
                    u[1] = my + (k // 14 - 6) * 40
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
        assert 0 <= x0 < x1 <= 1920 and 40 <= y0 < y1 <= 760
        inside = [u for u in self.units
                  if x0 <= self._screen(*u)[0] <= x1
                  and y0 <= self._screen(*u)[1] <= y1]
        self.selected = inside[:12] or None

    def key(self, name):
        self.inputs += 1
        if name == "m":
            if self.selected == "barracks":
                self.m_on_barracks += 1
            else:
                self.m_elsewhere += 1
        if name == "a":
            assert isinstance(self.selected, list)   # never A on nothing
            self.attack = True

    def sleep(self, s):
        self.time += s

    def now(self):
        return self.time

    def shot(self, label, keep=True):
        if not self.showing:
            return Image.new("RGB", (1920, 1080))
        return screen("card_barracks.png" if self.selected == "barracks"
                      else "card_units.png" if self.selected else None)

    def log(self, text, quiet=False):
        pass


def near(u, point, tiles):
    return abs(u[0] - point[0]) < tiles * 32 and abs(u[1] - point[1]) < tiles * 32


def test_reads_the_real_pictures():
    assert live.minimap_showing(screen("card_units.png"))
    assert not live.minimap_showing(Image.new("RGB", (1920, 1080)))
    assert live.barracks_selected(screen("card_barracks.png"))
    assert not live.barracks_selected(screen("card_units.png"))
    assert live.units_selected(screen("card_units.png"))
    assert not live.units_selected(screen("card_barracks.png"))
    assert not live.units_selected(screen(None))


def test_map_data():
    m = trial.load_map()
    assert len(trial.barracks_of(m)) == 8
    assert len(m["slots"]["5"]["units"]) == 175
    w = trial.place(m, trial.TARGET)
    x, y = live.minimap_point(w["x"], w["y"])
    assert 13 < x < 302 and 817 < y < 1033


def test_camera_stays_on_the_map():
    cam = live.camera_after_click(*live.minimap_point(6650, 100))
    assert cam[1] == 1080 / live.ZOOM / 2          # held at the top edge
    assert live.on_screen(6650, 100, cam)[1] < live.CENTRE[1]


def test_opening_gathers_the_army_and_sends_it():
    m = trial.load_map()
    w = trial.place(m, trial.TARGET)
    for error in [(0, 0), (40, 80), (-60, 10), (70, -60)]:
        g = FakeGame(m, error=error)
        result = trial.run(g, m)
        assert result["trained"] >= 6, error
        assert g.m_elsewhere == 0                  # never M on something else
        assert g.m_on_barracks == 5 * result["trained"]
        assert g.rallies == result["trained"]
        # nearly the whole starting army was ordered, and ended at Warsaw
        # (the pretend units arrive at once, so the wave sweeps them all)
        at_target = sum(near(u, (w["x"], w["y"]), 12) for u in g.units)
        assert at_target >= 0.85 * len(g.units), (error, at_target)


def test_opening_does_nothing_without_the_game_screen():
    m = trial.load_map()
    g = FakeGame(m, showing=False)
    assert trial.run(g, m) == {"trained": 0, "gathered": 0, "sent": 0}
    assert g.inputs == 0
