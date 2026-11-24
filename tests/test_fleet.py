"""The fleet keys: only Scouts on them, found by their gold."""
import os

from PIL import Image

from bot import trial
from eyes import live
from tests.test_trial import StubIO

DATA = os.path.join(os.path.dirname(__file__), "data")


def panel(name):
    s = Image.new("RGB", (1920, 1080))
    s.paste(Image.open(os.path.join(DATA, name)).convert("RGB"), (600, 880))
    return s


def test_the_pictures_of_a_few_units_are_found_where_the_game_puts_them():
    # two stand one above the other; three are two and one; seven are
    # four and three
    assert live.frame_box(1, 2)[:2] == (live.SLOT_ORIGIN[0],
                                        live.SLOT_ORIGIN[1] + live.SLOT_STEP[1])
    assert live.frame_box(2, 3)[:2] == (live.SLOT_ORIGIN[0],
                                        live.SLOT_ORIGIN[1] + live.SLOT_STEP[1])
    assert live.frame_box(4, 7)[:2] == (live.SLOT_ORIGIN[0],
                                        live.SLOT_ORIGIN[1] + live.SLOT_STEP[1])
    assert live.frame_box(6, 12)[:2] == (live.SLOT_ORIGIN[0],
                                         live.SLOT_ORIGIN[1] + live.SLOT_STEP[1])


def test_new_scouts_are_taken_and_anything_else_refused():
    """Trials 24 and 25: real Scouts were refused (the check looked at
    the wrong places, and compared colours, which change with health)."""
    st, io = trial.State(), StubIO()
    learnt = panel("panel_scouts2.png")
    st.scout_frame = trial._crop(learnt, trial._frame_box(0, 2))
    for name, n, ok in [("panel_scouts2.png", 2, True),
                        ("panel_scouts3.png", 3, True),
                        ("panel_mixed4.png", 4, False),     # with a tank
                        ("panel_marines7.png", 7, False)]:
        io.shot = lambda label, keep=True, name=name: panel(name)
        assert trial.picked_are_scouts(io, st, n) == ok, name


def test_one_unit_nearer_the_battlecruiser_is_refused():
    st, io = trial.State(), StubIO()
    import numpy as np
    scout = np.zeros((170, 540, 3), dtype=int)
    scout[20:120, 20:120] = (40, 220, 40)
    ship = np.zeros((170, 540, 3), dtype=int)
    ship[20:150, 20:200] = (40, 220, 40)
    st.scout_one, st.ship_one = scout, ship

    def shows(a):
        s = Image.new("RGB", (1920, 1080))
        s.paste(Image.fromarray(a.astype("uint8")), trial.PANEL_ONE[:2])
        return s
    damaged = scout.copy()
    damaged[20:120, 20:120] = (220, 200, 30)        # yellow: hurt, same shape
    io.shot = lambda label, keep=True: shows(damaged)
    assert trial.picked_are_scouts(io, st, 1)
    io.shot = lambda label, keep=True: shows(ship)
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


def test_blood_on_the_ground_is_not_counted_as_enemy():
    """Trials 24, 25: trails of blood counted as dozens of enemy."""
    for name, most in [("blood_trial24.jpg", 4), ("blood_trial25.jpg", 8)]:
        s = Image.new("RGB", (1920, 1080))
        s.paste(Image.open(os.path.join(DATA, name)).convert("RGB"), (0, 40))
        assert trial.enemy_on_screen(s, 960, 400, 2000) <= most, name
    # a real red unit with grey metal round it still counts
    s = Image.new("RGB", (1920, 1080), (40, 60, 30))
    s.paste((150, 150, 150), (900, 380, 960, 440))
    s.paste((230, 20, 20), (915, 395, 945, 425))
    assert trial.enemy_on_screen(s, 930, 410, 200) >= 1


def test_a_building_in_the_air_shows_move_and_one_on_the_ground_lift_off():
    for name, flying in [("card_lifted.png", True), ("card_grounded.png", False)]:
        s = Image.new("RGB", (1920, 1080))
        s.paste(Image.open(os.path.join(DATA, name)), (1560, 760))
        assert live.units_selected(s) == flying, name


def test_a_building_that_does_not_lift_is_not_sent_and_is_tried_again(monkeypatch):
    m = trial.load_map()
    st, io = trial.State(), StubIO()
    grounded = Image.new("RGB", (1920, 1080))
    grounded.paste(Image.open(os.path.join(DATA, "card_grounded.png")), (1560, 760))
    io.card = lambda: grounded
    io.shot = lambda label, keep=True: grounded
    monkeypatch.setattr(trial, "look_at", lambda io_, x, y, wait=0: (4000, 1600))
    monkeypatch.setattr(trial.live, "on_screen", lambda x, y, cam: (900, 400))
    assert not trial.fly_building(io, m, st, "Factory", (165, 49), "Krakow 200")
    assert (*trial.LIFT_BUTTON, "left") in io.clicks
    assert not any(c[2] == "right" for c in io.clicks)   # not sent anywhere
    assert st.lift_fails[(165, 49)] == 1
    # in the air: sent to the city
    lifted = Image.new("RGB", (1920, 1080))
    lifted.paste(Image.open(os.path.join(DATA, "card_lifted.png")), (1560, 760))
    io.clicks.clear()
    io.card = lambda: lifted if (*trial.LIFT_BUTTON, "left") in io.clicks \
        else grounded
    assert trial.fly_building(io, m, st, "Factory", (165, 49), "Krakow 200")
    assert sum(1 for c in io.clicks if c[2] == "right") == 2


def test_with_no_troops_forward_the_fleet_goes_back_to_its_spot():
    m = trial.load_map()
    st, io = trial.State(), StubIO()
    st.air_keys = ["9"]
    st.battle = trial.Battle("Berlin 1000", 0)
    st.battle.front = None
    trial.fight(io, None, m, st, None)
    park = live.minimap_point(*trial.fleet_spot())
    assert io.keys == ["9"] and (*park, "right") in io.clicks
    assert st.air_home


def test_troops_on_another_front_do_not_count_for_the_next_hit():
    st, io = trial.State(), StubIO()
    st.battle = trial.Battle("Berlin 1000", 0)
    st.planned_target = "Romania 300"
    assert not trial.same_front(st, st.battle, io, 0)
    st.planned_target = "Berlin 1000"
    assert trial.same_front(st, st.battle, io, 0)
