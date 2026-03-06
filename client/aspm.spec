# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('assets/*.ui',  'assets'),    # Qt .ui Dateien
        ('assets/*.png', 'assets'),    # Bilder / Logo
        ('assets/*.ico', 'assets'),    # Windows Icon
    ],
    hiddenimports=[
        'PyQt5.sip',
        'PyQt5.uic',
        'PyQt5.QtPrintSupport',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher,
)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='aspm',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,                     # Kein Konsolenfenster
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/logo.ico',            # Windows Icon
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='aspm',
)

# ── Nur macOS ────────────────────────────────────────────────────────────────
import sys
if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='aspm.app',
        icon='app.icns',               # Wird automatisch im Workflow erzeugt
        bundle_identifier='com.fredima.aspm',
        info_plist={
            'CFBundleName': 'ASPM',
            'CFBundleDisplayName': 'ASPM',
            'CFBundleShortVersionString': '1.0.0',
            'CFBundleVersion': '1.0.0',
            'NSHighResolutionCapable': True,
            'LSMinimumSystemVersion': '10.13.0',
        },
    )