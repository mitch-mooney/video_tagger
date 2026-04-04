# build.py
import subprocess
import sys
import shutil

def main():
    # Use the Python interpreter that has PyQt6/vlc/pyinstaller installed.
    # On machines with multiple Pythons, prefer 'py -3.9' if available,
    # otherwise fall back to the current interpreter.
    py_launcher = shutil.which("py")
    if py_launcher and sys.platform == "win32":
        cmd = [py_launcher, "-3.9", "-m", "PyInstaller", "--clean", "VideoTagger.spec"]
    else:
        cmd = [sys.executable, "-m", "PyInstaller", "--clean", "VideoTagger.spec"]

    print("Building VideoTagger...")
    subprocess.run(cmd, check=True)

    if sys.platform == "darwin":
        _make_dmg()
    elif sys.platform == "win32":
        print("Build complete. Output: dist/VideoTagger.exe")

def _make_dmg():
    """Create a distributable .dmg from the .app bundle (macOS only)."""
    import os
    app = "dist/VideoTagger.app"
    dmg = "dist/VideoTagger.dmg"

    if not os.path.exists(app):
        print(f"ERROR: {app} not found — PyInstaller may have failed.")
        return

    # Remove previous dmg
    if os.path.exists(dmg):
        os.remove(dmg)

    # Try create-dmg (brew install create-dmg) first, fall back to hdiutil
    if shutil.which("create-dmg"):
        subprocess.run([
            "create-dmg",
            "--volname", "VideoTagger",
            "--window-size", "540", "380",
            "--icon-size", "128",
            "--icon", "VideoTagger.app", "130", "170",
            "--app-drop-link", "400", "170",
            dmg,
            app,
        ], check=True)
    else:
        print("create-dmg not found — using hdiutil (no drag-to-Applications UI).")
        print("Install create-dmg for a better result: brew install create-dmg")
        subprocess.run([
            "hdiutil", "create",
            "-volname", "VideoTagger",
            "-srcfolder", app,
            "-ov", "-format", "UDZO",
            dmg,
        ], check=True)

    print(f"Build complete. Output: {dmg}")

if __name__ == "__main__":
    main()
