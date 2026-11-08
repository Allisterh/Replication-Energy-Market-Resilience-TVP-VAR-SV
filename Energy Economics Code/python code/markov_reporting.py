"""Final Markov tables and a compact report; no model estimation is performed here."""

from html import escape
from pathlib import Path
import json
import math

import numpy as np
import pandas as pd
from openpyxl.styles import Alignment, Font, PatternFill


def format_workbook(writer):
    """Apply consistent, readable formatting without changing worksheet values."""
    for sheet in writer.sheets.values():
        sheet.freeze_panes = "A2"
        sheet.auto_filter.ref = sheet.dimensions
        sheet.sheet_view.showGridLines = False
        for cell in sheet[1]:
            cell.font = Font(name="Arial", size=10, bold=True, color="FFFFFF")
            cell.fill = PatternFill("solid", fgColor="294D65")
            cell.alignment = Alignment(vertical="center", wrap_text=True)
        sheet.row_dimensions[1].height = 32
        for row in sheet.iter_rows(min_row=2):
            for cell in row:
                cell.font = Font(name="Arial", size=10, color="26323B")
                cell.alignment = Alignment(vertical="center", wrap_text=True)
                if cell.row % 2 == 0:
                    cell.fill = PatternFill("solid", fgColor="F2F5F7")
                if isinstance(cell.value, (float, np.floating)):
                    header = str(sheet.cell(1, cell.column).value).lower()
                    cell.number_format = "0.0000" if not any(
                        word in header for word in ("p_value", "q_value")) else "0.0000E+00"
                if hasattr(cell.value, "year") and hasattr(cell.value, "month"):
                    cell.number_format = "yyyy-mm-dd"
        for column in sheet.columns:
            values = [str(cell.value or "") for cell in column[:300]]
            width = max(len(line) for value in values for line in value.split("\n"))
            sheet.column_dimensions[column[0].column_letter].width = min(34, max(13, width + 2))
        if sheet.title == "Guide":
            sheet.column_dimensions["A"].width = 25
            sheet.column_dimensions["B"].width = 104
        for row in sheet.iter_rows(min_row=2):
            lines = 1
            for cell in row:
                width = sheet.column_dimensions[cell.column_letter].width
                text = "" if cell.value is None else str(cell.value)
                lines = max(lines, sum(max(1, math.ceil(len(line) / max(8, int(width))))
                                       for line in text.split("\n")))
            sheet.row_dimensions[row[0].row].height = max(18, 14 * lines)


def _number(value, places=4):
    if pd.isna(value):
        return "--"
    if np.isinf(value):
        return "infinite"
    return f"{value:,.{places}f}"


def _p_value(value):
    return "--" if pd.isna(value) else ("<0.001" if value < 0.001 else f"{value:.3f}")


def _table(frame):
    return '<div class="table-scroll">' + frame.to_html(index=False, border=0, escape=True) + '</div>'


def write_markov_report(output_dir, paper_tables, model_overview, coefficients,
                        state_mapping_tables, individual_tests, joint_tests,
                        model_warnings, probability_files, input_sha256,
                        appendix_diagnostics=None):
    """Export final results and return one HTML fragment for notebook display."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    intercepts = individual_tests.loc[individual_tests["test_type"] == "intercept"].copy()
    slopes = individual_tests.loc[individual_tests["test_type"] == "slope"].copy()
    selected = slopes.loc[slopes["q_value_bh"] < 0.05].copy()
    def bh_count(frame):
        values = frame.get("q_value_bh", pd.Series(dtype=float))
        return int((values < .05).sum()) if values.notna().any() else pd.NA
    summary = pd.DataFrame([
        {"Test family": "Conditional levels", "Tests": len(intercepts),
         "Raw p < 0.05": int((intercepts.p_value < .05).sum()), "BH q < 0.05": bh_count(intercepts)},
        {"Test family": "Individual slopes", "Tests": len(slopes),
         "Raw p < 0.05": int((slopes.p_value < .05).sum()),
         "BH q < 0.05": int((slopes.q_value_bh < .05).sum())},
        {"Test family": "Joint slopes", "Tests": len(joint_tests),
         "Raw p < 0.05": int((joint_tests.p_value < .05).sum()), "BH q < 0.05": bh_count(joint_tests)},
    ])
    notes = pd.DataFrame({"Item": ["Model", "Economic states", "Coefficient tests",
                                   "BH adjustment", "State duration", "Source consistency"],
                          "Definition": [
        "Two-state Markov regression; switching intercept, four slopes and variance; Nelder-Mead, maxiter=10000.",
        "RI: State 1 has higher absorption. RD: State 1 has faster relative recovery.",
        "Parentheses in coefficient tables contain within-state z-statistics; stars use raw p-values.",
        f"Three independent families: {len(intercepts)} conditional levels, {len(slopes)} individual slopes, {len(joint_tests)} joint slopes. Raw p-values are retained.",
        "Expected months = 1/(1-p_ss), using unrounded staying probabilities; this is distinct from RD.",
        "Tables, probabilities and Wald tests all use the same fitted model objects.",
    ]})
    workbook_path = output_dir / "Markov_results.xlsx"
    with pd.ExcelWriter(workbook_path, engine="openpyxl") as writer:
        notes.to_excel(writer, sheet_name="Guide", index=False)
        model_overview.to_excel(writer, sheet_name="Model_overview", index=False)
        for shock, panels in paper_tables.items():
            for measure, table in panels.items():
                rows = []
                stats = model_overview.loc[(model_overview.shock == shock) & (model_overview.measure == measure)]
                for _, row in table.iterrows():
                    overview = stats.loc[stats.market == row["Market"]].iloc[0]
                    for state in (1, 2):
                        rows.append({"Market": row["Market"], "State": state,
                                     "Conditional mean": row[f"State {state} Cond. mean"],
                                     **{variable: row[f"State {state} {variable}"]
                                        for variable in ("DXY", "GSCPI", "CPI", "Industrial")},
                                     "Persistence": overview[f"p{state}{state}"],
                                     "Expected months": overview[f"expected_months_state{state}"]})
                pd.DataFrame(rows).to_excel(writer, sheet_name=f"{shock}_{measure}", index=False)
        coefficients.to_excel(writer, sheet_name="Coefficients_numeric", index=False)
        summary.to_excel(writer, sheet_name="Test_overview", index=False)
        slopes.to_excel(writer, sheet_name="Slope_differences", index=False)
        intercepts.to_excel(writer, sheet_name="Level_differences", index=False)
        joint_tests.to_excel(writer, sheet_name="Joint_slope_tests", index=False)
        pd.concat(state_mapping_tables.values(), ignore_index=True).to_excel(
            writer, sheet_name="State_mapping", index=False)
        if model_warnings:
            pd.DataFrame(model_warnings).to_excel(writer, sheet_name="Fit_warnings", index=False)
        if appendix_diagnostics is not None:
            for name, frame in appendix_diagnostics.items():
                frame.to_excel(writer, sheet_name=name[:31], index=False)
        format_workbook(writer)

    css = """
    .markov-report {font:14px/1.5 Arial,sans-serif;color:#26323b;max-width:1180px;margin:24px auto;padding:0 20px;}
    .markov-report h1 {font-size:26px;margin:0 0 6px;font-weight:600;}
    .markov-report h2 {font-size:19px;border-bottom:1px solid #cdd7df;padding-bottom:7px;margin-top:30px;}
    .markov-report h3 {font-size:15px;margin:20px 0 8px;}
    .markov-report .note {color:#52616d;font-size:12px;}
    .markov-report .status {background:#f0f4f7;padding:12px 16px;border-left:3px solid #527289;}
    .markov-report .attention {background:#fff4de;padding:12px 16px;border-left:3px solid #b38438;}
    .markov-report .table-scroll {overflow-x:auto;}
    .markov-report table {border-collapse:collapse;width:100%;font-size:12px;margin:8px 0 12px;white-space:nowrap;}
    .markov-report th {background:#e9eff3;font-weight:600;text-align:right;padding:8px 9px;border-bottom:1px solid #b8c8d3;}
    .markov-report td {text-align:right;padding:7px 9px;border-bottom:1px solid #e4eaee;}
    .markov-report th:first-child,.markov-report td:first-child {text-align:left;}
    .markov-report tbody tr:nth-child(even) {background:#f7f9fa;}
    .markov-report details {margin:12px 0;padding:10px 12px;border:1px solid #dce4e9;}
    .markov-report summary {cursor:pointer;font-weight:600;color:#294d65;}
    .markov-report a {color:#24557b;}
    @media print {.markov-report {max-width:none;padding:0;font-size:10pt;} .markov-report table {font-size:8pt;} details {break-inside:avoid;}}
    """
    converged = int(model_overview["converged"].fillna(False).sum())
    nobs = sorted(model_overview["nobs"].unique())
    parts = [f'<style>{css}</style><article class="markov-report">',
             '<h1>Markov regression: final results</h1>',
             '<p class="note">State 1: higher absorption for RI; faster relative recovery for RD. '
             'All tables and probabilities use the same estimation pass.</p>',
             f'<p class="status">{len(model_overview)} models · observations per model: '
             f'{", ".join(map(str, nobs))} · converged: {converged}/{len(model_overview)} · '
             f'individual slopes with BH q &lt; 0.05: {len(selected)}/{len(slopes)}</p>',
             f'<p><a href="{workbook_path.name}">Download the complete results workbook</a></p>']
    if converged != len(model_overview) or model_warnings:
        parts.append(f'<p class="attention">Review optimizer diagnostics: {len(model_warnings)} recorded '
                     'warnings. Convergence status is listed for every model in the workbook.</p>')
    for shock, panels in paper_tables.items():
        parts.append(f'<h2>{escape(shock)}: state levels and persistence</h2>')
        for measure, table in panels.items():
            overview = model_overview.loc[(model_overview.shock == shock) & (model_overview.measure == measure)]
            view = overview[["market", "mean_state1", "mean_state2", "p11", "p22",
                             "expected_months_state1", "expected_months_state2"]].copy()
            for column in ("mean_state1", "mean_state2", "p11", "p22"):
                view[column] = view[column].map(_number)
            for column in ("expected_months_state1", "expected_months_state2"):
                view[column] = view[column].map(lambda x: _number(x, 1))
            view.columns = ["Market", "State 1 mean", "State 2 mean", "p11", "p22", "E(D1), months", "E(D2), months"]
            parts.extend([f'<h3>{measure}</h3>', _table(view)])
            rows = []
            for _, row in table.iterrows():
                for state in (1, 2):
                    rows.append({"Market": row["Market"], "State": state,
                                 "Conditional mean": row[f"State {state} Cond. mean"],
                                 **{var: row[f"State {state} {var}"] for var in ("DXY", "GSCPI", "CPI", "Industrial")}})
            parts.extend([f'<details><summary>{measure}: full coefficient table</summary>',
                          '<p class="note">Estimates with raw within-state significance stars; z-statistics in parentheses.</p>',
                          _table(pd.DataFrame(rows)), '</details>'])
    parts.extend(['<h2>Cross-state inference</h2>', _table(summary.fillna("--")),
                  f'<p class="note">BH adjustment uses three separate families: {len(intercepts)} levels, '
                  f'{len(slopes)} individual slopes and {len(joint_tests)} joint slopes. '
                  'Raw p-values are also retained in the workbook.</p>',
                  '<h3>Individual slope differences retained after BH correction (q &lt; 0.05)</h3>'])
    view = selected[["shock", "measure", "market", "variable", "estimate_state1", "estimate_state2", "p_value", "q_value_bh"]].copy()
    for column in ("estimate_state1", "estimate_state2"):
        view[column] = view[column].map(_number)
    for column in ("p_value", "q_value_bh"):
        view[column] = view[column].map(_p_value)
    view.columns = ["Shock", "Measure", "Market", "Variable", "State 1", "State 2", "Raw p", "BH q"]
    parts.append(_table(view) if len(view) else '<p>No individual slope difference meets q &lt; 0.05.</p>')
    diagnostic_metadata = None
    if appendix_diagnostics is not None:
        diagnostics = appendix_diagnostics
        period = diagnostics["period_indicator"]
        alignment = diagnostics["weighted_alignment"]
        max_difference = float(alignment.absolute_difference.max()) if not alignment.empty else None
        parts.extend(['<h2>Appendix: date sensitivity</h2>',
            '<p class="note">Weighted regressions retain full-sample smoothed state probabilities and '
            'standardization. The primary level indicator starts in January 2021; alternatives start '
            'in March 2020 and February 2022. HAC uses six lags. States are not re-estimated.</p>'])
        if not period.empty:
            view = period[["shock", "measure", "market", "variable"]].copy()
            for state in (1, 2):
                view[f"State {state} with indicator"] = [f"{_number(b)} ({t:.2f})" for b, t in
                    zip(period[f"withD_s{state}"], period[f"withD_s{state}_t"])]
            view["Indicator, State 2"] = [f"{_number(b)} ({t:.2f})" for b, t in
                zip(period.indicator_s2, period.indicator_s2_t)]
            for tag in ("202003", "202101", "202202"):
                view[f"Ratio {tag[:4]}-{tag[4:]}"] = period[f"ratio_{tag}"].map(lambda x: _number(x, 2))
            parts.extend([f'<details><summary>Period-indicator results: {len(period)} selected slope differences</summary>',
                          _table(view), '<p class="note">Parentheses contain unadjusted HAC t-statistics. '
                          'Ratios are signed slope differences relative to the original Markov difference; '
                          'they are not explained-variance shares. No new cross-state tests or BH correction '
                          'are applied to these conditional sensitivity estimates.</p></details>'])
        parts.extend(['<details><summary>Supporting macrofinancial and subsample checks</summary>',
                      _table(diagnostics["macro_summary"]),
                      '<p class="note">The workbook contains the linear HAC benchmark, weighted pre-2021 '
                      'and excluding-2020 regressions, all three indicator dates, and full-sample alignment checks.</p>',
                      '</details>'])
        if max_difference is not None:
            parts.append(f'<p class="note">Maximum absolute slope difference between the no-indicator '
                         f'weighted regressions and the original Markov estimates: {max_difference:.6f}.</p>')
        diagnostic_metadata = dict(selected_slope_differences=len(period), primary_date="2021-01-01",
                                   indicator_dates=["2020-03-01", "2021-01-01", "2022-02-01"],
                                   hac_lags=6, probability_floor=1e-6,
                                   max_weighted_markov_slope_difference=max_difference,
                                   state_process_reestimated=False)
    parts.append('<h2>Probability files for R</h2><ul>')
    for path in probability_files.values():
        name = Path(path).name
        parts.append(f'<li><a href="{escape(name)}">{escape(name)}</a></li>')
    parts.append('</ul><p class="note">Exact estimates, convergence flags, all Wald tests and state mappings are retained in the workbook.</p></article>')
    fragment = "\n".join(parts)
    (output_dir / "Markov_results.html").write_text(
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        '<title>Markov regression: final results</title></head><body>' + fragment + '</body></html>', encoding="utf-8")
    (output_dir / "Markov_run_manifest.json").write_text(json.dumps({
        "input_sha256": input_sha256, "models": len(model_overview),
        "bh_family": "individual slopes (separate level and joint families)", "bh_family_size": len(slopes),
        "bh_significant_slopes_5pct": len(selected), "converged_models": converged,
        "recorded_fit_warnings": len(model_warnings), "one_estimation_pass": True,
        "bh_families": summary.fillna("not available").to_dict(orient="records"),
        "appendix_diagnostics": diagnostic_metadata,
    }, indent=2) + "\n", encoding="utf-8")
    # Notebook links resolve beside Markov.ipynb; the standalone HTML is inside output/.
    return fragment.replace('href="', 'href="output/')
