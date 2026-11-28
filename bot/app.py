"""The first trial as a small Windows app.

Start it and get into a game as the country chosen in its window. It
starts by itself when the game begins (bot/autostart.py) and takes over
the mouse and keyboard for up to two hours, or until the game ends.
Press F9 to stop it at any moment.
"""
import os
import sys
import threading
import time


def main(keys_version=False, rel_version=False, back_version=False):
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

    if keys_version:
        trial.HIT_STYLE = "keys"        # hits: the mass on keys, in a line
    if rel_version:
        trial.HIT_STYLE = "rel"         # the line placed by where the mass is
    if back_version:
        trial.HIT_STYLE = "back7"       # seven groups from the back, then keys
    root = tk.Tk()
    root.title("StarCraft bot: first trial"
               + (" (line ahead)" if keys_version else "")
               + (" (line beside)" if rel_version else "")
               + (" (back first)" if back_version else "")
               + f" - build {trial.build_id()}")
    root.attributes("-topmost", True)
    root.resizable(False, False)
    status = tk.StringVar(value="Choose the country below and get into a game.\n"
                                "The bot starts by itself when the game begins\n"
                                "and uses your mouse and keyboard.\n"
                                "This window hides while it plays.\n"
                                "Press F9 to stop it.")
    tk.Label(root, textvariable=status, width=52, height=5,
             justify="left").pack(padx=10, pady=8)
    state = {"busy": False, "down": False}
    key_label = tk.StringVar()
    # The light beside the key: green when Anthropic accepts it, red
    # when it does not, yellow while checking, grey with no key.
    LIGHTS = {"ok": "#2ecc40", "bad": "#e03131", "checking": "#f0b400",
              "none": "#9a9a9a"}
    key_row = tk.Frame(root)
    key_row.pack()
    light = tk.Canvas(key_row, width=18, height=18, highlightthickness=0)
    light.pack(side="left", padx=(0, 6))
    dot = light.create_oval(2, 2, 16, 16, fill=LIGHTS["none"], outline="#555555")
    tk.Label(key_row, textvariable=key_label, width=50, anchor="w").pack(side="left")
    key_state = {"light": "none", "text": ""}

    def show(light_name, text):
        # called from the checking thread too: the window is only
        # touched from its own loop, in refresh() below
        key_state["light"], key_state["text"] = light_name, text

    def refresh():
        light.itemconfig(dot, fill=LIGHTS[key_state["light"]])
        key_label.set(key_state["text"])
        root.after(200, refresh)

    def check_key():
        """Ask Anthropic whether the saved key is accepted."""
        key = secret.load()
        if not key:
            show("none", "Claude key: none. The bot plays by its rules alone.")
            return
        show("checking", "Claude key: checking it ...")

        def work():
            ok, message = general_module.check_key(
                key, memory.load_model(general_module.MODEL))
            show("ok" if ok else "bad",
                 "Claude key: active. " + message if ok
                 else "Claude key: NOT working. " + message)
        threading.Thread(target=work, daemon=True).start()

    def set_key():
        key = simpledialog.askstring(
            "Claude API key", "Paste your Claude API key.\n"
            "It is kept on this PC only, locked to your Windows account.\n"
            "Leave empty to remove it.", show="*", parent=root)
        if key is None:
            return
        if key.strip():
            secret.save(key)
        else:
            secret.forget()
        check_key()

    tk.Button(root, text="Set Claude API key", command=set_key).pack(pady=(0, 6))
    from bot import settings_view
    tk.Button(root, text="Recommended settings",
              command=lambda: settings_view.show(root, tk)).pack(pady=(0, 6))
    check_key()                         # the saved key is checked at start
    refresh()
    labels = {text: model for model, text in general_module.CHOICES}
    by_model = {model: text for model, text in general_module.CHOICES}
    chosen = tk.StringVar(value=by_model.get(
        memory.load_model(general_module.MODEL),
        by_model[general_module.MODEL]))
    country = tk.StringVar(value=memory.load_country())
    tk.Label(root, text="Which country the bot plays:").pack()
    tk.OptionMenu(root, country, *memory.COUNTRIES,
                  command=lambda c: memory.save_country(c)).pack(pady=(0, 8))
    tk.Label(root, text="Which Claude model commands:").pack()
    tk.OptionMenu(root, chosen, *labels,
                  command=lambda text: (memory.save_model(labels[text]),
                                        check_key())
                  ).pack(pady=(0, 8))

    def work():
        out = os.path.join(desktop,
                           "starcraft-trial-" + time.strftime("%Y%m%d-%H%M%S"))
        io = None
        # Hide this window while the bot plays. Left on screen, the bot
        # can click it by accident, which takes StarCraft out of front.
        root.after(0, root.withdraw)
        # the screen kept twice a second while it plays, as the
        # recorder app does (the repository owner: one app, not two)
        from bot import screen_rec
        from recorder import recorder as rec_mod
        recording = None
        try:
            os.makedirs(out, exist_ok=True)
            recording = screen_rec.ScreenRecording(
                out, screen_rec.windows_grab(), info=rec_mod.windows_info,
                setup=rec_mod.setup_info).start()
        except Exception:
            recording = None
        try:
            with mss.mss() as sct:
                io = WinIO(out, sct, status=lambda s: status.set(s[:200]))
                try:
                    key = secret.load()
                    advisor = general_module.make(
                        key, lessons=memory.load(),
                        model=memory.load_model(general_module.MODEL))
                    from bot import team
                    play = trial
                    if country.get() == "Norway":
                        from bot import norway as play
                    io.log(f"playing {country.get()}")
                    result = play.run(io, general=advisor,
                                       save_lessons=memory.save,
                                       ears=team.make_ears(key))
                    io.log(f"finished: {result}")
                except trial.Stopped as e:
                    io.log(f"stopped: {e}")
                except Exception as e:
                    io.log(f"error: {e!r}")
                last = io.lines[-1][9:]
                if recording is not None:
                    status.set("Packing the screen recording ...")
                    shots = recording.stop()
                    io.log(f"screen recording: {recording.frames} pictures in "
                           f"{len(shots)} zip file(s)"
                           + (f" (problem: {recording.problem})"
                              if recording.problem else ""))
                paths = io.finish()
                if recording is not None:
                    paths = list(paths) + recording.paths
            status.set(f"{last}\n{len(paths)} zip file(s) in:\n{out}")
            os.startfile(out)
        except Exception as e:
            if recording is not None:
                recording.stop()
            status.set(f"Something went wrong:\n{e!r}"[:300])
        root.after(0, root.deiconify)
        time.sleep(1.0)
        starter.played()                # not again for the same game
        state["busy"] = False

    def start():
        if not state["busy"]:
            state["busy"] = True
            threading.Thread(target=work, daemon=True).start()

    # The bot starts by itself when a game begins (the owner: the seconds
    # until F9 is pressed count); F9 only stops it. The button is there in
    # case a game is not noticed.
    from bot import autostart
    from eyes import live as live_eyes
    from hands.win import GAME_WINDOW
    starter = autostart.Starter()
    tk.Button(root, text="Start now (if it did not start by itself)",
              command=start).pack(pady=(0, 8))
    watcher = {"sct": None, "last": 0.0}

    def game_in_front():
        title = ctypes.create_unicode_buffer(200)
        user.GetWindowTextW(user.GetForegroundWindow(), title, 200)
        return title.value == GAME_WINDOW

    def look():
        from PIL import Image
        if watcher["sct"] is None:
            watcher["sct"] = mss.mss()
        shot = watcher["sct"].grab(watcher["sct"].monitors[1])
        return Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")

    def poll():
        now = time.time()
        if not state["busy"] and now - watcher["last"] >= autostart.LOOK_EVERY:
            watcher["last"] = now
            try:
                if game_in_front() and starter.look(look()):
                    start()
            except Exception:
                pass
        root.after(50, poll)

    poll()
    root.mainloop()


def selftest(path):
    """Used by the build to check that everything needed is packed in."""
    import anthropic

    from bot import general, norway, screen_rec, team, trial
    from eyes import clock, numbers
    from recorder import recorder as rec_mod
    assert screen_rec.ScreenRecording and rec_mod.setup_info
    general.General(anthropic.Anthropic(api_key="not-a-real-key"))
    team.ChatEars(anthropic.Anthropic(api_key="not-a-real-key"))
    trial.load_map()
    numbers._load()
    clock.templates()
    from bot import places, settings_view
    places.reachable()
    settings_view.layout()
    open(path, "w").write("ok " + anthropic.__version__)


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--selftest":
        selftest(sys.argv[2])
        sys.exit(0)
    if sys.platform != "win32":
        sys.exit("The bot runs on Windows only.")
    main()
