# VideoTagger.spec  — cross-platform (Windows + macOS)
import sys
from pathlib import Path

if sys.platform == 'win32':
    ffmpeg_datas = [('ffmpeg.exe', '.')] if Path('ffmpeg.exe').exists() else []
elif sys.platform == 'darwin':
    ffmpeg_datas = [('ffmpeg', '.')] if Path('ffmpeg').exists() else []
else:
    ffmpeg_datas = []

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=(
        # Windows: only the WMF backend — ffmpegmediaplugin.dll ships without its
        # FFmpeg DLL dependencies and fails to load, causing Qt to find no backends.
        [('.venv/lib/site-packages/PyQt6/Qt6/plugins/multimedia/windowsmediaplugin.dll',
          'PyQt6/Qt6/plugins/multimedia')]
        if sys.platform == 'win32' else
        # macOS: AVFoundation backend; discovered at build time from the active venv.
        [(str(Path(__import__('PyQt6').__file__).parent /
              'Qt6' / 'plugins' / 'multimedia' / 'libqdarwinmediaplugin.dylib'),
          'PyQt6/Qt6/plugins/multimedia')]
        if sys.platform == 'darwin' else []
    ),
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
