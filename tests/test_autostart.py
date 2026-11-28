"""The bot starts by itself when a game begins; F9 only stops it."""
from PIL import Image

from bot import autostart
from eyes import live


def setup(monkeypatch, state):
    monkeypatch.setattr(autostart.live, "minimap_showing", lambda pic: state["map"])
    monkeypatch.setattr(autostart, "read_clock", lambda pic: state["clock"])
    return Image.new("RGB", live.SCREEN)


def test_a_game_that_has_just_begun_starts_the_bot_once(monkeypatch):
    state = {"map": False, "clock": None}
    pic = setup(monkeypatch, state)
    s = autostart.Starter()
    assert not s.look(pic)                      # the lobby: no minimap
    state.update(map=True, clock=1)
    assert s.look(pic)                          # the game begins: start
    assert not s.look(pic)                      # and only once
    # stopped with F9 three seconds in: it does not start itself anew
    s.played()
    state["clock"] = 4
    assert not s.look(pic) and not s.look(pic)
    # that game goes on, then a new one begins
    state["clock"] = 300
    assert not s.look(pic)
    state.update(map=False, clock=None)
    assert not s.look(pic)
    state.update(map=True, clock=0)
    assert s.look(pic)


def test_a_game_well_under_way_does_not_start_it(monkeypatch):
    state = {"map": True, "clock": 161}
    pic = setup(monkeypatch, state)
    s = autostart.Starter()
    assert not s.look(pic)
    state["clock"] = None                       # the clock cannot be read
    assert not s.look(pic)
    assert not autostart.game_begun(None)
    assert not autostart.game_begun(Image.new("RGB", (800, 600)))   # not the game's size


def test_f9_no_longer_starts_the_bot():
    import inspect
    from bot import app
    src = inspect.getsource(app.main)
    assert "starter.look(" in src and "Start now" in src
    assert "GetAsyncKeyState(STOP_KEY)" not in src      # F9 is only read while playing
