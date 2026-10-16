"""Check a declared single-joint hold record; never auto-release a hardware gate.

Synthetic controls validate this checker, not the rover. Sampled voltage/current
cannot establish transient capture, calibration validity, or safe fault response.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from models.cots_rover import DEFAULT_CONFIG, load_config

FIELDS = (
    "time_s",
    "measured_torque_nm",
    "motor_case_temp_c",
    "driver_temp_c",
    "ambient_temp_c",
    "bus_voltage_v",
    "bus_current_a",
    "aux_output_power_w",
    "torque_sensor_ok",
    "motor_feedback_ok",
    "driver_fault_code",
)
TEMPLATE = Path(__file__).with_name("tranche_02") / "bench_manifest_template.json"


def finish(status, reasons, checks=None, metrics=None):
    return {
        "status": status,
        "reasons": reasons,
        "checks": checks or {},
        "metrics": metrics or {},
        "hardware_validated": False,
        "gates_closed": [],
        "scope": "M5 and E2 numerical record checks only; physical review remains required",
        "excluded": [
            "calibration authenticity",
            "internal winding temperature unless separately instrumented",
            "voltage transients and regeneration E1",
            "fault-response timing C2",
            "structural and landing proof M4/L1",
            "lunar qualification",
        ],
    }


def evaluate_record(manifest_path: Path) -> dict[str, Any]:
    if not manifest_path.exists():
        return finish("SOURCE-GATED", ["No acquisition manifest supplied"])
    try:
        m = json.loads(manifest_path.read_text())
        if not isinstance(m, dict):
            return finish("REJECTED", ["Manifest must be an object"])
        if m.get("dataset_origin") not in ("measured", "synthetic_control") or not m.get("csv_file"):
            return finish("SOURCE-GATED", ["No declared measured record; template is not evidence"])
        path = manifest_path.parent / m["csv_file"]
        if not path.is_file():
            return finish("SOURCE-GATED", ["Raw CSV is missing"])
        expected = m.get("csv_sha256")
        if not expected:
            return finish("SOURCE-GATED", ["Raw CSV integrity hash is missing"])
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            return finish("REJECTED", ["Raw CSV hash mismatch"])
        with path.open(newline="") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames != list(FIELDS):
                return finish("REJECTED", ["CSV columns/units do not match the declared schema"])
            raw = list(reader)
        if not raw:
            return finish("SOURCE-GATED", ["CSV has no measurements"])
        rows = []
        for i, row in enumerate(raw):
            if None in row or any(row[k] is None or not row[k].strip() for k in FIELDS):
                return finish("REJECTED", [f"Missing or extra field at CSV record {i + 1}"])
            values = {k: float(row[k]) for k in FIELDS}
            if not all(math.isfinite(v) for v in values.values()):
                return finish("REJECTED", [f"Nonfinite number at CSV record {i + 1}"])
            if any(values[k] not in (0, 1) for k in ("torque_sensor_ok", "motor_feedback_ok")):
                return finish("REJECTED", [f"Invalid boolean flag at CSV record {i + 1}"])
            if values["driver_fault_code"] < 0 or not values["driver_fault_code"].is_integer():
                return finish("REJECTED", [f"Invalid driver fault code at CSV record {i + 1}"])
            rows.append(values)
        for key in (
            "acquisition_utc",
            "operator",
            "fixture_id",
            "actuator_serial",
            "driver_revision",
            "firmware_revision",
            "calibration_record",
            "protocol_id",
        ):
            if not m.get(key):
                return finish("SOURCE-GATED", [f"Missing provenance field: {key}"])
        if m["protocol_id"] != "COTS-T02-HOLD-01":
            return finish("REJECTED", ["Unknown hold protocol"])
        acquired = datetime.fromisoformat(m["acquisition_utc"].replace("Z", "+00:00"))
        if acquired.tzinfo is None:
            return finish("REJECTED", ["Acquisition time needs an explicit timezone"])
        config_hash = hashlib.sha256(DEFAULT_CONFIG.read_bytes()).hexdigest()
        if m.get("config_sha256") != config_hash:
            return finish("REJECTED", ["Configuration hash mismatch"])
        limits = m.get("temperature_limits_c", {})
        if not isinstance(limits, dict) or not isinstance(m.get("temperature_limit_sources", {}), dict):
            return finish("REJECTED", ["Temperature limits and sources must be objects"])
        for channel in ("motor_case_temp_c", "driver_temp_c"):
            if channel not in limits or not m.get("temperature_limit_sources", {}).get(channel):
                return finish(
                    "SOURCE-GATED", [f"Missing supplier limit for the actual measurement location: {channel}"]
                )
            if not isinstance(limits[channel], (int, float)) or not math.isfinite(limits[channel]):
                return finish("REJECTED", [f"Invalid temperature limit: {channel}"])
        if not isinstance(m.get("target_torque_nm"), (float, int)) or not math.isfinite(m["target_torque_nm"]):
            return finish("SOURCE-GATED", ["A finite hold target is required"])
    except (ValueError, TypeError, KeyError, OSError, AttributeError) as exc:
        return finish("REJECTED", [f"Malformed record or manifest: {exc}"])
    c = load_config()
    cap = c["actuator"]["design_torque_limit_nm"]
    target = abs(m["target_torque_nm"])
    if not math.isclose(target, cap, abs_tol=1e-9, rel_tol=0):
        return finish(
            "REJECTED",
            [
                "This protocol fixes the target magnitude to the 43.2 Nm design cap; lower-load trials use a different protocol"
            ],
        )
    times = [r["time_s"] for r in rows]
    gaps = [b - a for a, b in zip(times, times[1:])]
    checks = {
        "elapsed_time_nonnegative": times[0] >= 0,
        "time_strictly_increasing": bool(gaps) and min(gaps) > 0,
        "hold_duration_at_least_3600s": times[-1] - times[0] >= 3600,
        "sample_gap_at_most_1p5s": bool(gaps) and max(gaps) <= 1.5,
        "torque_within_target_band": all(0.95 * target <= abs(r["measured_torque_nm"]) <= cap + 1e-9 for r in rows),
        "torque_direction_matches_target": all(r["measured_torque_nm"] * m["target_torque_nm"] > 0 for r in rows),
        "continuous_valid_feedback": all(r["torque_sensor_ok"] == r["motor_feedback_ok"] == 1 for r in rows),
        "driver_fault_free": all(r["driver_fault_code"] == 0 for r in rows),
        "bus_voltage_in_operating_range": all(
            c["power"]["operating_cutoff_v"] <= r["bus_voltage_v"] <= c["actuator"]["driver_voltage_range_v"][1]
            for r in rows
        ),
        "motoring_bus_current_budget": all(0 <= r["bus_current_a"] <= c["power"]["design_bus_current_a"] for r in rows),
        "auxiliary_output_budget": all(0 <= r["aux_output_power_w"] <= 100.8 for r in rows),
    }
    rise = {}
    for channel in ("motor_case_temp_c", "driver_temp_c"):
        checks[channel + "_limit"] = all(r[channel] <= limits[channel] for r in rows)
        early = [r[channel] for r in rows if times[-1] - 600 <= r["time_s"] < times[-1] - 540]
        late = [r[channel] for r in rows if times[-1] - 60 < r["time_s"] <= times[-1]]
        rise[channel] = sum(late) / len(late) - sum(early) / len(early) if early and late else None
        tail_rise = rise[channel]
        checks[channel + "_tail_rise"] = tail_rise is not None and tail_rise < 1.0
    metrics = {
        "records": len(rows),
        "duration_s": times[-1] - times[0],
        "maximum_sample_gap_s": max(gaps) if gaps else None,
        "tail_mean_rise_c": rise,
        "peak_bus_current_a": max(r["bus_current_a"] for r in rows),
        "peak_auxiliary_output_w": max(r["aux_output_power_w"] for r in rows),
        "csv_sha256": expected,
        "config_sha256": config_hash,
        "dataset_origin": m["dataset_origin"],
    }
    failed = [k for k, v in checks.items() if not v]
    if failed:
        return finish("REJECTED", failed, checks, metrics)
    status = (
        "SYNTHETIC_CONTROL_ONLY"
        if m["dataset_origin"] == "synthetic_control"
        else "NUMERICAL_CHECKS_PASS_REVIEW_REQUIRED"
    )
    return finish(
        status,
        ["Calibration, measurement-location limits, setup and acquisition provenance require physical review"],
        checks,
        metrics,
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--manifest", type=Path, default=TEMPLATE)
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    result = evaluate_record(args.manifest)
    serialized = json.dumps(result, indent=2, allow_nan=False) + "\n"
    if args.output:
        args.output.write_text(serialized)
    print(serialized)
    raise SystemExit(
        0 if result["status"] in ("NUMERICAL_CHECKS_PASS_REVIEW_REQUIRED", "SYNTHETIC_CONTROL_ONLY") else 2
    )
