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


_template = None


def barracks_selected(screen):
    """True when the first command button is the Marine button, which
    means a barracks is selected."""
    global _template
    if _template is None:
        _template = np.asarray(
            Image.open(data_path("barracks_card.png")).convert("RGB")).astype(int)
    cell = np.asarray(screen.convert("RGB").crop(CARD_CELL)).astype(int)
    return bool(np.abs(cell - _template).mean() < CARD_MATCH)
