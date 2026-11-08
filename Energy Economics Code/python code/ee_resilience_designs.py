"""Compare six publication figure designs using the supplied resilience data.

Run this file directly. All PDF, editable SVG, and PNG outputs go to Fig/.
The script reads existing workbooks and does not estimate any model.
"""

from pathlib import Path
import argparse
import hashlib
import json
import math
import os
import tempfile
import textwrap

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "ee_resilience_mpl"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.lines import Line2D
from matplotlib.font_manager import FontProperties
import matplotlib.dates as mdates
from matplotlib.ticker import FormatStrFormatter
import numpy as np
import pandas as pd
from PIL import Image, ImageOps

# Editable vector text and standard journal fonts; compact panels override sizes.
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
METRIC_COLORS = {"RI": "#254F72", "RD": "#946754"}
SHOCK_COLORS = {"GPR": "#254F72", "CPU": "#25877E", "OPU": "#B17E50"}
SHOCK_STYLES = {"GPR": "-", "CPU": (0, (4, 1.6)), "OPU": (0, (1.2, 1.2))}
METRIC_NAMES = {"RI": "Resilience intensity (RI)", "RD": "Resilience duration (RD)"}
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
DESIGNS = {
    "A": ("Classic 5 x 2", "Serif market grid; event windows and names on the same page."),
    "B": ("Horizontal 2 x 5", "Compact market columns; shared event-name and date key."),
    "C": ("All-shock matrix 5 x 6", "Three RI/RD column pairs; named events with source membership."),
    "D": ("Shock overlay 2 x 5", "Three sources per panel; event names and monthly ranges below."),
    "E": ("Grayscale matrix 6 x 5", "Print-oriented source/metric rows with a named event key."),
    "F": ("Event context 5 x 2", "Event shading and a timeline labelled with full event names and dates."),
}


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


def style_axis(ax, metric, limits, bottom=False, labels=True, dense=False, grid=False):
    ax.set_xlim(pd.Timestamp("2009-12-01"), pd.Timestamp("2024-01-01"))
    years = [2011, 2017, 2023] if dense else [2010, 2014, 2018, 2023]
    ax.set_xticks([pd.Timestamp(f"{year}-01-01") for year in years])
    ax.set_xticklabels([str(year) for year in years])
    ax.set_ylim(limits[metric])
    ticks = [0.3, 0.6, 0.9] if metric == "RI" else [1, 2.5, 4]
    ax.set_yticks(ticks)
    ax.yaxis.set_major_formatter(FormatStrFormatter("%.1f"))
    ax.tick_params(axis="both", direction="out", length=2.4, width=0.5, pad=2.4)
    ax.tick_params(axis="x", labelbottom=bottom)
    ax.tick_params(axis="y", labelleft=labels)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    if grid:
        ax.grid(axis="y", color="#E6E8EA", linewidth=0.45, zorder=0)
    ax.set_axisbelow(True)


def draw_series(ax, dates, series, shock, market, metric, color, lw=0.85, ls="-"):
    values = series[(shock, market, metric)]
    line, = ax.plot(dates, values, color=color, linewidth=lw, linestyle=ls,
                    solid_capstyle="round", solid_joinstyle="round", zorder=3)
    if not np.array_equal(np.asarray(line.get_ydata()), values):
        raise AssertionError("A plotted series differs from its workbook values.")
    line.set_gid(f"{shock}_{market}_{metric}_166_original_observations")
    return line


def panel_letter(ax, index):
    ax.text(0, 1.025, chr(ord("a") + index), transform=ax.transAxes,
            ha="left", va="bottom", fontsize=7.5, fontweight="bold")


def events_for(shock):
    return [event for event in EVENTS if shock in event[1]]


def add_named_event_context(fig, shock, already_shaded=False):
    """Put event names and exact monthly ranges on each individual figure."""
    sources = (shock,) if shock else SHOCKS
    relevant = {e[0]: e for source in sources for e in events_for(source)}
    events = sorted(relevant.values(), key=lambda e: (e[2], e[0]))
    if already_shaded:
        # Design F already names the events directly on its timeline.
        fig._ee_event_ids = [e[0] for e in events]
        fig._ee_named_event_count = len(events)
        return fig

    # Each panel uses only the events belonging to the source(s) it displays.
    # Overlay panels use a very light union of windows to keep their lines clear.
    if not already_shaded:
        for ax in fig.axes:
            panel_sources = set()
            for line in ax.lines:
                gid = line.get_gid() or ""
                if gid.endswith("_166_original_observations"):
                    panel_sources.add(gid.split("_", 1)[0])
            panel_events = {e[0]: e for source in panel_sources for e in events_for(source)}
            for event in panel_events.values():
                ax.axvspan(pd.Timestamp(event[2]), pd.Timestamp(event[3]),
                           color="#D8DCDF", alpha=0.11 if len(panel_sources) > 1 else 0.23,
                           linewidth=0, zorder=0)

    # Increase the canvas instead of reducing the data panels or their font sizes.
    columns = 3 if shock else 4
    rows = math.ceil(len(events) / columns)
    row_height = 0.34
    footer_height = 0.46 + rows * row_height
    width, height = fig.get_size_inches()
    new_height = height + footer_height
    positions = [(ax, ax.get_position().frozen()) for ax in fig.axes]
    figure_text = [(text, text.get_position()) for text in fig.texts]
    figure_lines = [(line, np.asarray(line.get_ydata(), dtype=float))
                    for line in fig.artists if isinstance(line, Line2D)]
    fig.set_size_inches(width, new_height)
    for ax, box in positions:
        ax.set_position([box.x0, (box.y0 * height + footer_height) / new_height,
                         box.width, box.height * height / new_height])
    for text, (x, y) in figure_text:
        text.set_position((x, (y * height + footer_height) / new_height))
    for line, y in figure_lines:
        line.set_ydata((y * height + footer_height) / new_height)

    left, right = 0.055, 0.985
    title_y = (footer_height - 0.07) / new_height
    title = "Events and monthly windows"
    if not shock:
        title += "  |  G = GPR; C = CPU; O = OPU"
    fig.text(left, title_y, title, fontsize=7.5, fontweight="bold", va="top")
    fig.add_artist(Line2D([left, right], [title_y + 0.045 / new_height] * 2,
                         transform=fig.transFigure, color="#AEB5BB", linewidth=0.5))
    for i, event in enumerate(events):
        row, col = divmod(i, columns)
        x = left + col * (right - left) / columns
        y = (footer_height - 0.31 - row * row_height) / new_height
        name = "OPEC+ cuts" if event[0] == "E20" and "OPU" in sources else event[4]
        memberships = "/".join(source[0] if source != "OPU" else "O"
                                for source in sources if event in events_for(source))
        dates = f"{event[2][:7]} to {event[3][:7]}"
        if not shock:
            dates += f"  [{memberships}]"
        fig.text(x, y, f"{event[0]}  {name}", fontsize=7.1, va="top", color="#29323A")
        fig.text(x, y - 0.14 / new_height, dates, fontsize=7.0,
                 va="top", color="#626D76")
    fig._ee_event_ids = [e[0] for e in events]
    fig._ee_named_event_count = len(events)
    return fig


def vertical_figure(shock, dates, series, limits, events=False):
    compact_style(serif=not events)
    fig, axes = plt.subplots(5, 2, figsize=(7.25, 9.2 if events else 8.0), squeeze=False)
    fig.subplots_adjust(left=0.115, right=0.98, top=0.925,
                        bottom=0.30 if events else 0.065, hspace=0.16, wspace=0.20)
    for row, market in enumerate(MARKETS):
        for col, metric in enumerate(METRICS):
            ax = axes[row, col]
            style_axis(ax, metric, limits, bottom=row == 4, grid=False)
            if events:
                for event in events_for(shock):
                    ax.axvspan(pd.Timestamp(event[2]), pd.Timestamp(event[3]),
                               color="#D8DCDF", alpha=0.32, linewidth=0, zorder=0)
            draw_series(ax, dates, series, shock, market, metric, METRIC_COLORS[metric], lw=0.95)
            panel_letter(ax, row * 2 + col)
            if row == 0:
                ax.set_title(METRIC_NAMES[metric], pad=12, fontsize=9.5)
        box = axes[row, 0].get_position()
        fig.text(0.028, (box.y0 + box.y1) / 2, market, rotation=90,
                 ha="center", va="center", fontsize=9, fontweight="bold")
    fig.text(0.115, 0.98, shock, ha="left", va="top", fontsize=10, fontweight="bold")
    if events:
        timeline = fig.add_axes([0.115, 0.035, 0.865, 0.21])
        timeline.set_xlim(axes[0, 0].get_xlim())
        renderer = fig.canvas.get_renderer()
        font = FontProperties(family=plt.rcParams["font.family"], size=7.0)
        x_min, x_max = timeline.get_xlim()
        pixel_width = timeline.get_window_extent(renderer).width
        lane_ends = []
        placements = []
        for event in sorted(events_for(shock), key=lambda x: x[2]):
            start, end = pd.Timestamp(event[2]), pd.Timestamp(event[3])
            name = "OPEC+ cuts" if event[0] == "E20" and shock == "OPU" else event[4]
            label = textwrap.fill(name, width=16, break_long_words=False) + "\n" + \
                f"{event[2][:7]} to {event[3][:7]}"
            width = max(renderer.get_text_width_height_descent(line, font, False)[0]
                        for line in label.splitlines())
            half_width = (width / pixel_width) * (x_max - x_min) / 2 + 25
            midpoint = (mdates.date2num(start) + mdates.date2num(end)) / 2
            label_center = np.clip(midpoint, x_min + half_width, x_max - half_width)
            label_left, label_right = label_center - half_width, label_center + half_width
            lane = next((i for i, previous_end in enumerate(lane_ends)
                         if label_left > previous_end), len(lane_ends))
            if lane == len(lane_ends):
                lane_ends.append(label_right)
            else:
                lane_ends[lane] = label_right
            placements.append((event, start, end, lane, midpoint, label_center, label))
        for event, start, end, lane, midpoint, label_center, label in placements:
            timeline.plot([start, end], [lane, lane], color="#ADB6BD", lw=3.6, solid_capstyle="butt")
            if abs(midpoint - label_center) > 25:
                timeline.plot([midpoint, label_center], [lane + 0.02, lane + 0.12],
                              color="#ADB6BD", lw=0.5)
            timeline.text(label_center, lane + 0.14, label, ha="center", va="bottom",
                          fontsize=7.0, linespacing=1.12, color="#34414A")
        timeline.set_ylim(-0.25, max(1, len(lane_ends)) + 0.35)
        timeline.set_xticks([pd.Timestamp(f"{y}-01-01") for y in (2010, 2014, 2018, 2023)])
        timeline.set_xticklabels(["2010", "2014", "2018", "2023"], fontsize=7)
        timeline.set_yticks([])
        timeline.tick_params(axis="x", length=2.3, width=0.5, pad=3)
        timeline.spines["left"].set_visible(False)
        timeline.set_title("Events and monthly windows", loc="left", fontsize=7.5, pad=8)
    return fig


def horizontal_figure(shock, dates, series, limits, overlay=False):
    compact_style()
    fig, axes = plt.subplots(2, 5, figsize=(7.25, 3.6), squeeze=False)
    fig.subplots_adjust(left=0.09, right=0.98, bottom=0.15, top=0.80, wspace=0.16, hspace=0.27)
    for row, metric in enumerate(METRICS):
        for col, market in enumerate(MARKETS):
            ax = axes[row, col]
            style_axis(ax, metric, limits, bottom=row == 1, labels=col == 0, dense=True, grid=True)
            if overlay:
                for source in SHOCKS:
                    draw_series(ax, dates, series, source, market, metric,
                                SHOCK_COLORS[source], lw=0.8, ls=SHOCK_STYLES[source])
            else:
                draw_series(ax, dates, series, shock, market, metric, METRIC_COLORS[metric], lw=0.9)
            panel_letter(ax, row * 5 + col)
            if row == 0:
                ax.set_title(market, pad=12, fontsize=9, fontweight="bold")
        box = axes[row, 0].get_position()
        fig.text(0.018, (box.y0 + box.y1) / 2, metric, rotation=90,
                 ha="center", va="center", fontsize=9, fontweight="bold")
    if overlay:
        handles = [Line2D([], [], color=SHOCK_COLORS[s], lw=1.1, ls=SHOCK_STYLES[s]) for s in SHOCKS]
        fig.legend(handles, SHOCKS, ncol=3, loc="upper center", bbox_to_anchor=(0.54, 0.995),
                   fontsize=8, handlelength=2.8, columnspacing=2.5)
    else:
        fig.text(0.09, 0.98, shock, ha="left", va="top", fontsize=10, fontweight="bold")
    return fig


def matrix_figure(dates, series, limits):
    compact_style()
    fig = plt.figure(figsize=(10.8, 7.65))
    grid = fig.add_gridspec(5, 8, width_ratios=[1, 1, 0.15, 1, 1, 0.15, 1, 1],
                            left=0.075, right=0.985, bottom=0.07, top=0.89, hspace=0.16, wspace=0.25)
    group_axes = {}
    for row, market in enumerate(MARKETS):
        for source_col, shock in enumerate(SHOCKS):
            for metric_col, metric in enumerate(METRICS):
                ax = fig.add_subplot(grid[row, source_col * 3 + metric_col])
                style_axis(ax, metric, limits, bottom=row == 4, dense=True, grid=True)
                draw_series(ax, dates, series, shock, market, metric, SHOCK_COLORS[shock], lw=0.8)
                if row == 0:
                    ax.set_title(metric, pad=8, fontsize=8)
                    group_axes[(shock, metric)] = ax
                if source_col == 0 and metric_col == 0:
                    box = ax.get_position()
                    fig.text(0.022, (box.y0 + box.y1) / 2, market,
                             ha="center", va="center", fontsize=9, fontweight="bold")
    for shock in SHOCKS:
        first, last = group_axes[(shock, "RI")].get_position(), group_axes[(shock, "RD")].get_position()
        fig.text((first.x0 + last.x1) / 2, 0.975, shock, fontsize=10, fontweight="bold",
                 color=SHOCK_COLORS[shock], ha="center", va="top")
        fig.add_artist(Line2D([first.x0, last.x1], [0.943, 0.943],
                             transform=fig.transFigure, lw=0.7, color=SHOCK_COLORS[shock]))
    return fig


def grayscale_figure(dates, series, limits):
    compact_style()
    fig = plt.figure(figsize=(7.25, 8.65))
    grid = fig.add_gridspec(8, 5, height_ratios=[1, 1, 0.20, 1, 1, 0.20, 1, 1],
                            left=0.135, right=0.985, top=0.94, bottom=0.065, hspace=0.23, wspace=0.18)
    for group, shock in enumerate(SHOCKS):
        pair = []
        for metric_row, metric in enumerate(METRICS):
            row = group * 3 + metric_row
            for col, market in enumerate(MARKETS):
                ax = fig.add_subplot(grid[row, col])
                style_axis(ax, metric, limits, bottom=group == 2 and metric_row == 1,
                           labels=col == 0, dense=True, grid=True)
                draw_series(ax, dates, series, shock, market, metric, "#33383D", lw=0.8)
                if group == 0 and metric_row == 0:
                    ax.set_title(market, pad=10, fontsize=8.5, fontweight="bold")
                if col == 0:
                    box = ax.get_position()
                    fig.text(0.063, (box.y0 + box.y1) / 2, metric,
                             ha="center", va="center", fontsize=8)
                    pair.append(box)
        fig.text(0.018, (pair[0].y1 + pair[1].y0) / 2, shock, rotation=90,
                 ha="center", va="center", fontsize=9, fontweight="bold")
    return fig


def cover_page(pdf):
    compact_style()
    fig = plt.figure(figsize=(8.0, 9.2))
    fig.text(0.08, 0.94, "Energy-market resilience", fontsize=20, fontweight="bold")
    fig.text(0.08, 0.90, "Six figure designs for comparison", fontsize=12, color="#555D65")
    y = 0.81
    for code, (title, description) in DESIGNS.items():
        fig.text(0.08, y, code, fontsize=12, fontweight="bold", color="#254F72")
        fig.text(0.135, y, title, fontsize=11, fontweight="bold")
        fig.text(0.135, y - 0.032, description, fontsize=9)
        y -= 0.093
    fig.text(0.08, 0.18, "Reading the figures", fontsize=10, fontweight="bold")
    fig.text(0.08, 0.145, "166 monthly observations: February 2010-November 2023.\n"
             "Original RI/RD values; common scales within each metric; no smoothing.\n"
             "Every figure includes event names and exact monthly windows on the same page.\n"
             "A, B and F include a separate figure for each uncertainty source.\n"
             "C is a wide landscape design; do not shrink its labels to single-column size.",
             fontsize=8.7, linespacing=1.65, va="top")
    pdf.savefig(fig)
    plt.close(fig)


def event_key_page(pdf, outdir):
    compact_style()
    fig = plt.figure(figsize=(8.3, 9.8))
    fig.text(0.07, 0.95, "Event-window reference", fontsize=15, fontweight="bold")
    fig.text(0.07, 0.91, "Definitions follow the existing R plotting script.", fontsize=9, color="#555D65")
    key_rows = [[e[0], e[2][:7], e[3][:7], e[4]] for e in EVENTS]
    ax = fig.add_axes([0.07, 0.16, 0.87, 0.70])
    ax.axis("off")
    table = ax.table(cellText=key_rows, colLabels=["ID", "From", "To", "Event"],
                     colWidths=[0.09, 0.15, 0.15, 0.61], cellLoc="left", loc="upper left", bbox=[0, 0, 1, 1])
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor("white")
        cell.set_facecolor("#F0F2F4" if row == 0 else "white")
        if row == 0:
            cell.set_text_props(weight="bold", ha="left")
    fig.text(0.07, 0.09, "CPU follows the revised eight-event appendix list; E16 is no longer used.\n"
             "Shaded windows are historical context and do not identify causal effects.", fontsize=8.3, linespacing=1.6)
    fig.savefig(outdir / "design_event_key.pdf")
    pdf.savefig(fig)
    plt.close(fig)
    lines = ["EVENT-WINDOW REFERENCE", "All figures now include their own event names and dates.",
             "Definitions follow ee_plot_for_resilience.r.", ""]
    lines.extend(f"{e[0]}  {e[2][:7]} to {e[3][:7]}  {e[4]}  [{e[1]}]" for e in EVENTS)
    lines.append("\nCPU: eight revised events, without E16. OPU: use 'OPEC+ cuts' for E20.")
    (outdir / "design_event_key.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def export_figure(fig, code, shock, basename, pdf, outdir, dpi, records):
    # The individual files contain only the figure; booklet labels are added later.
    metadata = {"Title": f"{DESIGNS[code][0]} - {shock or 'all uncertainty sources'}"}
    fig.savefig(outdir / f"{basename}.svg")
    fig.savefig(outdir / f"{basename}.pdf", metadata=metadata)
    fig.savefig(outdir / f"{basename}.png", dpi=dpi, facecolor="white")
    fig.text(0.99, 0.009, f"Design {code}  |  {shock or 'All sources'}", ha="right",
             va="bottom", fontsize=6, color="#737A80")
    pdf.savefig(fig)
    records.append({"design": code, "shock": shock or "all", "basename": basename,
                    "width_mm": round(fig.get_figwidth() * 25.4, 1),
                    "height_mm": round(fig.get_figheight() * 25.4, 1),
                    "n_series": 30 if code in "CDE" else 10,
                    "observations_per_series": 166, "smoothing": False,
                    "named_events_on_figure": fig._ee_named_event_count,
                    "event_ids": fig._ee_event_ids})
    plt.close(fig)


def gallery(outdir, records):
    compact_style()
    fig, axes = plt.subplots(3, 2, figsize=(12.8, 12.6))
    fig.subplots_adjust(left=0.035, right=0.98, bottom=0.025, top=0.90, wspace=0.08, hspace=0.17)
    for ax, code in zip(axes.flat, DESIGNS):
        item = next(r for r in records if r["design"] == code)
        with Image.open(outdir / f"{item['basename']}.png") as source:
            image = ImageOps.contain(source.convert("RGB"), (1400, 850), Image.Resampling.LANCZOS)
            canvas = Image.new("RGB", (1400, 850), "white")
            canvas.paste(image, ((1400 - image.width) // 2, (850 - image.height) // 2))
            ax.imshow(canvas)
        ax.axis("off")
        ax.set_title(f"{code}   {DESIGNS[code][0]}", loc="left", pad=10,
                     fontsize=12, fontweight="bold", color="#254F72")
    fig.text(0.035, 0.98, "Resilience figure designs", fontsize=20, fontweight="bold", va="top")
    fig.text(0.035, 0.951, "All designs include event names and dates. A, B and F previews use GPR.",
             fontsize=10, color="#5C646C", va="top")
    fig.savefig(outdir / "design_resilience_gallery.png", dpi=180)
    fig.savefig(outdir / "design_resilience_gallery.pdf")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--dpi", type=int, default=300)
    args = parser.parse_args()
    root = args.project_root.resolve()
    outdir = root / "Fig"
    outdir.mkdir(parents=True, exist_ok=True)
    dates, series, limits, source_hashes = load_data(root)
    records = []
    comparison_file = outdir / "design_resilience_comparison_with_events.pdf"
    with PdfPages(comparison_file) as pdf:
        cover_page(pdf)
        for code in DESIGNS:
            for shock in (SHOCKS if code in "ABF" else (None,)):
                if code in "AF":
                    fig = vertical_figure(shock, dates, series, limits, events=code == "F")
                elif code in "BD":
                    fig = horizontal_figure(shock, dates, series, limits, overlay=code == "D")
                elif code == "C":
                    fig = matrix_figure(dates, series, limits)
                else:
                    fig = grayscale_figure(dates, series, limits)
                add_named_event_context(fig, shock, already_shaded=code == "F")
                label = {"A": "classic_5x2", "B": "horizontal_2x5", "C": "all_shocks_5x6",
                         "D": "overlay_2x5", "E": "grayscale_6x5", "F": "event_context_5x2"}[code]
                basename = f"design_{code}_{label}" + (f"_{shock}" if shock else "")
                export_figure(fig, code, shock, basename, pdf, outdir, args.dpi, records)
                print(f"Saved {basename}", flush=True)
        event_key_page(pdf, outdir)
    (outdir / "design_resilience_comparison.pdf").write_bytes(comparison_file.read_bytes())
    gallery(outdir, records)
    final_hashes = {p: hashlib.sha256((root / p).read_bytes()).hexdigest() for p in source_hashes}
    if source_hashes != final_hashes:
        raise AssertionError("An input workbook changed during plotting.")
    manifest = {"period": [str(dates[0].date()), str(dates[-1].date())],
                "input_sha256": source_hashes, "y_limits": limits,
                "plotted_series_verified_against_input": sum(r["n_series"] for r in records),
                "outputs": records}
    (outdir / "design_resilience_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Completed {len(records)} figures, the comparison PDF, and the gallery in {outdir}")


if __name__ == "__main__":
    main()
