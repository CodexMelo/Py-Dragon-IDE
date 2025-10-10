# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path

block_cipher = None

# Encontrar o caminho correto do setuptools
def find_setuptools_path():
    try:
        import setuptools
        setuptools_path = Path(setuptools.__file__).parent
        lorem_path = setuptools_path / '_vendor' / 'jaraco' / 'text' / 'Lorem ipsum.txt'
        if lorem_path.exists():
            return str(lorem_path), 'setuptools/_vendor/jaraco/text/'
    except:
        pass
    return None, None

lorem_source, lorem_dest = find_setuptools_path()

datas_list = []
if lorem_source and lorem_dest:
    datas_list.append((lorem_source, lorem_dest))

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas_list,  # Usar a lista dinâmica
    hiddenimports=[
        'pkg_resources',
        'setuptools',
        'setuptools.extern',
        'setuptools._vendor',
        'setuptools._vendor.jaraco',
        'setuptools._vendor.jaraco.text',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='PyDragonStudio',
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
    icon=None,
)