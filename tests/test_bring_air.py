"""\"@R bring air\": find the ally's air and take the fleet there safely."""
import numpy as np
import pytest

from bot import trial
from eyes import live
from tests.test_trial import StubIO


class Watch:
    """Our pixels and other players' pixels, by slot."""
    def __init__(self, ours=(), by_slot=None):
        self.ours, self.by_slot = set(ours), by_slot or {}
        self.buildings = np.zeros((217, 288), dtype=bool)

    def units(self, picture):
        return set(self.ours)

    def others(self, picture, slots):
        out = set()
        for s in slots:
            out |= set(self.by_slot.get(s, ()))
        return out


def square(c, r, n=3):
    return {(c + i, r + j) for i in range(n) for j in range(n)}


def test_the_allys_air_is_their_colour_over_water():
    land = trial._land()
    sea = next((c, r) for r in range(60, 120) for c in range(60, 120)
               if not land[r:r + 4, c:c + 4].any())
    shore = next((c, r) for r in range(100, 150) for c in range(150, 200)
                 if land[r:r + 4, c:c + 4].all())
    io = StubIO()
    io.shot = lambda label, keep=True: None
    watch = Watch(by_slot={2: square(*sea) | square(*shore, n=5)})
    x, y = trial.find_ally_air(io, watch, "teal")
    c, r = live.to_drawn(x, y)
    assert abs(c - (sea[0] + 1)) <= 1 and abs(r - (sea[1] + 1)) <= 1
    # another ally's colour is not theirs; an enemy colour is never asked
    assert trial.find_ally_air(io, watch, "orange") is None
    assert trial.find_ally_air(io, watch, "red") is None


def test_the_way_keeps_to_friendly_ground_and_round_enemy_buildings():
    start, goal = (60 * 32, 60 * 32), (140 * 32, 60 * 32)
    sc, sr = (int(v) for v in live.to_drawn(*start))
    gc, gr = (int(v) for v in live.to_drawn(*goal))
    mid = ((sc + gc) // 2, sr)
    # enemy buildings across the straight line; our side's units along
    # a way round to the north
    enemy = {(mid[0] + i, sr + j) for i in range(-3, 4) for j in range(-6, 7)}
    friends = {(c, sr - 18) for c in range(sc, gc + 1, 3)}
    watch = Watch(ours=friends, by_slot={0: enemy})
    stops = trial.air_route(watch, None, start, goal)
    assert stops, stops
    end = live.to_drawn(*stops[-1])
    assert abs(end[0] - gc) <= 1 and abs(end[1] - gr) <= 1
    for x, y in stops:
        c, r = live.to_drawn(x, y)
        assert min(abs(c - e[0]) + abs(r - e[1]) for e in enemy) > \
            trial.ENEMY_NEAR, (c, r)


def ping_picture(at=None):
    """A screen whose minimap shows a yellow ping at drawn pixel `at`."""
    from PIL import Image, ImageDraw
    pic = Image.new("RGB", (1920, 1080))
    if at:
        d = live.DRAWN
        x, y = d["left"] + at[0], d["top"] + at[1]
        ImageDraw.Draw(pic).ellipse((x - 3, y - 3, x + 3, y + 3),
                                    outline=(250, 240, 40))
    return pic


def asked(monkeypatch):
    said = []
    monkeypatch.setattr(trial, "say", lambda io, st, text, force=False:
                        said.append(text))
    return said


def test_bring_air_asks_for_a_ping_and_follows_the_allies_air_there(monkeypatch):
    """The repository owner: "ping the map"; at the ping, allied air:
    follow it by a safe way, attack-moving."""
    m = trial.load_map()
    said = asked(monkeypatch)
    io = StubIO()
    io.shot = lambda label, keep=True: ping_picture()
    st = trial.State()
    st.air_keys, st.air_home = ["9", "0"], True
    assert trial.bring_air(io, Watch(), m, st, "teal")
    assert said == ["ping the map"]
    trial.watch_for_ping(st, ping_picture((60, 60)))      # the ping
    at = st.air_ping["at"]
    assert abs(live.to_drawn(*at)[0] - 60) <= 2
    monkeypatch.setattr(trial, "count_ally_air", lambda *a: 5)
    monkeypatch.setattr(trial, "enemy_on_screen", lambda *a, **k: 0)
    monkeypatch.setattr(trial, "look_at", lambda io_, x, y, wait=0: (x, y))
    trial.ping_step(io, Watch(), m, st)
    assert said[-1] == "following your air"
    assert st.fleet_task["mode"] == "follow" and not st.air_home
    assert io.keys.count("a") >= 2                           # attack-move, both keys
    # while it is with them, the fleet is not steered back over the army
    st.battle = trial.Battle("Berlin 1000", 0)
    st.battle.front = (100 * 32, 90 * 32)
    called = []
    monkeypatch.setattr(trial, "steer_fleet", lambda *a: called.append(1))
    st.air_moved = -1e9
    trial.fight(io, Watch(), m, st, None)
    assert called == []


def test_at_a_ping_with_mostly_enemy_the_air_attacks_then_comes_back(monkeypatch):
    m = trial.load_map()
    said = asked(monkeypatch)
    io = StubIO()
    io.shot = lambda label, keep=True: ping_picture()
    st = trial.State()
    st.air_keys = ["9"]
    trial.bring_air(io, Watch(), m, st, "orange")
    trial.watch_for_ping(st, ping_picture((120, 80)))
    monkeypatch.setattr(trial, "count_ally_air", lambda *a: 0)
    enemy = iter([12, 6, 0])
    monkeypatch.setattr(trial, "enemy_on_screen", lambda *a, **k: next(enemy))
    monkeypatch.setattr(trial, "look_at", lambda io_, x, y, wait=0: (x, y))
    monkeypatch.setattr(trial, "fleet_left", lambda io_, st_: 6)
    trial.ping_step(io, Watch(), m, st)
    assert said[-1] == "attacking at your ping" and st.fleet_task["mode"] == "attack"
    io.t += trial.ALLY_AIR_CHECK
    trial.follow_ally_air(io, Watch(), m, st)              # still enemy there
    assert st.fleet_task is not None
    io.t += trial.ALLY_AIR_CHECK
    trial.follow_ally_air(io, Watch(), m, st)              # cleared
    assert st.fleet_task is None and st.air_home
    assert said[-1] == "area cleared, air coming back"


def test_nothing_at_the_ping_no_ping_or_lost_planes(monkeypatch):
    m = trial.load_map()
    said = asked(monkeypatch)
    io = StubIO()
    io.shot = lambda label, keep=True: ping_picture()
    monkeypatch.setattr(trial, "look_at", lambda io_, x, y, wait=0: (x, y))
    # nothing there
    st = trial.State()
    st.air_keys = ["9"]
    trial.bring_air(io, Watch(), m, st, "purple")
    trial.watch_for_ping(st, ping_picture((100, 100)))
    monkeypatch.setattr(trial, "count_ally_air", lambda *a: 0)
    monkeypatch.setattr(trial, "enemy_on_screen", lambda *a, **k: 0)
    trial.ping_step(io, Watch(), m, st)
    assert said[-1] == "I can't find your air" and st.fleet_task is None
    # no ping within ten minutes
    trial.bring_air(io, Watch(), m, st, "purple")
    io.t += trial.PING_WAIT + 1
    trial.ping_step(io, Watch(), m, st)
    assert said[-1] == "can't find ping" and st.air_ping is None
    # following, and the planes are all lost: no more following
    st.fleet_task = {"colour": "teal", "spot": (0, 0), "since": io.t,
                     "checked": io.t - 99, "mode": "follow"}
    monkeypatch.setattr(trial, "fleet_left", lambda io_, st_: 0)
    trial.follow_ally_air(io, Watch(), m, st)
    assert st.fleet_task is None and said[-1] == "my air is gone"
    # no air at all
    st2 = trial.State()
    assert not trial.bring_air(io, Watch(), m, st2, "teal")
    assert said[-1] == "I have no air"


def test_the_fleet_stays_with_the_ally_through_hits_and_resets(monkeypatch):
    m = trial.load_map()
    said = []
    monkeypatch.setattr(trial, "say", lambda io, st, text, force=False:
                        said.append(text))
    st = trial.State()
    st.air_keys, st.ground_keys = ["9", "0"], ["1", "2"]
    st.fleet_task = {"colour": "teal", "spot": (0, 0), "since": 0}
    # Russia's own orders do not use the fleet keys while it is away
    assert trial.own_fleet_keys(st) == []
    assert trial.keys_for(st, "air") == [] and trial.keys_for(st, "all") == ["1", "2"]
    io = StubIO()
    trial.recall(io, st, "test")
    assert "9" not in io.keys and "0" not in io.keys
    # a hit does not take it back
    monkeypatch.setattr(trial, "sweep_mass", lambda *a, **k: (0, 0))
    monkeypatch.setattr(trial, "push_front", lambda *a, **k: 0)
    io = StubIO()
    trial.hit(io, None, m, st, "Berlin 1000", use_keys=False)
    assert "9" not in io.keys and st.fleet_task is not None
    # "@R reset" is for massing and hitting: the air stays
    trial.reset_orders(StubIO(), m, st)
    assert st.fleet_task is not None
    # "@R return air" brings it back to its spot
    io = StubIO()
    assert trial.return_air(io, m, st)
    assert st.fleet_task is None and st.air_home
    assert io.keys.count("a") == 2 and said[-1] == "air coming back"
    assert trial.own_fleet_keys(st) == ["9", "0"]
    assert not trial.return_air(StubIO(), m, st)      # already back


def test_return_air_and_reset_are_told_apart():
    from bot import team
    got = []
    t = team.Team(lambda s: None, lambda s: None,
                  on_reset=lambda: got.append("reset"),
                  on_return_air=lambda: got.append("return"),
                  on_bring_air=lambda o: got.append("bring " + o.colour))
    def order(kind):
        return team.Order({"colour": "orange", "kind": kind, "front": "none",
                           "wait_seconds": -1, "until_clock": "", "place": "",
                           "said": "@R x"})
    for k in ("bring_air", "reset", "return_air"):
        t.heard(order(k), 10)
    assert got == ["bring orange", "reset", "return"]
    # "@Reset" is not Russia's tag (other countries' bots will have their
    # own); only "@R reset" is
    assert not team.addressed("@Reset") and team.addressed("@R reset")
    assert team.addressed("@R return air")
    assert not team.addressed("@Re go")


def test_the_fleet_follows_the_allys_air_every_eight_seconds(monkeypatch):
    m = trial.load_map()
    io = StubIO()
    io.shot = lambda label, keep=True: None
    st = trial.State()
    st.air_keys = ["9"]
    st.fleet_task = {"colour": "teal", "spot": (40 * 32, 60 * 32),
                     "since": io.t, "checked": io.t}
    seen = iter([(40 * 32, 60 * 32), (70 * 32, 40 * 32), None])
    monkeypatch.setattr(trial, "find_ally_air", lambda *a, **k: next(seen))
    monkeypatch.setattr(trial, "fleet_left", lambda io_, st_: 6)
    # not before 8 seconds
    io.t += 5
    assert not trial.follow_ally_air(io, Watch(), m, st)
    # 8 s on, their air has not moved: the fleet stays on it
    io.t += 4
    assert trial.follow_ally_air(io, Watch(), m, st)
    assert io.keys == ["9", "a"]
    # 8 s later it has moved: the fleet follows along the safe way
    io.keys.clear()
    io.t += 8
    assert trial.follow_ally_air(io, Watch(), m, st)
    assert st.fleet_task["spot"] == (70 * 32, 40 * 32)
    assert io.keys.count("a") >= 1
    assert any("the fleet follows" in line for line in io.lines)
    # their air not seen: the fleet waits where it is
    io.keys.clear()
    io.t += 8
    assert not trial.follow_ally_air(io, Watch(), m, st)
    assert io.keys == []
    # back home: no more check-ups
    st.fleet_task = None
    io.t += 8
    assert not trial.follow_ally_air(io, Watch(), m, st)


def test_the_massing_goes_on_while_the_fleet_is_away(monkeypatch):
    """The check-ups are part of the massing loop: training and gathering
    carry on in between."""
    import inspect
    src = inspect.getsource(trial.build_big_mass)
    assert "follow_ally_air(" in src and "gather_idle(" in src \
        and "train_everywhere(" in src
    assert "follow_ally_air(" in inspect.getsource(trial.wait_for_mass)


class CountingEars:
    def __init__(self, counts):
        self.counts, self.asked = list(counts), []

    def count_air(self, picture, colour, kind):
        self.asked.append((colour, kind))
        return self.counts.pop(0)


def two_places():
    land = trial._land()
    seas = [(c, r) for r in range(60, 140, 3) for c in range(40, 140, 3)
            if not land[r:r + 4, c:c + 4].any()]
    a = seas[0]
    b = next(p for p in seas if abs(p[0] - a[0]) + abs(p[1] - a[1]) > 40)
    return a, b


@pytest.mark.parametrize("colour, kind, mass", [
    ("orange", "Wraith", 8), ("purple", "Scout", 11), ("teal", "Wraith", 22)])
def test_the_allys_air_mass_is_found_by_counting_their_air(colour, kind, mass):
    a, b = two_places()
    slot = trial.ALLY_SLOTS[colour]
    io = StubIO()
    io.shot = lambda label, keep=True: None
    # the bigger patch is a dropship and some ground (none of their
    # air there); the smaller has their air mass
    watch = Watch(by_slot={slot: square(*a, n=5) | square(*b)})
    st = trial.State()
    st.ears = CountingEars([0, mass])
    x, y = trial.find_ally_air(io, watch, colour, st)
    c, r = live.to_drawn(x, y)
    assert abs(c - (b[0] + 1)) <= 1 and abs(r - (b[1] + 1)) <= 1
    assert st.ears.asked == [(colour, kind)] * 2
    # below their mass everywhere: the place with the most of their air
    st.ears = CountingEars([mass - 3, 2])
    x, y = trial.find_ally_air(io, watch, colour, st)
    c, r = live.to_drawn(x, y)
    assert abs(c - (a[0] + 2)) <= 1 and abs(r - (a[1] + 2)) <= 1
    # none of their air anywhere: not found
    st.ears = CountingEars([0, 0])
    assert trial.find_ally_air(io, watch, colour, st) is None
    # following: near where their air last was, no need to count again
    st.ears = CountingEars([])
    assert trial.find_ally_air(io, watch, colour, st,
                               last=live.from_drawn(*b)) is not None


def test_a_place_that_could_not_be_counted_is_never_taken():
    """Trial 25: one place counted 0, the next could not be counted, and
    the fleet went to the biggest patch of orange anyway."""
    a, b = two_places()
    io = StubIO()
    io.shot = lambda label, keep=True: None
    watch = Watch(by_slot={4: square(*a, n=5) | square(*b)})
    st = trial.State()
    st.ears = CountingEars([0, None])
    assert trial.find_ally_air(io, watch, "orange", st) is None


def test_while_following_their_air_is_counted_again_now_and_then(monkeypatch):
    m = trial.load_map()
    io = StubIO()
    io.shot = lambda label, keep=True: None
    st = trial.State()
    st.air_keys = ["9"]
    st.fleet_task = {"colour": "teal", "spot": (40 * 32, 60 * 32),
                     "since": io.t, "checked": io.t}
    asked = []
    monkeypatch.setattr(trial, "find_ally_air",
                        lambda *a, **k: asked.append(k["recount"]) or
                        (40 * 32, 60 * 32))
    for _ in range(6):
        io.t += trial.ALLY_AIR_CHECK
        trial.follow_ally_air(io, Watch(), m, st)
    assert asked == [False, False, True, False, False, True]
