#!/usr/bin/env python3
"""Generate v0.6 blueprint comparing compact vs scaled full-cleat variants."""

from __future__ import annotations

from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import yaml

ROOT = Path(__file__).resolve().parents[1]
PRESETS = ROOT / "configs" / "rover_geometry_variants_2026-02-22.yaml"
OUTDIR = ROOT / "results" / "blueprints"


def style(ax):
    ax.set_facecolor("#0b1e39")
    ax.tick_params(colors="white", labelsize=7)
    for s in ax.spines.values():
        s.set_color("white")
    ax.grid(True, color="#4a6a8a", linestyle=":", linewidth=0.5)


def draw_top(ax, title, body_l, body_w, xs, foot_r):
    ax.set_title(title, color="white", fontsize=10)
    ax.add_patch(patches.Rectangle((-body_l / 2, -body_w / 2), body_l, body_w, fill=False, ec="#7fd3ff", lw=2))
    for side in (-1, 1):
        y = side * body_w / 2
        for x in xs:
            ax.add_patch(patches.Circle((x, y), radius=foot_r, fill=False, ec="#ff6b6b", lw=1.2, ls="--"))
            ax.plot([x, x], [y, y + side * 14], color="#7fd3ff", lw=1.2)

    min_pitch = min(abs(xs[i] - xs[i + 1]) for i in range(len(xs) - 1))
    clr = min_pitch - 2 * foot_r
    ax.text(0.02, 0.98, f"pitch={min_pitch:.1f} mm\n2R={2*foot_r:.1f} mm\nclearance={clr:.1f} mm", transform=ax.transAxes,
            va="top", ha="left", color="#d9ecff", fontsize=8)

    ax.set_aspect("equal")
    ax.set_xlim(-260, 260)
    ax.set_ylim(-180, 180)


def draw_tradeoff(ax, compact, scaled):
    ax.axis("off")
    ax.set_title("Variant Tradeoffs", color="white", fontsize=11)

    lines = [
        "Compact auto-clamped:",
        f"- Footprint: {compact['body_length_mm']:.0f} x {compact['body_width_mm']:.0f} mm",
        f"- Foot radius used: {compact['expected_foot_radius_used_mm']:.1f} mm (from 80 mm request)",
        f"- Same-side clearance: {compact['expected_clearance_pitch_minus_2r_mm']:.1f} mm",
        "- Better packaging and transport density",
        "",
        "Scaled full-cleat:",
        f"- Footprint: {scaled['body_length_mm']:.0f} x {scaled['body_width_mm']:.0f} mm",
        f"- Foot radius used: {scaled['expected_foot_radius_used_mm']:.1f} mm (full cleat intent)",
        f"- Same-side clearance: {scaled['expected_clearance_pitch_minus_2r_mm']:.1f} mm",
        "- Better cleat fidelity and stance stability margin",
        "",
        "Recommended default: SCALED_FULL_CLEAT",
    ]

    y = 0.95
    for line in lines:
        ax.text(0.02, y, line, transform=ax.transAxes, color="#d9ecff", fontsize=9, va="top")
        y -= 0.06


def main() -> int:
    cfg = yaml.safe_load(PRESETS.read_text(encoding="utf-8"))
    compact = cfg["variants"]["compact_auto_clamped"]
    scaled = cfg["variants"]["scaled_full_cleat"]

    fig = plt.figure(figsize=(14, 7), facecolor="#0b1e39")
    gs = fig.add_gridspec(1, 3, width_ratios=[1, 1, 1.1], wspace=0.25)
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])
    ax3 = fig.add_subplot(gs[0, 2])

    for ax in (ax1, ax2):
        style(ax)

    draw_top(ax1, "Compact Auto-Clamped", compact["body_length_mm"], compact["body_width_mm"],
             compact["side_leg_x_positions_mm"], compact["expected_foot_radius_used_mm"])
    draw_top(ax2, "Scaled Full-Cleat", scaled["body_length_mm"], scaled["body_width_mm"],
             scaled["side_leg_x_positions_mm"], scaled["expected_foot_radius_used_mm"])
    draw_tradeoff(ax3, compact, scaled)

    fig.suptitle("Lunar Weevil Blueprint v0.6 — Cleat-Overlap Resolution (2026-02-22)", color="white", fontsize=15)
    OUTDIR.mkdir(parents=True, exist_ok=True)
    out = OUTDIR / "lunar_weevil_blueprint_v0_6_variants_2026-02-22.png"
    fig.savefig(out, dpi=260, facecolor=fig.get_facecolor(), bbox_inches="tight")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
