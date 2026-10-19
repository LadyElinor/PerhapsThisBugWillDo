"""Independent planar necessary-condition certificate for baseline failures.

This is a post-comparison diagnostic, not an additional candidate experiment.
All supporting ankles share a plane. Force/moment equilibrium fixes the normal
load sum and its centroid at the gravity-line projection. Enumerating the
vertices of 0 <= N_i <= cap, sum N_i = total gives a capped support polygon.
A projection outside it is impossible regardless of motor torque or friction.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import itertools
import json
from pathlib import Path

import numpy as np
from scipy.spatial import ConvexHull

import support_loss_analysis as study


def capped_polygon(feet_xy, total_n, cap_n):
    points = np.asarray(feet_xy, dtype=float)
    n = len(points)
    if (points.shape != (n, 2) or n < 3 or not np.isfinite(points).all()
            or not np.isfinite([total_n, cap_n]).all() or total_n <= 0 or cap_n <= 0):
        raise ValueError("Invalid capped polygon inputs")
    if n*cap_n < total_n:
        return np.empty((0, 2))
    vertices = []
    # In an n-dimensional clipped simplex, all but at most one weight are at bounds.
    for free in range(n):
        fixed = [i for i in range(n) if i != free]
        for bits in itertools.product((0, 1), repeat=n-1):
            loads = np.zeros(n)
            loads[fixed] = np.array(bits)*cap_n
            loads[free] = total_n - loads.sum()
            if -1e-10 <= loads[free] <= cap_n + 1e-10:
                vertices.append(loads @ points / total_n)
    return np.unique(np.array(vertices), axis=0)


def polygon_margin(vertices, point):
    if len(vertices) < 3:
        raise ValueError("Degenerate capped polygon")
    h = ConvexHull(vertices)
    distances = -(h.equations[:, :2] @ point + h.equations[:, 2])
    i = int(np.argmin(distances))
    return float(distances[i]), h.equations[i].tolist()


def run(results_dir):
    report = json.loads((results_dir / "results.json").read_text())
    if not report["complete"]:
        raise ValueError("Incomplete comparison")
    _, c = study.frozen_inputs()
    baseline = report["variants"][0]
    assert baseline["id"] == "baseline"
    poses = {(p, s): (f, a) for p, s, _, f, a in study.poses(c, {"id": "baseline"})}
    loads = {(sx, sy, gid): (com, g) for sx, sy, gid, _, _, com, g in study.load_cases(c)}
    certificates = []
    mismatch = []
    counts = {"outside_uncapped_support_polygon": 0, "inside_uncapped_but_outside_capped": 0,
              "inside_capped_polygon": 0, "baseline_loss_cases": 0}
    examples = {}
    with gzip.open(results_dir / "cases.csv.gz", "rt") as f:
        for row in csv.DictReader(f):
            if row["variant"] != "baseline" or not row["lost_leg_1based"]:
                continue
            feet, active = poses[int(row["phase"]), int(row["sample"])]
            lost = int(row["lost_leg_1based"]) - 1
            supports = tuple(i for i in active if i != lost)
            gid = row["scenario"].split("|")[-1]
            com, g = loads[int(row["com_sign_x"]), int(row["com_sign_y"]), gid]
            total = -c["gross_mass_kg"]*c["screening"]["load_factor"]*g[2]
            _, _, projection = study.edge_margin(feet, supports, com, g)
            vertices = capped_polygon(feet[list(supports), :2], total, c["screening"]["normal_force_limit_n"])
            capped_margin, separating_plane = polygon_margin(vertices, projection)
            uncapped_margin = float(row["margin_m"])
            impossible = capped_margin < -1e-9
            lp_failed = row["lp_feasible"] == "0"
            if impossible != lp_failed:
                mismatch.append(row["scenario"])
            if uncapped_margin < -1e-9:
                category = "outside_uncapped_support_polygon"
            elif impossible:
                category = "inside_uncapped_but_outside_capped"
            else:
                category = "inside_capped_polygon"
            counts[category] += 1
            counts["baseline_loss_cases"] += 1
            cert = {"scenario": row["scenario"], "total_normal_n": total,
                    "uncapped_margin_m": uncapped_margin, "capped_margin_m": capped_margin,
                    "separating_plane": separating_plane, "category": category}
            certificates.append(cert)
            if category not in examples:
                examples[category] = {**cert, "feet_m": feet.tolist(), "supports_1based": [i+1 for i in supports],
                                      "projection_xy_m": projection, "capped_vertices_xy_m": vertices.tolist(),
                                      "swing_leg_1based": int(row["swing_leg_1based"]), "lost_leg_1based": lost+1}
    if len(certificates) != 5400 or mismatch:
        raise ValueError(f"Planar certificate disagrees with baseline: {mismatch[:10]}")
    output = {"method": __doc__, "counts": counts, "disagreements": mismatch, "examples": examples,
              "source_sha256": study.sha256(__file__), "comparison_results_sha256": study.sha256(results_dir / "results.json"),
              "certificates": certificates, "hardware_motion_allowed": False}
    target = results_dir / "planar_certificates.json.gz"
    if target.exists():
        raise ValueError("Refusing to overwrite certificates")
    with target.open("wb") as raw, gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as gz:
        gz.write((json.dumps(output, separators=(",", ":"), allow_nan=False)+"\n").encode())
    draw(report, examples, results_dir)
    print(json.dumps(counts, indent=2))


def draw(report, examples, output):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size": 10, "svg.hashsalt": "support-loss-01"})
    baseline = report["variants"][0]
    matrix = np.full((6, 6), np.nan)
    for pair, count in baseline["loss_breakdowns"]["swing_lost_pair"].items():
        i, j = map(int, pair.split(","))
        matrix[i-1, j-1] = count["rejected"]
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(11.5, 5.7), layout="constrained")
    ax.imshow(matrix, vmin=0, vmax=180, cmap="YlOrRd")
    for i, j in itertools.product(range(6), repeat=2):
        ax.text(j, i, "—" if i == j else str(int(matrix[i, j])), ha="center", va="center", fontsize=11, color="white" if i != j and matrix[i, j] >= 90 else "black")
    ax.set(xticks=range(6), yticks=range(6), xticklabels=range(1, 7), yticklabels=range(1, 7),
           xlabel="Additional lost leg", ylabel="Swing leg", title="Baseline rejections by missing pair\n180 sampled cases per off-diagonal cell")
    example = examples["inside_uncapped_but_outside_capped"]
    feet = np.array(example["feet_m"])
    supports = np.array(example["supports_1based"]) - 1
    hull = ConvexHull(feet[supports, :2])
    poly = feet[supports[hull.vertices], :2]
    bx.fill(poly[:, 0], poly[:, 1], color="#cbd5e1", label="Uncapped support polygon")
    vertices = np.array(example["capped_vertices_xy_m"])
    capped = vertices[ConvexHull(vertices).vertices]
    bx.fill(capped[:, 0], capped[:, 1], color="#86c5b3", label="Centroids allowed by 300 N cap")
    for i, foot in enumerate(feet):
        bx.scatter(foot[0], foot[1], color="#243b53" if i in supports else "#b91c1c", marker="o" if i in supports else "x")
        bx.annotate(str(i+1), foot[:2], xytext=(6, 6), textcoords="offset points")
    projection = example["projection_xy_m"]
    bx.scatter(*projection, marker="*", s=160, color="#b91c1c", label="Projected COM")
    bx.set(xlabel="Body x (m)", ylabel="Body y (m)", title="Why being inside the hull is insufficient\nSwing 1, lost 2 · flat · COM (−40, −30) mm")
    bx.set_aspect("equal")
    bx.legend(loc="upper center", bbox_to_anchor=(.5, -.16), fontsize=8)
    fig.suptitle("Lunar Weevil COTS-1.1 • conditional static analysis", fontsize=14)
    fig.savefig(output / "support_loss_diagnostics.svg", metadata={"Date": None})
    fig.savefig(output / "support_loss_diagnostics.png", dpi=160)
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, required=True)
    run(parser.parse_args().results_dir)
