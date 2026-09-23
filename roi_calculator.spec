from pathlib import Path
import runpy

version = runpy.run_path("src/roi_calculator/version.py")["__version__"]
name = f"ROI-Calculator-v{version}"
icon = "build/roi_calculator.ico" if Path("build/roi_calculator.ico").exists() else None

a = Analysis(
    ["src/roi_calculator/app.py"],
    pathex=["src"],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
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
    name=name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=icon,
)
