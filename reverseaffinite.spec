# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('/usr/lib/python3/dist-packages/PyQt5', 'PyQt5'), ('/usr/lib/python3/dist-packages/numpy', 'numpy'), ('/usr/local/lib/python3.12/dist-packages/PIL', 'PIL'), ('/usr/local/lib/python3.12/dist-packages/psd_tools', 'psd_tools')]
binaries = []
hiddenimports = ['editor', 'editor.file_formats', 'editor.file_formats.psd_import', 'psd_tools', 'psd_tools.api', 'psd_tools.compression', 'psd_tools.compression.rle']
tmp_ret = collect_all('editor')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='reverseaffinite',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
