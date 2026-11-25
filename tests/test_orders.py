"""The allies' "@R tax <city>" and "@R upgrade"."""
from PIL import Image

from bot import team, trial
from tests.test_trial import StubIO, StubWatch, blob


class O:
    def __init__(self, kind, place="", colour="teal", said="@R x"):
        self.kind, self.place, self.colour, self.said = kind, place, colour, said


def said(monkeypatch):
    out = []
    monkeypatch.setattr(trial, "say", lambda io, st, text, force=False:
                        out.append(text))
    return out


def money_io(values):
    io = StubIO()
    vals = iter(values)
    io.shot = lambda label, keep=True: Image.new("RGB", (1920, 1080))
    return io, vals


def test_upgrade_starts_both_when_the_money_is_there(monkeypatch):
    m = trial.load_map()
    out = said(monkeypatch)
    st = trial.State()
    io = StubIO()
    io.shot = lambda label, keep=True: None
    money = iter([1000, 900, 800])
    monkeypatch.setattr(trial.numbers, "read_minerals", lambda pic: next(money))
    picked = []
    monkeypatch.setattr(trial, "select_building",
                        lambda io_, b: picked.append((b["x"] // 32, b["y"] // 32)) or True)
    trial.upgrade_order(io, m, st)
    assert io.keys == ["w", "a"] and len(set(picked)) == 2   # one bay each
    assert out == ["upgrading infantry weapons and armor"]
    assert st.upgrade_level == {"weapons": 1, "armor": 1} and not st.upgrade_wanted


def test_upgrade_waits_for_the_money_and_says_so(monkeypatch):
    m = trial.load_map()
    out = said(monkeypatch)
    st = trial.State()
    io = StubIO()
    io.shot = lambda label, keep=True: None
    money = iter([50, 400, 300, 200])
    monkeypatch.setattr(trial.numbers, "read_minerals", lambda pic: next(money))
    monkeypatch.setattr(trial, "select_building", lambda io_, b: True)
    trial.upgrade_order(io, m, st)
    assert out == ["I'll upgrade infantry when I have the resources"]
    assert io.keys == [] and st.upgrade_wanted == {"weapons", "armor"}
    io.t += trial.UPGRADE_EVERY                     # the money has come
    assert trial.upgrade_step(io, m, st)
    assert io.keys == ["w", "a"] and out[-1] == "upgrading infantry weapons and armor"


def test_tax_order_secures_the_city_then_builds_a_depot_then_comes_back(monkeypatch):
    m = trial.load_map()
    out = said(monkeypatch)
    st, io = trial.State(), StubIO()
    io.shot = lambda label, keep=True: None
    warsaw = trial.place(m, "Warsaw 200")
    xy = (warsaw["x"], warsaw["y"])
    guards, depots = [], []

    def guard(io_, watch, mapdata, st_, name, picture):
        guards.append(name)
        return True
    monkeypatch.setattr(trial, "send_guard", guard)

    def depot(io_, watch, mapdata, st_, name, ours, cc_tile=None, then_home=False):
        depots.append((name, cc_tile, then_home))
        st_.depots.setdefault(name, {"stage": "walking", "due": io_.now() + 30})
        return 1
    monkeypatch.setattr(trial, "depot_at", depot)
    back = []
    monkeypatch.setattr(trial, "select_group", lambda *a, **k: True)
    monkeypatch.setattr(trial, "attack_move", lambda io_, x, y: back.append((x, y)))
    trial.tax_order(io, None, m, st, O("tax", "Warsaw"))
    assert out == ["taxing Warsaw"] and st.tax_job["city"] == "Warsaw 200"
    # enemies there: a detachment first
    watch = StubWatch(blob(xy, 2), blob(xy, 3))
    trial.tax_order_step(io, watch, m, st, None)
    assert guards == ["Warsaw 200"] and depots == []
    # cleared: an SCV from Moscow builds the depot, and goes home after
    watch = StubWatch(blob(xy, 3), set())
    trial.tax_order_step(io, watch, m, st, None)
    trial.tax_order_step(io, watch, m, st, None)
    assert depots[0] == ("Warsaw 200", trial.MOSCOW_CC, True)
    # the depot stands: taxed; the detachment walks back near the mass
    st.depots["Warsaw 200"]["stage"] = "done"
    trial.tax_order_step(io, StubWatch(blob(xy, 3), set()), m, st, None)
    assert out[-1] == "Warsaw taxed" and st.tax_job is None
    assert back and all(abs(x - trial.MASS[0]) <= trial.BACK_NEAR * 32
                        and abs(y - trial.MASS[1]) <= trial.BACK_NEAR * 32
                        for x, y in back)


def test_a_failed_tax_order_is_said_and_not_tried_again(monkeypatch):
    m = trial.load_map()
    out = said(monkeypatch)
    st, io = trial.State(), StubIO()
    io.shot = lambda label, keep=True: None
    calls = []

    def depot(io_, watch, mapdata, st_, name, ours, cc_tile=None, then_home=False):
        calls.append(1)
        if len(calls) == 1:
            st_.depots[name] = {"stage": "walking", "due": io_.now()}
        return 1
    monkeypatch.setattr(trial, "depot_at", depot)
    trial.tax_order(io, None, m, st, O("tax", "Kiev"))
    watch = StubWatch(set(), set())
    trial.tax_order_step(io, watch, m, st, None)    # clear: to the depot
    trial.tax_order_step(io, watch, m, st, None)    # the SCV goes
    st.depots.clear()                               # ... and never builds
    trial.tax_order_step(io, watch, m, st, None)
    assert out[-1] == "couldn't tax Ukraine" and st.tax_job is None
    trial.tax_order_step(io, watch, m, st, None)    # nothing more
    assert len(calls) == 1


def test_the_allies_orders_reach_the_bot():
    got = []
    t = team.Team(lambda s: None, lambda s: None,
                  on_tax=lambda o: got.append(("tax", o.place)),
                  on_upgrade=lambda: got.append(("upgrade",)))
    t.heard(team.Order({"colour": "teal", "kind": "tax", "place": "Warsaw",
                        "said": "@R tax Warsaw"}), 100)
    t.heard(team.Order({"colour": "purple", "kind": "upgrade",
                        "said": "@R upgrade"}), 100)
    assert got == [("tax", "Warsaw"), ("upgrade",)]


def test_the_scv_builds_by_the_beacon_and_then_goes_home_to_moscow(monkeypatch):
    m = trial.load_map()
    st, io = trial.State(), StubIO()
    io.shot = lambda label, keep=True: None
    monkeypatch.setattr(trial, "look_at", lambda io_, x, y, wait=0: (x, y))
    monkeypatch.setattr(trial.live, "units_selected", lambda pic: True)
    monkeypatch.setattr(trial.live, "selected_count", lambda pic: 1)
    money = iter([1000, 1000, 1000, 900])            # the second spot takes it
    monkeypatch.setattr(trial.numbers, "read_minerals", lambda pic: next(money))
    job = {"stage": "walking", "due": io.t}
    st.depots["Warsaw 200"] = job
    w = trial.place(m, "Warsaw 200")
    assert trial.depot_by_order(io, m, st, "Warsaw 200", w["x"], w["y"], job) == 1
    assert job["stage"] == "building"
    assert io.keys.count("esc") == 1                 # the first spot refused
    mx, my = trial.MOSCOW_CC
    home = trial.live.minimap_point(mx * 32, my * 32)
    assert io.keys[-1] == "m" and io.clicks[-1] == (*home, "shift")
