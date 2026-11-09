ENERGY ECONOMICS: SELF-CONTAINED MARKOV NOTEBOOK
===============================================

1. FILES AND RUNNING ORDER
--------------------------
Markov.ipynb contains the complete Python workflow. There are no project-local
.py dependencies. The folder's active contents are:

  Markov.ipynb   Model estimation, tests, diagnostics, reporting and verification.
  readme.txt    This guide.
  output/       Final reports and the existing R integration workbooks.

Open Markov.ipynb, restart the kernel, and run all six code stages in order:
  1. Find paths, load dependencies and define shared/report/verification helpers.
  2. Estimate final Markov models once and export the probabilities for R.
  3. Compute individual cross-state slope tests with raw p-values.
  4. Compute level, slope and joint Wald tests with separate BH families.
  5. Compute the supplementary macrofinancial and conditional sensitivity checks.
  6. Write the final report and optionally compare it against the TeX tables.

The first cell's helper definitions are collapsed by default; expand them for
inspection. The numerical diagnostics are defined in Stage 5. The former
markov_reporting, markov_diagnostics and verification helpers are embedded in
the notebook; their numerical functions retain the same definitions.

By default only the last stage displays a report. Complete coefficient tables
can be expanded. Start with output/Markov_results.html or Markov_results.xlsx.
PRINT_STATSMODELS_SUMMARY and VERBOSE remain optional, disabled controls.
Optimizer warnings are summarized and retained in the final workbook.

Python resilience time-series plotting scripts and their design guides have
been removed. Use the R plotting workflow in r code/ee_plot_for_resilience.r.

2. PATHS, INPUTS AND SOFTWARE
-----------------------------
Keep Energy Economics Code and Energy Economics Data under the same project
root. Start the Jupyter kernel inside that tree, preferably in python code/.
The setup stage searches upward from the working directory for both folders.

Inputs:
  Energy Economics Code/matlab code/resilience_metrics.xlsx
  Energy Economics Data/markov_scale_data_166.csv

Destination:
  Energy Economics Code/python code/output/

Requirements:
  Python >= 3.9, numpy, pandas, scipy, statsmodels, openpyxl, IPython, Jupyter.
  Example: python3 -m pip install numpy pandas scipy statsmodels openpyxl jupyterlab

The resilience workbook supplies t, Variable, RP and RD; RP is reported as RI.
The baseline has 166 observations, February 2010-November 2023 (t=2,...,167).
The conditioning CSV supplies date and already standardized DXY, GSCPI, CPI
and Industrial, in that order. Market order and workbook mappings are:

  Shock   OIL     NG      COAL    ERIX    EUA
  GPR     Var6    Var7    Var8    Var9    Var10
  CPU     Var14   Var15   Var16   Var17   Var18
  OPU     Var22   Var23   Var24   Var25   Var26

The original estimation alignment is retained: truncate to the shortest
positional length, remove missing date/y/X jointly, then sort by date. Keep
the supplied chronological ordering. Supplementary diagnostics attach X by
date and explicitly verify that y and X equal the fitted model's observations.

3. MODEL SETTINGS AND STATE LABELS
----------------------------------
Stage 2 settings, configured once:
  SELECTED_UNCERTAINTY = "ALL"       GPR, CPU, OPU, or ALL.
  STATE_TO_PLOT = 1                  Economic state for prob_selected.
  USE_SMOOTHED_PROBABILITIES = True   Full-sample smoothed probabilities.
  EXPORT_PROBABILITY_XLSX = True     Export probability workbooks.
  PRINT_STATSMODELS_SUMMARY = False  Optional full model summaries.
  VERBOSE = False                   Optional progress headings.

ALL fits 30 models: three shocks x two measures x five markets. Selecting one
source fits ten. Each model centers y by its sample mean and estimates:
  y_t - mean(y) = alpha[s_t] + beta[s_t]' X_t + error_t

The specification and optimizer remain:
  MarkovRegression(k_regimes=2, trend="c", switching_trend=True,
                   switching_exog=True, switching_variance=True)
  fit(method="nm", maxiter=10000, disp=False)

The intercept, four slopes and variance switch across states; transition
probabilities are time-invariant. Existing statsmodels starting values are
retained. Original-scale conditional means add mean(y) back to the intercept
and are evaluated at X=0. Slopes refer to the standardized conditioning data.

Each model is relabeled independently:
  RI State 1: higher conditional mean / stronger absorption.
  RI State 2: lower conditional mean / weaker absorption.
  RD State 1: lower conditional mean / faster relative recovery.
  RD State 2: higher conditional mean / slower relative recovery.

p11/p22 are staying probabilities after relabeling. Expected persistence is
1/(1-p_ss), using unrounded probabilities and measured in observation months.
This differs from the RD measure within the GIRF horizon.

Displayed estimates use four decimals and z-statistics three decimals.
Within-state stars use raw p-values; full numerical precision is preserved
in the result objects and numerical workbook sheets.

4. WALD TESTS AND SUPPLEMENTARY DIAGNOSTICS
------------------------------------------
All cross-state Wald tests use the full parameter covariance, including
cross-state terms. BH adjustment uses three independent families under ALL:
  30 conditional-level tests; 120 individual slopes; 30 joint-slope tests.
Raw p-values and adjusted q-values are both retained. Baseline 5% BH rejection
counts are 28, 11 and 9. Ten of the 11 individual differences concern CPI and
one concerns Industrial. Use ALL to reproduce the paper's adjustment families.

Stage 5 implements the three supplementary diagnostic tables:
  - Fitted macrofinancial dispersion: compare sd(X_t' beta_s) over common X
    observations in both states (ddof=0), then omit March-December 2020 while
    keeping the coefficients fixed. Also count within-state and linear OLS-HAC
    coefficient detections using unadjusted p-values.
  - Weighted subsamples: for the original BH-significant slopes, retain the
    full-sample state probabilities and standardization, then fit regressions
    before 2021 and excluding March-December 2020. Removed rows become adjacent
    in the retained-observation HAC calculation.
  - Period indicators: fit state-weighted regressions with the intercept,
    original four standardized variables, and a level indicator. January 2021
    is the primary date; March 2020 and February 2022 are alternatives.

Signed ratio = (beta_2,D - beta_1,D) / (beta_2,MS - beta_1,MS).
Negative values indicate a sign reversal. Ratios are not explained-variance
shares or causal contributions. These conditional sensitivity checks add no
new cross-state equality tests, coefficient-change tests or BH adjustment.

All weighted checks use full-sample smoothed probabilities, independently of
the R probability-export flag, with the original numerical floor of 1e-6.
Raw probability exports are unchanged. Non-finite probabilities raise an
error. HAC uses six lags, the Bartlett kernel, no small-sample correction and
normal-reference inference (use_t=False). Weighted statistics in parentheses
are coefficients divided by their HAC standard errors.

Baseline sample sizes are 166 in full, 131 before 2021 and 156 after excluding
the ten 2020 months. Indicator-one counts are 45, 35 and 22. The no-indicator
weighted slopes agree with the original Markov slopes within 0.002.
All settings, sample counts and numerical alignment checks are exported.

5. OUTPUT FILES
----------------
Main entry points:
  Markov_results.html
    One readable report, with expandable coefficient and diagnostic tables.
  Markov_results.xlsx
    Guide, Model_overview, six shock/measure coefficient sheets,
    Coefficients_numeric, Test_overview, Slope_differences, Level_differences,
    Joint_slope_tests, State_mapping, and Fit_warnings when needed.
    Supplementary sheets: macro_summary, fitted_dispersion, linear_hac,
    subsample_checks, period_indicator, indicator_dates, weighted_alignment,
    diagnostic_samples and diagnostic_settings.
  Markov_run_manifest.json
    Input hashes, model counts, BH families, convergence/warning counts and
    supplementary settings. Input hashes are checked again before export.

Existing R integration and test files retain their names and schemas:
  gpr_ms_state_probabilities_state1.xlsx
  cpu_ms_state_probabilities_state1.xlsx
  opu_ms_state_probabilities_state1.xlsx
    probabilities_long: dates, outcomes, raw/economic-state probabilities and
    prob_selected (1660 rows per shock). state_mapping: ten records per shock.
  cross_state_equality_tests.xlsx
    equality_tests: 120 raw individual slope tests.
  cross_state_comprehensive_tests.xlsx
    individual_tests: 30 levels and 120 slopes, with independent BH families.
    joint_slope_tests: 30 joint tests with their own BH correction.

XLSX files have formatted headers, frozen rows, filters and readable column/row
sizes. STATE_TO_PLOT=2 changes probability filenames to state2.xlsx; both state
columns remain available. Files ending _no100.xlsx are earlier alternatives,
not default inputs or outputs. R reads the probability files from output/ and
writes figures to the project-root Fig/ directory.

6. OPTIONAL MANUSCRIPT VERIFICATION IN STAGE 6
---------------------------------------------
Normal analysis needs no manuscript files. The verification functions are
included in the same notebook. In Stage 6, change:

  VERIFY_MANUSCRIPT = True
  APPENDIX_TEX = Path("/path/to/Supplementary_Appendix.tex")
  MAIN_TEX = Path("/path/to/main_J1108.tex")

Then run Stage 6 again after the result objects have been computed. Set
MAIN_TEX=None to check the appendix alone. A mismatch raises an error.
There is no separate verification script or command-line dependency.

The checker compares generated results to the three supplementary diagnostic
tables, sample sizes, the weighted/Markov alignment bound and, when supplied,
all main Panel C Wald statistics and BH stars. Numbers are checked at their
displayed precision; p-value inequalities are checked as inequalities. The
manuscripts supply reference values only and never enter estimation.

Files written beside the result workbook:
  Appendix_verification.csv   Every comparison and pass/fail status.
  Appendix_verification.json  Counts and source-document SHA-256 hashes.

The current baseline passes 384 appendix-only comparisons, or 504 with the
main manuscript. The consolidated notebook was executed with the separate
Python helpers removed; its estimates and numerical outputs match the prior
version. Each model is still fitted once, and only the final report is shown
by default.
