"""Screen recorder for building the StarCraft screen reader.

Run it, start StarCraft, press F9 to start and F9 again to stop. It
saves a picture of the screen every few seconds, with the mouse
position, and packs them into zip files on the Desktop.

It only takes pictures. It does not touch the game, the mouse or the
keyboard.
"""
import json
import os
import sys
import time
import zipfile

INTERVAL = 3.0          # seconds between pictures
MAX_FRAMES = 120        # stop by itself after this many
PNG_EVERY = 10          # every n-th picture is also kept exact (PNG)
JPEG_QUALITY = 88
PART_BYTES = 18 * 1024 * 1024   # zip parts are kept under this size
HOTKEY = 0x78           # F9


class Recorder:
    """Takes the pictures and packs them. Knows nothing about Windows."""

    def __init__(self, grab, out_dir, info=lambda: {}, max_frames=MAX_FRAMES,
                 png_every=PNG_EVERY, clock=time.time):
        self.grab, self.info, self.clock = grab, info, clock
        self.out_dir, self.max_frames, self.png_every = \
            out_dir, max_frames, png_every
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
        name = f"frame{n:04d}.jpg"
        img.save(os.path.join(self.out_dir, name), quality=JPEG_QUALITY)
        files = [name]
        if n % self.png_every == 0:
            exact = f"frame{n:04d}.png"
            img.save(os.path.join(self.out_dir, exact))
            files.append(exact)
        entry = {"files": files, "seconds": round(now - self.t0, 2),
                 "size": list(img.size)}
        entry.update(self.info())
        self.frames.append(entry)
        return len(self.frames) < self.max_frames

    def finish(self, part_bytes=PART_BYTES):
        """Write the notes file and pack everything into zip parts."""
        with open(os.path.join(self.out_dir, "info.json"), "w",
                  encoding="utf-8") as f:
            json.dump({"frames": self.frames}, f, indent=1)
        names = ["info.json"] + [n for e in self.frames for n in e["files"]]
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
                more = True
                while state["on"] and more:
                    started = time.time()
                    more = rec.tick()
                    status.set(f"Recording: {len(rec.frames)} of "
                               f"{MAX_FRAMES} pictures.\nPress F9 to stop.")
                    while state["on"] and time.time() - started < INTERVAL:
                        time.sleep(0.05)
                status.set("Packing the pictures ...")
                paths = rec.finish()
            status.set(f"Done: {len(rec.frames)} pictures in "
                       f"{len(paths)} zip file(s).\nFolder: {out_dir}")
            os.startfile(out_dir)
        except Exception as e:           # show the problem, don't vanish
            status.set(f"Something went wrong:\n{e!r}"[:300])
        state["on"] = False
        button.config(text="Start")

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
