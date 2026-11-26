import json
import os
import zipfile

from PIL import Image

from recorder.recorder import Recorder


def noisy(size):
    return lambda: Image.frombytes("RGB", size, os.urandom(size[0] * size[1] * 3))


def run(tmp_path, size, **options):
    t = iter(range(0, 10000, 3))
    rec = Recorder(noisy(size), str(tmp_path), info=lambda: {"mouse": [1, 2]},
                   clock=lambda: next(t), **options)
    while rec.tick():
        pass
    return rec


def read(parts):
    names, info = [], None
    for p in parts:
        with zipfile.ZipFile(p) as z:
            names += z.namelist()
            if "info.json" in z.namelist():
                info = json.loads(z.read("info.json"))
    return names, info


def test_records_packs_and_cleans_up(tmp_path):
    rec = run(tmp_path, (320, 240), max_frames=7, png_every=3, full_every=1)
    assert len(rec.frames) == 7 and not rec.tick()
    parts = rec.finish(part_bytes=400_000)
    assert len(parts) > 1                      # split into several zips
    assert sorted(os.listdir(tmp_path)) == sorted(
        os.path.basename(p) for p in parts)    # loose files removed
    assert all(os.path.getsize(p) < 700_000 for p in parts)
    names, info = read(parts)
    assert len(names) == len(set(names)) == 1 + 7 + 3   # info, jpg, png
    assert info["frames"][2]["seconds"] == 6
    assert info["frames"][0]["mouse"] == [1, 2]
    assert info["frames"][3]["files"] == ["frame0003.jpg", "frame0003.png"]


def test_a_whole_game_keeps_the_small_parts_every_look(tmp_path):
    """On a full-size screen a look without the whole screen keeps the
    minimap and the top strip exactly."""
    rec = run(tmp_path, (1920, 1080), max_frames=12, png_every=100,
              full_every=10)
    names, info = read(rec.finish())
    assert sum(n.startswith("map") for n in names) == 10
    assert sum(n.startswith("top") for n in names) == 10
    assert sorted(n for n in names if n.endswith(".jpg")) == \
        ["frame0000.jpg", "frame0010.jpg"]
    assert info["frames"][5]["files"] == ["map0005.png", "top0005.png"]


def test_by_default_the_whole_screen_twice_a_second(tmp_path):
    from recorder import recorder
    assert recorder.INTERVAL == 0.5 and recorder.FULL_EVERY == 1
    assert recorder.MAX_FRAMES * recorder.INTERVAL == 20 * 60
    rec = run(tmp_path, (1920, 1080), max_frames=3, png_every=100)
    names, _ = read(rec.finish())
    assert sorted(n for n in names if n.endswith(".jpg")) == \
        ["frame0000.jpg", "frame0001.jpg", "frame0002.jpg"]
    assert not any(n.startswith(("map", "top")) for n in names)


def test_clicks_drags_and_keys_are_noted_but_never_the_chat(tmp_path):
    from recorder.recorder import InputLog, is_game
    log = InputLog(t0=100.0)
    feed = lambda t, down, at=(500, 500), game=True: log.feed(t, down, list(at), game)
    feed(100.0, [])
    feed(100.1, [0x11, 0x31])           # Ctrl+1: a hotkey group made
    feed(100.2, [])
    feed(100.3, [0x01], (400, 300))     # a box drawn with the left button
    feed(100.5, [0x01], (700, 500))
    feed(100.6, [], (700, 500))
    feed(100.7, [0x41])                 # A, then a click: attack-move
    feed(100.8, [0x01], (900, 200))
    feed(100.9, [], (902, 201))
    feed(101.0, [0x0D])                 # Enter opens the chat ...
    feed(101.1, [])
    for t, code in enumerate([0x48, 0x49, 0x10, 0x4A]):
        feed(101.2 + t / 10, [code])    # ... "hi" typed: never noted
        feed(101.25 + t / 10, [])
    feed(102.0, [0x0D])                 # sent
    feed(102.1, [])
    feed(102.2, [0x10, 0x32], game=False)   # another window in front
    feed(102.3, [])
    kinds = [(e["type"], e.get("key") or e.get("button")) for e in log.events]
    assert kinds == [("key", "1"), ("press", "left"), ("drag", "left"),
                     ("key", "a"), ("press", "left"), ("click", "left"),
                     ("chat opened", None), ("chat closed", None)]
    assert log.events[0]["mods"] == ["ctrl"]
    drag = log.events[2]
    assert drag["at"] == [400, 300] and drag["to"] == [700, 500]
    assert abs(drag["t"] - 0.3) < 1e-6
    assert is_game("Brood War") and is_game("StarCraft") \
        and not is_game("StarCraft recorder") \
        and not is_game("StarCraft bot: first trial - build x")


def test_the_inputs_go_into_the_zip(tmp_path):
    from recorder.recorder import InputLog
    rec = run(tmp_path, (1920, 1080), max_frames=2, png_every=100)
    log = InputLog(rec.t0)
    log.feed(rec.t0 + 1, [0x53], [1, 1], True)
    names, _ = read(rec.finish(extra=[log.save(str(tmp_path))]))
    assert "inputs.json" in names
