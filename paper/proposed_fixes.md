# Proposed Fixes for Results & Discussion Inconsistencies

Each section shows the **location**, the **current text**, and the **proposed replacement**. Review and polish these, then I'll merge them into `main.tex`.

---

## Fix 1: "cold-response ATAC" → "cold-start integrative ATAC"

**Location:** Table 1, line 190 (`paper/main.tex`)

**Current:**
```
B-ALL ATAC, cold-response ATAC
```

**Proposed:**
```
B-ALL ATAC (GSE161501, primary + cold-start integrative)
```

**Rationale:** The `cold_*` evals are cold-start multi-omic integration tasks on the same B-ALL dataset (GSE161501, Diedrich 2021), not a separate cold-response (temperature stress) experiment. The trap analysis explicitly says: "Cold-start evals (`cold_*`) test integrative RNA+ATAC analysis including TF regulon hubs, cis peak-gene coupling, and subtype-specific regulatory architecture."

---

## Fix 2: Failure-mode categories need grounding

**Location:** Lines 383–391 (subsection "Errors trace to assay-specific choices")

**Current:**
```
Manual review localizes endpoint misses to concrete analysis decisions. Review
coverage is incomplete (25/106 evaluations), and the labels are task-level
diagnostics rather than per-run error calls. Within that reviewed subset, the
most common error types were incorrect statistic or ranking (14 evaluations;
33.9% pass rate), unstable threshold choice (9; 31.9%), biological prior
over provided evidence (8; 45.6%), gene/peak identifier mismatch (6; 0.0%),
and incorrect biological unit or reference set (6; 42.7%). These are not
generic reasoning failures. They are local choices about which data layer,
feature identity, comparison group, threshold, or biological prior should
control the final answer.
```

**Proposed:**
```
Manual review localizes endpoint misses to concrete analysis decisions. Review
coverage spans 25/106 evaluations, and evaluations carry multiple trap labels
because a single task can test several decision points. Within the reviewed
subset, we identify five recurring error families: prior-driven assertion ---
substituting textbook biology for computation (10 evaluations; 48.0\% aggregate
fail rate, ranging from 0\% to 100\% per eval); depth or normalization
confounding --- equalizing after feature detection rather than before (7
evaluations; 67.2\%); format or mode selection --- the same tool flag producing
opposite errors depending on assay context (4 evaluations; 65.9\%); signal
source substitution --- choosing the wrong enrichment column or coverage track
(4 evaluations; 91.1\%); and strand or context mishandling in bisulfite data (7
evaluations; 99.0\%). These are not generic reasoning failures. They are local
choices about which parameter, data layer, or biological prior should control
the final answer.
```

**Rationale:** The original five categories ("incorrect statistic or ranking," "unstable threshold choice," etc.) don't map onto either the Trap_Analysis.md taxonomy or the summary data. The replacement uses the actual cross-assay trap categories from the trap leaderboard with real fail rates. The "evaluations carry multiple trap labels" sentence explains why label-counts exceed 25.

---

## Fix 3: "gene/peak identifier mismatch (6; 0.0%)" → remove or replace

**Location:** Same paragraph as Fix 2

**Note:** This is handled by Fix 2 above. The "gene/peak identifier mismatch" category has no clear grounding in the trap analysis — the 0%-pass evals fail for diverse reasons (strand-merging, multi-omic integration, detection bias), not a unified "identifier mismatch" mechanism.

---

## Fix 4: ChIP-seq source description too vague

**Location:** Table 1, line 195

**Current:**
```
ChIP-seq workflow snapshots
```

**Proposed:**
```
B-ALL H3K27ac (GSE211631)
```

**Rationale:** The trap analysis identifies this as GSE211631 (Barnett et al. 2023), H3K27ac ChIP-seq of 11 pediatric B-ALL patients + 1 input control. The other entries already name specific datasets or biology.

---

## Fix 5: ChIP-seq "easiest" claim needs nuance

**Location:** Lines 309–310

**Current:**
```
ChIP-seq was easiest in this inventory, driven in part by high performance on
quality-control tasks.
```

**Proposed:**
```
ChIP-seq had the highest aggregate pass rate, but this reflects a bimodal
distribution: A5 (69\%), E5 (65\%), and K2 (76\%) pass easily, while F2, H3,
and L3 have 0\% pass rates across all models. The aggregate is driven by
evaluations where the methodology is procedural rather than conceptual.
```

**Rationale:** Calling it "easiest" is misleading when 30% of ChIP evals (3/10) have 0% pass. The trap analysis confirms this bimodality (Key Takeaway #5).

---

## Fix 6: "despite familiar peak-level data" → specific mechanism

**Location:** Lines 302–304

**Current:**
```
ATAC-seq was the hardest aggregate despite familiar peak-level data,
because many tasks required preserving the correct sample, peak, or contrast
definition through secondary analysis.
```

**Proposed:**
```
ATAC-seq had the lowest aggregate pass rate (22.8\%), driven by two dominant
failure modes: multi-omic integration tasks that require subtype-preserving
RNA+ATAC pairing (75.8\% fail rate across 13 evaluations), and the Tn5
insertion-site convention where agents feed paired-end BAMs directly to MACS3
instead of extracting single-bp cut sites, producing $\sim$10$\times$ fewer peaks.
```

**Rationale:** "Familiar peak-level data" is an unsupported judgment. The actual traps are specific and documented: multi-omic integration (Story 8, #1 by volume) and Tn5 BED format (Story 1).

---

## Fix 7: Discussion `\new{}` references `--keep-dup` without Results grounding

**Location:** Lines 451–457 (first `\new{}` paragraph in Discussion)

**Current (excerpt):**
```
\texttt{--local} vs \texttt{end-to-end}, \texttt{-f BAMPE} vs \texttt{-f BAM},
\texttt{--broad} vs narrow, or the appropriate \texttt{--keep-dup} setting.
```

**Proposed:**
```
\texttt{--local} vs \texttt{end-to-end} for spike-in alignment,
\texttt{-f BAMPE} vs Tn5 insertion-site BED for ATAC-seq peak calling,
\texttt{--broad} vs narrow for domain-spanning marks, or pre- vs
post-peak-calling depth equalization.
```

**Rationale:** `--keep-dup` is never mentioned in the Results. Replacing it with "depth equalization" connects to the actual Results content (normalization confounding, 67.2% fail). Each flag now maps to a specific trap described in the Results.

---

## Fix 8: "progressive-difficulty" claims need Results anchoring

**Location:** Lines 469–476 (third `\new{}` paragraph in Discussion)

**Current:**
```
\new{The progressive-difficulty design is validated by the trap analysis.
Procedural evaluations saturate at the ceiling model (100\% pass, requiring
hardening), scientific-judgment evaluations discriminate (30--50\% pass at
ceiling), and conceptual-biology evaluations defeat all models (0\% pass,
probing future capability). As weaker models are tested, failures should
migrate from the decision layer (``computed correctly but chose wrong'') to
the computation layer (``cannot compute at all''), producing the graduated
difficulty curve needed for meaningful model separation.}
```

**Proposed:**
```
\new{The progressive-difficulty design is validated by the failure
distribution. Of 106 evaluations, 21 have 0\% pass rates across all 16
model-harness pairs --- these are dominated by strand-merging catastrophes,
multi-omic integration, and signal-source traps where no current agent
overcomes the underlying scientific-judgment barrier. At the other extreme,
GPT-5.5 / Pi passes 38/106 evaluations on all three replicates, indicating
stable mastery of procedural tasks. The middle band (30--50\% pass at the
leading model) concentrates in discriminative traps --- spike-in alignment
mode, depth confounding, and prior-driven assertion --- where the ceiling
model sometimes computes the correct answer but discards it in favor of a
more familiar alternative.}
```

**Rationale:** The current text uses vague tier names ("procedural," "scientific-judgment," "conceptual-biology") that aren't defined in the Results. The replacement anchors the progressive-difficulty claim in actual numbers and specific trap categories from the Results.

---

## Fix 9: Verify figure file references

**Location:** Lines 243, 321, 367–368, 417–419

**Action needed:** Confirm that these files actually exist in `paper/figures/`:
- `figures/fig4.pdf` (was previously `fig4a.pdf` + `fig4c.pdf`)
- `figures/fig5a.pdf`, `fig5b.pdf`, `fig5c.pdf`
- `figures/fig6a.pdf`, `fig6b.pdf`
- `figures/fig7a.pdf`, `fig7b.pdf`

If these were regenerated with new names after the latest repo pull, this is fine. Otherwise they'll produce missing-figure errors in the PDF. Let me know and I'll verify.

---

## Summary of changes

| Fix | Severity | Type |
|-----|----------|------|
| 1. cold-response → cold-start | High | Factual error |
| 2. Failure-mode categories | High | Data mismatch |
| 3. (Handled by Fix 2) | High | — |
| 4. ChIP source label | Medium | Vagueness |
| 5. ChIP "easiest" | Medium | Misleading |
| 6. ATAC "familiar" | Medium | Unsupported judgment |
| 7. `--keep-dup` in Discussion | Medium | Grounding gap |
| 8. Progressive-difficulty | Medium | Grounding gap |
| 9. Figure files | Low | Verify only |
