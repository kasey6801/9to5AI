# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = []
binaries = []
hiddenimports = []

for pkg in [
    'flask', 'werkzeug',
    'feedparser',
    'requests', 'urllib3',
    'bs4', 'lxml',
    'certifi', 'charset_normalizer',
]:
    try:
        d, b, h = collect_all(pkg)
        datas        += d
        binaries     += b
        hiddenimports += h
    except Exception:
        pass

hiddenimports += [
    'flask',
    'werkzeug',
    'werkzeug.serving',
    'werkzeug.routing',
    'feedparser',
    'bs4',
    'lxml.html',
    'lxml.etree',
    'xml.etree.ElementTree',
    'email.mime.multipart',
    'email.mime.text',
    'concurrent.futures',
]

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter', 'matplotlib', 'IPython',
        'notebook', 'pytest', 'unittest',
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='9to5AI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,          # UPX corrupts Python dylibs on Apple Silicon
    console=False,      # No terminal window when launched from Finder
    disable_windowed_traceback=False,
    argv_emulation=False,
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
    name='9to5AI',
)

app = BUNDLE(
    coll,
    name='9to5AI.app',
    icon=None,
    bundle_identifier='com.9to5ai.app',
    version='0.42',
    info_plist={
        'NSPrincipalClass': 'NSApplication',
        'NSHighResolutionCapable': True,
        'LSBackgroundOnly': False,
        'NSHumanReadableCopyright': '9to5AI — AI News Aggregator',
        'CFBundleShortVersionString': '0.42',
        'CFBundleVersion': '42',
        'LSMinimumSystemVersion': '12.0',
        'NSAppTransportSecurity': {
            'NSAllowsArbitraryLoads': True,
        },
    },
)
