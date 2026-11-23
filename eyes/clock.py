"""Read the game clock in the console at the bottom of the screen.

The clock counts up from 00:00 at the start of the game, in real
seconds, and stops while the game is paused. It is the clock players
mean when they say "wait two minutes". (The countdown at the top of the
screen belongs to the map's rounds, and runs faster.)

The digits are white on black, evenly spaced, and always in the same
place on a 1920 x 1080 screen, so each one is matched against a stored
picture of that digit (data/clock_digits.json, cut from real games).
"""
import json

import numpy as np

from eyes.live import data_path

FIELD = (990, 820, 1075, 838)    # left, top, right, bottom of the clock text
GLYPH = (8, 14)                  # every digit is scaled to this width, height
_templates = None


def text_mask(screen, field=FIELD):
    """True where the field shows the clock's grey-white text."""
    a = np.asarray(screen.crop(field).convert("RGB")).astype(int)
    return (a.mean(axis=2) > 110) & (a.max(axis=2) - a.min(axis=2) < 70), a


def glyphs(screen, field=FIELD):
    """The clock's characters, left to right: ("digit", picture) or
    (":", None)."""
    mask, a = text_mask(screen, field)
    if mask.sum() < 20:
        return []
    lum = a.mean(axis=2)
    cols = mask.any(axis=0)
    out, start = [], None
    for x, on in enumerate(list(cols) + [False]):
        if on and start is None:
            start = x
        elif not on and start is not None:
            part = mask[:, start:x]
            rows = np.nonzero(part.any(axis=1))[0]
            h, w = rows.max() - rows.min() + 1, x - start
            if w <= 3 or part.sum() < 14:
                # a colon's two dots, or a speck
                if part.sum() >= 3 and out and out[-1][0] != ":":
                    out.append((":", None))
            elif h >= 9:
                g = lum[rows.min():rows.max() + 1, start:x]
                out.append(("digit", _scale(g)))
            start = None
    return out


def _scale(g):
    """A digit's picture, scaled to GLYPH and to the range 0..1."""
    from PIL import Image
    im = Image.fromarray(np.clip(g, 0, 255).astype(np.uint8))
    v = np.asarray(im.resize(GLYPH, Image.BILINEAR)).astype(float)
    v -= v.min()
    return v / max(v.max(), 1.0)


def templates():
    global _templates
    if _templates is None:
        with open(data_path("clock_digits.json")) as f:
            raw = json.load(f)
        _templates = {d: np.array(v) for d, v in raw.items()}
    return _templates


def read_clock(screen):
    """Seconds shown on the game clock, or None if it cannot be read."""
    marks = glyphs(screen)
    digits = [g for kind, g in marks if kind == "digit"]
    if len(digits) < 3:
        return None
    t = templates()
    text = ""
    for g in digits:
        best, d = min((float(((g - v) ** 2).mean()), d) for d, v in t.items())
        if best > 0.08:
            return None                 # not a digit we know
        text += d
    # m:ss, mm:ss or h:mm:ss, read from the right
    secs, mins, hours = int(text[-2:]), int(text[-4:-2] or 0), int(text[:-4] or 0)
    if secs > 59 or mins > 59:
        return None
    return hours * 3600 + mins * 60 + secs
