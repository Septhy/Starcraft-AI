"""The settings the bot was trained with, shown the way the game's own
Options screen shows them, so players can copy them one by one.

The page is a list of simple shapes (layout()), drawn by the app's
window with tkinter (show()) and, for checking, into a picture with
PIL (picture()). The values are the repository owner's own settings
(StarCraft: Remastered, Options > Video) and the screen size the bot
reads the game at.
"""

WINDOWS = [
    ("Screen resolution", "1920 x 1080 (Windows Settings > System > Display)"),
    ("Scale", "100%"),
    ("StarCraft window", "in front of everything, nothing over it"),
]

VIDEO = {
    "display_mode": "Windowed (Fullscreen)",
    "gamma": (0.79, 7),          # between notches: 79% of the way to max,
                                 # just short of the 6th of 7 notches
    "fps_cap": False,            # its slider is left at 300
    "sd_filter": (0, 4),         # Sharp
    "boxes": [("Enable Vertical Sync", False), ("HD Graphics", True),
              ("Environment Effects", False), ("Real-Time Lighting", False),
              ("Smooth Unit Turning", True), ("Shadow Stacking", True),
              ("Pillarbox", False)],
}

W, H = 1160, 860
BLACK, RED, DARK_RED = "#000000", "#8c1010", "#3c0606"
GREEN, YELLOW, GREY = "#8fe06a", "#f2e43a", "#c9c9d6"
WHITE, DIM = "#ffffff", "#8a8a96"


def layout():
    """The page as shapes: ("rect", x0, y0, x1, y1, outline, fill),
    ("text", x, y, text, colour, size, anchor), ("oval", x0, y0, x1, y1,
    outline, fill), ("line", x0, y0, x1, y1, colour, width)."""
    out = [("rect", 0, 0, W, H, BLACK, BLACK),
           ("rect", 8, 8, W - 8, H - 8, RED, BLACK),
           ("text", 50, 66, "Recommended settings", WHITE, 26, "w"),
           ("text", 52, 108, "The bot was trained with these. Copy them before "
            "you start it.", GREY, 11, "w")]
    # the tabs down the left, Video picked, as in the game
    for k, tab in enumerate(["Speed", "Sound", "Video", "Game", "Network"]):
        y = 150 + k * 70
        out.append(("rect", 4, y, 242, y + 54, RED,
                    BLACK if tab == "Video" else DARK_RED))
        out.append(("text", 123, y + 27, tab,
                    WHITE if tab == "Video" else GREEN, 16, "center"))
    x0, x1 = 288, 675
    # Display Mode
    out += [("text", x0, 141, "Display Mode", GREY, 12, "w"),
            ("rect", x0, 157, x1, 189, RED, BLACK),
            ("text", x0 + 6, 173, VIDEO["display_mode"], GREEN, 12, "w")]
    # Gamma
    out.append(("text", x0, 294, "Gamma Correction", DIM, 12, "w"))
    out += slider(x0 + 12, x1 - 12, 322, *VIDEO["gamma"], line=DIM,
                  pick=WHITE)
    out += [("text", x0, 354, "min", DIM, 10, "w"),
            ("text", x1, 354, "max", DIM, 10, "e")]
    # right column
    r0, r1 = 705, 1092
    out += checkbox(r0, 143, "Enable FPS Cap", VIDEO["fps_cap"])
    out += slider(r0 + 12, r1 - 12, 185, 6, 7, line=DIM, pick=WHITE)
    out += [("text", r0, 216, "100", GREY, 10, "w"),
            ("text", r1, 216, "300", GREY, 10, "e"),
            ("text", r0, 271, "SD Graphics Filter", WHITE, 12, "w")]
    out += slider(r0 + 12, r1 - 12, 300, *VIDEO["sd_filter"], line=RED,
                  pick=YELLOW)
    out += [("text", r0, 331, "Sharp", GREY, 10, "w"),
            ("text", r1, 331, "Filtered", GREY, 10, "e")]
    for k, (name, on) in enumerate(VIDEO["boxes"]):
        out += checkbox(r0, 388 + k * 40.5, name, on)
    # Windows, below
    out += [("line", 270, 680, W - 40, 680, RED, 1),
            ("text", 288, 708, "Windows", WHITE, 14, "w")]
    for k, (name, value) in enumerate(WINDOWS):
        y = 742 + k * 30
        out += [("text", 288, y, name, GREY, 12, "w"),
                ("text", 470, y, value, GREEN, 12, "w")]
    return out


def checkbox(x, y, label, on):
    out = [("rect", x, y - 10, x + 20, y + 10, RED, BLACK)]
    if on:
        out.append(("rect", x + 5, y - 5, x + 15, y + 5, YELLOW, YELLOW))
    out.append(("text", x + 31, y, label, GREY, 12, "w"))
    return out


def slider(x0, x1, y, picked, notches, line, pick):
    """A slider with its notches; `picked` is a notch's number, or a
    share of the way from left to right (0.0 to 1.0) for a knob that
    sits between notches."""
    out = [("line", x0, y, x1, y, line, 3)]
    if isinstance(picked, float):
        at, picked = x0 + (x1 - x0) * picked, None
    for k in range(notches):
        x = x0 + (x1 - x0) * k / (notches - 1)
        if k == picked:
            at = x
        else:
            out.append(("oval", x - 7, y - 7, x + 7, y + 7, DIM, BLACK))
    out.append(("oval", at - 10, y - 10, at + 10, y + 10, pick, BLACK))
    out.append(("oval", at - 5, y - 5, at + 5, y + 5, pick, pick))
    return out


def show(root, tk):
    """Open the page in a window of its own over the app's."""
    top = tk.Toplevel(root)
    top.title("Recommended settings")
    top.resizable(False, False)
    canvas = tk.Canvas(top, width=W, height=H, bg=BLACK, highlightthickness=0)
    canvas.pack()
    for op in layout():
        kind = op[0]
        if kind == "rect":
            _, a, b, c, d, outline, fill = op
            canvas.create_rectangle(a, b, c, d, outline=outline, fill=fill,
                                    width=2)
        elif kind == "oval":
            _, a, b, c, d, outline, fill = op
            canvas.create_oval(a, b, c, d, outline=outline, fill=fill, width=2)
        elif kind == "line":
            _, a, b, c, d, colour, width = op
            canvas.create_line(a, b, c, d, fill=colour, width=width)
        else:
            _, x, y, text, colour, size, anchor = op
            canvas.create_text(x, y, text=text, fill=colour,
                               font=("Segoe UI", size), anchor=anchor)
    tk.Button(top, text="Close", command=top.destroy).pack(pady=6)
    return top


def picture(path=None):
    """The page drawn into a picture (to check it, without a screen)."""
    from PIL import Image, ImageDraw, ImageFont
    im = Image.new("RGB", (W, H), BLACK)
    d = ImageDraw.Draw(im)
    fonts = {}

    def font(size):
        if size not in fonts:
            try:
                fonts[size] = ImageFont.truetype("DejaVuSans.ttf", size + 4)
            except OSError:
                fonts[size] = ImageFont.load_default()
        return fonts[size]
    anchors = {"w": "lm", "e": "rm", "center": "mm"}
    for op in layout():
        kind = op[0]
        if kind == "rect":
            _, a, b, c, e, outline, fill = op
            d.rectangle((a, b, c, e), outline=outline, fill=fill, width=2)
        elif kind == "oval":
            _, a, b, c, e, outline, fill = op
            d.ellipse((a, b, c, e), outline=outline, fill=fill, width=2)
        elif kind == "line":
            _, a, b, c, e, colour, width = op
            d.line((a, b, c, e), fill=colour, width=width)
        else:
            _, x, y, text, colour, size, anchor = op
            d.text((x, y), text, fill=colour, font=font(size),
                   anchor=anchors[anchor])
    if path:
        im.save(path)
    return im
