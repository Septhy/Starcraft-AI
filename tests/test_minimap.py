import os

from PIL import Image

from eyes import minimap

DATA = os.path.join(os.path.dirname(__file__), "data")


def screen(name):
    """A blank 1920 x 1080 screen with a real minimap cut-out pasted in."""
    s = Image.new("RGB", (1920, 1080))
    s.paste(Image.open(os.path.join(DATA, name)),
            (minimap.LAYOUT["left"], minimap.LAYOUT["top"]))
    return s


def centre(tiles):
    xs, ys = zip(*tiles)
    return sum(xs) / len(xs), sum(ys) / len(ys)


def test_finds_each_country_where_it_should_be():
    r = minimap.read(screen("minimap_70.png"))
    s = r["slots"]
    assert all(len(s[k]) > 30 for k in s)          # all eight colours seen
    assert centre(s[5])[0] > 150                   # Russia: east
    assert centre(s[7])[0] < 60 and centre(s[7])[1] > 130   # Spain: SW
    assert centre(s[4])[1] < 70                    # Norway: north
    gx, gy = centre(s[0])                          # Germany: middle
    assert 80 < gx < 140 and 70 < gy < 130
    ix, iy = centre(s[1])                          # Italy: south of Germany
    assert iy > gy


def test_finds_the_view_rectangle():
    r = minimap.read(screen("minimap_70.png"))
    l, t, rt, b = r["view"]
    assert 100 < l < 140 and 15 < t < 40 and 200 < rt < 240 and 80 < b < 110
    r2 = minimap.read(screen("minimap_110.png"))
    assert r2["view"] != r["view"] and r2["view"][0] > l


def test_tile_to_screen_round_trip():
    x, y = minimap.tile_to_screen(128, 96)
    L = minimap.LAYOUT
    assert L["left"] < x < L["left"] + L["width"]
    assert abs(x - (L["left"] + L["width"] / 2)) <= 2
    assert abs(y - (L["top"] + L["height"] / 2)) <= 2
