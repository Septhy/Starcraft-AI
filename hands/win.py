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
SCAN = {"m": 0x32, "a": 0x1E, "esc": 0x01, "shift": 0x2A, "ctrl": 0x1D,
        "1": 0x02, "2": 0x03, "3": 0x04, "4": 0x05, "5": 0x06, "6": 0x07,
        "7": 0x08, "8": 0x09, "9": 0x0A, "0": 0x0B, "l": 0x26,
        "h": 0x23, "y": 0x15, "enter": 0x1C, "s": 0x1F, "b": 0x30}

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
        i.u.ki = KEYBDINPUT(0, SCAN[name], KEY_SCAN | (KEY_UP if up else 0), 0, 0)
        self._send(i)

    # The pauses below are about as short as the game reliably accepts:
    # it reads input once a frame, 24 times a second at Fastest.
    def _move(self, x, y):
        self.user.SetCursorPos(int(x), int(y))
        time.sleep(0.015)

    def click(self, x, y, button="left"):
        self._check()
        self._move(x, y)
        time.sleep(0.01)
        down, up = (LEFT_DOWN, LEFT_UP) if button == "left" else (RIGHT_DOWN, RIGHT_UP)
        self._mouse(down)
        time.sleep(0.035)
        self._mouse(up)
        self.log(f"click {button} {int(x)},{int(y)}", quiet=True)

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

    def key(self, name):
        self._check()
        self._key(name)
        time.sleep(0.03)
        self._key(name, up=True)
        self.log(f"key {name}", quiet=True)

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
