"""Starting by itself (the owner, after Norway trial 64: Finland was a
bit too close, and the seconds until F9 is pressed count).

The app looks at the screen a few times a second while it waits. A game
that has just begun shows the minimap and a game clock near zero; then
the bot starts, without F9. F9 only stops it. After a game the app waits
until that game is off the screen before it will start again, so a bot
stopped in the first seconds does not start itself anew."""
from eyes import live
from eyes.clock import read_clock

START_WITHIN = 8               # game seconds: a clock at most this old is a
                               # game that has just begun
LOOK_EVERY = 0.2               # seconds between looks while waiting


def game_begun(picture):
    """True when the picture shows a game in its first seconds."""
    if picture is None or tuple(picture.size) != tuple(live.SCREEN):
        return False
    try:
        if not live.minimap_showing(picture):
            return False
        seen = read_clock(picture)
    except Exception:
        return False
    return seen is not None and seen <= START_WITHIN


class Starter:
    """Says once for each game that it has begun."""

    def __init__(self):
        self.armed = True

    def played(self):
        """A game was played (or stopped): not again for that game."""
        self.armed = False

    def look(self, picture):
        """True when the bot should start now."""
        begun = game_begun(picture)
        if not self.armed:
            if not begun:
                self.armed = True       # that game is over, or well under way
            return False
        if begun:
            self.armed = False
            return True
        return False
