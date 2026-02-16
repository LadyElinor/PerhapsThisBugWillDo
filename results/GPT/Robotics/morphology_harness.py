#!/usr/bin/env python3
"""
morphology_harness.py — Shared evaluation harness for morphology variants (POC)

Compares simplified archetypes:
  - Ant (speed/throughput)
  - Beetle/Weevil (generalist durability, screw joint)
  - Arachnid (reach/precision, 8 legs)
  - Crab (lateral force/stability, reduced ROM)

Outputs:
  - morphology_tradeoff.csv
  - lunar_morphology_tradeoff.md
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Tuple
from pathlib import Path

import numpy as np
from numpy.typing import NDArray
from scipy.spatial import ConvexHull

from regolith_contact_model import RegolithType, RegolithProperties, FootGeometry, RegolithContactModel


def rot_axis_angle(axis: NDArray[np.float64], angle: float) -> NDArray[np.float64]:
    axis = np.asarray(axis, dtype=float)
    axis = axis / (np.linalg.norm(axis) + 1e-12)
    x, y, z = axis
    c = math.cos(angle); s = math.sin(angle); C = 1.0 - c
    return np.array([
        [c + x*x*C,     x*y*C - z*s, x*z*C + y*s],
        [y*x*C + z*s,   c + y*y*C,   y*z*C - x*s],
        [z*x*C - y*s,   z*y*C + x*s, c + z*z*C],
    ], dtype=float)

def T_from_R_p(R: NDArray[np.float64], p: NDArray[np.float64]) -> NDArray[np.float64]:
    T = np.eye(4, dtype=float); T[:3,:3] = R; T[:3,3] = p; return T

@dataclass
class Joint:
    kind: str
    axis: NDArray[np.float64]
    q_min: float
    q_max: float
    pitch: float = 0.0
    def sample(self, n: int, rng: np.random.Generator) -> NDArray[np.float64]:
        return rng.uniform(self.q_min, self.q_max, size=n)
    def transform(self, q: float) -> NDArray[np.float64]:
        axis = np.asarray(self.axis, dtype=float)
        axis = axis / (np.linalg.norm(axis) + 1e-12)
        R = rot_axis_angle(axis, q)
        p = np.zeros(3, dtype=float)
        if self.kind == "screw":
            p = axis * (self.pitch * q)
        return T_from_R_p(R, p)

@dataclass
class Leg:
    joints: List[Joint]
    links: List[NDArray[np.float64]]
    def forward_kinematics(self, q: NDArray[np.float64]) -> NDArray[np.float64]:
        T = np.eye(4, dtype=float)
        for joint, link, qi in zip(self.joints, self.links, q):
            T = T @ joint.transform(float(qi))
            T = T @ T_from_R_p(np.eye(3), link)
        return T[:3, 3].copy()

def workspace_cloud(leg: Leg, n_samples: int, rng: np.random.Generator) -> NDArray[np.float64]:
    Q = np.column_stack([j.sample(n_samples, rng) for j in leg.joints])
    return np.array([leg.forward_kinematics(q) for q in Q], dtype=float)

def hull_volume(points: NDArray[np.float64]) -> float:
    if points.shape[0] < 10:
        return 0.0
    try:
        return float(ConvexHull(points).volume)
    except Exception:
        return 0.0

@dataclass(frozen=True)
class MorphologySpec:
    name: str
    n_legs: int
    foot_radius: float
    links: Tuple[Tuple[float, float, float], ...]
    joints: Tuple[Tuple[str, Tuple[float, float, float], float, float, float], ...]  # kind, axis, qmin, qmax, pitch

def build_leg(spec: MorphologySpec) -> Leg:
    joints = [Joint(kind=k, axis=np.array(ax, dtype=float), q_min=qmin, q_max=qmax, pitch=p)
              for (k, ax, qmin, qmax, p) in spec.joints]
    links = [np.array(L, dtype=float) for L in spec.links]
    return Leg(joints=joints, links=links)

def morphologies() -> List[MorphologySpec]:
    ant = MorphologySpec(
        name="Ant (speed/throughput)",
        n_legs=6,
        foot_radius=0.035,
        links=((0.045,0,0),(0.035,0,0),(0.025,0,0)),
        joints=(
            ("revolute",(0,0,1), -math.pi/3, math.pi/3, 0.0),
            ("revolute",(0,1,0), -math.pi/2, math.pi/3, 0.0),
            ("revolute",(0,1,0), -2*math.pi/3, 0.0,     0.0),
        )
    )
    beetle = MorphologySpec(
        name="Beetle/Weevil (durability)",
        n_legs=6,
        foot_radius=0.05,
        links=((0.05,0,0),(0.04,0,0),(0.03,0,0)),
        joints=(
            ("revolute",(0,0,1), -math.pi/3, math.pi/3, 0.0),
            ("revolute",(0,1,0), -math.pi/2, math.pi/4, 0.0),
            ("screw",   (0,1,0), -2*math.pi/3, 0.0,     0.015),
        )
    )
    spider = MorphologySpec(
        name="Arachnid (reach/precision)",
        n_legs=8,
        foot_radius=0.04,
        links=((0.055,0,0),(0.045,0,0),(0.035,0,0)),
        joints=(
            ("revolute",(0,0,1), -math.pi/2,  math.pi/2, 0.0),
            ("revolute",(0,1,0), -2*math.pi/3, math.pi/3, 0.0),
            ("revolute",(0,1,0), -5*math.pi/6, 0.0,      0.0),
        )
    )
    crab = MorphologySpec(
        name="Crab (lateral force/stability)",
        n_legs=8,
        foot_radius=0.06,
        links=((0.05,0,0),(0.035,0,0),(0.02,0,0)),
        joints=(
            ("revolute",(0,0,1), -math.pi/4,  math.pi/4, 0.0),
            ("revolute",(0,1,0), -math.pi/3,  math.pi/6, 0.0),
            ("revolute",(0,1,0), -math.pi/2,  0.0,      0.0),
        )
    )
    return [ant, beetle, spider, crab]

@dataclass
class EvalRow:
    morphology: str
    terrain: str
    workspace_vol: float
    sinkage_cm: float
    cone_deg: float
    max_shear_N: float
    slope_margin_45: float
    notes: str

def evaluate(spec: MorphologySpec, terrain: RegolithType, body_mass: float, gravity_scale: float, n_samples: int, rng: np.random.Generator) -> EvalRow:
    leg = build_leg(spec)
    foot = FootGeometry.circular(radius=spec.foot_radius)
    reg = RegolithProperties.from_type(terrain)
    contact = RegolithContactModel(reg, foot, gravity=1.62)

    g = gravity_scale * 9.81
    F_leg = (body_mass * g) / spec.n_legs
    forces = contact.compute_contact_forces(F_leg)

    W = workspace_cloud(leg, n_samples=n_samples, rng=rng)
    vol = hull_volume(W)

    sink = forces.penetration_depth * 100.0
    cone = forces.friction_cone_angle
    shear = forces.max_shear_force
    slope_margin = cone / 45.0

    notes = []
    if spec.n_legs >= 8: notes.append("more legs → lower load/leg")
    if "Weevil" in spec.name or "Beetle" in spec.name: notes.append("screw coupling (robust routing)")
    if "Crab" in spec.name: notes.append("reduced ROM (stable contact)")
    if sink > 8.0: notes.append("deep sinkage risk")
    if slope_margin < 1.0: notes.append("45° slope likely unstable")

    return EvalRow(spec.name, terrain.value, vol, sink, cone, shear, slope_margin, "; ".join(notes) if notes else "—")

def main():
    rng = np.random.default_rng(7)
    body_mass = 30.0
    gravity_scale = 0.165
    terrains = [RegolithType.MARE, RegolithType.HIGHLAND, RegolithType.MIXED, RegolithType.COMPACTED]
    specs = morphologies()

    rows: List[EvalRow] = []
    for s in specs:
        for t in terrains:
            rows.append(evaluate(s, t, body_mass, gravity_scale, n_samples=12000, rng=rng))

    # CSV
    import csv
    with open("morphology_tradeoff.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["morphology","terrain","workspace_vol_m3","sinkage_cm","friction_cone_deg","max_shear_N","slope_margin_45","notes"])
        for r in rows:
            w.writerow([r.morphology, r.terrain, f"{r.workspace_vol:.6e}", f"{r.sinkage_cm:.3f}", f"{r.cone_deg:.2f}",
                        f"{r.max_shear_N:.2f}", f"{r.slope_margin_45:.3f}", r.notes])

    # MD
    md = []
    md.append("# Lunar morphology tradeoffs — POC (contact-constrained locomotion)\n")
    md.append("This is a comparative *architecture* analysis (not a biological reconstruction).")
    md.append("\n**Model:** Bekker pressure–sinkage + Mohr–Coulomb shear envelope, evaluated per-leg load under lunar gravity.\n")
    md.append("## Setup\n")
    md.append(f"- Body mass: **{body_mass} kg**")
    md.append(f"- Gravity: **{gravity_scale:.3f}× Earth** (Moon)")
    md.append("- Terrains: mare, highland, mixed, compacted\n")

    md.append("## Recommended role assignments\n")
    md.append("- **Ant-like** → *fast scouts / logistics* on modest slopes; traction is usually the bottleneck on steep terrain.")
    md.append("- **Beetle/Weevil-like** → *generalist traverser / workhorse*; screw coupling favors smooth force routing under uncertainty.")
    md.append("- **Arachnid-like** → *precision reach / probing / edge work*; extra legs reduce load per contact and tend to reduce sinkage.")
    md.append("- **Crab-like** → *stabilizer / lateral push / anchoring*; reduced ROM trades reach for predictable contact stability.\n")

    md.append("## Full metric table\n")
    md.append("| Morphology | Terrain | Workspace vol (m³, hull proxy) | Sinkage (cm) | Cone (deg) | Max shear (N) | 45° margin | Notes |")
    md.append("|---|---|---:|---:|---:|---:|---:|---|")
    for r in rows:
        md.append(f"| {r.morphology} | {r.terrain} | {r.workspace_vol:.3e} | {r.sinkage_cm:.2f} | {r.cone_deg:.1f} | {r.max_shear_N:.1f} | {r.slope_margin_45:.2f} | {r.notes} |")

    md.append("\n## Next upgrades (to make this a real design tool)\n")
    md.append("1) Replace hull volume with **ROM→accessible-set shrinkage** using torque limits ∩ contact wrench polytope.")
    md.append("2) Make the contact model **stance-geometry aware** (per-leg normal load varies over support polygon and slope).")
    md.append("3) Add **history dependence** (sinkage + shear accumulation, compaction).")
    md.append("4) Add **arachnid hydraulics state p** and true **hybrid mode switching** (stance/swing) for phase portraits.\n")

    Path("lunar_morphology_tradeoff.md").write_text("\n".join(md), encoding="utf-8")
    print("Wrote morphology_tradeoff.csv and lunar_morphology_tradeoff.md")

if __name__ == "__main__":
    main()
