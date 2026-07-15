from __future__ import annotations

import json
from pathlib import Path
import re
import shutil
import subprocess
from typing import Any


ODE_ROOT = Path(r"C:\Users\arren\.openclaw\workspace\0sourceforge\ode-0.11.1\ode-0.11.1")
BUILD_DIR = ODE_ROOT / "build"
PREMAKE_EXE = BUILD_DIR / "premake4.exe"
PREMAKE_SCRIPT = BUILD_DIR / "premake4.lua"
LEGACY_SOLUTION = BUILD_DIR / "vs2008" / "ode.sln"
LEGACY_ODE_PROJECT = BUILD_DIR / "vs2008" / "ode.vcproj"
LEGACY_TESTS_PROJECT = BUILD_DIR / "vs2008" / "tests.vcproj"
PROBE_SCRIPT = BUILD_DIR / "probe_ode_toolchain.cmd"
VSVCVARS = Path(r"C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat")


def _run_cmd(script: str, cwd: Path) -> tuple[bool, str]:
    proc = subprocess.run(
        ["cmd.exe", "/d", "/c", script],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        shell=False,
    )
    output = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode == 0, output.strip()


def _premake_actions_from_output(output: str) -> list[str]:
    actions: list[str] = []
    in_actions = False
    for line in output.splitlines():
        stripped = line.strip()
        if stripped == "ACTIONS":
            in_actions = True
            continue
        if in_actions:
            if not stripped:
                continue
            if stripped.startswith("For additional information"):
                break
            action = stripped.split()[0]
            actions.append(action)
    return actions


def preflight() -> dict[str, Any]:
    cl_on_path = shutil.which("cl")
    msbuild_on_path = shutil.which("msbuild")
    cmd_exe_on_path = shutil.which("cmd.exe")

    vcvars_exists = VSVCVARS.exists()
    probe_ok = False
    probe_output = ""
    if PROBE_SCRIPT.exists():
        probe_ok, probe_output = _run_cmd(PROBE_SCRIPT.name, BUILD_DIR)

    cl_via_vcvars = "C/C++ Optimizing Compiler Version" in probe_output or "usage: cl [ option... ]" in probe_output
    premake_actions = _premake_actions_from_output(probe_output)

    msbuild_match = re.findall(r"^[A-Z]:\\.*MSBuild\.exe$", probe_output, flags=re.MULTILINE | re.IGNORECASE)
    if msbuild_match:
        msbuild_on_path = msbuild_match[0]
    premake_supports_vs2008 = "vs2008" in premake_actions
    premake_supports_modern_vs = any(action in {"vs2010", "vs2012", "vs2013", "vs2015", "vs2017", "vs2019", "vs2022"} for action in premake_actions)

    blockers: list[str] = []
    recommendation: list[str] = []

    if not ODE_ROOT.exists():
        blockers.append("ODE source root is missing")
    if not PREMAKE_EXE.exists():
        blockers.append("premake4.exe is missing from ODE build directory")
    if not vcvars_exists:
        blockers.append("vcvars64.bat not found for installed MSVC Build Tools")
    if vcvars_exists and not cl_via_vcvars:
        blockers.append("MSVC compiler was not usable even after vcvars64 initialization")
    if not premake_supports_vs2008:
        blockers.append("ODE premake script did not expose the expected vs2008 action")
    if not premake_supports_modern_vs:
        blockers.append("legacy premake does not expose a modern Visual Studio project generator")
    if not msbuild_on_path:
        blockers.append("msbuild is not visible on PATH")

    if not premake_supports_modern_vs:
        recommendation.append("Treat generated Visual Studio 2008 files as legacy artifacts, not a guaranteed headless build path")
    if vcvars_exists and not cl_via_vcvars:
        recommendation.append("Open an initialized Developer Command Prompt or fix Build Tools installation before ODE build attempts")
    if premake_supports_vs2008 and not LEGACY_SOLUTION.exists():
        recommendation.append("Generate legacy project files with premake4 before attempting any ODE build")

    headless_runtime_ready = bool(
        ODE_ROOT.exists()
        and PREMAKE_EXE.exists()
        and vcvars_exists
        and cl_via_vcvars
        and premake_supports_modern_vs
    )

    return {
        "ode_root": str(ODE_ROOT),
        "ode_root_exists": ODE_ROOT.exists(),
        "build": {
            "build_dir_exists": BUILD_DIR.exists(),
            "premake_exe": str(PREMAKE_EXE),
            "premake_exe_exists": PREMAKE_EXE.exists(),
            "premake_script_exists": PREMAKE_SCRIPT.exists(),
            "premake_actions": premake_actions,
            "premake_supports_vs2008": premake_supports_vs2008,
            "premake_supports_modern_visual_studio": premake_supports_modern_vs,
            "legacy_solution_exists": LEGACY_SOLUTION.exists(),
            "legacy_ode_project_exists": LEGACY_ODE_PROJECT.exists(),
            "legacy_tests_project_exists": LEGACY_TESTS_PROJECT.exists(),
        },
        "toolchain": {
            "cmd_exe_on_path": cmd_exe_on_path,
            "msbuild_on_path": msbuild_on_path,
            "cl_on_path": cl_on_path,
            "vcvars64_bat": str(VSVCVARS),
            "vcvars64_exists": vcvars_exists,
            "cl_usable_via_vcvars": cl_via_vcvars,
            "cl_usable_via_vcvars_excerpt": probe_output.splitlines()[-1] if probe_output else "",
            "vcvars_probe_had_output": bool(probe_output),
            "probe_script_exists": PROBE_SCRIPT.exists(),
            "probe_script_succeeded": probe_ok,
        },
        "runtime_path": {
            "headless_runtime_ready": headless_runtime_ready,
            "status": "blocked" if not headless_runtime_ready else "ready",
            "reason": "Legacy ODE premake only exposes vs2008 generation, so current headless MSBuild flow remains blocked" if not headless_runtime_ready else "Modern headless generation path available",
        },
        "blockers": blockers,
        "recommendation": recommendation,
    }


if __name__ == "__main__":
    print(json.dumps(preflight(), indent=2))
