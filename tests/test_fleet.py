"""The fleet keys: only Scouts on them, found by their gold."""
import pytest
import os

from PIL import Image

from bot import trial
from eyes import live
from tests.test_trial import StubIO, blob
import math

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
    watch = StubWatch(blob(trial.MASS, 16), set())
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


def test_each_barracks_rallies_to_its_own_spot_by_the_mass():
    """The repository owner: each barracks its own rally point, within
    an area 16 tiles across round the massing place."""
    m = trial.load_map()
    spots = [trial.rally_spot(m, b) for b in trial.barracks_of(m)]
    assert len(set(spots)) == len(spots)            # all different
    for x, y in spots:
        assert abs(x - trial.MASS[0]) <= 8 * 32 and abs(y - trial.MASS[1]) <= 8 * 32
        p = live.to_drawn(x, y)
        assert trial.at_mass({(int(p[0]), int(p[1]))})   # still the mass
    # and training clicks each barracks' own spot
    io = StubIO()
    io.shot = lambda label, keep=True: None
    st = trial.State()
    trial_select = trial.select_barracks
    try:
        trial.select_barracks = lambda io_, b: True
        trial.train_everywhere(io, m, st, check_supply=False)
    finally:
        trial.select_barracks = trial_select
    rallies = {c[:2] for c in io.clicks if c[2] == "right"}
    assert len(rallies) == len(trial.barracks_of(m))


def _apart_tiles(spots):
    return min(max(abs(a[0] - b[0]), abs(a[1] - b[1])) / 32
               for i, a in enumerate(spots) for b in spots[i + 1:])


def test_rally_spots_and_spawn_spots_are_at_least_8_tiles_apart():
    """The repository owner: each barracks' rally spot, and each group
    brought in, its own spot at least 8 tiles from the others."""
    m = trial.load_map()
    rallies = [trial.rally_spot(m, b) for b in trial.barracks_of(m)]
    assert _apart_tiles(rallies) >= 8
    st = trial.State()
    spawns = [trial.spawn_spot(st) for _ in range(len(trial.SPREAD_WIDE))]
    assert len(set(spawns)) == len(spawns) and _apart_tiles(spawns) >= 8
    for x, y in spawns:                              # all still the mass
        p = live.to_drawn(x, y)
        assert trial.at_mass({(int(p[0]), int(p[1]))})


def test_groups_brought_in_go_each_to_its_own_spot():
    m = trial.load_map()
    st, io = trial.State(), StubIO()
    far = (240 * 32, 50 * 32)                        # Siberia
    trial.to_mass(io, m, far, st)
    trial.to_mass(io, m, far, st)
    clicks = [c[:2] for c in io.clicks]
    assert len(set(clicks)) == 2                     # two different spots


def test_the_fleet_is_not_ordered_again_while_the_army_stands_still(monkeypatch):
    from tests.test_trial import StubWatch, blob
    m = trial.load_map()
    looks = []
    monkeypatch.setattr(trial, "enemy_near_fleet",
                        lambda io_, spot: looks.append(spot) or (0, None))
    w = trial.place(m, "Warsaw 200")
    front = (w["x"], w["y"])
    st, io = trial.State(), StubIO()
    st.fleet = [{"key": "9", "scouts": 6, "ha": None}]
    st.air_keys = ["9"]
    st.battle = trial.Battle("Berlin 1000", io.t - 100)
    st.battle.front = front
    watch = StubWatch(blob(front), set())
    trial.steer_fleet(io, watch, m, st, None)
    assert io.keys.count("9") == 1 and len(looks) == 1
    io.t += trial.AIR_FOLLOW_EVERY                   # nothing has moved
    trial.steer_fleet(io, watch, m, st, None)
    assert io.keys.count("9") == 1 and len(looks) == 1   # no clicks at all
    moved = (front[0] - 6 * 32, front[1])            # the army moves on
    trial.steer_fleet(io, StubWatch(blob(moved), set()), m, st, None)
    assert io.keys.count("9") == 2


def test_the_fleet_goes_once_most_of_the_hit_is_sent(monkeypatch):
    m = trial.load_map()
    st, io = trial.State(), StubIO()
    st.air_keys = ["9"]
    io.shot = lambda label, keep=True: None
    calls = []
    monkeypatch.setattr(trial, "sweep_mass",
                        lambda *a, **k: calls.append(("sweep", k.get("steer"))) or (0, 0))
    monkeypatch.setattr(trial, "send_fleet_with_hit",
                        lambda *a, **k: calls.append(("fleet",)) or 1)
    monkeypatch.setattr(trial, "push_front", lambda *a, **k: 1 / 0)
    trial.hit(io, None, m, st, "Berlin 1000", use_keys=False)
    assert calls[-1] == ("fleet",)                   # after the boxes
    assert all(c[1] is False for c in calls if c[0] == "sweep")   # no steering


def test_back_first_version_sends_seven_groups_from_the_back_before_the_keys(monkeypatch):
    m = trial.load_map()
    monkeypatch.setattr(trial, "HIT_STYLE", "back7")
    st, io = trial.State(), StubIO()
    io.shot = lambda label, keep=True: None
    st.keyed = [(k, (trial.MASS[0] + 200 * i, trial.MASS[1]))
                for i, k in enumerate("1234567")]
    st.mass_keyed = (io.t - 20, list("1234567"), "Berlin 1000")
    calls = []
    monkeypatch.setattr(trial, "sweep_mass", lambda *a, **k: calls.append(
        ("sweep", k.get("max_boxes"), bool(k.get("front_first")))) or (7, 60))
    monkeypatch.setattr(trial, "keyed_attack", lambda io_, m_, st_, t, keys:
                        calls.append(("keys",)) or len(keys))
    from tests.test_trial import StubWatch
    trial.hit(io, StubWatch(set(), set()), m, st, "Berlin 1000", use_keys=False)
    assert calls[0] == ("sweep", trial.BACK_FORMATIONS, False)   # the back first
    assert calls[1] == ("keys",)
    assert trial.keys_style()


def test_full_fleet_keys_are_counted_again_and_lost_scouts_make_room(monkeypatch):
    """Trial 33: "every fleet key is full" for half the game, its Scouts
    long dead, and the factories' new Scouts never went on a key."""
    st, io = trial.State(), StubIO()
    st.fleet = [{"key": k, "scouts": trial.FLEET_SIZE, "ha": (0, 0)}
                for k in "9087"]
    counts = {"9": 12, "0": 3, "8": 12, "7": 12}    # key 0: 2 Scouts left
    io.shot = lambda label, keep=True: label
    pressed = []
    io.key = lambda k: pressed.append(k)
    monkeypatch.setattr(trial.live, "selected_count",
                        lambda pic: counts[pressed[-1]] if pic == "fleet-count" else 2)
    monkeypatch.setattr(trial, "picked_are_scouts", lambda io_, st_, n: True)
    monkeypatch.setattr(trial, "attack_move", lambda *a: None)
    n = trial.add_selected_scouts(io, st, lambda: 2)
    assert n == 2
    assert st.fleet[1]["scouts"] == 2 + 2 and st.last_added_key == "0"


def test_orders_to_the_fleet_are_counted_for_the_air_report():
    """Plan step 1: every order given through a fleet key is counted:
    a move (right-click, or M then a click), an attack (A then a click,
    and each queued stop), a Hold (H)."""
    st, raw = trial.State(), StubIO()
    st.air_keys = ["9", "0"]
    io = trial.AirCounting(raw, st)
    io.key("9"); io.click(5, 5, button="right")         # a move
    io.key("a"); io.click(6, 6)                         # an attack
    io.key("a"); io.click_with("shift", 7, 7)           # a queued stop
    io.key("h")                                         # Hold
    io.key("1"); io.click(8, 8, button="right")         # a ground key: not air
    io.key("0"); io.click(9, 9)                         # a plain click: a pick
    io.click(9, 9, button="right")                      # not counted
    a = st.air
    assert a.orders == {"move": 1, "attack": 2, "hold": 1}
    trial.air_report(raw, st)
    text = [l for l in raw.lines if l.startswith("AIR REPORT")][0]
    assert "4 in" in text and "1 hold" in text


def test_the_air_brain_keeps_one_state_and_adds_up_its_time():
    st, io = trial.State(), StubIO()
    trial.air_stats(io, st).count(20, io.t)
    trial.set_air_state(io, st, "with the hit", "Berlin")
    io.t += 30
    trial.air_stats(io, st).count(15, io.t)
    trial.set_air_state(io, st, "parked", "back")
    a = st.air
    assert a.state == "parked" and a.spent["with the hit"] == 30
    assert a.fights == [[io.t - 30, 20, io.t, 15]]
    trial.air_report(io, st)
    text = [l for l in io.lines if l.startswith("AIR REPORT")][0]
    assert "Scouts 20 -> 15" in text and "lost about 5" in text


def test_leftover_scouts_go_on_the_next_key_or_to_the_fleet_never_the_mass(monkeypatch):
    """Plan step 2: three new Scouts, one space on key 9 and one on key 0,
    no key left to start: one goes on 9, the rest are picked again, one
    goes on 0, and the last flies to the fleet without a key."""
    st, io = trial.State(), StubIO()
    st.fleet = [{"key": "9", "scouts": trial.FLEET_SIZE - 1, "ha": (0, 0)},
                {"key": "0", "scouts": trial.FLEET_SIZE - 1, "ha": (0, 0)}]
    st.air_keys = ["9", "0"]
    monkeypatch.setattr(trial, "picked_are_scouts", lambda io_, st_, n: True)
    monkeypatch.setattr(trial, "trim_selection", lambda io_, keep, st_=None: keep)
    monkeypatch.setattr(trial, "attack_move", lambda *a: None)
    monkeypatch.setattr(trial, "recount_fleet", lambda *a, **k: False)
    monkeypatch.setattr(trial, "open_fleet_key", lambda io_, st_: False)
    sent = []
    monkeypatch.setattr(trial, "attack_move", lambda io_, x, y: sent.append((x, y)))
    picks = iter([3, 2, 1])
    assert trial.add_selected_scouts(io, st, lambda: next(picks)) == 3
    assert st.fleet[0]["scouts"] == st.fleet[1]["scouts"] == trial.FLEET_SIZE
    assert sent == [trial.fleet_spot()] * 3          # all three to the fleet
    assert any("without a key" in line for line in io.lines)


def test_a_key_without_the_moscow_gun_gets_it_at_the_upkeep(monkeypatch):
    m = trial.load_map()
    st, io = trial.State(), StubIO()
    st.fleet = [{"key": "9", "scouts": 5, "ha": trial.MOSCOW_HA, "ha_dead": True}]
    st.air_keys = ["9"]
    trial.air_stats(io, st)
    io.t += trial.AIR_UPKEEP + 1
    io.shot = lambda label, keep=True: label
    monkeypatch.setattr(trial.live, "selected_count", lambda pic: 5)
    monkeypatch.setattr(trial, "locate_fleet", lambda io_, st_: None)
    picked = []
    monkeypatch.setattr(trial, "pick_ha",
                        lambda io_, st_, x, y: picked.append((x, y)) or True)
    assert trial.air_upkeep(io, None, m, st)
    assert picked == [trial.MOSCOW_HA] and not st.fleet[0]["ha_dead"]
    assert ("shift", "9") in io.combos and "9" in st.ha_keys


def test_the_moscow_gun_is_tried_three_times_then_left(monkeypatch):
    st, io = trial.State(), StubIO()
    e = {"key": "0", "scouts": 3, "ha": trial.MOSCOW_HA, "ha_dead": True}
    st.fleet = [e]
    monkeypatch.setattr(trial, "pick_ha", lambda *a, **k: False)
    for _ in range(5):
        assert not trial.replace_ha(io, st, e)
    assert st.ha_tries["0"] == 3
    assert any("Scouts alone" in l for l in io.lines)


def test_a_keys_pictures_tell_its_scouts_from_its_artillery(monkeypatch):
    st = trial.State()
    st.scout_frame = "scout"
    monkeypatch.setattr(trial.live, "selected_count", lambda pic: 4)
    monkeypatch.setattr(trial, "_crop", lambda pic, box: box)
    looks = {trial._frame_box(i, 4): ("scout" if i else "tank") for i in range(4)}
    monkeypatch.setattr(trial, "alike",
                        lambda a, b, trim=None: 1.0 if looks[a] == b else 0.1)
    assert trial.read_key(st, "pic") == (4, 3, True)
    looks[trial._frame_box(0, 4)] = "scout"
    assert trial.read_key(st, "pic") == (4, 4, False)


class FightIO(StubIO):
    """The game screen as the dogfight sees it, scripted look by look."""
    def __init__(self, looks):
        super().__init__()
        self.looks = list(looks)
        self.shot = lambda label, keep=True: "pic"

    def sleep(self, s):
        self.t += s


def fight_setup(monkeypatch, looks, counts=None):
    st = trial.State()
    st.air_keys = ["9", "0"]
    st.fleet = [{"key": "9", "scouts": 10, "ha": (0, 0)},
                {"key": "0", "scouts": 10, "ha": (0, 0)}]
    io = FightIO(looks)
    monkeypatch.setattr(trial, "look_at", lambda io_, x, y, wait=0: (x, y))
    seq = iter(looks)
    monkeypatch.setattr(trial, "sense_fight", lambda pic, guess, skip=(): next(seq))
    monkeypatch.setattr(trial, "army_anchor", lambda w, pic, goal: None)
    c = iter(counts or [])
    monkeypatch.setattr(trial, "fleet_left",
                        lambda io_, st_: next(c, 20))
    monkeypatch.setattr(trial, "attack_move", lambda *a: None)
    # (asked of the game: by default it answers where the fleet was sent)
    monkeypatch.setattr(trial, "where_is_fleet",
                        lambda io_, st_, quiet=False: trial.fleet_spot())
    # (and the hit is still out there, unless a test says otherwise)
    monkeypatch.setattr(trial, "hit_gone", lambda w, pic, m, xy: False)
    return st, io


def test_the_dogfight_hops_round_the_enemy_with_holds_and_picked_targets(monkeypatch):
    """Plan step 3: once most of the hit is sent, only the air: short
    hops toward the edge of the enemy near the fleet, a Hold every third
    hop, a click on the enemy every ninth order; done when no enemy has
    been near for a while."""
    m = trial.load_map()
    cam = trial.centred(*trial.toward(trial.MASS, (4160, 2928), trial.AIR_LEAD))
    fleet = trial.live.CENTRE
    enemy = (fleet[0] + 9 * 72 // 2, fleet[1])          # about 4.5 tiles off
    looks = [(fleet, [enemy])] * 18 + [(fleet, [])] * (trial.QUIET_END + 1)
    st, io = fight_setup(monkeypatch, looks)
    n = trial.dogfight(io, None, m, st, "Warsaw 200")
    assert n >= 15
    rights = [c for c in io.clicks if c[2] == "right"]
    assert io.keys.count("h") >= 2 * 4                  # Holds, on both keys
    on_enemy = [c for c in rights if abs(c[0] - enemy[0]) < 3 and abs(c[1] - enemy[1]) < 3]
    assert on_enemy                                     # a target picked
    hops = [c for c in rights if c not in on_enemy]
    assert all(fleet[0] < c[0] < enemy[0] for c in hops)   # toward, not into
    assert st.air.state == "with the army"
    assert any("dogfight:" in l and "no enemy left" in l for l in io.lines)


def test_the_dogfight_steps_back_when_scouts_die_fast_and_goes_home_at_half(monkeypatch):
    m = trial.load_map()
    fleet = trial.live.CENTRE
    enemy = (fleet[0] + 200, fleet[1])
    looks = [(fleet, [enemy])] * 200
    st, io = fight_setup(monkeypatch, looks, counts=[20, 16, 9])
    trial.dogfight(io, None, m, st, "Warsaw 200")
    assert any("a step back" in l for l in io.lines)
    assert any("half the Scouts lost" in l for l in io.lines)
    assert st.air.state == "parked"


def test_the_dogfight_ends_when_the_fleet_is_out_of_sight(monkeypatch):
    m = trial.load_map()
    st, io = fight_setup(monkeypatch, [(None, [])] * 200)
    asked = []
    monkeypatch.setattr(trial, "where_is_fleet",
                        lambda io_, st_, quiet=False: asked.append(1))
    assert trial.dogfight(io, None, m, st, "Warsaw 200") == 0
    assert len(asked) == 1 + trial.FIND_TRIES   # at the start, then three looks
    assert io.t - 100 < 5                       # and over at once, not after 15 s
    assert any("out of sight" in l for l in io.lines)


def test_a_lone_gold_light_or_one_on_our_buildings_is_not_the_fleet(monkeypatch):
    """Trial 33 pictures: a walker's lights and our factories' lamps are
    gold too. A fleet is three or more gold patches together, off our
    buildings."""
    monkeypatch.setattr(trial, "enemy_mask", lambda pic: None)
    monkeypatch.setattr(trial, "patches", lambda m: [])
    one = [(500, 300)]
    many = [(500, 300), (540, 320), (520, 360)]
    monkeypatch.setattr(trial, "gold_on_screen", lambda pic, x, y, r: list(one))
    assert trial.sense_fight("pic", (500, 300))[0] is None
    monkeypatch.setattr(trial, "gold_on_screen", lambda pic, x, y, r: list(many))
    assert trial.sense_fight("pic", (500, 300))[0] is not None
    assert trial.sense_fight("pic", (500, 300), skip=[(520, 330, 150)])[0] is None


class TargetEars:
    def __init__(self, found):
        self.found, self.asked = found, 0

    def find_targets(self, picture):
        self.asked += 1
        return [dict(f) for f in self.found]


def test_scouts_shoot_battlecruisers_then_scvs_by_bunkers_then_bunkers():
    """The repository owner: the screen scanned; Battlecruisers first,
    then SCVs by bunkers, then bunkers, the nearest first; each attacked
    alone (A, click), never queued."""
    st, io = trial.State(), StubIO()
    st.air_keys = ["9"]
    cam = (4000, 2000)
    fleet = (900, 400)
    st.ears = TargetEars([{"kind": "bunker", "x": 1000, "y": 400},
                          {"kind": "scv", "x": 1050, "y": 420},
                          {"kind": "battlecruiser", "x": 1600, "y": 300},
                          {"kind": "battlecruiser", "x": 1300, "y": 300}])
    found = trial.scan_targets(io, st, "pic", fleet, cam)
    assert [f["kind"] for f in found] == ["battlecruiser", "battlecruiser",
                                          "scv", "bunker"]
    assert abs(trial.live.on_screen(*found[0]["xy"], cam)[0] - 1300) <= 1  # nearer first
    assert trial.attack_target(io, st, found[0], cam)
    assert io.keys == ["9", "a"] and len(io.clicks) == 1
    assert abs(io.clicks[0][0] - 1300) <= 1 and io.clicks[0][2] == "left"
    st.ears = TargetEars([])
    assert trial.scan_targets(io, st, "pic", fleet, cam) == []
    st.ears = None
    assert trial.scan_targets(io, st, "pic", fleet, cam) is None


def test_only_targets_in_an_axis_colour_are_shot():
    """Trial 37: the Scouts attacked one of Russia's own bunkers. A target
    is shot only if red, blue or yellow shows on it, more than brown."""
    from PIL import Image, ImageDraw
    pic = Image.new("RGB", (1920, 1080), (30, 50, 20))
    d = ImageDraw.Draw(pic)
    d.rectangle((990, 390, 1010, 410), fill=(240, 20, 20))    # a red bunker
    d.rectangle((1290, 290, 1310, 310), fill=(112, 48, 20))   # our brown one
    d.rectangle((590, 490, 610, 510), fill=(250, 245, 60))    # a yellow one
    st, io = trial.State(), StubIO()
    st.ears = TargetEars([{"kind": "bunker", "x": 1000, "y": 400},
                          {"kind": "bunker", "x": 1300, "y": 300},
                          {"kind": "bunker", "x": 600, "y": 500}])
    found = trial.scan_targets(io, st, pic, (900, 400), (4000, 2000))
    xs = sorted(round(trial.live.on_screen(*f["xy"], (4000, 2000))[0])
                for f in found)
    assert len(found) == 2 and abs(xs[0] - 600) <= 1 and abs(xs[1] - 1000) <= 1
    assert any("not in an Axis colour" in l for l in io.lines)


def test_in_the_dogfight_one_target_then_a_hop_back_then_the_next(monkeypatch):
    """A Battlecruiser and a bunker seen: the Battlecruiser is attacked,
    shot at for a while with no hops, then a hop back, then the bunker.
    None seen: only hops and Holds."""
    m = trial.load_map()
    fleet = trial.live.CENTRE
    enemy = (fleet[0] + 300, fleet[1])
    looks = [(fleet, [enemy])] * 40 + [(fleet, [])] * (trial.QUIET_END + 1)
    st, io = fight_setup(monkeypatch, looks)
    monkeypatch.setattr(trial, "look_at", lambda io_, x, y, wait=0: (4000, 2000))
    st.ears = TargetEars([{"kind": "battlecruiser", "x": 1200, "y": 300},
                          {"kind": "bunker", "x": 1250, "y": 500}])
    trial.dogfight(io, None, m, st, "Warsaw 200")
    focus = [l for l in io.lines if "focus fire" in l]
    assert focus[:2] == ["dogfight: focus fire on a battlecruiser",
                         "dogfight: focus fire on a bunker"]
    assert not any(c[2] == "shift" for c in io.clicks)      # never queued
    # between the two attacks (A, click on each key), a hop back: a
    # right-click on each key
    attacks = [i for i, c in enumerate(io.clicks) if c[2] == "left"]
    rights = [i for i, c in enumerate(io.clicks) if c[2] == "right"]
    first_end, second_start = attacks[1], attacks[2]
    assert any(first_end < i < second_start for i in rights)
    # none found: hops and Holds only
    st, io = fight_setup(monkeypatch, looks)
    st.ears = TargetEars([])
    trial.dogfight(io, None, m, st, "Warsaw 200")
    assert not any("focus fire" in l for l in io.lines)
    assert io.keys.count("h") >= 2 and "a" not in io.keys[:20]


class CoverWatch:
    """The minimap round the fleet: our pixels and the enemy's."""
    def __init__(self, ours, theirs):
        self.ours, self.theirs = ours, theirs

    def units(self, picture):
        return set(self.ours)

    def others(self, picture, slots):
        return set(self.theirs)


def blob_at(xy, n):
    c, r = trial.live.to_drawn(*xy)
    return {(int(c) + i % 5, int(r) + i // 5) for i in range(n)}


def test_cover_is_our_ground_under_the_scouts_against_the_enemy_there():
    xy = (4000, 2400)
    ours, theirs = blob_at(xy, 20), blob_at(xy, 10)
    assert trial.ground_cover(CoverWatch(ours, theirs), "pic", xy) == (16, 10)
    assert trial.covered((16, 10))
    assert not trial.covered((4, 2))           # too few of ours
    assert not trial.covered((8, 30))          # far fewer than theirs
    assert trial.covered(None)                 # cannot tell: carry on


def test_the_scouts_go_home_when_the_ground_under_them_is_too_thin(monkeypatch):
    """The repository owner: the Scouts need enough of our ground army
    under them; without it two counts in a row, they go home."""
    m = trial.load_map()
    fleet = trial.live.CENTRE
    enemy = (fleet[0] + 300, fleet[1])
    looks = [(fleet, [enemy])] * 200
    st, io = fight_setup(monkeypatch, looks)
    watch = CoverWatch(set(), blob_at((4000, 2400), 25))
    monkeypatch.setattr(trial, "ground_cover", lambda w, pic, xy: (2, 25))
    trial.dogfight(io, watch, m, st, "Warsaw 200")
    assert any("too little of our ground army under the Scouts" in l
               for l in io.lines)
    assert st.air.state == "parked"
    # with cover, it fights on
    st, io = fight_setup(monkeypatch, looks[:60] + [(fleet, [])] * 10)
    monkeypatch.setattr(trial, "ground_cover", lambda w, pic, xy: (30, 10))
    trial.dogfight(io, watch, m, st, "Warsaw 200")
    assert not any("too little" in l for l in io.lines)


def test_the_spread_never_boxes_the_same_marines_twice_in_a_row(monkeypatch):
    """Trial 34: six boxes in a row on the same spot. The ground round a
    box is left alone for the rest of the round."""
    from tests.test_trial import StubWatch, blob
    m = trial.load_map()
    st, io = trial.State(), StubIO()
    io.shot = lambda label, keep=True: None
    monkeypatch.setattr(trial, "look_at", lambda io_, x, y, wait=0: (x, y))
    seeds = []
    monkeypatch.setattr(trial, "select_full",
                        lambda io_, st_, seed, pool, cam: seeds.append(seed) or ([seed], 12))
    trial.spread_at_mass(io, StubWatch(blob(trial.MASS, 16), set()), m, st)
    assert all(max(abs(a[0] - b[0]), abs(a[1] - b[1])) > trial.SPREAD_GAP
               for i, a in enumerate(seeds) for b in seeds[:i])


def test_the_fleet_is_found_on_its_way_out_not_only_where_it_goes(monkeypatch):
    """Trial 34: the dogfight looked only where the fleet was going; it
    was still on its way, so every dogfight ended at once."""
    m = trial.load_map()
    looked = []
    there = (150 * 32, 90 * 32)             # where it really is
    enemy = (trial.live.CENTRE[0] + 200, trial.live.CENTRE[1])
    st, io = fight_setup(monkeypatch, [(None, [])] * 2 +
                         [(trial.live.CENTRE, [enemy])] * 6 +
                         [(trial.live.CENTRE, [])] * 200)
    monkeypatch.setattr(trial, "look_at",
                        lambda io_, x, y, wait=0: looked.append((x, y)) or (x, y))
    monkeypatch.setattr(trial, "where_is_fleet", lambda io_, st_, quiet=False: there)
    n = trial.dogfight(io, None, m, st, "Warsaw 200")
    assert n > 0 and not any("out of sight" in l for l in io.lines)
    # (after trial 39: no guessing; the game is asked, and the view goes
    # to where the fleet is)
    want = trial.centred(*there)
    assert all(abs(x - want[0]) < 1 and abs(y - want[1]) < 1 for x, y in looked[:3])


def test_no_marines_while_the_air_is_out_with_a_hit(monkeypatch):
    """The repository owner: after a hit, the barracks wait until the air
    is back or gone (at most AIR_OUT_MAX seconds after the hit)."""
    m = trial.load_map()
    st, io = trial.State(), StubIO()
    st.air_keys = ["9"]
    st.hit_sent = io.t
    trial.set_air_state(io, st, "with the hit", "Berlin")
    monkeypatch.setattr(trial, "select_barracks", lambda *a: pytest.fail("trained"))
    assert trial.train_everywhere(io, m, st, check_supply=False) == 0
    assert any("the air is still out with the hit" in l for l in io.lines)
    trial.set_air_state(io, st, "parked", "back")
    trained = []
    monkeypatch.setattr(trial, "select_barracks", lambda *a: trained.append(1) or False)
    trial.train_everywhere(io, m, st, check_supply=False)
    assert trained                                   # back: the barracks go on
    trial.set_air_state(io, st, "with the army", "over the army after the fight")
    trained.clear()
    trial.train_everywhere(io, m, st, check_supply=False)
    assert trained                                   # the fight is over: on
    trial.set_air_state(io, st, "fighting", "out again")
    io.t += trial.AIR_OUT_MAX + 1
    trained.clear()
    trial.train_everywhere(io, m, st, check_supply=False)
    assert trained                                   # a stalled hit: not forever


def test_a_missed_click_never_keys_the_scouts_as_the_artillery(monkeypatch):
    """Trial 35: the click by the Heavy Artillery missed, the Scouts
    selected before stayed selected, and Ctrl + 9 keyed them. Only a
    gun's buttons (no Move) count as picked; not picked, the keys start
    without it, and a new key's first Scouts make it with Ctrl (trial 36:
    Shift + 0 on a key not yet made did nothing)."""
    st, io = trial.State(), StubIO()
    io.shot = lambda label, keep=True: label
    boxes = []
    io.drag = lambda *b: boxes.append(b)
    monkeypatch.setattr(trial, "look_at", lambda io_, x, y, wait=0: (x, y))
    gun = [False]                                   # still the Scouts
    monkeypatch.setattr(trial.live, "gun_selected", lambda pic: gun[0])
    assert not trial.pick_ha(io, st, 5684, 2489)
    assert boxes                                    # small boxes dragged round it
    gun[0] = True                                   # no Move, Stop second
    assert trial.pick_ha(io, st, 5684, 2489)
    gun[0] = False
    assert not trial.key_moscow_ha(io, st)
    assert not any(c[0] == "ctrl" for c in io.combos)
    assert trial.open_fleet_key(io, st)
    e = st.fleet[0]
    assert e["ha_dead"] and e["new"] and st.air_keys == []   # nothing on it yet
    trial.add_to_key(io, st, e)
    assert io.combos[-1] == ("ctrl", "9") and st.air_keys == ["9"]
    trial.add_to_key(io, st, e)
    assert io.combos[-1] == ("shift", "9")

def test_a_hop_off_the_screen_goes_by_the_minimap_not_to_the_corner():
    """Trial 35: hop points off the screen were squeezed onto its edge,
    and the Scouts were sent to the corner (30, 730)."""
    st, io = trial.State(), StubIO()
    st.air_keys = ["9"]
    st.dogfight_cam = (4000, 2000)
    far = trial.live.on_screen(4000 - 40 * 32, 2000 + 20 * 32, st.dogfight_cam)
    trial.order_fleet(io, st, far)
    x, y, button = io.clicks[-1]
    assert button == "right" and (x, y) != (30, 730)
    m = trial.live.MINIMAP
    assert m["left"] <= x < m["left"] + m["width"] and y >= m["top"]


def test_before_a_hit_every_parked_scout_is_keyed_afresh(monkeypatch):
    """Trial 36: an unkeyed squadron sat at the parking spot, and the
    dogfight's camera jumped between it and the keyed one. Before a hit
    the parked Scouts are boxed a dozen at a time onto 9, 0, 8 (Ctrl),
    each keyed box stepping aside. Trial 37: a key holding the Moscow
    gun is pressed first and the box added to it (Shift + drag), so the
    gun stays on it and is never picked again."""
    st, io = trial.State(), StubIO()
    st.fleet = [{"key": "9", "scouts": 6, "ha": trial.MOSCOW_HA}]
    st.air_keys = ["9"]
    st.ha_keys = {"9", "0", "8"}
    trial.air_stats(io, st)                       # parked
    io.shot = lambda label, keep=True: label
    io.drag = lambda *box: pytest.fail("a plain box would drop the gun")
    shift_boxes = []
    io.drag_with = lambda held, *box: shift_boxes.append((held, io.keys[-1]))
    monkeypatch.setattr(trial, "look_at", lambda io_, x, y, wait=0: (x, y))
    bunches = iter([[(900, 400), (950, 420)], [(1200, 400)], []])
    monkeypatch.setattr(trial, "gold_on_screen", lambda pic, x, y, r: next(bunches))
    counts = iter([12, 5])                        # each with its gun
    monkeypatch.setattr(trial.live, "selected_count", lambda pic: next(counts))
    monkeypatch.setattr(trial, "scouts_picked",
                        lambda io_, st_, n, guns=0: (n, guns))
    monkeypatch.setattr(trial, "trim_selection", lambda io_, keep, st_=None: keep)
    monkeypatch.setattr(trial, "pick_ha", lambda *a: pytest.fail("picked again"))
    assert trial.regroup_fleet(io, st) == 15
    assert shift_boxes == [("shift", "9"), ("shift", "0")]
    assert [e["key"] for e in st.fleet] == ["9", "0"]
    assert [e["scouts"] for e in st.fleet] == [trial.FLEET_SIZE, 4]
    assert not any(e["ha_dead"] for e in st.fleet)
    assert ("ctrl", "9") in io.combos and ("ctrl", "0") in io.combos
    assert st.ha_keys == {"9", "0", "8"}         # 8 still has it: opened later
    assert st.air_keys == ["9", "0"]
    assert trial.open_fleet_key(io, st) and st.fleet[-1]["key"] == "8"
    assert not st.fleet[-1]["new"] and not st.fleet[-1]["ha_dead"]
    # not while the fleet is out
    trial.set_air_state(io, st, "with the army", "out")
    assert trial.regroup_fleet(io, st) == 0


def fake_panel(monkeypatch, kinds):
    """A bottom panel whose pictures are `kinds` ("scout", "gun",
    "other"); a Shift + click on a picture takes that unit out."""
    sel = list(kinds)
    monkeypatch.setattr(trial.live, "selected_count", lambda pic: len(sel))
    monkeypatch.setattr(trial, "frame_kinds",
                        lambda st_, pic, n: list(sel) if len(sel) >= 2 else None)
    monkeypatch.setattr(trial, "picked_are_scouts",
                        lambda io_, st_, n: all(k == "scout" for k in sel))

    def click_with(held, x, y):
        for i in range(len(sel)):
            x0, y0, x1, y1 = trial._frame_box(i, len(sel))
            if x0 <= x <= x1 and y0 <= y <= y1:
                del sel[i]
                return
    return sel, click_with


def test_trimming_never_takes_the_gun_out(monkeypatch):
    """Trial 37: the bot clicked the Heavy Artillery's picture to drop it."""
    st, io = trial.State(), StubIO()
    st.scout_frame = "learnt"
    sel, io.click_with = fake_panel(monkeypatch, ["scout"] * 5 + ["gun"])
    io.shot = lambda label, keep=True: label
    assert trial.trim_selection(io, 3, st) == 3
    assert sel == ["scout", "scout", "gun"]


def test_ground_units_picked_with_scouts_go_but_never_the_gun(monkeypatch):
    st, io = trial.State(), StubIO()
    st.scout_frame, st.ha_frame = "learnt", "learnt"
    sel, io.click_with = fake_panel(monkeypatch, ["gun", "scout", "other", "scout",
                                             "other"])
    io.shot = lambda label, keep=True: label
    assert trial.scouts_picked(io, st, 5) == (3, 1)
    assert sel == ["gun", "scout", "scout"]
    # before the gun's picture is learnt: nothing is taken out
    st.ha_frame = None
    sel, io.click_with = fake_panel(monkeypatch, ["scout", "other", "scout"])
    assert trial.scouts_picked(io, st, 3) is None and len(sel) == 3
    assert trial.scouts_picked(io, st, 3, guns=1) == (3, 1)   # a key's own gun


def test_the_gun_s_picture_is_learnt_from_a_pressed_key(monkeypatch):
    st, io = trial.State(), StubIO()
    st.scout_frame = "learnt"
    st.ha_keys = {"9"}
    e = {"key": "9", "scouts": 2, "ha_dead": False}
    monkeypatch.setattr(trial, "frame_kinds",
                        lambda st_, pic, n: ["other", "scout", "scout"])
    monkeypatch.setattr(trial, "_crop", lambda pic, box: ("crop", box))
    trial.learn_ha_frame(io, st, e, "pic", 3)
    assert st.ha_frame == ("crop", trial._frame_box(0, 3))


def test_a_key_that_holds_the_gun_is_never_given_it_again(monkeypatch):
    st, io = trial.State(), StubIO()
    st.ha_keys = {"9"}
    e = {"key": "9", "scouts": 4, "ha_dead": True}
    monkeypatch.setattr(trial, "pick_ha", lambda *a: pytest.fail("picked again"))
    assert not trial.replace_ha(io, st, e) and not e["ha_dead"]


def test_a_factory_s_new_tanks_are_seen_on_the_screen_and_sent(monkeypatch):
    """Trial 37: Factory 3 stands among Moscow's buildings, which the
    minimap reading leaves out: its tanks never left."""
    m = trial.load_map()
    st, io = trial.State(), StubIO()
    cam = (6500, 1400)
    monkeypatch.setattr(trial, "look_at", lambda io_, x, y, wait=0: cam)
    f = trial.place(m, "Factory 3")
    fx, fy = trial.live.on_screen(f["x"], f["y"], cam)
    monkeypatch.setattr(trial, "own_on_screen",
                        lambda pic: [(fx - 60, fy + 20), (fx + 40, fy + 50),
                                     (fx + 900, fy)])      # the last: too far
    io.shot = lambda label, keep=True: label
    boxes = []
    io.drag = lambda *box: boxes.append(box)
    io.card = lambda: "card"
    monkeypatch.setattr(trial.live, "units_selected", lambda card: True)
    monkeypatch.setattr(trial, "drop_scouts", lambda io_, st_: 4)
    sent = []
    monkeypatch.setattr(trial, "to_mass", lambda io_, mapdata, xy, st_: sent.append(xy))
    assert trial.fetch_factory_ground(io, m, st, "Factory 3") == 4
    x0, y0, x1, y1 = boxes[0]
    assert x0 <= fx - 60 and x1 >= fx + 40 and x1 < fx + 900
    assert sent == [(f["x"], f["y"])]


class ParkWatch:
    def __init__(self, ours=(), allies=(), axis=()):
        self.ours, self.allies, self.axis = set(ours), set(allies), set(axis)

    def units(self, picture):
        return set(self.ours)

    def others(self, picture, slots):
        return set(self.axis) if slots == trial.AXIS else set(self.allies)


def test_the_fleet_waits_by_a_beacon_with_friends_not_in_the_mass(monkeypatch):
    """Trial 37: the air sat in the way at the massing place; it waits by
    a nearby city beacon with brown or allied troops by it."""
    m = trial.load_map()
    st, io = trial.State(), StubIO()
    default = trial.fleet_spot()
    beacons = [p for p in m["places"] if trial.is_beacon(p["name"])]
    berlin = trial.place(m, trial.TARGETS[0])

    def ok(p):
        d = math.hypot(p["x"] - trial.MASS[0], p["y"] - trial.MASS[1]) / 32
        mass_front = math.hypot(trial.MASS[0] - berlin["x"],
                                trial.MASS[1] - berlin["y"]) / 32
        front = math.hypot(p["x"] - berlin["x"], p["y"] - berlin["y"]) / 32
        return trial.PARK_MIN <= d <= trial.PARK_MAX and \
            front >= mass_front - trial.PARK_FORWARD
    good = [p for p in beacons if ok(p)]
    assert good, "no beacon near the mass to test with"
    b = good[0]
    # no friends there: the fixed spot
    assert not trial.choose_park(io, ParkWatch(), m, st, "pic")
    assert trial.fleet_spot() == default
    # allied troops by a beacon: the fleet waits beside it
    io.t += trial.PARK_EVERY
    watch = ParkWatch(allies=blob((b["x"], b["y"]), 2))
    assert trial.choose_park(io, watch, m, st, "pic")
    assert trial.fleet_spot() == (b["x"] + trial.PARK_SIDE * 32, b["y"])
    # the Axis there: not that one
    io.t += trial.PARK_EVERY
    watch = ParkWatch(ours=blob((b["x"], b["y"]), 2),
                      axis=blob((b["x"], b["y"]), 1))
    assert trial.choose_park(io, watch, m, st, "pic")
    assert trial.fleet_spot() == default
    trial.State()                                 # a new game forgets it
    assert trial.fleet_spot() == default


# ------------------------------------------------ plan phase 1: where it is
from PIL import Image as _Image
import os as _os


def _data(name):
    return _Image.open(_os.path.join(_os.path.dirname(__file__), "data", name))


def test_scouts_and_the_artillery_are_told_by_their_small_pictures():
    """The owner's recording for phase 0: a key with six Scouts and the
    Heavy Artillery (second picture), one with four and it (third)."""
    seven, five = _data("fleet_key_7.jpg"), _data("fleet_key_5.jpg")
    assert trial.scout_pictures(seven) == (7, [0, 2, 3, 4, 5, 6])
    assert trial.scout_pictures(five) == (5, [0, 1, 3, 4])
    assert trial.live.frames_like(seven, 7, "artillery") == [1]
    assert trial.live.frames_like(five, 5, "artillery") == [2]


class FindIO(StubIO):
    """A fleet key shows its pictures; a click on a Scout's picture and
    Ctrl+C centre the view on the Scouts, a click on the artillery's on
    Moscow."""
    def __init__(self, keys):
        super().__init__()
        self.groups = keys              # key -> list of "scout"/"artillery"
        self.sel, self.one, self.centred_on = [], None, None
        self.combos = []
        self.shot = lambda label, keep=True: self

    def key(self, name):
        super().key(name)
        if name in self.groups:
            self.sel, self.one = list(self.groups[name]), None

    def sleep(self, s):
        self.t += s

    def click(self, x, y, button="left"):
        super().click(x, y, button)
        for i in range(len(self.sel)):
            x0, y0, x1, y1 = trial.live.frame_box(i, len(self.sel))
            if x0 <= x <= x1 and y0 <= y <= y1:
                self.one = self.sel[i]

    def combo(self, *keys):
        self.combos.append(keys)
        if keys == ("ctrl", "c"):
            self.centred_on = self.one


def find_setup(monkeypatch, keys, fleet_at=(150 * 32, 90 * 32)):
    io = FindIO(keys)
    st = trial.State()
    st.air_keys = list(keys)
    live = trial.live
    monkeypatch.setattr(live, "frames_shown",
                        lambda s: len(s.sel) if len(s.sel) >= 2 else 0)
    monkeypatch.setattr(live, "frames_like",
                        lambda s, n, kind: [i for i, k in enumerate(s.sel) if k == kind])
    monkeypatch.setattr(live, "camera_from_minimap",
                        lambda s: fleet_at if s.centred_on == "scout"
                        else (209 * 32, 50 * 32) if s.centred_on else None)
    # (gold lamps show at Moscow too: the gun centred is told by its buttons)
    monkeypatch.setattr(trial, "gold_on_screen",
                        lambda s, cx, cy, r: [(cx, cy)] if s.centred_on else [])
    monkeypatch.setattr(live, "gun_selected",
                        lambda s: s.centred_on == "artillery")
    return io, st


def test_the_fleet_is_found_by_a_scout_s_picture_and_ctrl_c(monkeypatch):
    """Phase 0 (the owner's recording): the key twice lands eleven to
    fifteen tiles off the Scouts, pulled by the artillery at Moscow; one
    Scout's picture clicked, then Ctrl+C, centres on it."""
    io, st = find_setup(monkeypatch, {"9": ["artillery"] + ["scout"] * 6})
    assert trial.where_is_fleet(io, st) == (150 * 32, 90 * 32)
    assert io.one == "scout" and ("ctrl", "c") in io.combos    # never the gun
    assert st.air.seen[0] == (150 * 32, 90 * 32) and st.air.finds == 1
    assert io.t - 100 < 1.0                                    # about half a second
    assert any("the fleet is at 150, 90" in l for l in io.lines)
    # the first key holds only its artillery: the next key's Scout
    io, st = find_setup(monkeypatch, {"9": ["artillery"],
                                      "0": ["scout", "artillery", "scout"]})
    assert trial.where_is_fleet(io, st) == (150 * 32, 90 * 32) and io.one == "scout"
    # no Scout on any key: nothing clicked, no Ctrl+C
    io, st = find_setup(monkeypatch, {"9": ["artillery"], "0": []})
    assert trial.where_is_fleet(io, st) is None and not io.combos


def test_a_single_fleet_key_is_not_pressed_twice_running(monkeypatch):
    """The key of what is selected already makes the game jump the view
    to it. One fleet key alone: pressed for the first order after the
    fleet was looked for, not again for the next."""
    st = trial.State()
    st.air_keys = ["9"]
    st.dogfight_cam = (4000, 2000)
    io = StubIO()
    trial.order_fleet(io, st, (900, 400))
    trial.order_fleet(io, st, (950, 420))
    assert io.keys.count("9") == 1 and len(io.clicks) == 2
    st.air_selected = False                 # (the fleet was looked for again)
    trial.order_fleet(io, st, (900, 400))
    assert io.keys.count("9") == 2
    st.air_keys = ["9", "0"]                # two keys take turns: always pressed
    io = StubIO()
    trial.order_fleet(io, st, (900, 400))
    trial.order_fleet(io, st, (900, 400))
    assert io.keys.count("9") == 2 and io.keys.count("0") == 2


def test_the_remembered_scout_picture_is_read_again_when_it_fails(monkeypatch):
    io, st = find_setup(monkeypatch, {"9": ["artillery"] + ["scout"] * 3})
    assert trial.where_is_fleet(io, st) is not None
    shots = []
    io.shot = lambda label, keep=True: shots.append(label) or io
    assert trial.where_is_fleet(io, st) is not None
    assert "fleet-find" not in shots        # the picture was remembered
    # a Scout dies and the artillery's picture is where the Scout's was
    io.groups["9"] = ["scout", "artillery", "scout"]
    st.air.scout_at["9"] = (1, 3)
    shots.clear()
    assert trial.where_is_fleet(io, st) is not None and io.one == "scout"
    assert "fleet-find" in shots            # read afresh


def test_hops_keep_out_of_the_axis_turrets_reach():
    m = trial.load_map()
    turrets = trial.axis_turrets(m)
    assert len(turrets) >= 20
    tx, ty = turrets[0]
    spot = trial.off_turrets((tx + 2 * 32, ty + 1 * 32), m)
    assert all((spot[0] - x) ** 2 + (spot[1] - y) ** 2 >= (trial.AA_KEEP * 32 - 1) ** 2
               for x, y in turrets) or \
        (spot[0] - tx) ** 2 + (spot[1] - ty) ** 2 >= (trial.AA_KEEP * 32 - 1) ** 2
    far = (trial.MASS[0], trial.MASS[1])
    assert trial.off_turrets(far, m) == far


def test_with_nothing_near_the_fleet_waits_behind_the_front_by_a_move(monkeypatch):
    """The owner: nothing to shoot and the hit alive: the fleet loiters
    slightly behind the front. A plain move, no attack-move ahead."""
    m = trial.load_map()
    fleet = trial.CENTRED_AT
    st, io = fight_setup(monkeypatch, [(fleet, [])] * 400)
    front = (trial.MASS[0] - 30 * 32, trial.MASS[1])
    monkeypatch.setattr(trial, "army_anchor", lambda w, pic, goal: front)
    amoves = []
    monkeypatch.setattr(trial, "attack_move", lambda *a: amoves.append(a))
    monkeypatch.setattr(trial, "DOGFIGHT_TIME", 12)
    n = trial.dogfight(io, None, m, st, "Warsaw 200")
    assert n >= 1 and not amoves and "a" not in io.keys
    rights = [c for c in io.clicks if c[2] == "right"]
    assert rights and len(rights) <= 2 * 9          # one order a look, both keys


def test_the_artillery_centred_is_never_taken_for_the_fleet(monkeypatch):
    """Trial 41: the remembered picture had become the gun's, the view
    went to Moscow, gold lamps there passed for Scouts, and the bot
    stared at the Heavy Artillery for a minute."""
    io, st = find_setup(monkeypatch, {"9": ["artillery", "scout", "scout"]})
    trial.air_stats(io, st).scout_at["9"] = (0, 3)   # wrongly remembered: the gun
    assert trial.where_is_fleet(io, st) == (150 * 32, 90 * 32)
    assert io.one == "scout" and st.air.scout_at["9"] == (1, 3)


def test_far_outnumbered_the_fleet_keeps_back_and_picks_no_target(monkeypatch):
    """The owner: three to one of our Scouts is a large body. Trial 41:
    seven Scouts flew into the middle of Germany's army after a
    Battlecruiser and all were lost in 27 s."""
    m = trial.load_map()
    fleet = trial.CENTRED_AT
    crowd = [(fleet[0] + 150 + 12 * i, fleet[1] + 8 * (i % 5)) for i in range(24)]
    st, io = fight_setup(monkeypatch, [(fleet, crowd)] * 400, counts=[7] * 50)
    monkeypatch.setattr(trial, "DOGFIGHT_TIME", 10)
    shot = []
    monkeypatch.setattr(trial, "attack_target",
                        lambda *a, **k: shot.append(1) or True)
    trial.dogfight(io, None, m, st, "Warsaw 200")
    assert any("the fleet keeps back" in l for l in io.lines)
    assert not shot and "a" not in io.keys
    rights = [c for c in io.clicks if c[2] == "right"]
    assert rights and all(c[0] < fleet[0] + 150 or c[1] > 800 for c in rights)   # never into them


def test_on_a_balkan_hit_the_air_waits_for_the_army_to_go_on_into_serbia(monkeypatch):
    """The owner (trial 41): on a Balkan hit the air takes a pause until
    most of the army has reached Romania and been sent on into Serbia."""
    import inspect
    src = inspect.getsource(trial.hit)
    assert 'front_of(target) == "balks"' in src and "air_waits_serbia = True" in src
    src = inspect.getsource(trial.into_serbia)
    assert "air_waits_serbia" in src and "dogfight(" in src


def test_no_hit_east_while_our_troops_are_in_the_balkans(monkeypatch):
    from tests.test_trial import StubWatch, blob
    m = trial.load_map()
    st = trial.State()
    st.t0, st.balkan_start = 0.0, 0
    io = StubIO()
    io.shot = lambda label, keep=True: "pic"
    io.t = 500.0                                # the plan says north now
    assert trial.planned_front(500.0) == "north"
    ours = blob(trial.BALKS_POINT, 8) | blob(trial.MASS, 6)
    target = trial.choose_target(io, StubWatch(ours, set()), st, m)
    assert trial.team_rules.front_of(target) == "balks"
    assert any("still in the Balkans" in l for l in io.lines)
    io2 = StubIO()
    io2.shot = io.shot
    io2.t = 500.0
    target = trial.choose_target(io2, StubWatch(blob(trial.MASS, 6), set()), st, m)
    assert trial.team_rules.front_of(target) == "east"


def test_enemy_fighters_are_attacked_only_when_it_pays(monkeypatch):
    """The owner: the enemy's air (Wraiths, Scouts) is attacked when our
    Scouts are clearly more than theirs, or when their air has come too
    far forward over our marines; a large air (two to one of our Scouts)
    is kept away from."""
    io = StubIO()
    bc = {"kind": "battlecruiser", "xy": (1, 1)}
    f = [{"kind": "fighter", "xy": (i, 0)} for i in range(6)]
    # clearly more of ours: fighters first
    out = trial.air_first(io, [bc] + f[:3], 8, False)
    assert [t["kind"] for t in out] == ["fighter"] * 3 + ["battlecruiser"]
    # about even, out over the enemy: fighters left alone
    out = trial.air_first(io, [bc] + f[:5], 6, False)
    assert [t["kind"] for t in out] == ["battlecruiser"]
    # about even, but they have come over our own army: attacked
    out = trial.air_first(io, [bc] + f[:5], 6, True)
    assert out[0]["kind"] == "fighter"
    # a large air: nothing, the fleet keeps back
    assert trial.air_first(io, [bc] + f, 3, True) is None
    assert any("a large air" in l for l in io.lines)
    # no fighters: as before
    assert trial.air_first(io, [bc], 3, False) == [bc]
    from bot import team
    assert "fighter" in team.TARGET_SCHEMA["properties"]["targets"]["items"][
        "properties"]["kind"]["enum"]
