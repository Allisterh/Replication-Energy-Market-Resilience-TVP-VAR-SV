STATIC VAR BENCHMARK AND RESILIENCE MEASURES
==========================================

1. RUNNING THE BENCHMARK
------------------------
Keep these three new functions together in the existing matlab code folder:

  static_var_main.m     Data import, standardization, exports, and comparison.
  static_var_fit.m      OLS estimation and generalized impulse responses.
  static_resilience.m   The same RI/RD formulas used by resilience.m.

In MATLAB, set the Current Folder to this matlab code folder and run:

  results = static_var_main;

This single command estimates the static VAR, computes resilience, and exports
the results. The TVP-VAR does not need to be re-estimated. The default input is
resolved relative to the function location:

  <project root>/Energy Economics Data/VAR_100data.xlsx

Outputs go to matlab code/static_var_output/. The existing tvpvar_imp.xlsx and
resilience_metrics.xlsx are not overwritten. Re-running this benchmark replaces
its own four output files in static_var_output/.

Optional path overrides are available for separate data/output locations:

  results = static_var_main(input_file, output_dir, tvp_file);

Pass '' as tvp_file to run without the optional comparison. A missing default
TVP workbook produces a warning and does not prevent static estimation. A
supplied TVP workbook with invalid columns or unmatched observations raises an
error, so an invalid comparison is not silently reported.

2. SPECIFICATION AND MATCHING SETTINGS
--------------------------------------
The baseline matches the prepared data, variable order, scaling, lag order,
intercept inclusion, generalized shock definition, response horizon, and RI/RD
indexing of tvpvar_main.m and resilience.m:

  Variable order: GPR, CPU, OPU, OIL, NG, COAL, ERIX, EUA.
  Input sample: 167 months, January 2010-November 2023.
  Standardization: subtract full-sample mean; divide by sample SD (T-1 divisor).
  Lag order p: 1.
  Intercept: included and constant.
  Estimator: equation-by-equation OLS with the same regressors in every equation.
  Innovation covariance: U'*U/(T-p-(1+K*p)); constant over time.
  Maximum response horizon H: 8; the response includes horizons 0:8.
  Number of response points N: H+1=9.
  Matched TVP comparison months: February 2010-November 2023 (166 months).

Do not difference or multiply the input returns by 100 again: the workbook
already contains the prepared uncertainty levels and percentage returns.
The sample covariance divisor is residual degrees of freedom, not the Gaussian
MLE divisor T-p. This scalar choice changes GIRF amplitudes but not RI or RD.

The model is:

  y_t = c + B_1*y_(t-1) + ... + B_p*y_(t-p) + u_t,
  E(u_t*u_t') = Sigma.

The function uses generalized innovations, without Cholesky orthogonalization:

  g_(h,j) = Phi_h * Sigma(:,j) / sqrt(Sigma(j,j)),  h=0,...,H.

Phi_0=I. For p=1, Phi_h=B_1^h. For p>1, Phi_h is obtained from powers of the
VAR companion matrix. The intercept cancels from the response difference.
The code tests covariance positive definiteness and reports the companion
spectral radius. A value at least one produces a stability warning.

lag_order and max_horizon are settings near the top of static_var_main.m.
static_var_fit supports other positive lag orders and nonnegative horizons.
The optional comparison runs only when the static settings match the declared
tvp_lag_order and tvp_max_horizon settings (default 1 and 8). Verify these TVP
settings against the run that produced the existing workbook: the old metrics
workbook itself does not store lag order or response-horizon metadata.

3. RESILIENCE DEFINITIONS
-------------------------
For a_h=abs(g_h), h=0,...,H, N=H+1, P=max(a_h), and S=sum(a_h):

  RI = RP = (N*P-S)/(N*P).
  RD = sum((h+1)*a_h)/S = 1 + sum(h*a_h)/S.

RP is retained as the workbook column name to match the existing pipeline.
Both measures include the impact response h=0. RD uses weights 1:9 at H=8,
exactly as the supplied resilience.m. This is a response-weighted timing measure
with the existing one-based offset, not an exact time to full recovery.
Higher RI means stronger relative absorption; lower RD means earlier response
concentration. An identically zero response has undefined RI/RD and is exported
as NaN rather than assigned an artificial resilience score.

Each shock-response pair has ONE static GIRF and ONE static RI/RD pair. Repeating
these estimates at monthly dates does not create time variation. Do not use the
constant repeated panel to estimate a Markov-switching model or claim a monthly
resilience trajectory. It is provided for matching/overlaying the existing data.

4. OUTPUT FILES
----------------
  static_var_imp.xlsx
    The same three-header-row, shock-major layout as tvpvar_imp.xlsx. Columns
    C:BN contain all 64 pairs. The initial p response blocks are blank, and
    the same static path is repeated for t=p+1,...,T. At baseline the first
    valid worksheet row is 13, with 9 response rows per observation.

  static_resilience_metrics.xlsx
    Compatible columns t, Variable, RP, RD; 166*64=10624 data rows at baseline.
    Var3:Var66 identifiers preserve the existing mapping. Static values repeat
    for every matched t. This file is not the time-varying resilience input.

  static_var_summary.xlsx
    all_pairs:           64 unique shock-response RI/RD estimates.
    market_pairs:        15 uncertainty-market estimates with RI/RD ranks.
    date_mapping:        Original observation index t and date label.
    coefficients:        OLS estimates; columns are response equations.
    residual_covariance: Constant reduced-form innovation covariance Sigma.
    diagnostics:         Sample sizes, settings, residual df, spectral radius.
    tvp_comparison:      Optional comparison with existing monthly TVP metrics.

  static_var_results.mat
    results structure containing coefficients, covariance, residuals, GIRFs,
    standardized inputs, standardization constants, dates, and result tables.

The existing energy-response mappings remain:

  Shock   OIL     NG      COAL    ERIX    EUA
  GPR     Var6    Var7    Var8    Var9    Var10
  CPU     Var14   Var15   Var16   Var17   Var18
  OPU     Var22   Var23   Var24   Var25   Var26

5. HOW TO READ THE TVP COMPARISON
--------------------------------
The default TVP input is the existing matlab code/resilience_metrics.xlsx.
It is only read. The code validates one finite RI/RD observation for every
matching t in each of the 15 uncertainty-market combinations. Confirm that this
workbook comes from the same original data, order, standardization, and horizon.

The tvp_comparison sheet reports static RI/RD, the mean and time-series SD of
monthly TVP RI/RD, static-minus-TVP-mean differences, and market ranks within
each uncertainty source. Rank 1 denotes higher RI or lower RD; ties use average
ranks. The TVP SD describes variation across dates, not an estimation standard
error. TVP ranks use the means of monthly metrics, not metrics of an averaged
GIRF. No significance test or confidence interval is implied by these columns.

This benchmark compares a constant-coefficient, constant-covariance OLS VAR
with the existing Bayesian TVP-VAR-SV results. Differences may reflect both
time variation and estimation/summarization choices. It is a descriptive
benchmark comparison, not a test that isolates the contribution of each TVP
component or establishes predictive superiority. It addresses the static-VAR
alternative; spillover and event-study alternatives require their own metrics.

6. SOFTWARE
------------
MATLAB with readtable, writecell, writematrix, and writetable is required.
Only base MATLAB numerical functions are used; this new benchmark does not
require Econometrics Toolbox or Statistics and Machine Learning Toolbox.
The baseline TVP functions and their dependencies are unchanged.

7. VERIFICATION
----------------
Verified in MATLAB R2023b on 2026-11-02 using synthetic data only. Code Analyzer
reported no findings for the three new .m files. The checks covered OLS matrix
orientation, VAR(1) and VAR(2) GIRFs, variable-order invariance, RI/RD scale and
sign invariance, zero-response handling, spreadsheet layouts, and the optional
15-pair TVP comparison. The constant-parameter GIRFs matched impulse_girf.m,
and an unmodified copy of resilience.m reproduced all 10624 synthetic monthly
RI/RD output rows. The verification process completed with exit status zero.
The study workbook was inspected for its input schema but was not estimated;
no empirical static-VAR results have been generated by this verification.
