SELECTED WIDE RESILIENCE FIGURE: COMPLETE INDEPENDENT CODE
========================================================

1. SCRIPT AND REQUIREMENTS
--------------------------
ee_plot_resilience_2x3.py is the complete independent script for the selected
wide figure. It includes all event definitions, file loading, market mappings,
styling, label placement, alignment checks, and export code. It does not import
the earlier design-comparison scripts.

Requirements: Python 3.9 or newer, numpy, pandas, matplotlib, openpyxl.
Install missing packages once if needed:

  python3 -m pip install numpy pandas matplotlib openpyxl

2. RUN
------
From the project root:

  python3 "Energy Economics Code/python code/ee_plot_resilience_2x3.py"

The root is located by searching upward from the saved script and then the
current working directory. The root must contain Energy Economics Code and
Energy Economics Data. The script can therefore run from r code/, python code/,
the project root, or another working directory when saved inside the package.

To run a copied script from elsewhere, supply the project root explicitly:

  python3 ee_plot_resilience_2x3.py --project-root "/path/to/Replication-Energy-Market-Resilience"

Optional --dpi changes only PNG resolution; the default is 300.

Event names use a 45-degree angle by default. To choose another angle:

  python3 "Energy Economics Code/python code/ee_plot_resilience_2x3.py" --angle 30

To export all three design alternatives (30, 45 and 60 degrees) and a
three-page comparison PDF, keeping 45 degrees as the selected main figure:

  python3 "Energy Economics Code/python code/ee_plot_resilience_2x3.py" --compare-angles

--angle accepts values strictly between 0 and 90 degrees. Combining it with
--compare-angles also includes that angle if it differs from 30, 45 and 60.

3. INPUTS
---------
  Energy Economics Code/matlab code/resilience_metrics.xlsx
    Columns: t, Variable, RP, RD. RP is plotted as RI.

  Energy Economics Data/VAR_100data.xlsx, sheet VAR_100data
    The existing date column contains 167 months, January 2010-November 2023.
    Observations 2-167 provide the 166 plotted months, February 2010-November
    2023, matching t = 2,...,167 in the resilience workbook.

Every selected series must contain those 166 indices and finite RI/RD values.
All curves retain the existing values. No model is estimated and no smoothing,
standardization, aggregation, or interpolation of missing data is applied.

Market order: OIL, NG, COAL, ERIX, EUA.
Variable mappings:
  GPR: Var6, Var7, Var8, Var9, Var10
  CPU: Var14, Var15, Var16, Var17, Var18
  OPU: Var22, Var23, Var24, Var25, Var26

4. LAYOUT AND PARAMETERS
------------------------
Rows: RI above, RD below.
Columns: GPR, CPU, OPU.
Each of the six data panels contains the five markets. Each RI panel has its
own market legend, placed in one row inside its lower blank area. Colors and
line patterns stay fixed across panels. All six panels show numerical y-axis
tick labels. The RI and RD axis titles appear once each, at the left of their
respective rows. Scales stay identical across uncertainty columns.

CONFIG near the top of the script controls the selected design:
  width = 11.0              Overall width in inches (279.4 mm).
  panel_height = 1.65       Height of each data panel in inches.
  gap = 0.32                Space between uncertainty columns in inches.
  fontsize = 8.2            Main plot and tick-label size in points.
  event_fontsize = 7.0      Event-name size in points.
  event_angle = 45          Default event-name rotation in degrees.
  top = 0.55                Top clearance in inches.
  event_gap = 0.24          Gap from RD to the event strip in inches.
  event_bar_pad = 0.06      Clearance above the event bars in inches.
  event_text_gap = 0.04     Gap from an event bar to its name in inches.
  event_bottom_pad = 0.08  Clearance below the deepest event name in inches.
  bottom = 0.10            Bottom margin in inches.
  legend_fontsize = 7.8    Per-RI market-legend size in points.

Height adjusts to the actual rendered extent of the rotated event names.
With the supplied inputs and installed Arial font, the alternatives are:

  Angle       Figure width x height       Event-strip height
  30 degrees  279.4 x 137.8 mm             24.5 mm
  45 degrees  279.4 x 144.7 mm             31.4 mm (selected)
  60 degrees  279.4 x 149.7 mm             36.4 mm

The 45-degree version balances readability and compactness in the densely
spaced late-sample events. Event names stay on one line at 7 points, and the
original physical data-panel dimensions are retained. Arial is preferred;
DejaVu Sans is the fallback. Font substitution can change the required height.

MARKET_COLORS and MARKET_STYLES contain the five market colors and line patterns.
Data-line width is 1.05 points. Limits are common across all markets and sources
within each metric, rounded outward from the actual data range. The supplied
data give RI = 0.2-0.9 and RD = 1.0-4.5. Each data panel uses identical dates.

5. EVENT ALIGNMENT
-------------------
EVENTS contains the 21 retained event IDs, source memberships, start/end dates,
and names. The GPR, CPU and OPU columns use 9, 8 and 8 events respectively.
CPU excludes E16, following the revised appendix. OPU labels E20 as OPEC+ cuts.

Every uncertainty column has a date-aligned event strip beneath RD. Its left
edge, width and date limits equal those of RI and RD. Pale interval windows
span the whole column, including both data panels and the event strip.

Event bars keep their exact original boundaries. Each event name is anchored
at its actual interval midpoint. The script measures the rendered rotated text
boxes and moves names vertically only when they would collide. All columns
are checked together, including the spaces between columns. At the left/right
edge, text alignment changes without changing the date anchor.
The short vertical leaders and bars connect names to the shaded intervals.
The plot displays names only to avoid repeatedly printing dates; exact monthly
boundaries are retained in the exported event CSV.

validate_alignment() verifies identical pixel x positions for every event
boundary in RI, RD and the event strip. It also checks label overlaps and
confirms that no event anchor has moved horizontally. It checks that visible
text remains inside the canvas and that each inset legend covers no RI curve
observations in its own uncertainty column.

6. OUTPUTS
----------
All outputs go to the project-root Fig/ directory, created if needed:

  resilience_markets_2x3_wide.pdf             Vector figure with embedded fonts.
  resilience_markets_2x3_wide.svg             Vector figure with editable text.
  resilience_markets_2x3_wide.png             300-dpi preview by default.
  resilience_markets_2x3_wide_events.csv      Event names and exact boundaries.
  resilience_markets_2x3_wide_manifest.json   Input hashes and figure settings.

With --compare-angles, the script additionally writes:

  resilience_markets_2x3_wide_angle_30.pdf/.svg/.png
  resilience_markets_2x3_wide_angle_45.pdf/.svg/.png
  resilience_markets_2x3_wide_angle_60.pdf/.svg/.png
  resilience_markets_2x3_event_angles.pdf    One page per angle, in angle order.

The selected angle is also saved under the usual main basename above. The
comparison pages identify their angle in the upper-right corner; individual
figure files omit this comparison-only label.

OUTPUT_STEM controls the shared output basename. Running again replaces these
same-named outputs. Input workbooks are read only and their SHA-256 hashes are
checked again after export.

7. VERIFICATION
---------------
The independent script was run against the existing package. Each figure
contains 30 unchanged series of 166 monthly observations. The six data panels
retain their original physical dimensions. All applicable event names are
retained, with exact date alignment and non-overlapping labels checked.
The selected PDF was rendered for visual inspection after export.
No TVP-VAR, resilience, Markov, or statistical-test calculation was rerun.

REVISED CPU EVENT LIST (main_J1104.tex / Supplementary_Appendix.tex)
The active CPU figure uses eight windows: EU ETS backloading/Phase III,
COP21/Paris Agreement, U.S. Paris exit announcement, European Green Deal,
Fit for 55/Glasgow Pact, REPowerEU, IRA, and MSR/EU ETS reform. E16 is absent;
remaining IDs and monthly boundaries are retained. Event windows provide
historical context and are not imposed as estimated break dates.
