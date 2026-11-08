"""Supplementary conditional diagnostics using the existing full-sample fits.

No Markov model is estimated here. The state probabilities and standardized
conditioning variables remain fixed in every weighted sensitivity regression.
"""

import numpy as np
import pandas as pd
import statsmodels.api as sm


HAC_LAGS = 6
PROBABILITY_FLOOR = 1e-6
PRIMARY_DATE = "2021-01-01"
INDICATOR_DATES = ("2020-03-01", PRIMARY_DATE, "2022-02-01")
EXCLUDED_START, EXCLUDED_END = "2020-03-01", "2020-12-01"
EXOG_COLUMNS = ("DXY", "GSCPI", "CPI", "Industrial")


def _hac_fit(y, design, weights=None, maxlags=HAC_LAGS):
    model = sm.OLS(y, design) if weights is None else sm.WLS(y, design, weights=weights)
    return model.fit(cov_type="HAC", cov_kwds={"maxlags": maxlags,
                                             "use_correction": False}, use_t=False)


def _state_probability(result, raw_state):
    probabilities = result.smoothed_marginal_probabilities
    if isinstance(probabilities, pd.DataFrame):
        values = probabilities.iloc[:, raw_state].to_numpy(dtype=float)
    else:
        values = np.asarray(probabilities, dtype=float)
        if values.shape[0] != int(result.nobs):
            values = values.T
        values = values[:, raw_state]
    if not np.isfinite(values).all() or np.any((values < -1e-10) | (values > 1 + 1e-10)):
        raise ValueError("Supplementary diagnostics require valid smoothed probabilities.")
    # Preserve the 1e-6 numerical floor in the scripts used to construct the
    # appendix. This copy is not written back to the probability workbooks.
    return np.clip(values, PROBABILITY_FLOOR, 1 - PROBABILITY_FLOOR)


def run_appendix_diagnostics(results, probability_tables, state_mapping_tables,
                            conditioning_data, coefficients, individual_tests):
    """Return the three supplementary diagnostic tables and full numeric detail."""
    conditioning = conditioning_data[["date", *EXOG_COLUMNS]].copy()
    conditioning["date"] = pd.to_datetime(conditioning["date"], utc=True).dt.tz_convert(None)
    if conditioning["date"].duplicated().any():
        raise ValueError("Conditioning dates must be unique for the diagnostic date merge.")
    selected = individual_tests.loc[(individual_tests.test_type == "slope") &
                                    (individual_tests.q_value_bh < .05)].copy()
    fitted, exposure_rows, linear_rows, sample_rows = {}, [], [], []
    for shock, measures in results.items():
        mappings = state_mapping_tables[shock]
        for measure, markets in measures.items():
            for market, result in markets.items():
                key = {"shock": shock, "measure": measure, "market": market}
                mask = (probability_tables[shock].measure == measure) & (probability_tables[shock].market == market)
                sample = probability_tables[shock].loc[mask, ["date", "metric_value"]].copy()
                sample["date"] = pd.to_datetime(sample["date"], utc=True).dt.tz_convert(None)
                sample = sample.merge(conditioning, on="date", how="left", validate="one_to_one").sort_values("date")
                if len(sample) != int(result.nobs) or sample.isna().any().any():
                    raise ValueError(f"Diagnostic observations do not match the fitted model: {key}")
                y = sample.metric_value.to_numpy(dtype=float)
                x = sample[list(EXOG_COLUMNS)].to_numpy(dtype=float)
                design = np.column_stack([np.ones(len(y)), x])
                if not np.allclose(np.asarray(result.model.exog), design, rtol=0, atol=1e-12):
                    raise ValueError(f"Diagnostic conditioning vectors differ from the original fit: {key}")
                if not np.allclose(np.asarray(result.model.endog), y - y.mean(), rtol=0, atol=1e-12):
                    raise ValueError(f"Diagnostic outcomes differ from the original fit: {key}")
                mapping = mappings.loc[(mappings.measure == measure) & (mappings.market == market)].iloc[0]
                p1 = _state_probability(result, int(mapping.state1_raw))
                dates = pd.DatetimeIndex(sample.date)
                pre = dates < PRIMARY_DATE
                keep = ~((dates >= EXCLUDED_START) & (dates <= EXCLUDED_END))
                local = coefficients.loc[(coefficients.shock == shock) &
                                         (coefficients.measure == measure) &
                                         (coefficients.market == market)]
                beta = {state: local.loc[local.state == state].set_index("term").loc[
                    list(EXOG_COLUMNS), "estimate"].to_numpy(dtype=float) for state in (1, 2)}
                linear = _hac_fit(y, design)
                for i, variable in enumerate(EXOG_COLUMNS, 1):
                    linear_rows.append({**key, "variable": variable, "estimate": linear.params[i],
                                        "hac_t": linear.tvalues[i], "p_value": linear.pvalues[i]})
                exposure_rows.append({**key,
                    **{f"sd_state{state}": float(np.std(x @ beta[state], ddof=0)) for state in (1, 2)},
                    **{f"sd_excl2020_state{state}": float(np.std(x[keep] @ beta[state], ddof=0)) for state in (1, 2)}})
                sample_rows.append({**key, "n_full": len(y), "n_pre2021": int(pre.sum()),
                                    "n_excl2020": int(keep.sum()),
                                    **{f"n_indicator_{date[:7]}": int((dates >= date).sum()) for date in INDICATOR_DATES}})
                fitted[(shock, measure, market)] = dict(y=y, x=x, design=design, dates=dates,
                    p1=p1, beta=beta, linear=linear, pre=pre, keep=keep)

    exposure = pd.DataFrame(exposure_rows)
    linear_table = pd.DataFrame(linear_rows)
    slope_coefficients = coefficients.loc[coefficients.term.isin(EXOG_COLUMNS)]
    counts = slope_coefficients.loc[slope_coefficients.p_value < .05].groupby("state").size()
    linear_counts = linear_table.loc[linear_table.p_value < .05].groupby("variable").size()
    macro_summary = pd.DataFrame([
        {"diagnostic": "greater_dispersion_full", "value": int((exposure.sd_state2 > exposure.sd_state1).sum())},
        {"diagnostic": "greater_dispersion_excl2020", "value": int((exposure.sd_excl2020_state2 > exposure.sd_excl2020_state1).sum())},
        *[{"diagnostic": f"within_state{state}_detections", "value": int(counts.get(state, 0))} for state in (1, 2)],
        *[{"diagnostic": f"linear_{variable}_detections", "value": int(linear_counts.get(variable, 0))} for variable in EXOG_COLUMNS],
    ])

    subsample_rows, period_rows, detail_rows, alignment_rows = [], [], [], []
    for _, test in selected.iterrows():
        key = {name: test[name] for name in ("shock", "measure", "market", "variable")}
        data = fitted[(test.shock, test.measure, test.market)]
        position = EXOG_COLUMNS.index(test.variable) + 1
        ms = {state: data["beta"][state][position - 1] for state in (1, 2)}
        baseline_gap = ms[2] - ms[1]
        if not np.isfinite(baseline_gap) or baseline_gap == 0:
            raise ValueError(f"A selected slope difference has an undefined ratio: {key}")
        row = {**key, "linear": data["linear"].params[position],
               "linear_p": data["linear"].pvalues[position], "ms_s1": ms[1], "ms_s2": ms[2]}
        for label, mask in (("full", np.ones(len(data["y"]), dtype=bool)),
                            ("pre2021", data["pre"]), ("excl2020", data["keep"])):
            # Retained observations become adjacent for HAC after the 2020 rows
            # are removed, exactly as stated in the supplementary table notes.
            for state, weights in ((1, data["p1"]), (2, 1 - data["p1"])):
                fit = _hac_fit(data["y"][mask], data["design"][mask], weights[mask])
                row[f"{label}_s{state}"] = fit.params[position]
                row[f"{label}_s{state}_t"] = fit.tvalues[position]
                if label == "full":
                    alignment_rows.append({**key, "state": state, "markov_slope": ms[state],
                        "weighted_slope": fit.params[position],
                        "absolute_difference": abs(fit.params[position] - ms[state])})
        subsample_rows.append(row)

        period = {**key, "ms_s1": ms[1], "ms_s2": ms[2]}
        for date in INDICATOR_DATES:
            indicator = (data["dates"] >= date).astype(float)
            design = np.column_stack([data["design"], indicator])
            fits = {state: _hac_fit(data["y"], design, weights) for state, weights in (
                (1, data["p1"]), (2, 1 - data["p1"]))}
            gap = fits[2].params[position] - fits[1].params[position]
            ratio = gap / baseline_gap
            tag = date[:7].replace("-", "")
            period[f"ratio_{tag}"] = ratio
            detail = {**key, "indicator_start": date, "nobs": len(indicator),
                      "n_indicator": int(indicator.sum()), "difference_ms_s2_minus_s1": baseline_gap,
                      "difference_indicator_s2_minus_s1": gap, "signed_ratio": ratio}
            for state, fit in fits.items():
                detail.update({f"slope_s{state}": fit.params[position], f"slope_s{state}_t": fit.tvalues[position],
                               f"indicator_s{state}": fit.params[-1], f"indicator_s{state}_t": fit.tvalues[-1]})
                if date == PRIMARY_DATE:
                    period.update({f"withD_s{state}": fit.params[position], f"withD_s{state}_t": fit.tvalues[position],
                                   f"indicator_s{state}": fit.params[-1], f"indicator_s{state}_t": fit.tvalues[-1]})
            detail_rows.append(detail)
        period_rows.append(period)

    parameters = pd.DataFrame([
        {"setting": "HAC lags", "value": HAC_LAGS},
        {"setting": "HAC kernel", "value": "Bartlett"},
        {"setting": "HAC small-sample correction", "value": False},
        {"setting": "HAC normal reference (use_t)", "value": False},
        {"setting": "Probability floor", "value": PROBABILITY_FLOOR},
        {"setting": "Primary indicator starts", "value": PRIMARY_DATE},
        {"setting": "Alternative indicator dates", "value": ", ".join(d for d in INDICATOR_DATES if d != PRIMARY_DATE)},
        {"setting": "Standardization", "value": "Existing full-sample standardized X; no subset rescaling"},
        {"setting": "Latent states", "value": "Existing full-sample smoothed probabilities; no state refit"},
        {"setting": "Selection", "value": "Original individual-slope BH q < 0.05; no new BH adjustment"},
        {"setting": "Ratio", "value": "(beta_2,D - beta_1,D) / (beta_2,MS - beta_1,MS); signed"},
    ])
    return dict(macro_summary=macro_summary, fitted_dispersion=exposure, linear_hac=linear_table,
                subsample_checks=pd.DataFrame(subsample_rows), period_indicator=pd.DataFrame(period_rows),
                indicator_dates=pd.DataFrame(detail_rows), weighted_alignment=pd.DataFrame(alignment_rows),
                diagnostic_samples=pd.DataFrame(sample_rows), diagnostic_settings=parameters)
