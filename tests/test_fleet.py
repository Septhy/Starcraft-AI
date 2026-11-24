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
    assert not trial.fly_building(io, m, st, "Factory", (165, 49), "Warsaw 200")
    assert (*trial.LIFT_BUTTON, "left") in io.clicks
    assert not any(c[2] == "right" for c in io.clicks)   # not sent anywhere
    assert st.lift_fails[(165, 49)] == 1
    # in the air: sent to the city
    lifted = Image.new("RGB", (1920, 1080))
    lifted.paste(Image.open(os.path.join(DATA, "card_lifted.png")), (1560, 760))
    io.clicks.clear()
    io.card = lambda: lifted if (*trial.LIFT_BUTTON, "left") in io.clicks \
        else grounded
    assert trial.fly_building(io, m, st, "Factory", (165, 49), "Warsaw 200")
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


def test_scouts_are_taken_out_of_a_box_before_it_is_ordered(monkeypatch):
    """Trial 26: boxes at the mass took the fleet into the hits."""
    st, io = trial.State(), StubIO()
    st.scout_frame = trial._crop(panel("panel_scouts2.png"),
                                 trial._frame_box(0, 2))
    shots = iter([panel("panel_mixed4.png"), panel("panel_marines7.png")])
    counts = iter([4, 2])
    io.shot = lambda label, keep=True: next(shots)
    monkeypatch.setattr(trial.live, "selected_count", lambda pic: next(counts))
    assert trial.drop_scouts(io, st) == 2
    x0, y0, x1, y1 = trial._frame_box(1, 4)          # the second Scout of four
    assert io.clicks[0] == ((x0 + x1) // 2, (y0 + y1) // 2, "shift")
    # all Scouts: nothing left for the ground
    io2 = StubIO()
    io2.shot = lambda label, keep=True: panel("panel_scouts3.png")
    monkeypatch.setattr(trial.live, "selected_count", lambda pic: 3)
    assert trial.drop_scouts(io2, st) == 0


def test_the_scouts_for_the_middle_east_are_kept_in_their_box(monkeypatch):
    """Trial 27: the box round the two scouting Scouts was emptied of
    Scouts as if it were for the ground; no scout went."""
    m = trial.load_map()
    st, io = trial.State(), StubIO()
    st.scout_frame = trial._crop(panel("panel_scouts2.png"),
                                 trial._frame_box(0, 2))
    io.shot = lambda label, keep=True: panel("panel_scouts2.png")
    io.drag = lambda *box: None
    io.card = lambda: None
    monkeypatch.setattr(trial.live, "units_selected", lambda card: True)
    monkeypatch.setattr(trial.live, "selected_count", lambda pic: 2)
    assert trial.send_scout(io, m, st)
    me = live.minimap_point(*trial.MIDDLE_EAST)
    assert (*me, "right") in io.clicks
    assert not any(c[2] == "shift" for c in io.clicks)   # none taken out
    # a ground box over the same Scouts is emptied
    assert not trial.box_and_check(io, (100, 100, 300, 300), st)


def test_a_balkans_hit_clears_romania_then_goes_on_toward_serbia():
    m = trial.load_map()
    st, io = trial.State(), StubIO()
    trial.send_at(io, m, st, "Romania 300")
    beyond = live.minimap_point(*trial.BALKS_POINT)
    assert io.keys == ["a", "a"]
    assert io.clicks[-1] == (*beyond, "shift")      # queued after Romania
    io2 = StubIO()
    trial.send_at(io2, m, st, "Berlin 1000")
    assert io2.keys == ["a"]


def test_east_is_always_berlin_and_the_balkans_always_romania():
    st = trial.State()
    for name in ("Warsaw 200", "Krakow 200", "Konigsberg 200", "Berlin 1000"):
        assert trial.road_start(st, name) == "Berlin 1000"
    for name in ("Factory 7", "Hungary 200", "Romania 300"):
        assert trial.road_start(st, name) == "Romania 300"


def test_the_keys_version_keys_the_mass_left_to_right_and_moves_it_aside(monkeypatch):
    """The repository owner's way: a dozen at a time from the left of
    the mass onto the next key, each moved aside into a line."""
    from tests.test_trial import StubWatch, blob
    m = trial.load_map()
    st, io = trial.State(), StubIO()
    io.shot = lambda label, keep=True: None
    monkeypatch.setattr(trial, "look_at", lambda io_, x, y, wait=0: (x, y))
    seeds = []
    monkeypatch.setattr(trial, "select_full",
                        lambda io_, st_, seed, pool, cam: seeds.append(seed)
                        or ([seed], 12))
    watch = StubWatch(blob(trial.MASS, 9), set())
    for _ in range(9):
        io.t += trial.KEY_EVERY
        trial.key_step(io, watch, m, st, "Berlin 1000")
    assert [k for k, _ in st.keyed] == list("1234567")   # then full
    assert [c for h, c in io.combos] == list("1234567")
    # from the left: each seed is the leftmost of what was left
    assert seeds[0][0] == min(c for c, r in blob(trial.MASS, 9))
    # moved aside, each to its own place in a line
    spots = {c[:2] for c in io.clicks if c[2] == "right"}
    assert len(spots) == 7


def test_the_keys_version_hit_boxes_the_back_then_the_keys_then_the_rest(monkeypatch):
    m = trial.load_map()
    monkeypatch.setattr(trial, "HIT_STYLE", "keys")
    st, io = trial.State(), StubIO()
    io.shot = lambda label, keep=True: None
    st.keyed = [(k, (trial.MASS[0] + 200 * i, trial.MASS[1]))
                for i, k in enumerate("1234567")]
    st.mass_keyed = (io.t - 20, list("1234567"), "Berlin 1000")
    calls = []

    def sweep(*a, **k):
        calls.append(("sweep", k.get("max_boxes")))
        return (3, 60)

    def attack(io_, mapdata, st_, target, keys):
        calls.append(("keys", tuple(keys)))
        return len(keys)
    monkeypatch.setattr(trial, "sweep_mass", sweep)
    monkeypatch.setattr(trial, "keyed_attack", attack)
    monkeypatch.setattr(trial, "push_front", lambda *a, **k: 1 / 0)
    from tests.test_trial import StubWatch
    trial.hit(io, StubWatch(set(), set()), m, st, "Berlin 1000", use_keys=False)
    assert calls[0] == ("sweep", trial.BACK_BOXES)   # the back first
    assert calls[1] == ("keys", tuple("1234567"))    # then every key
    assert calls[2][0] == "sweep" and calls[2][1] is None   # then the rest
    assert st.keyed == [] and st.mass_keyed is None


def test_after_a_hit_new_troops_go_straight_to_it_in_the_keys_version(monkeypatch):
    st, io = trial.State(), StubIO()
    st.battle = trial.Battle("Berlin 1000", io.t - 10)
    assert trial.reinforce_target(io, st) is None    # the usual version
    monkeypatch.setattr(trial, "HIT_STYLE", "keys")
    assert trial.reinforce_target(io, st) == "Berlin 1000"
    io.t += trial.REINFORCE_FOR
    assert trial.reinforce_target(io, st) is None    # a minute on: to the mass


def test_the_mass_is_spread_out_between_rounds_of_marines(monkeypatch):
    from tests.test_trial import StubWatch, blob
    m = trial.load_map()
    monkeypatch.setattr(trial, "HIT_STYLE", "keys")
    st, io = trial.State(), StubIO()
    io.shot = lambda label, keep=True: None
    monkeypatch.setattr(trial, "look_at", lambda io_, x, y, wait=0: (x, y))
    monkeypatch.setattr(trial, "select_full",
                        lambda io_, st_, seed, pool, cam: ([seed], 12))
    watch = StubWatch(blob(trial.MASS, 8), set())
    # the keys version spreads as it keys, not here
    assert trial.spread_at_mass(io, watch, m, st) == 0
    # the usual version spreads it: 8 tiles apart, 24 tiles across
    monkeypatch.setattr(trial, "HIT_STYLE", "boxes")
    io2 = StubIO()
    io2.shot = lambda label, keep=True: None
    st2 = trial.State()
    assert trial.spread_at_mass(io2, watch, m, st2) == trial.SPREAD_BOXES
    xs = sorted({dx for dx, dy in trial.SPREAD_WIDE})
    assert xs == [-12, -4, 4, 12] and max(xs) - min(xs) == 24
    # all of it still counts as at the mass
    for dx, dy in trial.SPREAD_WIDE:
        p = live.to_drawn(trial.MASS[0] + dx * 32, trial.MASS[1] + dy * 32)
        assert trial.at_mass({(int(p[0]), int(p[1]))})
    # not while a hit is announced
    from bot import team
    st2.team = team.Team(lambda t: None, lambda t: None)
    st2.team.announced = ("east", 999)
    assert trial.spread_at_mass(io2, watch, m, st2) == 0


def test_rel_version_lines_up_by_where_the_mass_is_from_the_target():
    """The repository owner: the mass top right of the target, a line on
    its left; bottom right, on its right; level with it, both sides."""
    mass = trial.MASS
    t = 32
    top_right = (mass[0] - 60 * t, mass[1] + 13 * t)     # like Berlin
    bottom_right = (mass[0] - 40 * t, mass[1] - 30 * t)
    level = (mass[0] - 42 * t, mass[1] + 4 * t)          # like Konigsberg
    assert trial.rel_side(mass, top_right) == "left"
    assert trial.rel_side(mass, bottom_right) == "right"
    assert trial.rel_side(mass, level) == "both"
    left = [trial.rel_spot(k, 7, mass, top_right) for k in range(7)]
    assert all(x == mass[0] - trial.REL_SIDE * t for x, y in left)
    assert len({y for x, y in left}) == 7                 # one up-and-down line
    right = [trial.rel_spot(k, 7, mass, bottom_right) for k in range(7)]
    assert all(x == mass[0] + trial.REL_SIDE * t for x, y in right)
    both = [trial.rel_spot(k, 7, mass, level) for k in range(7)]
    lefts = [p for p in both if p[0] < mass[0]]
    rights = [p for p in both if p[0] > mass[0]]
    assert len(lefts) == 4 and len(rights) == 3          # as equal as seven goes
    assert len({p for p in both}) == 7


def test_rel_version_keys_the_mass_into_its_side_line(monkeypatch):
    from tests.test_trial import StubWatch, blob
    m = trial.load_map()
    monkeypatch.setattr(trial, "HIT_STYLE", "rel")
    st, io = trial.State(), StubIO()
    io.shot = lambda label, keep=True: None
    monkeypatch.setattr(trial, "look_at", lambda io_, x, y, wait=0: (x, y))
    monkeypatch.setattr(trial, "select_full",
                        lambda io_, st_, seed, pool, cam: ([seed], 12))
    watch = StubWatch(blob(trial.MASS, 9), set())
    for _ in range(3):
        io.t += trial.KEY_EVERY
        trial.key_step(io, watch, m, st, "Berlin 1000")
    # Berlin: the mass is to its top right, so the line is on the left
    assert all(spot[0] < trial.MASS[0] for _, spot in st.keyed)
    assert trial.keys_style()
