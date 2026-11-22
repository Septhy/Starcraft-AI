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
SCAN = {"m": 0x32, "a": 0x1E, "esc": 0x01, "shift": 0x2A, "ctrl": 0x1D}

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


class WinIO:
    def __init__(self, out_dir, sct, status=lambda s: None):
        self.user = ctypes.windll.user32
        self.out_dir, self.sct, self.status = out_dir, sct, status
        self.names, self.n, self.lines = [], 0, []
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
        while time.time() < end:
            self._check()
            time.sleep(0.03)

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

    def _move(self, x, y):
        self.user.SetCursorPos(int(x), int(y))
        time.sleep(0.06)

    def click(self, x, y, button="left"):
        self._check()
        self._move(x, y)
        down, up = (LEFT_DOWN, LEFT_UP) if button == "left" else (RIGHT_DOWN, RIGHT_UP)
        self._mouse(down)
        time.sleep(0.05)
        self._mouse(up)
        self.log(f"click {button} {int(x)},{int(y)}", quiet=True)

    def drag(self, x0, y0, x1, y1):
        self._check()
        self._move(x0, y0)
        time.sleep(0.1)
        self._mouse(LEFT_DOWN)
        time.sleep(0.2)                 # the game must see the press first
        for k in range(1, 13):
            self._move(x0 + (x1 - x0) * k / 12, y0 + (y1 - y0) * k / 12)
        time.sleep(0.15)
        self._mouse(LEFT_UP)
        self.log(f"drag {int(x0)},{int(y0)} to {int(x1)},{int(y1)}", quiet=True)

    def key(self, name):
        self._check()
        self._key(name)
        time.sleep(0.04)
        self._key(name, up=True)
        self.log(f"key {name}", quiet=True)

    # --- seeing and reporting
    def shot(self, label):
        from PIL import Image, ImageStat
        for _ in range(4):
            s = self.sct.grab(self.sct.monitors[1])
            img = Image.frombytes("RGB", s.size, s.bgra, "raw", "BGRX")
            # the capture sometimes returns a black game; take it again
            if max(ImageStat.Stat(img.crop((400, 800, 1500, 1080))).mean) > 6:
                break
            time.sleep(0.12)
        name = f"{self.n:03d}-{label}.jpg"
        img.save(os.path.join(self.out_dir, name), quality=85)
        self.names.append(name)
        self.n += 1
        return img

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
