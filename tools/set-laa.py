"""Let Split/Second (a 32-bit game) use 4 GB of address space instead of 2 GB: sets the exe's
large-address-aware flag. Needed for long sessions on the DLC build, whose bigger data can run the
game out of address space (crash with E_OUTOFMEMORY after ~10 minutes).

  python set-laa.py            show the flag
  python set-laa.py --apply    set it (copies the exe to SplitSecond.exe.before-laa first)
  python set-laa.py --restore  clear it again
  --exe <path>                 the game's SplitSecond.exe (default: found through Steam)

Only one bit of the PE file header changes. The game must be closed. Needs 64-bit Windows.
Licensed under the GNU General Public License v3.0 (see LICENSE).
"""
import argparse, os, re, shutil, struct, subprocess, sys

LAA = 0x0020


def find_exe():
    steam = r"C:\Program Files (x86)\Steam"
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam") as k:
            steam = winreg.QueryValueEx(k, "SteamPath")[0]
    except OSError:
        pass
    libs = [steam]
    vdf = os.path.join(steam, "steamapps", "libraryfolders.vdf")
    if os.path.exists(vdf):
        libs += [p.replace("\\\\", "\\") for p in re.findall(r'"path"\s+"([^"]+)"', open(vdf, encoding="utf-8").read())]
    for lib in libs:
        exe = os.path.join(lib, "steamapps", "common", "SplitSecond", "SplitSecond.exe")
        if os.path.exists(exe):
            return exe
    return None


def characteristics_offset(f):
    f.seek(0x3C)
    pe = struct.unpack("<I", f.read(4))[0]
    f.seek(pe)
    if f.read(4) != b"PE\0\0":
        sys.exit("not a PE file")
    return pe + 4 + 18  # IMAGE_FILE_HEADER.Characteristics


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--restore", action="store_true")
    ap.add_argument("--exe")
    a = ap.parse_args()
    exe = a.exe or find_exe()
    if not exe or not os.path.exists(exe):
        sys.exit('SplitSecond.exe not found; pass --exe "<path>"')
    with open(exe, "rb") as f:
        off = characteristics_offset(f)
        f.seek(off)
        ch = struct.unpack("<H", f.read(2))[0]
    print(f"{exe}: large address aware: {'yes' if ch & LAA else 'no'}")
    if not (a.apply or a.restore):
        return
    want = ch | LAA if a.apply else ch & ~LAA
    if want == ch:
        print("nothing to change")
        return
    if "SplitSecond.exe" in subprocess.run(["tasklist", "/FI", "IMAGENAME eq SplitSecond.exe"], capture_output=True, text=True).stdout:
        sys.exit("close Split/Second first")
    if a.apply and not os.path.exists(exe + ".before-laa"):
        shutil.copy2(exe, exe + ".before-laa")
        print(f"backup: {exe}.before-laa")
    with open(exe, "r+b") as f:
        f.seek(off)
        f.write(struct.pack("<H", want))
    print(f"large address aware: {'yes' if want & LAA else 'no'}")


if __name__ == "__main__":
    main()
