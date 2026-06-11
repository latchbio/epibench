# CUTnTAG and CUTnRUN Trap stories

Trap mode synopsis for Zebrafish evals tested with gpt-5.5
The battery's discriminating power concentrates in a handful of recurring scientific-judgment traps — above all the CUT&RUN spike-in alignment mode (and its BAMPE paired-end analog), which silently underlies ~15 evals. gpt-5.5 can almost always compute the right answer; it fails by choosing the wrong methodology — including cases where it had the correct value in hand and discarded it. A couple of evals (001a Q2, 006e MCQ) already pin the ceiling model at 0% and may not rank weaker models; the 1/3-pass evals (002f, 006a, 012a, 012d) are the sweet spot; and the currently-saturated evals (002b pre-hardening, 013a) mark where the discrimination will appear as models get weaker.

Scope: 53 evals. Model under test: gpt-5.5 (assumed ceiling; weaker models expected to find these progressively harder). Findings drawn from each eval's grader, designed-trap notes, and the "Judge Feedback Override" comments recording the cold runs (3 initial-pass replicates + notes-retry per version).

1. One trap quietly underpins a third of the battery: the CUT&RUN spike-in alignment mode
The single most consequential finding is that one domain-knowledge decision drives the discrimination in a large cluster of evals. CUT&RUN spike-in reads are single-end and adapter-contaminated, so they need Bowtie2 --local; the default end-to-end mode gives pathologically low (6-27%) alignment and ~3x under-recovery. This same trap is the active discriminator in 002a, 002b, 002c, 002e, 002f, 002g, 005b, 006a, 006c, and 006d — and the notes record it firing at ~100% in cold tests.

The strongest piece of evidence is in 002g: one trajectory computed the correct value (0.0030) with --very-sensitive-local and then submitted the default (0.0004) anyway — "the agent had the correct number in its hands but lacked the domain prior." That is the cleanest possible proof the eval tests knowledge/judgment, not arithmetic.

There is a paired-end analog with the same shape — -f BAMPE vs default -f BAM — running through 006e, 006f, 007a, 007b, 007c, 008a, 009a, and 009c.

Why this matters for the multi-model rollout: these two "mode" decisions are powerful, validated discriminators, but they are correlated across ~15 evals. A weaker model that lacks the CUT&RUN prior will not fail these independently — it will fail the whole cluster at once. The model-ranking signal from this set is, to a meaningful degree, "does the model know CUT&RUN spike-in alignment?" repeated many ways. Worth knowing when interpreting aggregate scores.

2. gpt-5.5's failures are dominated by the decision layer, not computation
The most interesting capability story: the smartest model usually can compute the right answer — it just does not choose it. Recurring "explored the right answer, then discarded it" pattern:

- 002g — computed 0.0030, submitted 0.0004.
- 006e — trajectory 2 had the fully correct answer set (788/385/0.758/8) early, then walked it back to a worse one and committed to a textbook interpretation.
- 014c — trajectory 1 computed the correct gene-TSS +/-2 kb result (0.4846), then deliberately switched to a wider transcript-TSS +/-3 kb variant at the write step and failed by 0.034.

For the ceiling model, the bottleneck is principled selection among self-generated alternatives. The benchmark is not measuring whether the model can run Picard/MACS2 — it is measuring scientific judgment at the moment of committing an answer. Expect weaker models' failures to move "left" (cannot compute at all), which is exactly the progressive-difficulty gradient we want.

3. The 100%-fail evals — real floors even for the smartest model
Two places where gpt-5.5 went 3/3 wrong:

- 001a Q2 (strand-aware gene merging): every agent independently wrote strand-unaware merge code despite the strand column being visible in its own zcat output. A Tier-4 implicit-biology trap that fired at 100%.
- 006e MCQ: all three picked the mechanistically-plausible distractor (generic NELF/DSIF promoter-proximal pausing) instead of the correct Polycomb-block-at-bivalent-loci answer, which required integrating developmental stage + bivalent signature + the paper's specific finding.

These validate that the trap is real — but flag them deliberately: if the assumed ceiling model fails 100%, that field cannot rank the weaker models (everyone fails). They function as "no model can do this yet" probes, not discriminators. Decide which you intend each to be.

4. The "sounds reasonable but scientifically wrong" judgment trap
The protein-coding biotype filter shows up as a recurring 1/3-pass discriminator (012a, 012d): agents filter to protein-coding genes before computing bivalent stats — defensible in isolation, but wrong for H3K27me3 (broadly deposited including non-coding loci), which inflates the bivalent fraction. The one agent that "worked with the data as provided" passed. This is the ideal discriminator shape and a clean capability axis distinct from the alignment-mode family.

5. Not all failures are reasoning — some are agentic execution
005c is a nice outlier: trajectory 3 killed makeTagDirectory before HOMER's autocorrelation/QC phase finished, leaving sentinel values (fragmentLengthEstimate=-123456789), so HOMER fell back to its default 150 bp and called the wrong number of peaks. A process-management failure — misreading an intermediate artifact as completion — not a domain error. Weaker / less patient agents will hit this class far more, and it is a different competency than the science.

6. Tolerances are doing real work (compounding drift)
012d trajectory 2 shows the grading philosophy paying off: q30 MAPQ + protein-coding universe + a narrow promoter window were each individually within tolerance, but stacked they pushed the K4-only counts out. The tolerance budget absorbs one defensible choice and catches accumulation — a design feature worth surfacing, not an accident.

7. Where gpt-5.5 saturates -> discriminators for weaker models
Several evals were all-pass and had to be hardened, which is the most direct signal for the progressive-difficulty thesis:

- 002b: first version 7/7 (100%) because the dedup formula was in the task text; it was removed so the agent must derive it.
- 013a (visualization track generation): 100% pass at v1, v2, and v3 — genuinely easy for gpt-5.5.
- 001c (earlier version): 3/3 + notes-retry all identical -> 0.0 spread; revised to de-recipe.

These are exactly the fields/evals that will start discriminating once you drop below gpt-5.5. The set looks deliberately tuned so the ceiling model lands ~30-50% on the hard fields and ~100% on the deterministic ones — the right shape to fan weaker models out.

[5] Epigenetics Trap Stories
June 5, 2026 (updated). The zebrafish set (53 evals) is now fully approved; the formerly-pending zebrafish evals (001c, 012c, 012e, 014h, 014i) have been folded into the main stories below and the trailing "Extensions" section retired. This snapshot may still miss coverage of some non-zebrafish evals, so take the non-zebrafish references (WGBS, ChIP-seq, ATAC) as zebrafish-set-centric.
1. CpG strand-merging catastrophe (WGBS)
Bismark reports each CpG dinucleotide as two rows (+ strand at position N, − strand at N+1). Agents must merge these before computing coverage, methylation rates, or DMCs. At a 10x coverage filter, the unmerged approach retains only 21% of CpGs (vs 69% merged) — a 3.3-fold loss that cascades through every downstream analysis.
Why it's interesting: A single data-representation error cascades through 8 evals, corrupting coverage, correlation, and DMC counts in different directions and magnitudes. The 10x coverage threshold sits exactly at the per-strand mean (~6.7x), maximizing the damage.
Evals: cpgreport_mean_coverage, cpgreport_cpg_count_10x, cpgreport_dmc_count, cpgreport_cross_sample_corr, cpgreport_strand_discordance, covgz_dmc_count, covgz_cross_sample_corr, covgz_extreme_dmc_coverage
Cross-references: Compounds with Story 9 (epiallele discordance uses the same XM tag but a different context trap). Story 2 also tests Bismark-specific parsing but on a different axis (context filtering vs strand merging).
2. Bisulfite conversion rate illusion (WGBS)
Conversion efficiency must be computed from non-CpG contexts (CHG + CHH) only, because CpG cytosines carry real biological methylation (~75%). Including CpG drops the apparent rate from 99.5% to ~95% — a 4.5pp gap that makes a perfect library look borderline failed.
Why it's interesting: Agents must know that CpG methylation is real biology, not conversion failure — a concept with no analog in standard sequencing. The 4.5pp gap crosses the standard QC pass/fail threshold, so the wrong method flags a perfect library as borderline failed.
Evals: bam_bisulfite_conversion_rate, bam_bisulfite_conversion_chr11
Cross-references: Same XM-tag parsing pipeline as Stories 1 and 9 but tests a disjoint field (conversion efficiency vs coverage vs discordance).
3. Textbook methylation-expression model is wrong (WGBS + RNA-seq)
The canonical "hypomethylation = activation" model is so deeply embedded that agents report <10% downregulated genes without checking. The actual figure (~30%) and the positive correlation at hypermethylated promoters (PRC2 displacement) both contradict the textbook.
Why it's interesting: Tests whether agents compute or assert. The canonical model is deeply embedded in training data. The positive methylation-expression correlation at hypermethylated promoters contradicts the expected negative correlation, forcing computation over recall.
Evals: c4_paradox_hypo_downregulated, noncanonical_correlation_direction
Cross-references: Thematically linked to Story 10 (prior-driven guessing defeats agents in ChIP-seq too). Both evals also connect to tss_hypermethylation_enrichment and dmr_tss_enrichment, which test positional stratification of DMCs near promoters.
4. Spike-in alignment mode trap (CUT&RUN)
Single-end spike-in reads with adapter contamination fail catastrophically under Bowtie2 end-to-end mode (6% mapping) while local mode succeeds (99.5%). The 16x read loss corrupts all downstream normalization. The trap is asymmetric: PE samples are unaffected, so a blanket mode choice passes some samples and silently fails others.
Why it's interesting: The asymmetry is the key: agents that apply a single alignment mode across all samples pass on PE and fail silently on SE. The 16x read loss cascades through normalization factors, differential enrichment, and cross-sample comparisons — each downstream eval amplifies the original error differently.
Evals: 002c, 002e, 002f, 002g, 005b, 006a, 006c, 006e
Cross-references: The normalization factors computed here feed into 006d (cross-assay Spearman), 006f (Pol II transcriptional validation), and 011a (RNA-seq integration). Story 6 tests a related but distinct format trap (BAMPE vs BAM). Story 16 extends spike-in normalization with a formula-independent ratio design.
5. Broad vs narrow peak calling mode (CUT&RUN, ChIP-seq)
H3K4me3 is narrow (promoter-localized), H3K27me3/H3K9me3 are broad (domain-spanning). Narrow mode on a broad mark fragments contiguous domains into 2–5x more peaks with lower enrichment. The task text names the mark but never says "use --broad."
Why it's interesting: Agents must know chromatin biology to pick the right mode. Narrow mode on a broad mark produces a plausible-looking but biologically meaningless result — more peaks that are individually weaker.
Evals: 009b, 012b, 012c, 012d, 012e, 007a
Cross-references: 009b and 012b also involve Story 7 (--keep-dup sensitivity), since broad marks at heterochromatic repeats compound both traps simultaneously. 012c adds a compound trap on the same bivalent data — the discriminating metric is fraction-expressed, not mean-TPM, so peak mode and expression metric must both be chosen correctly. 012e tests bivalent-gene GO classification, where keyword matching vs ontology-hierarchy traversal gives 0.44 vs 0.31 developmental-term fraction. 014c tests broad vs narrow for H2A.Z where the correct choice is less obvious. 014h extends this to show broad-only peaks reveal H2A.Z gene body occupancy (52%) invisible to narrow calling.
6. BAMPE format trap (CUT&Tag, ATAC-seq)
The same wrong choice (-f BAM on PE data) produces opposite errors depending on the assay: 25–75% peak inflation for CUT&Tag, but ~10x fewer peaks for ATAC-seq (where the Tn5 insertion-BED workflow is canonical).
Why it's interesting: The same mistake produces opposite errors in different assays. Agents must reason from the enzymatic mechanism (Tn5 tagmentation vs MNase digestion), not apply a single recipe.
Evals: 007a, 007b (CUT&Tag); atac_1a, atac_2c, atac_4b, atac_5a (ATAC)
Cross-references: Connects to Story 4 (alignment mode) as another format-selection trap. ATAC evals 5c, 8a, 8b (chromVAR/motif) depend on correct peak calling upstream, so this trap cascades into the motif analysis evals.
7. --keep-dup for heterochromatin (CUT&RUN)
Narrow promoter marks (H3K4me3) are insensitive to --keep-dup, but broad heterochromatic marks (H3K9me3) lose 85% of signal under the default --keep-dup 1. Deep sequencing of broad domains produces genuine position overlaps, not PCR artifacts.
Why it's interesting: Duplicate handling is mark-specific. The same default that is harmless for one mark destroys another. Agents must reason from the genomic architecture of the mark (narrow promoters vs broad heterochromatic domains).
Evals: 009b, 012b
Cross-references: Both evals also test Story 5 (broad mode). 006d tests a related question: CUT&RUN vs CUT&Tag duplicates arise from different chemistries (MNase vs Tn5) requiring different handling. Story 15 extends this to the opposite conclusion for CUT&Tag.
8. IgG/input control omission (CUT&RUN, ChIP-seq)
The control file is present in the bundle and described in the README, but agents skip it anyway — doubling peak counts. A second-layer trap: MACS2 BAMPE mode crashes with ZeroDivisionError when given a control BAM, so agents that correctly try to use IgG must troubleshoot the crash.
Why it's interesting: Two-layer trap: agents must both use the control and survive the tool crash it causes. In ChIP-seq evals, the input control has a dual role — include for peak calling, exclude from patient-level rankings.
Evals: 011a (CUT&RUN IgG); chipseq_A1, A4, E5, B1 (ChIP-seq input)
Cross-references: In the ChIP-seq evals, the input control has a dual role: it must be included as MACS background but excluded from patient-level rankings (A1, A4, B3, H1). This "include for calling, exclude for interpretation" distinction is tested across the full ChIP-seq set.
9. Epiallele discordance context trap (WGBS)
Including non-CpG contexts (CHG/CHH) inflates within-read discordance from 36% to 59% (23pp gap) because CHG/CHH sites are ~99.5% unmethylated, making every methylated-CpG read appear discordant. The gap varies by chromosome (23pp chr22, 19pp chr15, 10pp chr11), reflecting biological differences in CpG density.
Why it's interesting: Same XM tag, different error mode from Stories 1 and 2. Three distinct traps from the same Bismark output: context filtering (Story 2), strand merging (Story 1), and context-aware concordance (this story). Agents that master one may still fail the others.
Evals: bam_epiallele_discordance, bam_epiallele_discordance_chr15
Cross-references: Three distinct traps from the same Bismark XM tag: context filtering (Story 2), strand merging (Story 1), and context-aware concordance (this story).
10. Super-enhancer is not at the oncogene (ChIP-seq)
The largest H3K27ac super-enhancer sits beside a non-coding antisense locus, not a canonical B-ALL driver. Agents steeped in B-ALL biology guess without computing. A secondary trap: BigWig coverage vs peak-call enrichment scores can swap the close top two regions.
Why it's interesting: Size and oncogenic importance are decoupled. Agents that assert from disease priors fail; agents that compute from the data succeed. Mirrors Story 3 (prior-driven assertion).
Evals: chipseq_F2
Cross-references: chipseq_F1 (super-enhancer counts) and chipseq_F4 (signal concentration) test related ROSE-lite methodology on the same data. chipseq_B1 tests the inverse: the most-peaks sample is the lowest-enrichment library (noise, not biology). Thematically mirrors Story 3 (prior-driven assertion defeats agents).
11. Strand-aware gene coverage (CUT&RUN)
H3K4me3 promoter analysis requires strand-aware interval merging because genes on opposite strands have independent TSSs. bedtools merge without -s collapses overlapping opposite-strand genes into single intervals, yielding 236.8 Mb instead of 314.2 Mb — a 77 Mb gap. The task text deliberately says "merging overlapping genes" without mentioning strand-awareness; agents must infer it from the H3K4me3/promoter context.
Why it's interesting: 77 Mb is the largest single-trap gap in the entire benchmark. The biological reasoning chain (H3K4me3 → promoter-deposited → TSS is strand-specific → merging must be strand-aware) is a pure epigenetics inference with no procedural shortcut.
Evals: 001a, 001b, 001c
Cross-references: Complements Story 5 (mark biology dictates tool parameter). 001c extends to isoform-level TSS selection: the most-5' strand-aware TSS must be chosen from among multiple transcript isoforms in GRCz12tu's annotation.
12. Genome size for subset data (CUT&RUN)
BAMs are subsetted to chr14 (~51.5 Mb), but agents that look up "zebrafish genome size" pass -g 1.4e9 to MACS2. The 27x genome size inflation lowers the Poisson background lambda, producing 3000+ peaks instead of ~700.
Why it's interesting: Tests whether agents inspect the data they're given rather than relying on species-level lookup. The error is silent — MACS2 runs fine with the wrong genome size and produces a plausible-looking peak set.
Evals: 005a
Cross-references: Extends Stories 5 and 6 — a third axis of peak-caller misconfiguration. Also relevant to 006e, where the genome size trap is weak (±29 peaks) because Pol II peaks are sparse.
13. Depth confounding in developmental comparison (CUT&Tag)
6 hpf and 24 hpf H2A.Z CUT&Tag samples differ 14x in sequencing depth. Naive peak counting shows 2.1x more peaks at 24 hpf, which agents interpret as "H2A.Z occupancy increases during development." But the 2.1x ratio is artificially small (saturation at high depth) — the real confound goes the other direction from what agents expect. Agents must downsample BEFORE peak calling, not after.
Why it's interesting: Downsampling order is a validated methodology trap: downsampling reads after peak calling doesn't fix the confound because peaks were already called at asymmetric depths. The biological interpretation flips depending on whether you control for depth.
Evals: 014a, 014f, 014ie
Cross-references: 014i strengthens this story — after README cleanup, the task and README no longer reveal which files are depth-matched, forcing agents to discover the 14x depth imbalance themselves. 014f adds a Jaccard trap (peak-count vs base-pair Jaccard) that compounds the downsampling error. Thematically related to Story 10 (computing vs asserting).
14. Fragment size reveals chromatin target identity (CUT&Tag)
CUT&Tag fragment size distributions encode the target's relationship to nucleosomes. A high dinucleosomal fraction (~280+ bp) indicates the target is a histone variant at positioned nucleosomes flanking NFRs — not heterochromatin or gene bodies, which are common wrong answers from superficial reasoning about large fragments.
Why it's interesting: The only eval testing backwards reasoning from a QC metric to biological identity. Three evals test fragment biology directly (008a, 014b, 014d), but this is the only one where the fragment signature must be used to infer the chromatin target.
Evals: 008a, 014b
Cross-references: 014b tests the related question of Tn5 vs pA-MNase cutting signatures — agents familiar with CUT&RUN but not CUT&Tag confuse the two enzymes.
15. CUT&Tag duplicates are real artifacts; CUT&RUN duplicates may not be
CUT&Tag uses Tn5, which has many possible cut sites per accessible region, so identical fragments are overwhelmingly PCR artifacts and should be removed. CUT&RUN uses pA-MNase, which cuts at fixed positions around the antibody-bound nucleosome, so identical fragments can reflect genuine biology and should be retained. Agents must select --keep-dup based on the enzymatic mechanism, not the assay family name.
Why it's interesting: Directly contradicts a "one-size-fits-all" duplicate policy. The same --keep-dup auto that is correct for CUT&RUN H3K9me3 (Story 7) may be wrong for CUT&Tag at the same locus, because the duplicate-generating mechanisms differ.
Evals: 014d, 014h
Cross-references: Extends Story 7 (--keep-dup for heterochromatin) to the opposite conclusion for a related assay. 006d tests the cross-assay Spearman correlation between dup rate and spike-in fraction, which depends on this distinction. 014h adds peak mode comparison where --keep-dup interacts with narrow vs broad calling for H2A.Z, and shows broad-only peaks reveal 52% gene-body occupancy invisible to narrow calling.
16. Formula-independent dedup detection via ratio design (CUT&RUN)
Scale factor ratios cancel formula constants (C, 1e6) so agents using any reasonable normalization formula get the same ratio. But the dedup trap doesn't cancel: agents who incorrectly dedup spike-in reads get 1.85 instead of 0.97. The trap fires harder in ratio space (gap 0.884) than in absolute space (gap 0.126).
Why it's interesting: A novel eval design pattern — testing biological reasoning while being agnostic to implementation details. Any formula proportional to 1/(spike × genome) produces the same ratio, but the decision of whether to dedup spike-in reads remains discriminating. Orlando-style formulas (no genome term) give ~0.876 which passes tolerance but fails the MCQ because dedup correction has no effect without a genome term.
Eval: 002a
Relationship: Extends Story 4 (spike-in normalization) and Story 7 (dedup reasoning). The 0.884 gap in ratio space is 7x larger than the 0.126 gap in absolute space, making the trap more robust to computational noise.


# WGBS (MethylSeq) Trap Stories

June 10, 2026. The WGBS set (25 evals) covers whole-genome bisulfite sequencing analysis of esophageal squamous cell carcinoma (ESCC) from GSE149608/GSE149609 (Cao et al. 2020). Evals span three data layers: Bismark BAM output (XM tags), Bismark coverage reports (CpG report and .cov.gz), and integrated methylation-expression analysis (parquet matrices + RNA-seq TPM). This snapshot describes the trap architecture organized into 9 stories.

## 1. CpG strand-merging catastrophe

Bismark reports each CpG dinucleotide as two rows: the + strand at position N and the − strand at position N+1. Agents must merge these before computing coverage, methylation rates, or DMCs. Per-strand coverage averages ~6.7x, so at a 10x threshold the unmerged approach retains only 21% of CpGs (vs 69% merged) — a 3.3-fold loss that cascades through every downstream analysis. The trap fires on two independent file formats (CpG report with explicit strand column, and .cov.gz without one), so agents that learn the fix for one format may still fail the other.

**Why it's interesting:** A single data-representation error cascades through 8 evals, corrupting coverage, correlation, and DMC counts in different directions and magnitudes. The 10x coverage threshold sits exactly at the per-strand mean (~6.7x), maximizing the damage. The .cov.gz variant is harder because there is NO strand column — positions N and N+1 silently represent two strands of the same CpG.

**Evals:** cpgreport_mean_coverage, cpgreport_cpg_count_10x, cpgreport_dmc_count, cpgreport_cross_sample_corr, covgz_dmc_count, covgz_cross_sample_corr, covgz_extreme_dmc_coverage

**Cross-references:** Compounds with Story 3 (epiallele discordance uses the same XM tag but a different context trap). Story 2 also tests Bismark-specific parsing but on a disjoint axis (context filtering vs strand merging).

## 2. Non-CpG context contamination

Bismark's XM tag encodes multiple methylation contexts: CpG (Z/z), CHG (X/x), CHH (H/h). Several analyses require restricting to CpG only, but the trap manifests differently depending on the downstream task. For bisulfite conversion rate, CpG methylation is real biology (~75% methylated), so including CpG drops the apparent conversion rate from 99.5% to ~95% — a 4.5pp gap that crosses the standard QC pass/fail threshold. For non-canonical methylation fraction, agents must isolate CHG+CHH contexts to quantify the true non-CpG methylation rate (~0.3–0.5%), which is biologically meaningful in certain cancers. Including CpG inflates the apparent "non-canonical" rate by ~150-fold.

**Why it's interesting:** The same XM tag requires opposite filtering depending on the question: EXCLUDE CpG for conversion rate, INCLUDE only CpG for epiallele analysis, EXCLUDE CpG for non-CpG methylation rate. Agents must reason about what each context means biologically rather than applying a single filter.

**Evals:** noncanonical_fraction, noncanonical_methylation_fraction

**Cross-references:** Same XM-tag parsing pipeline as Stories 1 and 3 but tests a disjoint field (non-CpG fraction vs coverage vs discordance).

## 3. Epiallele discordance context trap

Including non-CpG contexts (CHG/CHH) when computing within-read methylation concordance inflates discordance from 36% to 59% (23pp gap on chr22) because CHG/CHH sites are ~99.5% unmethylated, making every methylated-CpG read appear discordant. The gap varies by chromosome (23pp chr22, 19pp chr15), reflecting biological differences in CpG density and non-CpG methylation rates.

**Why it's interesting:** Three distinct traps from the same Bismark XM tag: context filtering (Story 2), strand merging (Story 1), and context-aware concordance (this story). Agents that master one may still fail the others. The chr15 variant adds sample-specificity — a different sample with a different chromosome produces a different gap magnitude, preventing agents from memorizing the answer.

**Evals:** bam_epiallele_discordance (chr22), bam_epiallele_discordance_chr15 (chr15)

**Cross-references:** Three distinct traps from the same Bismark XM tag: context filtering (Story 2), strand merging (Story 1), and context-aware concordance (this story).

## 4. Textbook methylation-expression model is wrong

The canonical "hypomethylation = activation" model is so deeply embedded that agents report <10% downregulated genes without checking. The actual figure (~30%) for C4 cluster genes directly contradicts the textbook. Meanwhile, C3 genes show the inverse paradox: promoter hypermethylation with INCREASED expression, driven by PRC2 displacement. Agents must compute cluster sizes from scratch using statistical tests (Welch t-test + BH correction) and unbiased directional classification rather than asserting from prior knowledge.

**Why it's interesting:** Tests whether agents compute or assert. The canonical model is deeply embedded in training data. The ~30% non-canonical fraction and the positive methylation-expression correlation at hypermethylated promoters both contradict the expected negative correlation, forcing computation over recall. The four-cluster framework (C1-C4) is the paper's central finding and requires genuine multi-omics integration.

**Evals:** c4_paradox_hypo_downregulated, noncanonical_correlation_direction, noncanonical_fraction, noncanonical_methylation_fraction, c3_prc2_derepression

**Cross-references:** Thematically linked to Story 5 (gene-body methylation contradicts the promoter-centric model). Both test whether agents can overcome prior-driven assertion. Also connects to cpg_island_hypermethylation and tss_hypermethylation_enrichment, which test the spatial paradox from a different angle.

## 5. Gene-body methylation is the stronger correlate

Agents default to promoter methylation when asked about methylation-expression coupling, because the textbook focuses exclusively on promoter methylation. But gene-body methylation shows a POSITIVE correlation with expression (r ≈ 0.149) that is 2.7x stronger than the promoter correlation (r ≈ 0.056). The task does not hint that gene-body should be explored — agents must independently realize that the promoter-centric model is incomplete.

**Why it's interesting:** The promoter answer is not wrong per se (r = 0.056 is real), but it misses the stronger signal. The eval's tolerance window (0.104–0.194) firmly rejects the promoter correlation, forcing agents to explore beyond the obvious. This is a methodology trap: agents that dutifully compute promoter correlations and stop have done real work but missed the point.

**Evals:** genebody_methylation_expression

**Cross-references:** Extends Story 4 (non-canonical methylation-expression). Both test whether agents explore beyond the promoter-centric model.

## 6. Genome build and annotation traps

Multiple evals require agents to infer the correct genome build (hg19) from data provenance and use build-matched annotations. The data never states the build explicitly — agents must infer it from GSE149608 metadata, coordinate ranges, or BSMAP alignment references. Using hg38 annotations on hg19 coordinates silently shifts gene positions, corrupting promoter methylation estimates by hundreds of base pairs.

The WNT2 promoter eval compounds this with a TSS source trap: GENCODE v19 and UCSC refGene place the WNT2 TSS 231bp apart (chr7:116,963,343 vs chr7:116,963,112), producing different mean methylation values depending on the reference used. The CpG island hypermethylation eval adds a second layer: UCSC distributes cpgIslandExt for both hg19 and hg38, and overlaying hg38 islands on hg19 coordinates gives wrong enrichment values.

**Why it's interesting:** Silent coordinate mismatches are the most dangerous class of bioinformatics error — no tool crashes, no warning is raised, and the output looks plausible. Agents must chain provenance reasoning (paper → GEO → aligner → build) rather than defaulting to the latest genome assembly.

**Evals:** wnt2_promoter_genome_build, cpg_island_hypermethylation, roadmap_chromatin_state_enrichment, tss_hypermethylation_enrichment, dmr_tss_enrichment

**Cross-references:** roadmap_chromatin_state_enrichment requires downloading Roadmap Epigenomics chromatin state annotations at the correct build. The EZH2 eval (Story 7) requires ENCODE ChIP-seq data, also build-sensitive.

## 7. Polycomb switching and cell-line selection

Cancer hypermethylation preferentially targets ancestral Polycomb/bivalent domains — loci marked by PRC2 (EZH2) in stem cells. The enrichment varies dramatically across cell lines: H1-hESC EZH2 peaks show ~34x enrichment while differentiated K562 peaks show only ~4–6x, because cancer recapitulates the developmental program. Agents must select the biologically appropriate cell line (stem cell, not differentiated) and explain WHY the enrichment differs.

**Why it's interesting:** Tests biological reasoning beyond computation. The right answer requires understanding the Polycomb-switching model: cancer hypermethylation targets loci that were bivalent (H3K4me3 + H3K27me3) in embryonic stem cells, not loci that are currently marked in adult tissues. This is why H1-hESC is the informative reference.

**Evals:** ezh2_encode_cell_line_selection

**Cross-references:** Connects to Story 6 (genome build for ENCODE downloads) and Story 8 (spatial heterogeneity). The Polycomb-switching model is the mechanistic explanation for the C3 cluster in Story 4.

## 8. Spatial heterogeneity of cancer methylation

Cancer methylation changes are not uniformly distributed. Three evals test different facets of this spatial heterogeneity: (a) hypermethylation is 10x enriched near TSS (15.6% hyper) versus distal regions (1.6% hyper), despite 97.3% of all DMCs being hypomethylated; (b) heterochromatin is DEPLETED for hypermethylation (fold 0.1–0.3x), contradicting the textbook expectation that "silent chromatin = methylated"; (c) C3 enhancer methylation shows that promoter hypermethylation does NOT extend to nearby enhancers — the hypermethylation is spatially restricted.

**Why it's interesting:** Each eval tests a different axis of the same biological principle: cancer methylation is spatially targeted, not random. The heterochromatin depletion is particularly counterintuitive — agents steeped in the "methylation = silencing" model expect heterochromatin to be hypermethylated, when in reality it undergoes global hypomethylation while Polycomb regions gain methylation.

**Evals:** tss_hypermethylation_enrichment, roadmap_chromatin_state_enrichment, c3_enhancer_methylation, dmr_tss_enrichment

**Cross-references:** Connects to Story 4 (non-canonical patterns) and Story 7 (Polycomb targeting). The spatial restriction of C3 enhancer methylation provides the mechanistic explanation for why promoter hypermethylation can coexist with gene activation.

## 9. Effect-size thresholds and platform mismatch

WGBS data has fundamentally different statistical properties from Illumina methylation arrays (450K/EPIC). Array-era conventions (|Δβ| ≥ 0.2 effect-size filters, |log2FC| ≥ 1 on methylation) are inappropriate for WGBS because: (a) WGBS captures all ~28M CpGs vs arrays' ~450K, so the multiple testing burden is different; (b) true biological DMCs can have small effect sizes in heterogeneous tumors; (c) the WNT2 epigenetic activation eval requires gene family analysis across 19 WNT ligands, where array-era filters would miss the paradoxical hypermethylation-activation at WNT2.

The DEG count eval adds a related trap: TPM values must be log-transformed before t-testing because the raw distribution is severely right-skewed. Testing on raw TPM inflates variance for highly expressed genes, producing ~500 DEGs instead of ~1500 — a 3x undercount that changes the biological interpretation.

**Why it's interesting:** Tests whether agents adapt their methodology to the data platform rather than applying memorized recipes. The effect-size threshold trap is subtle because the filtered results are a strict subset of the correct results — nothing looks wrong, but statistical power is silently destroyed.

**Evals:** dmc_count_effect_size_filter, wnt2_epigenetic_activation, deg_count_log_transform, noncanonical_methylation_fraction

**Cross-references:** The effect-size filter trap compounds with Story 4 (non-canonical fraction) — applying array thresholds to WGBS data disproportionately removes small-effect non-canonical genes, biasing the apparent non-canonical fraction downward.

---

## Summary

| Story | Theme | Evals | Pass Rate |
|---|---|---|---|
| 1. Strand-merging catastrophe | Data representation | 7 | 0–2% |
| 2. Non-CpG context contamination | Context filtering | 2 | 1–93% |
| 3. Epiallele discordance context | Context filtering | 2 | 24–44% |
| 4. Textbook model is wrong | Prior vs computation | 5 | 7–89% |
| 5. Gene-body > promoter | Methodology | 1 | 73% |
| 6. Genome build traps | Annotation | 5 | 60–84% |
| 7. Polycomb switching | Biology | 1 | 52% |
| 8. Spatial heterogeneity | Biology | 4 | 29–84% |
| 9. Platform mismatch | Methodology | 4 | 0–36% |

The 25 WGBS evals divide into three difficulty tiers: **universally hard** (Story 1: strand-merging, 0–2% pass rate across all models), **discriminative** (Stories 3, 4, 7, 8, 9: 20–60% pass rate, strong model separation), and **moderate-to-easy** (Stories 5, 6: 60–84%, most frontier models pass).


# ATAC-seq Trap Stories

June 10, 2026. The ATAC-seq set (24 evals: 12 primary + 12 cold-start) covers FAST-ATAC analysis of a pediatric B-cell acute lymphoblastic leukemia (B-ALL) cohort from GSE161501 (Diedrich et al. 2021). The dataset consists of 23 paired-end sub-20M BAMs spanning three molecular subtypes (ETV6-RUNX1 n=5, DUX4-ERG n=7, Hyperdiploid n=11) with matched RNA-seq. Primary evals (`atac_*`) test peak calling, QC, consensus construction, chromatin state analysis, and motif enrichment. Cold-start evals (`cold_*`) test integrative RNA+ATAC analysis including TF regulon hubs, cis peak-gene coupling, and subtype-specific regulatory architecture. This snapshot describes the trap architecture organized into 9 stories.

## 1. Tn5 insertion-site BED vs BAMPE format trap

The canonical FAST-ATAC peak-calling convention uses a two-step Tn5 insertion-site workflow: (1) extract single-bp Tn5 insertion sites from BAM (+4 forward / -5 reverse offset on both mates), producing ~20M insertions per sub-20M BAM; (2) call MACS3 on the resulting BED with fixed shift/extension (--shift -75 --extsize 150 --nomodel --nolambda --keep-dup all -p 0.01). Agents that instead feed the raw paired-end BAM to MACS3 with `-f BAMPE` invoke paired-end fragment-length modeling, producing ~10x fewer peaks (~25K–50K vs ~270K–310K per sample). This 10x deficit cascades through every downstream analysis.

A critical subtrap: agents must process BOTH mates (read1 and read2) to emit two insertion sites per properly-paired fragment. Processing only read1 yields ~10M MACS tags instead of ~20M and produces peak counts ~37% below the correct regime (~170K vs ~270K). The diagnostic is the MACS3 "total tags in treatment" report.

**Why it's interesting:** The same wrong choice (-f BAM/BAMPE on PE data) produces OPPOSITE errors depending on the assay: for ATAC-seq, it produces ~10x fewer peaks, while for CUT&Tag it produces 25–75% peak inflation. Agents must reason from the enzymatic mechanism (Tn5 tagmentation creates single-bp cut sites) rather than applying a generic PE recipe.

**Evals:** atac_1a (peak calling convention), atac_2c (QC metrics depend on correct peak set), atac_5a (depth control and RAG1 accessibility)

**Cross-references:** Directly parallels CUT&Tag Story 6 (BAMPE format trap) but with opposite error direction. The same Tn5 biology underlies both assays, but the canonical analysis differs.

## 2. Union vs majority-gated consensus (94% rejection)

When 23 per-sample narrowPeak files are pooled, the union contains ~1.68M intervals. Applying a 50% majority gate (supported by >=12/23 libraries) reduces this to ~103K intervals — a 94% rejection rate. The 50% filter, NOT the score-ranking/merge step, does the discrimination work. Agents that assume depth-equalized samples produce identical union and consensus sets (the "byte-identical" fallacy) fail to recognize that singleton and low-prevalence peaks are numerous even at matched depth.

**Why it's interesting:** The 94% rejection rate has direct biological consequences. Over 88% of B-ALL subtype-accessible sites are promoter-distal (Diedrich 2021), and these distal enhancers are precisely the low-prevalence calls lost by a strict pan-dataset gate. The IGH-DUX4 rearrangement locus (DUX4-ERG subtype) is accessible in only ~7/23 libraries (30%), so its peaks fail the 50% gate — meaning a cohort-wide consensus systematically discards the most biologically informative subtype-specific regulatory elements.

**Evals:** atac_4a (union vs 50% consensus, V(D)J locus accessibility), atac_4b (subtype-specific consensus rescues lost loci)

**Cross-references:** Connects to ChIP-seq Story 5 (consensus semantics). The biological insight — that stringent consensus gates disproportionately discard subtype-specific enhancers — is unique to the ATAC-seq set.

## 3. Depth equalization before peak calling

Post-hoc normalization (RPKM, CPM, TMM) cannot recover weak accessible regions that were missed during peak calling in shallower libraries. Peak detection itself is depth-sensitive: a region must exceed the local background threshold to be called, and that threshold depends on read coverage. The correct strategy is to subsample alignments to a common target depth BEFORE peak calling, so peak-detection sensitivity is comparable across samples.

**Why it's interesting:** The distinction between pre-peak-calling depth control and post-hoc count scaling is not widely taught. RPKM was developed for RNA-seq gene bodies where the feature universe is fixed by annotation; in ATAC-seq, the feature universe IS the peak set, so depth directly controls which features exist in the matrix. An agent that normalizes RPKM after peak calling has done real statistical work but missed the fundamental problem.

**Evals:** atac_5a (depth control is the technical MC answer), atac_1a (23 sub-20M BAMs reflect pre-equalized depth)

**Cross-references:** Parallels ChIP-seq Story 6 (A4 subsampling) and CUT&Tag Story 13 (depth confounding in developmental comparison). All three test whether agents equalize before calling.

## 4. Fragment-length deconvolution and DNA helical pitch

ATAC-seq fragment-size distributions encode chromatin architecture. A dominant ~10 bp oscillation in the 80–150 bp range reflects the DNA helical pitch: Tn5 cuts are enriched on accessible rotational faces of protein-bound or nucleosome-adjacent DNA. This is NOT the mono-to-dinucleosome spacing (~180 bp repeat), NOT adapter dimers, and NOT a paired-end truncation artifact. Proper deconvolution requires fitting constrained Gaussian mixture components (NFR, mono-, di-, tri-nucleosome) with biophysical bounds, then using per-subtype NNLS solves — not aggregate GMM mixture weights applied directly as per-subtype fractions.

DUX4-ERG has a higher nucleosome-associated deconvolved fraction than Hyperdiploid (~0.64 vs ~0.58), indicating greater global chromatin packing. This direction must be computed from the deconvolved fractions, not asserted from prior biology.

**Why it's interesting:** The fragment-length distribution is a QC metric that agents typically plot and move on from. This eval forces computation of biologically meaningful quantities from the shape of the distribution. The constrained-fit requirement catches agents that use unconstrained EM (sklearn GaussianMixture), which converges to wrong local minima and inflates nucleosome-associated fractions by ~0.13.

**Evals:** atac_5a (periodicity, deconvolution, packing interpretation)

**Cross-references:** Connects to CUT&Tag Story 14 (fragment size reveals chromatin target identity). Both test backwards reasoning from a QC metric to biological properties.

## 5. Subtype-specific chromatin biology

The three B-ALL subtypes have distinct regulatory programs that manifest across multiple evals:

- **DUX4-ERG:** IGH-DUX4 structural rearrangement hijacks the IGHJ4 super-enhancer, driving AP-1/JDP2/BRD4/EP300 chromatin opening at germline-restricted distal regulatory elements. These sites are predominantly promoter-distal, giving DUX4-ERG the lowest TSS-proximal consensus fraction (~0.318).
- **ETV6-RUNX1:** TEL-AML1 fusion recruits NuRD complex to RUNX1 binding sites, concentrating accessible chromatin at promoter-proximal targets (IKZF1, PAX5, EBF1, BCL6). TSS-proximal fraction ~0.348.
- **Hyperdiploid:** Trisomies of chr4/6/10/14/17/18/21 produce dosage-driven chromatin redistribution. Most normal-B-cell-like accessibility landscape, highest TSS-proximal fraction (~0.375).

**Why it's interesting:** The subtype biology creates genuine, reproducible differences in TSS-proximal fraction, motif enrichment, and QC metrics. Agents must discover these from computation rather than asserting from textbook descriptions. The DUX4-ERG distal enhancer program is particularly important because it explains why DUX4-ERG peaks dominate the long tail of the union consensus but fail the 50% majority gate (Story 2).

**Evals:** atac_1a (TSS-proximal fractions), atac_2c (subtype FRiP shifts), atac_5c (PAX5 motif enrichment), atac_7a (H3K27ac accessibility-expression coupling), atac_7b/7d (chromatin state analysis)

**Cross-references:** The subtype biology connects to Story 2 (consensus gating removes subtype enhancers) and Story 7 (motif enrichment reflects lineage identity, not just the "star" factor).

## 6. QC metric interpretation and the dual-borderline pattern

FRiP and TSS enrichment are complementary but not interchangeable QC metrics. FRiP depends on the called peak set (circular), while TSS enrichment uses fixed genome annotations (independent). When they disagree for the same sample, TSS enrichment is more informative because it doesn't depend on which peaks were called.

Several Hyperdiploid samples show a "dual borderline" pattern: simultaneously low FRiP (<0.2) and marginal TSS enrichment (5–8). This should NOT be interpreted as library failure. Instead, Hyperdiploid aneuploidy-associated chromatin redistribution broadens accessible territory, lowering FRiP (signal is spread over more regions) and softening the TSS peak-to-flank ratio. These samples should be retained but flagged for sensitivity analysis.

**Why it's interesting:** The trap tests whether agents make binary QC decisions (pass/fail) or nuanced subtype-aware interpretations. A naive agent removes all borderline samples, losing up to half the Hyperdiploid representation. The correct approach preserves them with caveats, recognizing that the QC pattern reflects biology, not technical failure.

**Evals:** atac_2c (dual-fail interpretation), atac_6b (PCA outlier classification cross-referenced with TSS enrichment)

**Cross-references:** The QC interpretation theme connects to ChIP-seq Story 2 (detection bias as biology). Both test whether agents distinguish technical artifacts from biological signal.

## 7. Motif enrichment reflects lineage identity, not just the "star" factor

PAX5 is the canonical B-cell master regulator, but at distal active enhancers, an ETS-family pioneer (PU.1/SPI1) tops the motif enrichment ranking — not PAX5. In the ATAC-seq evals, PAX5 motif enrichment IS significant across all three B-ALL subtype foregrounds, but it reflects retained B-cell regulatory identity rather than a uniquely subtype-specific oncogenic program. Hyperdiploid shows the strongest PAX5 enrichment because its promoter-proximal accessibility is most normal-B-cell-like.

In the HINT-ATAC footprinting analysis, the top subtype-discriminative motifs are NOT dominated by DUX4-ERG AP-1 (as chromVAR would suggest). Instead, ETV6-RUNX1 contributes the most top discriminators (~7/10), including a bHLH-leading signal, while DUX4-ERG contributes a smaller AP-1-associated subset. The ranking statistic matters: subtype discrimination requires the three-way protection-score range (max - min across subtypes), not single-subtype strength or statistical significance alone.

**Why it's interesting:** Both evals test whether agents compute motif enrichment from the data or assert from disease priors. The PAX5 eval catches agents that assume the "master regulator" must top the enrichment. The HINT-ATAC eval catches agents that project the chromVAR AP-1 result onto a different measurement (footprint protection is not accessibility deviation).

**Evals:** atac_5c (PAX5 motif enrichment), atac_10c (HINT-ATAC three-way footprinting), atac_8a/8b (chromVAR motif analysis)

**Cross-references:** Directly parallels ChIP-seq Story 3 (prior-driven assertion) and K2 (PAX5 not the top motif at enhancers).

## 8. Multi-omic integration requires subtype preservation

The cold-start evals test whether agents can integrate paired RNA+ATAC data while preserving subtype structure. The central principle: pooling subtypes before computing associations attenuates real signal, inflates apparent universal hubs, and distorts private subtype-specific regulatory programs.

Key integration traps:
- **TF regulon hubs (cold_01a):** Building one cohort-wide hub ranking and labeling subtypes afterward collapses private subtype programs into an apparent universal hub signal. The correct approach ranks hubs within each subtype first, then measures recurrence.
- **Cis peak-gene coupling (cold_02a):** Within-subtype absolute coupling is stronger than pooled (ETV6-RUNX1 median |rho| = 0.40 vs cohort median = 0.23), but direction-discordant strong pooled links are rare (~3%). Pooling mostly attenuates, not reverses, cis signal.
- **H3K27ac accessibility-expression coupling (atac_7a):** Agents must restrict peak-gene links to the RNA gene universe (genes present in counts.tsv) before counting. Skipping this inflates distal link counts by ~38% because many GENCODE v19 TSS entries (pseudogenes, lncRNAs) are absent from the quantification.

**Why it's interesting:** Multi-omic integration is the hardest analysis in the benchmark. The 18 paired RNA+ATAC samples (RNAseq_2 excluded because its processed ATAC counterpart is missing) require careful sample matching by numeric suffix, not by column order. Each cold-start eval requires a genuine multi-step computation that cannot be shortcut by reading paper conclusions.

**Evals:** cold_01a (TF regulon hubs), cold_02a (cis coupling), cold_01d (subtype-specific regulatory programs), cold_02b-d (peak-gene linking variants), cold_03a-d (regulatory architecture), cold_04a (cross-validation), cold_x04 (integrative summary), atac_7a (H3K27ac coupling)

**Cross-references:** Connects to WGBS Story 4 (methylation-expression integration) and Story 5 (gene-body vs promoter correlation). All test whether agents can perform genuine multi-omic computation rather than asserting from prior knowledge.

## 9. PCA outlier interpretation requires joint distance-quality reasoning

In PCA of the consensus ATAC-seq count matrix, all 5 of the top-5 most distant samples from their subtype centroids are Hyperdiploid. The correct interpretation requires two layers of reasoning: (a) Hyperdiploid samples with marginal TSS enrichment are likely influenced by technical noise (flag but retain); (b) Hyperdiploid samples with passing TSS enrichment represent genuine within-subtype chromatin heterogeneity from variable aneuploidy (retain with confidence).

The PC1-loading peaks (top 100 by absolute loading) are a mix of promoter-proximal, intermediate, and distal regulatory elements — NOT exclusively far-distal and NOT exclusively promoter-proximal. This composite profile reflects the multi-subtype accessibility axis (DUX4-ERG enhancers, ETV6-RUNX1 promoter targets, V(D)J developmental elements).

**Why it's interesting:** Agents must resist three wrong conclusions: (1) relabeling distant Hyperdiploid samples as another subtype, (2) removing all borderline samples as failed libraries, (3) treating the PCA outlier pattern as a batch effect. The correct answer requires computing centroid distances FIRST, then cross-referencing with TSS enrichment quality SECOND — not ranking by quality score alone.

**Evals:** atac_6b (PCA outliers and PC1 loading interpretation)

**Cross-references:** Connects to Story 6 (QC interpretation) and ChIP-seq Story 2 (detection bias). All test whether agents make nuanced, data-informed interpretations rather than binary decisions.

---

## Summary

| Story | Theme | Evals | Key Trap |
|---|---|---|---|
| 1. Tn5 BED vs BAMPE | Peak calling | atac_1a, 2c, 5a | Wrong input format yields 10x fewer peaks |
| 2. Union vs consensus | Data handling | atac_4a, 4b | 94% of union peaks fail 50% gate; subtype enhancers lost |
| 3. Depth equalization | Methodology | atac_5a, 1a | Post-hoc normalization cannot recover missed peaks |
| 4. Fragment deconvolution | QC → biology | atac_5a | Helical pitch ≠ nucleosome repeat; constrained fits required |
| 5. Subtype biology | Biology | atac_1a, 2c, 5c, 7a, 7b, 7d | DUX4-ERG distal, ETV6-RUNX1 proximal, Hyperdiploid balanced |
| 6. Dual-borderline QC | QC interpretation | atac_2c, 6b | Hyperdiploid aneuploidy mimics technical failure |
| 7. Motif enrichment | Prior vs computation | atac_5c, 10c, 8a, 8b | PAX5 not top; HINT-ATAC ≠ chromVAR |
| 8. Multi-omic integration | Integration | cold_01a-x04, atac_7a | Pooling attenuates subtype signal; RNA universe filtering |
| 9. PCA outlier interpretation | QC interpretation | atac_6b | Joint distance-quality reasoning required |

The 24 ATAC-seq evals divide into three difficulty tiers: **universally hard** (Stories 1, 8: peak-calling convention and multi-omic integration, <20% pass rate), **discriminative** (Stories 2, 4, 7: consensus construction, fragment biology, and motif enrichment, 20–50% pass rate), and **moderate** (Stories 3, 5, 6, 9: depth control, subtype biology, and QC interpretation, 50–80% pass rate).


# ChIP-seq Trap Stories

June 10, 2026. The ChIP-seq set (9 evals, problem 958: epigeneticsbench_RB_chipseq) covers H3K27ac ChIP-seq analysis of a pediatric B-cell acute lymphoblastic leukemia (B-ALL) patient cohort from GSE211631 (Barnett et al. 2023). The dataset consists of 11 patient H3K27ac libraries plus one matched input control, processed through nf-core/chipseq with MACS3 broad-peak calling on hg19. The cohort contains two replicated molecular subtypes — KMT2A-rearranged (n=4, samples 3-6) and BCR-ABL1/Ph+ (n=2, samples 1-2) — plus five single-patient subtypes excluded from differential contrasts. All processing follows the Alder ChIP-seq Tutorial (ciernialab/Alder-ChIPseq-Tutorial) conventions. This snapshot describes the trap architecture organized into 7 stories.

## 1. Input control is not a patient sample

The matched input control (GSM7074430_Input_sample_12) is deeply sequenced (67.9M primary mapped reads) and present in the data bundle alongside the 11 patient H3K27ac BAMs. Multiple evals require agents to exclude it from patient-level rankings while still using it as the MACS3 background for peak calling. Including the input as a 12th "patient" displaces which library leads in depth, peak count, or enrichment rankings, corrupting every downstream answer.

**Why it's interesting:** The control has a dual role — include for peak calling, exclude for patient interpretation. Agents must understand that input DNA measures background noise, not active regulatory signal. The trap fires differently across evals: in A4 it inflates depth ranking, in B1 it changes which sample leads the peak count, in E5 it adds a 12th required sample to the constitutive consensus.

**Evals:** chipseq_A4 (depth normalization), chipseq_B1 (peak abundance), chipseq_E5 (constitutive consensus), chipseq_F1 (super-enhancer counts)

**Cross-references:** The "include for calling, exclude for interpretation" distinction is tested across the full ChIP-seq set and mirrors Story 8 in the CUT&Tag notes (IgG/input control omission).

## 2. Detection bias masquerades as biology

The sample with the most H3K27ac peaks is NOT the most biologically active patient — it is a low-enrichment technical outlier that permissively calls shallow background regions. Sample 10 leads the peak count by more than 2x over the runner-up but has the lowest fraction-of-reads-in-peaks and highest plotFingerprint AUC, the signature of an over-calling library. Agents steeped in the intuition that "more peaks = richer biology" mistake this detection artifact for a genuine regulatory signal.

**Why it's interesting:** The trap cascades through three evals in different forms. In B1, the most-peaks sample is the leading active-mark library — but it's the outlier. In F1, the same sample carries the highest super-enhancer count under the ROSE-lite recipe — because more low-enrichment peaks stitch into more super-enhancer regions. In H3, the strong negative Pearson correlation (r = -0.79) between per-sample peak count and mean per-peak signalValue reveals the detection behavior systematically: samples that call many regions do so by admitting faint regions near the detection floor.

**Evals:** chipseq_B1 (peak abundance ranking), chipseq_F1 (super-enhancer counts), chipseq_H3 (count-intensity anticorrelation)

**Cross-references:** Connects to Story 3 (prior-driven assertion). The same sample's inflated peak set also affects F4 (signal concentration) and E5 (consensus construction).

## 3. Prior-driven assertion defeats computation

Two evals directly test whether agents compute from data or assert from disease priors. In F2, the largest H3K27ac super-enhancer by signal area sits beside a non-coding antisense locus (FAM53B-AS1) — not a canonical B-ALL driver like MYC, IKZF1, or PVT1. Agents steeped in B-ALL biology guess the famous oncogene without computing the ranking. In K2, an ETS-family pioneer program dominates the recurrent distal active-enhancer surface: 17 of the top 20 known-motif enrichments are ETS-family motifs (ETS1, ETV, ERG, FLI1, ELF, ELK, GABPA, SPI1/PU.1), while the canonical B-cell paired-domain factor PAX5 ranks 45th — well outside the leading band. Agents reasoning from "this is B-cell leukemia, so PAX5 must be the top motif" fail completely.

**Why it's interesting:** Both evals exploit the gap between what training data says and what computation reveals. The F2 trap is sharpened because the top two regions are close in signal area, so a wrong signal source (BigWig coverage vs broadPeak enrichment) can swap the winner. The K2 trap requires understanding enhancer biology: the ETS-family pioneer opens and maintains the distal enhancer repertoire, leaving the most recurrent footprint, while PAX5 binds a broader, less-recurrent target set. The eval now has robust binary fields (pax5_outside_leading_band, ets_family_dominates) alongside the numeric evidence (top20_ets_motif_count, pax5_known_motif_rank), so categorical calls and numeric work must both agree.

**Evals:** chipseq_F2 (super-enhancer neighborhood), chipseq_K2 (distal-enhancer motif enrichment)

**Cross-references:** Mirrors WGBS Story 4 (textbook methylation-expression model is wrong) and CUT&Tag Story 10 (prior-driven guessing). Both test computation over recall.

## 4. Signal source determines the answer

The choice of enrichment column — broadPeak signalValue (column 7) vs BigWig coverage area vs other score columns — is the load-bearing methodological decision in several evals. In F1, scoring stitched super-enhancer regions from peak-call enrichment vs coverage-track area changes which sample carries the most super-enhancers. In F2, the same substitution reorders the close top regions and changes which locus is the "largest" super-enhancer. In F4, the eval now explicitly contrasts two surfaces: interval signal mass (width x signalValue) vs enrichment-height-only (signalValue alone). The top 5% of records by interval signal mass hold ~48% of total signal, while the top 5% by signalValue alone hold only ~23% — a dramatic difference showing that broad, moderately enriched domains carry disproportionate mass that height-only ranking misses. In H3, substituting a BigWig coverage average for the per-call MACS signalValue yields an unrelated correlation coefficient.

**Why it's interesting:** The signal-source trap is subtle because all approaches produce plausible-looking numbers — no tool crashes, no obvious error. F4's explicit two-surface design forces agents to understand that occupied span and enrichment height jointly shape which records dominate the strongest tail, rather than treating one or the other as the "correct" signal.

**Evals:** chipseq_F1 (super-enhancer signal source), chipseq_F2 (top-region ranking), chipseq_F4 (interval mass vs height-only concentration), chipseq_H3 (intensity field choice)

**Cross-references:** Analogous to WGBS Story 1 (strand-merging) in that a single data-representation choice cascades through multiple downstream analyses.

## 5. Consensus peak construction and differential semantics

Building a consensus peak set from multiple samples involves subtle choices. In E5, the eval asks for constitutive active-mark regions — positions simultaneously covered by a peak in all 11 patients. The trap is using a pre-merged union-consensus boolean table (which first merges all peaks, then checks sample membership) instead of computing simultaneous basewise all-patient support first, then merging. The two approaches answer different questions because merging first changes interval boundaries before membership is tested.

In L3, the eval now tests a genuine differential H3K27ac analysis between the two replicated subtypes: KMT2A-rearranged (n=4) vs BCR-ABL1/Ph+ (n=2). Agents must correctly identify the replicated contrast groups (excluding single-patient subtypes), run DESeq2 with library-size normalization (-simpleNorm, NOT norm2total) using BOTH a fold-change threshold (|log2FC| > 1) AND FDR < 0.05, then annotate differential regions by TSS distance to isolate distal putative enhancers (>= 2.5 kb). The key finding: distal regions dominate the differential surface, and ~66% of distal differential enhancers are KMT2A-enriched, with the top KMT2A locus being PROM1/CD133 — a canonical stem/progenitor marker of KMT2A-rearranged B-ALL.

**Why it's interesting:** L3 tests the full differential-analysis pipeline: group definition, normalization choice, dual significance threshold, distance annotation, and biological interpretation. Agents that use FDR alone (without fold-change) or norm2total (inappropriate for H3K27ac where signal is comparable across libraries) fail the numeric fields. The PROM1/CD133 finding connects chromatin-level observations to disease biology without overclaiming direct transcription.

**Evals:** chipseq_E5 (constitutive consensus), chipseq_L3 (KMT2A-vs-BCR-ABL1 differential distal enhancers)

**Cross-references:** The consensus-construction question also appears in ATAC-seq (atac_4a). The L3 differential analysis parallels DESeq2 methodology testing across the benchmark.

## 6. Read-depth normalization and subsampling

Read-depth differences across the cohort create both detection-sensitivity confounds and interpretive traps. In A4, agents must normalize 11 patient BAMs to a 15M-read target while carrying one below-target sample (8.7M reads) forward at full depth. The trap has multiple layers: (a) using the shallow outlier as the denominator despite the explicit 15M target; (b) treating the deepest sample (38.8M reads, sample 9) as automatically having the most peak loss, when in fact sample 10 loses the most peaks because it has the largest full-depth peak set; (c) comparing only peak counts rather than computing which full-depth intervals are absent from the normalized set.

In A5, agents must pair the correct alignment stages (raw-aligned reads vs final analysis-ready reads after duplicate/artifact cleanup) to compute the retained-read fraction. Grabbing the wrong stage drives the ratio toward 1.0, erasing the retention signal.

**Why it's interesting:** Subsampling order matters: the 15M normalization must happen to BAMs before peak calling, and peak loss must be computed by interval comparison, not count subtraction. The A5 trap is more subtle — the ratio is a simple division, but the agent must locate the correct numerator and denominator among multiple samtools-stats stages in the MultiQC output.

**Evals:** chipseq_A4 (subsampling and peak loss), chipseq_A5 (retained-read fraction)

**Cross-references:** Depth-normalization traps also appear in CUT&Tag Story 13 (depth confounding in developmental comparison) and ATAC-seq (atac_5a, where pre-peak-calling depth equalization is the key).

## 7. Super-enhancer methodology forks

Super-enhancer calling involves multiple methodology choices that are not interchangeable. The eval set uses a calibrated ROSE-lite recipe: exclude promoter-proximal peaks (abs(Distance to TSS) <= 2500), stitch at 12,500 bp, score by summed width-weighted broadPeak signalValue, and designate the top 5% per sample. Each of these choices is a potential fork:

- **Cutoff philosophy:** The fixed top-5% fraction is not equivalent to the ROSE tangent/knee/inflection cutoff. Agents that apply a tangent cutoff produce a different count.
- **Signal source:** Peak-call enrichment area vs BigWig coverage area (Story 4).
- **Promoter exclusion:** The window size and TSS catalog density affect which peaks survive as enhancer candidates.
- **Stitching distance:** 12,500 bp is standard for H3K27ac but not universal.

**Why it's interesting:** Two evals (F1, F2) share the same ROSE-lite recipe but test different downstream questions. An agent that gets the recipe wrong fails both. The F2 result — that the largest super-enhancer sits at a non-coding locus, not a canonical oncogene — reveals a genuine biological finding about how super-enhancer magnitude is decoupled from oncogenic importance.

**Evals:** chipseq_F1 (per-sample SE counts), chipseq_F2 (cohort max SE)

**Cross-references:** Super-enhancer methodology is not tested in the CUT&Tag or WGBS eval sets; it is ChIP-seq-specific because H3K27ac is the canonical super-enhancer mark.

---

## Summary

| Story | Theme | Evals | Key Trap |
|---|---|---|---|
| 1. Input control scope | Data handling | A4, B1, E5, F1 | Include for calling, exclude for ranking |
| 2. Detection bias as biology | QC interpretation | B1, F1, H3 | Most-peaks sample is lowest-enrichment outlier |
| 3. Prior vs computation | Biology | F2, K2 | Super-enhancer not at oncogene; PAX5 ranks 45th, 17/20 top motifs are ETS |
| 4. Signal source | Methodology | F1, F2, F4, H3 | Interval mass (48%) vs height-only (23%); broadPeak signalValue vs BigWig |
| 5. Consensus & differential | Data handling | E5, L3 | Merge-then-test vs test-then-merge; KMT2A distal enhancers dominate (66%) |
| 6. Depth normalization | Methodology | A4, A5 | Subsampling order; alignment-stage pairing |
| 7. Super-enhancer forks | Methodology | F1, F2 | Top-5% vs tangent cutoff; scoring recipe |

The 9 ChIP-seq evals (problem 958) divide into two difficulty tiers: **hard** (Stories 2, 3, 5-L3: agents must overcome strong priors, recognize technical outliers, and execute full differential pipelines) and **moderate** (Stories 1, 4, 5-E5, 6, 7: agents must make correct methodology choices but the traps are procedural rather than conceptual).


# EpiBench Trap Summary — Cross-Assay Failure Analysis

June 10, 2026. Aggregated across 16 model×harness configurations, ~4,748 total runs, 106 evals.
Each eval is mapped to one or more trap categories; evals may appear in multiple traps.

## Trap Leaderboard (sorted by total failure count)

| Rank | Trap Category | Assay(s) | Evals | Runs | Fail Count | Fail Rate |
|---|---|---|---|---|---|---|
| 1 | Multi-omic integration requires subtype preservation | ATAC | 13 | 574 | 435 | 75.8% |
| 2 | CpG strand-merging catastrophe | WGBS | 7 | 314 | 311 | 99.0% |
| 3 | Prior-driven assertion / textbook model is wrong | All | 10 | 452 | 235 | 52.0% |
| 4 | Depth / normalization confounding | ChIP, ATAC, CUT&Tag | 7 | 305 | 205 | 67.2% |
| 5 | Detection bias masquerades as biology | ChIP, ATAC | 5 | 229 | 197 | 86.0% |
| 6 | Differential analysis methodology (dual threshold) | ChIP, WGBS | 4 | 182 | 180 | 98.9% |
| 7 | Signal source / column substitution | ChIP | 4 | 191 | 174 | 91.1% |
| 8 | Effect-size threshold / platform mismatch | WGBS | 4 | 187 | 158 | 84.5% |
| 9 | Input / IgG control scope | ChIP, CUT&Run | 5 | 223 | 152 | 68.2% |
| 10 | Peak-calling format trap (Tn5 BED vs BAMPE) | ATAC, CUT&Tag | 4 | 182 | 120 | 65.9% |
| 11 | Motif enrichment reflects lineage, not star factor | ATAC, ChIP | 5 | 215 | 118 | 54.9% |
| 12 | Consensus construction semantics | ChIP, ATAC | 3 | 141 | 110 | 78.0% |
| 13 | Spatial heterogeneity of cancer methylation | WGBS | 4 | 176 | 105 | 59.7% |
| 14 | Non-CpG context contamination | WGBS | 4 | 183 | 98 | 53.6% |
| 15 | Genome build / annotation mismatch | WGBS | 5 | 217 | 96 | 44.2% |
| 16 | Fragment-length deconvolution / chromatin biology | ATAC, CUT&Tag | 3 | 137 | 92 | 67.2% |
| 17 | QC metric interpretation / dual-borderline pattern | ATAC | 2 | 88 | 88 | 100.0% |
| 18 | Super-enhancer methodology forks | ChIP | 2 | 96 | 86 | 89.6% |
| 19 | Polycomb switching / cell-line selection | WGBS | 1 | 46 | 22 | 47.8% |

## Tier Classification

### Tier 1: Nearly Universal Failures (>90% fail rate)
These traps defeat essentially all agents regardless of model capability.

| Trap | Fail Rate | Why it's devastating |
|---|---|---|
| QC metric interpretation (dual-borderline) | **100.0%** | No agent reasons jointly about FRiP + TSS enrichment |
| CpG strand-merging catastrophe | **99.0%** | Per-strand Bismark rows silently halve coverage |
| Differential analysis methodology | **98.9%** | Both FC + FDR thresholds required; agents use one or neither |
| Signal source / column substitution | **91.1%** | broadPeak signalValue vs BigWig — all produce plausible numbers |
| Super-enhancer methodology forks | **89.6%** | ROSE tangent vs top-5%; recipe choices compound silently |
| Detection bias as biology | **86.0%** | Most-peaks sample is lowest-enrichment outlier |

### Tier 2: Discriminative Traps (50–90% fail rate)
These traps separate frontier from non-frontier models.

| Trap | Fail Rate | What separates winners from losers |
|---|---|---|
| Effect-size threshold / platform mismatch | **84.5%** | Array-era conventions on WGBS data |
| Consensus construction semantics | **78.0%** | Union vs majority-gated; merge order matters |
| Multi-omic integration | **75.8%** | Pooling subtypes attenuates signal |
| Input / IgG control scope | **68.2%** | Dual-role: include for calling, exclude for ranking |
| Depth / normalization confounding | **67.2%** | Must equalize before peak calling |
| Fragment-length deconvolution | **67.2%** | Constrained fits required; unconstrained EM fails |
| Peak-calling format trap | **65.9%** | Tn5 BED vs BAMPE produces opposite errors per assay |
| Spatial heterogeneity | **59.7%** | Heterochromatin is depleted, not enriched |
| Motif enrichment | **54.9%** | PAX5 not top; HINT-ATAC ≠ chromVAR |
| Non-CpG context contamination | **53.6%** | Same tag, opposite filtering per question |
| Prior-driven assertion | **52.0%** | Compute vs assert; wide variance (0–100% per eval) |

### Tier 3: Moderate Traps (<50% fail rate)
Most frontier models pass these; non-frontier models still struggle.

| Trap | Fail Rate | Why some agents pass |
|---|---|---|
| Polycomb switching / cell-line selection | **47.8%** | Stem-cell reference selection is inferable |
| Genome build / annotation mismatch | **44.2%** | hg19 provenance is discoverable from metadata |

## Cross-Assay Patterns

### Traps that recur across multiple assays

| Trap Pattern | WGBS | ChIP-seq | ATAC-seq | CUT&Tag/Run |
|---|---|---|---|---|
| Prior-driven assertion | c4_paradox, noncanonical_corr, c3_prc2, genebody | F2, K2 | 5c, 10c | — |
| Depth confounding | — | A4, A5 | 5a, 1a | 014a, 014f, 014i |
| Peak-calling format/mode | — | — | 1a, 2c, 5a | 007a |
| Input/control handling | — | A4, B1, E5, F1 | — | 002e |
| Fragment biology | — | — | 5a | 008a, 014b |
| Consensus semantics | — | E5, L3 | 4a | — |

### Hardest individual evals (0% pass rate across all models)

| Eval | Assay | Trap(s) |
|---|---|---|
| chipseq_F2 | ChIP-seq | Prior-driven assertion + Signal source + Super-enhancer forks |
| chipseq_H3 | ChIP-seq | Detection bias + Signal source |
| chipseq_L3 | ChIP-seq | Consensus/differential + Dual threshold |
| atac_2c | ATAC-seq | Detection bias + QC interpretation + Peak-calling format |
| atac_4a | ATAC-seq | Consensus construction |
| atac_5c | ATAC-seq | Motif enrichment (PAX5 not top) |
| atac_6b | ATAC-seq | QC interpretation + PCA outlier |
| atac_7a | ATAC-seq | Multi-omic integration |
| atac_7b | ATAC-seq | Subtype chromatin biology |
| atac_8a | ATAC-seq | Motif enrichment (chromVAR) |
| cold_01d | ATAC-seq | Multi-omic integration |
| cold_02c | ATAC-seq | Multi-omic integration |
| cold_03a | ATAC-seq | Multi-omic integration |
| cold_04a | ATAC-seq | Multi-omic integration |
| cold_x04 | ATAC-seq | Multi-omic integration |
| cpgreport_mean_coverage | WGBS | Strand-merging |
| cpgreport_cross_sample_corr | WGBS | Strand-merging |
| covgz_dmc_count | WGBS | Strand-merging + Differential methodology |
| covgz_cross_sample_corr | WGBS | Strand-merging |
| covgz_extreme_dmc_coverage | WGBS | Strand-merging |
| dmc_count_effect_size_filter | WGBS | Effect-size threshold + Differential methodology |
| dmr_tss_enrichment | WGBS | Genome build + Spatial heterogeneity |
| 008a_fragment_profile_identification | CUT&Tag | Fragment biology |

### Highest-pass individual evals (>90% pass rate)

| Eval | Assay | Pass Rate | Why agents succeed |
|---|---|---|---|
| atac_10c | ATAC-seq | 100% | HINT-ATAC footprinting — computation-friendly |
| noncanonical_fraction | WGBS | 91.1% | Simple XM-tag context filtering |
| c4_paradox_hypo_downregulated | WGBS | 89.4% | Cluster membership is computable |

## Key Takeaways

1. **Multi-omic integration is the #1 failure mode by volume** (435 failures), driven by 13 cold-start + ATAC evals that require genuine RNA+ATAC pairing with subtype preservation.

2. **Strand-merging is the #1 failure mode by rate** (99.0%), a single data-representation error that cascades through 7 WGBS evals and defeats all 16 model configurations.

3. **Six trap categories have >85% fail rates**, meaning they defeat nearly all agents: QC interpretation, strand-merging, differential methodology, signal source, super-enhancer forks, and detection bias.

4. **Prior-driven assertion is the most heterogeneous trap** (52.0% aggregate, but ranging from 0% to 100% per eval). Some evals in this category are trivially easy (atac_10c: 100% pass, c4_paradox: 89% pass) while others are universally hard (chipseq_F2: 0%, atac_5c: 0%).

5. **ChIP-seq evals cluster at the extremes**: either very easy (A5: 69%, E5: 65%, K2: 76%) or universally hard (F2: 0%, H3: 0%, L3: 0%).

6. **Three trap types cross all assay boundaries**: prior-driven assertion, depth confounding, and peak-calling format/mode. These are the most generalizable failure modes in the benchmark.

