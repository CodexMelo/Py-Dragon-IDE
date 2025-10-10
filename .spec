# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        # Incluir arquivos de dados do setuptools manualmente
        ('venv/Lib/site-packages/setuptools/_vendor/jaraco/text/Lorem ipsum.txt', 'setuptools/_vendor/jaraco/text/'),
        ('venv/Lib/site-packages/setuptools/_vendor/jaraco/text/__init__.py', 'setuptools/_vendor/jaraco/text/'),
    ],
    hiddenimports=[
        'pkg_resources',
        'setuptools',
        'setuptools._vendor.jaraco.text',
    ],
    hookspath=['hooks'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    icon='icon.ico',  # Adicione um ícone se desejar
)