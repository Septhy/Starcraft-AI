import json
import os

import pytest
from PIL import Image

from bot import general, trial
from eyes import live
from tests.test_trial import FakeGame, near, real_game_screen

anthropic = pytest.importorskip("anthropic")
httpx2 = pytest.importorskip("httpx2")

GOOD = {"read": "Our marines are dying at Berlin.", "fight": "losing",
        "action": "pull_back", "target": "Romania"}


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
    assert g.submit(picture(), "Time in game: 2:00.")
    advice = g.take()
    assert (advice.action, advice.target, advice.fight) == \
        ("pull_back", "Romania", "losing")
    assert g.take() is None                       # advice is handed out once
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
                  api_reply(json.dumps({**GOOD, "action": "dance"}))]:
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
    """A general that gives one fixed piece of advice whenever asked."""
    def __init__(self, action, target):
        self.action, self.target, self.asked, self.reports = action, target, 0, []
        self.waiting = None

    def submit(self, picture, status):
        self.asked += 1
        self.reports.append(status)
        self.waiting = general.Advice(
            {"read": "test", "fight": "even", "action": self.action,
             "target": self.target}, 0, 0.1)
        return True

    def take(self):
        advice, self.waiting = self.waiting, None
        return advice

    def summary(self):
        return "general: scripted"


def test_the_bot_follows_the_generals_advice():
    m = trial.load_map()
    # "hit_now, Romania": later hits go to Romania without waiting long
    g = FakeGame(m)
    scripted = Scripted("hit_now", "Romania")
    result = trial.run(g, m, general=scripted)
    assert scripted.asked > 3
    assert "Romania 300" in result["targets"][1:]
    assert "Our last hit went to Berlin 1000" in scripted.reports[0]
    # "pull_back": the number-key groups are ordered back to the mass
    g = FakeGame(m)
    scripted = Scripted("pull_back", "Berlin")
    logs = []
    g.log = lambda text, quiet=False: logs.append(text)
    trial.run(g, m, general=scripted)
    assert any("army recalled" in l and "general" in l for l in logs)


def test_the_bot_defends_when_the_axis_reaches_the_mass():
    m = trial.load_map()
    g = FakeGame(m)
    st = trial.State()
    st.ground_keys = ["1", "2"]
    g.selected = [g.units[0]]
    g.groups = {"1": [g.units[0]], "2": [g.units[1]]}
    for u in g.units[:2]:
        u["to"] = (100 * 32, 89 * 32)             # away at Berlin
    logs = []
    g.log = lambda text, quiet=False: logs.append(text)
    assert trial.recall(g, st, "test")
    assert all(near(u["to"], trial.MASS, 12) for u in g.units[:2])
    assert not trial.recall(g, st, "again")       # not twice in a row
