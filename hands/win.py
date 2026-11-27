"""The real mouse, keyboard and screen on Windows.

Everything the bot does goes through this class. It refuses to act
unless StarCraft is the window in front, and stops as soon as the stop
key (F9) is pressed.
"""
import ctypes
import os
import time
from ctypes import wintypes

from bot.trial import Stopped

GAME_WINDOW = "Brood War"
STOP_KEY = 0x78            # F9
SCAN = {"esc": 0x01, "shift": 0x2A, "ctrl": 0x1D, "alt": 0x38,
        "enter": 0x1C, "space": 0x39, "tab": 0x0F, "backspace": 0x0E,
        "1": 0x02, "2": 0x03, "3": 0x04, "4": 0x05, "5": 0x06, "6": 0x07,
        "7": 0x08, "8": 0x09, "9": 0x0A, "0": 0x0B}
# every letter (trial 39: Norway's Dropship unload, U, was missing and
# the game stopped at once)
SCAN.update(dict(zip("qwertyuiop", range(0x10, 0x1A))))
SCAN.update(dict(zip("asdfghjkl", range(0x1E, 0x27))))
SCAN.update(dict(zip("zxcvbnm", range(0x2C, 0x33))))
# the arrow keys move the game screen (the owner, after trial 56: look
# for the SCVs by moving the screen, not by the minimap); they are
# "extended" keys
SCAN.update({"up": 0x48, "down": 0x50, "left": 0x4B, "right": 0x4D})
EXTENDED = {"up", "down", "left", "right"}
KEY_EXTENDED = 0x01

ULONG_PTR = ctypes.c_size_t


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", wintypes.LONG), ("dy", wintypes.LONG),
                ("mouseData", wintypes.DWORD), ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD), ("dwExtraInfo", ULONG_PTR)]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", wintypes.WORD), ("wScan", wintypes.WORD),
                ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD),
                ("dwExtraInfo", ULONG_PTR)]


class _U(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT)]


class INPUT(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD), ("u", _U)]


LEFT_DOWN, LEFT_UP, RIGHT_DOWN, RIGHT_UP = 0x02, 0x04, 0x08, 0x10
KEY_SCAN, KEY_UP = 0x08, 0x02


def paused(img):
    """True if the picture is the greyed-out screen of a paused game:
    lit, but with no colour anywhere on the minimap."""
    from PIL import ImageStat
    r, g, b = img.crop((14, 819, 302, 1036)).split()
    from PIL import ImageChops
    spread = ImageStat.Stat(ImageChops.difference(r, b)).mean[0] \
        + ImageStat.Stat(ImageChops.difference(r, g)).mean[0]
    return max(ImageStat.Stat(img.crop((14, 819, 302, 1036))).mean) > 6 \
        and spread < 2.0


class WinIO:
    def __init__(self, out_dir, sct, status=lambda s: None):
        self.user = ctypes.windll.user32
        self.out_dir, self.sct, self.status = out_dir, sct, status
        self.names, self.n, self.lines = [], 0, []
        self.last_kept = 0.0
        self.t0 = time.time()
        os.makedirs(out_dir, exist_ok=True)

    # --- safety
    def _check(self):
        if self.user.GetAsyncKeyState(STOP_KEY) & 0x8000:
            raise Stopped("stopped with F9")
        title = ctypes.create_unicode_buffer(200)
        self.user.GetWindowTextW(self.user.GetForegroundWindow(), title, 200)
        if title.value != GAME_WINDOW:
            raise Stopped(f"StarCraft is not in front ({title.value!r})")

    def sleep(self, seconds):
        end = time.time() + seconds
        while True:
            self._check()
            left = end - time.time()
            if left <= 0:
                return
            time.sleep(min(0.03, left))     # exact, even for short pauses

    # --- input
    def _send(self, inp):
        self.user.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))

    def _mouse(self, flag):
        i = INPUT(type=0)
        i.u.mi = MOUSEINPUT(0, 0, 0, flag, 0, 0)
        self._send(i)

    def _key(self, name, up=False):
        i = INPUT(type=1)
        flags = KEY_SCAN | (KEY_UP if up else 0) | \
            (KEY_EXTENDED if name in EXTENDED else 0)
        i.u.ki = KEYBDINPUT(0, SCAN[name], flags, 0, 0)
        self._send(i)

    # The pauses below are about as short as the game reliably accepts:
    # it reads input once a frame, 24 times a second at Fastest.
    def _move(self, x, y):
        self.user.SetCursorPos(int(x), int(y))
        time.sleep(0.015)

    def hover(self, x, y):
        """Move the mouse without clicking (to see a landing outline)."""
        self._check()
        self._move(x, y)

    def click(self, x, y, button="left"):
        self._check()
        self._move(x, y)
        time.sleep(0.01)
        down, up = (LEFT_DOWN, LEFT_UP) if button == "left" else (RIGHT_DOWN, RIGHT_UP)
        self._mouse(down)
        time.sleep(0.035)
        self._mouse(up)
        self.log(f"click {button} {int(x)},{int(y)}", quiet=True)

    def click_with(self, held, x, y, button="left"):
        """Click while holding a key: "ctrl" picks every unit of that kind
        on screen, "shift" adds a unit to or drops it from the selection;
        with the right button, Shift queues the order after the last."""
        self._check()
        down, up = (LEFT_DOWN, LEFT_UP) if button == "left" else (RIGHT_DOWN, RIGHT_UP)
        self._key(held)
        time.sleep(0.04)
        self._move(x, y)
        time.sleep(0.01)
        self._mouse(down)
        time.sleep(0.035)
        self._mouse(up)
        time.sleep(0.03)
        self._key(held, up=True)
        self.log(f"click {held}+{button} {int(x)},{int(y)}", quiet=True)

    def drag(self, x0, y0, x1, y1):
        self._check()
        self._move(x0, y0)
        time.sleep(0.03)
        self._mouse(LEFT_DOWN)
        time.sleep(0.07)                # the game must see the press first
        for k in range(1, 4):
            self._move(x0 + (x1 - x0) * k / 3, y0 + (y1 - y0) * k / 3)
        time.sleep(0.045)
        self._mouse(LEFT_UP)
        self.log(f"drag {int(x0)},{int(y0)} to {int(x1)},{int(y1)}", quiet=True)

    def drag_with(self, held, x0, y0, x1, y1):
        """A box dragged while holding a key: "shift" adds what it takes
        to the selection."""
        self._check()
        self._key(held)
        time.sleep(0.04)
        self._move(x0, y0)
        time.sleep(0.03)
        self._mouse(LEFT_DOWN)
        time.sleep(0.07)
        for k in range(1, 4):
            self._move(x0 + (x1 - x0) * k / 3, y0 + (y1 - y0) * k / 3)
        time.sleep(0.045)
        self._mouse(LEFT_UP)
        time.sleep(0.03)
        self._key(held, up=True)
        self.log(f"drag {held} {int(x0)},{int(y0)} to {int(x1)},{int(y1)}",
                 quiet=True)

    def key(self, name):
        self._check()
        self._key(name)
        time.sleep(0.03)
        self._key(name, up=True)
        self.log(f"key {name}", quiet=True)

    def hold_key(self, name, seconds):
        """Hold a key down for a while (an arrow key scrolls the screen)."""
        self._check()
        self._key(name)
        try:
            end = time.time() + seconds
            while time.time() < end:
                time.sleep(min(0.05, max(0.0, end - time.time())))
        finally:
            self._key(name, up=True)
        self.log(f"key {name} held {seconds:.2f}s", quiet=True)

    def combo(self, held, name):
        """Press a key while holding another, e.g. combo("ctrl", "3")."""
        self._check()
        self._key(held)
        time.sleep(0.04)
        self._key(name)
        time.sleep(0.04)
        self._key(name, up=True)
        time.sleep(0.03)
        self._key(held, up=True)
        self.log(f"key {held}+{name}", quiet=True)

    def type_text(self, text):
        """Type characters, for chat."""
        self._check()
        for ch in text:
            for flags in (0x0004, 0x0004 | KEY_UP):     # unicode character
                i = INPUT(type=1)
                i.u.ki = KEYBDINPUT(0, ord(ch), flags, 0, 0)
                self._send(i)
            time.sleep(0.015)
        self.log("typed a chat line", quiet=True)

    # --- seeing and reporting
    def now(self):
        return time.time()

    def shot(self, label, keep=True):
        from PIL import Image, ImageStat
        for _ in range(4):
            s = self.sct.grab(self.sct.monitors[1])
            img = Image.frombytes("RGB", s.size, s.bgra, "raw", "BGRX")
            # the capture sometimes returns a black game; take it again
            if max(ImageStat.Stat(img.crop((400, 800, 1500, 1080))).mean) > 6:
                break
            time.sleep(0.12)
        img = self._wait_out_pause(img)
        # A long game would fill the zip with pictures: after the first
        # forty, keep at most one every 45 seconds.
        if keep and self.n >= 40 and time.time() - self.last_kept < 45:
            keep = False
        if keep:
            self.last_kept = time.time()
            name = f"{self.n:03d}-{label}.jpg"
            img.save(os.path.join(self.out_dir, name), quality=75)
            self.names.append(name)
            self.n += 1
        return img

    def _grab(self):
        from PIL import Image
        s = self.sct.grab(self.sct.monitors[1])
        return Image.frombytes("RGB", s.size, s.bgra, "raw", "BGRX")

    def _wait_out_pause(self, img, longest=600):
        """When a player pauses, the whole screen turns grey. Do nothing
        until the colour comes back, so no order is given blind."""
        if not paused(img):
            return img
        self.log("the game is paused; waiting")
        start = time.time()
        while paused(img) and time.time() - start < longest:
            self.sleep(1.0)             # also notices F9 and a lost window
            img = self._grab()
        self.log(f"pause over after {time.time() - start:.0f} s")
        return img

    def card(self):
        """A quick look at just the first command button."""
        from PIL import Image
        from eyes.live import CARD_CELL
        mon = self.sct.monitors[1]
        l, t, r, b = CARD_CELL
        s = self.sct.grab({"left": mon["left"] + l, "top": mon["top"] + t,
                           "width": r - l, "height": b - t})
        return Image.frombytes("RGB", s.size, s.bgra, "raw", "BGRX")

    def log(self, text, quiet=False):
        self.lines.append(f"{time.time() - self.t0:7.2f}  {text}")
        if not quiet:
            self.status(text)

    def finish(self):
        from recorder.recorder import pack
        with open(os.path.join(self.out_dir, "log.txt"), "w",
                  encoding="utf-8") as f:
            f.write("\n".join(self.lines) + "\n")
        return pack(self.out_dir, ["log.txt"] + self.names)
