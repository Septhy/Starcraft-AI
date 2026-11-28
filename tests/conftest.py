"""The real bot plays for two hours; the pretend games run eight minutes."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture(autouse=True)
def short_games(monkeypatch):
    from bot import trial
    monkeypatch.setattr(trial, "TRIAL_SECONDS", 480)
    monkeypatch.setattr(trial, "RUSH_ODDS", 0.0)    # (its own test sets it)
