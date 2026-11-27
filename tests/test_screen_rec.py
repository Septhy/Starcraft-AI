"""The recorder inside the bot (bot/screen_rec.py)."""
import json
import os
import zipfile
from contextlib import contextmanager

from PIL import Image

from bot import screen_rec


def fake_grab():
    @contextmanager
    def make():
        yield (lambda: Image.new("RGB", (1920, 1080), (40, 60, 20))), \
            {"left": 0, "top": 0, "width": 1920, "height": 1080}
    return make


def test_the_bot_records_the_screen_while_it_plays(tmp_path):
    t = [0.0]

    def clock():
        return t[0]

    def sleep(s):
        t[0] += s
    rec = screen_rec.ScreenRecording(
        str(tmp_path), fake_grab(), setup=lambda: {"system_scale": 1.0},
        max_frames=3, clock=clock, sleep=sleep).start()
    rec.thread.join(timeout=30)         # stops by itself after 3 pictures
    paths = rec.stop()
    assert rec.problem is None and rec.frames == 3
    assert paths and all(os.path.basename(p).startswith("screen-part")
                         for p in paths)
    with zipfile.ZipFile(paths[0]) as z:
        info = json.loads(z.read("info.json"))
        assert info["setup_start"]["system_scale"] == 1.0
        assert info["setup_start"]["recorded_monitor"]["width"] == 1920
        assert len([n for n in z.namelist() if n.endswith(".jpg")]) == 3
    assert not os.path.exists(os.path.join(str(tmp_path), "screen"))


def test_a_problem_never_stops_the_bot(tmp_path):
    @contextmanager
    def broken():
        raise OSError("no screen")
        yield
    rec = screen_rec.ScreenRecording(str(tmp_path), broken).start()
    assert rec.stop() == [] and "no screen" in rec.problem
