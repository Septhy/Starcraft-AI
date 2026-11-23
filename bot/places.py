"""The map's cities by name, and which of them Russia can walk to.

The map file names its locations as the map maker wrote them, often
with the tax value after the name ("Warsaw 200"). Here they get plain
names, a few common other names (Belgrade, Kiev, Gibraltar), and a
check of whether Russia's troops can walk there from Smolensk.

Walking: data/land.png is the land of the map (white) and the sea
(black), one pixel per pixel of the drawn minimap. It was made from a
picture of the minimap at the start of a game, where the sea is bluer
than red and the land redder than blue once averaged over a few
pixels. Land joined to Smolensk can be walked to; Britain, Ireland,
America and the islands of the Mediterranean cannot.
"""
import re
from collections import deque

import numpy as np

from eyes import live

NOT_CITIES = re.compile(r"^(Capital City|Factory|Bunker|bunker|Spain rush|"
                        r"Location|8 French|Italian Units|Invasion|"
                        r"American Invasion|Z)")
OTHER_NAMES = {"Belgrade": "Serbia 100", "Kiev": "Ukraine 200",
               "Kyiv": "Ukraine 200", "Gibraltar": "Gilbritar 100",
               "Netherlands": "Amsterdam 100", "Holland": "Amsterdam 100",
               "Koenigsberg": "Konigsberg 200", "Königsberg": "Konigsberg 200",
               "St Nazaire": "St. Nazaire 200", "Newfoundland": "Newfound Land 100",
               "Sevastapol": "Sevastopol 100"}
HOME = "Smolensk 200"
_reach = None


def plain(name):
    """"Warsaw 200" -> "Warsaw"."""
    return re.sub(r"\s+\d+$", "", name).strip()


def cities(mapdata):
    """Map location name -> plain name, for the real cities."""
    out = {}
    for p in mapdata["places"]:
        n = p["name"]
        if re.search(r"\s\d+$", n) and not NOT_CITIES.match(n):
            out[n] = plain(n)
    return out


def names_for_chat(mapdata):
    """The place names the chat reader may answer with."""
    return sorted(set(cities(mapdata).values()) | set(OTHER_NAMES))


def resolve(mapdata, text):
    """The map location meant by a place name, or None."""
    t = " ".join(str(text).split()).lower().strip(" .,!?")
    if not t:
        return None
    for other, real in OTHER_NAMES.items():
        if t == other.lower():
            return real
    for real, name in cities(mapdata).items():
        if t in (name.lower(), real.lower()):
            return real
    return None


def reachable():
    """The drawn-minimap pixels Russia's troops can walk to."""
    global _reach
    if _reach is None:
        from PIL import Image
        land = np.asarray(Image.open(live.data_path("land.png")).convert("L")) > 127
        from bot.trial import load_map, place
        home = place(load_map(), HOME)
        c, r = (int(v) for v in live.to_drawn(home["x"], home["y"]))
        h, w = land.shape
        seen = np.zeros_like(land)
        seen[r, c] = True
        todo = deque([(r, c)])
        while todo:
            y, x = todo.popleft()
            for ny, nx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                if 0 <= ny < h and 0 <= nx < w and land[ny, nx] \
                        and not seen[ny, nx]:
                    seen[ny, nx] = True
                    todo.append((ny, nx))
        _reach = seen
    return _reach


def walkable(map_x, map_y):
    """True if Russia's troops can walk to this point from Smolensk."""
    seen = reachable()
    h, w = seen.shape
    c, r = (int(v) for v in live.to_drawn(map_x, map_y))
    c, r = min(max(c, 0), w - 1), min(max(r, 0), h - 1)
    return bool(seen[max(0, r - 2):r + 3, max(0, c - 2):c + 3].any())
