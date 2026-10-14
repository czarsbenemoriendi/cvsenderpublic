#!/usr/bin/env python3
"""CDP-free apply channel for CVSender — no chrome.debugger, no DevTools.

Two independent primitives (research/2026-09-09-antibot-form-driving.md §4):

1. AppleScript `execute javascript` — drives the REAL Chrome tab in its normal
   main world: same V8 context, cookies, extensions; no CDP session, no
   Runtime.enable, no navigator.webdriver. Synthetic events dispatched this
   way are still isTrusted:false — this channel fixes the CDP-leak class, not
   behavior-based fingerprinting.

   ONE-TIME USER OPT-IN (do not enable programmatically, ever):
       Chrome menu: View -> Developer -> Allow JavaScript from Apple Events
   (or default: `defaults write com.google.Chrome AllowJavaScriptAppleEvents -bool true`
   then restart Chrome). detect_applescript() reports this state; when the
   opt-in is missing it returns instructions instead of failing mysteriously.

2. Trusted clicks — macOS posts real CGEvents into the window server
   (`isTrusted:true`, indistinguishable from a human click):
       - `cliclick` if installed (brew install cliclick), else
       - pyobjc Quartz (pip package — OPTIONAL, project itself stays stdlib), else
       - unavailable: instructions returned.
   Screen coords = window position + element viewport rect; on Retina the
   POINT size is what CGEvents expect — divide CSS pixels by nothing, but
   add the window's content-area origin (see viewport_to_screen()).

Honest limits: foreground-tab oriented, no network interception, no
waitForResponse (poll in-page instead), no native file-picker automation.
Status CLI (safe pre-opt-in):  python3 lib/nocdp.py --status
Live probe:                    python3 lib/nocdp.py --js "document.title"
Stdlib only (subprocess, shutil, json).
"""

import json
import shutil
import subprocess
import sys

CHROME_APPLESCRIPT = """
tell application "Google Chrome"
    tell {target} of front window to execute javascript "{js}"
end tell
"""


def _run_osascript(script):
    """Return (returncode, stdout, stderr). Never raises on AppleScript errors."""
    proc = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True, text=True, timeout=30,
    )
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def chrome_running():
    """Cheap pgrep check — avoids poking TCC permission dialogs needlessly."""
    proc = subprocess.run(["pgrep", "-x", "Google Chrome"],
                          capture_output=True, text=True)
    return proc.returncode == 0


def detect_applescript():
    """Probe the execute-javascript channel WITHOUT changing anything.

    Returns {"available": bool, "state": str, "instruction": str|None}.
    A trivial "1+1" in the active tab is the probe (read-only)."""
    if not chrome_running():
        return {"available": False, "state": "chrome-not-running",
                "instruction": "Start Google Chrome, open any tab, then re-run "
                               "nocdp --status."}
    rc, out, err = _run_osascript(
        CHROME_APPLESCRIPT.format(target="active tab", js="1+1"))
    blob = (out + " " + err).lower()
    if rc == 0 and out.strip() == "2":
        return {"available": True, "state": "ready", "instruction": None}
    if "turned off" in blob or "allow javascript from apple events" in blob \
            or "-1743" in blob or "not authorized" in blob:
        return {"available": False, "state": "opt-in-missing",
                "instruction": "One-time opt-in required (user action, never "
                               "automate it): Chrome menu View -> Developer -> "
                               "Allow JavaScript from Apple Events, then "
                               "restart Chrome."}
    if "assistive" in blob or "-1719" in blob or "-25211" in blob:
        return {"available": False, "state": "permissions",
                "instruction": "Grant the calling app (Terminal/omp) "
                               "Automation permission: System Settings -> "
                               "Privacy & Security -> Automation."}
    return {"available": False, "state": "error",
            "instruction": f"osascript rc={rc} out={out[:120]!r} err={err[:200]!r}"}


def execute_js(js, target="active tab"):
    """Run JS in a real Chrome tab. Returns (ok, result_or_error_text)."""
    state = detect_applescript()
    if not state["available"]:
        return False, state["instruction"]
    # keep quotes safe inside the AppleScript string literal
    safe_js = js.replace("\\", "\\\\").replace('"', '\\"')
    rc, out, err = _run_osascript(
        CHROME_APPLESCRIPT.format(target=target, js=safe_js))
    if rc == 0:
        return True, out
    return False, err or f"osascript rc={rc}"


# ------------------------------------------------------- trusted clicks

def cliclick_available():
    return shutil.which("cliclick") is not None


def quartz_available():
    try:
        import Quartz  # noqa: F401 — pyobjc, optional non-project dependency
        return True
    except ImportError:
        return False


def click_capabilities():
    return {"cliclick": cliclick_available(), "quartz": quartz_available()}


def viewport_to_screen(x, y, window_x, window_y):
    """CSS-pixel viewport coords + window content origin -> screen point.
    (CGEvents take points; on Retina CSS px == points, the 2x is device px.)"""
    return window_x + x, window_y + y


def click(x, y):
    """One real (isTrusted:true) click at SCREEN coordinates.

    Prefers cliclick, falls back to Quartz. Returns (ok, detail)."""
    if cliclick_available():
        proc = subprocess.run(["cliclick", "-e", "80", "c:%d,%d" % (x, y)],
                              capture_output=True, text=True, timeout=15)
        return proc.returncode == 0, f"cliclick rc={proc.returncode} {proc.stderr.strip()}"
    if quartz_available():
        # Quartz via a tiny python -c to stay out of AppleScript land
        code = (
            "import Quartz, time;"
            f"e=Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseDown, ({x},{y}), 0);"
            "Quartz.CGEventPost(Quartz.kCGHIDEventTap, e);"
            "time.sleep(0.06);"
            f"e=Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseUp, ({x},{y}), 0);"
            "Quartz.CGEventPost(Quartz.kCGHIDEventTap, e)"
        )
        proc = subprocess.run([sys.executable, "-c", code],
                              capture_output=True, text=True, timeout=15)
        return proc.returncode == 0, f"quartz rc={proc.returncode} {proc.stderr.strip()}"
    return False, ("No trusted-click backend. Install one: `brew install "
                   "cliclick` (recommended) or `pip install pyobjc-framework-Quartz`.")

def status():
    report = {
        "chrome_running": chrome_running(),
        "applescript": detect_applescript(),
        "trusted_click": click_capabilities(),
    }
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    if "--status" in sys.argv:
        status()
    elif "--js" in sys.argv:
        ok, result = execute_js(sys.argv[sys.argv.index("--js") + 1])
        print(("OK: " if ok else "FAIL: ") + result)
        sys.exit(0 if ok else 1)
    else:
        print(__doc__)
