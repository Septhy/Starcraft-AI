"""The recorder inside the bot (the repository owner, trial 41): while
the bot plays, the whole screen is kept twice a second, as the
StarcraftRecorder app does, with the screen setup (monitors, scale, the
game window) at the start and the end. Up to 20 minutes; packed next to
the bot's own log as screen-part1.zip, screen-part2.zip ...

It runs in its own thread with its own screen grabber and never touches
the game, the mouse or the keyboard. Nothing it does can stop the bot:
a problem is noted and the recording ends.
"""
import os
import threading
import time

from recorder import recorder as rec


class ScreenRecording:
    def __init__(self, out_dir, make_grab, info=lambda: {},
                 setup=lambda: {}, interval=rec.INTERVAL,
                 max_frames=rec.MAX_FRAMES, clock=time.time,
                 sleep=time.sleep):
        self.out_dir = out_dir
        self.work_dir = os.path.join(out_dir, "screen")
        self.make_grab, self.info, self.setup = make_grab, info, setup
        self.interval, self.max_frames = interval, max_frames
        self.clock, self.sleep = clock, sleep
        self.on = False
        self.thread = None
        self.frames = 0
        self.problem = None
        self.paths = []

    def start(self):
        self.on = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        return self

    def _run(self):
        try:
            with self.make_grab() as (grab, monitor):
                r = rec.Recorder(grab, self.work_dir, info=self.info,
                                 setup=self.setup,
                                 max_frames=self.max_frames,
                                 clock=self.clock)
                if isinstance(r.setup_start, dict) and monitor:
                    r.setup_start["recorded_monitor"] = dict(monitor)
                more = True
                while self.on and more:
                    started = self.clock()
                    more = r.tick()
                    self.frames = len(r.frames)
                    while self.on and self.clock() - started < self.interval:
                        self.sleep(0.05)
                paths = r.finish()
            for i, p in enumerate(paths, 1):
                dest = os.path.join(self.out_dir, f"screen-part{i}.zip")
                os.replace(p, dest)
                self.paths.append(dest)
            try:
                os.rmdir(self.work_dir)
            except OSError:
                pass
        except Exception as e:         # never stops the bot
            self.problem = repr(e)
        self.on = False

    def stop(self, wait=180):
        """Stop and pack. Returns the zip files made."""
        self.on = False
        if self.thread is not None:
            self.thread.join(timeout=wait)
        return list(self.paths)


def windows_grab():
    """A grabber for the main monitor, made in the recording's own thread
    (a screen grabber may only be used by the thread that made it)."""
    from contextlib import contextmanager

    @contextmanager
    def make():
        import mss
        from PIL import Image
        with mss.mss() as sct:
            mon = sct.monitors[1]

            def grab():
                shot = sct.grab(mon)
                return Image.frombytes("RGB", shot.size, shot.bgra, "raw",
                                       "BGRX")
            yield grab, mon
    return make
