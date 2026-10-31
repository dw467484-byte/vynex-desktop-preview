# PyInstaller spec for macOS with app icon and privacy purpose strings.
# Compile this file on a macOS runner; PyInstaller is not a cross-compiler.
block_cipher = None

a = Analysis(
    ['VYNEX.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('assets/VYNEX_icon.png', 'assets'),
        ('assets/VYNEX_splash.png', 'assets'),
    ],
    hiddenimports=[],
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
    [],
    exclude_binaries=True,
    name='VYNEX',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='VYNEX',
)
app = BUNDLE(
    coll,
    name='VYNEX.app',
    icon='assets/VYNEX.icns',
    bundle_identifier='com.vynex.desktop',
    version='0.1.0',
    info_plist={
        'NSPrincipalClass': 'NSApplication',
        'LSMinimumSystemVersion': '10.15',
        'NSMicrophoneUsageDescription': 'VYNEX utilise le microphone uniquement lorsque vous lancez la dictée ou la conversation vocale.',
        'NSScreenCaptureUsageDescription': 'VYNEX capture l’écran uniquement après votre confirmation, pour préparer une pièce jointe à un message.',
    },
)
