#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = Path.home() / "Downloads" / "epibench_manifest_updated.csv"
DEFAULT_CACHE = ROOT / ".scratch" / "epi_outputs_updated"
DEFAULT_OUT = ROOT / "analysis_outputs" / "epi_manifest_updated_summary"


def source_prefix(eval_name: str) -> str:
    if eval_name.startswith("gse149608_"):
        return "gse149608"
    if eval_name.startswith("gse149609_"):
        return "gse149609"
    return eval_name.split("_", 1)[0]


def load_json(path: Path) -> dict[str, Any]:
    with path.open() as fh:
        return json.load(fh)


def wilson_interval(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n <= 0:
        return (math.nan, math.nan)
    p = successes / n
    denom = 1.0 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt((p * (1.0 - p) + z * z / (4 * n)) / n) / denom
    return max(0.0, center - half), min(1.0, center + half)


def summarize_group(df: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
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


def total_tokens(usage: Any) -> float:
    if not isinstance(usage, dict):
        return math.nan
    return float(sum(v for v in usage.values() if isinstance(v, (int, float))))


def main() -> None:
    parser = argparse.ArgumentParser(description="Build EpigeneticsBench summary tables from a manifest and cached JSONs.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    manifest = pd.read_csv(args.manifest)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    eval_meta: dict[str, dict[str, Any]] = {}
    eval_failure_rows: list[dict[str, str]] = []
    for eval_name in sorted(manifest["eval_name"].unique()):
        path = args.cache_dir / "evals" / f"{eval_name}.json"
        obj = load_json(path)
        md = obj.get("metadata") or {}
        failure_modes = md.get("failure_modes") or []
        eval_meta[eval_name] = {
            "eval_name": eval_name,
            "source_prefix": source_prefix(eval_name),
            "eval_type": md.get("eval_type"),
            "metadata_kit": md.get("kit"),
            "task_family": md.get("task"),
            "time_horizon": md.get("time_horizon"),
            "grader_type": (obj.get("grader") or {}).get("type"),
            "data_node_count": len(obj.get("data_node") or []),
            "task_chars": len(obj.get("task") or ""),
            "has_failure_modes": bool(failure_modes),
            "failure_mode_count": len(failure_modes),
        }
        for mode in failure_modes:
            eval_failure_rows.append({"eval_name": eval_name, "failure_mode": mode})

    run_rows: list[dict[str, Any]] = []
    field_rows: list[dict[str, Any]] = []
    for row in manifest.itertuples(index=False):
        result_path = args.cache_dir / "results" / row.model_harness / f"{row.eval_name}__{row.round}.json"
        obj = load_json(result_path)
        result = obj.get("result") or {}
        grader = result.get("grader_result") or {}
        md = result.get("metadata") or {}
        eval_info = eval_meta[row.eval_name]
        passed = bool(grader.get("passed", result.get("passed", False)))
        score = grader.get("score")
        if score is None:
            score = 1.0 if passed else 0.0
        usage = md.get("usage")
        rec = {
            "model": row.model,
            "harness": row.harness,
            "model_harness": row.model_harness,
            "eval_name": row.eval_name,
            "round": row.round,
            "trial_index": obj.get("trial_index"),
            "model_name_result": obj.get("model_name"),
            "harness_result": obj.get("harness"),
            "passed": passed,
            "score": float(score),
            "duration_s": md.get("duration_s", obj.get("agent_runtime_seconds")),
            "timed_out": bool(md.get("timed_out", False)),
            "oom_detected": bool(md.get("oom_detected", False)),
            "oom_restarts": md.get("oom_restarts", 0),
            "n_turns": md.get("n_turns"),
            "total_cost": md.get("total_cost"),
            "total_tokens": total_tokens(usage),
            "result_path": str(result_path),
            "source_result_json_path": row.source_result_json_path,
            "source_prefix": eval_info["source_prefix"],
            "eval_type": eval_info["eval_type"],
            "kit": row.assay_type,
            "assay_type": row.assay_type,
            "metadata_kit": eval_info["metadata_kit"],
            "task_family": eval_info["task_family"],
            "time_horizon": eval_info["time_horizon"],
            "grader_type": eval_info["grader_type"],
            "data_node_count": eval_info["data_node_count"],
            "task_chars": eval_info["task_chars"],
            "has_failure_modes": eval_info["has_failure_modes"],
            "failure_mode_count": eval_info["failure_mode_count"],
            "instance_id": f"{row.eval_name}__{row.round}",
        }
        run_rows.append(rec)

        field_scores = grader.get("field_scores") or {}
        if isinstance(field_scores, dict):
            for field, field_score in field_scores.items():
                try:
                    numeric = float(field_score)
                except (TypeError, ValueError):
                    numeric = math.nan
                field_rows.append(
                    {
                        "model_harness": row.model_harness,
                        "model": row.model,
                        "harness": row.harness,
                        "eval_name": row.eval_name,
                        "round": row.round,
                        "field": field,
                        "field_score": numeric,
                        "field_passed": bool(numeric >= 1.0) if not math.isnan(numeric) else False,
                        "kit": row.assay_type,
                        "assay_type": row.assay_type,
                        "task_family": eval_info["task_family"],
                        "time_horizon": eval_info["time_horizon"],
                        "source_prefix": eval_info["source_prefix"],
                    }
                )

    run_results = pd.DataFrame(run_rows)
    for col in ["duration_s", "n_turns", "total_cost", "total_tokens"]:
        run_results[col] = pd.to_numeric(run_results[col], errors="coerce")
    run_results.to_csv(args.out_dir / "run_results.csv", index=False)

    eval_inventory = pd.DataFrame(eval_meta.values()).sort_values("eval_name")
    assay_map = manifest[["eval_name", "assay_type"]].drop_duplicates("eval_name")
    eval_inventory = eval_inventory.merge(assay_map, on="eval_name", how="left")
    eval_inventory["kit"] = eval_inventory["assay_type"]
    eval_inventory.to_csv(args.out_dir / "eval_inventory.csv", index=False)

    pd.DataFrame(eval_failure_rows).to_csv(args.out_dir / "eval_failure_modes.csv", index=False)

    model_summary = summarize_group(run_results, ["model", "harness", "model_harness"]).sort_values(
        ["pass_rate", "mean_score"], ascending=False
    )
    model_summary.insert(0, "rank_available_runs", np.arange(1, len(model_summary) + 1))
    model_summary.to_csv(args.out_dir / "model_summary_available_runs.csv", index=False)

    full_design_runs = int(manifest["eval_name"].nunique() * manifest["round"].nunique())
    coverage = (
        run_results.groupby(["model", "harness", "model_harness"], as_index=False)
        .agg(n_runs=("passed", "size"), n_evals=("eval_name", "nunique"), n_instances=("instance_id", "nunique"))
    )
    coverage["full_design_runs"] = full_design_runs
    coverage["missing_from_full_design"] = coverage["full_design_runs"] - coverage["n_runs"]
    coverage.to_csv(args.out_dir / "coverage_by_model_harness.csv", index=False)

    counts = run_results.groupby("instance_id")["model_harness"].nunique()
    common_instances = set(counts[counts == run_results["model_harness"].nunique()].index)
    common = run_results[run_results["instance_id"].isin(common_instances)].copy()
    common_summary = summarize_group(common, ["model", "harness", "model_harness"]).sort_values(
        ["pass_rate", "mean_score"], ascending=False
    )
    common_summary.insert(0, "rank_common_subset", np.arange(1, len(common_summary) + 1))
    common_summary.to_csv(args.out_dir / "model_summary_common_instances.csv", index=False)

    pd.DataFrame(
        [
            {
                "n_model_harnesses": run_results["model_harness"].nunique(),
                "n_common_eval_round_instances": len(common_instances),
                "n_common_rows": len(common),
                "n_total_instance_ids": run_results["instance_id"].nunique(),
            }
        ]
    ).to_csv(args.out_dir / "common_subset_inventory.csv", index=False)

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
        summarize_group(run_results, cols).sort_values(cols).to_csv(args.out_dir / name, index=False)

    eval_difficulty = summarize_group(run_results, ["eval_name", "source_prefix", "kit", "task_family", "time_horizon", "grader_type"])
    eval_difficulty.sort_values(["pass_rate", "mean_score", "eval_name"]).to_csv(args.out_dir / "eval_difficulty.csv", index=False)

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
    replicate.to_csv(args.out_dir / "model_eval_replicate_results.csv", index=False)

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
    robustness.to_csv(args.out_dir / "replicate_robustness_by_model.csv", index=False)

    field_scores = pd.DataFrame(field_rows)
    field_scores.to_csv(args.out_dir / "field_scores.csv", index=False)
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
            .to_csv(args.out_dir / "field_score_summary.csv", index=False)
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
            .to_csv(args.out_dir / "field_score_by_kit_task.csv", index=False)
        )

    failure_modes = pd.DataFrame(eval_failure_rows)
    if not failure_modes.empty:
        fail_runs = run_results.merge(failure_modes, on="eval_name", how="inner")
        summarize_group(fail_runs, ["failure_mode"]).sort_values(["n_evals", "pass_rate"], ascending=[False, True]).to_csv(
            args.out_dir / "summary_by_failure_mode.csv", index=False
        )
        summarize_group(fail_runs, ["model_harness", "failure_mode"]).sort_values(["model_harness", "failure_mode"]).to_csv(
            args.out_dir / "model_by_failure_mode.csv", index=False
        )

    summary_facts = {
        "manifest": str(args.manifest),
        "manifest_sha256": hashlib.sha256(args.manifest.read_bytes()).hexdigest(),
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
    (args.out_dir / "summary_facts.json").write_text(json.dumps(summary_facts, indent=2))
    (args.out_dir / "README.md").write_text(
        f"# EpigeneticsBench updated manifest summary\n\n"
        f"Manifest: `{args.manifest}`\n\n"
        f"SHA256: `{summary_facts['manifest_sha256']}`\n\n"
        f"Rows: {summary_facts['total_runs']} result attempts; evals: {summary_facts['evals']}; "
        f"model-harness pairs: {summary_facts['model_harnesses']}.\n\n"
        f"Balanced design: {summary_facts['full_design_runs_per_pair']} attempts per model-harness pair.\n\n"
    )

    print(json.dumps({k: summary_facts[k] for k in ["total_runs", "evals", "model_harnesses", "total_pass", "overall_pass_rate", "field_pass_weighted"]}, indent=2))


if __name__ == "__main__":
    main()
