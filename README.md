# EpigeneticsBench Paper

This branch contains the EpigeneticsBench manuscript draft and the supporting
summary artifacts generated from `epibench_manifest_updated.csv`.

## Contents

- `paper/`: manuscript source, style file, references, rendered figures, and
  compiled `main.pdf`.
- `paper/scripts/make_figures.py`: regenerates all manuscript figures from the
  summary tables.
- `analysis_outputs/epi_manifest_updated_summary/`: derived CSV/JSON summary
  tables used by the paper.
- `scripts/download_manifest_data.py`: downloads result JSONs listed in a
  manifest into a local cache.
- `scripts/summarize_manifest.py`: parses the cached results and regenerates
  the derived summary tables.

The raw downloaded result cache is intentionally not committed.

## Rebuild

From the repository root:

```bash
python3 paper/scripts/make_figures.py
cd paper
latexmk -pdf main.tex
```

To regenerate summaries from a local manifest and downloaded cache:

```bash
python3 scripts/summarize_manifest.py \
  --manifest ~/Downloads/epibench_manifest_updated.csv \
  --cache-dir .scratch/epi_outputs_updated \
  --out-dir analysis_outputs/epi_manifest_updated_summary
```
