"""Talking with the team: announcing hits and doing what the allies say."""
import glob
import json
import os

import pytest
from PIL import Image, ImageDraw

from bot import team, trial
from eyes import clock
from tests.test_trial import FakeGame

DATA = os.path.join(os.path.dirname(__file__), "data")


class Chat:
    def __init__(self):
        self.said, self.notes = [], []

    def say(self, text):
        self.said.append(text)

    def log(self, text):
        self.notes.append(text)


def order(kind, front="none", wait=-1, until="", colour="teal", said="x"):
    return team.Order({"colour": colour, "kind": kind, "front": front,
                       "wait_seconds": wait, "until_clock": until,
                       "said": said})


def run_until(t, chat, now, end, ready=True, front="east", step=1):
    """Call gate() each second from `now` to `end`; the clock time of the
    first "go", or None."""
    while now <= end:
        if t.gate(now, ready, front) == "go":
            return now
        now += step
    return None


def test_a_hit_is_announced_and_goes_thirty_seconds_later():
    chat = Chat()
    t = team.Team(chat.say, chat.log)
    assert t.gate(100, False, "east") == "mass" and chat.said == []
    went = run_until(t, chat, 100, 200)
    assert went == 130
    assert chat.said == ["gone east in 30 seconds", "gone east"]
    # then back to the usual: nothing more until it is ready again
    assert t.gate(131, False, "east") == "mass" and len(chat.said) == 2
    chat.said.clear()
    assert run_until(t, chat, 300, 400, front="balks") == 330
    assert chat.said == ["gone balks in 30 seconds", "gone balks"]


@pytest.mark.parametrize("word", ["no", "don't", "stop", "wait", "halt"])
def test_an_ally_saying_stop_holds_the_hit_two_minutes(word):
    chat = Chat()
    t = team.Team(chat.say, chat.log)
    t.gate(100, True, "east")                       # announced, goes at 130
    t.heard(order("stop", said=word), 110)
    went = run_until(t, chat, 111, 400)
    # no hit for two minutes of the game clock, then a new 30 seconds
    assert went == 110 + 120 + 30
    assert chat.said == ["gone east in 30 seconds",
                         "gone east in 30 seconds", "gone east"]


def test_an_ally_naming_how_long_to_wait_is_obeyed_exactly():
    chat = Chat()
    t = team.Team(chat.say, chat.log)
    t.gate(100, True, "east")
    t.heard(order("stop", wait=45, said="wait 45"), 105)
    assert run_until(t, chat, 106, 400) == 105 + 45 + 30
    # or a time on the game clock
    t2 = team.Team(chat.say, chat.log)
    t2.gate(100, True, "east")
    t2.heard(order("stop", until="03:00", said="wait till 3:00"), 110)
    assert run_until(t2, chat, 111, 400) == 180 + 30


def test_hit_east_or_balks_with_no_time_goes_now_and_overrides_the_plan():
    chat = Chat()
    t = team.Team(chat.say, chat.log)
    # Russia's own plan is not ready, and was going east
    t.heard(order("go", front="balks", said="@R hit balks"), 200)
    went = run_until(t, chat, 200, 400, ready=False, front="east")
    assert went == 200 and t.front == "balks"
    assert chat.said == ["gone balks"]
    # an announced hit is sent at once too
    chat2 = Chat()
    t2 = team.Team(chat2.say, chat2.log)
    t2.gate(300, True, "east")
    t2.heard(order("go", front="east", said="@R hit east"), 305)
    assert t2.gate(305, True, "east") == "go"
    assert chat2.said == ["gone east in 30 seconds", "gone east"]


def test_go_with_no_front_named_goes_on_russias_own_front():
    chat = Chat()
    t = team.Team(chat.say, chat.log)
    t.heard(order("go", front="none", said="@R go"), 50)
    assert t.gate(50, False, "balks") == "go" and t.front == "balks"


@pytest.mark.parametrize("text, meant", [
    ("@R hit east", True), ("@r wait", True), ("@Russ go balks", True),
    ("@Russia stop", True), ("  @RUSSIA: no", True), ("@R, go", True),
    ("hit east", False), ("rus go east", False), ("@Romania go", False),
    ("wait @R", False), ("@Rus go", False), ("", False)])
def test_only_messages_tagged_for_russia_are_orders(text, meant):
    assert team.addressed(text) == meant


def test_go_in_two_waits_two_minutes_then_hits_that_way():
    chat = Chat()
    t = team.Team(chat.say, chat.log)
    t.gate(100, True, "balks")                      # Russia meant the Balkans
    t.heard(order("go", front="east", wait=120, said="go east in 2"), 105)
    # its own announcement is dropped; the allies' time stands
    went = run_until(t, chat, 106, 400, ready=True, front="balks")
    assert went == 225 and t.front == "east"
    assert chat.said == ["gone balks in 30 seconds",
                         "gone east in 30 seconds", "gone east"]


def test_bot_keeps_building_while_the_allies_hold_it(monkeypatch):
    """The massing loop goes on (training, gathering) while held."""
    chat = Chat()
    t = team.Team(chat.say, chat.log)
    t.heard(order("stop", wait=60), 0)
    assert all(t.gate(s, True, "east") == "mass" for s in range(0, 60))


# ------------------------------------------------------------ the clock
def clock_screen(path):
    s = Image.new("RGB", (1920, 1080))
    s.paste(Image.open(path).convert("RGB"), (970, 812))
    return s


def test_reads_the_game_clock_at_the_bottom():
    paths = sorted(glob.glob(os.path.join(DATA, "clock", "*.png")))
    assert len(paths) >= 40
    for p in paths:
        m, s = os.path.basename(p)[3:-4].split("-")
        assert clock.read_clock(clock_screen(p)) == int(m) * 60 + int(s), p
    assert clock.read_clock(Image.new("RGB", (1920, 1080))) is None


def test_game_clock_carries_on_between_readings():
    now = [10.0]
    c = team.GameClock(lambda: now[0])
    p = sorted(glob.glob(os.path.join(DATA, "clock", "*.png")))[20]
    c.update(clock_screen(p))                       # shows 05:21
    assert c.time() == 321
    now[0] += 4
    assert c.update(Image.new("RGB", (1920, 1080))) == 325


# ------------------------------------------------------------ chat
def chat_picture(lines):
    """A screen with chat lines drawn as the game does: white text with
    a dark shadow, low on the left."""
    s = Image.new("RGB", (1920, 1080), (40, 70, 40))
    d = ImageDraw.Draw(s)
    for k, text in enumerate(lines):
        y = 620 - 37 * (len(lines) - 1 - k)
        for dx in range(0, 3):
            d.text((24 + dx + 2, y + 2), text, fill=(0, 0, 0))
        d.text((24, y), text, fill=(235, 235, 235))
    return s.resize((1920, 1080))


def test_chat_signature_sees_new_text_only():
    empty = team.chat_signature(Image.new("RGB", (1920, 1080), (40, 70, 40)))
    one = team.chat_signature(chat_picture(["Norway: no wait"] * 1))
    two = team.chat_signature(chat_picture(["Norway: no wait",
                                            "UK: go balks in 2"]))
    assert len(empty) == 0 and len(one) >= 3 and len(two ^ one) >= 3


anthropic = pytest.importorskip("anthropic")
httpx2 = pytest.importorskip("httpx2")


def chat_client(answer, seen):
    from tests.test_general import api_reply, client_answering
    return client_answering([(200, api_reply(json.dumps(answer)))], seen)


def test_ears_take_orders_only_from_allies_and_only_once():
    seen = []
    answer = {"lines": [{"colour": "orange", "text": "Norway: wait"},
                        {"colour": "red", "text": "Germany: stop"}],
              "orders": [{"colour": "orange", "kind": "stop", "front": "none",
                          "wait_seconds": -1, "until_clock": "",
                          "said": "@R wait"}]}
    now = [0.0]
    ears = team.ChatEars(chat_client(answer, seen), clock=lambda: now[0],
                         background=False)
    assert ears.listen(chat_picture(["Norway: wait"]), 100)
    got = ears.orders(100)
    assert [(o.colour, o.kind) for o in got] == [("orange", "stop")]
    # the request shows only the chat strip, with the clock
    body = seen[0][2]
    assert body["model"] == team.CHAT_MODEL
    assert "Game clock now: 01:40" in body["messages"][0]["content"][1]["text"]
    # the same line still on screen is not a second order
    now[0] += 2
    assert ears.listen(chat_picture(["Norway: wait", "UK: ok"]), 102)
    assert ears.orders(102) == []
    assert ("red", "Germany: stop") in [(c, t) for _, c, t in ears.lines(102)]
    # an ally's message without the tag is never an order, whatever the
    # reply says
    untagged = {"lines": [], "orders": [{"colour": "teal", "kind": "go",
                                         "front": "east", "wait_seconds": -1,
                                         "until_clock": "", "said": "go east"}]}
    ears3 = team.ChatEars(chat_client(untagged, []), background=False)
    ears3.listen(chat_picture(["UK: go east"]), 60)
    assert ears3.orders(60) == []
    # an enemy's "order" never gets through, whatever the reply says
    bad = {"lines": [], "orders": [{"colour": "red", "kind": "stop",
                                    "front": "none", "wait_seconds": -1,
                                    "until_clock": "", "said": "@R stop"}]}
    ears2 = team.ChatEars(chat_client(bad, []), background=False)
    ears2.listen(chat_picture(["Germany: stop"]), 50)
    assert ears2.orders(50) == []


def test_the_bot_announces_its_first_hit_in_a_game():
    m = trial.load_map()
    g = FakeGame(m)
    trial.run(g, m)
    typed = getattr(g, "typed", [])
    assert "gone east in 30 seconds" in typed and "gone east" in typed
    assert typed.index("gone east in 30 seconds") < typed.index("gone east")
