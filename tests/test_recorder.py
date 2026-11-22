import json
import os
import zipfile

from PIL import Image

from recorder.recorder import Recorder


def noisy(size):
    return lambda: Image.frombytes("RGB", size, os.urandom(size[0] * size[1] * 3))


def test_records_packs_and_cleans_up(tmp_path):
    t = iter(range(0, 1000, 3))
    rec = Recorder(noisy((320, 240)), str(tmp_path),
                   info=lambda: {"mouse": [1, 2]}, max_frames=7,
                   png_every=3, clock=lambda: next(t))
    ticks = 0
    while rec.tick():
        ticks += 1
    assert len(rec.frames) == 7 and not rec.tick()
    parts = rec.finish(part_bytes=400_000)
    assert len(parts) > 1                      # split into several zips
    assert sorted(os.listdir(tmp_path)) == sorted(
        os.path.basename(p) for p in parts)    # loose files removed
    names = []
    for p in parts:
        assert os.path.getsize(p) < 700_000
        with zipfile.ZipFile(p) as z:
            names += z.namelist()
            if "info.json" in z.namelist():
                info = json.loads(z.read("info.json"))
    assert len(names) == len(set(names)) == 1 + 7 + 3   # info, jpg, png
    assert info["frames"][2]["seconds"] == 6
    assert info["frames"][0]["mouse"] == [1, 2]
    assert info["frames"][3]["files"] == ["frame0003.jpg", "frame0003.png"]
