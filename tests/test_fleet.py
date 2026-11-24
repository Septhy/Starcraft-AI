"""The fleet keys: only Scouts on them, found by their gold."""
import os

from PIL import Image

from bot import trial
from eyes import live
from tests.test_trial import StubIO

DATA = os.path.join(os.path.dirname(__file__), "data")


def panel(colour):
    s = Image.new("RGB", (1920, 1080))
    s.paste(Image.new("RGB", (540, 170), colour), trial.PANEL_ONE[:2])
    return s


def test_a_battlecruiser_is_never_taken_for_a_scout():
    st, io = trial.State(), StubIO()
    st.scout_one = trial._crop(panel((200, 160, 40)), trial.PANEL_ONE)
    st.ship_one = trial._crop(panel((90, 90, 110)), trial.PANEL_ONE)
    io.shot = lambda label, keep=True: panel((200, 160, 40))
    assert trial.picked_are_scouts(io, st, 1)
    io.shot = lambda label, keep=True: panel((90, 90, 110))
    assert not trial.picked_are_scouts(io, st, 1)
    # between the two, but nearer the Battlecruiser: not a Scout
    io.shot = lambda label, keep=True: panel((120, 110, 90))
    assert not trial.picked_are_scouts(io, st, 1)


def test_the_scout_learnt_is_far_from_every_battlecruiser():
    m = trial.load_map()
    air = m["slots"][trial.SLOT]["air"]
    scouts = [a for a in air if a["type"] == "Scout"]
    ships = [a for a in air if a["type"] == "Battlecruiser"]
    far, scout = max(trial._apart(scouts, ships), key=lambda d: d[0])
    assert far > 20 * 32                # no Battlecruiser on that screen


def test_new_scouts_are_found_by_their_gold():
    s = Image.new("RGB", (1920, 1080), (40, 50, 30))
    s.paste(Image.open(os.path.join(DATA, "scouts_gold.png")), (940, 80))
    found = trial.gold_on_screen(s, 1070, 180, 300)
    assert len(found) >= 3
    assert all(940 <= x <= 1200 and 80 <= y <= 280 for x, y in found)
    # the grass, the kills list and the buttons over the minimap are not
    assert trial.gold_on_screen(Image.new("RGB", (1920, 1080), (40, 50, 30)),
                                960, 400, 2000) == []


def test_a_scout_is_clicked_on_its_gold_and_checked(monkeypatch):
    s = Image.new("RGB", (1920, 1080), (40, 50, 30))
    s.paste(Image.open(os.path.join(DATA, "scouts_gold.png")), (940, 80))
    st, io = trial.State(), StubIO()
    io.shot = lambda label, keep=True: s
    io.card = lambda: None
    monkeypatch.setattr(trial, "look_at", lambda io_, x, y, wait=0: (0, 0))
    monkeypatch.setattr(trial.live, "on_screen", lambda x, y, cam: (1070, 180))
    monkeypatch.setattr(trial.live, "units_selected", lambda card: True)
    answers = iter([False, True])       # the first gold is a tank's stripe
    monkeypatch.setattr(trial, "picked_are_scouts",
                        lambda io_, st_, n: next(answers))
    p = trial.click_scout(io, st, 0, 0)
    first, second = io.clicks[0][:2], io.clicks[1][:2]
    assert p == second
    gold = trial.gold_on_screen(s, 1070, 180, trial.SCOUT_LOOK * 32 * live.ZOOM)
    assert [first, second] == [tuple(int(v) for v in g) for g in gold[:2]]


def test_the_fleet_waits_north_east_of_smolensk():
    c, r = trial.fleet_spot()
    assert (round(c / 32), round(r / 32)) == (181, 65)
