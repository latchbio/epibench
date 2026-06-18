#!/usr/bin/env python3
"""Failure-divergence analysis across models for the EpiBench whitepaper.

Quantifies how much model failures diverge: the union/oracle pass rate, the
per-eval coverage histogram, and the mean pairwise Jaccard of solved-eval sets.
Reads the per-run pass/fail table (run_results.csv); writes summary CSVs/JSON
next to it and prints the headline numbers for the manuscript text.

Usage:
    python scripts/divergence_analysis.py                  # uses DATA/run_results.csv
    python scripts/divergence_analysis.py --input PATH.csv --outdir DIR
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_figures import DATA, divergence_tables  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", type=Path, default=DATA / "run_results.csv")
    ap.add_argument("--outdir", type=Path, default=DATA)
    args = ap.parse_args()

    df = pd.read_csv(args.input)
    df["passed"] = df["passed"].astype(str).str.lower().isin(["true", "1", "1.0", "yes", "t"])
    args.outdir.mkdir(parents=True, exist_ok=True)

    overall = df["passed"].mean()
    print(f"run_results: {len(df)} rows | {df.eval_name.nunique()} evals | "
          f"{df.model_harness.nunique()} models | overall attempt pass rate {overall*100:.1f}%\n")

    summary = {"overall_attempt_pass_rate": round(float(overall), 4)}
    for threshold in ("majority", "any"):
        coverage, per_model, m = divergence_tables(df, threshold)
        N, M = m["n_evals"], m["n_models"]
        label = "majority (>=2/3 attempts)" if threshold == "majority" else "any (>=1/3 attempts)"
        print(f"===== threshold = {label} =====")
        print(f"  union (>=1 model solves):  {m['union']}/{N} = {100*m['union']/N:.1f}%")
        print(f"  best single model:         {m['best_solved']}/{N} = {100*m['best_solved']/N:.1f}%  ({m['best_model']})")
        print(f"  union - best single:       +{100*(m['union']-m['best_solved'])/N:.1f} pts")
        print(f"  solved by none / all {M}:   {m['universal_fail']}/{N} ({100*m['universal_fail']/N:.0f}%)"
              f" / {m['solved_by_all']}/{N} ({100*m['solved_by_all']/N:.0f}%)")
        print(f"  divergent middle:          {N-m['universal_fail']-m['solved_by_all']}/{N}"
              f" = {100*(N-m['universal_fail']-m['solved_by_all'])/N:.1f}%")
        print(f"  mean pairwise Jaccard:     solved={m['mean_jaccard_solved']:.3f}  failed={m['mean_jaccard_failed']:.3f}\n")
        summary[threshold] = m

        # per-eval coverage (how many models solve each eval)
        cov_df = coverage.rename("n_models_solved").reset_index().sort_values(
            ["n_models_solved", "eval_name"])
        cov_df["frac_models_solved"] = (cov_df["n_models_solved"] / M).round(3)
        cov_df.to_csv(args.outdir / f"divergence_eval_coverage_{threshold}.csv", index=False)

    (args.outdir / "divergence_metrics.json").write_text(json.dumps(summary, indent=2))
    print(f"Wrote divergence_metrics.json, divergence_eval_coverage_*.csv -> {args.outdir}")


if __name__ == "__main__":
    main()
