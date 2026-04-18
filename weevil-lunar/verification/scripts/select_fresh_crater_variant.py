#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORT_DIR = ROOT / "verification" / "reports"
EVAL_CSV = REPORT_DIR / "fresh_crater_variant_evaluation.csv"
CAD_CFG = ROOT / "cad" / "assets" / "fresh_crater_candidates.yaml"


def _b(v: str) -> bool:
    return str(v).strip().lower() in {"true", "1", "yes"}


def _f(v: str, d: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return d


def _load_actuator_map() -> dict[str, str]:
    mapping: dict[str, str] = {}
    if not CAD_CFG.exists():
        return mapping
    import yaml

    data = yaml.safe_load(CAD_CFG.read_text(encoding="utf-8"))
    for asset in data.get("assets", []):
        mapping[str(asset.get("asset_id", ""))] = str(asset.get("intended_role", ""))
    return mapping


def _pick(rows: list[dict[str, str]], mission: str, reserve: float, telemetry: float) -> dict[str, str] | None:
    valid = [r for r in rows if _b(r.get("pass", "False"))]
    if not valid:
        return None

    guarded = [
        r for r in valid
        if reserve >= _f(r.get("reserve", "0")) and telemetry <= _f(r.get("telemetry_buffer_effective_s", "9999")) + 120.0
    ]
    if not guarded:
        guarded = valid

    if mission == "conservative_rim":
        pool = [r for r in guarded if (r.get("risk_posture") or "") == "conservative"] or guarded
        return sorted(pool, key=lambda r: _f(r.get("synthetic_success_score", "0")), reverse=True)[0]

    if mission == "guarded_descent":
        pool = [r for r in guarded if r.get("variant") == "partial_descent_guarded"] or guarded
        feasible = [r for r in pool if reserve >= 0.30 and telemetry >= 210.0]
        pick_pool = feasible if feasible else pool
        return sorted(pick_pool, key=lambda r: _f(r.get("synthetic_success_score", "0")), reverse=True)[0]

    balanced = [r for r in guarded if (r.get("risk_posture") or "") == "balanced"]
    preferred = balanced if balanced else guarded
    defaults = [r for r in preferred if _b(r.get("default_recommended", "False"))]
    pool = defaults if defaults else preferred
    return sorted(pool, key=lambda r: _f(r.get("synthetic_success_score", "0")), reverse=True)[0]


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--mission-intent", choices=["baseline", "conservative_rim", "guarded_descent"], default="baseline")
    p.add_argument("--runtime-energy-reserve", type=float, default=0.30)
    p.add_argument("--runtime-telemetry-buffer-s", type=float, default=180.0)
    args = p.parse_args()

    if not EVAL_CSV.exists():
        raise FileNotFoundError(f"missing evaluation file: {EVAL_CSV}")

    with EVAL_CSV.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    chosen = _pick(rows, args.mission_intent, args.runtime_energy_reserve, args.runtime_telemetry_buffer_s)
    if not chosen:
        raise RuntimeError("no valid fresh-crater variant available")

    actuator_map = _load_actuator_map()
    recommended_actuator = chosen.get("recommended_actuator", "unknown")
    geometry_profile = chosen.get("recommended_geometry_profile", "unknown")

    out_csv = REPORT_DIR / "fresh_crater_variant_selection.csv"
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "mission_intent",
            "runtime_energy_reserve",
            "runtime_telemetry_buffer_s",
            "selected_variant",
            "recommended_actuator",
            "recommended_actuator_role",
            "recommended_geometry_profile",
            "distance",
            "pass",
        ]
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerow(
            {
                "mission_intent": args.mission_intent,
                "runtime_energy_reserve": args.runtime_energy_reserve,
                "runtime_telemetry_buffer_s": args.runtime_telemetry_buffer_s,
                "selected_variant": chosen.get("variant", ""),
                "recommended_actuator": recommended_actuator,
                "recommended_actuator_role": actuator_map.get(recommended_actuator, "unknown"),
                "recommended_geometry_profile": geometry_profile,
                "distance": chosen.get("synthetic_success_score", ""),
                "pass": True,
            }
        )

    out_md = REPORT_DIR / "fresh_crater_variant_selection.md"
    out_md.write_text(
        "\n".join(
            [
                "# Fresh Crater Variant Selection",
                "",
                f"- mission intent: `{args.mission_intent}`",
                f"- runtime reserve: `{args.runtime_energy_reserve:.3f}`",
                f"- runtime telemetry buffer (s): `{args.runtime_telemetry_buffer_s:.1f}`",
                f"- selected variant: `{chosen.get('variant', '')}`",
                f"- recommended actuator: `{recommended_actuator}`",
                f"- recommended geometry profile: `{geometry_profile}`",
                f"- score: `{chosen.get('synthetic_success_score', '')}`",
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
