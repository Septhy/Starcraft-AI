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


def test_by_default_the_whole_screen_every_two_seconds(tmp_path):
    from recorder import recorder
    assert recorder.INTERVAL == 2.0 and recorder.FULL_EVERY == 1
    assert recorder.MAX_FRAMES * recorder.INTERVAL == 45 * 60
    rec = run(tmp_path, (1920, 1080), max_frames=3, png_every=100)
    names, _ = read(rec.finish())
    assert sorted(n for n in names if n.endswith(".jpg")) == \
        ["frame0000.jpg", "frame0001.jpg", "frame0002.jpg"]
    assert not any(n.startswith(("map", "top")) for n in names)
