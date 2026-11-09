ENERGY ECONOMICS DATA: FILES, UNITS, AND SAMPLE
=============================================

1. PURPOSE AND PACKAGE LAYOUT
-----------------------------
This folder contains prepared monthly inputs for the energy-market resilience
analysis. Keep it beside Energy Economics Code under the same parent directory.
The Code README provides the full MATLAB -> resilience -> Python -> R workflow.

The folder contains four primary monthly input files:

  VAR_100data.xlsx
  VAR_data.csv
  markov_100data_167.csv
  markov_scale_data_166.csv

The horizon_resilience/ subfolder additionally contains three archived
resilience workbooks for the H = 6, 8, and 10 comparison figure (Section 8).

The preferred VAR and variable-summary input is VAR_100data.xlsx. The CSV
VAR_data.csv provides decimal energy returns as a reference series.

2. FILE INVENTORY
-----------------
File                         Observations  Period                    Main use
---------------------------  ------------  ------------------------  --------------------------
VAR_100data.xlsx              167           Jan 2010-Nov 2023         MATLAB VAR and R summaries
VAR_data.csv                 167           Jan 2010-Nov 2023         Decimal-return reference
markov_100data_167.csv        167           Jan 2010-Nov 2023         R macrofinancial summaries
markov_scale_data_166.csv     166           Feb 2010-Nov 2023         Python Markov regressors

The workbook contains one worksheet, VAR_100data. The listed observation counts
exclude the header row. All four primary input files have a first column named
date, with complete observations and unique monthly dates.

Dates are stored as month-start ISO 8601 strings, for example:
  2010-01-01T00:00:00Z
Preserve the monthly order and date labels when importing the files.

3. VAR_100data.xlsx: PREFERRED VAR INPUT
----------------------------------------
Columns, in the required order, are:

  date, GPR, CPU, OPU, OIL, NG, COAL, ERIX, EUA

The date column is also the calendar for the R baseline and
horizon-comparison figures. Both plotting blocks read it automatically from
sheet VAR_100data. Its 167 monthly dates cover January 2010-November 2023;
observations 2-167 provide the 166 dates for resilience and Markov analysis,
February 2010-November 2023.

Uncertainty indicators:
  GPR: geopolitical risk index, in index levels.
  CPU: climate policy uncertainty index, in index levels.
  OPU: oil price uncertainty index, in index levels.

Energy-market series:
  OIL: Brent crude oil front-month futures.
  NG: Henry Hub natural gas front-month futures.
  COAL: Newcastle thermal coal front-month futures.
  ERIX: European Renewable Energy Total Return Index.
  EUA: EU ETS carbon allowance front-month futures.

The five energy columns contain monthly log returns multiplied by 100:

  return_percent = 100 * log(P_current / P_previous)

The uncertainty columns are index levels. tvpvar_main.m standardizes the eight
numerical columns using zscore() before fitting the TVP-VAR-SV model. The R
variable-summary script describes the workbook in its supplied units.

Variable definitions and source citations are provided in the manuscript's
variable-definition and data-source table.

4. VAR_data.csv: DECIMAL-RETURN REFERENCE
-----------------------------------------
This CSV has the same dates, column order, and three uncertainty-index series
as VAR_100data.xlsx. Its five energy-market returns are expressed as decimal
log returns:

  return_decimal = log(P_current / P_previous)
  return_percent = 100 * return_decimal

For example, the first OIL observation is approximately -0.086673 in the CSV
and -8.667314 in the workbook. The return-unit conversion applies to OIL, NG,
COAL, ERIX, and EUA. Both files share the same GPR, CPU, OPU, and date values.

The main scripts use the percentage-scale workbook values directly.

5. markov_100data_167.csv: UNSTANDARDIZED MACROFINANCIAL DATA
-----------------------------------------------------------
Columns are:

  date, DXY, GSCPI, CPI, Industrial

The file contains transformed monthly conditioning variables on their original
analysis scales:

  DXY: 100 times the monthly log change in the U.S. Dollar Index.
  GSCPI: 100 times the monthly first difference in the Global Supply Chain
         Pressure Index. Positive values indicate tightening supply pressure;
         negative values indicate easing pressure.
  CPI: 100 times the monthly log change in the Consumer Price Index.
  Industrial: 100 times the monthly log change in the Industrial Production Index.

Thus GSCPI uses a first difference, while the other three use log changes.
The file is unstandardized and covers the full 167-month descriptive sample.
ee_descriptive_statistics.r joins it to VAR_100data.xlsx by date for the
main-variable summary table.

6. markov_scale_data_166.csv: STANDARDIZED MARKOV INPUT
------------------------------------------------------
Columns are the same as in the unstandardized macrofinancial file:

  date, DXY, GSCPI, CPI, Industrial

The 166-month file is constructed by:

  1. Taking rows 2:167 of the 167-observation macrofinancial data, which removes
     January 2010 and retains February 2010-November 2023.
  2. Standardizing each numerical column over those retained 166 observations:

       z_t = (x_t - mean_166(x)) / sample_SD_166(x)

The sample SD uses denominator n-1, equivalent to R scale() or pandas
std(ddof=1). Each supplied conditioning series has mean approximately zero
and sample SD one. Standardization is performed on the 166-month sample,
after removing the first observation.

Markov.ipynb reads these standardized values directly. The series are aligned
by row order with the 166 resilience observations; preserve both the dates and
the common chronological order when using this file.

7. CONNECTION TO GENERATED RESILIENCE AND MODEL OUTPUTS
-------------------------------------------------------
The MATLAB VAR input has 167 months. With nlag = 1, resilience observations use
sample periods 2:167, covering 166 months.
The generated workbook is stored under the Code package:

  Energy Economics Code/matlab code/resilience_metrics.xlsx

Its t indices run from 2 to 167 and correspond to February 2010-November 2023.
Its columns are t, Variable, RP, and RD. RP is the output name for resilience
intensity (RI).

The Python notebook combines that resilience workbook with
markov_scale_data_166.csv, then exports state probabilities and Wald tests to:

  Energy Economics Code/python code/output/

The R descriptive statistics use the 167-month files before standardization;
the Markov regressions use the 166-month standardized macrofinancial input.
This accounts for the different sample lengths and units in the two stages.

8. horizon_resilience/: HORIZON-COMPARISON INPUTS
-----------------------------------------------
This subfolder contains the precomputed workbooks used by R Block 3:

  resilience_metrics_median6.xlsx   H = 6
  resilience_metrics_median.xlsx    H = 8
  resilience_metrics_median10.xlsx  H = 10

Each workbook contains t, Variable, RP, and RD, with 166 observations for each
of the 64 shock-response combinations. The sample indices are t = 2,...,167,
corresponding to February 2010-November 2023. These are precomputed resilience
measures, separate from the four monthly VAR/macrofinancial source inputs.

The R plotting script reads this subfolder using PROJECT_DIR and saves its
comparison PDF to the common <project root>/Fig/ folder. The MATLAB README, Section 9, describes the
H/N/worksheet-row settings for generating alternative-horizon workbooks.
