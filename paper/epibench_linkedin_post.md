Introducing EpiBench, a benchmark for practical epigenomics analysis. Agents
must recover empirical results from real workflow states without being handed a
prescribed method.

106 evaluations span CUT&Tag/CUT&RUN, ATAC-seq, ChIP-seq, and DNA methylation
workflows. The best agent-harness pair passes 45.0%.

Evaluations reflect the assay outputs scientists use in practice.
A task may depend on alignment files, peak calls, methylation tables, QC
metrics, sample metadata, genomic annotations, or downstream summaries. Solving
them requires more than writing code: agents need assay-specific judgment about
what should be compared, normalized, counted, filtered, and reported.

This tests the transition from running tools to doing analysis.

Raw epigenomics data are not directly interpretable. Biological conclusions
depend on local choices across read alignment, peak calling, motif
interpretation, sample aggregation, normalization, methylation statistics, and
genomic annotation. Small procedural choices can change the final answer.

Ground truth is hard to define even for short-horizon scientific tasks. Nearby
workflow conventions can produce plausible but unsupported answers, and some
answers are sensitive to the biological unit being measured.

We construct each evaluation as a snapshot of a real workflow immediately
before a target analysis decision. The task specifies what empirical result
should be recovered, not the exact commands the agent must run.

Candidate tasks are hardened through manual quality control. We remove prompts
that over-specify the method, answers that can be solved by shortcuts, and
graders that fail to distinguish supported results from plausible biological
expectations.

Grading uses deterministic functions over structured final answers. Some
graders check numerical intervals, others check structured labels or all-of
field matches. The goal is to measure whether the agent recovered the result
supported by the provided assay context.

Across 16 model-harness pairs and 5,088 valid trajectories, GPT-5.5 / Pi led
at 45.0% (143/318 attempts), followed by GPT-5.5 / OpenAI Codex at 39.9%
(127/318 attempts). Claude Opus 4.8 Max / Pi and GPT-5.4 / Pi each passed
39.0% (124/318 attempts).

No system passed a majority of endpoint attempts.

Performance also varied by assay family. CUT&Tag/CUT&RUN had the highest
aggregate pass rate at 34.0%, followed by methylation-seq at 33.3%, ChIP-seq
at 30.6%, and ATAC-seq at 22.8%.

Endpoint grading alone hides partial progress. Across scored answer fields,
agents passed 68.2% of fields, compared with a 31.0% endpoint pass rate. Many
failed runs found relevant files or computed useful intermediate values, but
still submitted the wrong final biological answer.

Trajectory review showed recurring failures at the level of scientific choice:
using the wrong statistic, applying thresholds incorrectly, using the wrong
biological unit, mishandling genomic features, or relying on a literature prior
when the provided files supported a different result.

This separates execution from judgment. An agent can operate the tools of an
epigenomics workflow and still choose the wrong answer.

Short-horizon tasks may sound easy, but this is the current frontier for
reliable scientific agents. Before models can own deeper biological reasoning,
they need to become dependable at local assay-specific decisions.

The positive signal is that agents often got close. They found data, ran code,
and sometimes computed the correct answer before replacing it with a familiar
workflow default or biological expectation.

That feels like a real path forward: not just better tool use, but better
grounding of biological claims in the specific assay artifacts that support
them.
