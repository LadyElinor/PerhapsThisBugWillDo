#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "cad" / "weevil_leg_params.yaml"
OVERLAY = ROOT / "cad" / "fresh_crater_leg_params_overlay_2026-04-18.yaml"
OUT = ROOT / "cad" / "generated" / "weevil_leg_params_fresh_crater_2026-04-18.yaml"


def merge_dict(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    out = dict(base)
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = merge_dict(out[key], value)
        else:
            out[key] = value
    return out


def main() -> None:
    if not BASE.exists():
        raise FileNotFoundError(f"missing base file: {BASE}")
    if not OVERLAY.exists():
        raise FileNotFoundError(f"missing overlay file: {OVERLAY}")

    base = yaml.safe_load(BASE.read_text(encoding="utf-8"))
    overlay = yaml.safe_load(OVERLAY.read_text(encoding="utf-8"))
    merged = merge_dict(base, overlay.get("fresh_crater_overlay", {}))

    meta = merged.setdefault("meta", {})
    meta["materialized_profile"] = "fresh_crater"
    meta["source_base"] = str(BASE.relative_to(ROOT)).replace("\\", "/")
    meta["source_overlay"] = str(OVERLAY.relative_to(ROOT)).replace("\\", "/")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(yaml.safe_dump(merged, sort_keys=False), encoding="utf-8")

    print(f"Wrote {OUT}")
    print("STATUS=pass")


if __name__ == "__main__":
    main()
