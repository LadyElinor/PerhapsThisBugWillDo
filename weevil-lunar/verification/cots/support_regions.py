"""Robust planar support regions and a fixed-mechanism necessary bound.

Regions are outer bounds: omit joint torque and body-dependent IK. A nonempty
region never admits motion. One body translation must serve every unknown loss.
"""
from __future__ import annotations

import math

import numpy as np
from scipy.optimize import linprog
from scipy.spatial import ConvexHull, QhullError

import support_loss_analysis as study
from explain_support_loss import capped_polygon

TOL = 1e-8


def mechanism_certificate(c, slope_deg=5.):
    """A relaxed 1-D normal-force bound, valid for ANY eligible foot placement.

Fixed body height/orientation, original hip locations and yaw ranges, coplanar
ankles, fixed body-relative COM, and the inherited shaft allowance are premises.
For same-side swing/loss, exactly one foot remains on that side. Opposite feet
cannot cross their hip-side boundary under the accepted IK yaw convention.
"""
    expected = {
        "hips_xy_m": [[.24,.26],[0,.26],[-.24,.26],[-.24,-.26],[0,-.26],[.24,-.26]],
        "leg_azimuth_deg": [60,90,120,-120,-90,-60],
        "joint_limits_deg": [[-35,35],[-30,80],[25,140]],
        "hip_height_m": .3, "foot_pivot_height_m": .055, "com_m": [0.,0.,.31],
    }
    if any(c.get(k) != v for k, v in expected.items()) or c["structure"]["shaft_load_eccentricity_m"] != .4:
        raise ValueError("Mechanism certificate premises changed")
    if type(slope_deg) not in (int, float) or not math.isfinite(slope_deg) or not 0 <= slope_deg <= 5:
        raise ValueError("Invalid certificate slope")
    # With r=norm(target_xy-hip_xy)>=0 and q0 in [-35,35], sin(azimuth+q0)
    # is strictly positive on the left and strictly negative on the right.
    for i, az in enumerate(c["leg_azimuth_deg"]):
        lo, hi = az - 35, az + 35
        if not ((0 < lo <= hi < 180) if i < 3 else (-180 < lo <= hi < 0)):
            raise ValueError("Hip-side yaw premise fails")
    h = .26
    dz = c["hip_height_m"] - c["foot_pivot_height_m"]
    allowance = .04  # inherited, unchanged from support-loss-01 shaft audit
    reach = math.sqrt((c["structure"]["shaft_load_eccentricity_m"] - allowance)**2 - dz**2)
    theta = math.radians(slope_deg)
    total = c["gross_mass_kg"] * c["screening"]["load_factor"] * c["earth_gravity_m_s2"] * math.cos(theta)
    y = c["com_uncertainty_xy_m"][1] + (c["com_m"][2] - c["foot_pivot_height_m"])*math.tan(theta)
    if not np.isfinite([total, y, reach]).all() or total <= 0 or y < 0:
        raise ValueError("Invalid force-bound parameters")
    cap = c["screening"]["normal_force_limit_n"]
    ymax = h + reach
    lower = total * (y + h) / (ymax + h)
    # Independent numerical relaxation: all three opposite feet are generously
    # placed AT the hip boundary, sole support at its maximum possible y.
    a = np.array([[1., 1., 1., 1.], [ymax, -h, -h, -h]])
    b = np.array([total, total*y])
    r = linprog([1.,0.,0.,0.], A_eq=a, b_eq=b,
                bounds=[(0.,None)]+[(0.,cap)]*3, method="highs")
    if not r.success:
        raise RuntimeError(f"Relaxed normal-force bound indeterminate: {r.status}")
    if (np.linalg.norm(a @ r.x - b) > 1e-6 or np.min(r.x) < -TOL
            or np.max(r.x[1:]) > cap + TOL or abs(r.x[0] - lower) > 1e-6):
        raise ValueError("Analytical/LP normal bound disagreement")
    witnesses = []
    for swing in range(6):
        same = list(range(3)) if swing < 3 else list(range(3,6))
        lost = next(i for i in same if i != swing)
        sole = next(i for i in same if i not in (swing, lost))
        witnesses.append({"swing_leg_1based": swing+1, "lost_leg_1based": lost+1,
                          "sole_side_leg_1based": sole+1, "heading_deg": 90 if swing < 3 else 270,
                          "com_sign_y": 1 if swing < 3 else -1,
                          "required_normal_lower_bound_n": lower})
    return {"closed": lower > cap + 1e-6, "normal_lower_bound_n": lower,
            "normal_cap_n": cap, "shortfall_n": lower-cap, "total_normal_n": total,
            "projected_outward_com_m": y, "hip_side_m": h, "maximum_horizontal_hip_reach_m": reach,
            "sole_side_maximum_y_m": ymax, "shaft_allowance_m": allowance,
            "relaxed_lp_forces_n": r.x.tolist(), "relaxed_lp_residual": float(np.linalg.norm(a @ r.x-b)),
            "witnesses": witnesses, "hardware_motion_allowed": False,
            "scope": "Fixed original body height/orientation/COM, hips, accepted IK yaw ranges, planar ankle contacts and 400 mm shaft envelope including 40 mm allowance. Not arbitrary redesign or dynamic recovery."}


def region_constraints(c, feet, active):
    """A b <= rhs for COMMON body x/y translation b and all additional losses.

feet are reference-world positions. Actual body-frame feet would be feet-b;
COM in that frame remains unchanged. Recompute IK/Jacobians for any future
candidate body pose. Here torque, reach, collision and COP cannot be admitted.
"""
    feet = np.asarray(feet, dtype=float)
    if (feet.shape != (6,3) or not np.isfinite(feet).all() or len(active) != 5
            or len(set(active)) != 5 or any(type(i) is not int or i not in range(6) for i in active)
            or np.ptp(feet[list(active),2]) > 1e-12):
        raise ValueError("Five coplanar, identified supports required")
    rows, bounds, tags = [], [], []
    for lost in active:
        supports = tuple(i for i in active if i != lost)
        xy = feet[list(supports), :2]
        try:
            ordinary = ConvexHull(xy).equations
        except QhullError:
            # Positive required inset cannot fit in a line or point.
            rows.append([0.,0.]); bounds.append(-c["screening"]["support_margin_required_m"])
            tags.append({"lost_leg_1based": lost+1, "constraint": "degenerate_support_margin"})
            continue
        cache = {}
        for sx, sy, gid, _, _, com, gravity in study.load_cases(c):
            total = -c["gross_mass_kg"]*c["screening"]["load_factor"]*gravity[2]
            if total not in cache:
                points = capped_polygon(xy, total, c["screening"]["normal_force_limit_n"])
                if len(points) < 3:
                    raise ValueError("Degenerate or insufficient normal-cap region")
                cache[total] = ConvexHull(points).equations
            offset = com[:2] + (feet[supports[0],2]-com[2])/gravity[2]*gravity[:2]
            for family, equations, inset in (
                    ("normal_cap", cache[total], 0.),
                    ("stability_margin", ordinary, c["screening"]["support_margin_required_m"])):
                for eq in equations:
                    rows.append(eq[:2].tolist())
                    bounds.append(float(-eq[2]-eq[:2] @ offset-inset))
                    tags.append({"lost_leg_1based": lost+1, "gravity": gid,
                                 "com_sign_x": sx, "com_sign_y": sy, "constraint": family})
    return np.array(rows), np.array(bounds), tags


def solve_region(a, b, tags=None):
    """Maximize signed common slack; check a dual contradiction if empty.

For unit normal rows slack is a Chebyshev radius in meters. A negative
optimum supplies lambda>=0, lambda*A=0, lambda*b<0. This is a checked
floating-point certificate, not an exact-arithmetic proof.
"""
    a, b = np.asarray(a,dtype=float), np.asarray(b,dtype=float)
    if (a.ndim != 2 or a.shape[1] != 2 or b.shape != (len(a),) or not len(a)
            or not np.isfinite(a).all() or not np.isfinite(b).all()):
        raise ValueError("Invalid region halfspaces")
    norms = np.linalg.norm(a, axis=1)
    if np.any((norms > TOL) & (np.abs(norms-1) > TOL)):
        raise ValueError("Region halfspaces must be normalized")
    matrix = np.column_stack([a, np.ones(len(a))])
    r = linprog([0.,0.,-1.], A_ub=matrix, b_ub=b, bounds=[(None,None)]*3, method="highs")
    if not r.success:
        raise RuntimeError(f"Region solver indeterminate: {r.status}: {r.message}")
    if not np.isfinite(r.x).all() or np.max(matrix @ r.x - b) > TOL:
        raise ValueError("Invalid region primal witness")
    slack = float(r.x[2])
    result = {"status": "EMPTY" if slack < -TOL else ("BOUNDARY_UNRESOLVED" if slack <= TOL else "NECESSARY_REGION_ONLY"),
              "center_body_translation_xy_m": r.x[:2].tolist(), "signed_inradius_m": slack,
              "row_count": len(a), "hardware_motion_allowed": False}
    if slack < -TOL:
        lam = -np.asarray(r.ineqlin.marginals)
        cancel = float(np.linalg.norm(lam @ a))
        rhs = float(lam @ b)
        if (not np.isfinite(lam).all() or np.min(lam) < -TOL or abs(lam.sum()-1) > TOL
                or cancel > TOL or rhs >= -TOL or abs(rhs-slack) > TOL):
            raise ValueError("Invalid region dual infeasibility certificate")
        selected = np.flatnonzero(lam > 0)
        result["empty_certificate"] = {"normal_cancellation_residual": cancel, "combined_rhs_m": rhs,
            "terms": [{"row": int(i), "weight": float(lam[i]), "a": a[i].tolist(), "b": float(b[i]),
                       "tag": None if tags is None else tags[i]} for i in selected]}
    return result
