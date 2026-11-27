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


# ------------------------------------- the exact view after a minimap click
# (Norway, after trial 59.) A left click on the minimap moves the view in
# whole pixels of the old, small minimap: 128 wide, drawn 2.25 times
# bigger here, one pixel two tiles. So after a click the screen's top-left
# corner always sits on an even tile, six old pixels left of the click
# and three above it. Fitted on 47 different clicks seen in the screen
# recordings of trials 51 to 59 (1,564 frames, every one agrees) and
# checked against buildings of known place at Oslo, in Finland, at
# Murmansk and at Arkhangelsk: each lands on its picture.
# The older camera_after_click with CENTRE puts things about two tiles too
# high: good enough for boxes, not for clicking one thing or for placing a
# building on a chosen tile.
MM_X0, MM_Y0 = 12.4, 817.7     # screen x, y where the old minimap's first pixel starts
MM_SX, MM_SY = 2.25, 217 / 96  # screen pixels to one old minimap pixel
MM_HALF = (6, 3)               # old pixels from the view's left and top to the click
TILE_PX = 72                   # screen pixels a tile
MAP_TILES = (256, 192)


def view_after_click(px, py):
    """Top-left tile (left, top) of the screen after a left click on the
    minimap at screen pixel (px, py)."""
    kx = int((px - MM_X0) // MM_SX) - MM_HALF[0]
    ky = int((py - MM_Y0) // MM_SY) - MM_HALF[1]
    kx = min(max(kx, 0), int((MAP_TILES[0] - SCREEN[0] / TILE_PX) // 2))
    ky = min(max(ky, 0), MAP_TILES[1] // 2 - 2 * MM_HALF[1])
    return 2 * kx, 2 * ky


def click_for_view(left, top):
    """The minimap pixel to click so that the screen's top-left tile comes
    to (left, top), rounded to the nearest even tiles."""
    kx = max(0, int(round(left / 2)))
    ky = max(0, int(round(top / 2)))
    return (int(round(MM_X0 + (kx + MM_HALF[0] + 0.5) * MM_SX)),
            int(round(MM_Y0 + (ky + MM_HALF[1] + 0.5) * MM_SY)))


def tile_xy(tx, ty, view):
    """Screen pixel of a tile point (a tile's top-left corner; fractions
    of a tile allowed) for a view (left, top) from view_after_click."""
    return (tx - view[0]) * TILE_PX, (ty - view[1]) * TILE_PX


def mm_point(tx, ty):
    """The minimap pixel that stands for tile (tx, ty): for an order given
    on the minimap (the middle of its old pixel)."""
    return (int(round(MM_X0 + (int(tx) // 2 + 0.5) * MM_SX)),
            int(round(MM_Y0 + (int(ty) // 2 + 0.5) * MM_SY)))


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


def building_selected(picture):
    """True when something with command buttons is selected that is not
    a group of units: a building that can train or lift off."""
    return not _first_button_is(picture, "blank_card.png") and \
        not _first_button_is(picture, "units_card.png")


STOP_CELL = (1717, 800, 1809, 890)   # the second command button


def gun_selected(screen):
    """A unit that cannot move is selected, as the sieged Heavy Defensive
    Artillery: the first button is empty and the second is Stop (from the
    repository owner's pictures; units with Move have it first, nothing
    selected has no Stop)."""
    if screen is None or screen.size != (1920, 1080):
        return False
    if not _first_button_is(screen, "blank_card.png"):
        return False
    if "stop_card.png" not in _templates:
        _templates["stop_card.png"] = np.asarray(
            Image.open(data_path("stop_card.png")).convert("RGB")).astype(int)
    cell = np.asarray(screen.convert("RGB").crop(STOP_CELL)).astype(int)
    return bool(np.abs(cell - _templates["stop_card.png"]).mean() < CARD_MATCH)


def units_selected(screen):
    """True when the first command button is Move, which means units
    that can be ordered about are selected."""
    return _first_button_is(screen, "units_card.png")


def move_shown(picture):
    """True when the first command button is Move, drawn yellow or white.
    The game draws a unit's current order in white, so units on the move
    (and a building in the air that is flying somewhere) show a white
    Move button, which units_selected, fitted on the yellow one, does not
    know (the repository owner's recording; Norway trial 59)."""
    return _first_button_is(picture, "units_card.png") or \
        _first_button_is(picture, "units_moving_card.png")


def build_menu_shown(picture):
    """True when the first command button is the build menu's first
    building: what an SCV, and only an SCV, shows after B."""
    return _first_button_is(picture, "build_menu_card.png")


def placing_shown(picture):
    """True when the first command button is empty, as while a building
    is being placed (only Cancel shows then, bottom right)."""
    return _first_button_is(picture, "blank_card.png")


def building_card(picture):
    """A building's own buttons: not empty, not Move in either colour,
    not an SCV's build menu."""
    return not placing_shown(picture) and not move_shown(picture) and \
        not build_menu_shown(picture)


ATTACK_CELL = (1850, 825, 1900, 873)   # inside the third command button
ATTACK_ICON = 200                      # bright icon pixels there: an Attack button


def attack_shown(screen):
    """True when the third command button holds an icon: Attack, which
    marines and SCVs have and a Dropship or a building in the air has not
    (measured: about 560 bright pixels against 2). Needs the whole
    screen."""
    if screen is None or tuple(getattr(screen, "size", ())) != tuple(SCREEN):
        return False
    a = np.asarray(screen.convert("RGB").crop(ATTACK_CELL)).astype(int)
    R, G, B = a[..., 0], a[..., 1], a[..., 2]
    icon = ((R > 180) & (G > 160) & (B < 110)) | (a.min(axis=2) > 200)
    return int(icon.sum()) >= ATTACK_ICON


BUILD_CELL = (1640, 1010, 1690, 1058)   # inside the bottom-left command button
BUILD_YELLOW = 200                     # yellow pixels there: an SCV's Build button


def scv_selected(screen):
    """True when the bottom-left command button is the yellow Build
    button, which only SCVs have (marines and buildings show an empty
    plate there). Norway trial 55: a click near the depots' place left two
    marines selected and they were taken for SCVs.

    It needs the whole screen. Trials 56 to 59: it was handed the quick
    card picture, which holds the first button only, cut an empty piece
    out of it and so said no every time, also with an SCV selected."""
    if screen is None or tuple(getattr(screen, "size", ())) != tuple(SCREEN):
        return False
    try:
        a = np.asarray(screen.convert("RGB").crop(BUILD_CELL)).astype(int)
    except Exception:
        return False
    R, G, B = a[..., 0], a[..., 1], a[..., 2]
    return int(((R > 180) & (G > 160) & (B < 90)).sum()) >= BUILD_YELLOW


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


def camera_from_minimap(screen):
    """Where the view is, read from the white box on the minimap: the map
    point (map pixels) in the middle of the box, or None. Good to about a
    tile; used when the screen is moved by the arrow keys."""
    a = _drawn(screen)
    white = a.min(axis=2) >= 190
    runs = []
    for y in range(white.shape[0]):
        row = white[y].copy()           # gaps of up to 2 pixels (a dot on
        for g in (1, 2):                # the line) are closed
            row[g:-g] |= white[y][:-2 * g] & white[y][2 * g:]
        x = 0
        while x < len(row):
            if row[x]:
                x2 = x
                while x2 < len(row) and row[x2]:
                    x2 += 1
                if 24 <= x2 - x <= 38:
                    runs.append((y, x, x2 - x))
                x = x2
            else:
                x += 1
    for y, x, n in runs:
        for y2, x2, n2 in runs:
            if 12 <= y2 - y <= 22 and abs(x2 - x) <= 2 and abs(n2 - n) <= 3:
                left, top = from_drawn(x, y)
                right, bottom = from_drawn(x + n, y2)
                return (left + right) / 2, (top + bottom) / 2
    # at the map's edge one side of the box is cut off: one line with
    # its two sides running up (a bottom line) or down (a top line)
    box_h = SCREEN[1] / ZOOM / MAP_PX[1] * DRAWN["height"]
    for y, x, n in runs:
        ends = (x, min(x + n - 1, white.shape[1] - 1))
        def side(r0, r1):
            return r0 >= 0 and r1 <= white.shape[0] and all(
                white[r0:r1, max(0, c - 1):c + 2].any(axis=1).all()
                for c in ends)
        up, down = side(y - 6, y), side(y + 2, y + 8)
        if up == down:
            continue
        top = y - box_h if up else y
        left, t = from_drawn(x, top)
        right, b = from_drawn(x + n, top + box_h)
        return (left + right) / 2, (t + b) / 2
    return None


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


    def others(self, screen, slots):
        """Minimap pixels in the colours of the given slots (see
        eyes/minimap.py SLOT_COLOURS): other players' units and
        buildings. In a real game our own side is drawn in green and
        everyone else in their own colour."""
        from eyes.minimap import SLOT_COLOURS
        mm = _drawn(screen)
        out = set()
        for slot in slots:
            mask = np.abs(mm - np.array(SLOT_COLOURS[slot][1])).max(axis=2) < 45
            rows, cols = np.nonzero(mask)
            out.update(zip(cols.tolist(), rows.tolist()))
        return out

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


# ------------------------------------------------ how many units are selected
# With several units selected, the bottom panel shows one small framed
# picture per unit, up to twelve, in two rows of six.
SLOT_ORIGIN = (617, 893)        # left, top of the first frame
SLOT_STEP = (81, 83)            # from one frame to the next: across, down
SLOT_SIZE = 72


def frame_box(i, n=12):
    """The screen box of the i-th framed picture when n units are
    selected. The game fills two rows, half the units in each (the top
    row takes the odd one): two units stand one above the other, seven
    are four and three (trials 24, 25)."""
    per_row = min(6, max(1, -(-n // 2)))
    col, row = i % per_row, i // per_row
    x = SLOT_ORIGIN[0] + col * SLOT_STEP[0]
    y = SLOT_ORIGIN[1] + row * SLOT_STEP[1]
    return (x, y, x + SLOT_SIZE, y + SLOT_SIZE)


SCV_FRAME_MATCH = 0.4                 # overlap with the SCV wireframe: an SCV
FRAME_KINDS = {"scv": "scv_frame.png", "dropship": "dropship_frame.png"}


def _frame_lines(a, box):
    x0, y0, x1, y1 = box
    c = a[y0 + 8:y1 - 8, x0 + 8:x1 - 8]
    return (c.max(axis=2) > 100) & (c[..., 2] < np.maximum(c[..., 0], c[..., 1]) - 20)


def frames_like(screen, n, kind):
    """Which of the n framed pictures of a selection show a unit of
    `kind` ("scv", "dropship"), told by its wireframe. Checked on every
    recorded frame of trials 51 to 59 with several units selected (about
    900): each one found was that kind of unit, never a marine."""
    name = FRAME_KINDS[kind]
    if name not in _templates:
        _templates[name] = np.asarray(
            Image.open(data_path(name)).convert("L")) > 127
    t = _templates[name]
    a = np.asarray(screen.convert("RGB")).astype(int)
    out = []
    for i in range(n):
        m = _frame_lines(a, frame_box(i, n))
        if m.shape != t.shape:
            continue
        best = 0.0
        for dy in (-2, -1, 0, 1, 2):
            for dx in (-2, -1, 0, 1, 2):
                r = np.roll(np.roll(t, dy, 0), dx, 1)
                best = max(best, (m & r).sum() / max(1, (m | r).sum()))
        if best >= SCV_FRAME_MATCH:
            out.append(i)
    return out


def scv_frames(screen, n):
    """Which of the n framed pictures of a selection are SCVs, told by
    their wireframe (bulky, no gun) against a marine's (Norway trial 58:
    two SCVs had been boxed into an army key with the marines)."""
    return frames_like(screen, n, "scv")


def frames_shown(screen):
    """How many framed pictures the bottom panel shows: 2 to 12 with
    several units selected, 0 with one unit or none. Unlike
    selected_count it does not ask for a yellow Move button, so it also
    counts units that are on the move."""
    a = np.asarray(screen.convert("RGB")).astype(int)
    count = 0
    for row in range(2):
        for col in range(6):
            x = SLOT_ORIGIN[0] + col * SLOT_STEP[0]
            y = SLOT_ORIGIN[1] + row * SLOT_STEP[1]
            top = a[y - 1:y + 5, x + 8:x + SLOT_SIZE - 8].max(axis=2).max(axis=0)
            left = a[y + 8:y + SLOT_SIZE - 8, x - 1:x + 7].max(axis=2).max(axis=1)
            if (top > 120).mean() > 0.7 and (left > 120).mean() > 0.7:
                count += 1
    return count


def selected_count(screen):
    """How many units the game shows as selected, read from the framed
    pictures in the bottom panel: 0 to 12. One unit alone is shown
    differently (a large picture and its name) and counts as 1."""
    if not units_selected(screen):
        return 0
    a = np.asarray(screen.convert("RGB")).astype(int)
    count = 0
    for row in range(2):
        for col in range(6):
            x = SLOT_ORIGIN[0] + col * SLOT_STEP[0]
            y = SLOT_ORIGIN[1] + row * SLOT_STEP[1]
            # the frame's top and left edges are bright lines
            # (each line is a few pixels thick with soft edges, so take
            # the brightest pixel across its thickness)
            top = a[y - 1:y + 5, x + 8:x + SLOT_SIZE - 8].max(axis=2).max(axis=0)
            left = a[y + 8:y + SLOT_SIZE - 8, x - 1:x + 7].max(axis=2).max(axis=1)
            if (top > 120).mean() > 0.7 and (left > 120).mean() > 0.7:
                count += 1
    return max(count, 1)
