STATIC VAR BENCHMARK AND RESILIENCE MEASURES
==========================================

1. RUNNING THE BENCHMARK
------------------------
Keep these three functions together in the matlab code folder:

  static_var_main.m     Data import, standardization, exports, and comparison.
  static_var_fit.m      OLS estimation and generalized impulse responses.
  static_resilience.m   The same RI/RD formulas used by resilience.m.

In MATLAB, set the Current Folder to this matlab code folder and run:

  results = static_var_main;

This single command estimates the static VAR, computes resilience, and exports
the results. The default input is resolved relative to the function location:

  <project root>/Energy Economics Data/VAR_100data.xlsx

Outputs go to matlab code/static_var_output/. Re-running the benchmark replaces
its four output files in that folder.

Optional path overrides are available for separate data/output locations:

  results = static_var_main(input_file, output_dir, tvp_file);

Pass '' as tvp_file to compute the static estimates alone. For the TVP comparison,
supply a workbook with t, Variable, RP, and RD for the same 166 monthly dates.

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

Use the prepared uncertainty levels and percentage returns directly.
The covariance divisor is the residual degrees of freedom, as specified above.

The model is:

  y_t = c + B_1*y_(t-1) + ... + B_p*y_(t-p) + u_t,
  E(u_t*u_t') = Sigma.

The function uses generalized innovations:

  g_(h,j) = Phi_h * Sigma(:,j) / sqrt(Sigma(j,j)),  h=0,...,H.

Phi_0=I. For p=1, Phi_h=B_1^h. For p>1, Phi_h is obtained from powers of the
VAR companion matrix. The intercept cancels from the response difference.
The code tests covariance positive definiteness and reports the companion
spectral radius. A value at least one produces a stability warning.

lag_order and max_horizon are settings near the top of static_var_main.m.
static_var_fit supports other positive lag orders and nonnegative horizons.
The optional comparison runs only when the static settings match the declared
tvp_lag_order and tvp_max_horizon settings (default 1 and 8). Verify these TVP
settings against the run that produced the TVP workbook.

3. RESILIENCE DEFINITIONS
-------------------------
For a_h=abs(g_h), h=0,...,H, N=H+1, P=max(a_h), and S=sum(a_h):

  RI = RP = (N*P-S)/(N*P).
  RD = sum((h+1)*a_h)/S = 1 + sum(h*a_h)/S.

RP is the workbook column name for RI throughout the workflow.
Both measures include the impact response h=0. RD uses weights 1:9 at H=8,
as in resilience.m. Higher RI means stronger relative absorption; lower RD
means earlier response concentration. An identically zero response is exported
as NaN.

Each shock-response pair has one static GIRF and one static RI/RD pair.
The monthly panel repeats these constant estimates for alignment with the TVP
calendar. The Markov workflow uses the time-varying resilience_metrics.xlsx
produced by resilience.m.

4. OUTPUT FILES
----------------
  static_var_imp.xlsx
    The same three-header-row, shock-major layout as tvpvar_imp.xlsx. Columns
    C:BN contain all 64 pairs. The initial p response blocks are blank, and
    the same static path is repeated for t=p+1,...,T. At baseline the first
    valid worksheet row is 13, with 9 response rows per observation.

  static_resilience_metrics.xlsx
    Compatible columns t, Variable, RP, RD; 166*64=10624 data rows at baseline.
    Var3:Var66 identifiers follow the mapping below. Static values repeat
    for every matched t.

  static_var_summary.xlsx
    all_pairs:           64 unique shock-response RI/RD estimates.
    market_pairs:        15 uncertainty-market estimates with RI/RD ranks.
    date_mapping:        Original observation index t and date label.
    coefficients:        OLS estimates; columns are response equations.
    residual_covariance: Constant reduced-form innovation covariance Sigma.
    diagnostics:         Sample sizes, settings, residual df, spectral radius.
    tvp_comparison:      Optional comparison with monthly TVP metrics.

  static_var_results.mat
    results structure containing coefficients, covariance, residuals, GIRFs,
    standardized inputs, standardization constants, dates, and result tables.

Energy-response mappings:

  Shock   OIL     NG      COAL    ERIX    EUA
  GPR     Var6    Var7    Var8    Var9    Var10
  CPU     Var14   Var15   Var16   Var17   Var18
  OPU     Var22   Var23   Var24   Var25   Var26

5. HOW TO READ THE TVP COMPARISON
--------------------------------
The default TVP input is matlab code/resilience_metrics.xlsx.
The code validates one finite RI/RD observation for every
matching t in each of the 15 uncertainty-market combinations. Confirm that this
workbook comes from the same original data, order, standardization, and horizon.

The tvp_comparison sheet reports static RI/RD, the mean and time-series SD of
monthly TVP RI/RD, static-minus-TVP-mean differences, and market ranks within
each uncertainty source. Rank 1 denotes higher RI or lower RD; ties use average
ranks. TVP SD is the sample standard deviation across the monthly estimates.
TVP ranks are based on the means of monthly metrics.

6. SOFTWARE
------------
Base MATLAB with readtable, writecell, writematrix, and writetable.
The benchmark uses base MATLAB numerical functions.
