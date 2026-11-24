"""The rel version of the trial app: as the keys version, but the keyed
groups line up by where the mass stands from the target: to the top
right of it, a line on the mass's left; to the bottom right, on its
right; level with it, half on each side."""
import sys

from bot import app

if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--selftest":
        app.selftest(sys.argv[2])
        sys.exit(0)
    if sys.platform != "win32":
        sys.exit("The bot runs on Windows only.")
    app.main(rel_version=True)
