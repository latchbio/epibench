#!/usr/bin/env python3
from __future__ import annotations

import argparse
import concurrent.futures
import subprocess
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = Path.home() / "Downloads" / "epibench_manifest_updated.csv"
DEFAULT_OUT = ROOT / ".scratch" / "epi_outputs_updated"


@dataclass(frozen=True)
class Download:
    remote: str
    local: Path
    kind: str


def build_downloads(manifest: Path, out_dir: Path, force: bool = False) -> list[Download]:
    df = pd.read_csv(manifest)
    downloads: list[Download] = []

    eval_rows = df[["eval_name", "eval_path"]].drop_duplicates("eval_name")
    for row in eval_rows.itertuples(index=False):
        local = out_dir / "evals" / f"{row.eval_name}.json"
        if force or not local.exists():
            downloads.append(Download(str(row.eval_path), local, "eval"))

    for row in df.itertuples(index=False):
        local = out_dir / "results" / row.model_harness / f"{row.eval_name}__{row.round}.json"
        if force or not local.exists():
            downloads.append(Download(str(row.source_result_json_path), local, "result"))

    return downloads


def download_one(item: Download) -> tuple[bool, str]:
    item.local.parent.mkdir(parents=True, exist_ok=True)
    tmp = item.local.with_suffix(item.local.suffix + ".tmp")
    if tmp.exists():
        tmp.unlink()
    cmd = ["latch", "cp", "--progress", "none", item.remote, str(tmp)]
    try:
        proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=180)
    except subprocess.TimeoutExpired:
        if tmp.exists():
            tmp.unlink()
        return False, f"{item.kind}\t{item.local}\t{item.remote}\ttimed out after 180s"
    if proc.returncode != 0:
        if tmp.exists():
            tmp.unlink()
        msg = proc.stderr.strip() or proc.stdout.strip()
        return False, f"{item.kind}\t{item.local}\t{item.remote}\t{msg}"
    tmp.replace(item.local)
    return True, f"{item.kind}\t{item.local}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Download eval and result JSONs referenced by an EpigeneticsBench manifest.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    downloads = build_downloads(args.manifest, args.out_dir, force=args.force)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "manifest_path.txt").write_text(str(args.manifest) + "\n")
    print(f"Missing downloads: {len(downloads)}")
    if not downloads:
        return

    failures: list[str] = []
    done = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(download_one, item) for item in downloads]
        for fut in concurrent.futures.as_completed(futures):
            ok, msg = fut.result()
            done += 1
            if not ok:
                failures.append(msg)
            if done % 25 == 0 or done == len(downloads):
                print(f"{done}/{len(downloads)} complete; failures={len(failures)}")

    if failures:
        fail_path = args.out_dir / "download_failures.tsv"
        fail_path.write_text("\n".join(failures) + "\n")
        raise SystemExit(f"{len(failures)} downloads failed; see {fail_path}")


if __name__ == "__main__":
    main()
