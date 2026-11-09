function model = static_var_fit(y, lag_order, max_horizon)
%STATIC_VAR_FIT Estimate an intercept VAR by OLS and calculate generalized IRFs.
% y is T-by-K, already standardized in the same way as the TVP-VAR input.
% GIRF columns are shock-major: all K responses to shock 1, then shock 2, etc.

validateattributes(y, {'double'}, {'2d', 'real', 'finite', 'nonempty'});
validateattributes(lag_order, {'numeric'}, {'scalar', 'integer', 'positive'});
validateattributes(max_horizon, {'numeric'}, {'scalar', 'integer', 'nonnegative'});
[n_obs, n_vars] = size(y);
n_effective = n_obs - lag_order;
n_regressors = 1 + n_vars * lag_order;
residual_df = n_effective - n_regressors;
if residual_df <= 0
    error('staticVAR:SampleSize', 'Too few observations for the selected VAR lag order.');
end

x = ones(n_effective, n_regressors);
for ell = 1:lag_order
    cols = 2 + (ell - 1) * n_vars : 1 + ell * n_vars;
    x(:, cols) = y(lag_order + 1 - ell:n_obs - ell, :);
end
if rank(x) < n_regressors
    error('staticVAR:Rank', 'The VAR design matrix is rank deficient.');
end
beta = x \ y(lag_order + 1:end, :);
residuals = y(lag_order + 1:end, :) - x * beta;
sigma = (residuals' * residuals) / residual_df;
sigma = (sigma + sigma') / 2;
[~, covariance_flag] = chol(sigma);
if covariance_flag ~= 0
    error('staticVAR:Covariance', 'The estimated innovation covariance is not positive definite.');
end

ar = zeros(n_vars, n_vars, lag_order);
for ell = 1:lag_order
    cols = 2 + (ell - 1) * n_vars : 1 + ell * n_vars;
    ar(:, :, ell) = beta(cols, :)';
end
companion = zeros(n_vars * lag_order);
companion(1:n_vars, :) = reshape(ar, n_vars, []);
if lag_order > 1
    companion(n_vars + 1:end, 1:end - n_vars) = eye(n_vars * (lag_order - 1));
end
spectral_radius = max(abs(eig(companion)));
if spectral_radius >= 1
    warning('staticVAR:Unstable', ...
        'The fitted VAR is not stable (spectral radius %.6f). Finite-horizon responses are still exported.', ...
        spectral_radius);
end

% Column j is Sigma*e_j/sqrt(Sigma(j,j)); no orthogonalized shock is used.
impact = sigma ./ sqrt(diag(sigma))';
girf = zeros(max_horizon + 1, n_vars^2);
companion_power = eye(n_vars * lag_order);
for h = 0:max_horizon
    propagation = companion_power(1:n_vars, 1:n_vars);
    response = propagation * impact;
    girf(h + 1, :) = response(:)';
    companion_power = companion * companion_power;
end

model = struct('Beta', beta, 'Intercept', beta(1, :)', 'AR', ar, ...
    'Sigma', sigma, 'Residuals', residuals, 'GIRF', girf, ...
    'LagOrder', lag_order, 'MaxHorizon', max_horizon, ...
    'NObservations', n_obs, 'NEffective', n_effective, ...
    'NRegressors', n_regressors, 'ResidualDF', residual_df, ...
    'SpectralRadius', spectral_radius);
end
