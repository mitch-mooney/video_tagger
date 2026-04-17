# VideoTagger.spec  — cross-platform (Windows + macOS)
import sys
from pathlib import Path
from glob import glob

# ── FFmpeg ──────────────────────────────────────────────────────────────────
if sys.platform == 'win32':
    ffmpeg_datas = [('ffmpeg.exe', '.')] if Path('ffmpeg.exe').exists() else []
elif sys.platform == 'darwin':
    ffmpeg_datas = [('ffmpeg', '.')] if Path('ffmpeg').exists() else []
else:
    ffmpeg_datas = []

# ── QtMultimedia backend plugins ─────────────────────────────────────────────
# Discover the PyQt6 package directory at build time so this works regardless
# of venv location, system Python, or CI runner paths.
_pyqt6_dir = Path(__import__('PyQt6').__file__).parent
_mm_dir = _pyqt6_dir / 'Qt6' / 'plugins' / 'multimedia'

if sys.platform == 'win32':
    # Use only the WMF backend — ffmpegmediaplugin.dll ships without its
    # FFmpeg DLL dependencies and fails to load at runtime.
    _win_plugin = _mm_dir / 'windowsmediaplugin.dll'
    platform_binaries = (
        [(str(_win_plugin), 'PyQt6/Qt6/plugins/multimedia')]
        if _win_plugin.exists() else []
    )
elif sys.platform == 'darwin':
    # Include all .dylib files found in the multimedia plugin directory.
    platform_binaries = [
        (p, 'PyQt6/Qt6/plugins/multimedia')
        for p in glob(str(_mm_dir / '*.dylib'))
    ]
else:
    platform_binaries = []

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=platform_binaries,
    datas=[
        ('videotagger/resources', 'videotagger/resources'),
    ] + ffmpeg_datas,
    hiddenimports=[
        'pkgutil',
        'PyQt6.QtCore',
        'PyQt6.QtWidgets',
        'PyQt6.QtGui',
        'PyQt6.QtMultimedia',
        'PyQt6.QtMultimediaWidgets',
    ],
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
            'CFBundleVersion': '2.0.0',
            'CFBundleShortVersionString': '2.0.0',
            'NSHighResolutionCapable': True,
            'NSRequiresAquaSystemAppearance': False,
        },
    )
