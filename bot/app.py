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

    from tkinter import simpledialog

    from bot import general as general_module
    from bot import memory, trial
    from hands import secret
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
                                "This window hides while it plays.\n"
                                "Press F9 again to stop it.")
    tk.Label(root, textvariable=status, width=52, height=5,
             justify="left").pack(padx=10, pady=8)
    state = {"busy": False, "down": False}
    key_label = tk.StringVar()

    def show_key_state():
        key_label.set("Claude key: saved on this PC. The general will advise."
                      if secret.load() else
                      "Claude key: none. The bot plays by its rules alone.")

    def set_key():
        key = simpledialog.askstring(
            "Claude API key", "Paste your Claude API key.\n"
            "It is kept on this PC only, locked to your Windows account.\n"
            "Leave empty to remove it.", show="*", parent=root)
        if key is None:
            return
        if not key.strip():
            secret.forget()
            show_key_state()
            return
        secret.save(key)
        key_label.set("Claude key: checking it ...")

        def check():
            ok, message = general_module.check_key(
                secret.load(), memory.load_model(general_module.MODEL))
            key_label.set("Claude key: " + message)
        threading.Thread(target=check, daemon=True).start()

    tk.Label(root, textvariable=key_label, width=52).pack()
    tk.Button(root, text="Set Claude API key", command=set_key).pack(pady=(0, 6))
    show_key_state()
    labels = {text: model for model, text in general_module.CHOICES}
    by_model = {model: text for model, text in general_module.CHOICES}
    chosen = tk.StringVar(value=by_model.get(
        memory.load_model(general_module.MODEL),
        by_model[general_module.MODEL]))
    tk.Label(root, text="Which Claude model commands:").pack()
    tk.OptionMenu(root, chosen, *labels,
                  command=lambda text: memory.save_model(labels[text])
                  ).pack(pady=(0, 8))

    def work():
        out = os.path.join(desktop,
                           "starcraft-trial-" + time.strftime("%Y%m%d-%H%M%S"))
        io = None
        # Hide this window while the bot plays. Left on screen, the bot
        # can click it by accident, which takes StarCraft out of front.
        root.after(0, root.withdraw)
        try:
            with mss.mss() as sct:
                io = WinIO(out, sct, status=lambda s: status.set(s[:200]))
                time.sleep(0.6)          # let go of F9 first
                try:
                    advisor = general_module.make(
                        secret.load(), lessons=memory.load(),
                        model=memory.load_model(general_module.MODEL))
                    result = trial.run(io, general=advisor,
                                       save_lessons=memory.save)
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
        root.after(0, root.deiconify)
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


def selftest(path):
    """Used by the build to check that everything needed is packed in."""
    import anthropic

    from bot import general, trial
    from eyes import numbers
    general.General(anthropic.Anthropic(api_key="not-a-real-key"))
    trial.load_map()
    numbers._load()
    open(path, "w").write("ok " + anthropic.__version__)


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--selftest":
        selftest(sys.argv[2])
        sys.exit(0)
    if sys.platform != "win32":
        sys.exit("The bot runs on Windows only.")
    main()
