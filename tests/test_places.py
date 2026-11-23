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
