import os

from PIL import Image

from bot import trial
from eyes import live

DATA = os.path.join(os.path.dirname(__file__), "data")


def screen(card):
    """A 1920 x 1080 screen with a real minimap and command card pasted in."""
    s = Image.new("RGB", (1920, 1080))
    s.paste(Image.open(os.path.join(DATA, "live_minimap.png")), (0, 780))
    s.paste(Image.open(os.path.join(DATA, card)), (1560, 760))
    return s


class FakeGame:
    """Pretends to be the game: a click within reach of a barracks'
    true position on screen selects it."""

    def __init__(self, mapdata, error=(40, 80), showing=True):
        self.barracks = trial.barracks_of(mapdata)
        self.error, self.showing = error, showing
        self.camera, self.selected = None, False
        self.actions, self.keys_on_barracks, self.keys_elsewhere = [], 0, 0
        self.slept = 0.0

    def click(self, x, y, button="left"):
        self.actions.append(("click", x, y))
        m = live.MINIMAP
        if m["left"] <= x < m["left"] + m["width"] and y >= m["top"]:
            self.camera = live.camera_after_click(x, y)
            return
        self.selected = False
        for b in self.barracks:
            px, py = live.on_screen(b["x"], b["y"], self.camera)
            px, py = px + self.error[0], py + self.error[1]
            if abs(x - px) < 130 and abs(y - py) < 95:
                self.selected = True

    def drag(self, x0, y0, x1, y1):
        assert 0 <= x0 < x1 <= 1920 and 40 <= y0 < y1 <= 760
        self.actions.append(("drag", x0, y0, x1, y1))
        self.selected = False

    def key(self, name):
        self.actions.append(("key", name))
        if name == "m":
            if self.selected:
                self.keys_on_barracks += 1
            else:
                self.keys_elsewhere += 1

    def sleep(self, s):
        self.slept += s

    def shot(self, label):
        if not self.showing:
            return Image.new("RGB", (1920, 1080))
        return screen("card_barracks.png" if self.selected else "card_units.png")

    def log(self, text, quiet=False):
        self.actions.append(("log", text))


def test_reads_the_real_pictures():
    assert live.minimap_showing(screen("card_units.png"))
    assert not live.minimap_showing(Image.new("RGB", (1920, 1080)))
    assert live.barracks_selected(screen("card_barracks.png"))
    assert not live.barracks_selected(screen("card_units.png"))


def test_map_data():
    m = trial.load_map()
    assert len(trial.barracks_of(m)) == 8
    w = trial.place(m, trial.TARGET)
    x, y = live.minimap_point(w["x"], w["y"])
    assert 13 < x < 302 and 817 < y < 1033


def test_camera_stays_on_the_map():
    cam = live.camera_after_click(*live.minimap_point(6650, 100))
    assert cam[1] == 1080 / live.ZOOM / 2          # held at the top edge
    assert live.on_screen(6650, 100, cam)[1] < live.CENTRE[1]


def test_trial_trains_only_on_barracks_and_sends_groups():
    m = trial.load_map()
    for error in [(0, 0), (40, 80), (-60, 10), (0, 140)]:
        g = FakeGame(m, error=error)
        result = trial.run(g, m)
        assert result["trained"] >= 6, error       # most barracks found
        assert g.keys_elsewhere == 0               # never M on something else
        assert g.keys_on_barracks == 5 * result["trained"]
        assert result["sent"] == result["trained"]
        tx, ty = live.minimap_point(*[trial.place(m, trial.TARGET)[k]
                                      for k in ("x", "y")])
        i = [k for k, a in enumerate(g.actions) if a == ("key", "a")]
        assert len(i) == result["sent"]
        assert all(g.actions[k + 1] == ("click", tx, ty) for k in i)


def test_trial_does_nothing_without_the_game_screen():
    m = trial.load_map()
    g = FakeGame(m, showing=False)
    assert trial.run(g, m) == {"trained": 0, "sent": 0}
    assert not [a for a in g.actions if a[0] in ("click", "key", "drag")]
