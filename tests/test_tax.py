"""Tax cities, and fetching every idle body for the next hit."""
from bot import team, trial
from eyes import live
from tests.test_trial import StubIO, StubWatch, blob


def setup(monkeypatch, clock_seconds=0.0, ours=(), axis=()):
    m = trial.load_map()
    st, io = trial.State(), StubIO()
    st.hits_sent = trial.TAX_AFTER_HITS             # tax efforts have begun
    st.clock = team.GameClock(io.now)
    st.clock.value = clock_seconds
    flown = []

    def fly(io_, mapdata, st_, kind, tile, city):
        flown.append((kind, tile, city))
        return True
    monkeypatch.setattr(trial, "fly_building", fly)
    guards = []

    def guard(io_, watch, mapdata, st_, name, picture):
        guards.append(name)
        st_.guards[name] = io_.now()
        return True
    monkeypatch.setattr(trial, "send_guard", guard)
    return m, st, io, StubWatch(ours, axis), flown, guards


def at(m, name, n=5):
    c = trial.place(m, name)
    return blob((c["x"], c["y"]), n)


def countdown_at(c):
    """The game clock at which the round countdown shows c seconds."""
    return (300 - c) / trial.COUNTDOWN_RATE


def test_floats_buildings_to_krakow_and_romania_when_clear(monkeypatch):
    m, st, io, watch, flown, guards = setup(monkeypatch, countdown_at(150))
    assert trial.tax_rounds(io, watch, m, st, None) == 2
    cities = [c for _, _, c in flown]
    assert cities == ["Krakow 200", "Romania 300"]      # not Factory 7 at 2:30
    assert all(kind != "Command Center" for kind, _, _ in flown)
    assert all(kind != "Barracks" for kind, _, _ in flown)   # spare ones first
    assert guards == []
    # on its way: not sent again
    io.t += trial.TAX_EVERY
    assert trial.tax_rounds(io, watch, m, st, None) == 0


def test_a_lost_building_is_replaced(monkeypatch):
    m, st, io, watch, flown, _ = setup(monkeypatch, countdown_at(150))
    trial.tax_rounds(io, watch, m, st, None)
    io.t += 400                         # long after it should have arrived
    st.clock.value += 400
    assert trial.tax_rounds(io, watch, m, st, None) >= 2
    tiles = [t for _, t, _ in flown]
    assert len(set(tiles)) == len(tiles)                    # other buildings


def test_our_troops_at_a_city_do_not_stop_its_building(monkeypatch):
    m = trial.load_map()
    m, st, io, watch, flown, _ = setup(
        monkeypatch, countdown_at(150), ours=at(m, "Krakow 200", 3))
    trial.tax_rounds(io, watch, m, st, None)
    assert [c for _, _, c in flown] == ["Krakow 200", "Romania 300"]


def test_krakow_gets_the_factory_and_romania_the_starport(monkeypatch):
    m, st, io, watch, flown, guards = setup(monkeypatch, countdown_at(150))
    # a building went to Warsaw after the first hit: not those two
    trial.flights_after(io, m, st, 1)
    trial.tax_rounds(io, watch, m, st, None)
    got = {c: (kind, tile) for kind, tile, c in flown}
    assert got["Krakow 200"] == ("Factory", (165, 49))
    assert got["Romania 300"] == ("Starport", (190, 110))
    assert got["Warsaw 200"][1] not in ((165, 49), (190, 110))
    # and Factory 7 still has a building that can reach it in time
    st.clock.value = countdown_at(40)
    trial.tax_rounds(io, watch, m, st, None)
    assert [c for _, _, c in flown].count("Factory 7") == 1


def test_no_building_floats_into_the_enemy(monkeypatch):
    m = trial.load_map()
    many = at(m, "Krakow 200", 9)                   # the hit has not won yet
    m, st, io, watch, flown, guards = setup(monkeypatch, countdown_at(150),
                                            axis=many)
    assert trial.tax_with_hit(io, watch, m, st, "Berlin 1000", object()) == 0
    assert flown == []
    # just taken: our troops there far outnumber the enemy left
    k = trial.place(m, "Krakow 200")
    watch.axis = blob((k["x"], k["y"]), 2)
    watch.ours = at(m, "Krakow 200", 9)
    trial.tax_with_hit(io, watch, m, st, "Berlin 1000", object())
    assert [c for _, _, c in flown] == ["Krakow 200"]


def test_factory_7_sets_off_at_one_minute_and_must_arrive_by_three(monkeypatch):
    # (at 0:20 only Romania's own starport could still make it in time,
    # and it has gone to Romania)
    for c, goes in [(150, False), (100, False), (60, True), (40, True),
                    (250, False), (170, False)]:   # 250: too late to arrive
        m, st, io, watch, flown, _ = setup(monkeypatch, countdown_at(c))
        trial.tax_rounds(io, watch, m, st, None)
        sent = [f for f in flown if f[2] == "Factory 7"]
        assert bool(sent) == goes, c
        if sent:
            kind, tile, _ = sent[0]
            b = next(b for b in m["slots"]["5"]["buildings"]
                     if (b["x"] // 32, b["y"] // 32) == tile)
            f7 = trial.place(m, "Factory 7")
            left = trial.until_countdown(st.clock.time(), trial.F7_ARRIVE)
            assert trial.float_time(b, f7) <= left, (c, kind, tile)
            assert kind != "Command Center"


def test_enemies_get_a_detachment_first_and_many_are_left_to_hits(monkeypatch):
    m = trial.load_map()
    few = at(m, "Krakow 200", 3)                    # 9 enemy pixels
    m, st, io, watch, flown, guards = setup(monkeypatch, countdown_at(150),
                                            axis=few)
    trial.tax_rounds(io, watch, m, st, None)
    assert guards == ["Krakow 200"]
    assert "Krakow 200" not in [c for _, _, c in flown]
    io.t += trial.TAX_EVERY                         # not again so soon
    trial.tax_rounds(io, watch, m, st, None)
    assert guards == ["Krakow 200"]
    many = at(m, "Romania 300", 9)                  # 81 enemy pixels
    m, st, io, watch, flown, guards = setup(monkeypatch, countdown_at(150),
                                            axis=many)
    trial.tax_rounds(io, watch, m, st, None)
    assert "Romania 300" not in guards
    assert "Romania 300" not in [c for _, _, c in flown]


def test_every_idle_body_is_fetched_small_or_forward(monkeypatch):
    m = trial.load_map()
    st, io = trial.State(), StubIO()
    moscow = blob((210 * 32, 52 * 32), 2)           # 4 pixels: a dozen men
    forward = blob((140 * 32, 85 * 32), 2)          # left by an earlier hit
    fighting = blob((128 * 32, 70 * 32), 3)
    enemy = blob((128 * 32 + 64, 70 * 32), 3)
    mass = blob(trial.MASS, 6)
    watch = StubWatch(moscow | forward | fighting | mass, enemy)
    picked = []

    def select(io_, pixels, st_, watch_=None, margin=None):
        picked.append(set(pixels))
        return True
    monkeypatch.setattr(trial, "select_group", select)
    monkeypatch.setattr(trial.live, "clusters", live.clusters)
    io.shot = lambda label, keep=True: None
    orders, _, _ = trial.gather_idle(io, watch, m, st, {})
    assert orders == 2
    assert any(p & moscow for p in picked) and any(p & forward for p in picked)
    assert not any(p & fighting for p in picked)
    assert not any(p & mass for p in picked)
    # the farthest from the mass goes first
    assert picked[0] & moscow


def test_never_a_barracks_or_command_centre(monkeypatch):
    m = trial.load_map()
    st = trial.State()
    kinds = {b["type"] for b in trial.spare_buildings(m, st)}
    assert kinds and not kinds & {"Barracks", "Command Center"}
    io = StubIO()
    assert not trial.fly_building(io, m, st, "Barracks", (173, 80), "Warsaw 200")
    assert io.clicks == [] and "l" not in io.keys


def test_with_nothing_left_to_float_an_scv_builds_a_depot(monkeypatch):
    m, st, io, watch, flown, guards = setup(monkeypatch, countdown_at(150))
    for b in trial.spare_buildings(m, st):          # everything already flown
        st.flights_done.add((b["x"] // 32, b["y"] // 32))
    monkeypatch.setattr(trial, "select_building", lambda io_, b: True)
    trial.tax_rounds(io, watch, m, st, None)
    assert flown == []
    krakow = trial.place(m, "Krakow 200")
    assert "s" in io.keys                           # an SCV is made
    rally = live.minimap_point(krakow["x"], krakow["y"])
    assert (*rally, "right") in io.clicks           # and sent to the city
    assert st.depots["Krakow 200"]["stage"] == "walking"
    # it arrives; it is picked and told to build a depot by the beacon
    io.keys.clear()
    io.t = st.depots["Krakow 200"]["due"] + 1
    st.last_tax = -1e9
    watch.ours = at(m, "Krakow 200", 2)
    monkeypatch.setattr(trial, "select_group", lambda *a, **k: True)
    monkeypatch.setattr(trial, "look_at", lambda io_, x, y, wait=0: (x - 900, y - 400))
    io.shot = lambda label, keep=True: None
    trial.tax_rounds(io, watch, m, st, None)
    assert io.keys[:2] == ["b", "s"] and io.keys[-1] == "esc"
    assert st.depots["Krakow 200"]["stage"] == "building"


def test_no_tax_effort_before_the_second_hit(monkeypatch):
    m, st, io, watch, flown, guards = setup(monkeypatch, countdown_at(150))
    st.hits_sent = 1
    assert trial.tax_rounds(io, watch, m, st, None) == 0 and flown == []
    assert trial.tax_with_hit(io, watch, m, st, "Berlin 1000", None) == 0


def test_a_building_follows_a_hit_to_krakow_or_romania(monkeypatch):
    m, st, io, watch, flown, guards = setup(monkeypatch, countdown_at(150))
    trial.tax_with_hit(io, watch, m, st, "Berlin 1000", None)
    trial.tax_with_hit(io, watch, m, st, "Romania 300", None)
    assert [c for _, _, c in flown] == ["Krakow 200", "Romania 300"]
    trial.tax_with_hit(io, watch, m, st, "Berlin 1000", None)   # on its way
    assert len(flown) == 2


def test_a_balkans_hit_always_goes_in_through_romania():
    st = trial.State()
    st.reached |= {"Romania 300", "Factory 7", "Hungary 200"}
    st.sent_at += ["Romania 300", "Factory 7", "Munich 200"]
    assert trial.south_next(st) == "Romania 300"
    st.advised = ("Factory 7", 0.0)
    io = StubIO()
    io.t = 1.0
    assert trial.choose_target(io, None, st) == "Romania 300"


def test_detachments_go_home_once_their_time_is_up():
    m = trial.load_map()
    st = trial.State()
    krakow = at(m, "Krakow 200", 3)
    st.guards["Krakow 200"] = 0.0
    assert trial.guarding(st, m, krakow, 30.0) == krakow
    assert trial.guarding(st, m, krakow, trial.GUARD_KEEP + 1) == set()


def test_survivors_of_a_lost_hit_are_fetched_back():
    m = trial.load_map()
    st = trial.State()
    st.battle = trial.Battle("Berlin 1000", 0)
    w = trial.place(m, "Berlin 1000")
    near_front = blob((w["x"] + 10 * 32, w["y"]), 2)
    st.battle.front = (w["x"] + 10 * 32, w["y"])
    st.battle.samples = [(10, 100, 5, 30), (60, 90, 5, 18)]   # advancing
    assert trial.in_battle(st, m, near_front)          # still being fought
    st.battle.samples.append((90, 10, 5, 18))          # lost
    assert trial.in_battle(st, m, near_front) == set()


def test_a_big_crowd_that_leaves_a_dozen_at_a_time_is_not_stuck(monkeypatch):
    m = trial.load_map()
    st, io = trial.State(), StubIO()
    c, r = (int(v) for v in live.to_drawn(210 * 32, 52 * 32))
    rows = [list(range(r, r + 6)), list(range(r + 1, r + 5)),
            [r + 2, r + 3], [r + 2, r + 3], [r + 2, r + 3], [r + 2, r + 3],
            [r + 2, r + 3]]
    picked = []
    monkeypatch.setattr(trial, "select_group",
                        lambda io_, pixels, st_, watch_=None, margin=None:
                        picked.append(len(pixels)) or True)
    monkeypatch.setattr(trial.live, "clusters", live.clusters)
    io.shot = lambda label, keep=True: None
    for k, ys in enumerate(rows):
        body = {(c + i, y) for i in range(3) for y in ys}
        watch = StubWatch(body | blob(trial.MASS, 6), set())
        io.t += trial.RETRY_IDLE + 1
        trial.gather_idle(io, watch, m, st, {})
    # it shrank twice, so it was ordered more than three times; once it
    # stopped shrinking, three more orders and it is left alone
    assert picked == [18, 12, 6, 6, 6]


def choke_setup(monkeypatch, ours, axis=()):
    m = trial.load_map()
    st, io = trial.State(), StubIO()
    watch = StubWatch(ours, axis)
    sent = []
    monkeypatch.setattr(trial, "select_group",
                        lambda io_, pixels, st_, watch_=None, margin=None:
                        sent.append(set(pixels)) or True)
    monkeypatch.setattr(trial, "attack_move",
                        lambda io_, x, y: sent.append((x, y)))
    monkeypatch.setattr(trial.live, "clusters", live.clusters)
    io.shot = lambda label, keep=True: None
    return m, st, io, watch, sent


def between(m, f):
    a, b = (trial.place(m, n) for n in trial.CHOKE)
    return (a["x"] + f * (b["x"] - a["x"]), a["y"] + f * (b["y"] - a["y"]))


def test_troops_in_the_balkans_choke_go_on_not_back(monkeypatch):
    m = trial.load_map()
    stuck = blob(between(m, 0.5), 4)
    romania = at(m, "Romania 300", 4)
    m, st, io, watch, sent, = choke_setup(monkeypatch, stuck | romania)
    # gathering leaves them alone: they would walk back through the choke
    picked = []
    monkeypatch.setattr(trial, "select_group",
                        lambda io_, pixels, st_, watch_=None, margin=None:
                        picked.append(set(pixels)) or True)
    trial.gather_idle(io, watch, m, st, {})
    assert not any(p & (stuck | romania) for p in picked)
    # Romania is ours and clear: they go on down the road, to Factory 7
    monkeypatch.setattr(trial, "select_group",
                        lambda io_, pixels, st_, watch_=None, margin=None:
                        sent.append(set(pixels)) or True)
    assert trial.clear_choke(io, watch, m, st, stuck | romania, None) >= 2
    f7 = trial.place(m, "Factory 7")
    points = [p for p in sent if isinstance(p, tuple)]
    assert points and all(abs(x - f7["x"]) < 12 * 32 and abs(y - f7["y"]) < 12 * 32
                          for x, y in points)
    # not again at once; again after a while
    io.t += 1
    assert trial.clear_choke(io, watch, m, st, stuck | romania, None) == 0


def test_with_romania_still_held_by_the_enemy_they_attack_it(monkeypatch):
    m = trial.load_map()
    stuck = blob(between(m, 0.3), 4)
    enemy = at(m, "Romania 300", 5)
    m, st, io, watch, sent = choke_setup(monkeypatch, stuck, enemy)
    trial.clear_choke(io, watch, m, st, stuck, None)
    r = trial.place(m, "Romania 300")
    points = [p for p in sent if isinstance(p, tuple)]
    assert points and all(abs(x - r["x"]) < 12 * 32 and abs(y - r["y"]) < 12 * 32
                          for x, y in points)
    assert "Romania 300" not in st.reached


def test_a_new_balkans_hit_clears_the_choke_first(monkeypatch):
    m = trial.load_map()
    stuck = blob(between(m, 0.5), 4)
    m, st, io, watch, sent = choke_setup(monkeypatch, stuck)
    calls = []
    monkeypatch.setattr(trial, "clear_choke",
                        lambda *a, **k: calls.append(k.get("force")) or 0)
    monkeypatch.setattr(trial, "sweep_mass", lambda *a, **k: (0, 0))
    monkeypatch.setattr(trial, "push_front", lambda *a, **k: 0)
    trial.hit(io, watch, m, st, "Romania 300", use_keys=False)
    assert calls == [True]
    calls.clear()
    trial.hit(io, watch, m, st, "Berlin 1000", use_keys=False)
    assert calls == []
