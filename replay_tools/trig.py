"""Print the map's triggers that mention a word. Usage: trig.py map.chk word [word...]"""
import struct, sys
sys.path.insert(0, __file__.rsplit("/", 1)[0])
import chk
sec, st = chk.load(sys.argv[1]); words = [w.lower() for w in sys.argv[2:]]
mrgn = sec["MRGN"][-1]
def loc(i):
    if i == 0: return "-"
    l, t, r, b, sid, _ = struct.unpack_from("<4IHH", mrgn, (i - 1) * 20)
    return f"[{chk.clean(st.get(sid, '?'))} @{(l + r) // 64},{(t + b) // 64}]"
U = {0:"Marine",1:"Ghost",2:"Vulture",3:"Goliath",5:"Siege Tank",7:"SCV",8:"Wraith",9:"Science Vessel",11:"Dropship",12:"Battlecruiser",20:"Raynor(Marine)",32:"Firebat",34:"Medic",58:"Valkyrie",60:"Corsair",64:"Probe",65:"Zealot",66:"Dragoon",69:"Shuttle",70:"Scout",72:"Carrier",229:"Any unit",230:"Men",231:"Buildings",232:"Factories"}
unix = sec.get("UNIx", sec.get("UNIS"))[-1]
def unit(u):
    return U.get(u, f"unit{u}")
def grp(g):
    return {13:"current player",17:"all players",18:"Force1",19:"Force2",20:"Force3",21:"Force4"}.get(g, f"P{g+1}" if g < 12 else f"grp{g}")
COND = {1:"CountdownTimer",2:"Command",3:"Bring",4:"Accumulate",5:"Kill",6:"CommandMost",11:"Switch",12:"ElapsedTime",15:"Deaths",22:"Always",23:"Never"}
ACT = {1:"Victory",2:"Defeat",3:"PreserveTrigger",4:"Wait",7:"Transmission",8:"PlayWAV",9:"DisplayText",10:"CenterView",11:"CreateUnitWithProps",12:"SetObjectives",13:"SetSwitch",14:"SetCountdown",22:"KillUnit",23:"KillUnitAt",24:"RemoveUnit",25:"RemoveUnitAt",26:"SetResources",27:"SetScore",28:"MinimapPing",38:"MoveUnit",39:"GiveUnits",44:"CreateUnit",45:"SetDeaths",46:"Order",47:"Comment",48:"GiveUnits",49:"ModifyHP",57:"SetAllianceStatus"}
trig = sec["TRIG"][-1]
for n in range(len(trig) // 2400):
    t = trig[n * 2400:(n + 1) * 2400]
    conds, acts, text = [], [], ""
    for i in range(16):
        l, g, amt, uid, cmp_, c, res, fl = struct.unpack_from("<IIIHBBBB", t, i * 20)
        if c == 0: continue
        conds.append(f"{COND.get(c, c)}({grp(g)}, {amt}, {unit(uid)}, cmp{cmp_}, {loc(l)})")
    for i in range(64):
        l, s, wav, tm, g1, g2, uid, a, num, fl = struct.unpack_from("<IIIIIIHBBB", t, 320 + i * 32)
        if a == 0: continue
        txt = chk.clean(st.get(s, "")) if s else ""
        text += " " + txt
        acts.append(f"{ACT.get(a, a)}({grp(g1)}, n={num}, {unit(uid)}, at {loc(l)}, g2={g2}{', ' + repr(txt[:110]) if txt else ''})")
    players = [i for i in range(27) if t[320 + 2048 + 4 + i]]
    blob = (" ".join(conds) + " " + " ".join(acts)).lower()
    if any(w in blob for w in words):
        print(f"--- trigger {n} for {[grp(p) for p in players]}")
        for c in conds: print("   IF ", c)
        for a in acts: print("   DO ", a)
