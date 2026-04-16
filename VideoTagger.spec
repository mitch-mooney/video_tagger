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
    binaries=[],
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
