function results = static_var_main(input_file, output_dir, tvp_file)
%STATIC_VAR_MAIN Run the constant-parameter VAR benchmark and resilience export.
% Run static_var_main from this folder. All defaults are location-relative.
% Optional paths: results = static_var_main(input_file, output_dir, tvp_file).
% Set tvp_file to '' to omit the comparison with existing TVP estimates.

%% Settings matched to tvpvar_main.m and resilience.m.
lag_order = 1;
max_horizon = 8;  % Include horizons 0:8; RD weights are 1:9.
variable_names = ["GPR", "CPU", "OPU", "OIL", "NG", "COAL", "ERIX", "EUA"];
tvp_lag_order = 1;   % Settings of the existing TVP workbook, not re-estimated.
tvp_max_horizon = 8;

script_dir = fileparts(mfilename('fullpath'));
project_dir = fileparts(fileparts(script_dir));
if nargin < 1 || isempty(input_file)
    input_file = fullfile(project_dir, 'Energy Economics Data', 'VAR_100data.xlsx');
end
if nargin < 2 || isempty(output_dir)
    output_dir = fullfile(script_dir, 'static_var_output');
end
if nargin < 3
    tvp_file = fullfile(script_dir, 'resilience_metrics.xlsx');
end
if ~isfile(input_file)
    error('staticVAR:InputFile', 'Input workbook not found: %s', input_file);
end

%% Read the same prepared data and standardize with sample SD, as in zscore.
input = readtable(input_file, 'VariableNamingRule', 'preserve', 'TextType', 'string');
if width(input) ~= 9 || ~isequal(string(input.Properties.VariableNames(2:9)), variable_names)
    error('staticVAR:InputColumns', ...
        'Expected date followed by GPR, CPU, OPU, OIL, NG, COAL, ERIX, EUA.');
end
raw = input{:, 2:9};
validateattributes(raw, {'double'}, {'2d', 'real', 'finite', 'nonempty'});
dates = string(input{:, 1});
if any(ismissing(dates)) || numel(unique(dates)) ~= height(input)
    error('staticVAR:Dates', 'Input dates must be nonmissing and unique.');
end
input_mean = mean(raw, 1);
input_sd = std(raw, 0, 1);
if any(input_sd <= 0)
    error('staticVAR:ConstantSeries', 'Each input series must have positive sample SD.');
end
y = (raw - input_mean) ./ input_sd;
model = static_var_fit(y, lag_order, max_horizon);
metrics = static_resilience(model.GIRF, variable_names);

%% Unique static estimates and a compatible constant monthly panel.
n_vars = numel(variable_names);
n_pairs = n_vars^2;
n_points = max_horizon + 1;
t_values = (lag_order + 1:height(input))';
market_rows = ismember(metrics.Shock, variable_names(1:3)) & ...
              ismember(metrics.Response, variable_names(4:8));
market_metrics = metrics(market_rows, :);
[market_metrics.RI_Rank, market_metrics.RD_Rank] = market_ranks( ...
    market_metrics.Shock, market_metrics.RP, market_metrics.RD);
panel = table(repelem(t_values, n_pairs), ...
    repmat(metrics.Variable, model.NEffective, 1), ...
    repmat(metrics.RP, model.NEffective, 1), repmat(metrics.RD, model.NEffective, 1), ...
    'VariableNames', {'t', 'Variable', 'RP', 'RD'});
date_mapping = table(t_values, dates(t_values), 'VariableNames', {'t', 'Date'});

comparison = table();
if strlength(string(tvp_file)) > 0
    if lag_order ~= tvp_lag_order || max_horizon ~= tvp_max_horizon
        warning('staticVAR:ComparisonSettings', ...
            'TVP comparison skipped: lag order or horizon differs from the declared TVP settings.');
    elseif isfile(tvp_file)
        comparison = compare_tvp(tvp_file, market_metrics, t_values);
    else
        warning('staticVAR:MissingTVP', 'TVP comparison skipped; file not found: %s', tvp_file);
    end
end

%% Export to a separate folder; existing TVP analysis outputs are not touched.
if ~isfolder(output_dir)
    mkdir(output_dir);
end
impulse_file = fullfile(output_dir, 'static_var_imp.xlsx');
metrics_file = fullfile(output_dir, 'static_resilience_metrics.xlsx');
summary_file = fullfile(output_dir, 'static_var_summary.xlsx');
for filename = {impulse_file, metrics_file, summary_file}
    if isfile(filename{1})
        delete(filename{1});
    end
end

% Preserve the TVP workbook's three-row header and Var3:Var66 mapping.
headers = cell(3, n_pairs + 2);
headers{1, 2} = 'Response:';
headers{2, 2} = 'Shock:';
headers(3, 1:2) = {'t', 'horizon'};
headers(1, 3:end) = cellstr(metrics.Response)';
headers(2, 3:end) = cellstr(metrics.Shock)';
impulse_panel = repmat(model.GIRF, height(input), 1);
impulse_panel(1:lag_order * n_points, :) = NaN;
time_column = nan(height(input) * n_points, 1);
time_column(1:n_points:end) = (1:height(input))';
horizon_column = repmat((0:max_horizon)', height(input), 1);
writecell(headers, impulse_file, 'Sheet', 1, 'Range', 'A1');
writematrix([time_column, horizon_column, impulse_panel], impulse_file, ...
    'Sheet', 1, 'Range', 'A4');
writetable(panel, metrics_file);
writetable(metrics, summary_file, 'Sheet', 'all_pairs');
writetable(market_metrics, summary_file, 'Sheet', 'market_pairs');
writetable(date_mapping, summary_file, 'Sheet', 'date_mapping');

terms = "Intercept";
for ell = 1:lag_order
    terms = [terms; variable_names' + "_L" + string(ell)]; %#ok<AGROW>
end
coefficient_table = [table(terms, 'VariableNames', {'Regressor'}), ...
    array2table(model.Beta, 'VariableNames', cellstr(variable_names))];
covariance_table = [table(variable_names', 'VariableNames', {'Variable'}), ...
    array2table(model.Sigma, 'VariableNames', cellstr(variable_names))];
diagnostics = table(["InputObservations"; "EffectiveObservations"; "LagOrder"; ...
    "MaxHorizon"; "ResponsePoints"; "RegressorsPerEquation"; "ResidualDF"; ...
    "SpectralRadius"], [height(input); model.NEffective; lag_order; max_horizon; ...
    n_points; model.NRegressors; model.ResidualDF; model.SpectralRadius], ...
    'VariableNames', {'Statistic', 'Value'});
writetable(coefficient_table, summary_file, 'Sheet', 'coefficients');
writetable(covariance_table, summary_file, 'Sheet', 'residual_covariance');
writetable(diagnostics, summary_file, 'Sheet', 'diagnostics');
if ~isempty(comparison)
    writetable(comparison, summary_file, 'Sheet', 'tvp_comparison');
end
results = struct('Model', model, 'Metrics', metrics, 'MarketMetrics', market_metrics, ...
    'Comparison', comparison, 'Dates', dates, 'VariableNames', variable_names, ...
    'InputMean', input_mean, 'InputSD', input_sd, 'StandardizedData', y, ...
    'InputFile', input_file, 'TVPFile', tvp_file, 'OutputDir', output_dir);
save(fullfile(output_dir, 'static_var_results.mat'), 'results');
fprintf('\nStatic VAR(%d), H=%d: %d input months, %d regression observations.\n', ...
    lag_order, max_horizon, height(input), model.NEffective);
fprintf('Spectral radius: %.6f. Outputs: %s\n', model.SpectralRadius, output_dir);
disp(market_metrics);
end

function comparison = compare_tvp(tvp_file, static_metrics, t_values)
% A static point estimate is compared with the mean of monthly TVP metrics.
tvp = readtable(tvp_file, 'TextType', 'string');
required = {'t', 'Variable', 'RP', 'RD'};
if ~all(ismember(required, tvp.Properties.VariableNames))
    error('staticVAR:TVPColumns', 'The TVP workbook must contain t, Variable, RP, RD.');
end
comparison = static_metrics(:, {'Variable', 'Shock', 'Response'});
n_rows = height(comparison);
tvp_ri = nan(n_rows, 1);
tvp_rd = nan(n_rows, 1);
tvp_ri_sd = nan(n_rows, 1);
tvp_rd_sd = nan(n_rows, 1);
for i = 1:n_rows
    rows = string(tvp.Variable) == comparison.Variable(i);
    block = sortrows(tvp(rows, required), 't');
    if height(block) ~= numel(t_values) || ~isequal(block.t, t_values) || ...
            any(~isfinite(block.RP)) || any(~isfinite(block.RD))
        error('staticVAR:TVPSample', ...
            'TVP series %s must contain one finite RI/RD pair for each matching t.', ...
            comparison.Variable(i));
    end
    tvp_ri(i) = mean(block.RP);
    tvp_rd(i) = mean(block.RD);
    tvp_ri_sd(i) = std(block.RP, 0);
    tvp_rd_sd(i) = std(block.RD, 0);
end
[tvp_ri_rank, tvp_rd_rank] = market_ranks(comparison.Shock, tvp_ri, tvp_rd);
comparison.Months = repmat(numel(t_values), n_rows, 1);
comparison.Static_RI = static_metrics.RP;
comparison.TVP_Mean_RI = tvp_ri;
comparison.TVP_SD_RI = tvp_ri_sd;
comparison.RI_Difference = static_metrics.RP - tvp_ri;
comparison.Static_RI_Rank = static_metrics.RI_Rank;
comparison.TVP_Mean_RI_Rank = tvp_ri_rank;
comparison.Static_RD = static_metrics.RD;
comparison.TVP_Mean_RD = tvp_rd;
comparison.TVP_SD_RD = tvp_rd_sd;
comparison.RD_Difference = static_metrics.RD - tvp_rd;
comparison.Static_RD_Rank = static_metrics.RD_Rank;
comparison.TVP_Mean_RD_Rank = tvp_rd_rank;
end

function [ri_rank, rd_rank] = market_ranks(shock, ri, rd)
% Rank the five markets within each shock; rank 1 is best, ties are averaged.
ri_rank = nan(size(ri));
rd_rank = nan(size(rd));
for s = unique(shock)'
    for i = find(shock == s)'
        group = shock == s;
        if isfinite(ri(i))
            ri_rank(i) = 1 + sum(ri(group) > ri(i)) + (sum(ri(group) == ri(i)) - 1) / 2;
        end
        if isfinite(rd(i))
            rd_rank(i) = 1 + sum(rd(group) < rd(i)) + (sum(rd(group) == rd(i)) - 1) / 2;
        end
    end
end
end
