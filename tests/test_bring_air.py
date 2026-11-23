"""\"@R bring air\": find the ally's air and take the fleet there safely."""
import numpy as np

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


def test_bring_air_attack_moves_the_whole_fleet_along_the_way(monkeypatch):
    m = trial.load_map()
    said = []
    monkeypatch.setattr(trial, "say", lambda io, st, text, force=False:
                        said.append(text))
    monkeypatch.setattr(trial, "find_ally_air",
                        lambda io, watch, colour: (40 * 32, 60 * 32))
    io = StubIO()
    io.shot = lambda label, keep=True: None
    st = trial.State()
    st.air_keys, st.air_home = ["9", "0"], True
    assert trial.bring_air(io, Watch(), m, st, "teal")
    stops = trial.air_route(Watch(), None, trial.fleet_spot(), (40 * 32, 60 * 32))
    assert io.keys.count("a") == 2 * len(stops)       # attack-move, both keys
    assert io.keys[0] == "9" and "0" in io.keys
    assert sum(1 for c in io.clicks if c[2] == "shift") == 2 * (len(stops) - 1)
    assert st.fleet_task["colour"] == "teal" and not st.air_home
    assert said == ["air on its way to you"]
    # while it is with them, the fleet is not steered back over the army
    st.battle = trial.Battle("Berlin 1000", 0)
    st.battle.front = (100 * 32, 90 * 32)
    st.battle.samples = [(10, 100, 5, 20)]
    called = []
    monkeypatch.setattr(trial, "steer_fleet", lambda *a: called.append(1))
    st.air_moved = -1e9
    trial.fight(io, Watch(), m, st, None)
    assert called == []


def test_no_air_found_is_said(monkeypatch):
    m = trial.load_map()
    said = []
    monkeypatch.setattr(trial, "say", lambda io, st, text, force=False:
                        said.append(text))
    monkeypatch.setattr(trial, "find_ally_air", lambda io, watch, colour: None)
    st = trial.State()
    st.air_keys = ["9"]
    assert not trial.bring_air(StubIO(), Watch(), m, st, "purple")
    assert said == ["I can't find your air"] and st.fleet_task is None


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
    assert team.addressed("@Reset") and team.addressed("@R return air")
    assert not team.addressed("@Re go")
