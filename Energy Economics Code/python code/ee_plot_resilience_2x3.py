"""Selected wide resilience figure: two rows, three uncertainty columns.

Top row: RI. Bottom row: RD. Each panel contains five energy-market series.
Event names, interval bars and pale windows share each column's date geometry.

Requirements: numpy, pandas, matplotlib, openpyxl.
Run: python3 ee_plot_resilience_2x3.py
Optional: --project-root /path/to/project --dpi 300 --angle 45 --compare-angles

The script reads existing estimates and writes the selected wide figure to Fig/.
"""

from pathlib import Path
import argparse
import hashlib
import json
import math
import os
import shutil
import tempfile

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "ee_resilience_mpl"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.font_manager import FontProperties
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from matplotlib.ticker import FormatStrFormatter
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.text import Text
import numpy as np
import pandas as pd

# Keep vector text editable and embed standard TrueType fonts in PDFs.
plt.rcParams.update({
    "font.family": "sans-serif", "font.sans-serif": ["Arial", "DejaVu Sans"],
    "svg.fonttype": "none", "pdf.fonttype": 42, "ps.fonttype": 42,
    "font.size": 16, "axes.spines.right": False, "axes.spines.top": False,
    "axes.linewidth": 2.5, "legend.frameon": False,
})


MARKETS = ("OIL", "NG", "COAL", "ERIX", "EUA")


SHOCKS = ("GPR", "CPU", "OPU")


METRICS = ("RI", "RD")


VAR_MAP = dict(zip(SHOCKS, (range(6, 11), range(14, 19), range(22, 27))))


MARKET_COLORS = {
    "OIL": "#24557B", "NG": "#BC6145", "COAL": "#A38732",
    "ERIX": "#27836E", "EUA": "#805B87",
}


MARKET_STYLES = {
    "OIL": "-", "NG": "-", "COAL": (0, (4, 1.5)),
    "ERIX": (0, (5, 1.4, 1.1, 1.4)), "EUA": (0, (1.2, 1.3)),
}


# Selected wide design. All dimensions below are in inches or points.
CONFIG = dict(width=11.0, panel_height=1.65, gap=0.32, fontsize=8.2,
              event_fontsize=7.0, event_angle=45, top=0.55,
              event_gap=0.24, event_bar_pad=0.06, event_text_gap=0.04,
              event_bottom_pad=0.08, bottom=0.10, legend_fontsize=7.8)
EVENT_BOX = dict(boxstyle="square,pad=0.10", facecolor="white",
                 edgecolor="none", alpha=0.93)
OUTPUT_STEM = "resilience_markets_2x3_wide"
X_MIN = mdates.date2num(pd.Timestamp("2009-12-01"))
X_MAX = mdates.date2num(pd.Timestamp("2024-01-01"))


# Event windows follow Supplementary_Appendix.tex, Table tab:event_windows_ext.
# E16 was removed from the revised CPU list; remaining IDs are kept stable.
EVENTS = [
    ("E01", "GPR_OPU", "2011-02-01", "2011-10-01", "Arab Spring and Libya"),
    ("E02", "GPR", "2012-01-01", "2012-07-01", "Iran sanctions"),
    ("E03", "GPR", "2014-02-01", "2015-02-01", "Crimea crisis"),
    ("E04", "CPU", "2012-11-01", "2013-09-01", "EU ETS backloading / Phase III"),
    ("E05", "OPU", "2014-11-01", "2016-02-01", "Oil price collapse"),
    ("E06", "CPU", "2015-11-01", "2016-01-01", "COP21 / Paris Agreement"),
    ("E07", "OPU", "2016-01-01", "2017-03-01", "OPEC+ cooperation"),
    ("E08", "GPR", "2017-01-01", "2017-12-01", "Middle East tensions"),
    ("E09", "CPU", "2017-06-01", "2017-12-01", "U.S. Paris exit announcement"),
    ("E10", "GPR_OPU", "2019-09-01", "2019-10-01", "Saudi attacks"),
    ("E11", "CPU", "2019-12-01", "2020-03-01", "European Green Deal"),
    ("E12", "GPR", "2020-01-01", "2020-02-01", "U.S.-Iran confrontation"),
    ("E13", "OPU", "2020-03-01", "2020-06-01", "COVID-19 oil crash"),
    ("E14", "CPU", "2021-07-01", "2021-12-01", "Fit for 55 / Glasgow Pact"),
    ("E15", "GPR", "2021-09-01", "2022-03-01", "European gas crisis"),
    ("E17", "GPR_OPU", "2022-02-01", "2022-12-01", "Russia-Ukraine war"),
    ("E18", "CPU", "2022-03-01", "2022-11-01", "REPowerEU"),
    ("E19", "CPU", "2022-08-01", "2023-04-01", "IRA"),
    ("E20", "OPU", "2023-04-01", "2023-11-01", "OPEC+ cuts and Mideast"),
    ("E21", "CPU", "2023-02-01", "2023-06-01", "MSR / EU ETS reform"),
    ("E22", "GPR_OPU", "2023-10-01", "2023-11-01", "Israel-Palestine"),
]


def find_project_root(explicit=None):
    """Find the folder containing both replication package directories."""
    if explicit is not None:
        root = Path(explicit).expanduser().resolve()
        if not all((root / name).is_dir() for name in ("Energy Economics Code", "Energy Economics Data")):
            raise FileNotFoundError("--project-root must contain Energy Economics Code and Energy Economics Data.")
        return root
    starts = [Path(__file__).resolve().parent, Path.cwd().resolve()]
    for start in starts:
        for candidate in (start, *start.parents):
            if all((candidate / name).is_dir() for name in ("Energy Economics Code", "Energy Economics Data")):
                return candidate
    raise FileNotFoundError("Project root not found. Supply --project-root or keep this script inside the package.")


def load_data(root):
    resilience_file = root / "Energy Economics Code/matlab code/resilience_metrics.xlsx"
    calendar_file = root / "Energy Economics Data/VAR_100data.xlsx"
    frame = pd.read_excel(resilience_file)
    calendar = pd.to_datetime(pd.read_excel(calendar_file, sheet_name="VAR_100data")["date"], utc=True)
    dates = pd.DatetimeIndex(calendar).tz_convert(None)
    expected = pd.date_range("2010-01-01", "2023-11-01", freq="MS")
    if not dates.equals(expected):
        raise ValueError("The VAR workbook must contain the 167 monthly dates, Jan 2010-Nov 2023.")
    dates = dates[1:]
    series = {}
    for shock in SHOCKS:
        for market, code in zip(MARKETS, VAR_MAP[shock]):
            block = frame.loc[frame["Variable"] == f"Var{code}"].sort_values("t")
            if not np.array_equal(block["t"].to_numpy(), np.arange(2, 168)):
                raise ValueError(f"Invalid or incomplete time indices for {shock}/{market}.")
            for metric, column in (("RI", "RP"), ("RD", "RD")):
                values = block[column].to_numpy(dtype=float)
                if not np.isfinite(values).all():
                    raise ValueError(f"Non-finite observations for {shock}/{market}/{metric}.")
                series[(shock, market, metric)] = values
    limits = {}
    for metric, scale in (("RI", 10), ("RD", 2)):
        values = np.concatenate([y for key, y in series.items() if key[2] == metric])
        limits[metric] = (math.floor(values.min() * scale) / scale,
                          math.ceil(values.max() * scale) / scale)
    sources = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
               for p in (resilience_file, calendar_file)}
    return dates, series, limits, sources


def compact_style(serif=False):
    plt.rcParams.update({
        "font.family": "serif" if serif else "sans-serif",
        "font.serif": ["Times New Roman", "DejaVu Serif"],
        "font.size": 8, "axes.labelsize": 8, "axes.titlesize": 9,
        "xtick.labelsize": 7.2, "ytick.labelsize": 7.2,
        "axes.linewidth": 0.55, "axes.edgecolor": "#555A60",
        "text.color": "#23272B", "xtick.color": "#454A50", "ytick.color": "#454A50",
        "axes.titleweight": "normal", "figure.facecolor": "white", "axes.facecolor": "white",
    })


def draw_series(ax, dates, series, shock, market, metric, color, lw=0.85, ls="-"):
    values = series[(shock, market, metric)]
    line, = ax.plot(dates, values, color=color, linewidth=lw, linestyle=ls,
                    solid_capstyle="round", solid_joinstyle="round", zorder=3)
    if not np.array_equal(np.asarray(line.get_ydata()), values):
        raise AssertionError("A plotted series differs from its workbook values.")
    line.set_gid(f"{shock}_{market}_{metric}_166_original_observations")
    return line


def events_for(shock):
    return [event for event in EVENTS if shock in event[1]]


def text_polygon(text):
    """Return the rendered, rotated square text-box polygon in display pixels."""
    patch = text.get_bbox_patch()
    vertices = patch.get_path().transformed(patch.get_transform()).vertices
    return vertices[:-1] if np.allclose(vertices[0], vertices[-1]) else vertices


def polygons_overlap(first, second):
    """Separating-axis test for convex rotated text boxes."""
    for polygon in (first, second):
        for edge in np.roll(polygon, -1, axis=0) - polygon:
            if np.linalg.norm(edge) < 1e-10:
                continue
            normal = np.array([-edge[1], edge[0]])
            a, b = first @ normal, second @ normal
            if a.max() <= b.min() + 1e-8 or b.max() <= a.min() + 1e-8:
                return False
    return True


def place_events(fig, panel_width, left, right, settings, angle):
    """Measure angled names, then move collisions down without changing dates."""
    font = FontProperties(family=plt.rcParams["font.family"], size=settings["event_fontsize"])
    probes, events = {}, {}
    for shock in SHOCKS:
        events[shock] = sorted(events_for(shock), key=lambda event: event[2])
        for event in events[shock]:
            name = "OPEC+ cuts" if event[0] == "E20" and shock == "OPU" else event[4]
            for align in ("right", "center", "left"):
                probes[(shock, event[0], align)] = fig.text(
                    0, 0, name, fontproperties=font, ha=align, va="top",
                    rotation=angle, rotation_mode="anchor", color="none",
                    bbox={**EVENT_BOX, "facecolor": "none"})
    fig.canvas.draw()
    relative = {key: text_polygon(probe).copy() for key, probe in probes.items()}
    for probe in probes.values():
        probe.remove()

    packed, occupied, max_depth = {}, [], 0.0
    for col, shock in enumerate(SHOCKS):
        x = left + col * (panel_width + settings["gap"])
        allowed_left = (0.04 if col == 0 else x - settings["gap"] / 2 + 0.02) * fig.dpi
        allowed_right = (settings["width"] - 0.04 if col == 2
                         else x + panel_width + settings["gap"] / 2 - 0.02) * fig.dpi
        packed[shock] = []
        for event in events[shock]:
            start, end = mdates.date2num(pd.Timestamp(event[2])), mdates.date2num(pd.Timestamp(event[3]))
            anchor = (start + end) / 2
            anchor_x = (x + (anchor - X_MIN) / (X_MAX - X_MIN) * panel_width) * fig.dpi
            choices = []
            for align in ("right", "center", "left"):
                polygon = relative[(shock, event[0], align)]
                x_min, x_max = polygon[:, 0].min() + anchor_x, polygon[:, 0].max() + anchor_x
                overflow = max(0, allowed_left - x_min) + max(0, x_max - allowed_right)
                choices.append((overflow, align, polygon))
            overflow, align, polygon = min(choices, key=lambda choice: choice[0])
            if overflow > 0.5:
                raise ValueError(f"Event name is too wide for this angle: {shock}/{event[0]}")
            shift_y = -settings["event_text_gap"] * fig.dpi - polygon[:, 1].max()
            candidate = polygon + np.array([anchor_x, shift_y])
            step = fig.dpi / 144  # half a point; only the vertical position changes.
            for _ in range(1200):
                if not any(polygons_overlap(candidate, previous) for previous in occupied):
                    break
                shift_y -= step
                candidate[:, 1] -= step
            else:
                raise ValueError("Unable to separate event names at the chosen angle.")
            occupied.append(candidate)
            max_depth = max(max_depth, -candidate[:, 1].min() / fig.dpi)
            name = "OPEC+ cuts" if event[0] == "E20" and shock == "OPU" else event[4]
            packed[shock].append(dict(event=event, start=start, end=end, anchor=anchor,
                                      label=name, align=align, text_y=shift_y / fig.dpi))
    return packed, max_depth


def build_figure(dates, series, limits, angle=None):
    settings = CONFIG
    angle = settings["event_angle"] if angle is None else float(angle)
    compact_style()
    plt.rcParams.update({"font.size": settings["fontsize"],
                         "xtick.labelsize": settings["fontsize"],
                         "ytick.labelsize": settings["fontsize"]})
    width = settings["width"]
    left, right = (0.56, 0.16)
    panel_width = (width - left - right - 2 * settings["gap"]) / 3
    fig = plt.figure(figsize=(width, 7))
    packed, max_depth = place_events(fig, panel_width, left, right, settings, angle)
    label_height = settings["event_bar_pad"] + max_depth + settings["event_bottom_pad"]
    bottom, event_gap, row_gap = settings["bottom"], settings["event_gap"], 0.27
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
            years = (2010, 2014, 2018, 2023)
            ax.set_xticks([mdates.date2num(pd.Timestamp(f"{year}-01-01")) for year in years])
            ax.set_xticklabels([str(year) for year in years])
            ax.tick_params(axis="both", length=2.6, width=0.5, pad=3,
                           labelbottom=row == 1, labelleft=True)
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.grid(axis="y", color="#DDE2E6", linewidth=0.45, zorder=0)
            for market in MARKETS:
                draw_series(ax, dates, series, shock, market, metric, MARKET_COLORS[market],
                            lw=1.05, ls=MARKET_STYLES[market])
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
        for placement in packed[shock]:
            start, end, anchor = placement["start"], placement["end"], placement["anchor"]
            # A figure-level window spans the entire column, including the event
            # strip. All x positions come from the same date-to-figure transform.
            shade_x = x / width + (start - X_MIN) / (X_MAX - X_MIN) * panel_width / width
            shade_width = (end - start) / (X_MAX - X_MIN) * panel_width / width
            fig.add_artist(Rectangle((shade_x, bottom / height), shade_width,
                                     (ri_bottom + settings["panel_height"] - bottom) / height,
                                     transform=fig.transFigure, facecolor="#C9D0D6", alpha=0.20,
                                     linewidth=0, zorder=-3))
            bar_y = label_height - settings["event_bar_pad"]
            text_y = bar_y + placement["text_y"]
            timeline.plot([anchor, anchor], [bar_y, text_y], color="#9FAAB3", lw=0.45, zorder=1)
            timeline.plot([start, end], [bar_y, bar_y], color="#8796A2", lw=2.8,
                          solid_capstyle="butt", zorder=2)
            label = timeline.text(anchor, text_y, placement["label"],
                                  ha=placement["align"], va="top", fontsize=settings["event_fontsize"],
                                  rotation=angle, rotation_mode="anchor", color="#303C46", zorder=3,
                                  bbox=EVENT_BOX)
            label.set_gid(f"{shock}_{placement['event'][0]}_date_aligned_label")

    handles = [Line2D([], [], color=MARKET_COLORS[m], ls=MARKET_STYLES[m], lw=1.3) for m in MARKETS]
    for shock in SHOCKS:
        legend = axes[(shock, "RI")].legend(
            handles, MARKETS, loc="lower center", ncol=5, bbox_to_anchor=(0.5, 0.06),
            borderaxespad=0, fontsize=settings["legend_fontsize"], handlelength=1.9,
            handletextpad=0.4, columnspacing=0.9, frameon=False)
        legend.set_gid(f"{shock}_RI_market_legend")
    fig._ee_data_axes = axes
    fig._ee_event_axes = event_axes
    fig._ee_event_placements = packed
    fig._ee_event_angle = angle
    fig._ee_event_height = label_height
    return fig


def validate_alignment(fig):
    """Check both physical date alignment and visible event text placement."""
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    all_event_labels = []
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
        all_event_labels.extend(labels)
        for label, placement in zip(labels, fig._ee_event_placements[shock]):
            if abs(label.get_position()[0] - placement["anchor"]) > 1e-10:
                raise AssertionError("An event label was moved to a different date.")
    for i, label in enumerate(all_event_labels):
        for other in all_event_labels[i + 1:]:
            if polygons_overlap(text_polygon(label), text_polygon(other)):
                raise AssertionError("Rotated event names overlap.")
    width, height = fig.canvas.get_width_height()
    for text in fig.findobj(Text):
        if text.get_visible() and text.get_text():
            bounds = text.get_window_extent(renderer)
            if bounds.x0 < -1 or bounds.y0 < -1 or bounds.x1 > width + 1 or bounds.y1 > height + 1:
                raise AssertionError(f"Text lies outside the figure: {text.get_text()}")
    for shock in SHOCKS:
        ax = fig._ee_data_axes[(shock, "RI")]
        legend = ax.get_legend().get_window_extent(renderer)
        for line in ax.lines:
            x = mdates.date2num(pd.to_datetime(line.get_xdata()))
            points = ax.transData.transform(np.column_stack([x, line.get_ydata()]))
            if any(legend.contains(*point) for point in points):
                raise AssertionError(f"The {shock}-RI legend obscures a market curve.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=None)
    parser.add_argument("--dpi", type=int, default=300)
    parser.add_argument("--angle", type=float, default=CONFIG["event_angle"])
    parser.add_argument("--compare-angles", action="store_true",
                        help="Also export 30-, 45- and 60-degree variants and a comparison PDF.")
    args = parser.parse_args()
    if args.dpi <= 0:
        parser.error("--dpi must be positive.")
    if not 0 < args.angle < 90:
        parser.error("--angle must be between 0 and 90 degrees.")
    root = find_project_root(args.project_root)
    dates, series, limits, source_hashes = load_data(root)
    out = root / "Fig"
    out.mkdir(exist_ok=True)

    angles = sorted(set([30.0, 45.0, 60.0, args.angle])) if args.compare_angles else [args.angle]
    comparison = PdfPages(out / "resilience_markets_2x3_event_angles.pdf") if args.compare_angles else None
    variants = []
    try:
        for angle in angles:
            fig = build_figure(dates, series, limits, angle)
            validate_alignment(fig)
            stem = f"{OUTPUT_STEM}_angle_{angle:g}" if args.compare_angles else OUTPUT_STEM
            title = f"Energy-market resilience: RI and RD; event names at {angle:g} degrees"
            fig.savefig(out / f"{stem}.svg")
            fig.savefig(out / f"{stem}.pdf", metadata={"Title": title})
            fig.savefig(out / f"{stem}.png", dpi=args.dpi)
            dimensions = dict(angle_degrees=angle,
                              native_size_mm=[round(float(value) * 25.4, 1) for value in fig.get_size_inches()],
                              event_strip_height_mm=round(fig._ee_event_height * 25.4, 1))
            variants.append(dimensions)
            if angle == args.angle:
                selected = dimensions
                if args.compare_angles:
                    for extension in ("svg", "pdf", "png"):
                        shutil.copyfile(out / f"{stem}.{extension}", out / f"{OUTPUT_STEM}.{extension}")
            if comparison is not None:
                fig.text(0.992, 0.992, f"{angle:g}\N{DEGREE SIGN}", ha="right", va="top",
                         fontsize=8, color="#555A60")
                comparison.savefig(fig)
            plt.close(fig)
    finally:
        if comparison is not None:
            comparison.close()

    event_rows = []
    for shock in SHOCKS:
        for event in events_for(shock):
            name = "OPEC+ cuts" if event[0] == "E20" and shock == "OPU" else event[4]
            event_rows.append(dict(shock=shock, event_id=event[0], event=name,
                                   start=event[2], end=event[3]))
    pd.DataFrame(event_rows).to_csv(out / f"{OUTPUT_STEM}_events.csv", index=False)

    final_hashes = {p: hashlib.sha256((root / p).read_bytes()).hexdigest() for p in source_hashes}
    if source_hashes != final_hashes:
        raise RuntimeError("An input workbook changed while the figure was being generated.")
    manifest = dict(input_sha256=source_hashes, rows=list(METRICS), columns=list(SHOCKS),
                    markets=list(MARKETS), period=[str(dates[0].date()), str(dates[-1].date())],
                    series=30, observations_per_series=166, smoothing=False,
                    **selected, event_fontsize_pt=CONFIG["event_fontsize"],
                    legend_position="inside each RI panel, lower center, one row per uncertainty source",
                    y_tick_labels="all six panels", y_axis_titles="leftmost panel in each row",
                    angle_comparison=variants,
                    event_x_coordinates_shared_with_curves=True)
    (out / f"{OUTPUT_STEM}_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Project root: {root}")
    for variant in variants:
        print(f"Event angle {variant['angle_degrees']:g} degrees: "
              f"figure {variant['native_size_mm']} mm; event strip {variant['event_strip_height_mm']} mm")
    print(f"Saved PDF, SVG, PNG, event CSV and manifest to {out / OUTPUT_STEM}")


if __name__ == "__main__":
    main()
