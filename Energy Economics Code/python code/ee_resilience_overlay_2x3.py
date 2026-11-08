"""Plot five markets together in a two-row, three-source resilience figure.

Rows are RI and RD; columns are GPR, CPU and OPU. An event strip shares the
exact x geometry of each column. This file reads existing estimates only.
"""

from pathlib import Path
import argparse
import hashlib
import json
import textwrap

from ee_resilience_designs import (
    MARKETS, SHOCKS, METRICS, compact_style, draw_series, events_for, load_data,
)
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.font_manager import FontProperties
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from matplotlib.ticker import FormatStrFormatter
import numpy as np
import pandas as pd

MARKET_COLORS = {
    "OIL": "#24557B", "NG": "#BC6145", "COAL": "#A38732",
    "ERIX": "#27836E", "EUA": "#805B87",
}
MARKET_STYLES = {
    "OIL": "-", "NG": "-", "COAL": (0, (4, 1.5)),
    "ERIX": (0, (5, 1.4, 1.1, 1.4)), "EUA": (0, (1.2, 1.3)),
}
PROFILES = {
    "wide": dict(width=11.0, panel_height=1.65, gap=0.32, fontsize=8.2,
                 event_fontsize=8.0, wrap=17, row_height=0.36, top=0.83),
    "journal": dict(width=7.25, panel_height=1.5, gap=0.23, fontsize=7.4,
                    event_fontsize=7.0, wrap=15, row_height=0.32, top=0.77),
}
X_MIN, X_MAX = mdates.date2num(pd.Timestamp("2009-12-01")), mdates.date2num(pd.Timestamp("2024-01-01"))


def place_events(shock, panel_width, renderer, dpi, settings):
    """Pack labels vertically while fixing every horizontal anchor at its date."""
    font = FontProperties(family="Arial", size=settings["event_fontsize"])
    ends = []
    placed = []
    for event in sorted(events_for(shock), key=lambda e: e[2]):
        name = "OPEC+ cuts" if event[0] == "E20" and shock == "OPU" else event[4]
        label = textwrap.fill(name, width=settings["wrap"], break_long_words=False)
        width_px = max(renderer.get_text_width_height_descent(line, font, False)[0]
                       for line in label.splitlines())
        width_days = width_px / (panel_width * dpi) * (X_MAX - X_MIN)
        start, end = mdates.date2num(pd.Timestamp(event[2])), mdates.date2num(pd.Timestamp(event[3]))
        anchor = (start + end) / 2
        # Text alignment changes at the boundaries; the event anchor never moves.
        if anchor - width_days / 2 < X_MIN:
            align, left, right = "left", anchor, anchor + width_days
        elif anchor + width_days / 2 > X_MAX:
            align, left, right = "right", anchor - width_days, anchor
        else:
            align, left, right = "center", anchor - width_days / 2, anchor + width_days / 2
        padding = 24
        lane = next((i for i, previous in enumerate(ends) if left - padding > previous), len(ends))
        if lane == len(ends):
            ends.append(right + padding)
        else:
            ends[lane] = right + padding
        placed.append(dict(event=event, start=start, end=end, anchor=anchor,
                           label=label, align=align, lane=lane))
    return placed, len(ends)


def build_figure(profile, dates, series, limits):
    settings = PROFILES[profile]
    compact_style()
    plt.rcParams.update({"font.size": settings["fontsize"],
                         "xtick.labelsize": settings["fontsize"],
                         "ytick.labelsize": settings["fontsize"]})
    width = settings["width"]
    left, right = (0.56, 0.16) if profile == "wide" else (0.48, 0.10)
    panel_width = (width - left - right - 2 * settings["gap"]) / 3
    fig = plt.figure(figsize=(width, 7))
    renderer = fig.canvas.get_renderer()
    packed = {s: place_events(s, panel_width, renderer, fig.dpi, settings) for s in SHOCKS}
    max_lanes = max(n for _, n in packed.values())
    label_height = 0.16 + max_lanes * settings["row_height"]
    bottom, event_gap, row_gap = 0.12, 0.42, 0.27
    height = bottom + label_height + event_gap + 2 * settings["panel_height"] + row_gap + settings["top"]
    fig.set_size_inches(width, height)
    label_top = bottom + label_height
    rd_bottom = label_top + event_gap
    ri_bottom = rd_bottom + settings["panel_height"] + row_gap
    axes, event_axes = {}, {}

    for col, shock in enumerate(SHOCKS):
        x = left + col * (panel_width + settings["gap"])
        for row, metric in enumerate(METRICS):
            y = ri_bottom if row == 0 else rd_bottom
            ax = fig.add_axes([x / width, y / height, panel_width / width,
                               settings["panel_height"] / height])
            axes[(shock, metric)] = ax
            ax.set_facecolor("none")
            ax.set_xlim(X_MIN, X_MAX)
            ax.set_ylim(limits[metric])
            ax.set_yticks([0.3, 0.6, 0.9] if metric == "RI" else [1, 2, 3, 4])
            ax.yaxis.set_major_formatter(FormatStrFormatter("%.1f"))
            years = (2010, 2014, 2018, 2023) if profile == "wide" else (2011, 2017, 2023)
            ax.set_xticks([mdates.date2num(pd.Timestamp(f"{year}-01-01")) for year in years])
            ax.set_xticklabels([str(year) for year in years])
            ax.tick_params(axis="both", length=2.6, width=0.5, pad=3,
                           labelbottom=row == 1, labelleft=col == 0)
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.grid(axis="y", color="#DDE2E6", linewidth=0.45, zorder=0)
            for market in MARKETS:
                draw_series(ax, dates, series, shock, market, metric, MARKET_COLORS[market],
                            lw=1.05 if profile == "wide" else 0.85, ls=MARKET_STYLES[market])
            ax.text(0, 1.035, chr(ord("a") + row * 3 + col), transform=ax.transAxes,
                    fontsize=settings["fontsize"], fontweight="bold", va="bottom")
            if row == 0:
                ax.set_title(shock, pad=14, fontsize=settings["fontsize"] + 2.5,
                             fontweight="bold")
            if col == 0:
                ax.set_ylabel(metric, fontsize=settings["fontsize"] + 2,
                              fontweight="bold", labelpad=9)

        timeline = fig.add_axes([x / width, bottom / height, panel_width / width, label_height / height],
                                sharex=axes[(shock, "RD")])
        event_axes[shock] = timeline
        timeline.set_xlim(X_MIN, X_MAX)
        timeline.set_ylim(0, label_height)
        timeline.set_facecolor("none")
        timeline.set_axis_off()
        timeline.text(0, 1.025, "Events", transform=timeline.transAxes,
                      ha="left", fontsize=settings["fontsize"], color="#59636D", fontweight="bold")

        for placement in packed[shock][0]:
            start, end, anchor = placement["start"], placement["end"], placement["anchor"]
            # A figure-level window spans the entire column, including the event
            # strip. All x positions come from the same date-to-figure transform.
            shade_x = x / width + (start - X_MIN) / (X_MAX - X_MIN) * panel_width / width
            shade_width = (end - start) / (X_MAX - X_MIN) * panel_width / width
            fig.add_artist(Rectangle((shade_x, bottom / height), shade_width,
                                     (ri_bottom + settings["panel_height"] - bottom) / height,
                                     transform=fig.transFigure, facecolor="#C9D0D6", alpha=0.20,
                                     linewidth=0, zorder=-3))
            bar_y = label_height - 0.07 - placement["lane"] * settings["row_height"]
            timeline.plot([anchor, anchor], [label_height, bar_y], color="#9FAAB3", lw=0.45, zorder=1)
            timeline.plot([start, end], [bar_y, bar_y], color="#8796A2", lw=2.8,
                          solid_capstyle="butt", zorder=2)
            label = timeline.text(anchor, bar_y - 0.055, placement["label"],
                                  ha=placement["align"], va="top", fontsize=settings["event_fontsize"],
                                  linespacing=1.12, color="#303C46", zorder=3,
                                  bbox=dict(facecolor="white", edgecolor="none", alpha=0.93, pad=0.6))
            label.set_gid(f"{shock}_{placement['event'][0]}_date_aligned_label")

    handles = [Line2D([], [], color=MARKET_COLORS[m], ls=MARKET_STYLES[m], lw=1.3) for m in MARKETS]
    fig.legend(handles, MARKETS, loc="upper center", ncol=5, bbox_to_anchor=(0.54, 0.997),
               fontsize=settings["fontsize"] + 1, handlelength=2.7, columnspacing=2.0)
    fig._ee_data_axes = axes
    fig._ee_event_axes = event_axes
    fig._ee_event_placements = packed
    return fig


def validate_alignment(fig):
    """Check both physical date alignment and visible event text placement."""
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    for shock in SHOCKS:
        ri, rd = fig._ee_data_axes[(shock, "RI")], fig._ee_data_axes[(shock, "RD")]
        timeline = fig._ee_event_axes[shock]
        for event in events_for(shock):
            points = mdates.date2num(pd.to_datetime([event[2], event[3]]))
            for x in points:
                projected = [ax.transData.transform((x, ax.get_ylim()[0]))[0] for ax in (ri, rd, timeline)]
                if not np.allclose(projected, projected[0], atol=1e-8):
                    raise AssertionError(f"Event and curve dates do not align: {shock}/{event[0]}")
        labels = [t for t in timeline.texts if (t.get_gid() or "").endswith("_date_aligned_label")]
        for i, label in enumerate(labels):
            for other in labels[i + 1:]:
                if label.get_window_extent(renderer).overlaps(other.get_window_extent(renderer)):
                    raise AssertionError(f"Event labels overlap: {shock}")
        for label, placement in zip(labels, fig._ee_event_placements[shock][0]):
            if abs(label.get_position()[0] - placement["anchor"]) > 1e-10:
                raise AssertionError("An event label was moved to a different date.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    root = args.project_root.resolve()
    out = root / "Fig"
    out.mkdir(exist_ok=True)
    dates, series, limits, source_hashes = load_data(root)
    records = []
    with PdfPages(out / "design_G_market_overlay_2x3_comparison.pdf") as booklet:
        for profile in PROFILES:
            fig = build_figure(profile, dates, series, limits)
            validate_alignment(fig)
            name = f"design_G_market_overlay_2x3_{profile}"
            fig.savefig(out / f"{name}.svg")
            fig.savefig(out / f"{name}.pdf", metadata={"Title": f"Five-market resilience comparison - {profile}"})
            fig.savefig(out / f"{name}.png", dpi=300)
            booklet.savefig(fig)
            records.append(dict(profile=profile, basename=name,
                                width_mm=round(fig.get_figwidth() * 25.4, 1),
                                height_mm=round(fig.get_figheight() * 25.4, 1),
                                event_lanes={s: n for s, (_, n) in fig._ee_event_placements.items()}))
            plt.close(fig)
            print("Saved", name, flush=True)
    assert source_hashes == {p: hashlib.sha256((root / p).read_bytes()).hexdigest() for p in source_hashes}
    (out / "design_G_market_overlay_2x3_manifest.json").write_text(json.dumps({
        "input_sha256": source_hashes, "rows": list(METRICS), "columns": list(SHOCKS),
        "markets": list(MARKETS), "series_per_figure": 30, "nobs_per_series": 166,
        "event_x_coordinates_shared_with_curves": True, "outputs": records,
    }, indent=2) + "\n")
    event_rows = []
    for shock in SHOCKS:
        for event in events_for(shock):
            name = "OPEC+ cuts" if event[0] == "E20" and shock == "OPU" else event[4]
            event_rows.append(dict(shock=shock, event_id=event[0], event=name,
                                   start=event[2], end=event[3]))
    pd.DataFrame(event_rows).to_csv(out / "design_G_market_overlay_2x3_events.csv", index=False)


if __name__ == "__main__":
    main()
