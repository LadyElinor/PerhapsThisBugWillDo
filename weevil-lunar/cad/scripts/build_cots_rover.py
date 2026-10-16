"""Generate a COTS rover packaging model, interface coupons and kinematics-only URDF.

Requires optional cadquery==2.7.0. Dimensions are mm in CAD, metres in analysis.
Commercial parts are dimensioned envelopes, not redistributed vendor geometry.
No manufacturing release or assembly-wide interference certification is implied.
"""

from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from models.cots_rover import load_config, nominal_feet, ik, points, axes, gait_samples


def normalize_exchange_text(path):
    """Remove exporter trailing whitespace without changing STEP/SVG tokens."""
    path.write_text("\n".join(line.rstrip() for line in path.read_text().splitlines()).rstrip() + "\n")


def output_adapter():
    import cadquery as cq

    # CubeMars drawing: six M4 at PCD28, two 3mm dowels at 0/180 degrees.
    disk = cq.Workplane("XY").circle(25).extrude(8)
    bolt = [(14 * math.cos(math.radians(a)), 14 * math.sin(math.radians(a))) for a in range(30, 360, 60)]
    disk = disk.faces(">Z").workplane().pushPoints(bolt).hole(4.5)
    disk = disk.faces(">Z").workplane().pushPoints([(14, 0), (-14, 0)]).hole(3)
    disk = disk.faces(">Z").workplane().hole(20.1)
    # Pilot is a fit coupon, deliberately detachable from the eventual torque hub.
    pilot = cq.Workplane("XY").circle(20.98 / 2).circle(20.1 / 2).extrude(-4.2)
    return disk.union(pilot).val()


def stator_adapter():
    import cadquery as cq

    p = cq.Workplane("XY").rect(116, 116).extrude(6)
    p = p.faces(">Z").workplane().hole(72)
    bolts = [(44.5 * math.cos(math.radians(a)), 44.5 * math.sin(math.radians(a))) for a in range(0, 360, 45)]
    p = p.faces(">Z").workplane().pushPoints(bolts).hole(3.4)
    p = p.faces(">Z").workplane().pushPoints([(x, y) for x in (-49, 49) for y in (-49, 49)]).hole(5.5)
    return p.val()


def cylinder(radius, length, center, axis):
    import cadquery as cq

    v = np.asarray(axis, dtype=float)
    v /= np.linalg.norm(v)
    return cq.Solid.makeCylinder(radius, length, cq.Vector(*(np.asarray(center) - v * length / 2)), cq.Vector(*v))


def bar(a, b, width=25):
    import cadquery as cq

    a, b = np.asarray(a), np.asarray(b)
    delta = b - a
    length = np.linalg.norm(delta)
    v = delta / length
    reference = np.array([0.0, 0.0, 1.0]) if abs(v[2]) < 0.9 else np.array([0.0, 1.0, 0.0])
    x = np.cross(reference, v)
    x /= np.linalg.norm(x)
    plane = cq.Plane(origin=cq.Vector(*a), xDir=cq.Vector(*x), normal=cq.Vector(*v))
    return cq.Workplane(plane).rect(width, width).rect(width - 4, width - 4).extrude(float(length)).val()


def packaging(c, feet):
    import cadquery as cq

    solids = []

    def add(name, shape, color, kind):
        solids.append({"name": name, "shape": shape, "color": color, "kind": kind})

    # Deck and two side rails; the interior is an equipment volume, not a solid block.
    length, w, h = np.array(c["chassis_size_m"]) * 1000
    z = c["chassis_center_z_m"] * 1000
    add("Deck", cq.Workplane("XY").box(length, w, 3).translate((0, 0, z - h / 2)).val(), (0.31, 0.38, 0.40), "frame")
    for sy in (-1, 1):
        add(
            f"Rail_{sy}",
            cq.Workplane("XY").box(length, 20, 40).translate((0, sy * (w / 2 - 10), z - h / 2 + 20)).val(),
            (0.32, 0.4, 0.44),
            "frame",
        )
    # Battery dimensions from Bioenno; allowance for restraints is kept separate.
    add(
        "Battery_BLF3620A",
        cq.Workplane("XY").box(241, 130, 147).translate((0, 0, z - h / 2 + 3 + 147 / 2)).val(),
        (0.12, 0.18, 0.24),
        "equipment",
    )
    for side in (-1, 1):
        add(
            f"Electronics_allowance_{side}",
            cq.Workplane("XY").box(160, 300, 120).translate((side * 210, 0, z - h / 2 + 63)).val(),
            (0.12, 0.34, 0.36),
            "equipment",
        )
    for i in range(6):
        q = ik(c, i, feet[i])
        ps = points(c, i, q) * 1000
        ax = axes(c, i, q)
        # Joint cartridge envelope includes independent support bearing allocation.
        for j, (origin, direction) in enumerate(zip(ps[:3], ax)):
            motor_center = origin - 72 * direction
            add(f"L{i + 1}_motor{j + 1}", cylinder(49, 61.9, motor_center, direction), (0.76, 0.36, 0.12), "actuator")
            add(f"L{i + 1}_carrier{j + 1}", cylinder(28, 84, origin, direction), (0.28, 0.34, 0.38), "carrier")
        for j, (a, b) in enumerate(zip(ps[:3], ps[1:])):
            offset = np.array([0.0, 0.0, -12.0]) if j == 0 else 38 * ax[1]
            # Visible link stock connects defined axes; end clevis detail is a separate fabrication item.
            add(f"L{i + 1}_link{j + 1}", bar(a + offset, b + offset), (0.62, 0.69, 0.70), "link_stock")
        f = ps[3]
        direction = (ps[3] - ps[2]) / np.linalg.norm(ps[3] - ps[2])
        add(f"L{i + 1}_Mini45", cylinder(57.9 / 2, 25.1, f - direction * 28, direction), (0.18, 0.45, 0.48), "sensor")
        add(f"L{i + 1}_gimbal", cylinder(17, 38, f - [0, 0, 19], [0, 0, 1]), (0.3, 0.4, 0.43), "gimbal")
        add(
            f"L{i + 1}_foot",
            cylinder(
                c["foot_radius_m"] * 1000,
                8,
                [f[0], f[1], 4 + (feet[i, 2] - c["foot_pivot_height_m"]) * 1000],
                [0, 0, 1],
            ),
            (0.16, 0.22, 0.25),
            "foot",
        )
    # Four independently guided landing shoes; rods may not take side loading.
    for x, y in [(x, y) for x in (-270, 270) for y in (-145, 145)]:
        add(f"LandingGuide_{x}_{y}", cylinder(18, 120, [x, y, 145], [0, 0, 1]), (0.47, 0.52, 0.56), "landing")
        add(
            f"LandingShoe_{x}_{y}",
            cq.Workplane("XY").box(65, 55, 10).translate((x, y, 75)).val(),
            (0.2, 0.24, 0.27),
            "landing",
        )
    return solids


def verify_geometry(solids):
    names = [p["name"] for p in solids]
    if len(names) != len(set(names)):
        raise ValueError("Duplicate component name")
    if any(not p["shape"].isValid() or len(p["shape"].Solids()) != 1 for p in solids):
        raise ValueError("Invalid or multi-solid component")
    # Packaging screen deliberately limited to actuator envelopes against each other,
    # the chassis and equipment. Joint/link mating overlaps are not silently waived.
    critical = [p for p in solids if p["kind"] in ("actuator", "frame", "equipment")]
    overlaps = []
    for n, a in enumerate(critical):
        for b in critical[n + 1 :]:
            if a["kind"] != "actuator" and b["kind"] != "actuator":
                continue
            boxa, boxb = a["shape"].BoundingBox(), b["shape"].BoundingBox()
            if any(
                getattr(boxa, v + "max") < getattr(boxb, v + "min")
                or getattr(boxb, v + "max") < getattr(boxa, v + "min")
                for v in "xyz"
            ):
                continue
            volume = a["shape"].intersect(b["shape"]).Volume()
            if volume > 1e-5:
                overlaps.append({"a": a["name"], "b": b["name"], "volume_mm3": volume})
    return overlaps


def render(solids, path, c):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    fig = plt.figure(figsize=(13, 9), facecolor="#f4f3ef")
    ax = fig.add_subplot(111, projection="3d")
    for p in solids:
        verts, triangles = p["shape"].tessellate(3)
        v = np.array([x.toTuple() for x in verts])
        faces = [v[list(t)] for t in triangles]
        mesh = Poly3DCollection(faces, facecolor=p["color"], edgecolor="none", alpha=1)
        ax.add_collection3d(mesh)
    ax.set_xlim(-620, 620)
    ax.set_ylim(-680, 680)
    ax.set_zlim(0, 480)
    ax.set_box_aspect((1240, 1360, 480))
    ax.view_init(elev=25, azim=-48)
    ax.set_xlabel("Forward / mm")
    ax.set_ylabel("Left / mm")
    ax.set_zlabel("Height / mm")
    ax.set_title("WEEVIL COTS-1 | assembled packaging model", loc="left", fontweight="bold", fontsize=18, pad=20)
    fig.text(
        0.08,
        0.045,
        f"Orange: commercial actuator envelopes  •  Teal: foot force sensors\n{c['gross_mass_kg']:g} kg gross design limit • Five-foot support gait • Prototype geometry, not a fabrication release",
        fontsize=11,
        color="#37484f",
    )
    fig.savefig(path, dpi=160, facecolor=fig.get_facecolor())
    plt.close(fig)


def urdf(c, path):
    root = ET.Element("robot", name="weevil_cots_v1_kinematics")
    root.append(
        ET.Comment("Kinematics-only: no inertials or validated collision meshes. Do not use as a dynamics model.")
    )

    def link(name, box=None):
        e = ET.SubElement(root, "link", name=name)
        if box:
            v = ET.SubElement(e, "visual")
            ET.SubElement(v, "geometry").append(ET.Element("box", size=" ".join(map(str, box))))
        return e

    def joint(name, parent, child, xyz, rpy, axis=None, limits=None):
        j = ET.SubElement(root, "joint", name=name, type="revolute" if axis else "fixed")
        ET.SubElement(j, "parent", link=parent)
        ET.SubElement(j, "child", link=child)
        ET.SubElement(j, "origin", xyz=" ".join(map(str, xyz)), rpy=" ".join(map(str, rpy)))
        if axis:
            ET.SubElement(j, "axis", xyz=" ".join(map(str, axis)))
            ET.SubElement(
                j,
                "limit",
                lower=str(limits[0]),
                upper=str(limits[1]),
                effort=str(c["actuator"]["design_torque_limit_nm"]),
                velocity=str(c["joint_velocity_limit_rad_s"]),
            )

    link("base", c["chassis_size_m"])
    limits = np.radians(c["joint_limits_deg"])
    for i in range(6):
        names = [f"L{i + 1}_{n}" for n in ("coxa", "femur", "tibia", "ankle")]
        for name in names:
            link(name)
        joint(
            f"L{i + 1}_yaw",
            "base",
            names[0],
            [*c["hips_xy_m"][i], 0.0],
            [0, 0, math.radians(c["leg_azimuth_deg"][i])],
            [0, 0, 1],
            limits[0],
        )
        joint(f"L{i + 1}_pitch", names[0], names[1], [c["coxa_m"], 0, 0], [0, 0, 0], [0, 1, 0], limits[1])
        joint(f"L{i + 1}_knee", names[1], names[2], [c["femur_m"], 0, 0], [0, 0, 0], [0, 1, 0], limits[2])
        joint(f"L{i + 1}_ankle_frame", names[2], names[3], [c["tibia_m"], 0, 0], [0, -math.pi / 2, 0])
    ET.indent(root)
    ET.ElementTree(root).write(path, encoding="unicode", xml_declaration=True)


def build(output: Path, config: Path):
    import cadquery as cq

    c = load_config(config)
    output.mkdir(parents=True, exist_ok=False)
    solids = packaging(c, nominal_feet(c))
    overlaps = verify_geometry(solids)
    sweep = []
    for name, feet, _ in gait_samples(c, 4):
        for issue in verify_geometry(packaging(c, feet)):
            sweep.append({"pose": name, **issue})
    if overlaps or sweep:
        raise ValueError(f"Actuator packaging interference: {(overlaps + sweep)[:6]}")
    assembly = cq.Assembly(name="COTS1_packaging")
    for p in solids:
        assembly.add(p["shape"], name=p["name"], color=cq.Color(*p["color"]))
    # AP214 is sufficient for this packaging exchange. Explicitly report the actual schema.
    # CadQuery's assembly exporter controls schema; do not relabel the file AP242.
    step = output / "rover_packaging.step"
    assembly.save(str(step))
    normalize_exchange_text(step)
    imported = cq.importers.importStep(str(step)).val()
    if not isinstance(imported, cq.Shape):
        raise ValueError("STEP import did not produce a shape")
    original_volume = sum(p["shape"].Volume() for p in solids)
    error = abs(imported.Volume() - original_volume) / original_volume
    if not imported.isValid() or len(imported.Solids()) != len(solids) or error > 1e-8:
        raise ValueError("STEP roundtrip failed")
    schema = next(x.strip() for x in step.read_text().splitlines() if "FILE_SCHEMA" in x)
    for name, shape in [("output_interface_coupon", output_adapter()), ("stator_interface_coupon", stator_adapter())]:
        if not shape.isValid() or len(shape.Solids()) != 1:
            raise ValueError(name)
        cq.exporters.export(shape, str(output / f"{name}.step"))
        cq.exporters.export(
            shape,
            str(output / f"{name}.svg"),
            opt={"projectionDir": (0, 0, 1), "showHidden": False, "width": 650, "height": 650},
        )
    for exported in output.iterdir():
        if exported.suffix in (".step", ".svg"):
            normalize_exchange_text(exported)
    render(solids, output / "rover_overview.png", c)
    urdf(c, output / "rover_kinematics.urdf")
    report = {
        "status": "packaging_and_interface_coupons_only",
        "cadquery": cq.__version__,
        "config_sha256": hashlib.sha256(config.read_bytes()).hexdigest(),
        "solids": len(solids),
        "valid": True,
        "actuator_interferences": overlaps,
        "swept_pose_count": 30,
        "swept_actuator_interferences": sweep,
        "step_schema": schema,
        "roundtrip_solid_count": len(imported.Solids()),
        "relative_volume_error": error,
        "unverified": [
            "Carrier/yoke/coupler manufacturing details and bearing fits",
            "Full link/cover/cable swept collision and structural analysis",
            "Inertials, thermal performance and flight qualification",
        ],
    }
    (output / "cad_checks.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=ROOT / "design/cots_v1/config.json")
    args = parser.parse_args()
    build(args.output, args.config)
