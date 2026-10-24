#!/usr/bin/env python3
"""Install a debug APK on the running emulator and capture store-style screenshots.

Usage: capture.py <apk> <out_dir>

The app is walked generically: home, every bottom-navigation tab, the navigation
drawer if there is one, the first item on the home screen, and home in dark mode.
Optional hints in .github/screenshots/taps.txt (one label per line) are tapped in
order after the generic pass, each followed by a screenshot.
"""
import glob
import os
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

APK, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
DISMISS = ["Skip", "SKIP", "Get started", "Get Started", "Continue", "Allow", "ALLOW", "OK", "Ok",
           "Agree", "Accept", "Consent", "Got it", "Not now", "No thanks", "Later", "Close", "Dismiss", "Wait"]
counter = [0]


def adb(*args, check=False):
    return subprocess.run(["adb", *args], capture_output=True, text=True, check=check).stdout


def package_name():
    tools = sorted(glob.glob(os.path.expandvars("$ANDROID_HOME/build-tools/*/aapt2")))
    out = subprocess.run([tools[-1], "dump", "packagename", APK], capture_output=True, text=True).stdout
    return out.strip()


def size():
    m = re.search(r"(\d+)x(\d+)", adb("shell", "wm", "size"))
    return int(m.group(1)), int(m.group(2))


def nodes(tries=2):
    raw = ""
    for _ in range(tries):
        adb("shell", "rm", "-f", "/sdcard/ui.xml")
        adb("shell", "uiautomator", "dump", "/sdcard/ui.xml")
        raw = adb("shell", "cat", "/sdcard/ui.xml")
        if "<hierarchy" in raw:
            break
        time.sleep(3)  # the UI was not idle (an animation is running); try again
    try:
        root = ET.fromstring(raw[raw.find("<"):])
    except ET.ParseError:
        return []
    result = []
    for n in root.iter("node"):
        b = re.findall(r"\d+", n.get("bounds", ""))
        if len(b) != 4:
            continue
        x1, y1, x2, y2 = map(int, b)
        label = (n.get("text") or n.get("content-desc") or "").strip()
        result.append({"label": label, "clickable": n.get("clickable") == "true",
                       "box": (x1, y1, x2, y2), "pkg": n.get("package", "")})
    return result


def tap(box):
    x1, y1, x2, y2 = box
    adb("shell", "input", "tap", str((x1 + x2) // 2), str((y1 + y2) // 2))


def find(label):
    for n in nodes():
        first = n["label"].split("\n")[0]
        if first == label or n["label"] == label:
            return n
    return None


def dismiss_popups(rounds=3):
    for _ in range(rounds):
        hit = False
        for n in nodes():
            first = n["label"].split("\n")[0]
            if first in DISMISS:
                tap(n["box"])
                hit = True
                time.sleep(2)
                break
        if not hit:
            return


def foreground(pkg):
    out = adb("shell", "dumpsys", "window")
    m = re.search(r"mCurrentFocus=.*?\{[^}]*\s(\S+)/(\S+)\}", out)
    return m and m.group(1) == pkg and "Ad" not in m.group(2).split(".")[-1]


def settle(pkg, wait=6):
    time.sleep(wait)
    for _ in range(3):
        if foreground(pkg):
            break
        adb("shell", "input", "keyevent", "KEYCODE_BACK")  # close an interstitial or app-open ad
        time.sleep(2)
    dismiss_popups()


START = time.time()


def late():
    return time.time() - START > 18 * 60  # leave time to publish what we have


def shot(name):
    if late():
        print("out of time, skipping", name)
        return
    dismiss_popups(1)
    counter[0] += 1
    path = os.path.join(OUT, f"{counter[0]:02d}_{name}.png")
    with open(path, "wb") as f:
        f.write(subprocess.run(["adb", "exec-out", "screencap", "-p"], capture_output=True).stdout)
    print("captured", path)


def launch(pkg):
    adb("shell", "am", "force-stop", pkg)
    adb("shell", "monkey", "-p", pkg, "-c", "android.intent.category.LAUNCHER", "1")
    settle(pkg, 25)
    time.sleep(20)  # give remote images time to load on the slow emulator
    dismiss_popups()


def bottom_nav(w, h):
    found = nodes()
    items = [n for n in found if n["clickable"] and n["box"][1] > h * 0.82
             and (n["box"][3] - n["box"][1]) < h * 0.15 and (n["box"][2] - n["box"][0]) < w * 0.45]
    if items:  # keep the lowest row only, so a banner ad above the tabs is ignored
        low = max(n["box"][1] for n in items)
        items = [n for n in items if abs(n["box"][1] - low) < h * 0.03]
    items.sort(key=lambda n: n["box"][0])
    for it in items:  # Compose puts the tab's text on a child node
        if not it["label"]:
            x1, y1, x2, y2 = it["box"]
            it["label"] = next((n["label"] for n in found if n["label"] and n["box"][0] >= x1 and n["box"][2] <= x2
                                and n["box"][1] >= y1 and n["box"][3] <= y2), "")
    if 2 <= len(items) <= 6:
        return items
    print("no bottom navigation found among", len(found), "nodes")
    return []


def slug(text, fallback):
    s = re.sub(r"[^a-z0-9]+", "_", text.split("\n")[0].lower()).strip("_")
    return s[:24] or fallback


def main():
    pkg = package_name()
    print("package", pkg)
    adb("install", "-r", "-g", APK, check=True)
    adb("shell", "settings", "put", "global", "window_animation_scale", "0")
    adb("shell", "settings", "put", "global", "transition_animation_scale", "0")
    adb("shell", "cmd", "uimode", "night", "no")
    w, h = size()
    time.sleep(60)  # let the freshly booted system settle so it doesn't show "isn't responding"
    dismiss_popups()

    launch(pkg)
    shot("home")

    tabs = bottom_nav(w, h)
    for i, t in enumerate(tabs[1:], start=2):
        tap(t["box"])
        settle(pkg, 12)
        shot(slug(t["label"], f"tab{i}"))
    if tabs:
        tap(tabs[0]["box"])
        settle(pkg, 3)

    menu = next((n for n in nodes() if re.search(r"menu|navigation|drawer", n["label"], re.I)
                 and n["box"][1] < h * 0.2), None)
    if menu:
        tap(menu["box"])
        time.sleep(3)
        shot("menu")
        adb("shell", "input", "keyevent", "KEYCODE_BACK")
        time.sleep(2)

    # First item of the content area (grid tile, article card or station row)
    adb("shell", "input", "tap", str(int(w * 0.27)), str(int(h * 0.42)))
    settle(pkg, 15)
    shot("detail")
    adb("shell", "input", "keyevent", "KEYCODE_BACK")
    time.sleep(2)

    hints = ".github/screenshots/taps.txt"
    if os.path.exists(hints):
        for line in open(hints):
            label = line.strip()
            if not label or label.startswith("#"):
                continue
            n = find(label)
            if n:
                tap(n["box"])
                settle(pkg, 5)
                shot(slug(label, "extra"))
            else:
                print("hint not found:", label)

    adb("shell", "cmd", "uimode", "night", "yes")
    launch(pkg)
    shot("home_dark")
    adb("shell", "cmd", "uimode", "night", "no")


if __name__ == "__main__":
    try:
        main()
    finally:  # keep the crash log next to the screenshots, it explains an empty or missing screen
        with open(os.path.join(OUT, "crash-log.txt"), "w") as f:
            f.write(adb("logcat", "-d", "-b", "crash"))
