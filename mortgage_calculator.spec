# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['mortgage_calculator.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'tkinter', 'tkinter.ttk', 'tkinter.messagebox', 'tkinter.filedialog',
        'matplotlib', 'matplotlib.backends.backend_tkagg',
        'matplotlib.pyplot', 'matplotlib.ticker',
        'ttkbootstrap', 'ttkbootstrap.constants', 'PIL', 'PIL.Image',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='住宅ローン計算アプリ',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,       # コンソール非表示（GUIアプリ）
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
