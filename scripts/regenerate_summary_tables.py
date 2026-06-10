#!/usr/bin/env python3
"""Regenerate EpiBench summary tables using correct task categories from eval_task_categories.tsv.

Reads run_results.csv and field_scores.csv, replaces incorrect task_family values
with correct task_category from eval_task_categories.tsv, then regenerates all
downstream summary tables.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "analysis_outputs" / "epibench_manifest_updated.csv"
TASK_CAT_PATH = ROOT / "analysis_outputs" / "eval_task_categories.tsv"
OUT = ROOT / "analysis_outputs" / "epi_manifest_updated_summary"


def wilson_interval(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n <= 0:
        return (math.nan, math.nan)
    p = successes / n
    denom = 1.0 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt((p * (1.0 - p) + z * z / (4 * n)) / n) / denom
    return max(0.0, center - half), min(1.0, center + half)


def summarize_group(df: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    rows: list[dict] = []
    grouped = [((), df)] if not group_cols else df.groupby(group_cols, dropna=False)
    for key, sub in grouped:
        if not isinstance(key, tuple):
            key = (key,)
        rec = {col: val for col, val in zip(group_cols, key)}
        n_runs = int(len(sub))
        pass_n = int(sub["passed"].sum())
        low, high = wilson_interval(pass_n, n_runs)
        rec.update(
            {
                "n_runs": n_runs,
                "n_evals": int(sub["eval_name"].nunique()),
                "pass_n": pass_n,
                "pass_rate": pass_n / n_runs if n_runs else math.nan,
                "pass_rate_wilson_low": low,
                "pass_rate_wilson_high": high,
                "mean_score": float(sub["score"].mean()) if n_runs else math.nan,
                "median_score": float(sub["score"].median()) if n_runs else math.nan,
                "timeout_rate": float(sub["timed_out"].fillna(False).mean()) if n_runs else math.nan,
                "oom_rate": float(sub["oom_detected"].fillna(False).mean()) if n_runs else math.nan,
                "median_duration_s": float(sub["duration_s"].median()) if sub["duration_s"].notna().any() else math.nan,
                "p90_duration_s": float(sub["duration_s"].quantile(0.9)) if sub["duration_s"].notna().any() else math.nan,
                "mean_duration_s": float(sub["duration_s"].mean()) if sub["duration_s"].notna().any() else math.nan,
                "nonmissing_cost_n": int(sub["total_cost"].notna().sum()),
                "mean_total_cost": float(sub["total_cost"].mean()) if sub["total_cost"].notna().any() else math.nan,
            }
        )
        rows.append(rec)
    return pd.DataFrame(rows)


def main() -> None:
    task_cats = pd.read_csv(TASK_CAT_PATH, sep="\t")
    cat_map = dict(zip(task_cats["eval_name"], task_cats["task_category"]))

    run_results = pd.read_csv(OUT / "run_results.csv")
    for col in ["duration_s", "n_turns", "total_cost", "total_tokens"]:
        run_results[col] = pd.to_numeric(run_results[col], errors="coerce")

    run_results["task_family"] = run_results["eval_name"].map(cat_map)
    unmapped = run_results["task_family"].isna().sum()
    if unmapped > 0:
        missing_evals = run_results.loc[run_results["task_family"].isna(), "eval_name"].unique()
        print(f"WARNING: {unmapped} rows ({len(missing_evals)} evals) have no task_category mapping: {list(missing_evals)[:5]}")
        run_results["task_family"] = run_results["task_family"].fillna("unknown")

    run_results.to_csv(OUT / "run_results.csv", index=False)

    field_scores = pd.read_csv(OUT / "field_scores.csv")
    field_scores["task_family"] = field_scores["eval_name"].map(cat_map)
    field_scores["task_family"] = field_scores["task_family"].fillna("unknown")
    field_scores.to_csv(OUT / "field_scores.csv", index=False)

    eval_inventory = pd.read_csv(OUT / "eval_inventory.csv")
    eval_inventory["task_family"] = eval_inventory["eval_name"].map(cat_map)
    eval_inventory["task_family"] = eval_inventory["task_family"].fillna("unknown")
    eval_inventory.to_csv(OUT / "eval_inventory.csv", index=False)

    # Model summary (unchanged by task remap but regenerate for consistency)
    model_summary = summarize_group(run_results, ["model", "harness", "model_harness"]).sort_values(
        ["pass_rate", "mean_score"], ascending=False
    )
    model_summary.insert(0, "rank_available_runs", np.arange(1, len(model_summary) + 1))
    model_summary.to_csv(OUT / "model_summary_available_runs.csv", index=False)

    # Common instances
    counts = run_results.groupby("instance_id")["model_harness"].nunique()
    common_instances = set(counts[counts == run_results["model_harness"].nunique()].index)
    common = run_results[run_results["instance_id"].isin(common_instances)].copy()
    common_summary = summarize_group(common, ["model", "harness", "model_harness"]).sort_values(
        ["pass_rate", "mean_score"], ascending=False
    )
    common_summary.insert(0, "rank_common_subset", np.arange(1, len(common_summary) + 1))
    common_summary.to_csv(OUT / "model_summary_common_instances.csv", index=False)

    # Group summaries
    for name, cols in {
        "summary_by_kit.csv": ["kit"],
        "summary_by_assay_type.csv": ["assay_type"],
        "summary_by_task_family.csv": ["task_family"],
        "summary_by_time_horizon.csv": ["time_horizon"],
        "summary_by_source_prefix.csv": ["source_prefix"],
        "summary_by_kit_task.csv": ["kit", "task_family"],
        "summary_by_harness_confounded.csv": ["harness"],
        "model_by_kit.csv": ["model_harness", "kit"],
        "model_by_source_prefix.csv": ["model_harness", "source_prefix"],
        "model_by_task_family.csv": ["model_harness", "task_family"],
        "model_by_time_horizon.csv": ["model_harness", "time_horizon"],
    }.items():
        summarize_group(run_results, cols).sort_values(cols).to_csv(OUT / name, index=False)

    # Eval difficulty
    eval_difficulty = summarize_group(run_results, ["eval_name", "source_prefix", "kit", "task_family", "time_horizon", "grader_type"])
    eval_difficulty.sort_values(["pass_rate", "mean_score", "eval_name"]).to_csv(OUT / "eval_difficulty.csv", index=False)

    # Replicate analysis
    replicate = (
        run_results.groupby(["model", "harness", "model_harness", "eval_name", "kit", "task_family", "time_horizon"], as_index=False)
        .agg(
            n_attempts=("passed", "size"),
            pass_n=("passed", "sum"),
            mean_score=("score", "mean"),
        )
    )
    replicate["pass_fraction"] = replicate["pass_n"] / replicate["n_attempts"]
    replicate["any_pass"] = replicate["pass_n"] >= 1
    replicate["majority_pass"] = replicate["pass_n"] >= np.floor(replicate["n_attempts"] / 2) + 1
    replicate["all_pass"] = replicate["pass_n"] == replicate["n_attempts"]
    replicate.to_csv(OUT / "model_eval_replicate_results.csv", index=False)

    robustness = (
        replicate.groupby(["model", "harness", "model_harness"], as_index=False)
        .agg(
            n_eval_model_pairs=("eval_name", "nunique"),
            mean_attempts_per_eval=("n_attempts", "mean"),
            any_pass_rate=("any_pass", "mean"),
            majority_pass_rate=("majority_pass", "mean"),
            all_pass_rate=("all_pass", "mean"),
            mean_eval_pass_fraction=("pass_fraction", "mean"),
            mean_eval_score=("mean_score", "mean"),
        )
        .sort_values(["mean_eval_pass_fraction", "mean_eval_score"], ascending=False)
    )
    robustness.to_csv(OUT / "replicate_robustness_by_model.csv", index=False)

    # Field score summaries
    if not field_scores.empty:
        (
            field_scores.groupby("field", as_index=False)
            .agg(
                n_field_scores=("field_score", "size"),
                mean_field_score=("field_score", "mean"),
                field_pass_rate=("field_passed", "mean"),
                n_evals=("eval_name", "nunique"),
            )
            .sort_values(["field_pass_rate", "mean_field_score", "field"])
            .to_csv(OUT / "field_score_summary.csv", index=False)
        )
        (
            field_scores.groupby(["kit", "task_family"], as_index=False)
            .agg(
                n_field_scores=("field_score", "size"),
                mean_field_score=("field_score", "mean"),
                field_pass_rate=("field_passed", "mean"),
                n_fields=("field", "nunique"),
                n_evals=("eval_name", "nunique"),
            )
            .sort_values(["kit", "task_family"])
            .to_csv(OUT / "field_score_by_kit_task.csv", index=False)
        )

    # Failure mode summaries
    eval_failure_modes = pd.read_csv(OUT / "eval_failure_modes.csv")
    if not eval_failure_modes.empty:
        fail_runs = run_results.merge(eval_failure_modes, on="eval_name", how="inner")
        summarize_group(fail_runs, ["failure_mode"]).sort_values(["n_evals", "pass_rate"], ascending=[False, True]).to_csv(
            OUT / "summary_by_failure_mode.csv", index=False
        )
        summarize_group(fail_runs, ["model_harness", "failure_mode"]).sort_values(["model_harness", "failure_mode"]).to_csv(
            OUT / "model_by_failure_mode.csv", index=False
        )

    # Summary facts
    manifest = pd.read_csv(MANIFEST_PATH)
    full_design_runs = int(manifest["eval_name"].nunique() * manifest["round"].nunique())
    summary_facts = {
        "manifest": str(MANIFEST_PATH),
        "manifest_sha256": hashlib.sha256(MANIFEST_PATH.read_bytes()).hexdigest(),
        "manifest_rows": int(len(manifest)),
        "evals": int(run_results["eval_name"].nunique()),
        "model_harnesses": int(run_results["model_harness"].nunique()),
        "full_design_runs_per_pair": full_design_runs,
        "common_instances": int(len(common_instances)),
        "common_rows": int(len(common)),
        "total_pass": int(run_results["passed"].sum()),
        "total_runs": int(len(run_results)),
        "overall_pass_rate": float(run_results["passed"].mean()),
        "field_pass_weighted": float(field_scores["field_passed"].mean()) if not field_scores.empty else math.nan,
        "eval_zero_pass": int((eval_difficulty["pass_n"] == 0).sum()),
        "eval_under_10": int((eval_difficulty["pass_rate"] < 0.10).sum()),
        "eval_all_pass": int((eval_difficulty["pass_rate"] == 1.0).sum()),
        "eval_over_90": int((eval_difficulty["pass_rate"] >= 0.90).sum()),
        "top_available": model_summary.head(5).to_dict(orient="records"),
        "by_kit": summarize_group(run_results, ["kit"]).sort_values("pass_rate", ascending=False).to_dict(orient="records"),
        "by_task": summarize_group(run_results, ["task_family"]).sort_values("pass_rate", ascending=False).to_dict(orient="records"),
        "by_horizon": summarize_group(run_results, ["time_horizon"]).sort_values("pass_rate", ascending=False).to_dict(orient="records"),
    }
    (OUT / "summary_facts.json").write_text(json.dumps(summary_facts, indent=2))
    (OUT / "README.md").write_text(
        f"# EpigeneticsBench Updated Manifest Summary\n\n"
        f"Manifest: `{MANIFEST_PATH.name}`\n\n"
        f"SHA256: `{summary_facts['manifest_sha256']}`\n\n"
        f"Rows: {summary_facts['total_runs']} result attempts; evals: {summary_facts['evals']}; "
        f"model-harness pairs: {summary_facts['model_harnesses']}.\n\n"
        f"Balanced design: {summary_facts['full_design_runs_per_pair']} attempts per model-harness pair.\n\n"
        f"Task categories from: `eval_task_categories.tsv`\n\n"
        f"These files are derived summary tables used by the manuscript. They do not\n"
        f"include the raw downloaded trajectory or result JSON cache.\n"
    )

    print("Task category distribution:")
    print(run_results["task_family"].value_counts().to_string())
    print(f"\nTotal runs: {summary_facts['total_runs']}")
    print(f"Overall pass rate: {summary_facts['overall_pass_rate']:.4f}")
    print(f"Evals: {summary_facts['evals']}")
    print("Done.")


if __name__ == "__main__":
    main()
