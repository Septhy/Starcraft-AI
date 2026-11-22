"""Read a StarCraft map (CHK) dumped from a replay and summarise it."""
import struct
import sys
from collections import Counter, defaultdict


def sections(data):
    out, i = defaultdict(list), 0
    while i + 8 <= len(data):
        name = data[i:i + 4].decode("latin1")
        size = struct.unpack_from("<i", data, i + 4)[0]
        if size < 0:
            break
        out[name].append(data[i + 8:i + 8 + size])
        i += 8 + size
    return out


def strings(sec):
    if "STRx" in sec:
        d = sec["STRx"][-1]
        n = struct.unpack_from("<I", d, 0)[0]
        offs = struct.unpack_from(f"<{n}I", d, 4)
    else:
        d = sec["STR "][-1]
        n = struct.unpack_from("<H", d, 0)[0]
        offs = struct.unpack_from(f"<{n}H", d, 2)
    res = {}
    for k, o in enumerate(offs):
        if 0 < o < len(d):
            end = d.find(b"\0", o)
            raw = d[o:end if end >= 0 else len(d)]
            for enc in ("utf-8", "cp949", "cp1252"):
                try:
                    res[k + 1] = raw.decode(enc)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                res[k + 1] = raw.decode("latin1")
    return res


def clean(s):
    return "".join(c if c >= " " else ("\\n" if c in "\r\n" else "")
                   for c in s)


def load(path):
    sec = sections(open(path, "rb").read())
    return sec, strings(sec)


if __name__ == "__main__":
    sec, st = load(sys.argv[1])
    what = sys.argv[2] if len(sys.argv) > 2 else "summary"
    if what == "summary":
        print({k: [len(x) for x in v] for k, v in sec.items()})
        sprp = struct.unpack_from("<2H", sec["SPRP"][-1])
        print("NAME:", clean(st.get(sprp[0], "")))
        print("DESC:", clean(st.get(sprp[1], "")))
        f = sec["FORC"][-1].ljust(20, b"\0")
        pf = list(f[:8])
        fn = struct.unpack_from("<4H", f, 8)
        print("player->force:", pf, "| force flags", list(f[16:20]))
        for i, s in enumerate(fn):
            print("  force", i, clean(st.get(s, "")))
        print("OWNR:", list(sec["OWNR"][-1][:12]))
        print("SIDE:", list(sec["SIDE"][-1][:12]))
        print("strings:", len(st))
    elif what == "strings":
        for k in sorted(st):
            print(k, "|", clean(st[k])[:300])
