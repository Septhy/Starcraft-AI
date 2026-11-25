"""The "back first" version of the trial app (StarcraftTrialBackFirst):
as the line ahead version (the mass keyed on 1 to 7 while massing, in a
line ahead of it), but at the hit seven groups are formed and sent from
the back of the mass before the keys attack. Everything else is the same
as StarcraftTrial."""
import sys

from bot import app

if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--selftest":
        app.selftest(sys.argv[2])
        sys.exit(0)
    if sys.platform != "win32":
        sys.exit("The bot runs on Windows only.")
    app.main(back_version=True)
