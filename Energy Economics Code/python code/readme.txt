ENERGY ECONOMICS PYTHON CODE
===========================

1. START HERE
-------------
Open Markov.ipynb and run its five code stages in order. Each selected model is
estimated once. Coefficient tables, economic state labels, state probabilities
and all Wald tests use the same fitted result objects.

Only the final stage displays results by default. It shows state levels and
persistence, a compact test overview, and the individual slope differences
retained after BH correction. Full coefficient tables can be expanded. The
same report is saved as output/Markov_results.html, with all numerical results
in output/Markov_results.xlsx. Start with these two files.

The earlier duplicate estimation pass, per-model console banners, repeated
wide text tables and full test dumps have been removed. Numerical model
settings, sample alignment and probability worksheet schemas are retained.
Optimizer warnings are recorded and summarized in the report; they are not
silently discarded. Full messages appear in the Fit_warnings workbook sheet.

2. PATHS AND REQUIREMENTS
-------------------------
Keep Energy Economics Code and Energy Economics Data under one project root.
Start the Jupyter kernel inside that tree, preferably in python code/. The
setup stage searches upward for both package folders.

Inputs:
  Energy Economics Code/matlab code/resilience_metrics.xlsx
  Energy Economics Data/markov_scale_data_166.csv

Outputs:
  Energy Economics Code/python code/output/

Requirements for Markov.ipynb:
  Python >= 3.9, numpy, pandas, scipy, statsmodels, openpyxl, IPython, Jupyter.
  Example: python3 -m pip install numpy pandas scipy statsmodels openpyxl jupyterlab

markov_reporting.py supplies display and spreadsheet formatting only; it does
not estimate models. Keep it next to Markov.ipynb. The notebook locates this
module through the resolved project root.

The separate figure scripts additionally use matplotlib. Design-comparison
prototypes also use Pillow. Figures are saved to the project-root Fig/ folder.

3. FIVE CODE STAGES
-------------------
  1. Find paths, import dependencies and define shared model utilities.
  2. Estimate final models and export R-ready probabilities.
  3. Compute individual slope-equality tests with raw p-values.
  4. Compute level, individual-slope and joint-slope Wald tests; adjust slopes.
  5. Export and display one final formatted report.

Markdown headings identify stages; these numbers refer to code stages, not to
all notebook cells. Restart the kernel before running the entire notebook.

Stage 2 controls, configured once:
  SELECTED_UNCERTAINTY = "ALL"       GPR, CPU, OPU, or ALL.
  STATE_TO_PLOT = 1                  Economic state for prob_selected.
  USE_SMOOTHED_PROBABILITIES = True   Full-sample smoothed probabilities.
  EXPORT_PROBABILITY_XLSX = True     Write the three R-ready workbooks.
  PRINT_STATSMODELS_SUMMARY = False  Optional full optimizer/model summaries.
  VERBOSE = False                   Optional progress banners.

ALL fits 30 models: three shocks x two measures x five markets. Setting one
shock fits ten models. Test stages retain their separate XLSX export flags.
The final report is always written. Rerun stages 2-5 after changing selection.

4. SAMPLE AND MODEL
--------------------
The resilience workbook supplies t, Variable, RP and RD; RP is plotted and
reported as RI. The selected series contain 166 monthly observations,
February 2010-November 2023, corresponding to t = 2,...,167.

Market order and variable mappings:
  Shock   OIL     NG      COAL    ERIX    EUA
  GPR     Var6    Var7    Var8    Var9    Var10
  CPU     Var14   Var15   Var16   Var17   Var18
  OPU     Var22   Var23   Var24   Var25   Var26

The conditioning file supplies date, DXY, GSCPI, CPI and Industrial. Its four
numerical columns are already standardized over the 166-month sample. Inputs
retain the existing positional alignment: truncate to the shortest length,
remove missing date/y/X jointly within each model, then sort by date. Preserve
the supplied chronological ordering; no date merge is introduced.

Each model centers y by its sample mean and estimates:
  y_t - mean(y) = alpha[s_t] + beta[s_t]' X_t + error_t

statsmodels settings:
  MarkovRegression(k_regimes=2, trend="c", switching_trend=True,
                   switching_exog=True, switching_variance=True)
  fit(method="nm", maxiter=10000, disp=False)

The intercept, four slopes and variance switch across states. The default
statsmodels starting-value procedure and time-invariant transition matrix are
retained. Original-scale conditional levels equal mean(y) plus the fitted
intercept, evaluated at X=0. No TVP-VAR or resilience calculation is performed.

Economic labels, assigned independently for every model:
  RI State 1: higher conditional level / stronger absorption.
  RI State 2: lower conditional level / weaker absorption.
  RD State 1: lower conditional level / faster relative recovery.
  RD State 2: higher conditional level / slower relative recovery.

p11/p22 are staying probabilities after relabeling. Expected state duration is
1/(1-p_ss), computed from unrounded probabilities and measured in observation
months. It is distinct from RD within the GIRF horizon.

Displayed coefficients retain four decimals, z-statistics three decimals, and
raw within-state significance stars. Full-precision estimates, standard errors,
p-values, likelihood, AIC/BIC and convergence flags are retained in the final
workbook. Formatting does not change the fitted numerical objects.

5. WALD TESTS AND BH FAMILY
---------------------------
All cross-state Wald tests use the full covariance matrix, including
cross-state covariance terms. Under ALL, the final tests consist of:
  30 conditional-level equality tests;
  120 variable-specific slope equality tests;
  30 joint tests of equality of all four slopes.

The current main_J1104.tex and Supplementary_Appendix.tex define ONE BH family
of the 120 individual slope comparisons. q_value_bh and stars_q are populated
for those slopes only. Conditional-level and joint-slope tests retain raw
p-values; their BH q-values are not defined. This differs from within-state
coefficient significance and from the separate raw slope-test workbook.

The previous notebook pooled 30 levels with 120 slopes. The output revision
corrects that scope to match the current manuscript. On the supplied baseline
results, slope-only BH gives 11 significant differences at 5%: ten CPI and one
Industrial comparison. The old pooled family gave 15. Raw estimates, Wald
statistics and raw p-values are unaffected by this correction.

6. FINAL OUTPUTS
----------------
The main entry points are:
  Markov_results.html
    One readable report; full coefficient tables are expandable.
  Markov_results.xlsx
    Guide, Model_overview, six shock/measure coefficient sheets,
    Coefficients_numeric, Test_overview, Slope_differences, Level_differences,
    Joint_slope_tests, State_mapping, and Fit_warnings when needed.
  Markov_run_manifest.json
    Input SHA-256 hashes, model count, correction family, convergence and
    warning counts. Input hashes are verified again before final export.

Existing integration files keep their names and worksheet schemas:
  gpr_ms_state_probabilities_state1.xlsx
  cpu_ms_state_probabilities_state1.xlsx
  opu_ms_state_probabilities_state1.xlsx
    probabilities_long: date, shock, measure, market, metric_value, y_centered,
    probability_type, prob_raw_regime0/1, prob_state1/2, state_to_plot,
    selected_raw_regime and prob_selected. Baseline: 1660 rows per shock.
    state_mapping: ten raw-to-economic state mapping records per shock.
  cross_state_equality_tests.xlsx
    equality_tests: 120 individual slopes with raw p-values.
  cross_state_comprehensive_tests.xlsx
    individual_tests: 30 levels plus 120 slopes; BH q-values for slopes only.
    joint_slope_tests: 30 joint tests with raw p-values.

All XLSX files use readable headers, frozen header rows, filters and consistent
number/date formatting. The probability workbook stays active on
probabilities_long, the worksheet read by R. STATE_TO_PLOT=2 changes probability
filenames to state2.xlsx; both economic state probability columns remain.
Files ending in _no100.xlsx are earlier local alternatives, not default inputs
or outputs of this workflow. They are not used to build the final report.

7. FIGURES AND REVISED CPU EVENTS
---------------------------------
ee_plot_resilience_2x3.py is the selected standalone resilience figure script.
See readme_resilience_2x3_wide.txt for commands and layout parameters. It keeps
the accepted 45-degree, 7-point event labels, a market legend in each RI panel,
and numerical y-axis tick labels in all six data panels.

The revised CPU list follows Appendix Table tab:event_windows_ext in
Supplementary_Appendix.tex: eight windows, with no Indonesia coal-ban event.
Labels identify EU ETS backloading/Phase III, COP21/Paris, the U.S. Paris exit
announcement, European Green Deal, Fit for 55/Glasgow Pact, REPowerEU, IRA and
MSR/EU ETS reform. The R baseline generator and Python design scripts use the
same updated memberships and monthly boundaries. GPR and OPU retain nine and
eight windows, respectively; existing event IDs remain stable (E16 is absent).

R reads its Markov probabilities from output/ and writes PDF figures to Fig/.
Match R's SHOCK_LABEL and STATE_TO_PLOT to the Python workbook selection.

8. VERIFICATION
---------------
The updated notebook was parsed and run through all five code stages using
the supplied inputs. The regression specification was retained, and final
means/probabilities/raw tests were compared with the previous saved outputs.
Only individual-slope BH q-values change with the corrected family. Selected
figure PDFs were regenerated from the existing resilience workbook and
rendered to inspect text placement and the revised CPU event list.
