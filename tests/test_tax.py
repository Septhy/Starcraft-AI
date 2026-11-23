"""Tax cities, and fetching every idle body for the next hit."""
from bot import team, trial
from eyes import live
from tests.test_trial import StubIO, StubWatch, blob


def setup(monkeypatch, clock_seconds=0.0, ours=(), axis=()):
    m = trial.load_map()
    st, io = trial.State(), StubIO()
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


def test_a_city_already_held_is_left_alone(monkeypatch):
    m = trial.load_map()
    m, st, io, watch, flown, _ = setup(
        monkeypatch, countdown_at(150), ours=at(m, "Krakow 200", 3))
    trial.tax_rounds(io, watch, m, st, None)
    assert [c for _, _, c in flown] == ["Romania 300"]


def test_factory_7_sets_off_at_one_minute_and_must_arrive_by_three(monkeypatch):
    for c, goes in [(150, False), (100, False), (60, True), (20, True),
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
