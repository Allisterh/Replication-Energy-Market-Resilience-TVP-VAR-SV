RESILIENCE FIGURE DESIGN COMPARISON
=================================

1. PURPOSE
----------
ee_resilience_designs.py generates six alternative figure designs from the
existing resilience workbook. It is a separate plotting workflow. The TVP-VAR,
resilience calculation, Markov notebook, and original R scripts are unchanged.

The six design families produce twelve individual figures. Each is exported as
a vector PDF, an SVG with editable text, and a 300-dpi PNG. All files are written
to the existing project-root Fig/ directory with a design_ filename prefix.

Every individual figure includes the specific event names and exact start/end
months on the same page. Event definitions and source membership follow the
original R plotting code. Single-source figures include 9 GPR, 8 CPU, or 8 OPU
events; combined-source figures include all 21 distinct events. No separate
event document is needed to identify the displayed windows.

2. RUN
------
Requirements: Python 3.9 or newer, numpy, pandas, openpyxl, matplotlib, Pillow.

From the project root:

  python3 "Energy Economics Code/python code/ee_resilience_designs.py"

The default project root is resolved from the script location. An explicit root
can be supplied with --project-root. Use --dpi to change the PNG resolution;
the vector PDF and SVG exports are unaffected by PNG resolution.

Arial is used for the sans-serif designs. Design A uses Times New Roman.
DejaVu Sans/Serif provide fallbacks if these fonts are unavailable. Text is kept
editable in SVG and fonts are embedded as TrueType in PDF where available.

3. INPUTS AND SAMPLE
-------------------
  Energy Economics Code/matlab code/resilience_metrics.xlsx
    Columns: t, Variable, RP, RD. The exported RP column is plotted as RI.

  Energy Economics Data/VAR_100data.xlsx, worksheet VAR_100data
    The existing date column supplies the full 167-month TVP-VAR calendar.
    Observations 2-167 supply February 2010-November 2023, the 166-month sample
    corresponding to resilience indices t = 2,...,167.

Market order: OIL, NG, COAL, ERIX, EUA.
Shock-to-series mapping:
  GPR: Var6-Var10
  CPU: Var14-Var18
  OPU: Var22-Var26

Every curve shows all 166 original monthly observations, sorted by t. There is
no smoothing, interpolation, rescaling, aggregation, or re-estimation. No
confidence interval is drawn because none is supplied for these metric series.

4. DESIGNS (ROWS x COLUMNS)
--------------------------
A. Classic 5 x 2, three files (GPR, CPU, OPU)
   Five market rows, with RI and RD in two columns. Serif typography, thin
   navy/clay lines, market labels shown once, and years on the bottom row.
   Pale event windows are paired with a shared event-name/date key below.
   Intended for readable, separate main-text figures at approximately 184 mm
   width. The event key extends the native 184 x 203 mm data canvas vertically.

B. Horizontal 2 x 5, three files (GPR, CPU, OPU)
   Five market columns; RI in the first row and RD in the second. Arial,
   subdued horizontal reference lines, shared metric scales, and pale event
   windows. The event-name/date key extends the 184 x 91 mm data canvas below.
   A compact option when page height is limited.

C. All-shock matrix 5 x 6, one file
   Five market rows and three paired RI/RD column groups for GPR, CPU and OPU.
   Sources use a consistent navy/teal/ochre palette. The shared event key below
   the 274 x 194 mm data canvas gives all names, monthly ranges, and GPR/CPU/OPU
   membership. Suitable for a large landscape page or a large supplement.
   Reducing this entire 30-panel figure to 184 mm width makes text small.

D. Shock overlay 2 x 5, one file
   Each market/metric panel contains all three sources, distinguished by both
   color and line style. One shared line legend. The event key extends the
   184 x 91 mm data canvas. Background shading uses the light union of relevant
   windows. Useful for direct source comparisons; crossings can be dense.

E. Grayscale matrix 6 x 5, one file
   Five market columns and three source blocks, each with an RI/RD row pair.
   Monochrome lines, shared scales, and source-specific event windows. A named
   event key is included below the 184 x 220 mm data canvas. Suitable for
   print-oriented comparisons without a three-color line legend.

F. Event context 5 x 2, three files (GPR, CPU, OPU)
   Thin lines, pale event windows, and a shared event timeline beneath the
   grid. Full event names and monthly ranges are labelled directly on that
   timeline. Label widths are measured and allocated to separate lanes so
   nearby events do not collide. Shifted labels retain a leader to the actual
   event interval. Original dates and source membership are preserved. OPU
   uses the E20 label OPEC+ cuts; CPU excludes E16, matching the revised appendix.
   The full named timeline fits within a native 184 x 234 mm canvas.

All event labels use 7-point or larger text. Designs A-E extend the canvas to
include their shared key without shrinking the data panels or typography.
Design F reserves more of its original canvas for the directly named timeline.
Actual dimensions are recorded in design_resilience_manifest.json.

The default axis limits are common across all shocks and markets within each
metric: RI = 0.2-0.9 and RD = 1.0-4.5 for the supplied workbook. Limits are
derived from the global data range and rounded outward, not estimated from
individual panels. This prevents apparent differences caused by separate
market-specific scales. Tick density varies with panel size.

RI is the existing relative absorption measure. RD is the existing weighted
response timing measure within the fixed GIRF horizon; it is not Markov state
duration or an exact number of months to complete recovery. All plotted values
and the original one-based RD weighting are preserved.

5. START HERE
-------------
  Fig/design_resilience_comparison_with_events.pdf
    Fourteen pages: design guide, all twelve individual figures, event key.
    The previous design_resilience_comparison.pdf filename is kept in sync.

  Fig/design_resilience_gallery.png
  Fig/design_resilience_gallery.pdf
    Six-family overview. A, B and F thumbnails use GPR; their CPU and OPU
    versions are supplied separately.

  Fig/design_[A-F]_*.pdf / .svg / .png
    Individual figures, ready for detailed comparison or later refinement.

  Fig/design_resilience_manifest.json
    Input SHA-256 hashes, date range, shared limits, native output dimensions,
   series counts, and named-event counts. Source workbooks are checked again
   after plotting.

6. VALIDATION AND DESIGN BASIS
-----------------------------
The script checks the full 167-month calendar, every selected series' t indices,
finite values, and equality between every plotted y array and its source array.
The 12 figures contain 180 plotted series in total (30 distinct underlying
series, each used in six design families). Source workbooks are read only.

Each layout uses a white background, restrained line weights, consistent fonts,
minimal framing, and shared scale logic. Every layout retains specific event
names and monthly windows in its shared key. G/C/O membership tags are defined
in the key of combined-source figures. Event shading is contextual and does
not establish causal effects. Design F places the specific event names directly
on a shared timeline; the other designs use shared keys with explicit dates.

Publisher artwork guidance consulted for fonts, vector output and final sizing:
https://www.elsevier.com/about/policies-and-standards/author/artwork-and-media-instructions/artwork-overview
https://www.elsevier.com/en-au/about/policies-and-standards/author/artwork-and-media-instructions/artwork-sizing

These are alternative visual designs for review; a journal's final page width
and figure grouping should be confirmed when selecting the submission version.

7. FIVE-MARKET OVERLAY: TWO ROWS AND THREE COLUMNS (DESIGN G)
-----------------------------------------------------------
Run the independent additional script from the project root:

  python3 "Energy Economics Code/python code/ee_resilience_overlay_2x3.py"

The six data panels have RI in the top row and RD in the bottom row. Columns
are GPR, CPU and OPU. Every panel contains the five original market curves,
using one shared market-color and line-style legend above the figure.

Each column has its own event-label strip immediately below RD. RI, RD and the
event strip use exactly the same physical left edge, width and date limits.
Continuous pale windows span the whole column. Event bars use the unchanged
start/end dates. Labels are anchored at their actual event midpoints, with
vertical leaders; labels are only stacked vertically. Near a boundary, left or
right text alignment changes without moving the horizontal date anchor.
The renderer verifies that event boundaries project to identical pixel x
coordinates in all three axes and that event labels do not overlap.

To keep this version compact, the event strip prints the specific event names.
The full monthly ranges are retained in design_G_market_overlay_2x3_events.csv.
They are also expressed by the unchanged widths and positions of the windows.
No separate event key is needed to identify the named events on the figure.

Two sizes are supplied, both with legible native-size fonts:
  wide: approximately 279 mm wide, for a large review or landscape figure.
  journal: approximately 184 mm wide, for a compact two-column comparison.
Height is determined by the number of event-label lanes needed. Exact sizes
are recorded in the G manifest. Small native-size text should not be reduced
further when selecting a final page width.

Outputs in the project-root Fig/ directory:
  design_G_market_overlay_2x3_wide.pdf / .svg / .png
  design_G_market_overlay_2x3_journal.pdf / .svg / .png
  design_G_market_overlay_2x3_comparison.pdf  (two pages)
  design_G_market_overlay_2x3_manifest.json
  design_G_market_overlay_2x3_events.csv

Each version contains 30 unchanged series of 166 monthly observations. This
script checks the input hashes and every plotted y array using the same
read-only data-loading functions as the six earlier figure designs.

REVISED CPU EVENT LIST (main_J1104.tex / Supplementary_Appendix.tex)
The active CPU figure uses eight windows: EU ETS backloading/Phase III,
COP21/Paris Agreement, U.S. Paris exit announcement, European Green Deal,
Fit for 55/Glasgow Pact, REPowerEU, IRA, and MSR/EU ETS reform. E16 is absent;
remaining IDs and monthly boundaries are retained. Event windows provide
historical context and are not imposed as estimated break dates.
