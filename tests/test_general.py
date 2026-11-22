import json
import os

import pytest
from PIL import Image

from bot import general, memory, trial
from eyes import live
from tests.test_trial import FakeGame, near

anthropic = pytest.importorskip("anthropic")
httpx2 = pytest.importorskip("httpx2")

GOOD = {"read": "Our marines are dying at Warsaw.", "fight": "losing",
        "action": "pull_back", "target": "Romania", "group_orders": [],
        "chat": "", "notes": "Berlin hit died at Warsaw; try the south."}


def answer(**changes):
    return {**GOOD, **changes}


def api_reply(text, stop_reason="end_turn"):
    return {"id": "msg_1", "type": "message", "role": "assistant",
            "model": "claude-opus-5-5", "stop_reason": stop_reason,
            "stop_sequence": None,
            "content": [{"type": "text", "text": text}],
            "usage": {"input_tokens": 2000, "output_tokens": 100,
                      "cache_read_input_tokens": 1000,
                      "cache_creation_input_tokens": 0}}


def client_answering(replies, seen):
    """A real SDK client whose network is replaced: each request is
    recorded and answered from `replies` in turn."""
    def handler(request):
        seen.append((request.url.path, dict(request.headers),
                     json.loads(request.content)))
        status, body = replies[min(len(seen), len(replies)) - 1]
        return httpx2.Response(status, json=body)
    return anthropic.Anthropic(
        api_key="test-key", max_retries=0,
        http_client=anthropic.DefaultHttpxClient(
            transport=httpx2.MockTransport(handler)))


def picture():
    return Image.new("RGB", (1920, 1080), (20, 40, 20))


def test_asks_claude_and_reads_the_answer():
    seen = []
    g = general.General(client_answering([(200, api_reply(json.dumps(GOOD)))],
                                         seen), background=False)
    assert g.submit(picture(), "Time in game: 2:00.", camera=(100, 200))
    advice = g.take()
    assert (advice.action, advice.target, advice.fight) == \
        ("pull_back", "Romania", "losing")
    assert advice.camera == (100, 200)
    assert g.take() is None                       # an answer is handed out once
    path, headers, body = seen[0]
    assert body["model"] == "claude-opus-5-5"
    assert body["output_config"]["effort"] == "low"
    assert body["output_config"]["format"]["type"] == "json_schema"
    assert body["fallbacks"] == "default"
    assert "server-side-fallback-2026-07-01" in headers["anthropic-beta"]
    assert body["system"][0]["cache_control"] == {"type": "ephemeral"}
    image, text = body["messages"][0]["content"]
    assert image["source"]["media_type"] == "image/jpeg"
    assert text["text"] == "Time in game: 2:00."
    # 2000 in + 100 out + 1000 cache read, at Opus 5.5 prices
    assert abs(g.spent - (2000 * 4 + 100 * 20 + 1000 * 0.2) / 1e6) < 1e-9
    assert "test-key" not in g.summary()


def test_it_is_given_its_own_notes_answers_and_lessons_back():
    seen = []
    g = general.General(client_answering([(200, api_reply(json.dumps(GOOD)))],
                                         seen), background=False,
                        lessons="Do not feed Berlin in small groups.")
    g.submit(picture(), "Time in game: 2:00.")
    g.submit(picture(), "Time in game: 2:05.")
    first = seen[0][2]["messages"][0]["content"][1]["text"]
    second = seen[1][2]["messages"][0]["content"][1]["text"]
    assert "Do not feed Berlin in small groups." in first
    assert "Berlin hit died at Warsaw" not in first
    assert "Berlin hit died at Warsaw; try the south." in second   # notes
    assert "Time in game: 2:00. -> pull_back" in second            # history
    assert second.endswith("Time in game: 2:05.")
    # the fixed instructions do not change, so they stay cached
    assert seen[0][2]["system"] == seen[1][2]["system"]


def test_writes_lessons_for_the_next_game(tmp_path, monkeypatch):
    monkeypatch.setenv("STARCRAFT_BOT_HOME", str(tmp_path))
    assert memory.load() == ""
    seen = []
    g = general.General(client_answering(
        [(200, api_reply(json.dumps(GOOD))),
         (200, api_reply(json.dumps({"lessons": "Break Warsaw first."})))],
        seen), background=False)
    g.submit(picture(), "x")
    lessons = g.write_lessons("hit at Berlin 1000: stalled")
    assert lessons == "Break Warsaw first."
    assert "hit at Berlin 1000: stalled" in seen[1][2]["messages"][0]["content"]
    memory.save(lessons)
    assert memory.load() == "Break Warsaw first."
    assert "test-key" not in open(tmp_path / "lessons.txt").read()
    memory.save_model("claude-haiku-5-5")
    assert memory.load_model("claude-opus-5-5") == "claude-haiku-5-5"


def test_falls_back_to_a_plain_request_if_fallbacks_are_refused():
    seen = []
    error = {"type": "error", "error": {"type": "invalid_request_error",
                                        "message": "fallbacks not available"}}
    g = general.General(client_answering(
        [(400, error), (200, api_reply(json.dumps(GOOD)))], seen),
        background=False)
    g.submit(picture(), "x")
    assert g.take().action == "pull_back"
    assert "fallbacks" in seen[0][2] and "fallbacks" not in seen[1][2]
    assert g.use_fallbacks is False


def test_refusals_and_bad_answers_give_no_advice():
    for reply in [api_reply("", "refusal"), api_reply("{}"),
                  api_reply(json.dumps(answer(action="dance")))]:
        g = general.General(client_answering([(200, reply)], []),
                            background=False)
        g.submit(picture(), "x")
        assert g.take() is None


def test_stops_at_the_spending_cap_and_drops_stale_advice():
    seen = []
    g = general.General(client_answering([(200, api_reply(json.dumps(GOOD)))],
                                         seen), spend_cap=0.015,
                        background=False)
    assert g.submit(picture(), "x")               # costs about a cent
    assert g.submit(picture(), "x")               # passes the cap
    assert not g.submit(picture(), "x")           # refused: cap reached
    assert len(seen) == 2
    now = [100.0]
    g2 = general.General(client_answering(
        [(200, api_reply(json.dumps(GOOD)))], []), clock=lambda: now[0],
        background=False)
    g2.submit(picture(), "x")
    now[0] += general.STALE_AFTER + 1
    assert g2.take() is None                      # too old to act on


class Scripted:
    """A general that gives one fixed answer whenever asked."""
    def __init__(self, **changes):
        self.data = answer(**{"action": "keep_massing", "target": "Berlin",
                              **changes})
        self.asked, self.reports, self.waiting = 0, [], None
        self.lessons_asked = None

    def submit(self, picture, status, camera=None):
        self.asked += 1
        self.reports.append(status)
        self.waiting = general.Advice(self.data, 0, 0.1, camera)
        return True

    def take(self):
        advice, self.waiting = self.waiting, None
        return advice

    def write_lessons(self, outcome):
        self.lessons_asked = outcome
        return "lesson"

    def summary(self):
        return "general: scripted"


def test_the_general_chooses_targets_and_is_asked_all_through():
    m = trial.load_map()
    g = FakeGame(m)
    scripted = Scripted(action="hit_now", target="Romania")
    saved = []
    result = trial.run(g, m, general=scripted, save_lessons=saved.append)
    # the opening too: the first hit goes where it said
    assert result["targets"][0] == "Romania 300"
    assert "No hit has been sent yet" in scripted.reports[0]
    assert any("Our last hit was sent at Romania 300" in r
               for r in scripted.reports)
    assert scripted.asked > 20                      # all through, hits included
    assert "Number keys holding groups" in scripted.reports[-1]
    # and at the end it was asked for lessons, which were saved
    assert "hit at Romania 300" in scripted.lessons_asked
    assert saved == ["lesson"]


def test_lessons_are_written_even_when_the_run_is_stopped():
    m = trial.load_map()
    g = FakeGame(m)
    real_sleep = g.sleep

    def sleep(s):
        real_sleep(s)
        if g.time > 30:
            raise trial.Stopped("stopped with F9")
    g.sleep = sleep
    scripted = Scripted()
    saved = []
    with pytest.raises(trial.Stopped):
        trial.run(g, m, general=scripted, save_lessons=saved.append)
    assert saved == ["lesson"]


def game_with_groups(m):
    g = FakeGame(m)
    g.camera = live.camera_after_click(*live.minimap_point(*trial.MASS))
    st = trial.State()
    st.ground_keys, st.air_keys = ["1", "2"], ["9"]
    g.groups = {"1": g.units[0:3], "2": g.units[3:6], "9": g.units[6:8]}
    return g, st


def test_group_orders_are_carried_out():
    m = trial.load_map()
    g, st = game_with_groups(m)
    warsaw = trial.place(m, "Warsaw 200")
    order = lambda **o: {"group": "1", "order": "attack_move",
                         "place": "none", "x": 0, "y": 0, **o}
    # a named place, for one key
    assert trial.carry_out(g, m, st, order(place="Warsaw"), None)
    assert all(near(u["to"], (warsaw["x"], warsaw["y"]), 12)
               for u in g.units[0:3])
    assert not any(near(u["to"], (warsaw["x"], warsaw["y"]), 12)
                   for u in g.units[3:6])
    # "air" means the air keys; move goes to the mass without fighting
    assert trial.carry_out(g, m, st, order(group="air", order="move",
                                           place="mass"), None)
    assert all(near(u["to"], trial.MASS, 12) for u in g.units[6:8])
    # hold
    assert trial.carry_out(g, m, st, order(group="2", order="hold"), None)
    assert all(u.get("held") for u in g.units[3:6])
    # a point in the 1280 x 720 picture becomes a click on the real screen
    cam = (5000.0, 2400.0)
    assert trial.carry_out(g, m, st, order(order="attack_point",
                                           x=640, y=300), cam)
    assert g.point_orders[-1] == ("attack", 960, 450)
    assert trial.carry_out(g, m, st, order(group="9", order="yamato_point",
                                           x=400, y=200), cam)
    assert g.point_orders[-1] == ("yamato", 600, 300)
    # refused: a point on the panels, no camera, or a key with no group
    assert not trial.carry_out(g, m, st, order(order="attack_point",
                                               x=640, y=690), cam)
    assert not trial.carry_out(g, m, st, order(order="attack_point",
                                               x=640, y=300), None)
    assert not trial.carry_out(g, m, st, order(group="7", place="Warsaw"), None)


def test_chat_is_typed_to_allies_but_not_too_often():
    m = trial.load_map()
    g, st = game_with_groups(m)
    assert trial.say(g, st, "going  Berlin\nnow")
    assert g.typed == ["going  Berlinnow"]           # one line, plain letters
    assert not trial.say(g, st, "again")             # too soon
    g.time += trial.CHAT_EVERY + 1
    assert trial.say(g, st, "x" * 200)
    assert len(g.typed[-1]) == 60


def test_the_generals_orders_reach_the_groups_in_a_game():
    m = trial.load_map()
    g = FakeGame(m)
    scripted = Scripted(group_orders=[
        {"group": "air", "order": "move", "place": "mass", "x": 0, "y": 0}],
        chat="massing for Berlin")
    logs = []
    g.log = lambda text, quiet=False: logs.append(text)
    trial.run(g, m, general=scripted)
    assert any("1 of 1 group orders given" in l for l in logs)
    assert g.typed and g.typed[0] == "massing for Berlin"
    assert len(g.typed) < 15                         # not every few seconds


def test_the_bot_defends_when_the_axis_reaches_the_mass():
    m = trial.load_map()
    g, st = game_with_groups(m)
    for u in g.units[:6]:
        u["to"] = (100 * 32, 89 * 32)             # away at Berlin
    assert trial.recall(g, st, "test")
    assert all(near(u["to"], trial.MASS, 12) for u in g.units[:8])
    assert not trial.recall(g, st, "again")       # not twice in a row
