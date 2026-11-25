"""The allies' "@R tax <city>" and "@R upgrade"."""
from PIL import Image

from bot import team, trial
from tests.test_trial import StubIO, StubWatch, blob


class O:
    def __init__(self, kind, place="", colour="teal", said="@R x"):
        self.kind, self.place, self.colour, self.said = kind, place, colour, said


def by_minimap(monkeypatch):
    """Looking at a city, as the minimap shows it: enemies there, ours
    there (and the screen shows none), or no one of ours to see it."""
    monkeypatch.setattr(trial, "CITY_LOOK_EVERY", 0)

    def look(io, mapdata, name, ours, hostile):
        c = trial.place(mapdata, name)
        xy = (c["x"], c["y"])
        e = len(trial.near(hostile, xy, trial.TAX_ENEMY))
        if e:
            return "enemy", e
        return ("clear", 0) if trial.near(ours, xy, trial.TAX_ENEMY) \
            else ("unseen", 0)
    monkeypatch.setattr(trial, "look_city", look)


def said(monkeypatch):
    out = []
    monkeypatch.setattr(trial, "say", lambda io, st, text, force=False:
                        out.append(text))
    return out


def money_io(values):
    io = StubIO()
    vals = iter(values)
    io.shot = lambda label, keep=True: Image.new("RGB", (1920, 1080))
    return io, vals


def test_upgrade_starts_both_when_the_money_is_there(monkeypatch):
    m = trial.load_map()
    out = said(monkeypatch)
    st = trial.State()
    io = StubIO()
    io.shot = lambda label, keep=True: None
    money = iter([1000, 900, 800])
    monkeypatch.setattr(trial.numbers, "read_minerals", lambda pic: next(money))
    picked = []
    monkeypatch.setattr(trial, "select_building",
                        lambda io_, b: picked.append((b["x"] // 32, b["y"] // 32)) or True)
    trial.upgrade_order(io, m, st)
    assert io.keys == ["w", "a"] and len(set(picked)) == 2   # one bay each
    assert out == ["upgrading infantry weapons 1 and armor 1"]
    assert st.upgrade_level == {"weapons": 1, "armor": 1}
    assert st.upgrade_wanted == {"weapons", "armor"}     # on to levels 2 and 3


def test_upgrade_waits_for_the_money_and_says_so(monkeypatch):
    m = trial.load_map()
    out = said(monkeypatch)
    st = trial.State()
    io = StubIO()
    io.shot = lambda label, keep=True: None
    money = iter([50, 400, 300, 200])
    monkeypatch.setattr(trial.numbers, "read_minerals", lambda pic: next(money))
    monkeypatch.setattr(trial, "select_building", lambda io_, b: True)
    trial.upgrade_order(io, m, st)
    assert out == ["I'll upgrade infantry when I have the resources"]
    assert io.keys == [] and st.upgrade_wanted == {"weapons", "armor"}
    io.t += trial.UPGRADE_EVERY                     # the money has come
    assert trial.upgrade_step(io, m, st)
    assert io.keys == ["w", "a"] and out[-1] == "upgrading infantry weapons 1 and armor 1"


def test_tax_order_secures_the_city_then_builds_a_depot_then_comes_back(monkeypatch):
    m = trial.load_map()
    out = said(monkeypatch)
    by_minimap(monkeypatch)
    st, io = trial.State(), StubIO()
    io.shot = lambda label, keep=True: None
    warsaw = trial.place(m, "Warsaw 200")
    xy = (warsaw["x"], warsaw["y"])
    guards, depots = [], []

    def guard(io_, watch, mapdata, st_, name, picture, why=""):
        guards.append(name)
        return 12
    monkeypatch.setattr(trial, "send_guard", guard)

    def depot(io_, watch, mapdata, st_, name, ours, cc_tile=None, then_home=False):
        depots.append((name, cc_tile, then_home))
        st_.depots.setdefault(name, {"stage": "training", "due": io_.now() + 30})
        return 1
    monkeypatch.setattr(trial, "depot_at", depot)
    back = []
    monkeypatch.setattr(trial, "select_group", lambda *a, **k: True)
    monkeypatch.setattr(trial, "attack_move", lambda io_, x, y: back.append((x, y)))
    trial.tax_order(io, None, m, st, O("tax", "Warsaw"))
    assert out == ["taxing Warsaw"] and "Warsaw 200" in st.tax_jobs
    # enemies there: a detachment first
    watch = StubWatch(blob(xy, 2), blob(xy, 3))
    trial.tax_order_step(io, watch, m, st, None)
    assert guards == ["Warsaw 200"] and depots == []
    # cleared: an SCV from Moscow builds the depot, and goes home after
    watch = StubWatch(blob(xy, 3), set())
    trial.tax_order_step(io, watch, m, st, None)
    trial.tax_order_step(io, watch, m, st, None)
    assert depots[0] == ("Warsaw 200", trial.MOSCOW_CC, True)
    # the depot stands: taxed; the detachment walks back near the mass
    st.depots["Warsaw 200"]["stage"] = "done"
    trial.tax_order_step(io, StubWatch(blob(xy, 3), set()), m, st, None)
    assert out[-1] == "Warsaw taxed" and not st.tax_jobs
    assert back and all(abs(x - trial.MASS[0]) <= trial.BACK_NEAR * 32
                        and abs(y - trial.MASS[1]) <= trial.BACK_NEAR * 32
                        for x, y in back)


def test_a_failed_tax_order_is_said_and_not_tried_again(monkeypatch):
    m = trial.load_map()
    out = said(monkeypatch)
    by_minimap(monkeypatch)
    st, io = trial.State(), StubIO()
    io.shot = lambda label, keep=True: None
    calls = []

    def depot(io_, watch, mapdata, st_, name, ours, cc_tile=None, then_home=False):
        calls.append(1)
        if len(calls) == 1:
            st_.depots[name] = {"stage": "training", "due": io_.now()}
        return 1
    monkeypatch.setattr(trial, "depot_at", depot)
    trial.tax_order(io, None, m, st, O("tax", "Kiev"))
    from bot import places
    kiev = trial.place(m, places.resolve(m, "Kiev"))
    watch = StubWatch(blob((kiev["x"], kiev["y"]), 3), set())
    trial.tax_order_step(io, watch, m, st, None)    # clear: to the depot
    trial.tax_order_step(io, watch, m, st, None)    # the SCV goes
    st.depots.clear()                               # ... and never builds
    trial.tax_order_step(io, watch, m, st, None)
    assert out[-1] == "couldn't tax Ukraine" and not st.tax_jobs
    trial.tax_order_step(io, watch, m, st, None)    # nothing more
    assert len(calls) == 1


def test_the_allies_orders_reach_the_bot():
    got = []
    t = team.Team(lambda s: None, lambda s: None,
                  on_tax=lambda o: got.append(("tax", o.place)),
                  on_upgrade=lambda: got.append(("upgrade",)))
    t.heard(team.Order({"colour": "teal", "kind": "tax", "place": "Warsaw",
                        "said": "@R tax Warsaw"}), 100)
    t.heard(team.Order({"colour": "purple", "kind": "upgrade",
                        "said": "@R upgrade"}), 100)
    assert got == [("tax", "Warsaw"), ("upgrade",)]


def test_the_new_scv_is_ordered_to_the_depot_at_once_then_home(monkeypatch):
    """Trial 31: the SCV is not walked to the city first; picked where it
    waits by the command centre, it is ordered to build by the beacon,
    then goes back to Moscow."""
    m = trial.load_map()
    st, io = trial.State(), StubIO()
    io.shot = lambda label, keep=True: None
    looked = []
    monkeypatch.setattr(trial, "look_at",
                        lambda io_, x, y, wait=0: looked.append((x, y)) or (x, y))
    placing = iter([True, False, True])     # picked; first spot refused
    monkeypatch.setattr(trial.live, "units_selected", lambda pic: next(placing))
    monkeypatch.setattr(trial.live, "selected_count", lambda pic: 1)
    cc = (trial.MOSCOW_CC[0] * 32, trial.MOSCOW_CC[1] * 32 + 128)
    job = {"stage": "training", "due": io.t, "wait": cc, "walk": 50, "looks": 0}
    st.depots["Warsaw 200"] = job
    w = trial.place(m, "Warsaw 200")
    assert trial.depot_by_order(io, m, st, "Warsaw 200", w["x"], w["y"], job) == 1
    assert job["stage"] == "building"
    assert looked[0] == trial.centred(*cc)          # by the centre, not Warsaw
    assert io.keys.count("esc") == 1                 # the first spot refused
    mx, my = trial.MOSCOW_CC
    home = trial.live.minimap_point(mx * 32, my * 32)
    assert io.keys[-1] == "m" and io.clicks[-1] == (*home, "shift")


def test_an_scv_not_seen_at_the_second_look_ends_the_tax(monkeypatch):
    """Trial 31: it kept looking for a lost SCV. Not seen twice: the
    job is dropped, and the tax order says it couldn't tax."""
    m = trial.load_map()
    st, io = trial.State(), StubIO()
    io.shot = lambda label, keep=True: None
    monkeypatch.setattr(trial, "look_at", lambda io_, x, y, wait=0: (x, y))
    monkeypatch.setattr(trial.live, "units_selected", lambda pic: False)
    job = {"stage": "training", "due": io.t, "wait": (100, 100), "looks": 0}
    st.depots["Warsaw 200"] = job
    w = trial.place(m, "Warsaw 200")
    assert trial.depot_by_order(io, m, st, "Warsaw 200", w["x"], w["y"], job) == 0
    assert st.depots["Warsaw 200"]["due"] == io.t + trial.SCV_RECHECK
    trial.depot_by_order(io, m, st, "Warsaw 200", w["x"], w["y"], job)
    assert "Warsaw 200" not in st.depots


def test_tax_orders_keep_money_for_every_city_and_marines_wait(monkeypatch):
    """Trial 30: marines spent everything and the SCV never came. Each
    city asked for keeps 150 back (an SCV and a depot); without enough,
    the ally is told to ask next tax turn."""
    m = trial.load_map()
    out = said(monkeypatch)
    by_minimap(monkeypatch)
    st, io = trial.State(), StubIO()
    io.shot = lambda label, keep=True: None
    money = [320]
    monkeypatch.setattr(trial.numbers, "read_minerals", lambda pic: money[0])
    trial.tax_order(io, None, m, st, O("tax", "Warsaw"))
    trial.tax_order(io, None, m, st, O("tax", "Kiev"))
    trial.tax_order(io, None, m, st, O("tax", "Krakow"))
    assert out == ["taxing Warsaw", "taxing Ukraine",
                   "not enough money to tax Krakow: ask me next tax turn"]
    assert trial.tax_reserve(st) == 2 * trial.TAX_PRICE
    # 320 minerals, 300 kept: no marines now
    monkeypatch.setattr(trial, "room_for_marines", lambda io_: 100)
    assert trial.train_everywhere(io, m, st) == 0
    # once a depot is paid for, its money is free again
    st.tax_jobs["Warsaw 200"]["paid"] = True
    assert trial.tax_reserve(st) == trial.TAX_PRICE


def test_all_three_levels_then_all_upgrades_completed(monkeypatch):
    m = trial.load_map()
    out = said(monkeypatch)
    by_minimap(monkeypatch)
    st, io = trial.State(), StubIO()
    io.shot = lambda label, keep=True: None
    spent = {"m": 5000}

    def minerals(pic):
        return spent["m"]
    monkeypatch.setattr(trial.numbers, "read_minerals", minerals)

    def key(name):
        io.keys.append(name)
        if name in ("w", "a"):
            spent["m"] -= 300
    io.key = key
    monkeypatch.setattr(trial, "select_building", lambda io_, b: True)
    trial.upgrade_order(io, m, st)
    for _ in range(2):                              # levels 2 and 3
        io.t += trial.UPGRADE_TIME
        trial.upgrade_step(io, m, st)
    assert st.upgrade_level == {"weapons": 3, "armor": 3}
    io.t += trial.UPGRADE_TIME                      # the last levels finish
    trial.upgrade_step(io, m, st)
    assert out[-1] == "all upgrades completed" and st.upgrades_done
    keys = len(io.keys)
    io.t += 100
    trial.upgrade_step(io, m, st)                   # the bays left alone
    assert len(io.keys) == keys
    trial.upgrade_order(io, m, st)
    assert out[-1] == "all upgrades completed"


def test_r_commands_lists_every_order_in_short_lines(monkeypatch):
    out = said(monkeypatch)
    st, io = trial.State(), StubIO()
    t = team.Team(lambda s: None, lambda s: None,
                  on_commands=lambda: trial.list_commands(io, st))
    t.heard(team.Order({"colour": "orange", "kind": "commands",
                        "said": "@R commands"}), 100)
    assert out == team.COMMANDS and all(len(line) <= 60 for line in out)
    text = " ".join(out)
    for word in ("hit", "stop", "mass at", "tax", "upgrade", "bring air",
                 "return air", "status", "reset", "commands"):
        assert word in text
    assert "commands" in team.CHAT_SYSTEM


def test_r_commands_is_read_from_the_chat_line_itself_and_typed_once(monkeypatch):
    """Trial 32: "@R Commands" was read but no list came. The line alone
    is enough now; the model's order coming as well types nothing more."""
    out = said(monkeypatch)
    st, io = trial.State(), StubIO()
    assert trial.COMMANDS_ASKED.match("@R Commands")
    assert trial.COMMANDS_ASKED.match("@russia help")
    assert not trial.COMMANDS_ASKED.match("@Reset commands")
    trial.list_commands(io, st)
    trial.list_commands(io, st)                     # the model's copy
    assert out == team.COMMANDS
    io.t += trial.COMMANDS_AGAIN + 1
    trial.list_commands(io, st)
    assert len(out) == 2 * len(team.COMMANDS)


def test_a_city_held_in_strength_waits_for_a_hit_to_clear_it(monkeypatch):
    """Trial 32: Warsaw was held by about 20 Axis; seven men were sent,
    lost, and two minutes later "couldn't tax". Now no detachment is
    thrown at it: the ally is told, and the depot follows once a hit has
    cleared it."""
    m = trial.load_map()
    out = said(monkeypatch)
    by_minimap(monkeypatch)
    st, io = trial.State(), StubIO()
    io.shot = lambda label, keep=True: None
    warsaw = trial.place(m, "Warsaw 200")
    xy = (warsaw["x"], warsaw["y"])
    sent, depots = [], []
    monkeypatch.setattr(trial, "send_guard", lambda *a, **k: sent.append(1) or 12)
    monkeypatch.setattr(trial, "depot_at", lambda *a, **k: depots.append(1) or 0)
    trial.tax_order(io, None, m, st, O("tax", "Warsaw"))
    heavy = StubWatch(set(), blob(xy, 5))
    assert len(trial.near(heavy.others(None, trial.HOSTILE), xy,
                          trial.TAX_ENEMY)) > trial.TAX_HEAVY
    trial.tax_order_step(io, heavy, m, st, None)
    assert sent == [] and st.tax_jobs["Warsaw 200"]["stage"] == "held"
    assert out[-1].startswith("Axis hold Warsaw")
    io.t += trial.ORDER_TAX_SECURE + 10             # still held: it waits
    trial.tax_order_step(io, heavy, m, st, None)
    assert "Warsaw 200" in st.tax_jobs
    seen = StubWatch(blob(xy, 3), set())
    trial.tax_order_step(io, seen, m, st, None)     # cleared, and seen so
    assert st.tax_jobs["Warsaw 200"]["stage"] == "depot"
    trial.tax_order_step(io, seen, m, st, None)
    assert depots
    # never cleared: given up in the end
    st.tax_jobs.clear()
    trial.tax_order(io, None, m, st, O("tax", "Warsaw"))
    trial.tax_order_step(io, heavy, m, st, None)
    io.t += trial.ORDER_TAX_HELD + 1
    trial.tax_order_step(io, heavy, m, st, None)
    assert out[-1] == "couldn't tax Warsaw" and not st.tax_jobs


def test_too_few_men_to_send_waits_as_well(monkeypatch):
    m = trial.load_map()
    out = said(monkeypatch)
    by_minimap(monkeypatch)
    st, io = trial.State(), StubIO()
    io.shot = lambda label, keep=True: None
    xy = (trial.place(m, "Warsaw 200")["x"], trial.place(m, "Warsaw 200")["y"])
    monkeypatch.setattr(trial, "send_guard", lambda *a, **k: 5)
    trial.tax_order(io, None, m, st, O("tax", "Warsaw"))
    trial.tax_order_step(io, StubWatch(set(), blob(xy, 2)), m, st, None)
    assert st.tax_jobs["Warsaw 200"]["stage"] == "held"


def test_a_city_with_no_enemy_is_clear_and_the_detachment_goes_back_at_once(monkeypatch):
    """The repository owner: clear means no enemy there at all; the men
    need not stay while the SCV comes."""
    m = trial.load_map()
    said(monkeypatch)
    by_minimap(monkeypatch)
    st, io = trial.State(), StubIO()
    io.shot = lambda label, keep=True: None
    xy = (trial.place(m, "Warsaw 200")["x"], trial.place(m, "Warsaw 200")["y"])
    monkeypatch.setattr(trial, "send_guard", lambda *a, **k: 12)
    monkeypatch.setattr(trial, "depot_at", lambda *a, **k: 0)
    monkeypatch.setattr(trial, "select_group", lambda *a, **k: True)
    back = []
    monkeypatch.setattr(trial, "attack_move", lambda io_, x, y: back.append((x, y)))
    trial.tax_order(io, None, m, st, O("tax", "Warsaw"))
    one = {next(iter(blob(xy, 1)))}
    trial.tax_order_step(io, StubWatch(blob(xy, 3), one), m, st, None)
    job = st.tax_jobs["Warsaw 200"]
    assert job["stage"] == "secure" and job["guard"]    # one enemy: not clear
    trial.tax_order_step(io, StubWatch(blob(xy, 3), set()), m, st, None)
    assert job["stage"] == "depot" and not job["guard"] and back
    assert "Warsaw 200" not in st.guards


def test_a_city_russia_can_see_is_looked_at_not_sent_to(monkeypatch):
    """Trial 33 (the repository owner): with something of ours there to
    see it, a look at the screen settles it; no enemy, and the SCV comes
    at once, no detachment. Unseen, a detachment goes to look."""
    from PIL import Image
    m = trial.load_map()
    w = trial.place(m, "Warsaw 200")
    xy = (w["x"], w["y"])
    io = StubIO()
    io.shot = lambda label, keep=True: Image.new("RGB", (1920, 1080), (60, 70, 40))
    monkeypatch.setattr(trial, "look_at", lambda io_, x, y, wait=0: (x, y))
    assert trial.look_city(io, m, "Warsaw 200", blob(xy, 2), set()) == ("clear", 0)
    assert trial.look_city(io, m, "Warsaw 200", set(), set()) == ("unseen", 0)
    assert trial.look_city(io, m, "Warsaw 200", blob(xy, 2), blob(xy, 2))[0] == "enemy"
    monkeypatch.setattr(trial, "enemy_on_screen", lambda *a, **k: 3)
    assert trial.look_city(io, m, "Warsaw 200", blob(xy, 2), set())[0] == "enemy"

    out = said(monkeypatch)
    by_minimap(monkeypatch)
    st = trial.State()
    io.shot = lambda label, keep=True: None
    sent, depots = [], []
    monkeypatch.setattr(trial, "send_guard",
                        lambda *a, **k: sent.append(k.get("why")) or 12)
    monkeypatch.setattr(trial, "depot_at", lambda *a, **k: depots.append(1) or 1)
    monkeypatch.setattr(trial, "select_group", lambda *a, **k: True)
    monkeypatch.setattr(trial, "attack_move", lambda *a: None)
    trial.tax_order(io, None, m, st, O("tax", "Warsaw"))
    trial.tax_order_step(io, StubWatch(blob(xy, 2), set()), m, st, None)
    assert sent == [] and st.tax_jobs["Warsaw 200"]["stage"] == "depot"
    # unseen: a detachment goes to look; once it sees the city clear, on
    st.tax_jobs.clear()
    trial.tax_order(io, None, m, st, O("tax", "Warsaw"))
    trial.tax_order_step(io, StubWatch(set(), set()), m, st, None)
    assert sent == ["to look"] and st.tax_jobs["Warsaw 200"]["guard"]
    trial.tax_order_step(io, StubWatch(blob(xy, 2), set()), m, st, None)
    assert st.tax_jobs["Warsaw 200"]["stage"] == "depot"


def test_the_detachments_time_counts_from_when_it_is_sent(monkeypatch):
    """Trial 33: "@R tax romania" waited out a hit, sent its men 105 s
    later, and gave up 22 s after that."""
    m = trial.load_map()
    out = said(monkeypatch)
    by_minimap(monkeypatch)
    st, io = trial.State(), StubIO()
    io.shot = lambda label, keep=True: None
    r = trial.place(m, "Romania 300")
    xy = (r["x"], r["y"])
    monkeypatch.setattr(trial, "send_guard", lambda *a, **k: 12)
    trial.tax_order(io, None, m, st, O("tax", "Romania"))
    io.t += 105                                     # a hit in between
    trial.tax_order_step(io, StubWatch(set(), blob(xy, 2)), m, st, None)
    io.t += 22
    trial.tax_order_step(io, StubWatch(set(), blob(xy, 2)), m, st, None)
    assert "Romania 300" in st.tax_jobs and "couldn't" not in " ".join(out)


def test_the_new_scv_rallies_on_the_screen_and_waits_for_supply(monkeypatch):
    m = trial.load_map()
    st, io = trial.State(), StubIO()
    io.shot = lambda label, keep=True: None
    monkeypatch.setattr(trial, "select_building", lambda io_, b: True)
    monkeypatch.setattr(trial, "look_at", lambda io_, x, y, wait=0: (x, y))
    full = [True]
    monkeypatch.setattr(trial, "supply_full", lambda io_: full[0])
    assert trial.depot_at(io, None, m, st, "Warsaw 200", set(),
                          cc_tile=trial.MOSCOW_CC, then_home=True) == 0
    assert st.depots["Warsaw 200"]["stage"] == "supply" and "s" not in io.keys
    full[0] = False
    assert trial.depot_at(io, None, m, st, "Warsaw 200", set(),
                          cc_tile=trial.MOSCOW_CC, then_home=True) == 1
    job = st.depots["Warsaw 200"]
    cc = next(b for b in m["slots"][trial.SLOT]["buildings"]
              if b["type"] == "Command Center"
              and (b["x"] // 32, b["y"] // 32) == trial.MOSCOW_CC)
    sx, sy = trial.live.on_screen(*job["wait"], (cc["x"], cc["y"]))
    assert (sx, sy, "right") in io.clicks           # on the screen, not the minimap
    assert job["look"] == (cc["x"], cc["y"])        # picked with the same view
