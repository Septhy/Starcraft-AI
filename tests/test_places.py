"""Massing where the allies say: place names and walking."""
import pytest

from bot import places, team, trial
from tests.test_trial import StubIO


@pytest.mark.parametrize("name", [
    "London", "Southampton", "Wales", "Scotland", "Ireland", "Shetland",
    "Faeroe", "America", "Halifax", "Newfoundland", "Corsica", "Sardinia",
    "Sicily", "Crete"])
def test_islands_and_overseas_cannot_be_walked_to(name):
    m = trial.load_map()
    real = places.resolve(m, name)
    assert real, name
    c = trial.place(m, real)
    assert not places.walkable(c["x"], c["y"]), name


@pytest.mark.parametrize("name", [
    "Smolensk", "Moscow", "Warsaw", "Berlin", "Paris", "Madrid", "Lisbon",
    "Gibraltar", "Rome", "Oslo", "Stockholm", "Helsinki", "Belgrade", "Kiev",
    "Istanbul", "Baghdad", "Cairo", "Tobruk", "Odessa", "Romania"])
def test_the_mainland_can_be_walked_to(name):
    m = trial.load_map()
    real = places.resolve(m, name)
    assert real, name
    c = trial.place(m, real)
    assert places.walkable(c["x"], c["y"]), name


def test_place_names_and_other_names():
    m = trial.load_map()
    assert places.resolve(m, "warsaw") == "Warsaw 200"
    assert places.resolve(m, "Warsaw 200") == "Warsaw 200"
    assert places.resolve(m, "Belgrade") == "Serbia 100"
    assert places.resolve(m, "Kiev") == "Ukraine 200"
    assert places.resolve(m, "Capital City 13") is None     # not a city
    assert places.resolve(m, "Narnia") is None
    names = places.names_for_chat(m)
    assert "Warsaw" in names and "Belgrade" in names and "Factory 7" not in names


def order(place, said=None):
    return team.Order({"colour": "teal", "kind": "mass", "front": "none",
                       "wait_seconds": -1, "until_clock": "", "place": place,
                       "said": said or f"@R mass at {place}"})


def test_mass_orders_move_the_massing_place_or_are_refused(monkeypatch):
    m = trial.load_map()
    monkeypatch.setattr(trial, "MASS", trial.HOME_MASS)
    said = []
    monkeypatch.setattr(trial, "say", lambda io, st, text, force=False:
                        said.append(text))
    io, st = StubIO(), trial.State()
    trial.move_mass(io, m, st, order("Warsaw"))
    w = trial.place(m, "Warsaw 200")
    assert trial.MASS == (w["x"], w["y"]) and said[-1] == "massing at Warsaw"
    trial.move_mass(io, m, st, order("London"))
    assert said[-1] == "I can't mass there"
    assert trial.MASS == (w["x"], w["y"])           # unchanged
    trial.move_mass(io, m, st, order("Narnia"))
    assert said[-1] == "I can't find that place"
    trial.move_mass(io, m, st, order("home"))
    assert trial.MASS == trial.HOME_MASS and said[-1] == "massing at Smolensk"


def test_the_team_passes_mass_orders_on():
    got = []
    t = team.Team(lambda s: None, lambda s: None, on_mass=got.append)
    t.heard(order("Odessa"), 10)
    assert got and got[0].place == "Odessa"
    assert team.addressed("@R mass at Odessa")


def go(place, wait=-1, said=None):
    return team.Order({"colour": "orange", "kind": "go", "front": "none",
                       "wait_seconds": wait, "until_clock": "", "place": place,
                       "said": said or f"@R hit {place}"})


def a_team(m, said):
    return team.Team(said.append, lambda s: None,
                     resolve=lambda text: trial.place_for_hit(m, text))


def test_hit_a_city_now_or_later_or_refused():
    m = trial.load_map()
    said = []
    t = a_team(m, said)
    t.heard(go("Warsaw"), 100)
    assert t.gate(100, False, "balks") == "go"
    assert t.target == "Warsaw 200" and said == ["gone Warsaw"]
    said.clear()
    t.heard(go("Odessa", wait=120, said="@R hit Odessa in 2"), 200)
    went = None
    for s in range(200, 400):
        if t.gate(s, False, "east") == "go":
            went = s
            break
    assert went == 320 and t.target == "Odessa 200"
    assert said == ["gone Odessa in 30 seconds", "gone Odessa"]
    said.clear()
    t.heard(go("London"), 500)
    assert said == ["I can't hit there"] and t.ally_go is None
    t.heard(go("Narnia"), 501)
    assert said[-1] == "I can't find that place"
    # an east or balks hit names no city
    t.heard(team.Order({"colour": "teal", "kind": "go", "front": "east",
                        "wait_seconds": -1, "until_clock": "", "place": "",
                        "said": "@R hit east"}), 600)
    assert t.gate(600, False, "balks") == "go" and t.target is None


def test_the_hit_goes_to_the_city_named(monkeypatch):
    m = trial.load_map()
    st, io = trial.State(), StubIO()
    st.clock = team.GameClock(io.now)
    said = []
    st.team = a_team(m, said)
    st.team.heard(go("Krakow"), st.clock.time())
    assert trial.team_gate(io, None, m, st, False, "Berlin 1000") == "go"
    assert st.chosen_target == "Krakow 200"


def test_status_says_supply_mass_plan_and_when_the_next_hit_goes(monkeypatch):
    m = trial.load_map()
    monkeypatch.setattr(trial, "MASS", trial.HOME_MASS)
    st, io = trial.State(), StubIO()
    st.clock = team.GameClock(io.now)
    st.clock.value = 600                            # 10:00 on the game clock
    st.team = a_team(m, [])
    st.supply_seen = ((185, 200), 0.0)
    st.strength, st.need = 120, 140
    # grown from 60 to 120 men in the last minute: 1 man a second, so
    # 20 more in 20 s, then the 30 s warning: about 10:50
    st.strength_log = [(540.0, 60), (570.0, 90), (600.0, 120)]
    first, second = trial.status_lines(io, m, st)
    assert first == "Pop 185/200. Mass: Smolensk."
    assert second.startswith("Plan: 120/140 men, ") and \
        second.endswith(". Next hit est. 10:50."), second
    assert len(first) <= 60 and len(second) <= 60
    plan = lambda: trial.status_lines(io, m, st)[1]
    # not growing: no telling
    st.strength_log = [(540.0, 120), (600.0, 120)]
    assert plan().endswith("Next hit est. unknown.")
    # at full supply: as soon as the warning is out
    st.capped = True
    assert plan().endswith("Next hit est. 10:30.")
    st.capped = False
    # the allies said wait a minute: the hit 30 s after the wait, if the
    # army is ready by then
    st.team.heard(team.Order({"colour": "teal", "kind": "stop", "front": "none",
                              "wait_seconds": 60, "until_clock": "",
                              "place": "", "said": "@R wait 1"}), 600)
    st.strength_log = [(540.0, 60), (570.0, 90), (600.0, 120)]
    assert plan() == "Plan: waiting. Next hit est. 11:30."
    # wait 5: the army is ready long before; the wait decides
    st.team.hold_until = 900
    assert plan() == "Plan: waiting. Next hit est. 15:30."
    # a short wait, but a slow-growing army: the army decides
    st.team.hold_until = 610
    st.strength_log = [(510.0, 105), (600.0, 120)]  # 1 man every 6 s
    assert plan() == "Plan: waiting. Next hit est. 12:30."
    st.strength_log = [(540.0, 120), (600.0, 120)]  # not growing
    assert plan() == "Plan: waiting. Next hit est. unknown."
    # an announced hit: its time
    st.team.hold_until = None
    st.team.gate(600, True, "balks")
    assert plan() == "Plan: gone balks. Next hit est. 10:30."
    # massing elsewhere
    w = trial.place(m, "Warsaw 200")
    monkeypatch.setattr(trial, "MASS", (w["x"], w["y"]))
    assert trial.status_lines(io, m, st)[0] == "Pop 185/200. Mass: Warsaw."


def test_reset_drops_every_order_and_masses_at_smolensk(monkeypatch):
    m = trial.load_map()
    monkeypatch.setattr(trial, "MASS", trial.HOME_MASS)
    said = []
    monkeypatch.setattr(trial, "say", lambda io, st, text, force=False:
                        said.append(text))
    st, io = trial.State(), StubIO()
    st.team = team.Team(said.append, lambda s: None,
                        on_mass=lambda o: trial.move_mass(io, m, st, o),
                        on_reset=lambda: trial.reset_orders(io, m, st),
                        resolve=lambda text: trial.place_for_hit(m, text))
    st.team.heard(order("Warsaw"), 0)
    st.team.heard(team.Order({"colour": "teal", "kind": "stop", "front": "none",
                              "wait_seconds": 300, "until_clock": "",
                              "place": "", "said": "@R wait 5"}), 1)
    st.planned_target = "Romania 300"
    assert trial.MASS != trial.HOME_MASS and st.team.held(2)
    st.team.heard(team.Order({"colour": "purple", "kind": "reset",
                              "front": "none", "wait_seconds": -1,
                              "until_clock": "", "place": "",
                              "said": "@R reset"}), 2)
    assert trial.MASS == trial.HOME_MASS and not st.team.held(3)
    assert st.planned_target is None and st.team.ally_go is None
    assert said[-1].startswith("reset")
