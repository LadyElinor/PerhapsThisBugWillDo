#!/usr/bin/env python3
"""
regolith_contact_model.py — Minimal Lunar Regolith Contact Model (POC)

Implements:
  - Bekker-Wong pressure–sinkage (normal load ↔ sinkage depth)
  - Mohr–Coulomb shear envelope (max lateral force before slip)
  - friction cone helper

This is intentionally minimal so downstream scripts run end-to-end.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum


class RegolithType(Enum):
    MARE = "mare"
    HIGHLAND = "highland"
    MIXED = "mixed"
    COMPACTED = "compacted"


@dataclass(frozen=True)
class RegolithProperties:
    cohesion: float  # kPa
    phi: float       # degrees
    k_c: float       # kN/m^(n+1)
    k_phi: float     # kN/m^(n+2)
    n: float         # dimensionless
    density: float   # kg/m^3

    @classmethod
    def from_type(cls, regolith_type: RegolithType) -> "RegolithProperties":
        # POC buckets (Apollo-informed ranges; not mission-certified).
        if regolith_type == RegolithType.MARE:
            return cls(cohesion=0.10, phi=35.0, k_c=0.9, k_phi=1528.0, n=1.0, density=1500.0)
        if regolith_type == RegolithType.HIGHLAND:
            return cls(cohesion=0.05, phi=38.0, k_c=0.5, k_phi=820.0, n=1.1, density=1300.0)
        if regolith_type == RegolithType.COMPACTED:
            return cls(cohesion=0.40, phi=40.0, k_c=2.0, k_phi=3500.0, n=0.8, density=1800.0)
        # MIXED default
        return cls(cohesion=0.15, phi=37.0, k_c=1.2, k_phi=2000.0, n=1.0, density=1400.0)


@dataclass(frozen=True)
class FootGeometry:
    area: float
    radius: float
    cleat_gain_forward: float = 1.0
    cleat_gain_lateral: float = 1.0
    cleat_engage_threshold_preload: float = 20.0

    @classmethod
    def circular(
        cls,
        radius: float,
        cleat_gain_forward: float = 1.0,
        cleat_gain_lateral: float = 1.0,
        cleat_engage_threshold_preload: float = 20.0,
    ) -> "FootGeometry":
        return cls(
            area=math.pi * radius**2,
            radius=radius,
            cleat_gain_forward=cleat_gain_forward,
            cleat_gain_lateral=cleat_gain_lateral,
            cleat_engage_threshold_preload=cleat_engage_threshold_preload,
        )

    @classmethod
    def rectangular(
        cls,
        length: float,
        width: float,
        cleat_gain_forward: float = 1.0,
        cleat_gain_lateral: float = 1.0,
        cleat_engage_threshold_preload: float = 20.0,
    ) -> "FootGeometry":
        area = length * width
        radius = math.sqrt(area / math.pi)  # equivalent radius
        return cls(
            area=area,
            radius=radius,
            cleat_gain_forward=cleat_gain_forward,
            cleat_gain_lateral=cleat_gain_lateral,
            cleat_engage_threshold_preload=cleat_engage_threshold_preload,
        )


@dataclass(frozen=True)
class ContactForces:
    max_shear_force: float
    normal_reaction: float
    penetration_depth: float
    friction_cone_angle: float
    max_shear_forward: float | None = None
    max_shear_lateral: float | None = None
    friction_cone_forward_angle: float | None = None
    friction_cone_lateral_angle: float | None = None
    anchored: bool = False


class RegolithContactModel:
    def __init__(self, regolith: RegolithProperties, foot: FootGeometry, gravity: float = 1.62):
        self.regolith = regolith
        self.foot = foot
        self.gravity = gravity

    def bearing_capacity(self, depth: float) -> float:
        """Bekker pressure–sinkage: p = (k_c/b + k_phi) * z^n  (kPa)."""
        if depth <= 0.0:
            return 0.0
        b = max(self.foot.radius, 1e-9)
        return float((self.regolith.k_c / b + self.regolith.k_phi) * (depth ** self.regolith.n))

    def normal_load_from_depth(self, depth: float) -> float:
        p_pa = self.bearing_capacity(depth) * 1000.0
        return float(p_pa * self.foot.area)

    def depth_from_normal_load(self, F_normal: float, max_iter: int = 30, tol: float = 1e-8) -> float:
        if F_normal <= 0.0:
            return 0.0
        # initial guess (k_phi dominated)
        z = (F_normal / (max(self.regolith.k_phi, 1e-12) * 1000.0 * max(self.foot.area, 1e-12))) ** (1.0 / max(self.regolith.n, 1e-6))
        z = max(0.0, z)
        for _ in range(max_iter):
            F_calc = self.normal_load_from_depth(z)
            resid = F_calc - F_normal
            if abs(resid) <= tol * max(F_normal, 1.0):
                break
            dz = 1e-6
            dF = (self.normal_load_from_depth(z + dz) - F_calc) / dz
            if abs(dF) < 1e-12:
                break
            z = max(0.0, z - resid / dF)
        return float(z)

    def mohr_coulomb_shear(self, normal_load: float, depth: float) -> float:
        c_pa = self.regolith.cohesion * 1000.0
        phi = math.radians(self.regolith.phi)
        return float(c_pa * self.foot.area + normal_load * math.tan(phi))

    def friction_cone_angle(self, normal_load: float) -> float:
        depth = self.depth_from_normal_load(normal_load)
        shear = self.mohr_coulomb_shear(normal_load, depth)
        if normal_load <= 1e-12:
            return 0.0
        return float(math.degrees(math.atan(shear / normal_load)))

    def compute_contact_forces(self, normal_load: float) -> ContactForces:
        depth = self.depth_from_normal_load(normal_load)
        shear = self.mohr_coulomb_shear(normal_load, depth)
        angle = self.friction_cone_angle(normal_load)
        return ContactForces(
            max_shear_force=float(shear),
            normal_reaction=float(normal_load),
            penetration_depth=float(depth),
            friction_cone_angle=float(angle),
            max_shear_forward=float(shear),
            max_shear_lateral=float(shear),
            friction_cone_forward_angle=float(angle),
            friction_cone_lateral_angle=float(angle),
            anchored=False,
        )

    def compute_contact_forces_with_preload(
        self,
        body_normal_load: float,
        preload_normal: float = 0.0,
        twist_settle_gain: float = 1.0,
        use_directional_cleats: bool = True,
    ) -> ContactForces:
        """Preload-aware, optionally anisotropic contact estimate for active anchoring.

        Args:
            body_normal_load: Nominal per-foot normal load from body weight distribution.
            preload_normal: Additional commanded normal preload at the foot.
            twist_settle_gain: Multiplicative gain from twist-settle engagement.
            use_directional_cleats: Whether to apply directional forward/lateral gains.
        """
        preload = max(0.0, float(preload_normal))
        effective_normal = max(0.0, float(body_normal_load) + preload)
        base = self.compute_contact_forces(effective_normal)

        anchored = preload >= max(0.0, float(self.foot.cleat_engage_threshold_preload))
        settle_gain = max(0.1, float(twist_settle_gain)) if anchored else 1.0

        if use_directional_cleats:
            forward_gain = max(0.1, float(self.foot.cleat_gain_forward)) * settle_gain
            lateral_gain = max(0.1, float(self.foot.cleat_gain_lateral)) * settle_gain
        else:
            forward_gain = lateral_gain = settle_gain

        shear_fwd = base.max_shear_force * forward_gain
        shear_lat = base.max_shear_force * lateral_gain
        shear_iso = min(shear_fwd, shear_lat)

        cone_fwd = float(math.degrees(math.atan(shear_fwd / max(base.normal_reaction, 1e-12))))
        cone_lat = float(math.degrees(math.atan(shear_lat / max(base.normal_reaction, 1e-12))))
        cone_iso = float(math.degrees(math.atan(shear_iso / max(base.normal_reaction, 1e-12))))

        return ContactForces(
            max_shear_force=float(shear_iso),
            normal_reaction=base.normal_reaction,
            penetration_depth=base.penetration_depth,
            friction_cone_angle=cone_iso,
            max_shear_forward=float(shear_fwd),
            max_shear_lateral=float(shear_lat),
            friction_cone_forward_angle=float(cone_fwd),
            friction_cone_lateral_angle=float(cone_lat),
            anchored=anchored,
        )
