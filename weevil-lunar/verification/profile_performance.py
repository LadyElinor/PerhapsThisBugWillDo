#!/usr/bin/env python3
"""Simple cProfile entrypoint for verification workload."""

from __future__ import annotations

import cProfile
import pstats
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    from verification.sensitivity_sweep import main as sweep_main  # noqa: WPS433

    out_dir = Path("results/perf")
    out_dir.mkdir(parents=True, exist_ok=True)
    prof_path = out_dir / "sensitivity_sweep.prof"
    txt_path = out_dir / "sensitivity_sweep_top20.txt"

    profiler = cProfile.Profile()
    profiler.enable()
    sweep_main()
    profiler.disable()
    profiler.dump_stats(str(prof_path))

    with txt_path.open("w", encoding="utf-8") as f:
        stats = pstats.Stats(profiler, stream=f).sort_stats("cumtime")
        stats.print_stats(20)

    print(f"Wrote {prof_path}")
    print(f"Wrote {txt_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
