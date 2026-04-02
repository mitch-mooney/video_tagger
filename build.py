# build.py
import subprocess
import sys

def main():
    print("Building VideoTagger.exe...")
    subprocess.run(
        [sys.executable, "-m", "PyInstaller", "--clean", "VideoTagger.spec"],
        check=True
    )
    print("Build complete. Output: dist/VideoTagger.exe")

if __name__ == "__main__":
    main()
