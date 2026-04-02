# build.py
import subprocess
import sys

def main():
    print("Building VideoTagger.exe...")
    # Use the Python interpreter that has PyQt6/vlc/pyinstaller installed.
    # On machines with multiple Pythons, prefer 'py -3.9' if available,
    # otherwise fall back to the current interpreter.
    import shutil
    py_launcher = shutil.which("py")
    if py_launcher:
        cmd = [py_launcher, "-3.9", "-m", "PyInstaller", "--clean", "VideoTagger.spec"]
    else:
        cmd = [sys.executable, "-m", "PyInstaller", "--clean", "VideoTagger.spec"]
    subprocess.run(cmd, check=True)
    print("Build complete. Output: dist/VideoTagger.exe")

if __name__ == "__main__":
    main()
