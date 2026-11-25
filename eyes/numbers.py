"""Read the supply number at the top right of the live game screen.

The digits are a fixed font at a fixed place on a 1920 x 1080 screen,
so each one is matched against a stored picture of that digit
(data/digits.json, cut from real screenshots).
"""
import json

import numpy as np

from eyes.live import data_path

FIELD = (1800, 10, 1920, 32)     # left, top, right, bottom of the supply text
GLYPH = (12, 17)                 # every digit is padded to this width, height


def text_mask(screen, field=FIELD):
    """True where the field shows text: bright green, or red when the
    supply is over its limit."""
    l, t, r, b = field
    a = np.asarray(screen.convert("RGB")).astype(int)[t:b, l:r]
    green = (a[:, :, 1] > 140) & (a[:, :, 0] < 130) & (a[:, :, 2] < 130)
    red = (a[:, :, 0] > 150) & (a[:, :, 1] < 110) & (a[:, :, 2] < 110)
    return green | red


def glyphs(mask):
    """Cut a text mask into its characters, left to right."""
    cols = mask.any(axis=0)
    rows = np.nonzero(mask.any(axis=1))[0]
    if len(rows) == 0:
        return []
    top = rows.min()
    out, start = [], None
    for x, on in enumerate(list(cols) + [False]):
        if on and start is None:
            start = x
        elif not on and start is not None:
            g = np.zeros((GLYPH[1], GLYPH[0]), dtype=bool)
            cut = mask[top:top + GLYPH[1], start:min(x, start + GLYPH[0])]
            g[:cut.shape[0], :cut.shape[1]] = cut
            out.append(g)
            start = None
    return out


_templates = None


def _load():
    global _templates
    if _templates is None:
        raw = json.load(open(data_path("digits.json")))
        _templates = [(ch, np.array(bits, dtype=bool))
                      for ch, many in raw.items() for bits in many]
    return _templates


def read_text(screen, field=FIELD):
    """The characters in the field, or None if any is not recognised."""
    out = ""
    for g in glyphs(text_mask(screen, field)):
        best = {}
        for ch, t in _load():
            miss = int((g ^ t).sum())
            best[ch] = min(best.get(ch, 999), miss)
        ranked = sorted(best.items(), key=lambda p: p[1])
        # it must fit one digit well, and clearly better than any other
        if ranked[0][1] > 20 or ranked[1][1] - ranked[0][1] < 6:
            return None
        out += ranked[0][0]
    return out or None


def read_supply(screen):
    """(used, limit) from the supply display, or None if unreadable."""
    text = read_text(screen)
    if not text or text.count("/") != 1:
        return None
    used, limit = text.split("/")
    if not used.isdigit() or not limit.isdigit():
        return None
    if not 0 < int(limit) <= 400 or int(used) > int(limit) + 60:
        return None                     # not a believable reading
    return int(used), int(limit)


MINERALS = (1490, 10, 1600, 32)  # left, top, right, bottom of the minerals


def read_minerals(screen):
    """Minerals at the top of the screen, or None if unreadable. (On
    this map gas always equals minerals.)"""
    text = read_text(screen, MINERALS)
    if not text or not text.isdigit():
        return None
    return int(text)
