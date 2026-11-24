"""The keys version of the trial app: before each hit the mass is put
on keys 1 to 7 and spread out in a line, then each key attacks, and the
rest is boxed as usual. Everything else is the same as StarcraftTrial."""
import sys

from bot import app

if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--selftest":
        app.selftest(sys.argv[2])
        sys.exit(0)
    if sys.platform != "win32":
        sys.exit("The bot runs on Windows only.")
    app.main(keys_version=True)
