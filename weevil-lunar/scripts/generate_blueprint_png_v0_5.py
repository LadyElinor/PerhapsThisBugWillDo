#!/usr/bin/env python3
"""Generate Lunar Weevil blueprint PNG v0.5 reflecting 2026-02-22 updates."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import yaml

ROOT = Path(__file__).resolve().parents[1]
PARAMS = ROOT / "cad" / "weevil_leg_params.yaml"
RECEIPT = ROOT / "cad" / "exports" / "latest" / "export_receipt_v0.4.json"
OUTDIR = ROOT / "results" / "blueprints"


def load_params() -> dict:
    return yaml.safe_load(PARAMS.read_text(encoding="utf-8"))


def load_receipt() -> dict:
    if RECEIPT.exists():
        return json.loads(RECEIPT.read_text(encoding="utf-8"))
    return {"interface_version": "v0.5", "cots_profile_id": "unknown", "timestamp_utc": "unknown"}


def style(ax):
    ax.set_facecolor("#0b1e39")
    ax.tick_params(colors="white", labelsize=7)
    ax.title.set_color("white")
    for s in ax.spines.values():
        s.set_color("white")
    ax.grid(True, color="#4a6a8a", linestyle=":", linewidth=0.5)


def dim(ax, x1, y1, x2, y2, label):
    ax.annotate("", xy=(x1, y1), xytext=(x2, y2), arrowprops=dict(arrowstyle="<->", color="#ffd166", lw=1))
    ax.text((x1 + x2) / 2, (y1 + y2) / 2 + 3, label, color="#ffd166", fontsize=8, ha="center")


def top_view(ax, body_l, body_w, leg_reach):
    ax.set_title("Top")
    ax.add_patch(patches.Rectangle((-body_l / 2, -body_w / 2), body_l, body_w, fill=False, ec="#7fd3ff", lw=2))
    y_offsets = [body_w / 2 + 14, 0, -body_w / 2 - 14]
    for side in (-1, 1):
        x0 = side * body_l / 2
        for y in y_offsets:
            ax.plot([x0, x0 + side * leg_reach], [y, y], color="#7fd3ff", lw=2)

    ax.add_patch(patches.Circle((body_l / 2, 0), radius=10, fill=False, ec="#ff6b6b", lw=1.3, ls="--"))
    ax.add_patch(patches.Circle((-body_l / 2, 0), radius=10, fill=False, ec="#ff6b6b", lw=1.3, ls="--"))

    dim(ax, -body_l / 2, body_w / 2 + 24, body_l / 2, body_w / 2 + 24, f"L={body_l:.0f} mm")
    dim(ax, -body_l / 2 - 22, -body_w / 2, -body_l / 2 - 22, body_w / 2, f"W={body_w:.0f} mm")

    ax.set_aspect("equal")
    ax.set_xlim(-175, 175)
    ax.set_ylim(-130, 130)


def front_view(ax, body_w, stance_h, leg_span):
    ax.set_title("Front")
    ax.add_patch(patches.Rectangle((-body_w / 2, stance_h - 24), body_w, 24, fill=False, ec="#7fd3ff", lw=2))
    for x in (-body_w / 2 + 14, 0, body_w / 2 - 14):
        ax.plot([x, x], [stance_h - 24, 20], color="#7fd3ff", lw=2)
        ax.plot([x - 12, x + 12], [0, 0], color="#7fd3ff", lw=2)

    dim(ax, -body_w / 2, stance_h + 18, body_w / 2, stance_h + 18, f"Track={body_w:.0f} mm")
    dim(ax, body_w / 2 + 22, 0, body_w / 2 + 22, stance_h, f"H={stance_h:.0f} mm")
    dim(ax, -leg_span / 2, -14, leg_span / 2, -14, f"Span~{leg_span:.0f} mm")

    ax.set_aspect("equal")
    ax.set_xlim(-125, 125)
    ax.set_ylim(-30, 230)


def side_view(ax, body_l, stance_h, femur_len, tibia_stroke):
    ax.set_title("Side")
    ax.add_patch(patches.Rectangle((-body_l / 2, stance_h - 20), body_l, 20, fill=False, ec="#7fd3ff", lw=2))
    hip = (-20, stance_h - 20)
    knee = (hip[0] + femur_len * 0.6, hip[1] - femur_len * 0.55)
    foot = (knee[0] + tibia_stroke * 0.9, 0)
    ax.plot([hip[0], knee[0]], [hip[1], knee[1]], color="#7fd3ff", lw=2)
    ax.plot([knee[0], foot[0]], [knee[1], foot[1]], color="#7fd3ff", lw=2)
    ax.plot([foot[0] - 12, foot[0] + 12], [0, 0], color="#7fd3ff", lw=2)

    dim(ax, hip[0], hip[1] + 14, knee[0], knee[1] + 14, f"Femur={femur_len:.0f} mm")
    dim(ax, knee[0], knee[1] - 14, foot[0], foot[1] - 14, f"Stroke={tibia_stroke:.0f} mm")

    ax.set_aspect("equal")
    ax.set_xlim(-100, 160)
    ax.set_ylim(-30, 220)


def meta_panel(ax, receipt, p):
    ax.set_title("Update Metadata")
    ax.axis("off")
    lines = [
        "Blueprint: v0.5 (2026-02-22)",
        f"Interface receipt: {receipt.get('interface_version', 'v0.4')}",
        f"COTS profile: {receipt.get('cots_profile_id', 'unknown')}",
        "Baseline leg: uniform_ae070",
        "Baseline cleat: CLEAT-C1 (asymmetric chevron)",
        "Fallback: hybrid_b + CLEAT-C2",
        "Validation state: pre-hardware",
        "Phase-0 scope: single-leg bench readiness",
        f"Stance height: {p['body']['stance_height_mm']} mm",
        f"Femur length: {p['femur']['link_length_mm']} mm",
        f"Tibia stroke: {p['tibia_screw']['stroke_mm']} mm",
        "Next gate: execute 12-run 35°/45° A/B matrix",
    ]
    y = 0.97
    for line in lines:
        ax.text(0.02, y, line, color="#d9ecff", fontsize=9, va="top", transform=ax.transAxes)
        y -= 0.075


def main() -> int:
    p = load_params()
    receipt = load_receipt()

    stance_h = p["body"]["stance_height_mm"]
    femur_len = p["femur"]["link_length_mm"]
    tibia_stroke = p["tibia_screw"]["stroke_mm"]

    body_l = 120
    body_w = 80
    leg_reach = 40
    leg_span = 2 * (femur_len + tibia_stroke)

    fig = plt.figure(figsize=(15, 8), facecolor="#0b1e39")
    gs = fig.add_gridspec(2, 4, width_ratios=[1, 1, 1, 1.0], height_ratios=[1, 1], wspace=0.25, hspace=0.28)

    ax_top = fig.add_subplot(gs[0, 0:2])
    ax_front = fig.add_subplot(gs[0, 2])
    ax_side = fig.add_subplot(gs[1, 0:2])
    ax_iso = fig.add_subplot(gs[1, 2])
    ax_meta = fig.add_subplot(gs[:, 3])

    for ax in (ax_top, ax_front, ax_side, ax_iso):
        style(ax)

    top_view(ax_top, body_l, body_w, leg_reach)
    front_view(ax_front, body_w, stance_h, leg_span)
    side_view(ax_side, body_l, stance_h, femur_len, tibia_stroke)

    ax_iso.set_title("Concept Iso")
    ax_iso.plot([-20, 40, 90, 30, -20], [20, 50, 20, -10, 20], color="#7fd3ff", lw=2)
    ax_iso.plot([40, 40], [50, 95], color="#7fd3ff", lw=2)
    ax_iso.plot([90, 90], [20, 65], color="#7fd3ff", lw=2)
    ax_iso.plot([30, 30], [-10, 35], color="#7fd3ff", lw=2)
    ax_iso.add_patch(patches.Circle((60, 35), radius=10, fill=False, ec="#ff6b6b", ls="--", lw=1.2))
    ax_iso.set_aspect("equal")
    ax_iso.set_xlim(-40, 120)
    ax_iso.set_ylim(-30, 120)

    meta_panel(ax_meta, receipt, p)

    fig.suptitle("Lunar Weevil — Blueprint v0.5 (Updated Baseline)", color="white", fontsize=16)
    OUTDIR.mkdir(parents=True, exist_ok=True)
    out = OUTDIR / "lunar_weevil_blueprint_v0_5.png"
    fig.savefig(out, dpi=260, facecolor=fig.get_facecolor(), bbox_inches="tight")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
