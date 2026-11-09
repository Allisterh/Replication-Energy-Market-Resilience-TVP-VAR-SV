ENERGY ECONOMICS MATLAB CODE
===========================

Main estimation script: tvpvar_main.m
Resilience calculation: resilience.m
Final resilience data:  resilience_metrics.xlsx

1. PURPOSE AND RUNNING ORDER
---------------------------
The workflow has two stages:

  tvpvar_main.m: MCMC estimation -> tvpvar_imp.xlsx
  resilience.m: tvpvar_imp.xlsx -> resilience_metrics.xlsx

Keep all supplied .m files together and set MATLAB's Current Folder to this
matlab code directory. Exported workbooks are written in the Current Folder.
All PDF figures are written to <project root>/Fig/, resolved from this
function's location and created automatically when needed.

Step 1. Keep Energy Economics Code and Energy Economics Data as sibling folders.
        Open tvpvar_main.m from this matlab code folder. It resolves the input
        Energy Economics Data/VAR_100data.xlsx from its own script location,
        so the parent directory can be moved without editing a personal path.

Step 2. Run tvpvar_main.m. The script ends at:

          mcmc_girf_median(10000,Time,'yyyy');

        Wait for MCMC estimation and workbook/PDF export to finish.

Step 3. In the same Current Folder, run the separate resilience script:

          resilience

        It reads tvpvar_imp.xlsx and writes resilience_metrics.xlsx. It clears
        the workspace at the start, so all inputs for this stage come from the
        exported workbook. MCMC draws do not have to remain in the workspace.

The Time argument is passed to mcmc_girf_median(), but that function currently
does not use either its datetime or timeformat argument in its calculations.

The scripts reuse the existing output filenames. Keep results from different
parameter settings in separate directories if they need to be retained.

2. MATLAB REQUIREMENTS
----------------------
Use MATLAB with spreadsheet I/O functions readmatrix, readtable, writecell,
writematrix, and writetable. Statistics and Machine Learning Toolbox functions
used by the code include zscore, gamrnd, normcdf, and wishrnd. The baseline uses
gamrnd for diagonal innovation variances. All baseline custom helper functions
are included in this folder.

3. INPUT DATA AND VARIABLE ORDER
-------------------------------
tvpvar_main.m reads VAR_100data.xlsx using readmatrix(). The supplied input
has a date column followed by eight numerical series in this exact order:

  Column 1: date
  Column 2: GPR
  Column 3: CPU
  Column 4: OPU
  Column 5: OIL
  Column 6: NG
  Column 7: COAL
  Column 8: ERIX
  Column 9: EUA

The estimation data are selected with data(:, 2:9). The names in asvar must
match these eight numerical columns. The date column is assigned to Time.
The baseline input contains 167 monthly observations, January 2010 through
November 2023. With one VAR lag, valid GIRFs and resilience measures cover
166 months, February 2010 through November 2023.

The input already contains the prepared energy-market returns and uncertainty
indices. zscore(ydata) standardizes each numerical series to mean zero and unit
sample standard deviation before estimation. The MATLAB script does not apply
another return transformation to these input columns.

4. KEY SETTINGS IN tvpvar_main.m
-------------------------------
  Setting                            Baseline   Meaning
  ---------------------------------  --------   ----------------------------
  nlag                               1          VAR lag order.
  setvar_girf('fastimp', ...)          0          Draw-specific GIRF medians.
  setvar_girf('ranseed', ...)          2025       Random-number seed.
  setvar_girf('impulse', ...)          8          Maximum horizon H.
  setvar_girf('intercept', ...)        1          Time-varying intercept.
  setvar_girf('SigB', ...)             0          Diagonal beta-innovation Q.
  setvar_girf('SigA', ...)             0          Diagonal a-innovation Q.
  setvar_girf('SigH', ...)             0          Diagonal h-innovation Q.
  mcmc_girf_median(nsim, ...)          10000      Retained posterior draws.

The impulse setting is the largest exported horizon. setvar_girf.m stores
m_nimp = H + 1, so H = 8 generates nine response points: 0, 1, ..., 8.

With fastimp = 0, impulse_girf.m is evaluated for each retained MCMC draw.
The paths are stored in single precision, and their pointwise posterior
medians are exported to tvpvar_imp.xlsx. resilience.m then computes the metrics
from that median path. Consequently, the output metrics are calculated from
posterior-median GIRFs. fastimp = 1 instead evaluates responses using posterior
mean parameter paths and changes the response summary used for the metrics.

The GIRF impact vector for shock i is Sigma(:,i) / sqrt(Sigma(i,i)), providing
a one-standard-deviation innovation in the standardized system.

The three covariance flags refer to innovations in the time-varying regression
coefficients (beta), contemporaneous parameters (a), and log volatilities (h).
All three are diagonal in the baseline. The h covariance flag set to 1 calls
svsamp_mv(), which is not supplied in this folder; the supplied baseline uses
svsamp.m with SigH = 0.

Prior settings in the main script:

  setvar_girf('prior', 'b', 50, 2e-1);
  setvar_girf('prior', 'a',  8, 2e-2);
  setvar_girf('prior', 'h',  8, 2e-2);

Under the baseline diagonal flags, the individual state-innovation variances
have inverse-gamma priors with the following shape and scale parameters:

  beta innovations: IG(shape = 50, scale = 0.20)
  a innovations:    IG(shape =  8, scale = 0.02)
  h innovations:    IG(shape =  8, scale = 0.02)

Here IG(alpha, beta) means that the reciprocal follows a gamma distribution
with shape alpha and scale 1/beta. setvar_girf.m doubles the a and h arguments;
mcmc_girf_median.m doubles the b arguments for the diagonal case. The gamma
updates subsequently divide these stored prior parameters by two. The values
above describe the resulting priors for the actual variance parameters.

Other baseline settings inside mcmc_girf_median.m:

  - nburn = round(0.1 * nsim) = 1000.
  - The loop runs from -nburn through nsim, including zero. Draws are retained
    only for iteration indices 1:10000, with no thinning. Thus 1001 preliminary
    iterations (-1000 through 0) precede the 10000 retained draws.
  - Uniform and normal random-number generators are initialized with seed 2025.
  - Initial state priors are beta_1 ~ N(0, 10*I), a_1 ~ N(0, 10*I), and
    h_1 ~ N(0, 50*I) under the diagonal baseline.
  - Initial values of the three innovation covariance matrices are 0.01*I.
  - With eight series, one lag, and an intercept, beta has 72 coefficients;
    a has 28 contemporaneous parameters and h has eight log-volatility states.
  - nK = floor(167/30) - 1 = 4 controls blocks in volatility sampling.
  - Diagnostics store six innovation standard-deviation chains: the first two
    diagonal elements from each of the beta, a, and h covariance matrices.
  - The diagnostic bandwidth/maximum plotted autocorrelation lag is 500.

Storing all GIRF draws can require substantial RAM. At the current dimensions,
the single-precision mgirf_draws array alone contains 167*9*64*10000 elements,
or approximately 3.85 GB (3.58 GiB), in addition to other arrays and operations.

5. MCMC OUTPUTS AND WORKBOOK LAYOUT
----------------------------------
The main outputs in the Current Folder are:

  tvpvar_imp.xlsx   Pointwise posterior-median GIRFs.
  tvpvar_vol.xlsx   Posterior means and SDs of log-volatility states.
  tvpvar_a.xlsx     Posterior means and SDs of contemporaneous parameters.
  tvpvar_ai.xlsx    Posterior means and SDs of inverse-matrix elements.
  tvpvar_int.xlsx   Posterior means and SDs of the time-varying intercepts.

Five diagnostic/parameter PDF groups are exported to <project root>/Fig/:

  01_parameter_diagnostics.pdf
  02_stochastic_volatility.pdf
  03_time_varying_a.pdf
  04_time_varying_a_inverse.pdf
  05_time_varying_intercept.pdf

In tvpvar_imp.xlsx, columns A and B contain the sample index t and horizon.
Columns C:BN contain all 8*8 = 64 shock-response combinations. Responses vary
within each shock block in the same order as asvar. The first eight response
columns therefore correspond to a GPR shock, the next eight to a CPU shock,
and the next eight to an OPU shock; the remaining blocks are also exported.

The workbook has three header rows:

  Row 1: response-variable names.
  Row 2: shock-variable names.
  Row 3: t and horizon labels.

The numerical response blocks start at row 4. Each sample period occupies
N = H + 1 = 9 rows, with horizon labels 0:8. The sample index appears only in
the first row of each block; the following eight cells in column A are blank.
The first lagged sample period has no valid estimated GIRFs, so its response
cells are empty. At the baseline, the sheet has 1506 rows and 66 columns.

6. KEY SETTINGS IN resilience.m: N AND THE FIRST VALID ROW
---------------------------------------------------------
  filename = 'tvpvar_imp.xlsx';
  data = readtable(filename, 'ReadVariableNames', false);
  data = data(13:end, :);
  N = 9;

N is the number of response points used for each t and shock-response pair.
It equals H + 1 because the exported path includes the impact horizon 0.
For the baseline H = 8, the path is 0:8 and N = 9.

Why does the data selection begin at row 13?

  Excel rows 1-3:   three header rows; no numerical GIRF observations.
  Excel rows 4-12:  nine response rows for t = 1; GIRF cells are empty because
                    nlag = 1 leaves this initial period without valid responses.
  Excel row 13:    t = 2, horizon 0; the first valid numerical GIRF observation.

Thus data(13:end, :) keeps row 13 and all later rows. It skips the first
12 rows: three header rows plus nine initially undefined response rows.
The former Chinese comment saying "skip the first 13 header rows" was
imprecise. The current English comment describes the actual selection.
This row index assumes the current import preserves the worksheet's starting
row; inspect the imported table when changing the spreadsheet layout or import
options.

For the current three-row header layout, the first valid worksheet row is:

  first_valid_row = 3 + nlag * (H + 1) + 1

With nlag = 1, coordinated examples are:

  Maximum horizon H   Response points N   First valid row
  -----------------   -----------------   ---------------
          6                   7                  11
          8                   9                  13
         10                  11                  15

Changing H requires re-estimating/exporting the GIRFs and updating both N and
the starting-row selection in resilience.m. Changing nlag also changes the
number of initial undefined response blocks. Before computing the metrics,
each retained t must have exactly N complete response rows.

After removing the initial rows, the script forward-fills t within each block,
then processes every response column in C:BN. Automatically generated table
names Var3 through Var66 are retained as output identifiers.

7. RESILIENCE FORMULAS AND OUTPUT INTERPRETATION
-----------------------------------------------
For each sample period and shock-response combination, let g_h denote the
exported GIRF at horizon h = 0,...,H and define:

  a_h = abs(g_h)
  N = H + 1
  h_bar = max(a_h)
  S = sum(a_h)

The code calculates resilience intensity using:

  RP = (N * h_bar - S) / (N * h_bar)

RP is the existing Excel column name for the resilience intensity measure RI.
Higher values indicate stronger relative shock absorption. h_bar is the peak
absolute response within this particular time-specific GIRF path.

The code calculates resilience duration using:

  RD = sum((1:N)' .* abs_responses) / S

The exported horizon labels are 0:H and the RD weights are 1:N. Accordingly,
the impact response at horizon 0 receives weight 1, and the response at horizon
8 receives weight 9 in the baseline. Equivalently, the implementation gives:

  RD = 1 + sum(h * a_h, h = 0,...,H) / S

This records the existing indexing convention explicitly. The impact response
is included in both RP and RD, and the formulas and weights are preserved.
Lower RD indicates earlier concentration of the absolute response weight and
faster relative recovery within the evaluated response window.

The output resilience_metrics.xlsx has four columns:

  t         Original sample index; baseline values are 2 through 167.
  Variable  Automatically generated shock-response identifier (Var3-Var66).
  RP        Resilience intensity, subsequently labeled RI in the paper/R code.
  RD        Resilience duration using the one-based weights described above.

The baseline file has 166*64 = 10624 data rows, ordered first by t and then by
response-column position. The first worksheet row contains the column names.

Mappings used by the R figures and Python Markov analysis are:

  Shock   OIL     NG      COAL    ERIX    EUA
  -----   -----   -----   -----   -----   -----
  GPR     Var6    Var7    Var8    Var9    Var10
  CPU     Var14   Var15   Var16   Var17   Var18
  OPU     Var22   Var23   Var24   Var25   Var26

Retain the original variable order when reproducing these mappings.

8. SUPPORTING FILES AND ENGLISH TRANSLATION
------------------------------------------
mcmc_girf_median.m performs MCMC sampling, GIRF summarization, diagnostics, and
export. setvar.m initializes the data globals; setvar_girf.m configures the
options. impulse_girf.m computes GIRFs and impulse.m computes conventional
impulse responses. drawimp.m remains available for separate response plots. The remaining
helper functions support the state simulation smoother, stochastic volatility
sampler, matrix construction, standardization, and convergence diagnostics.

Chinese comments, plot-legend strings, and console messages have been replaced
with English. drawimp.m has also been converted from its original GB18030
encoding to an English UTF-8-compatible ASCII file. Estimation parameters,
random-number calls, numerical formulas, export filenames, and output column
identifiers are unchanged. tvpvar_main.m ends after MCMC estimation and export;
resilience.m is run separately to construct the resilience metrics.

9. ALTERNATIVE HORIZONS FOR THE COMPARISON FIGURE
-----------------------------------------------
The existing comparison inputs are supplied in:
  Energy Economics Data/horizon_resilience/
They can be plotted directly by R Block 3 without regenerating MCMC results.

To generate another horizon, keep the driver impulse setting, resilience.m's
N, and its first retained worksheet row consistent. For the supplied one-lag
specification, there are three header rows and N undefined response rows for
t = 1, so the first valid row is 3 + N + 1:

  H   N = H + 1   First retained row   Comparison workbook
  6       7              11          resilience_metrics_median6.xlsx
  8       9              13          resilience_metrics_median.xlsx
  10     11              15          resilience_metrics_median10.xlsx

Set setvar_girf('impulse', H) in tvpvar_main.m, then update N and
data(first_row:end,:) in resilience.m before running those two stages.
Retain each generated workbook separately under the listed comparison name.
Use a separate working copy when generating alternatives so the main H = 8
analysis workbooks remain available for the baseline Markov and R workflows.
The files packaged for the comparison were copied from the existing analysis;
this path update did not re-estimate them.

10. OPTIONAL STATIC VAR BENCHMARK
---------------------------------
Run the new constant-parameter VAR and resilience benchmark with:

  results = static_var_main;

The new functions static_var_main.m, static_var_fit.m, and static_resilience.m
use the same prepared VAR workbook, eight-variable order, full-sample
standardization, one lag, impact-inclusive horizons 0:8, generalized shock
normalization, and RI/RD formulas as the baseline. Estimation uses OLS with
a constant intercept and innovation covariance.

All benchmark outputs are written separately in static_var_output/. The
static_var_summary.xlsx workbook includes 15 uncertainty-market RI/RD pairs
and an optional comparison with the means and ranks of the existing monthly
TVP metrics. The original TVP analysis files are only read, not replaced.
Static RI/RD are constant for each pair; their repeated monthly export is
for alignment and should not be passed to the Markov estimation.

See readme_static_var.txt for settings, formulas, output sheets, comparison
definitions, and MATLAB requirements.
