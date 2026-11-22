"""The live game screen: where things are and how the map relates to it.

Measured on 1920 x 1080 full-screen pictures of a live game on the
256 x 192 tile Allied Final map, at the zoom the game starts with.
"""
import os
import sys

import numpy as np
from PIL import Image

SCREEN = (1920, 1080)
MINIMAP = {"left": 13, "top": 817, "width": 289, "height": 216}
MAP_PX = (256 * 32, 192 * 32)        # the map's size in map pixels
ZOOM = 72 / 32                       # screen pixels per map pixel
# A map point the camera is centred on shows up a little above and left
# of the middle of the screen. Estimated from two pictures; rough.
CENTRE = (960 - 40, 540 - 80)
GAME_AREA = (0, 40, 1920, 760)       # screen left, top, right, bottom free of panels
CARD_CELL = (1612, 800, 1704, 890)   # the first command button
CARD_MATCH = 12                      # how close a button must be to the template


def data_path(name):
    base = getattr(sys, "_MEIPASS", os.path.join(os.path.dirname(__file__), ".."))
    return os.path.join(base, "data", name)


def minimap_point(map_x, map_y):
    """Screen pixel on the minimap for a point given in map pixels."""
    m = MINIMAP
    return (m["left"] + int(map_x / MAP_PX[0] * m["width"]),
            m["top"] + int(map_y / MAP_PX[1] * m["height"]))


def camera_after_click(screen_x, screen_y):
    """Where the camera is centred (map pixels) after a left click on the
    minimap at that screen pixel. The view cannot leave the map."""
    m = MINIMAP
    cx = (screen_x - m["left"] + 0.5) / m["width"] * MAP_PX[0]
    cy = (screen_y - m["top"] + 0.5) / m["height"] * MAP_PX[1]
    half_w, half_h = SCREEN[0] / ZOOM / 2, SCREEN[1] / ZOOM / 2
    return (min(max(cx, half_w), MAP_PX[0] - half_w),
            min(max(cy, half_h), MAP_PX[1] - half_h))


def on_screen(map_x, map_y, camera):
    """Screen pixel where a map point should appear for that camera."""
    return (int(CENTRE[0] + (map_x - camera[0]) * ZOOM),
            int(CENTRE[1] + (map_y - camera[1]) * ZOOM))


def minimap_showing(screen):
    """True when the live game's minimap is on screen: its pale top
    border line is where it should be."""
    m = MINIMAP
    row = np.asarray(screen.convert("RGB")).astype(int)[
        m["top"] - 1, m["left"] + 5:m["left"] + m["width"] - 5]
    return bool(row.min() > 150 and row.std(axis=0).max() < 12)


_templates = {}


def card_cell(screen):
    """Cut the first command button out of a picture of the screen."""
    return screen.crop(CARD_CELL)


def _first_button_is(picture, name):
    """picture: the whole screen, or just the first command button."""
    if name not in _templates:
        _templates[name] = np.asarray(
            Image.open(data_path(name)).convert("RGB")).astype(int)
    if picture.size != (CARD_CELL[2] - CARD_CELL[0], CARD_CELL[3] - CARD_CELL[1]):
        picture = picture.crop(CARD_CELL)
    cell = np.asarray(picture.convert("RGB")).astype(int)
    return bool(np.abs(cell - _templates[name]).mean() < CARD_MATCH)


def barracks_selected(screen):
    """True when the first command button is the Marine button, which
    means a barracks is selected."""
    return _first_button_is(screen, "barracks_card.png")


def units_selected(screen):
    """True when the first command button is Move, which means units
    that can be ordered about are selected."""
    return _first_button_is(screen, "units_card.png")


# ------------------------------------------------- own forces on the minimap
# Where things are DRAWN on the minimap, fitted to the known positions of
# Russia's starting units and buildings on a real picture. It is two
# pixels lower than the frame MINIMAP describes, which is still what
# clicks are worked out from (that pairing is what the trials tested).
DRAWN = {"left": 14, "top": 819, "width": 288, "height": 217}


def _drawn(screen):
    d = DRAWN
    a = np.asarray(screen.convert("RGB")).astype(int)
    return a[d["top"]:d["top"] + d["height"] + 3,
             d["left"]:d["left"] + d["width"] + 3]


def to_drawn(map_x, map_y):
    """(column, row) on the drawn minimap of a point in map pixels."""
    return (int(map_x / MAP_PX[0] * DRAWN["width"]),
            int(map_y / MAP_PX[1] * DRAWN["height"]))


def from_drawn(col, row):
    """Map pixels of the middle of a drawn minimap pixel."""
    return ((col + 0.5) / DRAWN["width"] * MAP_PX[0],
            (row + 0.5) / DRAWN["height"] * MAP_PX[1])


class Watch:
    """Sees our own units on the minimap.

    Made from a picture taken at the very start of the game, when the
    map file says exactly where our units stand. Everything in our
    colour that is not one of those units is a building; buildings do
    not move, so from then on our colour anywhere else is a unit.
    Where a unit stood in front of a building at the start, the
    building shows through once the unit leaves; forget() removes it.
    A unit is drawn as a block about three pixels across, and one pixel
    is about 0.9 map tiles.
    """

    def __init__(self, screen, structures, units):
        mm = _drawn(screen)
        seen = {}
        for x, y in structures:
            c, r = to_drawn(x, y)
            p = mm[r, c]
            if p.max() > 140:
                seen.setdefault(tuple(int(v) // 32 for v in p), []).append(p)
        self.ok = bool(seen)
        if not self.ok:
            return
        self.colour = np.mean(max(seen.values(), key=len), axis=0)
        own = self._own(mm)
        at_units = np.zeros_like(own)
        for x, y in units:
            c, r = to_drawn(x, y)
            at_units[max(r - 1, 0):r + 2, max(c - 1, 0):c + 2] = True
        self.buildings = own & ~at_units

    def _own(self, mm):
        return np.abs(mm - self.colour).max(axis=2) < 70

    def units(self, screen):
        """Set of (column, row) drawn-minimap pixels showing our units."""
        mask = self._own(_drawn(screen)) & ~self.buildings
        rows, cols = np.nonzero(mask)
        return set(zip(cols.tolist(), rows.tolist()))


    def forget(self, pixels):
        """These pixels turned out not to be units (a box there came up
        empty): a building that a unit was standing in front of at the
        start. Stop reporting them."""
        for c, r in pixels:
            self.buildings[r, c] = True


def clusters(pixels, max_w, max_h):
    """Group minimap pixels into clusters no wider than max_w and no
    taller than max_h. Returns lists of pixels, biggest cluster first."""
    left = set(pixels)
    out = []
    while left:
        c0, r0 = min(left, key=lambda p: (p[1], p[0]))
        group = [p for p in left
                 if c0 - max_w // 2 <= p[0] < c0 - max_w // 2 + max_w
                 and r0 <= p[1] < r0 + max_h]
        left.difference_update(group)
        out.append(group)
    return sorted(out, key=len, reverse=True)
