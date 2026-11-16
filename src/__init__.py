"""Make the conda environment's DLLs and GDAL/PROJ data visible, even when the
notebook kernel was started without activating the environment (Windows)."""
import os
import sys
from pathlib import Path

if os.name == "nt":
    _env = Path(sys.executable).parent
    _dirs = [
        _env,
        _env / "Library" / "bin",
        _env / "Library" / "mingw-w64" / "bin",
        _env / "Library" / "usr" / "bin",
        _env / "Scripts",
    ]
    _dirs = [d for d in _dirs if d.exists()]
    os.environ["PATH"] = os.pathsep.join(str(d) for d in _dirs) + os.pathsep + os.environ.get("PATH", "")
    for _d in _dirs:
        os.add_dll_directory(str(_d))
    os.environ.setdefault("GDAL_DATA", str(_env / "Library" / "share" / "gdal"))
    os.environ.setdefault("PROJ_DATA", str(_env / "Library" / "share" / "proj"))