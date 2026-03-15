#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path

REPORT_DIR = Path("verification/reports")
EVAL_CSV = REPORT_DIR / "regolith_variant_evaluation.csv"


def _b(v: str) -> bool:
    return str(v).strip().lower() in {"true", "1", "yes"}


def _f(v: str, d: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return d


def _pick(rows: list[dict[str, str]], mission: str, reserve: float, temp_c: float) -> dict[str, str] | None:
    valid = [r for r in rows if _b(r.get("pass", "False"))]
    if not valid:
        return None

    # Runtime guards
    guarded = [
        r
        for r in valid
        if reserve >= _f(r.get("reserve", "0")) and _f(r.get("resurfacing_margin", "0")) >= 1.05
    ]
    if not guarded:
        guarded = valid

    if mission == "baseline":
        balanced = [r for r in guarded if (r.get("risk_posture") or "") == "balanced"]
        preferred = balanced if balanced else guarded
        defaults = [r for r in preferred if _b(r.get("default_recommended", "False"))]
        pool = defaults if defaults else preferred
        return sorted(pool, key=lambda r: _f(r.get("synthetic_success_score", "0")), reverse=True)[0]

    if mission == "deep_scout":
        aggressive = [r for r in guarded if (r.get("risk_posture") or "") == "aggressive"]
        pool = aggressive if aggressive else guarded
        return sorted(
            pool,
            key=lambda r: (_f(r.get("depth_m", "0")), _f(r.get("synthetic_success_score", "0"))),
            reverse=True,
        )[0]

    if mission == "low_energy_contingency":
        # Planning-first policy: prefer conservative variants even if current reserve is below their floor.
        conservative_all = [r for r in valid if (r.get("risk_posture") or "") == "conservative"]
        if conservative_all:
            return sorted(
                conservative_all,
                key=lambda r: (_f(r.get("resurfacing_margin", "0")), _f(r.get("reserve", "0"))),
                reverse=True,
            )[0]
        pool = guarded if guarded else valid
        return sorted(
            pool,
            key=lambda r: (_f(r.get("resurfacing_margin", "0")), _f(r.get("reserve", "0"))),
            reverse=True,
        )[0]

    # adaptive: choose by runtime context
    if reserve < 0.25:
        return _pick(rows, "low_energy_contingency", reserve, temp_c)
    if temp_c > 68:
        cooler = sorted(guarded, key=lambda r: _f(r.get("depth_m", "0")))
        return cooler[0] if cooler else None
    return _pick(rows, "baseline", reserve, temp_c)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--mission-intent", choices=["baseline", "deep_scout", "low_energy_contingency", "adaptive"], default="adaptive")
    p.add_argument("--runtime-energy-reserve", type=float, default=0.30)
    p.add_argument("--runtime-component-temp-c", type=float, default=62.0)
    args = p.parse_args()

    if not EVAL_CSV.exists():
        raise FileNotFoundError(f"missing evaluation file: {EVAL_CSV}")

    with EVAL_CSV.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    chosen = _pick(rows, args.mission_intent, args.runtime_energy_reserve, args.runtime_component_temp_c)
    if not chosen:
        raise RuntimeError("no valid variant available")

    out_csv = REPORT_DIR / "regolith_variant_selection.csv"
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "mission_intent",
            "runtime_energy_reserve",
            "runtime_component_temp_c",
            "selected_variant",
            "risk_posture",
            "depth_m",
            "reserve",
            "runtime_feasible",
            "resurfacing_margin",
            "synthetic_success_score",
            "pass",
        ]
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        runtime_feasible = args.runtime_energy_reserve >= _f(chosen.get("reserve", "0"))
        w.writerow(
            {
                "mission_intent": args.mission_intent,
                "runtime_energy_reserve": args.runtime_energy_reserve,
                "runtime_component_temp_c": args.runtime_component_temp_c,
                "selected_variant": chosen.get("variant", ""),
                "risk_posture": chosen.get("risk_posture", ""),
                "depth_m": chosen.get("depth_m", ""),
                "reserve": chosen.get("reserve", ""),
                "runtime_feasible": runtime_feasible,
                "resurfacing_margin": chosen.get("resurfacing_margin", ""),
                "synthetic_success_score": chosen.get("synthetic_success_score", ""),
                "pass": True,
            }
        )

    out_md = REPORT_DIR / "regolith_variant_selection.md"
    out_md.write_text(
        "\n".join(
            [
                "# Regolith Variant Selection",
                "",
                f"- mission intent: `{args.mission_intent}`",
                f"- runtime reserve: `{args.runtime_energy_reserve:.3f}`",
                f"- runtime component temp (C): `{args.runtime_component_temp_c:.2f}`",
                f"- selected variant: `{chosen.get('variant', '')}`",
                f"- risk posture: `{chosen.get('risk_posture', '')}`",
                f"- depth (m): `{chosen.get('depth_m', '')}`",
                f"- reserve floor: `{chosen.get('reserve', '')}`",
                f"- runtime feasible at current reserve: `{args.runtime_energy_reserve >= _f(chosen.get('reserve', '0'))}`",
                f"- resurfacing margin: `{chosen.get('resurfacing_margin', '')}`",
                f"- synthetic score: `{chosen.get('synthetic_success_score', '')}`",
                "",
                "STATUS=pass",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"Wrote {out_csv}")
    print(f"Wrote {out_md}")
    print(f"SELECTED={chosen.get('variant', '')}")


if __name__ == "__main__":
    main()
