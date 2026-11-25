"""Screen recorder for building the StarCraft screen reader.

Run it, start StarCraft, press F9 to start and F9 again to stop. Twice
a second it keeps the whole screen, with the mouse position, for up to
20 minutes. While StarCraft is the window in front it also notes every
mouse click and drag and every key pressed (hotkeys, commands), with
the time, so they line up with the pictures. What is typed into the
chat is never noted: from the Enter that opens it to the Enter or Esc
that closes it, keys are skipped. It packs everything into zip files on
the Desktop.

It only looks and listens. It does not touch the game, the mouse or the
keyboard.
"""
import json
import os
import sys
import time
import zipfile

INTERVAL = 0.5          # seconds between looks (the repository owner)
MAX_FRAMES = 2400       # stop by itself after this many looks (20 minutes:
                        # twice a second is about 40 MB a minute)
FULL_EVERY = 1          # every n-th look keeps the whole screen (JPEG)
PNG_EVERY = 600         # every n-th look also keeps it exact (PNG): 5 minutes
# A look without the whole screen keeps these small parts of it exactly:
# the minimap, and the strip along the top with the timer, money and
# supply. (With the whole screen every look, they are not needed.)
MINIMAP_PART = (0, 780, 330, 1080)
TOP_PART = (0, 0, 1920, 40)
JPEG_QUALITY = 70       # twice a second: kept smaller
PART_BYTES = 18 * 1024 * 1024   # zip parts are kept under this size
HOTKEY = 0x78           # F9
INPUT_EVERY = 0.01      # seconds between looks at the keys and buttons
DRAG_LEAST = 8          # screen pixels the mouse must move for a drag


class Recorder:
    """Takes the pictures and packs them. Knows nothing about Windows."""

    def __init__(self, grab, out_dir, info=lambda: {}, max_frames=MAX_FRAMES,
                 png_every=PNG_EVERY, clock=time.time, full_every=FULL_EVERY):
        self.grab, self.info, self.clock = grab, info, clock
        self.out_dir, self.max_frames, self.png_every = \
            out_dir, max_frames, png_every
        self.full_every = full_every
        self.frames = []
        self.t0 = None
        os.makedirs(out_dir, exist_ok=True)

    def tick(self):
        """Take one picture. Returns False once the limit is reached."""
        if len(self.frames) >= self.max_frames:
            return False
        now = self.clock()
        if self.t0 is None:
            self.t0 = now
        img = self.grab().convert("RGB")
        n = len(self.frames)
        files = []
        if img.size == (1920, 1080) and n % self.full_every != 0:
            for tag, part in (("map", MINIMAP_PART), ("top", TOP_PART)):
                name = f"{tag}{n:04d}.png"
                img.crop(part).save(os.path.join(self.out_dir, name))
                files.append(name)
        if n % self.full_every == 0:
            name = f"frame{n:04d}.jpg"
            img.save(os.path.join(self.out_dir, name), quality=JPEG_QUALITY)
            files.append(name)
        if n % self.png_every == 0:
            exact = f"frame{n:04d}.png"
            img.save(os.path.join(self.out_dir, exact))
            files.append(exact)
        entry = {"files": files, "seconds": round(now - self.t0, 2),
                 "size": list(img.size)}
        entry.update(self.info())
        self.frames.append(entry)
        return len(self.frames) < self.max_frames

    def finish(self, part_bytes=PART_BYTES, extra=()):
        """Write the notes file and pack everything into zip parts
        (with `extra` files already in the folder, such as the inputs)."""
        with open(os.path.join(self.out_dir, "info.json"), "w",
                  encoding="utf-8") as f:
            json.dump({"frames": self.frames}, f, indent=1)
        names = ["info.json"] + list(extra) + \
            [n for e in self.frames for n in e["files"]]
        return pack(self.out_dir, names, part_bytes)


def pack(out_dir, names, part_bytes=PART_BYTES):
    """Pack the named files into zip parts and remove the loose files."""
    parts, current, size = [], [], 0
    for n in names:
        s = os.path.getsize(os.path.join(out_dir, n))
        if current and size + s > part_bytes:
            parts.append(current)
            current, size = [], 0
        current.append(n)
        size += s
    if current:
        parts.append(current)
    paths = []
    for i, part in enumerate(parts, 1):
        path = os.path.join(out_dir, f"recording-part{i}.zip")
        with zipfile.ZipFile(path, "w", zipfile.ZIP_STORED) as z:
            for n in part:
                z.write(os.path.join(out_dir, n), n)
        paths.append(path)
    for n in names:
        os.remove(os.path.join(out_dir, n))
    return paths


# Key names by Windows key code: what is noted. Letters and digits are
# added below. Anything else is noted by its code.
KEY_NAMES = {0x08: "backspace", 0x09: "tab", 0x0D: "enter", 0x1B: "esc",
             0x20: "space", 0x25: "left", 0x26: "up", 0x27: "right",
             0x28: "down", 0x2E: "delete", 0xC0: "`"}
KEY_NAMES.update({c: chr(c).lower() for c in range(0x41, 0x5B)})
KEY_NAMES.update({c: chr(c) for c in range(0x30, 0x3A)})
KEY_NAMES.update({0x70 + i: f"f{i + 1}" for i in range(12)})
MODIFIERS = {0x10: "shift", 0x11: "ctrl", 0x12: "alt"}
BUTTONS = {0x01: "left", 0x02: "right", 0x04: "middle"}
WATCHED = sorted(set(KEY_NAMES) | set(MODIFIERS) | set(BUTTONS))


def is_game(title):
    """The game's own window (not this recorder's, nor the bot's)."""
    t = title.lower()
    return "starcraft" in t and "recorder" not in t and "bot" not in t


class InputLog:
    """The clicks, drags and keys, from what is held down at each look
    (feed). Only while the game is in front; never what is typed into
    the chat. Knows nothing about Windows."""

    def __init__(self, t0):
        self.t0, self.events = t0, []
        self.held, self.chat = set(), False
        self.pressed_at = {}            # mouse button -> (time, position)

    def feed(self, now, down, mouse, in_game):
        """`down`: the key codes held now; `mouse`: the pointer [x, y];
        `in_game`: StarCraft is the window in front."""
        down = set(down)
        new, gone = down - self.held, self.held - down
        self.held = down
        if not in_game:
            self.pressed_at.clear()
            return
        t = round(now - self.t0, 3)
        mods = [n for c, n in sorted(MODIFIERS.items()) if c in down]
        for code in sorted(new):
            if code in BUTTONS:
                self.pressed_at[code] = (t, list(mouse))
                self.events.append({"t": t, "type": "press",
                                    "button": BUTTONS[code],
                                    "at": list(mouse), "mods": mods})
            elif code in MODIFIERS:
                continue                # noted with the keys and clicks
            elif self.chat:
                if code in (0x0D, 0x1B):    # sent or given up
                    self.chat = False
                    self.events.append({"t": t, "type": "chat closed"})
            elif code == 0x0D:
                self.chat = True        # nothing typed from here is noted
                self.events.append({"t": t, "type": "chat opened"})
            else:
                self.events.append({"t": t, "type": "key",
                                    "key": KEY_NAMES.get(code, hex(code)),
                                    "mods": mods})
        for code in sorted(gone):
            if code in BUTTONS and code in self.pressed_at:
                t1, start = self.pressed_at.pop(code)
                moved = max(abs(mouse[0] - start[0]), abs(mouse[1] - start[1]))
                kind = "drag" if moved >= DRAG_LEAST else "click"
                event = {"t": t1, "type": kind, "button": BUTTONS[code],
                         "at": start, "mods": mods, "held": round(t - t1, 3)}
                if kind == "drag":
                    event["to"] = list(mouse)
                self.events.append(event)

    def save(self, out_dir):
        name = "inputs.json"
        with open(os.path.join(out_dir, name), "w", encoding="utf-8") as f:
            json.dump({"note": "t: seconds since the first picture; "
                               "press: a mouse button went down; click or "
                               "drag: it came up again (at: where it went "
                               "down, to: where a drag ended). Keys typed "
                               "into the chat are never noted.",
                       "events": self.events}, f, indent=0)
        return name


# ---------------------------------------------------------------- Windows
def windows_info():
    """The mouse position and the window in front, for each picture."""
    import ctypes
    from ctypes import wintypes
    user = ctypes.windll.user32
    pt = wintypes.POINT()
    user.GetCursorPos(ctypes.byref(pt))
    hwnd = user.GetForegroundWindow()
    title = ctypes.create_unicode_buffer(200)
    user.GetWindowTextW(hwnd, title, 200)
    rect = wintypes.RECT()
    user.GetWindowRect(hwnd, ctypes.byref(rect))
    client = wintypes.RECT()
    user.GetClientRect(hwnd, ctypes.byref(client))
    origin = wintypes.POINT(0, 0)
    user.ClientToScreen(hwnd, ctypes.byref(origin))
    return {"mouse": [pt.x, pt.y],
            "mouse_left": bool(user.GetAsyncKeyState(0x01) & 0x8000),
            "mouse_right": bool(user.GetAsyncKeyState(0x02) & 0x8000),
            "window": title.value,
            "window_rect": [rect.left, rect.top, rect.right, rect.bottom],
            "game_area": [origin.x, origin.y, client.right, client.bottom]}


def main():
    import ctypes
    import threading
    import tkinter as tk

    import mss
    from PIL import Image

    try:   # so that pictures and positions are in real screen pixels
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        pass
    user = ctypes.windll.user32
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    if not os.path.isdir(desktop):
        desktop = os.path.expanduser("~")

    root = tk.Tk()
    root.title("StarCraft recorder")
    root.attributes("-topmost", True)
    root.resizable(False, False)
    status = tk.StringVar(value="Press F9 (or the button) to start.\n"
                                "Press F9 again to stop.")
    tk.Label(root, textvariable=status, width=46, height=4,
             justify="left").pack(padx=10, pady=6)
    button = tk.Button(root, text="Start", width=14)
    button.pack(pady=(0, 10))

    state = {"on": False, "thread": None, "key_was_down": False}

    def work(out_dir):
        try:
            with mss.mss() as sct:
                mon = sct.monitors[1]

                def grab():
                    shot = sct.grab(mon)
                    return Image.frombytes("RGB", shot.size, shot.bgra,
                                           "raw", "BGRX")
                rec = Recorder(grab, out_dir, info=windows_info)
                rec.t0 = time.time()
                inputs = InputLog(rec.t0)
                listener = threading.Thread(target=listen, args=(inputs,),
                                            daemon=True)
                listener.start()
                more = True
                while state["on"] and more:
                    started = time.time()
                    more = rec.tick()
                    mins = (time.time() - rec.t0) / 60
                    status.set(f"Recording: {mins:.0f} minutes so far "
                               f"(stops by itself at 20).\nPress F9 to stop.")
                    while state["on"] and time.time() - started < INTERVAL:
                        time.sleep(0.05)
                status.set("Packing the pictures ...")
                state["on"] = False          # the listener stops too
                listener.join(timeout=1)
                paths = rec.finish(extra=[inputs.save(out_dir)])
            status.set(f"Done: {len(rec.frames)} pictures, "
                       f"{len(inputs.events)} clicks and keys, in "
                       f"{len(paths)} zip file(s).\nFolder: {out_dir}")
            os.startfile(out_dir)
        except Exception as e:           # show the problem, don't vanish
            status.set(f"Something went wrong:\n{e!r}"[:300])
        state["on"] = False
        button.config(text="Start")

    def listen(inputs):
        """Note the keys and buttons while recording."""
        from ctypes import wintypes
        pt = wintypes.POINT()
        title = ctypes.create_unicode_buffer(200)
        while state["on"]:
            down = [c for c in WATCHED if user.GetAsyncKeyState(c) & 0x8000]
            user.GetCursorPos(ctypes.byref(pt))
            user.GetWindowTextW(user.GetForegroundWindow(), title, 200)
            inputs.feed(time.time(), down, [pt.x, pt.y],
                        is_game(title.value))
            time.sleep(INPUT_EVERY)

    def toggle():
        if state["on"]:
            state["on"] = False          # the worker packs up and stops
            return
        if state["thread"] and state["thread"].is_alive():
            return                       # still packing the last one
        out_dir = os.path.join(
            desktop, "starcraft-recording-" + time.strftime("%Y%m%d-%H%M%S"))
        state["on"] = True
        button.config(text="Stop")
        state["thread"] = threading.Thread(target=work, args=(out_dir,),
                                           daemon=True)
        state["thread"].start()

    def poll():
        down = bool(user.GetAsyncKeyState(HOTKEY) & 0x8000)
        if down and not state["key_was_down"]:
            toggle()
        state["key_was_down"] = down
        root.after(50, poll)

    button.config(command=toggle)
    poll()
    root.mainloop()


if __name__ == "__main__":
    if sys.platform != "win32":
        sys.exit("The recorder runs on Windows only.")
    main()
