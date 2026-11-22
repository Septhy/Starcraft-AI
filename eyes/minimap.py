"""Read the minimap from a screenshot.

Measured on a 1920 x 1080 full-screen picture of the current StarCraft
client (the "Brood War" window) on the 256 x 192 tile Allied Final map.
Other screen sizes or maps need new numbers in LAYOUT.

The minimap gives, for every player colour, which map tiles hold that
player's units and buildings, and which part of the map the screen is
looking at.
"""
import numpy as np

# where the minimap sits on screen, and the map it shows
LAYOUT = {"left": 13, "top": 812, "width": 289, "height": 216,
          "map_tiles": (256, 192)}

# minimap colour of each slot on this map (StarCraft's standard colours)
SLOT_COLOURS = {
    0: ("red", (244, 4, 4)),          # Germany
    1: ("blue", (12, 72, 204)),       # Italy
    2: ("teal", (44, 180, 148)),      # UK
    3: ("purple", (136, 64, 156)),    # France
    4: ("orange", (248, 140, 20)),    # Norway
    5: ("brown", (112, 48, 20)),      # Russia
    6: ("white", (204, 224, 208)),    # computer: Turkey and the east
    7: ("yellow", (252, 252, 56)),    # Spain
}
TOLERANCE = 14          # how far a pixel may be from a slot's colour
VIEW_BOX = 250          # the view rectangle is drawn in pure white


def _crop(screen, layout):
    a = np.asarray(screen.convert("RGB")).astype(int)
    l, t = layout["left"], layout["top"]
    return a[t:t + layout["height"], l:l + layout["width"]]


def read(screen, layout=LAYOUT):
    """screen: a PIL image of the whole screen.

    Returns {"slots": {slot: [(tile_x, tile_y), ...]},
             "view": (left, top, right, bottom) in tiles, or None}
    """
    mm = _crop(screen, layout)
    sx = layout["map_tiles"][0] / layout["width"]
    sy = layout["map_tiles"][1] / layout["height"]
    slots = {}
    for slot, (_, rgb) in SLOT_COLOURS.items():
        ys, xs = np.nonzero(np.abs(mm - np.array(rgb)).max(axis=2)
                            <= TOLERANCE)
        slots[slot] = sorted({(int(x * sx), int(y * sy))
                              for x, y in zip(xs, ys)})
    ys, xs = np.nonzero(mm.min(axis=2) >= VIEW_BOX)
    view = None
    if len(xs) > 20:
        view = (int(xs.min() * sx), int(ys.min() * sy),
                int(xs.max() * sx), int(ys.max() * sy))
    return {"slots": slots, "view": view}


def tile_to_screen(tile_x, tile_y, layout=LAYOUT):
    """The screen pixel on the minimap that stands for a map tile.
    Clicking there moves the view; right-clicking sends units."""
    w, h = layout["map_tiles"]
    return (layout["left"] + int((tile_x + 0.5) * layout["width"] / w),
            layout["top"] + int((tile_y + 0.5) * layout["height"] / h))


def summary(result):
    """Short text for a person or an LLM: where each colour is."""
    lines = []
    for slot, tiles in result["slots"].items():
        if tiles:
            xs, ys = zip(*tiles)
            lines.append(f"{SLOT_COLOURS[slot][0]:7} {len(tiles):5d} tiles, "
                         f"centre ({sum(xs) // len(xs)}, {sum(ys) // len(ys)})")
    lines.append(f"view: {result['view']}")
    return "\n".join(lines)
