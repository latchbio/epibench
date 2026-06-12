#!/usr/bin/env python3
"""Generate all EpiBench paper figures from summary tables.

Outputs all figures to ROOT/figures/ named by paper panel (fig1a, fig1b, etc.).
Uses correct epigenomics task categories from eval_task_categories.tsv.

Paper figure structure:
  Figure 1 (topline): 1a = model leaderboard, 1b = assay×task, 1c = runtime scatter
  Figure 4 (main results): 4a = pass rate, 4b = balanced design, 4c = replicate heatmap
  Figure 5 (source/horizon): 5a = assay type bar, 5b = assay×task heatmap, 5c = eval count by source
  Figure 6 (partial credit): 6a = dumbbell, 6b = eval difficulty, 6c = failure modes
"""
from __future__ import annotations

import os
import textwrap
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib-cache")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.font_manager import FontProperties
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.ticker import FuncFormatter

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "analysis_outputs" / "epi_manifest_updated_summary"
FIGURES = ROOT / "paper" / "figures"

# Color palette
TEXT = "#15191F"
MUTED = "#5F6872"
GRID = "#D9DEE5"
AXIS = "#AFA89B"
WARM = "#F7F4F3"
LINE = "#DDD7CB"
ACCENT = "#A95F3D"
ACCENT_LIGHT = "#C97745"
TEAL = "#2A9D8F"
TEAL_DARK = "#19736A"
VIOLET = "#7267C8"
GRAY = "#B8B2AA"
GRAY_DARK = "#8D867E"
PAPER_WHITE = "#FFFFFF"

FAMILY_COLORS = {
    "OpenAI": "#171511",
    "Anthropic": ACCENT_LIGHT,
    "Gemini": TEAL,
    "xAI": VIOLET,
    "Kimi": "#B89142",
}

KIT_COLORS = {
    "atacseq": ACCENT,
    "chipseq": GRAY_DARK,
    "cuttag_cutrun": VIOLET,
    "methylseq": TEAL,
}

TASK_COLORS = {
    "secondary_analysis": ACCENT,
    "qc": TEAL,
    "chromatin_state_analysis": VIOLET,
    "peak_calling": "#B89142",
    "genomic_annotation": GRAY_DARK,
    "differential_methylation": "#D14B4B",
    "alignment": "#4B8BD1",
    "visualization": "#4CAF50",
}

# Font setup
SERIF_STACK = ["DejaVu Serif", "serif"]
MONO_STACK = ["DejaVu Sans Mono", "monospace"]
SERIF = FontProperties(family=SERIF_STACK)
SERIF_BOLD = FontProperties(family=SERIF_STACK, weight="bold")
MONO = FontProperties(family=MONO_STACK)

plt.rcParams.update({
    "font.family": SERIF_STACK,
    "font.serif": SERIF_STACK,
    "font.monospace": MONO_STACK,
    "font.size": 8.0,
    "figure.facecolor": PAPER_WHITE,
    "axes.facecolor": PAPER_WHITE,
    "savefig.facecolor": PAPER_WHITE,
    "savefig.edgecolor": PAPER_WHITE,
    "axes.edgecolor": AXIS,
    "axes.labelcolor": TEXT,
    "axes.titlecolor": TEXT,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "text.color": TEXT,
    "axes.grid": True,
    "grid.color": GRID,
    "grid.linewidth": 0.58,
    "grid.alpha": 1.0,
    "axes.axisbelow": True,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "svg.fonttype": "none",
})

CALLOUT = {
    "boxstyle": "round,pad=0.18,rounding_size=0.05",
    "facecolor": "#FFFFFF",
    "edgecolor": "#D3CCBE",
    "linewidth": 0.42,
    "alpha": 0.98,
}


def serif_prop(size: float, *, bold: bool = False) -> FontProperties:
    return FontProperties(family=SERIF_STACK, weight="bold" if bold else "normal", size=size)


def save_all(fig: plt.Figure, stem: str) -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    for ext in ("pdf", "svg", "png"):
        fig.savefig(FIGURES / f"{stem}.{ext}", dpi=520)
    plt.close(fig)
    print(f"  Saved: {stem}")


def clean(ax: plt.Axes, *, y_grid: bool = False) -> plt.Axes:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(AXIS)
    ax.spines["bottom"].set_color(AXIS)
    ax.tick_params(axis="both", length=3, width=0.65, colors=MUTED)
    ax.yaxis.grid(y_grid)
    ax.xaxis.grid(True)
    for lab in ax.get_xticklabels():
        lab.set_fontproperties(MONO)
    return ax


def percent_axis(ax: plt.Axes, xmax: float, step: float = 0.1) -> None:
    ax.set_xlim(0, xmax)
    ax.set_xticks(np.arange(0, xmax + 1e-9, step))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, pos: f"{x * 100:.0f}%"))


def panel_label(ax: plt.Axes, letter: str, x: float = -0.09, y: float = 1.04) -> None:
    ax.text(x, y, letter, transform=ax.transAxes, ha="left", va="bottom",
            fontsize=10.8, fontproperties=SERIF_BOLD, color=TEXT)


def add_bar_cis(ax: plt.Axes, df: pd.DataFrame, y: np.ndarray) -> None:
    x = df["pass_rate"].to_numpy()
    low = df["pass_rate_wilson_low"].to_numpy()
    high = df["pass_rate_wilson_high"].to_numpy()
    ax.errorbar(x, y, xerr=[x - low, high - x], fmt="none",
                ecolor=TEXT, elinewidth=0.58, capsize=1.55, capthick=0.58, zorder=4)


def model_family(model: str) -> str:
    value = str(model).lower()
    if "gpt" in value or value.startswith("openai/"):
        return "OpenAI"
    if "claude" in value or value.startswith("anthropic/"):
        return "Anthropic"
    if "gemini" in value:
        return "Gemini"
    if "grok" in value or value.startswith("xai/"):
        return "xAI"
    if "kimi" in value:
        return "Kimi"
    return "OpenAI"


def model_label(model: str, harness: str, *, short: bool = False) -> str:
    raw = str(model).split("/")[-1]
    labels = {
        "gpt-5.5": "GPT-5.5",
        "gpt-5.4": "GPT-5.4",
        "claude-opus-4-8_max": "Claude Opus 4.8 Max",
        "claude-opus-4-8": "Claude Opus 4.8",
        "claude-opus-4-7": "Claude Opus 4.7",
        "claude-opus-4-6": "Claude Opus 4.6",
        "claude-sonnet-4-6": "Claude Sonnet 4.6",
        "gemini-3.5-flash": "Gemini 3.5 Flash",
        "gemini-3.1-pro-preview": "Gemini 3.1 Pro",
        "grok-4.20-0309-reasoning": "Grok 4.20 reasoning",
        "grok-4.3": "Grok 4.3",
        "kimi-k2p6": "Kimi K2P6",
    }
    short_labels = {
        "gpt-5.5": "GPT-5.5",
        "gpt-5.4": "GPT-5.4",
        "claude-opus-4-8_max": "Opus 4.8 Max",
        "claude-opus-4-8": "Opus 4.8",
        "claude-opus-4-7": "Opus 4.7",
        "claude-opus-4-6": "Opus 4.6",
        "claude-sonnet-4-6": "Sonnet 4.6",
        "gemini-3.5-flash": "Gemini 3.5",
        "gemini-3.1-pro-preview": "Gemini 3.1",
        "grok-4.20-0309-reasoning": "Grok 4.20",
        "grok-4.3": "Grok 4.3",
        "kimi-k2p6": "Kimi K2P6",
    }
    base = (short_labels if short else labels).get(raw, raw)
    harness_labels = {
        "pi": "Pi",
        "openai-codex": "Codex" if short else "OpenAI Codex",
        "claude-code": "Claude Code",
    }
    return f"{base} / {harness_labels.get(harness, harness)}"


def kit_label(kit: str, *, short: bool = False) -> str:
    if short:
        return {
            "atacseq": "ATAC",
            "chipseq": "ChIP",
            "cuttag_cutrun": "CT&CR",
            "methylseq": "Methyl",
        }.get(kit, kit)
    return {
        "atacseq": "ATAC-seq",
        "chipseq": "ChIP-seq",
        "cuttag_cutrun": "CUT&Tag/CUT&RUN",
        "methylseq": "Methylation-seq",
    }.get(kit, kit)


def task_label(task: str, *, short: bool = False) -> str:
    if short:
        return {
            "secondary_analysis": "Secondary",
            "qc": "QC",
            "chromatin_state_analysis": "Chromatin state",
            "peak_calling": "Peak calling",
            "genomic_annotation": "Annotation",
            "differential_methylation": "Diff. meth.",
            "alignment": "Alignment",
            "visualization": "Visualization",
        }.get(task, task.replace("_", " "))
    return {
        "secondary_analysis": "Secondary analysis",
        "qc": "QC",
        "chromatin_state_analysis": "Chromatin state analysis",
        "peak_calling": "Peak calling",
        "genomic_annotation": "Genomic annotation",
        "differential_methylation": "Differential methylation",
        "alignment": "Alignment",
        "visualization": "Visualization",
    }.get(task, task.replace("_", " "))


def source_label(source: str) -> str:
    """Source labels include assay type for clarity."""
    return {
        "atac": "B-ALL (ATAC-seq)",
        "cold": "Cold-response (ATAC-seq)",
        "chipseq": "ChIP-seq",
        "gse149608": "GSE149608 (Methylation-seq)",
        "gse149609": "GSE149609 (Methylation-seq)",
        "zebrafish": "Zebrafish (CUT&Tag/CUT&RUN)",
    }.get(source, source)


# ═══════════════════════════════════════════════════════════════════════════════
# FIGURE 1: Topline Benchmark Performance
# ═══════════════════════════════════════════════════════════════════════════════

def fig1a() -> None:
    """1a: Pass rate by model-harness pair."""
    df = pd.read_csv(DATA / "model_summary_available_runs.csv").sort_values("pass_rate", ascending=False)
    df["label"] = [model_label(m, h) for m, h in zip(df["model"], df["harness"])]
    df["rank"] = np.arange(1, len(df) + 1)
    plot = df.sort_values("pass_rate", ascending=True).reset_index(drop=True)
    y = np.arange(len(plot))
    colors = [ACCENT if rank <= 3 else GRAY for rank in plot["rank"]]

    fig, ax = plt.subplots(figsize=(7.5, 3.75))
    ax.barh(y, plot["pass_rate"], height=0.55, color=colors, edgecolor="none", alpha=0.96)
    add_bar_cis(ax, plot, y)
    ax.set_yticks(y)
    ax.set_yticklabels(plot["label"], fontsize=5.5, fontproperties=SERIF, color=TEXT)
    percent_axis(ax, 0.70)
    ax.set_xlabel("Pass rate (106 evaluations, 3 replicates each)", fontproperties=SERIF, labelpad=4, fontsize=6)
    ax.tick_params(axis="x", labelsize=5.5)
    ax.yaxis.grid(False)
    clean(ax)
    for lab in ax.get_yticklabels():
        lab.set_fontproperties(SERIF)
        lab.set_color(TEXT)
    for yi, row in zip(y, plot.itertuples(index=False)):
        label_x = min(max(row.pass_rate_wilson_high + 0.018, row.pass_rate + 0.045), 0.615)
        ax.text(label_x, yi,
                f"{row.pass_rate * 100:.1f}%  {int(row.pass_n)}/{int(row.n_runs)}",
                va="center", ha="left", fontsize=5.0, fontproperties=MONO, bbox=CALLOUT)
    fig.tight_layout()
    save_all(fig, "fig1a")


def fig1b() -> None:
    """1b: Pass rate by assay type × task category."""
    df = pd.read_csv(DATA / "summary_by_kit_task.csv").sort_values("pass_rate", ascending=False)
    df["label"] = [f"{kit_label(k, short=True)}: {task_label(t, short=True)}" for k, t in zip(df["kit"], df["task_family"])]
    plot = df.sort_values("pass_rate", ascending=True).reset_index(drop=True)
    y = np.arange(len(plot))
    colors = [KIT_COLORS.get(k, GRAY) for k in plot["kit"]]
    alpha = [0.50 if n <= 1 else 0.92 for n in plot["n_evals"]]

    fig, ax = plt.subplots(figsize=(5.0, 3.5))
    for yi_val, row, color, a in zip(y, plot.itertuples(index=False), colors, alpha):
        ax.barh(yi_val, row.pass_rate, height=0.56, color=color, alpha=a, edgecolor="none")
    add_bar_cis(ax, plot, y)
    ax.set_yticks(y)
    ax.set_yticklabels(plot["label"], fontsize=5.5, fontproperties=SERIF, color=TEXT)
    percent_axis(ax, 1.0, step=0.25)
    ax.set_xlabel("Pass rate", fontproperties=SERIF, labelpad=3, fontsize=6.5)
    ax.tick_params(axis="x", labelsize=5.5)
    ax.yaxis.grid(False)
    clean(ax)
    for lab in ax.get_yticklabels():
        lab.set_fontproperties(SERIF)
        lab.set_color(TEXT)
    fig.tight_layout()
    save_all(fig, "fig1b")


def fig1c() -> None:
    """1c: Pass rate vs median runtime scatter. Same height as 1b."""
    df = pd.read_csv(DATA / "model_summary_available_runs.csv").copy()
    df["label"] = [model_label(m, h, short=True) for m, h in zip(df["model"], df["harness"])]
    df["family"] = df["model"].map(model_family)
    df["runtime_min"] = df["median_duration_s"] / 60.0

    fig, ax = plt.subplots(figsize=(2.8, 3.5))
    for fam, group in df.groupby("family", sort=False):
        ax.scatter(group["runtime_min"], group["pass_rate"],
                   s=18, color=FAMILY_COLORS.get(fam, GRAY_DARK),
                   edgecolor="#FFFFFF", linewidth=0.45, alpha=0.90, zorder=3, label=fam)

    select_labels = {
        "GPT-5.5 / Pi": (4, 7, "left"),
        "GPT-5.5 / Codex": (4, 11, "left"),
        "GPT-5.4 / Pi": (4, -10, "left"),
        "Opus 4.8 Max / Pi": (-25, -18, "right"),
        "Grok 4.3 / Pi": (4, 4, "left"),
    }
    for row in df.itertuples(index=False):
        if row.label not in select_labels:
            continue
        dx, dy, ha = select_labels[row.label]
        ax.annotate(
            row.label.replace(" / Pi", "").replace(" / Codex", " Codex"),
            (row.runtime_min, row.pass_rate),
            xytext=(dx, dy), textcoords="offset points", ha=ha, va="center",
            fontsize=5.5, fontproperties=SERIF, color=MUTED,
            arrowprops={"arrowstyle": "-", "linewidth": 0.35, "color": LINE, "shrinkA": 2, "shrinkB": 2},
        )

    ax.set_xlim(0, 18.0)
    ax.set_ylim(0.10, 0.55)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: f"{x * 100:.0f}%"))
    ax.set_xlabel("Median runtime (min)", fontproperties=SERIF, labelpad=3, fontsize=7)
    ax.set_ylabel("Pass rate", fontproperties=SERIF, labelpad=3, fontsize=7)
    ax.legend(frameon=False, loc="lower right", prop=serif_prop(5.5), handletextpad=0.4)
    clean(ax, y_grid=True)
    fig.tight_layout()
    save_all(fig, "fig1c")


# ═══════════════════════════════════════════════════════════════════════════════
# FIGURE 4: Main Results (pass rate, balanced, replicate)
# ═══════════════════════════════════════════════════════════════════════════════

def fig4a() -> None:
    """4a: Run-level pass rate by model-harness pair."""
    available = pd.read_csv(DATA / "model_summary_available_runs.csv").sort_values("pass_rate", ascending=False)
    available["label"] = [model_label(m, h, short=True) for m, h in zip(available["model"], available["harness"])]
    available["rank"] = np.arange(1, len(available) + 1)
    plot = available.sort_values("pass_rate", ascending=True).reset_index(drop=True)
    y = np.arange(len(plot))
    colors = [ACCENT if rank <= 3 else GRAY for rank in plot["rank"]]

    fig, ax = plt.subplots(figsize=(4.5, 3.5))
    ax.barh(y, plot["pass_rate"], height=0.52, color=colors, edgecolor="none", alpha=0.96)
    add_bar_cis(ax, plot, y)
    ax.set_yticks(y)
    ax.set_yticklabels(plot["label"], fontsize=5.8, fontproperties=SERIF, color=TEXT)
    percent_axis(ax, 0.70, 0.10)
    ax.set_xlabel("Run-level pass rate", fontproperties=SERIF, labelpad=4, fontsize=6.5)
    ax.tick_params(axis="x", labelsize=5.5)
    clean(ax)
    ax.yaxis.grid(False)
    for lab in ax.get_yticklabels():
        lab.set_fontproperties(SERIF)
        lab.set_color(TEXT)
    for yi, row in zip(y, plot.itertuples(index=False)):
        ax.text(min(row.pass_rate_wilson_high + 0.018, 0.640), yi,
                f"{int(row.pass_n)}/{int(row.n_runs)}",
                ha="left", va="center", fontsize=5.0, fontproperties=MONO, color=MUTED)
    fig.tight_layout()
    save_all(fig, "fig4a")


def fig4b() -> None:
    """4b: Balanced-design pass rate. Same height as 4a."""
    common = pd.read_csv(DATA / "model_summary_common_instances.csv").sort_values("pass_rate", ascending=False)
    common["label"] = [model_label(m, h, short=True) for m, h in zip(common["model"], common["harness"])]
    common["rank"] = np.arange(1, len(common) + 1)
    plot = common.sort_values("pass_rate", ascending=True).reset_index(drop=True)
    y = np.arange(len(plot))
    colors = [ACCENT if rank <= 3 else GRAY for rank in plot["rank"]]

    fig, ax = plt.subplots(figsize=(2.8, 4.2))
    ax.barh(y, plot["pass_rate"], height=0.52, color=colors, edgecolor="none", alpha=0.96)
    add_bar_cis(ax, plot, y)
    ax.set_yticks([])
    percent_axis(ax, 0.70, 0.10)
    ax.set_xlabel("Balanced-design pass rate", fontproperties=SERIF, labelpad=4, fontsize=7)
    clean(ax)
    ax.yaxis.grid(False)
    for yi, row in zip(y, plot.itertuples(index=False)):
        ax.text(min(row.pass_rate_wilson_high + 0.018, 0.640), yi,
                f"{int(row.pass_n)}/{int(row.n_runs)}",
                ha="left", va="center", fontsize=5.0, fontproperties=MONO, color=MUTED)
    fig.subplots_adjust(left=0.06, right=0.985, bottom=0.10, top=0.985)
    save_all(fig, "fig4b")


def fig4c() -> None:
    """4c: Replicate robustness heatmap. Same height as 4a/4b."""
    available = pd.read_csv(DATA / "model_summary_available_runs.csv").sort_values("pass_rate", ascending=False)
    repl = pd.read_csv(DATA / "replicate_robustness_by_model.csv")
    available["label"] = [model_label(m, h, short=True) for m, h in zip(available["model"], available["harness"])]

    heat = available[["model_harness", "label"]].merge(
        repl[["model_harness", "any_pass_rate", "majority_pass_rate", "all_pass_rate", "n_eval_model_pairs"]],
        on="model_harness", how="left",
    )
    cols = ["any_pass_rate", "majority_pass_rate", "all_pass_rate"]
    matrix = heat[cols].to_numpy()

    fig, ax = plt.subplots(figsize=(2.8, 3.5))
    cmap = LinearSegmentedColormap.from_list("replicate", [WARM, "#D7AE96", ACCENT])
    ax.imshow(matrix, aspect="auto", cmap=cmap, vmin=0.10, vmax=0.70)
    ax.set_xticks(range(3))
    ax.set_xticklabels(["Any", "Maj.", "All"], fontsize=6.0, fontproperties=SERIF)
    ax.set_yticks([])
    ax.tick_params(length=0)

    for i in range(matrix.shape[0]):
        n = int(heat.loc[i, "n_eval_model_pairs"])
        for j in range(3):
            value = matrix[i, j]
            color = "#FFFFFF" if value > 0.48 else TEXT
            ax.text(j, i, f"{round(value * n):.0f}/{n}",
                    ha="center", va="center", fontsize=4.8, fontproperties=MONO, color=color)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_xlabel("Replicate rate", fontproperties=SERIF, labelpad=5, fontsize=6.5)
    ax.grid(False)
    fig.tight_layout()
    save_all(fig, "fig4c")


# ═══════════════════════════════════════════════════════════════════════════════
# FIGURE 5: Source / Assay / Horizon
# ═══════════════════════════════════════════════════════════════════════════════

def fig5a() -> None:
    """5a: Pass rate by assay type. Height matches 5b/5c."""
    df = pd.read_csv(DATA / "summary_by_kit.csv").sort_values("pass_rate", ascending=False)
    df["label"] = df["kit"].map(kit_label)
    plot = df.sort_values("pass_rate", ascending=True).reset_index(drop=True)
    y = np.arange(len(plot))
    colors = [KIT_COLORS.get(k, GRAY) for k in plot["kit"]]

    fig, ax = plt.subplots(figsize=(2.8, 2.4))
    ax.barh(y, plot["pass_rate"], height=0.56, color=colors, edgecolor="none", alpha=0.92)
    add_bar_cis(ax, plot, y)
    ax.set_yticks(y)
    ax.set_yticklabels(plot["label"], fontsize=6.5, fontproperties=SERIF, color=TEXT)
    percent_axis(ax, 0.65, 0.20)
    ax.set_xlabel("Pass rate", fontproperties=SERIF, labelpad=3, fontsize=7)
    ax.yaxis.grid(False)
    clean(ax)
    for lab in ax.get_yticklabels():
        lab.set_fontproperties(SERIF)
        lab.set_color(TEXT)
    for yi, row in zip(y, plot.itertuples(index=False)):
        n_text = f"{int(row.n_evals)}"
        ax.text(min(row.pass_rate_wilson_high + 0.015, 0.60), yi,
                f"{row.pass_rate * 100:.0f}%",
                ha="left", va="center", fontsize=5.5, fontproperties=MONO, color=MUTED)
    fig.tight_layout()
    save_all(fig, "fig5a")


def fig5b() -> None:
    """5b: Assay type × task category heatmap. Same height as 5a/5c."""
    df = pd.read_csv(DATA / "summary_by_kit_task.csv")
    kits = ["atacseq", "chipseq", "cuttag_cutrun", "methylseq"]
    tasks = ["qc", "alignment", "peak_calling", "chromatin_state_analysis",
             "genomic_annotation", "secondary_analysis", "differential_methylation", "visualization"]

    mat = np.full((len(kits), len(tasks)), np.nan)
    eval_counts = np.zeros_like(mat)
    for i, k in enumerate(kits):
        for j, t in enumerate(tasks):
            sub = df[(df["kit"] == k) & (df["task_family"] == t)]
            if not sub.empty:
                mat[i, j] = sub["pass_rate"].iloc[0]
                eval_counts[i, j] = sub["n_evals"].iloc[0]

    fig, ax = plt.subplots(figsize=(4.8, 2.4))
    cmap = LinearSegmentedColormap.from_list("kit_task", [WARM, "#D8B09D", ACCENT])
    ax.imshow(np.ma.masked_invalid(mat), aspect="auto", cmap=cmap, vmin=0, vmax=0.90)
    ax.set_xticks(range(len(tasks)))
    ax.set_xticklabels([task_label(t, short=True) for t in tasks],
                       fontsize=5.2, fontproperties=SERIF, rotation=35, ha="right")
    ax.set_yticks(range(len(kits)))
    ax.set_yticklabels([kit_label(k) for k in kits], fontsize=6.0, fontproperties=SERIF)
    ax.tick_params(length=0)

    for i in range(len(kits)):
        for j in range(len(tasks)):
            if np.isnan(mat[i, j]):
                ax.text(j, i, "—", ha="center", va="center", fontsize=5.5, fontproperties=MONO, color="#A9A39C")
            else:
                color = "#FFFFFF" if mat[i, j] > 0.50 else TEXT
                ax.text(j, i, f"{mat[i, j] * 100:.0f}%",
                        ha="center", va="center", fontsize=5.5, fontproperties=MONO, color=color)

    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_xticks(np.arange(-0.5, len(tasks), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(kits), 1), minor=True)
    ax.grid(which="minor", color="#FFFFFF", linewidth=1.2)
    ax.grid(False)
    fig.tight_layout()
    save_all(fig, "fig5b")


def fig5c() -> None:
    """5c: Evaluation count by assay type."""
    inv = pd.read_csv(DATA / "eval_inventory.csv")
    kit_order = ["atacseq", "chipseq", "cuttag_cutrun", "methylseq"]

    counts = inv.groupby("kit", as_index=False)["eval_name"].nunique().rename(columns={"eval_name": "n"})
    plot_data = pd.DataFrame({"kit": kit_order, "label": [kit_label(k) for k in kit_order]})
    plot_data = plot_data.merge(counts, on="kit", how="left").fillna(0)
    plot_data["n"] = plot_data["n"].astype(int)

    colors = [KIT_COLORS.get(k, GRAY) for k in plot_data["kit"]]

    fig, ax = plt.subplots(figsize=(3.0, 2.4))
    y = np.arange(len(plot_data))
    ax.barh(y, plot_data["n"], height=0.56, color=colors, edgecolor="none", alpha=0.92)

    for yi, row in zip(y, plot_data.itertuples(index=False)):
        ax.text(row.n + 0.5, yi, str(int(row.n)), va="center", ha="left",
                fontsize=5.5, fontproperties=MONO, color=MUTED)

    ax.set_yticks(y)
    ax.set_yticklabels(plot_data["label"], fontsize=6.0, fontproperties=SERIF, color=TEXT)
    ax.set_xlim(0, 55)
    ax.set_xticks([0, 20, 40])
    ax.set_xlabel("Eval count", fontproperties=SERIF, labelpad=3, fontsize=6.5)
    ax.tick_params(axis="x", labelsize=5.5)
    ax.yaxis.grid(False)
    clean(ax)
    for lab in ax.get_yticklabels():
        lab.set_fontproperties(SERIF)
        lab.set_color(TEXT)
    fig.tight_layout()
    save_all(fig, "fig5c")


# ═══════════════════════════════════════════════════════════════════════════════
# FIGURE 6: Partial Credit and Failure Diagnostics
# ═══════════════════════════════════════════════════════════════════════════════

def fig6a() -> None:
    """6a: Dumbbell chart — endpoint vs field-level pass rate by assay × task."""
    run = pd.read_csv(DATA / "run_results.csv")
    fields = pd.read_csv(DATA / "field_scores.csv")

    endpoint = (
        run.assign(group=lambda d: d["kit"].map(kit_label) + ": " + d["task_family"].map(task_label))
        .groupby("group", as_index=False)
        .agg(endpoint_pass=("passed", "mean"), n_runs=("passed", "size"), n_evals=("eval_name", "nunique"))
    )
    field = (
        fields.assign(group=lambda d: d["kit"].map(kit_label) + ": " + d["task_family"].map(task_label))
        .groupby("group", as_index=False)
        .agg(field_pass=("field_passed", "mean"), n_field_scores=("field_passed", "size"))
    )
    dumbbell = endpoint.merge(field, on="group", how="inner")
    dumbbell = dumbbell[dumbbell["n_evals"] >= 1].sort_values("endpoint_pass", ascending=True)
    labels = dumbbell["group"].tolist()
    y = np.arange(len(dumbbell))

    fig, ax = plt.subplots(figsize=(7.5, 3.5))
    for yi, row in zip(y, dumbbell.itertuples(index=False)):
        ax.plot([row.endpoint_pass, row.field_pass], [yi, yi], color=LINE, linewidth=1.0, zorder=1)
    ax.scatter(dumbbell["endpoint_pass"], y, s=22, color=ACCENT, edgecolor="none", label="Endpoint", zorder=3)
    ax.scatter(dumbbell["field_pass"], y, s=22, color=TEAL, edgecolor="none", label="Field", zorder=3)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=6.0, fontproperties=SERIF, color=TEXT)
    percent_axis(ax, 0.95, 0.20)
    ax.set_xlabel("Pass rate", fontproperties=SERIF, labelpad=3, fontsize=7)
    ax.yaxis.grid(False)
    clean(ax)
    for lab in ax.get_yticklabels():
        lab.set_fontproperties(SERIF)
        lab.set_color(TEXT)
    ax.legend(frameon=False, loc="lower right", prop=serif_prop(6.5), handletextpad=0.4)
    fig.tight_layout()
    save_all(fig, "fig6a")


def fig6b() -> None:
    """6b: Evaluation difficulty spectrum (dot plot)."""
    eval_diff = pd.read_csv(DATA / "eval_difficulty.csv")
    fields = pd.read_csv(DATA / "field_scores.csv")
    eval_field = fields.groupby("eval_name", as_index=False).agg(field_pass=("field_passed", "mean"))
    diff = eval_diff[["eval_name", "pass_rate", "kit"]].merge(eval_field, on="eval_name", how="left")
    diff = diff.sort_values(["pass_rate", "field_pass"], ascending=[True, True]).reset_index(drop=True)
    x = np.arange(len(diff))
    endpoint_colors = diff["kit"].map(KIT_COLORS).fillna(GRAY)

    fig, ax = plt.subplots(figsize=(4.0, 3.0))
    ax.scatter(x, diff["field_pass"], s=8, color=TEAL, alpha=0.25, edgecolor=TEAL_DARK,
               linewidth=0.15, label="Field pass rate", zorder=2)
    ax.scatter(x, diff["pass_rate"], s=8, color=endpoint_colors, alpha=0.90,
               edgecolor="none", label="Endpoint pass rate", zorder=3)
    ax.axhline(0.5, color=LINE, linewidth=0.7, linestyle="--", zorder=1)
    ax.set_xlim(-2, len(diff) + 2)
    ax.set_ylim(-0.03, 1.03)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, pos: f"{v * 100:.0f}%"))
    ax.set_xticks([])
    ax.set_xlabel("Evaluations (sorted by difficulty)", fontproperties=SERIF, labelpad=3, fontsize=6.5)
    ax.set_ylabel("Pass rate", fontproperties=SERIF, labelpad=3, fontsize=6.5)
    clean(ax, y_grid=True)
    legend_elements = [
        Line2D([0], [0], marker="o", linestyle="none", markerfacecolor=ACCENT,
               markeredgecolor="none", markersize=3.5, label="Endpoint"),
        Line2D([0], [0], marker="o", linestyle="none", markerfacecolor=TEAL,
               markeredgecolor=TEAL_DARK, alpha=0.35, markersize=3.5, label="Field"),
    ]
    ax.legend(handles=legend_elements, frameon=False, loc="upper left",
              prop=serif_prop(6.0), handletextpad=0.35)
    fig.tight_layout()
    save_all(fig, "fig6b")


def fig6c() -> None:
    """6c: Failure mode pass rates."""
    failure = pd.read_csv(DATA / "summary_by_failure_mode.csv")
    fail = failure.sort_values(["n_evals", "pass_rate"], ascending=[False, True]).head(10).copy()
    fail = fail.sort_values("pass_rate", ascending=True)

    def fail_label(mode: str) -> str:
        suffix = str(mode).split(".", 1)[-1]
        labels = {
            "sign_direction_temporal_or_trajectory_orientation_error": "Orientation error",
            "feature_selection_or_panel_scope_mismatch": "Feature scope",
            "feature_namespace_or_identifier_mismatch": "Identifier mismatch",
            "pathway_program_or_score_method_mismatch": "Pathway/score method",
            "threshold_resolution_topk_or_significance_instability": "Top-k threshold",
            "pooled_vs_stratified_analysis_error": "Pooled vs stratified",
            "wrong_metric_summary_rank_or_association": "Wrong metric/rank",
            "prior_driven_or_overclaimed_biological_interpretation": "Prior-driven claim",
            "null_background_or_control_calibration_error": "Null/background",
            "wrong_data_layer_or_preprocessing": "Wrong data layer",
            "wrong_denominator_reference_or_abundance_base": "Wrong denominator",
            "technical_artifact_control_or_detection_bias_as_biology": "Artifact as biology",
        }
        return labels.get(suffix, textwrap.fill(suffix.replace("_", " "), width=22))

    y = np.arange(len(fail))
    colors = [ACCENT if p < 0.20 else TEAL if p > 0.35 else GRAY for p in fail["pass_rate"]]

    fig, ax = plt.subplots(figsize=(4.0, 3.0))
    ax.barh(y, fail["pass_rate"], height=0.52, color=colors, edgecolor="none", alpha=0.96)
    ax.set_yticks(y)
    ax.set_yticklabels([fail_label(m) for m in fail["failure_mode"]], fontsize=6.0, fontproperties=SERIF, color=TEXT)
    percent_axis(ax, 0.55, 0.10)
    ax.set_xlabel("Pass rate", fontproperties=SERIF, labelpad=3, fontsize=6.5)
    ax.tick_params(axis="x", labelsize=5.5)
    ax.yaxis.grid(False)
    clean(ax)
    for lab in ax.get_yticklabels():
        lab.set_fontproperties(SERIF)
        lab.set_color(TEXT)
    for yi, row in zip(y, fail.itertuples(index=False)):
        text = f"n={int(row.n_evals)}"
        ax.text(min(row.pass_rate + 0.015, 0.50), yi, text,
                ha="left", va="center", fontsize=5.0, fontproperties=MONO, color=MUTED)
    fig.tight_layout()
    save_all(fig, "fig6c")


# ═══════════════════════════════════════════════════════════════════════════════
# SUPPLEMENTAL: Cost vs performance
# ═══════════════════════════════════════════════════════════════════════════════

def fig_supp_cost() -> None:
    """Supplemental: Pass rate vs mean cost per run."""
    df = pd.read_csv(DATA / "model_summary_available_runs.csv").copy()
    df = df[df["mean_total_cost"].notna() & (df["mean_total_cost"] > 0)].copy()
    df["label"] = [model_label(m, h, short=True) for m, h in zip(df["model"], df["harness"])]
    df["family"] = df["model"].map(model_family)

    fig, ax = plt.subplots(figsize=(3.75, 3.75))
    for fam, group in df.groupby("family", sort=False):
        ax.scatter(group["mean_total_cost"], group["pass_rate"],
                   s=18, color=FAMILY_COLORS.get(fam, GRAY_DARK),
                   edgecolor="#FFFFFF", linewidth=0.45, alpha=0.90, zorder=3, label=fam)

    ax.set_xlabel("Mean cost per run ($)", fontproperties=SERIF, labelpad=3, fontsize=7)
    ax.set_ylabel("Pass rate", fontproperties=SERIF, labelpad=3, fontsize=7)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, pos: f"{v * 100:.0f}%"))
    ax.legend(frameon=False, loc="lower right", prop=serif_prop(5.5), handletextpad=0.4)
    clean(ax, y_grid=True)
    fig.tight_layout()
    save_all(fig, "fig_supp_cost")


# ═══════════════════════════════════════════════════════════════════════════════
# FIGURE: Failure divergence across models
# ═══════════════════════════════════════════════════════════════════════════════

RUN_RESULTS = DATA / "run_results.csv"

# An eval is "solved" by a model under one of three thresholds:
#   "any"      -> at least 1 of its 3 attempts passed (>=1/3; permissive)
#   "majority" -> a majority (>=2/3) of attempts passed
#   "all"      -> every attempt passed (3/3; conservative)
DIVERGENCE_THRESHOLD = "any"

# Oracle-curve definitions shown together (permissive vs conservative bounds).
ORACLE_CURVES = [
    ("any", "solved if ≥1/3 attempts pass", ACCENT),
    ("all", "solved if 3/3 attempts pass", TEAL_DARK),
]


def _load_runs() -> pd.DataFrame:
    """Load the per-run pass/fail table (one row per model x eval x replicate)."""
    df = pd.read_csv(RUN_RESULTS)
    df["passed"] = df["passed"].astype(str).str.lower().isin(["true", "1", "1.0", "yes", "t"])
    return df


def _solved_matrix(df: pd.DataFrame, threshold: str) -> pd.DataFrame:
    """Boolean eval x model matrix of whether each model solves each eval."""
    g = df.groupby(["model_harness", "eval_name"])["passed"].agg(n_pass="sum", n_att="size").reset_index()
    if threshold == "all":
        g["solved"] = g["n_pass"] >= g["n_att"]
    elif threshold == "majority":
        g["solved"] = g["n_pass"] / g["n_att"] >= 0.5
    else:  # "any"
        g["solved"] = g["n_pass"] >= 1
    return g.pivot(index="eval_name", columns="model_harness", values="solved").fillna(False)


def oracle_curve(df: pd.DataFrame, threshold: str, n_random: int = 400, seed: int = 0):
    """Model-pooling coverage curves.

    Returns (greedy, random_mean, best, union, saturation):
      greedy[k]      -- fraction of evals solved by >=1 of the (k+1) best-first models
      random_mean[k] -- same, averaged over random model orderings
      best           -- single best model's solve fraction (greedy[0])
      union          -- fraction solved by >=1 of all models (greedy[-1])
      saturation     -- smallest pool size that reaches the union
    """
    mat = _solved_matrix(df, threshold)
    n_evals = len(mat)
    models = list(mat.columns)
    solved = {m: set(mat.index[mat[m]]) for m in models}

    remaining, covered, greedy = set(models), set(), []
    while remaining:
        nxt = max(remaining, key=lambda m: len(solved[m] - covered))
        covered |= solved[nxt]
        remaining.discard(nxt)
        greedy.append(len(covered) / n_evals)

    rng = np.random.default_rng(seed)
    order = np.array(models, dtype=object)
    rand = np.zeros((n_random, len(models)))
    for r in range(n_random):
        rng.shuffle(order)
        cov = set()
        for k, m in enumerate(order):
            cov |= solved[m]
            rand[r, k] = len(cov) / n_evals
    random_mean = rand.mean(axis=0)

    union = greedy[-1]
    saturation = next(k + 1 for k, v in enumerate(greedy) if abs(v - union) < 1e-9)
    return np.array(greedy), random_mean, float(greedy[0]), float(union), saturation


def divergence_tables(df: pd.DataFrame, threshold: str = DIVERGENCE_THRESHOLD):
    """Per-eval model-coverage and divergence metrics.

    Returns (coverage, per_model_solved, metrics) where coverage is a Series
    indexed by eval_name giving how many models solve it, per_model_solved maps
    model_harness -> set(evals solved), and metrics is a summary dict.
    """
    import itertools

    mat = _solved_matrix(df, threshold)
    models = list(mat.columns)
    evals = list(mat.index)
    n_models, n_evals = len(models), len(evals)

    coverage = mat.sum(axis=1).astype(int)
    per_model = {m: set(mat.index[mat[m]]) for m in models}
    fail_sets = {m: set(evals) - per_model[m] for m in models}

    def mean_jaccard(sets: dict) -> float:
        vals = []
        for a, b in itertools.combinations(models, 2):
            union = sets[a] | sets[b]
            vals.append(len(sets[a] & sets[b]) / len(union) if union else 1.0)
        return float(np.mean(vals)) if vals else float("nan")

    ranked = sorted(((len(s), m) for m, s in per_model.items()), reverse=True)
    metrics = {
        "threshold": threshold,
        "n_evals": n_evals,
        "n_models": n_models,
        "union": int((coverage >= 1).sum()),
        "universal_fail": int((coverage == 0).sum()),
        "solved_by_all": int((coverage == n_models).sum()),
        "best_model": ranked[0][1],
        "best_solved": ranked[0][0],
        "mean_jaccard_solved": mean_jaccard(per_model),
        "mean_jaccard_failed": mean_jaccard(fail_sets),
        "coverage_hist": {int(k): int(v) for k, v in coverage.value_counts().sort_index().items()},
    }
    return coverage, per_model, metrics


def fig_divergence_a() -> None:
    """Divergence: oracle model-pooling curve (permissive >=1/3 vs conservative 3/3).

    Greedy best-first curve (solid) and random-order mean (dashed) for each
    threshold; the dotted line marks each threshold's best single model.
    """
    df = _load_runs()
    n_models = df["model_harness"].nunique()

    fig, ax = plt.subplots(figsize=(4.8, 3.0))
    for thr, label, color in ORACLE_CURVES:
        greedy, rmean, best, union, sat = oracle_curve(df, thr)
        x = np.arange(1, len(greedy) + 1)
        ax.plot(x, rmean, ls=(0, (4, 2)), lw=1.0, color=color, alpha=0.85, zorder=3)
        ax.plot(x, greedy, "-o", lw=1.6, ms=2.8, color=color, zorder=4, label=label)
        ax.scatter([1, len(greedy)], [best, union], s=15, color=color, zorder=5)
        # best single (curve start) and union (curve end) labelled directly off their markers
        best_y = best + 0.028 if thr == "any" else best - 0.052
        ax.annotate(f"{best * 100:.0f}%", (1, best), (0.32, best_y), ha="left",
                    fontproperties=MONO, fontsize=5.8, color=color)
        ax.annotate(f"union {union * 100:.0f}%", (len(greedy), union), (len(greedy) - 4.7, union + 0.028),
                    fontproperties=MONO, fontsize=5.8, color=color)

    clean(ax, y_grid=True)
    ax.xaxis.grid(False)
    ax.set_xlim(0.0, n_models + 0.4)
    ax.set_ylim(0.15, 0.85)
    ax.set_yticks(np.arange(0.20, 0.801, 0.10))
    ax.set_xticks(range(0, n_models + 1, 2))
    for lab in ax.get_xticklabels():
        lab.set_fontproperties(SERIF)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, pos: f"{v * 100:.0f}%"))
    ax.set_xlabel("Models pooled", fontproperties=SERIF, fontsize=7.5)
    ax.set_ylabel("Evaluations solved", fontproperties=SERIF, fontsize=7.5)
    # Left-aligned text legend: color encodes the threshold; note below explains line style.
    legend_left, legend_top, line_h = 0.55, 0.42, 0.052
    for i, (thr, label, color) in enumerate(ORACLE_CURVES):
        ax.text(legend_left, legend_top - i * line_h, label, transform=ax.transAxes,
                ha="left", va="top", fontproperties=serif_prop(6.2, bold=True), color=color)
    ax.text(legend_left, legend_top - len(ORACLE_CURVES) * line_h - 0.012,
            "solid: best-first pooling\ndashed: random-order mean", transform=ax.transAxes,
            ha="left", va="top", fontproperties=serif_prop(6.2), color=TEXT, linespacing=1.5)
    fig.tight_layout()
    save_all(fig, "fig_divergence_a")


# ═══════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    print(f"Generating figures in: {FIGURES}")

    # Figure 1: Topline
    fig1a()
    fig1b()
    fig1c()

    # Figure 4: Main results
    fig4a()
    fig4c()

    # Figure 5: Source / Assay / Horizon
    fig5a()
    fig5b()
    fig5c()

    # Figure 6: Partial credit / Failure
    fig6a()
    fig6b()
    fig6c()

    # Supplemental
    fig_supp_cost()

    # Failure divergence across models (requires run_results.csv)
    if RUN_RESULTS.exists():
        fig_divergence_a()
    else:
        print(f"  Skipped divergence figure: {RUN_RESULTS} not found")

    print(f"\nAll figures saved to: {FIGURES}")


if __name__ == "__main__":
    main()
