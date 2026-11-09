function metrics = static_resilience(girf, variable_names)
%STATIC_RESILIENCE Apply the existing resilience.m formulas to static GIRFs.
% girf has H+1 rows (horizons 0:H) and K^2 shock-major response columns.
% RP retains the existing workbook name for resilience intensity (RI).
% RD uses the existing one-based weights 1:(H+1), including the impact.

validateattributes(girf, {'double'}, {'2d', 'real', 'finite', 'nonempty'});
variable_names = string(variable_names(:));
n_vars = numel(variable_names);
if size(girf, 2) ~= n_vars^2 || numel(unique(variable_names)) ~= n_vars
    error('staticVAR:ResponseShape', 'Supply K unique names and exactly K^2 GIRF columns.');
end
n_points = size(girf, 1);
abs_response = abs(girf);
peak = max(abs_response, [], 1);
total = sum(abs_response, 1);
valid = peak > 0 & total > 0;
rp = nan(1, n_vars^2);
rd = nan(1, n_vars^2);
rp(valid) = (n_points * peak(valid) - total(valid)) ./ (n_points * peak(valid));
rd(valid) = ((1:n_points) * abs_response(:, valid)) ./ total(valid);

% Excel columns C onward map to Var3, Var4, ... in the existing pipeline.
Variable = "Var" + string((3:n_vars^2 + 2)');
Shock = repelem(variable_names, n_vars);
Response = repmat(variable_names, n_vars, 1);
metrics = table(Variable, Shock, Response, rp', rd', ...
    'VariableNames', {'Variable', 'Shock', 'Response', 'RP', 'RD'});
end
