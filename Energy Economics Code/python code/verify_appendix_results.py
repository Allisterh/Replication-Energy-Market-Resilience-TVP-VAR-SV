"""Compare generated results with the numerical entries in supplied TeX tables.

This optional checker reads the manuscript; estimation never imports its values.
Run with --appendix-tex /path/to/Supplementary_Appendix.tex and, optionally,
--main-tex /path/to/main_J1108.tex. A mismatch produces a nonzero exit status.
"""

from pathlib import Path
import argparse
import hashlib
import json
import re

import numpy as np
import pandas as pd


KEYS = ["shock", "measure", "market", "variable"]
NUMBER = re.compile(r"[+-]?(?:\d+\.\d+|\d+)")


def _region(text, label):
    start = text.index("\\label{" + label + "}")
    end = text.index("\\end{table}", start)
    return text[start:end]


def _numbers(cell):
    # The [-1pt] spacing command must not be interpreted as a table value.
    return NUMBER.findall(re.sub(r"\[[^\]]*\]", "", cell))


def _data_rows(text):
    rows = []
    for line in text.splitlines():
        if re.match(r"^(GPR|CPU|OPU)\s*&\s*(RI|RD)\s*&", line):
            rows.append([cell.strip() for cell in line.split(" & ")])
    if not rows:
        raise ValueError("No numerical rows were found in a requested TeX diagnostic table.")
    return rows


def verify_results(appendix_tex, workbook, main_tex=None):
    """Return one comparison record per displayed value or significance label."""
    text = Path(appendix_tex).read_text(encoding="utf-8")
    sheets = pd.read_excel(workbook, sheet_name=None)
    records = []

    def compare(table, case, field, displayed, computed, operator="rounded"):
        expected = float(displayed)
        computed = float(computed)
        decimals = len(displayed.split(".")[1]) if "." in displayed else 0
        tolerance = 0.5 * 10 ** (-decimals) + 1e-12
        if operator == "lt":
            match = np.isfinite(computed) and computed < expected
        elif operator == "le":
            match = np.isfinite(computed) and computed <= expected + 1e-12
        else:
            match = np.isfinite(computed) and abs(computed - expected) <= tolerance
        records.append(dict(table=table, case=case, field=field, expected_display=displayed,
                            computed=computed, difference=computed - expected,
                            tolerance=tolerance if operator == "rounded" else np.nan,
                            comparison=operator, match=bool(match)))

    specifications = [
        ("tab:period_indicator", "period_indicator", {
            4: ["ms_s1"], 5: ["ms_s2"], 6: ["withD_s1", "withD_s1_t"],
            7: ["withD_s2", "withD_s2_t"], 8: ["indicator_s2", "indicator_s2_t"],
            9: ["ratio_202003"], 10: ["ratio_202101"], 11: ["ratio_202202"]}),
        ("tab:macro_subsample_diagnostics", "subsample_checks", {
            4: ["linear", "linear_p"], 5: ["ms_s1"], 6: ["ms_s2"],
            7: ["pre2021_s1", "pre2021_s1_t"], 8: ["pre2021_s2", "pre2021_s2_t"],
            9: ["excl2020_s1", "excl2020_s1_t"], 10: ["excl2020_s2", "excl2020_s2_t"]}),
    ]
    for label, sheet, fields in specifications:
        calculated = sheets[sheet].set_index(KEYS)
        seen = set()
        for cells in _data_rows(_region(text, label)):
            key = tuple(cells[:4])
            seen.add(key)
            if key not in calculated.index:
                raise ValueError(f"A manuscript case is absent from the generated results: {key}")
            row = calculated.loc[key]
            for column, names in fields.items():
                values = _numbers(cells[column])
                if len(values) != len(names):
                    raise ValueError(f"Unexpected numerical format: {label}/{key}/{cells[column]}")
                for field, value in zip(names, values):
                    operator = "lt" if field == "linear_p" and "<" in cells[column] else "rounded"
                    compare(label, "-".join(key), field, value, row[field], operator)
        if seen != set(calculated.index):
            raise ValueError(f"The generated and manuscript case sets differ for {label}.")

    macro = _region(text, "tab:macro_diagnostic_summary")
    counts = sheets["macro_summary"].set_index("diagnostic")["value"]
    for line in macro.splitlines():
        if "greater fitted" in line or "same comparison, omitting" in line:
            field = "greater_dispersion_full" if "greater fitted" in line else "greater_dispersion_excl2020"
            value, total = re.search(r"&\s*(\d+)\s+of\s+(\d+)", line).groups()
            compare("tab:macro_diagnostic_summary", "all models", field, value, counts[field])
            compare("tab:macro_diagnostic_summary", "all models", "regressions", total, len(sheets["fitted_dispersion"]))
        elif "Within-state slope detections" in line:
            for state in (1, 2):
                value = re.search(r"State~" + str(state) + r":\s*(\d+)", line).group(1)
                field = f"within_state{state}_detections"
                compare("tab:macro_diagnostic_summary", "all models", field, value, counts[field])
        elif "Linear OLS--HAC coefficient detections" in line:
            for variable in ("DXY", "GSCPI", "CPI", "Industrial"):
                value = re.search(r"\b" + re.escape(variable) + r":\s*(\d+)", line).group(1)
                field = f"linear_{variable}_detections"
                compare("tab:macro_diagnostic_summary", "all models", field, value, counts[field])

    compare("tab:period_indicator", "all selected slopes", "maximum_weighted_alignment_error",
            "0.002", sheets["weighted_alignment"].absolute_difference.max(), "le")
    for field, value in {"n_full": 166, "n_pre2021": 131, "n_excl2020": 156,
                         "n_indicator_2021-01": 35}.items():
        for _, row in sheets["diagnostic_samples"].iterrows():
            compare("sample sizes", "-".join(str(row[k]) for k in KEYS[:3]), field, str(value), row[field])

    if main_tex is not None:
        main = Path(main_tex).read_text(encoding="utf-8")
        restrictions = [("intercept", r"\mu_1=\mu_2", sheets["Level_differences"]),
                        ("joint slopes", r"\bm{\beta}_1=\bm{\beta}_2", sheets["Joint_slope_tests"])]
        for shock in ("GPR", "CPU", "OPU"):
            body = _region(main, f"tab:ms_{shock.lower()}")
            panel = body[body.index("Panel C: Wald tests"):]
            for measure in ("RI", "RD"):
                for restriction, expression, frame in restrictions:
                    label = measure + ": $" + expression + "$"
                    tail = panel.split(label, 1)[1]
                    cells = tail[:tail.index(r"\\")].split("&")[1:]
                    if len(cells) != 5:
                        raise ValueError(f"Expected five markets in Panel C: {shock}/{measure}/{restriction}")
                    for market, cell in zip(("OIL", "NG", "COAL", "ERIX", "EUA"), cells):
                        row = frame.loc[(frame.shock == shock) & (frame.measure == measure) & (frame.market == market)].iloc[0]
                        case = f"{shock}-{measure}-{market}-{restriction}"
                        compare("main Panel C", case, "wald_chi2", _numbers(cell)[0], row.wald_chi2)
                        expected = re.search(r"\^\{(\*+)\}", cell)
                        expected = expected.group(1) if expected else ""
                        computed = "" if pd.isna(row.stars_q) else row.stars_q
                        records.append(dict(table="main Panel C", case=case, field="BH significance stars",
                                            expected_display=expected, computed=computed,
                                            difference=np.nan, tolerance=np.nan, comparison="exact",
                                            match=expected == computed))
    return pd.DataFrame(records)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--appendix-tex", type=Path, required=True)
    parser.add_argument("--main-tex", type=Path)
    parser.add_argument("--results", type=Path, default=Path(__file__).resolve().parent / "output/Markov_results.xlsx")
    args = parser.parse_args()
    comparisons = verify_results(args.appendix_tex, args.results, args.main_tex)
    destination = args.results.parent
    comparisons.to_csv(destination / "Appendix_verification.csv", index=False)
    sources = [args.appendix_tex, *([args.main_tex] if args.main_tex is not None else [])]
    summary = dict(comparisons=len(comparisons), matched=int(comparisons.match.sum()),
                   mismatched=int((~comparisons.match).sum()),
                   by_table=comparisons.groupby("table").agg(comparisons=("match", "size"), matched=("match", "sum")).to_dict("index"),
                   source_sha256={p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sources})
    (destination / "Appendix_verification.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    if not comparisons.match.all():
        print(comparisons.loc[~comparisons.match].to_string(index=False))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
