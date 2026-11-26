"""The general's lessons from earlier games: a small text file on this
PC. Nothing secret is kept in it."""
import os

LIMIT = 2000        # characters


def _path():
    folder = os.environ.get("STARCRAFT_BOT_HOME") or os.path.join(
        os.environ.get("APPDATA", os.path.expanduser("~")), "StarcraftBot")
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, "lessons.txt")


def load():
    try:
        with open(_path(), encoding="utf-8") as f:
            return f.read()[:LIMIT]
    except OSError:
        return ""


def save(text):
    with open(_path(), "w", encoding="utf-8") as f:
        f.write(text[:LIMIT])


def _settings_path():
    return os.path.join(os.path.dirname(_path()), "settings.txt")


def load_model(default):
    try:
        with open(_settings_path(), encoding="utf-8") as f:
            return f.read().strip() or default
    except OSError:
        return default


def save_model(model):
    with open(_settings_path(), "w", encoding="utf-8") as f:
        f.write(model)


COUNTRIES = ("Russia", "Norway")


def _country_path():
    return os.path.join(os.path.dirname(_path()), "country.txt")


def load_country():
    """The country the bot plays (Russia unless Norway was chosen)."""
    try:
        with open(_country_path(), encoding="utf-8") as f:
            c = f.read().strip()
            return c if c in COUNTRIES else "Russia"
    except OSError:
        return "Russia"


def save_country(country):
    with open(_country_path(), "w", encoding="utf-8") as f:
        f.write(country if country in COUNTRIES else "Russia")
