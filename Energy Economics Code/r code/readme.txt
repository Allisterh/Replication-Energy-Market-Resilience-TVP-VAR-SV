ENERGY ECONOMICS R CODE
======================

1. SCRIPTS
----------
ee_descriptive_statistics.r produces the variable-summary LaTeX table and the
resilience summaries, correlations, and monthly ranking counts.
ee_plot_for_resilience.r contains four complete plotting blocks.

All PDF figures are saved to <project root>/Fig/. Each plotting block includes
its own setup and can be run separately.

2. SOFTWARE
-----------
Descriptive statistics: readxl, tseries, e1071.
Plots: ggplot2, grid, readxl, sysfonts, showtext.
grid is included with R. Install the other packages once if needed:

  install.packages(c("readxl", "tseries", "e1071", "ggplot2", "sysfonts", "showtext"))

The font settings use these macOS files:
  /System/Library/Fonts/Supplemental/Times New Roman.ttf
  /System/Library/Fonts/Supplemental/Times New Roman Bold.ttf
  /System/Library/Fonts/Supplemental/Times New Roman Italic.ttf
  /System/Library/Fonts/Supplemental/Times New Roman Bold Italic.ttf

All four blocks use Times New Roman when the configured font files are
available and otherwise use a sans-serif fallback. Configure the font paths
within each block to use another installed font.

3. PROJECT ROOT AND RUNNING ORDER
--------------------------------
Keep Energy Economics Code and Energy Economics Data under the same parent.
Both scripts and each complete plotting block locate that parent by searching
upward from PROJECT_DIR, if supplied, and then the current R working directory.
The root must contain both package folders. Starting R in r code/ or another
package subdirectory is supported. A valid explicit PROJECT_DIR takes priority;
a supplied subdirectory is resolved to its root.

After changing PROJECT_DIR or moving the package, rerun the path-setup section
before reading data; this rebuilds RESILIENCE_FILE and the other path variables.
All remaining paths are built relative to the resolved root.

The variable-summary block can run before MATLAB estimation. The resilience
summaries and baseline plots require matlab code/resilience_metrics.xlsx.
The Markov plot additionally requires the exports from python code/Markov.ipynb.

To run the full descriptive script, start from the parent of the two folders:

  PROJECT_DIR <- normalizePath(getwd())
  source(file.path(PROJECT_DIR, "Energy Economics Code", "r code",
                   "ee_descriptive_statistics.r"))

If R starts in Energy Economics Code/r code/, the equivalent command is:

  source("ee_descriptive_statistics.r")

The script sets PROJECT_DIR to the package root. The baseline and
horizon-comparison plotting blocks each read the date column directly from
Energy Economics Data/VAR_100data.xlsx, sheet VAR_100data. This column already
contains the full TVP-VAR calendar: January 2010-November 2023 (167 months).
Each block validates that 167 nonmissing dates were read, then sets:

  x_date <- sample_dates[2:167]

These 166 dates cover February 2010-November 2023 and match the resilience
indices t = 2,...,167 and the Markov sample. The first month is excluded because
the model uses one VAR lag. Preserve the workbook's chronological order.

Run the Required packages section before selecting a complete plotting block
in RStudio. Sourcing the whole plotting file executes all four blocks and
requires every input, including the bundled horizon-comparison workbooks.
The helper functions are defined inside their respective blocks.

4. DESCRIPTIVE STATISTICS
-------------------------
Part A reads:
  Energy Economics Data/VAR_100data.xlsx
  Energy Economics Data/markov_100data_167.csv

Both cover January 2010-November 2023 (167 observations). The workbook supplies
percentage energy returns and uncertainty-index levels. The CSV supplies four
transformed, unstandardized macrofinancial series. The files are joined by date
while preserving workbook order and the supplied values.
The VAR reader also accepts CSV input. VAR_data.csv is the reference
copy with decimal energy returns, one hundredth of the workbook's energy values.

The three table panels are:
  Energy markets: OIL, NG, COAL, ERIX, EUA.
  Uncertainty indicators: GPR, CPU, OPU.
  Macrofinancial conditioning variables: GSCPI, DXY, CPI, Industrial.

Mean, median, minimum, maximum, and sample SD use their usual definitions.
Skewness and excess kurtosis use e1071 type = 3 (normal excess kurtosis = 0).
ADF uses tseries::adf.test(x, alternative = "stationary") and its default lag
rule. A reported lower-bound p-value of 0.01 receives three stars; p-values
below 0.05 and 0.10 receive two stars and one star, respectively.

The table is printed and saved to:
  Energy Economics Code/r code/variable_summary_statistics.tex
It requires the LaTeX packages float, booktabs, and threeparttable. Unrounded
results are available in variable_descriptive_statistics. The table displays
two decimal places and ADF significance stars.

Part B reads:
  Energy Economics Code/matlab code/resilience_metrics.xlsx

Expected columns: t, Variable, RP, RD. RP is resilience intensity (RI); RD is
resilience duration. The baseline contains 166 observations per series, from
February 2010 to November 2023. The R script reads these measures directly.
It produces RI/RD matrices, Pearson correlations with pairwise complete
observations, Mean/SD/Min/Max tables, individual ranking tables, and wide ranking
tables. RI ranks higher values first; RD ranks lower values first. Ranking
uses complete monthly observations and selects the first market in a tie.

RUN_IMPULSE_DIAGNOSTIC defaults to FALSE. Set it to TRUE to preview a single
GIRF path from matlab code/tvpvar_imp.xlsx.

The separate Python conditioning input is:
  Energy Economics Data/markov_scale_data_166.csv
It uses rows 2:167 of the 167-row macrofinancial file, standardized using the
166-period sample and sample SD (denominator n-1).

5. PLOTTING BLOCKS AND OUTPUTS
------------------------------
Block 1. Three-panel resilience schematic (6.2 x 12.2 inches).
  Output: r_plot_resilience_abc_vertical.pdf (main-article filename).
  The identical r_plot_resilience_abc_vertical_re.pdf is retained as an alias.
  Folder: <PROJECT_DIR>/Fig/.

Block 2. GPR/CPU/OPU baseline figures (each 12 x 16 inches, 6 x 2 layout).
  Input: <PROJECT_DIR>/Energy Economics Code/matlab code/resilience_metrics.xlsx
  Outputs:
    gpr_resilience_6x2_academic_fine_labels.pdf
    cpu_resilience_6x2_academic_fine_labels.pdf
    opu_resilience_6x2_academic_fine_labels.pdf
  Folder: <PROJECT_DIR>/Fig/.
  Rows 1-5 contain the five markets; row 6 contains event labels.

Block 3. Horizon comparison (12 x 16 inches, five market rows plus legend).
  Inputs: resilience_metrics_median6.xlsx, resilience_metrics_median.xlsx,
          resilience_metrics_median10.xlsx (H = 6, 8, and 10).
  Input folder: <PROJECT_DIR>/Energy Economics Data/horizon_resilience/
  Default output: gpr_resilience_H_comparison_academic_no_shades.pdf
  Folder: <PROJECT_DIR>/Fig/.
  Set TARGET_SHOCK to GPR, CPU, or OPU; it selects both the data
  mapping and the output filename. Run this block for all three selections
  to reproduce the three appendix horizon-comparison figures.

Block 4. Markov probabilities and resilience (12 x 16 inches, 5 x 2 plus legend).
  Input folder: <PROJECT_DIR>/Energy Economics Code/python code/output/
  Input: <shock>_ms_state_probabilities_state<state>.xlsx
  Default output: opu_ms_smoothed_probability_5x2_state1_prob_left_metric_right.pdf
  Output folder: <PROJECT_DIR>/Fig/.
  Required sheets: probabilities_long and state_mapping.
  Plotting columns: date, market, measure, metric_value, prob_selected.
  Measures are RI/RD; markets are OIL, NG, COAL, ERIX, EUA. The left axis shows
  probability and the right axis shows the resilience metric.

The default Markov settings are SHOCK_LABEL = "OPU" and STATE_TO_PLOT = 1.
Set both consistently with the Python export filename. For state 2, also update
the legend wording to identify State 2.
Running a block again replaces its PDFs at the same configured paths.

6. BASELINE FIGURE CONTROLS
---------------------------
TARGET_SHOCKS <- c("GPR", "CPU", "OPU") generates the three figures in that
order. Select a subset to draw fewer figures. Call the generator with:

  plot_vertical_resilience(
    target_shock = "GPR", r_data = r_data, x_date = x_date,
    target_dir = RESILIENCE_OUTPUT_DIR)

It returns the path invisibly. vertical_output_files retains the named paths.
MARKET_VAR_MAPS stores the mappings in OIL/NG/COAL/ERIX/EUA order:
  GPR: Var6,  Var7,  Var8,  Var9,  Var10
  CPU: Var14, Var15, Var16, Var17, Var18
  OPU: Var22, Var23, Var24, Var25, Var26

EVENT_LABEL_ADJUSTMENTS contains event_id, measure, x_shift_months, and y_pos.
"both" changes RI and RD together; "RI"/"RD" changes one column. Negative
x_shift_months moves a label left; positive values move it right. Larger y_pos
moves it upward. Rows apply in order, with later rows overriding earlier ones.
Append an override before the generation loop, for example:

  EVENT_LABEL_ADJUSTMENTS$GPR <- rbind(
    EVENT_LABEL_ADJUSTMENTS$GPR,
    data.frame(event_id = "E22", measure = "RD", x_shift_months = -2.2,
               y_pos = 0.12, stringsAsFactors = FALSE))

set_event_label_pos() within the generator also supports srt, cex, adj_x, adj_y,
col_text, and label controls. Further manual calls belong after the adjustment
loop and before plotting. Each shock uses common RI and RD axis ranges
across markets.

The eight CPU event windows are EU ETS backloading/Phase III, COP21/Paris
Agreement, U.S. Paris exit announcement, European Green Deal, Fit for 55/
Glasgow Pact, REPowerEU, IRA, and MSR/EU ETS reform. Full event descriptions
and dates are in Supplementary_Appendix.tex.

CPU label settings:
  CEX_EVENT:       1.75
  event_id:        E04, E06, E09, E11, E14, E18, E19, E21
  x_shift_months: -12, -12, -14, -26, -18, -10, -4, -9
  y_pos:          .75, .75, .25, .75, .25, .75, .50, .20

OPU uses the short label "OPEC+ cuts" for E20.
