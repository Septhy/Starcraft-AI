"""The first trial as a small Windows app.

Start it, get into a game as Russia, then press F9. It takes over the
mouse and keyboard for about a minute and a half. Press F9 again to
stop it at any moment.
"""
import os
import sys
import threading
import time


def main():
    import ctypes
    import tkinter as tk

    import mss

    from bot import trial
    from hands.win import STOP_KEY, WinIO

    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        pass
    user = ctypes.windll.user32
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    if not os.path.isdir(desktop):
        desktop = os.path.expanduser("~")

    root = tk.Tk()
    root.title("StarCraft bot: first trial")
    root.attributes("-topmost", True)
    root.resizable(False, False)
    status = tk.StringVar(value="Get into a game as Russia, then press F9.\n"
                                "It will use your mouse and keyboard.\n"
                                "Press F9 again to stop it.")
    tk.Label(root, textvariable=status, width=52, height=5,
             justify="left").pack(padx=10, pady=8)
    state = {"busy": False, "down": False}

    def work():
        out = os.path.join(desktop,
                           "starcraft-trial-" + time.strftime("%Y%m%d-%H%M%S"))
        io = None
        try:
            with mss.mss() as sct:
                io = WinIO(out, sct, status=lambda s: status.set(s[:200]))
                time.sleep(0.6)          # let go of F9 first
                try:
                    result = trial.run(io)
                    io.log(f"finished: {result}")
                except trial.Stopped as e:
                    io.log(f"stopped: {e}")
                except Exception as e:
                    io.log(f"error: {e!r}")
                last = io.lines[-1][9:]
                paths = io.finish()
            status.set(f"{last}\n{len(paths)} zip file(s) in:\n{out}")
            os.startfile(out)
        except Exception as e:
            status.set(f"Something went wrong:\n{e!r}"[:300])
        time.sleep(1.0)
        state["busy"] = False

    def poll():
        down = bool(user.GetAsyncKeyState(STOP_KEY) & 0x8000)
        if down and not state["down"] and not state["busy"]:
            state["busy"] = True
            threading.Thread(target=work, daemon=True).start()
        state["down"] = down
        root.after(50, poll)

    poll()
    root.mainloop()


if __name__ == "__main__":
    if sys.platform != "win32":
        sys.exit("The bot runs on Windows only.")
    main()
