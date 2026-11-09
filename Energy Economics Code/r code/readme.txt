ENERGY ECONOMICS R CODE
======================

1. SCRIPTS
----------
ee_descriptive_statistics.r produces the variable-summary LaTeX table and the
resilience summaries, correlations, and monthly ranking counts.
ee_plot_for_resilience.r contains four complete plotting blocks.

The refactor reuses console headings, paired RI/RD panel calls, and column
headers; the duplicate schematic helpers share one implementation. Both
schematic helper names remain available. Repeated separator comments and
excessive line wrapping have been removed. Settings, formulas, validation
messages, console output order, and output filenames are retained. All PDF
figures now use <project root>/Fig/. The horizon-comparison inputs are bundled
in Energy Economics Data/horizon_resilience/ rather than a personal directory.
Each plotting block keeps its own setup and can still be run separately.

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

Block 1 requires all four fonts and stops if any are absent. Blocks 2-4 use
Times New Roman when available and otherwise use a sans-serif fallback.
Configure the font paths within each block for another computer.

3. PROJECT ROOT AND RUNNING ORDER
--------------------------------
Keep Energy Economics Code and Energy Economics Data under the same parent.
Both scripts and each complete plotting block locate that parent by searching
upward from PROJECT_DIR, if supplied, and then the current R working directory.
The root must contain both package folders. Starting R in r code/ or another
package subdirectory therefore works without changing the data paths. A valid
explicit PROJECT_DIR takes priority; a supplied subdirectory is resolved to its
root. If no root is found, the code stops with an explanatory error.

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
the model uses one VAR lag. No separate date workbook or pre-existing date
object is needed. Preserve the workbook's chronological order.

Run the Required packages section before selecting a complete plotting block
in RStudio. Sourcing the whole plotting file executes all four blocks and
requires every input, including the bundled horizon-comparison workbooks.
The helper functions are defined inside their respective blocks; no extra
helper file or new initialization step is required.

4. DESCRIPTIVE STATISTICS
-------------------------
Part A reads:
  Energy Economics Data/VAR_100data.xlsx
  Energy Economics Data/markov_100data_167.csv

Both cover January 2010-November 2023 (167 observations). The workbook supplies
percentage energy returns and uncertainty-index levels. The CSV supplies four
transformed, unstandardized macrofinancial series. The files are joined by date
while preserving workbook order. No extra scaling or standardization is applied.
The VAR reader also retains its CSV-input branch. VAR_data.csv is the reference
copy with decimal energy returns, one hundredth of the workbook's energy values.

The three table panels are:
  Energy markets: OIL, NG, COAL, ERIX, EUA.
  Uncertainty indicators: GPR, CPU, OPU.
  Macrofinancial conditioning variables: GSCPI, DXY, CPI, Industrial.

Mean, median, minimum, maximum, and sample SD use their usual definitions.
Skewness and excess kurtosis use e1071 type = 3 (normal excess kurtosis = 0).
ADF uses tseries::adf.test(x, alternative = "stationary") and its default lag
rule. A reported lower-bound p-value of 0.01 receives three stars; larger
p-values retain the existing 5% and 10% significance rules.

The table is printed and saved to:
  Energy Economics Code/r code/variable_summary_statistics.tex
It requires the LaTeX packages float, booktabs, and threeparttable. Unrounded
results remain in variable_descriptive_statistics. The existing two-decimal
table formatting, ADF stars, caption, label, and notes are retained.

Part B reads:
  Energy Economics Code/matlab code/resilience_metrics.xlsx

Expected columns: t, Variable, RP, RD. RP is resilience intensity (RI); RD is
resilience duration. The baseline contains 166 observations per series, from
February 2010 to November 2023. The R script reads these measures directly.
It retains the RI/RD matrices, Pearson correlations with pairwise complete
observations, Mean/SD/Min/Max tables, individual ranking tables, and wide ranking
tables. RI ranks higher values first; RD ranks lower values first. Ranking
excludes incomplete months and selects the first market in a tie, with the
existing warnings. Console rounding and printing order are unchanged.

RUN_IMPULSE_DIAGNOSTIC remains FALSE. TRUE enables the original single-path
preview using matlab code/tvpvar_imp.xlsx; it does not supply the summaries.

The separate Python conditioning input is:
  Energy Economics Data/markov_scale_data_166.csv
It uses rows 2:167 of the 167-row macrofinancial file, standardized using the
166-period sample and sample SD (denominator n-1). It is not the R summary input.

5. PLOTTING BLOCKS AND OUTPUTS
------------------------------
Block 1. Three-panel resilience schematic (6.2 x 12.2 inches).
  Output: r_plot_resilience_abc_vertical_re.pdf
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
  Output: gpr_resilience_H_comparison_academic_no_shades.pdf
  Folder: <PROJECT_DIR>/Fig/.
  The archived workbooks preserve the original comparison inputs and are
  separate from the main MATLAB baseline workbook. There are no event shades
  or labels. The mapping stays GPR (Var6-Var10); TARGET_SHOCK names the PDF only.

Block 4. Markov probabilities and resilience (12 x 16 inches, 5 x 2 plus legend).
  Input folder: <PROJECT_DIR>/Energy Economics Code/python code/output/
  Input: <shock>_ms_state_probabilities_state<state>.xlsx
  Default output: opu_ms_smoothed_probability_5x2_state1_prob_left_metric_right.pdf
  Output folder: <PROJECT_DIR>/Fig/.
  Required sheets: probabilities_long and state_mapping.
  Plotting columns: date, market, measure, metric_value, prob_selected.
  Measures are RI/RD; markets are OIL, NG, COAL, ERIX, EUA. The left axis shows
  probability and the right axis shows the resilience metric.

The default Markov settings remain SHOCK_LABEL = "OPU" and STATE_TO_PLOT = 1.
Set both consistently with the Python export filename. For state 2, also update
the retained "State 1 Strong Resilience" legend wording as appropriate.
Running a block again replaces its PDFs at the same configured paths.

6. BASELINE FIGURE CONTROLS
---------------------------
TARGET_SHOCKS <- c("GPR", "CPU", "OPU") preserves the three output files and
that order. Select a subset to draw fewer figures. The existing interface is:

  plot_vertical_resilience(
    target_shock = "GPR", r_data = r_data, x_date = x_date,
    target_dir = RESILIENCE_OUTPUT_DIR)

It returns the path invisibly. vertical_output_files retains the named paths.
MARKET_VAR_MAPS stores the original mappings, in OIL/NG/COAL/ERIX/EUA order:
  GPR: Var6,  Var7,  Var8,  Var9,  Var10
  CPU: Var14, Var15, Var16, Var17, Var18
  OPU: Var22, Var23, Var24, Var25, Var26

EVENT_LABEL_ADJUSTMENTS retains event_id, measure, x_shift_months, and y_pos.
"both" changes RI and RD together; "RI"/"RD" changes one column. Negative
x_shift_months moves a label left; positive values move it right. Larger y_pos
moves it upward. Rows apply in order, with later rows overriding earlier ones.
Append an override before the generation loop, for example:

  EVENT_LABEL_ADJUSTMENTS$GPR <- rbind(
    EVENT_LABEL_ADJUSTMENTS$GPR,
    data.frame(event_id = "E22", measure = "RD", x_shift_months = -2.2,
               y_pos = 0.12, stringsAsFactors = FALSE))

set_event_label_pos() within the generator also retains srt, cex, adj_x, adj_y,
col_text, and label controls. Further manual calls belong after the adjustment
loop and before plotting. The revised CPU list excludes E16 (Indonesia coal ban). OPU
uses "OPEC+ cuts" for E20. CPU retains the original CEX_EVENT=1.75 and original
horizontal offsets for its eight retained events. E14 (Fit for 55/COP26) is
placed at y_pos=0.25 to avoid REPowerEU; all other vertical positions match
the original layout. Concise, two-line event
labels preserve the original visual arrangement; full event definitions remain
in Supplementary_Appendix.tex. GPR/OPU offsets and all data-panel settings are
retained. Each shock uses common RI and RD axis ranges across markets.

7. STATIC VERIFICATION
----------------------
Both scripts passed R syntax parsing. After accounting for the documented
project/input/output path changes and directory setup, the remaining executable
syntax trees match the previous versions. Statistical expressions and data-panel settings are retained. The revised CPU event list excludes E16. The subsequent layout correction
restores the original R event font size, compact labels and horizontal offsets
for the remaining CPU events, with one vertical correction for E14.
The horizon workbooks were copied byte for byte from the existing analysis.
Existing reference PDFs were relocated without changing their contents.
For the root-location fix, only the isolated path-setup expressions were
evaluated. Checks cover the project root, code subdirectories, supplied roots,
and an existing PROJECT_DIR pointing to r code/. Input existence and the common
Fig/ destination were checked.

For the date-input update, only the isolated date-reading expressions were
evaluated. The workbook's 167 dates match the corresponding original source
dates, and observations 2-167 match the 166-row Markov conditioning file.
Outside the date-reading setup, all statistical and plotting expressions are
unchanged. No numerical input or analysis workbook was
modified. Neither full script was sourced; no statistical results, LaTeX tables,
or PDFs were regenerated.

REVISED CPU EVENT LIST (main_J1104.tex / Supplementary_Appendix.tex)
The active CPU figure uses eight windows: EU ETS backloading/Phase III,
COP21/Paris Agreement, U.S. Paris exit announcement, European Green Deal,
Fit for 55/Glasgow Pact, REPowerEU, IRA, and MSR/EU ETS reform. E16 is absent;
remaining IDs and monthly boundaries are retained. Event windows provide
historical context and are not imposed as estimated break dates.

CPU R LAYOUT CORRECTION
The R CPU figure uses CEX_EVENT=1.75, matching GPR and OPU. Its original
horizontal adjustments and compact labels are restored after dropping E16.
Only E14 moves down to y_pos=0.25 to avoid REPowerEU:
  event_id:       E04, E06, E09, E11, E14, E18, E19, E21
  x_shift_months: -12, -12, -14, -26, -18, -10, -4, -9
  y_pos:          .75, .75, .25, .75, .25, .75, .50, .20
The figure keeps short labels such as Paris Agreement and Fit for 55 & COP26.
These identify the same updated appendix windows; the full policy descriptions
are documented there. Only the CPU R PDF was regenerated for this correction.
