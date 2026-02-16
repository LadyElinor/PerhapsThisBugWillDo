#!/usr/bin/env python3
"""
weevil_lunar_tests.py

Weevil-Lunar v0.3 tests with directional anchoring and slope rescue profiling.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from regolith_contact_model import RegolithType, RegolithProperties, FootGeometry, RegolithContactModel


@dataclass
class TestResult:
    name: str
    passed: bool
    value: float
    threshold: float
    note: str


def test_twist_settle_gain(model: RegolithContactModel, body_load: float, preload: float = 20.0, min_gain: float = 1.15) -> TestResult:
    base = model.compute_contact_forces_with_preload(body_load, preload_normal=preload, twist_settle_gain=1.0)
    twist = model.compute_contact_forces_with_preload(body_load, preload_normal=preload, twist_settle_gain=min_gain)
    ratio = twist.max_shear_force / max(base.max_shear_force, 1e-9)
    return TestResult(
        name="twist_settle_gain",
        passed=ratio >= min_gain,
        value=ratio,
        threshold=min_gain,
        note=f"shear ratio={ratio:.3f}",
    )


def test_sinkage_limit(model: RegolithContactModel, body_load: float, preload: float = 20.0, max_sink_cm: float = 8.0) -> TestResult:
    c = model.compute_contact_forces_with_preload(body_load, preload_normal=preload, twist_settle_gain=1.0)
    sink_cm = c.penetration_depth * 100.0
    return TestResult(
        name="sinkage_limit",
        passed=sink_cm <= max_sink_cm,
        value=sink_cm,
        threshold=max_sink_cm,
        note=f"sinkage={sink_cm:.2f} cm",
    )


def test_directional_slope_margin(
    model: RegolithContactModel,
    body_load: float,
    preload: float = 20.0,
    slope_deg: float = 45.0,
    downslope_margin_min: float = 1.05,
    lateral_margin_min: float = 1.20,
    cleat_gain_forward: float = 1.0,
    cleat_gain_lateral: float = 1.0,
    require_anchor_above_deg: float = 25.0,
    twist_settle_gain: float = 1.0,
) -> TestResult:
    # Temporarily patch foot gains for this test call
    old_fwd = model.foot.cleat_gain_forward
    old_lat = model.foot.cleat_gain_lateral
    old_thr = model.foot.cleat_engage_threshold_preload
    model.foot = FootGeometry(
        area=model.foot.area,
        radius=model.foot.radius,
        cleat_gain_forward=cleat_gain_forward,
        cleat_gain_lateral=cleat_gain_lateral,
        cleat_engage_threshold_preload=old_thr,
    )

    c = model.compute_contact_forces_with_preload(
        body_load,
        preload_normal=preload,
        twist_settle_gain=twist_settle_gain,
        use_directional_cleats=True,
    )

    # restore
    model.foot = FootGeometry(
        area=model.foot.area,
        radius=model.foot.radius,
        cleat_gain_forward=old_fwd,
        cleat_gain_lateral=old_lat,
        cleat_engage_threshold_preload=old_thr,
    )

    down_margin = (c.friction_cone_forward_angle or 0.0) / slope_deg
    lat_margin = (c.friction_cone_lateral_angle or 0.0) / slope_deg
    anchor_ok = (slope_deg <= require_anchor_above_deg) or c.anchored

    passed = down_margin >= downslope_margin_min and lat_margin >= lateral_margin_min and anchor_ok

    return TestResult(
        name="directional_slope_margin_45deg",
        passed=passed,
        value=min(down_margin, lat_margin),
        threshold=min(downslope_margin_min, lateral_margin_min),
        note=(
            f"cone_fwd={c.friction_cone_forward_angle:.2f}°, cone_lat={c.friction_cone_lateral_angle:.2f}°, "
            f"down_margin={down_margin:.3f}, lat_margin={lat_margin:.3f}, anchored={c.anchored}, "
            f"preload={preload:.1f}N, gf={cleat_gain_forward:.2f}, gl={cleat_gain_lateral:.2f}"
        ),
    )


def slope_rescue_sweep(
    regolith: RegolithProperties,
    body_load: float,
    gravity: float = 1.62,
    slope_deg: float = 45.0,
) -> dict:
    """Find minimal geometry+anchoring combo satisfying directional slope gates."""
    radii = [0.05, 0.06, 0.07, 0.08]
    preload_grid = [20, 35, 50, 70, 90, 120]
    gf_grid = [1.10, 1.20, 1.30, 1.40, 1.50, 1.60, 1.80, 2.00]
    gl_grid = [1.00, 1.10, 1.20, 1.30, 1.40, 1.60, 1.80, 2.00]

    best = None
    top_rows = []

    for r in radii:
        foot = FootGeometry.circular(
            radius=r,
            cleat_gain_forward=1.0,
            cleat_gain_lateral=1.0,
            cleat_engage_threshold_preload=20.0,
        )
        model = RegolithContactModel(regolith, foot, gravity=gravity)

        for preload in preload_grid:
            for gf in gf_grid:
                for gl in gl_grid:
                    tr = test_directional_slope_margin(
                        model,
                        body_load,
                        preload=float(preload),
                        slope_deg=float(slope_deg),
                        downslope_margin_min=1.05,
                        lateral_margin_min=1.20,
                        cleat_gain_forward=float(gf),
                        cleat_gain_lateral=float(gl),
                        require_anchor_above_deg=25.0,
                        twist_settle_gain=1.0,
                    )
                    if tr.passed:
                        # effort score: prefer smaller preload, lower gains, smaller feet
                        score = preload + 100.0 * (gf - 1.0) + 120.0 * (gl - 1.0) + 200.0 * max(0.0, r - 0.05)
                        # get sinkage for reporting
                        c = model.compute_contact_forces_with_preload(
                            body_load,
                            preload_normal=preload,
                            twist_settle_gain=1.0,
                            use_directional_cleats=True,
                        )
                        rec = {
                            "score": float(score),
                            "radius_m": float(r),
                            "preload_N": float(preload),
                            "gain_forward": float(gf),
                            "gain_lateral": float(gl),
                            "sinkage_cm": float(c.penetration_depth * 100.0),
                            "note": tr.note,
                        }
                        top_rows.append(rec)
                        if (best is None) or (score < best["score"]):
                            best = rec

    top_rows = sorted(top_rows, key=lambda x: x["score"])[:10]
    return {
        "best": best,
        "top": top_rows,
    }


def run_suite(
    terrain: RegolithType,
    body_mass_kg: float = 30.0,
    gravity: float = 1.62,
    n_legs: int = 6,
) -> tuple[List[TestResult], dict]:
    reg = RegolithProperties.from_type(terrain)
    foot = FootGeometry.circular(0.05, cleat_gain_forward=1.0, cleat_gain_lateral=1.0, cleat_engage_threshold_preload=20.0)
    model = RegolithContactModel(reg, foot, gravity=gravity)
    body_load_per_leg = body_mass_kg * gravity / n_legs

    tests = [
        test_twist_settle_gain(model, body_load_per_leg),
        test_sinkage_limit(model, body_load_per_leg),
        test_directional_slope_margin(model, body_load_per_leg),
    ]

    rescue = slope_rescue_sweep(reg, body_load_per_leg, gravity=gravity, slope_deg=45.0)
    return tests, rescue


def summarize(results_by_terrain: Dict[str, List[TestResult]], rescue_by_terrain: Dict[str, dict]) -> str:
    lines = []
    lines.append("# Weevil-Lunar v0.3 Test Summary (Directional Slope Rescue)")
    lines.append("")

    for terrain, results in results_by_terrain.items():
        lines.append(f"## {terrain}")
        for r in results:
            status = "PASS" if r.passed else "FAIL"
            lines.append(f"- [{status}] {r.name}: value={r.value:.3f}, threshold={r.threshold:.3f} ({r.note})")

        rr = rescue_by_terrain.get(terrain, {})
        best = rr.get("best") if rr else None
        if best is not None:
            lines.append(
                "- [RESCUE] feasible with "
                f"radius={best['radius_m']:.2f} m, preload={best['preload_N']:.1f} N, "
                f"gains(fwd/lat)=({best['gain_forward']:.2f}/{best['gain_lateral']:.2f}), "
                f"sinkage={best['sinkage_cm']:.2f} cm"
            )
            lines.append(f"  note: {best['note']}")
        else:
            lines.append("- [RESCUE] no feasible combo in tested geometry/anchoring grid")
        lines.append("")

    return "\n".join(lines)


def write_mare_rescue_profile(rescue_by_terrain: Dict[str, dict]) -> None:
    rr = rescue_by_terrain.get("mare", {})
    best = rr.get("best") if rr else None
    top = rr.get("top", []) if rr else []

    lines = []
    lines.append("# Mare Rescue Profile (Weevil-Lunar v0.3)")
    lines.append("")
    if best is None:
        lines.append("No feasible directional slope rescue solution found in current sweep grid.")
    else:
        lines.append("## Best feasible configuration")
        lines.append(
            f"- foot radius: **{best['radius_m']:.2f} m**\n"
            f"- preload: **{best['preload_N']:.1f} N**\n"
            f"- directional gains: **forward {best['gain_forward']:.2f} / lateral {best['gain_lateral']:.2f}**\n"
            f"- sinkage: **{best['sinkage_cm']:.2f} cm**"
        )
        lines.append("")
        lines.append("## Top feasible candidates")
        lines.append("| score | radius_m | preload_N | gain_fwd | gain_lat | sinkage_cm |")
        lines.append("|---:|---:|---:|---:|---:|---:|")
        for r in top:
            lines.append(
                f"| {r['score']:.1f} | {r['radius_m']:.2f} | {r['preload_N']:.1f} | {r['gain_forward']:.2f} | {r['gain_lateral']:.2f} | {r['sinkage_cm']:.2f} |"
            )

    with open("mare_rescue_profile.md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main() -> None:
    terrains = [RegolithType.MARE, RegolithType.HIGHLAND, RegolithType.MIXED, RegolithType.COMPACTED]
    out = {}
    rescue = {}
    for t in terrains:
        tests, rr = run_suite(t)
        out[t.value] = tests
        rescue[t.value] = rr

    text = summarize(out, rescue)
    with open("weevil_lunar_test_results.md", "w", encoding="utf-8") as f:
        f.write(text + "\n")

    write_mare_rescue_profile(rescue)

    print(text)
    print("\nWrote weevil_lunar_test_results.md")
    print("Wrote mare_rescue_profile.md")


if __name__ == "__main__":
    main()
