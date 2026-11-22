"""Keep the API key on this computer, locked to this Windows user.

The key is encrypted with Windows' own data protection, so only the
same Windows account on the same PC can read it back. It is stored in
the user's AppData folder, never in the log, the pictures or the zips.
"""
import ctypes
import os
from ctypes import wintypes


class _Blob(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD),
                ("pbData", ctypes.POINTER(ctypes.c_char))]


def _path():
    folder = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")),
                          "StarcraftBot")
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, "claude-key.bin")


def _crypt(data, protect):
    crypt32, kernel32 = ctypes.windll.crypt32, ctypes.windll.kernel32
    buf = ctypes.create_string_buffer(data, len(data))
    src = _Blob(len(data), ctypes.cast(buf, ctypes.POINTER(ctypes.c_char)))
    dst = _Blob()
    fn = crypt32.CryptProtectData if protect else crypt32.CryptUnprotectData
    if not fn(ctypes.byref(src), None, None, None, None, 0, ctypes.byref(dst)):
        raise OSError("Windows could not protect or read the key")
    try:
        return ctypes.string_at(dst.pbData, dst.cbData)
    finally:
        kernel32.LocalFree(dst.pbData)


def save(key):
    with open(_path(), "wb") as f:
        f.write(_crypt(key.strip().encode("utf-8"), protect=True))


def load():
    try:
        with open(_path(), "rb") as f:
            return _crypt(f.read(), protect=False).decode("utf-8")
    except (OSError, ValueError):
        return None


def forget():
    try:
        os.remove(_path())
    except OSError:
        pass
