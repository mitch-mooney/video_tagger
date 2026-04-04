# VideoTagger.spec  — cross-platform (Windows + macOS)
import sys
import os
from pathlib import Path

# ── VLC detection ─────────────────────────────────────────────────────────────
def _find_vlc_dir():
    """Locate VLC DLLs/dylibs regardless of platform."""
    try:
        import vlc
        candidate = Path(vlc.__file__).parent
        dll = 'libvlc.dll' if sys.platform == 'win32' else 'libvlc.dylib'
        if (candidate / dll).exists():
            return candidate
    except Exception:
        pass

    if sys.platform == 'win32':
        search = [
            Path(os.environ.get('PROGRAMFILES', 'C:/Program Files')) / 'VideoLAN' / 'VLC',
            Path(os.environ.get('PROGRAMFILES(X86)', 'C:/Program Files (x86)')) / 'VideoLAN' / 'VLC',
        ]
        for p in search:
            if (p / 'libvlc.dll').exists():
                return p

    elif sys.platform == 'darwin':
        mac_paths = [
            Path('/Applications/VLC.app/Contents/MacOS'),
            Path('/Applications/VLC.app/Contents/MacOS/lib'),
        ]
        for p in mac_paths:
            if (p / 'libvlc.dylib').exists():
                return p

    return None


vlc_dir = _find_vlc_dir()

if sys.platform == 'win32':
    if vlc_dir:
        vlc_binaries = [
            (str(vlc_dir / 'libvlc.dll'), '.'),
            (str(vlc_dir / 'libvlccore.dll'), '.'),
        ]
        vlc_datas = [(str(vlc_dir / 'plugins'), 'plugins')]
    else:
        vlc_binaries = []
        vlc_datas = []
    ffmpeg_datas = [('ffmpeg.exe', '.')] if Path('ffmpeg.exe').exists() else []

elif sys.platform == 'darwin':
    if vlc_dir:
        lib_dir = vlc_dir if 'lib' in str(vlc_dir) else vlc_dir / 'lib'
        vlc_binaries = [
            (str(lib_dir / 'libvlc.dylib'), '.'),
            (str(lib_dir / 'libvlccore.dylib'), '.'),
        ]
        plugins_dir = vlc_dir.parent / 'plugins' if 'MacOS' in str(vlc_dir) else vlc_dir / 'plugins'
        vlc_datas = [(str(plugins_dir), 'plugins')] if plugins_dir.exists() else []
    else:
        vlc_binaries = []
        vlc_datas = []
    ffmpeg_datas = [('ffmpeg', '.')] if Path('ffmpeg').exists() else []

else:
    vlc_binaries = []
    vlc_datas = []
    ffmpeg_datas = []

# ── Analysis ──────────────────────────────────────────────────────────────────
a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=vlc_binaries,
    datas=[
        ('videotagger/resources', 'videotagger/resources'),
    ] + vlc_datas + ffmpeg_datas,
    hiddenimports=['vlc', 'pkgutil', 'PyQt6.QtCore', 'PyQt6.QtWidgets', 'PyQt6.QtGui'],
    hookspath=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

# ── Windows: single-file EXE ──────────────────────────────────────────────────
if sys.platform == 'win32':
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.datas,
        [],
        name='VideoTagger',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        console=False,
        icon=None,
    )

# ── macOS: .app bundle ────────────────────────────────────────────────────────
elif sys.platform == 'darwin':
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name='VideoTagger',
        debug=False,
        strip=False,
        upx=False,
        console=False,
        icon='videotagger/resources/logo.png',
    )
    coll = COLLECT(
        exe,
        a.binaries,
        a.datas,
        strip=False,
        upx=False,
        name='VideoTagger',
    )
    app = BUNDLE(
        coll,
        name='VideoTagger.app',
        icon='videotagger/resources/logo.png',
        bundle_identifier='com.cheapstats.videotagger',
        info_plist={
            'CFBundleName': 'VideoTagger',
            'CFBundleDisplayName': 'VideoTagger',
            'CFBundleVersion': '1.0.0',
            'CFBundleShortVersionString': '1.0.0',
            'NSHighResolutionCapable': True,
            'NSRequiresAquaSystemAppearance': False,
        },
    )
