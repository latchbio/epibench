# EpiBench

EpiBench is a verifiable benchmark for practical epigenomics analysis. Agents
receive realistic workflow snapshots and must recover structured empirical
answers from the provided data, without being handed a prescribed method.

The preprint evaluates 106 tasks across CUT&Tag/CUT&RUN, ATAC-seq, ChIP-seq,
and DNA methylation workflows. Tasks cover QC, peak calling, chromatin-state
comparisons, genomic annotation, differential methylation, alignment,
visualization, and downstream quantitative analysis. Endpoint answers are
graded deterministically with numerical interval checks, structured label
matches, or all-of field comparisons.

Preprint PDF: [`paper/main.pdf`](paper/main.pdf).

## Current Release

- `evals/`: seven public example evaluations with prompt/config metadata.
- `analysis_outputs/epibench_manifest_updated_summary/`: derived summary tables
  for the 106-evaluation result set used in the manuscript; raw trajectory
  caches are not included.
- `paper/`: manuscript source, figures, and compiled PDF.
- `scripts/`: utilities for downloading manifest data, regenerating summary
  tables, and rebuilding paper figures.

## Headline Results

The manuscript analyzes 5,088 valid trajectories from 16 model-harness pairs:
three attempts for each of 106 evaluations and each model-harness pair. No
system passes a majority of endpoint attempts. GPT-5.5 / Pi leads at 45.0%
(143/318 attempts), followed by GPT-5.5 / OpenAI Codex at 39.9% (127/318), and
Claude Opus 4.8 Max / Pi and GPT-5.4 / Pi at 39.0% each (124/318).

Assay-level pass rates are descriptive rather than controlled comparisons:
CUT&Tag/CUT&RUN 34.0%, methylation-seq 33.3%, ChIP-seq 30.6%, and ATAC-seq
22.8%. Field-level scores are higher than endpoint scores, suggesting that
agents often find useful intermediate results but fail when assay-specific
scientific judgment determines the final answer.

## Rebuild

```bash
python scripts/make_figures.py
(cd paper && latexmk -pdf main.tex)
```

The paper source is pdfLaTeX-compatible and uses an inline `references.tex`
bibliography.

## Citation

```bibtex
@misc{epibench2026,
  title  = {EpiBench: Verifiable Evaluation of AI Agents on Epigenomics Analysis},
  author = {Muralidharan, Harihara and Baskar, Reema and Lee, Soo Hee and Proctor, Tim and Workman, Kenny},
  year   = {2026},
  url    = {https://github.com/latchbio/epibench}
}
```

## License

Apache 2.0. See [LICENSE](LICENSE).
