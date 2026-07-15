from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import shutil
from typing import Any


MUJOCO_BUNDLE_ROOT = Path(r"C:\Users\arren\.openclaw\workspace\0sourceforge\mujoco-3.10.0-windows-x86_64")
BIN_DIR = MUJOCO_BUNDLE_ROOT / "bin"
SAMPLE_DIR = MUJOCO_BUNDLE_ROOT / "sample"
COMPILE_EXE = BIN_DIR / "compile.exe"
TESTSPEED_EXE = BIN_DIR / "testspeed.exe"
MUJOCO_DLL = BIN_DIR / "mujoco.dll"


def _find_visual_studio_cl() -> list[str]:
    roots = [
        Path(r"C:\Program Files\Microsoft Visual Studio"),
        Path(r"C:\Program Files (x86)\Microsoft Visual Studio"),
    ]
    out: list[str] = []
    for root in roots:
        if root.exists():
            out.extend(str(p) for p in root.rglob("cl.exe"))
    return out


def preflight() -> dict[str, Any]:
    python_mujoco = importlib.util.find_spec("mujoco") is not None
    cl_on_path = shutil.which("cl")
    gxx_on_path = shutil.which("g++")
    cl_candidates = _find_visual_studio_cl()

    runtime_ready = COMPILE_EXE.exists() and TESTSPEED_EXE.exists() and MUJOCO_DLL.exists()
    custom_trace_ready = python_mujoco or bool(cl_on_path) or bool(gxx_on_path) or bool(cl_candidates)

    blockers: list[str] = []
    if not runtime_ready:
        blockers.append("MuJoCo runtime executables are incomplete or missing")
    if not custom_trace_ready:
        blockers.append("No visible Python MuJoCo binding or C/C++ compiler for custom trace harness compilation")

    recommendation = []
    if not python_mujoco:
        recommendation.append("Install Python package `mujoco` for fastest custom trace harness path")
    if not (cl_on_path or gxx_on_path or cl_candidates):
        recommendation.append("Install a C/C++ toolchain (MSVC Build Tools preferred on Windows)")

    return {
        "mujoco_bundle_root": str(MUJOCO_BUNDLE_ROOT),
        "bundle_exists": MUJOCO_BUNDLE_ROOT.exists(),
        "runtime": {
            "bin_dir_exists": BIN_DIR.exists(),
            "sample_dir_exists": SAMPLE_DIR.exists(),
            "compile_exe": str(COMPILE_EXE),
            "compile_exe_exists": COMPILE_EXE.exists(),
            "testspeed_exe": str(TESTSPEED_EXE),
            "testspeed_exe_exists": TESTSPEED_EXE.exists(),
            "mujoco_dll": str(MUJOCO_DLL),
            "mujoco_dll_exists": MUJOCO_DLL.exists(),
            "runtime_ready": runtime_ready,
        },
        "custom_trace_harness": {
            "python_mujoco_installed": python_mujoco,
            "cl_on_path": cl_on_path,
            "gxx_on_path": gxx_on_path,
            "visual_studio_cl_candidates": cl_candidates[:20],
            "custom_trace_ready": custom_trace_ready,
        },
        "blockers": blockers,
        "recommendation": recommendation,
    }


if __name__ == "__main__":
    print(json.dumps(preflight(), indent=2))
