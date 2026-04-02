# VideoTagger.spec
import sys
from pathlib import Path

def _find_vlc_dir():
    """Locate VLC installation: check python-vlc's directory first, then standard install paths."""
    import os
    try:
        import vlc
        candidate = Path(vlc.__file__).parent
        if (candidate / 'libvlc.dll').exists():
            return candidate
    except Exception:
        pass
    for p in [
        Path(os.environ.get('PROGRAMFILES', 'C:/Program Files')) / 'VideoLAN' / 'VLC',
        Path(os.environ.get('PROGRAMFILES(X86)', 'C:/Program Files (x86)')) / 'VideoLAN' / 'VLC',
    ]:
        if (p / 'libvlc.dll').exists():
            return p
    return None

vlc_dir = _find_vlc_dir()
if vlc_dir:
    vlc_binaries = [
        (str(vlc_dir / 'libvlc.dll'), '.'),
        (str(vlc_dir / 'libvlccore.dll'), '.'),
    ]
    vlc_datas = [(str(vlc_dir / 'plugins'), 'plugins')]
else:
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
