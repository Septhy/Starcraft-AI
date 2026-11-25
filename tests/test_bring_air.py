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
        ImageDraw.Draw(pic).rectangle((x - 20, y - 20, x + 20, y + 20),
                                      outline=(250, 235, 85), width=4)
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


def record_task(io, xy=(40 * 32, 60 * 32), n=10):
    groups = [{"owner": "teal", "kind": "Wraith", "count": n}]
    return {"colour": "teal", "spot": xy, "since": io.t, "checked": io.t,
            "mode": "follow", "from": (100 * 32, 60 * 32),
            "record": {"time": "10:00", "groups": groups, "xy": xy,
                       "place": "Sea", "at": io.t}}


def wraiths(n):
    return [{"owner": "teal", "kind": "Wraith", "count": n}]


def test_the_fleet_follows_the_record_every_eight_seconds(monkeypatch):
    """The repository owner: every 8 seconds, their air near the last
    record, roughly the same (within 30%): follow 4 to 6 tiles behind,
    and a new record is written."""
    m = trial.load_map()
    io = StubIO()
    io.shot = lambda label, keep=True: None
    st = trial.State()
    st.air_keys = ["9"]
    st.fleet_task = record_task(io)
    monkeypatch.setattr(trial, "fleet_left", lambda io_, st_: 6)
    monkeypatch.setattr(trial, "look_at", lambda io_, x, y, wait=0: (x, y))
    monkeypatch.setattr(trial, "ally_groups_near", lambda *a: [])
    reads = iter([wraiths(8), wraiths(4)])
    monkeypatch.setattr(trial, "read_fleet", lambda io_, st_, pic: next(reads))
    searched = []
    monkeypatch.setattr(trial, "search_fleet",
                        lambda *a: searched.append(1) or False)
    io.t += 5
    assert not trial.follow_ally_air(io, Watch(), m, st)   # not before 8 s
    io.t += 4
    assert trial.follow_ally_air(io, Watch(), m, st)       # 8 of 10: a match
    assert io.keys == ["9", "a"]
    rec = st.fleet_task["record"]
    assert trial.fleet_total(rec["groups"]) == 8
    assert any(line.startswith("FLEET RECORD") for line in io.lines)
    x, y = st.fleet_task["spot"]                           # 5 tiles behind
    d = ((x - 40 * 32) ** 2 + (y - 60 * 32) ** 2) ** 0.5 / 32
    assert 4 <= d <= 6
    io.t += 8
    trial.follow_ally_air(io, Watch(), m, st)              # 4 of 8: not it
    assert searched == [1]


def test_a_missing_fleet_is_searched_at_once_and_found(monkeypatch):
    """Not where it was: searched at once round the last record, our air
    kept still until found; found, the air goes there, a new record."""
    m = trial.load_map()
    io = StubIO()
    io.shot = lambda label, keep=True: None
    st = trial.State()
    st.air_keys = ["9"]
    st.fleet_task = record_task(io)
    monkeypatch.setattr(trial, "look_at", lambda io_, x, y, wait=0: (x, y))
    far = (60 * 32, 70 * 32)
    monkeypatch.setattr(trial, "ally_groups_near",
                        lambda io_, w, xy, reach: [far])
    looked = []

    def read(io_, st_, pic):
        io.t += 2                       # each look takes a while
        return wraiths(9) if len(looked) else wraiths(0)
    monkeypatch.setattr(trial, "look_fleet",
                        lambda io_, st_, xy: looked.append(xy) or read(io_, st_, None))
    sent = []
    monkeypatch.setattr(trial, "send_fleet",
                        lambda io_, w, st_, a, b: sent.append(b) or [b])
    assert trial.search_fleet(io, Watch(), m, st, st.fleet_task)
    assert looked == [far]
    assert st.fleet_task["record"]["xy"] == far and sent


def test_a_fleet_not_found_in_10_seconds_is_lost(monkeypatch):
    m = trial.load_map()
    io = StubIO()
    io.shot = lambda label, keep=True: None
    st = trial.State()
    st.air_keys = ["9"]
    st.fleet_task = record_task(io)
    said = []
    monkeypatch.setattr(trial, "say", lambda io_, st_, text, force=False:
                        said.append(text))
    monkeypatch.setattr(trial, "ally_groups_near", lambda *a: [])
    looked = []

    def look(io_, st_, xy):
        looked.append(xy)
        io.t += 3
        return []
    monkeypatch.setattr(trial, "look_fleet", look)
    monkeypatch.setattr(trial, "send_fleet", lambda *a: pytest.fail("moved"))
    assert not trial.search_fleet(io, Watch(), m, st, st.fleet_task)
    assert said == ["Lost the fleet"] and st.fleet_task is None
    assert st.air_home and 3 <= len(looked) <= 5    # 10 s of looks, then lost
    assert any(k == "right" for *_, k in io.clicks)  # back to its parking


def test_a_fleet_record_says_time_units_and_position():
    m = trial.load_map()
    io = StubIO()
    io.shot = lambda label, keep=True: None
    st = trial.State()
    groups = [{"owner": "teal", "kind": "Wraith", "count": 14},
              {"owner": "purple", "kind": "Scout", "count": 3}]
    rec = trial.write_record(io, st, m, groups, (40 * 32, 60 * 32))
    text = [l for l in io.lines if l.startswith("FLEET RECORD")][0]
    assert "* Time:" in text and "* Units: 17 in all: 14 Wraiths (teal), " \
        "3 Scouts (purple)" in text and "* Position: minimap" in text
    assert rec["place"] in text
    assert trial.fleet_matches(rec, [{"owner": "teal", "kind": "Wraith",
                                      "count": 12}])
    assert not trial.fleet_matches(rec, [{"owner": "teal", "kind": "Wraith",
                                          "count": 9}])
    assert not trial.fleet_matches(rec, [{"owner": "orange", "kind": "Wraith",
                                          "count": 17}])


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
    ("orange", "Wraith", 5), ("purple", "Scout", 5), ("teal", "Wraith", 5)])
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


def minimap_screen(name):
    from PIL import Image
    import os
    pic = Image.new("RGB", (1920, 1080))
    pic.paste(Image.open(os.path.join(os.path.dirname(__file__), "data",
                                      name + ".png")).convert("RGB"), (0, 780))
    return pic


def test_the_real_ping_is_found_and_spains_yellow_is_not():
    """The repository owner's recording: a ping is a hollow yellow
    square on the minimap, first four bars closing in."""
    base = trial.yellow_on_minimap(minimap_screen("ping_before"))
    at = trial.find_ping(minimap_screen("ping_square"), base)
    c, r = live.to_drawn(*at)
    assert abs(c - 107) <= 3 and abs(r - 117) <= 3        # over Germany
    bars = trial.find_ping(minimap_screen("ping_bars"), base)
    bc, br = live.to_drawn(*bars)
    assert abs(bc - 107) <= 14 and abs(br - 117) <= 14   # roughly there
    assert trial.find_ping(minimap_screen("ping_before"), base) is None


def test_the_bars_wait_for_the_square(monkeypatch):
    from bot import team
    st = trial.State()
    io = StubIO()
    st.clock = team.GameClock(io.now)
    st.clock.value = 100
    base = trial.yellow_on_minimap(minimap_screen("ping_before"))
    st.air_ping = {"colour": "teal", "since": 100, "at": None, "base": base}
    trial.watch_for_ping(st, minimap_screen("ping_bars"))
    assert st.air_ping["at"] is None and st.air_ping["bars"]
    trial.watch_for_ping(st, minimap_screen("ping_square"))
    c, r = live.to_drawn(*st.air_ping["at"])
    assert abs(c - 107) <= 3 and abs(r - 117) <= 3


def test_allied_planes_are_counted_by_colour_when_the_model_cannot(monkeypatch):
    """Trial 31: twenty teal Wraiths at the ping, the model's count came
    back empty ("? teal planes") and Russia said it couldn't find them."""
    from PIL import Image, ImageDraw
    pic = Image.new("RGB", (1920, 1080), (60, 70, 40))
    d = ImageDraw.Draw(pic)
    for k in range(7):                              # seven teal planes
        x, y = 700 + k * 90, 300 + (k % 2) * 60
        d.rectangle((x, y, x + 8, y + 6), fill=(40, 190, 160))
    assert trial.ally_air_by_colour(pic) == 7
    st, io = trial.State(), StubIO()
    st.ears = CountingEars([None])
    assert trial.allied_air_at(io, st, pic, "teal") == 7 >= trial.PING_ALLY_AIR
    st.ears = CountingEars([9])                     # the model, when it can
    assert trial.allied_air_at(io, st, pic, "teal") == 9
    assert trial.ally_air_by_colour(Image.new("RGB", (1920, 1080),
                                              (60, 70, 40))) == 0
