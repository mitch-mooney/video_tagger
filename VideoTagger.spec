# VideoTagger.spec
import sys
from pathlib import Path

try:
    import vlc
    vlc_dir = Path(vlc.__file__).parent
    vlc_binaries = [
        (str(vlc_dir / 'libvlc.dll'), '.'),
        (str(vlc_dir / 'libvlccore.dll'), '.'),
    ]
    vlc_datas = [(str(vlc_dir / 'plugins'), 'plugins')]
except Exception:
    vlc_binaries = []
    vlc_datas = []

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=vlc_binaries,
    datas=[
        ('videotagger/resources', 'videotagger/resources'),
    ] + vlc_datas,
    hiddenimports=['vlc', 'PyQt6.QtCore', 'PyQt6.QtWidgets', 'PyQt6.QtGui'],
    hookspath=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

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
