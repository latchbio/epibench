#!/usr/bin/env python3
from __future__ import annotations

import os
import textwrap
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/matplotlib-cache")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.font_manager import FontProperties
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.ticker import FuncFormatter


ROOT = Path(__file__).resolve().parents[2]
PAPER = ROOT / "paper"
DATA = ROOT / "analysis_outputs" / "epi_manifest_updated_summary"
TOPLINE = PAPER / "figures" / "topline"
RESULTS = PAPER / "figures" / "results"

TEXT = "#15191F"
MUTED = "#5F6872"
GRID = "#D9DEE5"
AXIS = "#AFA89B"
CREAM = "#FBFAF6"
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

FAMILY = {
    "OpenAI": "#171511",
    "Anthropic": ACCENT_LIGHT,
    "Gemini": TEAL,
    "xAI": VIOLET,
    "Kimi": "#B89142",
}


def register_fonts() -> None:
    for font_file in [
        Path("/Users/kenny/Library/Fonts/bitstream-iowan-old-style-bt-586c36a8d7712.ttf"),
        Path("/Users/kenny/Library/Fonts/bitstream-iowan-old-style-bold-bt-586c371d8d669.ttf"),
        Path("/Users/kenny/Library/Fonts/bitstream-iowan-old-style-italic-bt-586c3740dc396.ttf"),
        Path("/Users/kenny/Library/Fonts/bitstream-iowan-old-style-bold-italic-bt-586c37701cb62.ttf"),
        Path("/Applications/Cursor.app/Contents/Resources/app/out/media/jetbrains-mono-regular.ttf"),
    ]:
        if font_file.exists():
            font_manager.fontManager.addfont(str(font_file))


register_fonts()
SERIF_STACK = ["Iowan Old Style", "DejaVu Serif", "serif"]
MONO_STACK = ["JetBrains Mono", "DejaVu Sans Mono", "monospace"]
SERIF = FontProperties(family=SERIF_STACK)
SERIF_BOLD = FontProperties(family=SERIF_STACK, weight="bold")
MONO = FontProperties(family=MONO_STACK)


def serif_prop(size: float, *, bold: bool = False) -> FontProperties:
    return FontProperties(family=SERIF_STACK, weight="bold" if bold else "normal", size=size)

plt.rcParams.update(
    {
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
    }
)

CALLOUT = {
    "boxstyle": "round,pad=0.18,rounding_size=0.05",
    "facecolor": "#FFFFFF",
    "edgecolor": "#D3CCBE",
    "linewidth": 0.42,
    "alpha": 0.98,
}


def save_all(fig: plt.Figure, out_dir: Path, stem: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for ext in ("pdf", "svg", "png"):
        fig.savefig(out_dir / f"{stem}.{ext}", bbox_inches="tight", dpi=520)
    plt.close(fig)


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
    ax.text(
        x,
        y,
        letter,
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=10.8,
        fontproperties=SERIF_BOLD,
        color=TEXT,
    )


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


def source_label(source: str) -> str:
    return {
        "atac": "B-ALL ATAC",
        "cold": "Cold ATAC",
        "chipseq": "ChIP-seq",
        "gse149608": "GSE149608",
        "gse149609": "GSE149609",
        "zebrafish": "Zebrafish CUT&RUN",
    }.get(source, source)


def kit_label(kit: str) -> str:
    return {
        "atacseq": "ATAC-seq",
        "chipseq": "ChIP-seq",
        "cuttag_cutrun": "CUT&Tag/CUT&RUN",
        "methylseq": "methylation",
    }.get(kit, kit)


def task_label(task: str, *, short: bool = False) -> str:
    if short:
        return {
            "differential_expression": "Diff.\nanalysis",
            "dimensionality_reduction": "Dim.\nreduction",
            "spatial_analysis": "Spatial\nanalysis",
            "normalization": "Normalization",
            "clustering": "Clustering",
            "qc": "QC",
        }.get(task, task)
    return {
        "differential_expression": "differential analysis",
        "dimensionality_reduction": "dimensionality reduction",
        "spatial_analysis": "spatial analysis",
        "normalization": "normalization",
        "clustering": "clustering",
        "qc": "qc",
    }.get(task, task)


def add_bar_cis(ax: plt.Axes, df: pd.DataFrame, y: np.ndarray) -> None:
    x = df["pass_rate"].to_numpy()
    low = df["pass_rate_wilson_low"].to_numpy()
    high = df["pass_rate_wilson_high"].to_numpy()
    ax.errorbar(
        x,
        y,
        xerr=[x - low, high - x],
        fmt="none",
        ecolor=TEXT,
        elinewidth=0.58,
        capsize=1.55,
        capthick=0.58,
        zorder=4,
    )


def draw_rate_bars(
    ax: plt.Axes,
    df: pd.DataFrame,
    *,
    labels: list[str],
    xmax: float,
    label_mode: str = "count",
    highlight_n: int = 0,
    color_by: str | None = None,
) -> None:
    plot = df.sort_values("pass_rate", ascending=True).reset_index(drop=True)
    y = np.arange(len(plot))
    if color_by:
        colors = [color_by for _ in range(len(plot))]
    else:
        colors = [ACCENT if r <= highlight_n and highlight_n else GRAY for r in plot.index[::-1]]
    ax.barh(y, plot["pass_rate"], height=0.56, color=colors, edgecolor="none", alpha=0.96)
    add_bar_cis(ax, plot, y)
    ax.set_yticks(y)
    ax.set_yticklabels(labels[::-1], fontsize=7.4, fontproperties=SERIF, color=TEXT)
    percent_axis(ax, xmax)
    clean(ax)
    ax.yaxis.grid(False)
    for lab in ax.get_yticklabels():
        lab.set_fontproperties(SERIF)
        lab.set_color(TEXT)
    for yi, row in zip(y, plot.itertuples(index=False)):
        if label_mode == "percent_count":
            text = f"{row.pass_rate * 100:.1f}%   {int(row.pass_n)}/{int(row.n_runs)}"
            label_x = min(max(row.pass_rate_wilson_high + 0.018, row.pass_rate + 0.035), xmax - 0.11)
            ax.text(
                label_x,
                yi,
                text,
                ha="left",
                va="center",
                fontsize=6.55,
                fontproperties=MONO,
                color=TEXT,
                bbox=CALLOUT,
                zorder=5,
            )
        elif label_mode == "evals":
            text = "1 eval" if int(row.n_evals) == 1 else f"{int(row.n_evals)} evals"
            label_x = min(row.pass_rate_wilson_high + 0.012, xmax - 0.075)
            ax.text(
                label_x,
                yi,
                text,
                ha="left",
                va="center",
                fontsize=6.3,
                fontproperties=MONO,
                color=MUTED,
            )
        else:
            label_x = min(row.pass_rate_wilson_high + 0.012, xmax - 0.07)
            ax.text(
                label_x,
                yi,
                f"{int(row.pass_n)}/{int(row.n_runs)}",
                ha="left",
                va="center",
                fontsize=6.2,
                fontproperties=MONO,
                color=MUTED,
            )


def make_topline_a() -> None:
    df = pd.read_csv(DATA / "model_summary_available_runs.csv").sort_values("pass_rate", ascending=False)
    df["label"] = [model_label(m, h) for m, h in zip(df["model"], df["harness"])]
    df["rank"] = np.arange(1, len(df) + 1)
    plot = df.sort_values("pass_rate", ascending=True).reset_index(drop=True)
    y = np.arange(len(plot))
    colors = [ACCENT if rank <= 3 else GRAY for rank in plot["rank"]]

    fig, ax = plt.subplots(figsize=(7.7, 4.95))
    ax.barh(y, plot["pass_rate"], height=0.55, color=colors, edgecolor="none", alpha=0.96)
    add_bar_cis(ax, plot, y)
    ax.set_yticks(y)
    ax.set_yticklabels(plot["label"], fontsize=7.7, fontproperties=SERIF, color=TEXT)
    percent_axis(ax, 0.70)
    ax.set_xlabel("Pass rate", fontproperties=SERIF, labelpad=4)
    ax.yaxis.grid(False)
    clean(ax)
    for lab in ax.get_yticklabels():
        lab.set_fontproperties(SERIF)
        lab.set_color(TEXT)
    for yi, row in zip(y, plot.itertuples(index=False)):
        label_x = min(max(row.pass_rate_wilson_high + 0.018, row.pass_rate + 0.045), 0.615)
        ax.text(
            label_x,
            yi,
            f"{row.pass_rate * 100:.1f}%   {int(row.pass_n)}/{int(row.n_runs)}",
            va="center",
            ha="left",
            fontsize=6.8,
            fontproperties=MONO,
            bbox=CALLOUT,
        )
    fig.subplots_adjust(left=0.22, right=0.985, bottom=0.13, top=0.985)
    save_all(fig, TOPLINE, "figA_pass_rate_by_model")


def make_topline_b() -> None:
    df = pd.read_csv(DATA / "summary_by_kit_task.csv").sort_values("pass_rate", ascending=False)
    df["label"] = [f"{kit_label(k)}: {task_label(t)}" for k, t in zip(df["kit"], df["task_family"])]
    kit_colors = {"atacseq": ACCENT, "chipseq": GRAY_DARK, "cuttag_cutrun": VIOLET, "methylseq": TEAL}
    plot = df.sort_values("pass_rate", ascending=True).reset_index(drop=True)
    y = np.arange(len(plot))
    colors = [kit_colors[k] for k in plot["kit"]]
    alpha = [0.45 if n <= 1 else 0.96 for n in plot["n_evals"]]

    fig, ax = plt.subplots(figsize=(3.95, 3.05))
    for yi, row, color, a in zip(y, plot.itertuples(index=False), colors, alpha):
        ax.barh(yi, row.pass_rate, height=0.54, color=color, alpha=a, edgecolor="none")
    ax.set_yticks(y)
    ax.set_yticklabels(plot["label"], fontsize=6.6, fontproperties=SERIF, color=TEXT)
    percent_axis(ax, 0.72, 0.1)
    ax.set_xlabel("Pass rate", fontproperties=SERIF, labelpad=3)
    ax.yaxis.grid(False)
    clean(ax)
    for lab in ax.get_yticklabels():
        lab.set_fontproperties(SERIF)
        lab.set_color(TEXT)
    for yi, row in zip(y, plot.itertuples(index=False)):
        text = "1 eval" if int(row.n_evals) == 1 else f"{int(row.n_evals)} evals"
        ax.text(
            min(row.pass_rate + 0.025, 0.67),
            yi,
            text,
            va="center",
            ha="left",
            fontsize=5.9,
            fontproperties=MONO,
            color=MUTED,
        )
    fig.subplots_adjust(left=0.34, right=0.99, bottom=0.18, top=0.98)
    save_all(fig, TOPLINE, "figB_pass_rate_by_kit_task")


def make_topline_c() -> None:
    df = pd.read_csv(DATA / "model_summary_available_runs.csv").copy()
    df["label"] = [model_label(m, h, short=True) for m, h in zip(df["model"], df["harness"])]
    df["family"] = df["model"].map(model_family)
    df["runtime_min"] = df["median_duration_s"] / 60.0

    fig, ax = plt.subplots(figsize=(3.95, 3.05))
    for fam, group in df.groupby("family", sort=False):
        ax.scatter(
            group["runtime_min"],
            group["pass_rate"],
            s=17,
            color=FAMILY.get(fam, GRAY_DARK),
            edgecolor="#FFFFFF",
            linewidth=0.45,
            alpha=0.90,
            zorder=3,
        )
    labels = {
        "GPT-5.5 / Pi": (4, 8, "left"),
        "GPT-5.5 / Codex": (4, 15, "left"),
        "GPT-5.4 / Pi": (4, -11, "left"),
        "Opus 4.8 Max / Pi": (-30, -24, "right"),
        "Grok 4.3 / Pi": (4, 4, "left"),
        "Gemini 3.5 / Pi": (-30, 8, "right"),
    }
    for row in df.itertuples(index=False):
        if row.label not in labels:
            continue
        dx, dy, ha = labels[row.label]
        ax.annotate(
            row.label.replace(" / Pi", "").replace(" / Codex", " Codex"),
            (row.runtime_min, row.pass_rate),
            xytext=(dx, dy),
            textcoords="offset points",
            ha=ha,
            va="center",
            fontsize=5.9,
            fontproperties=SERIF,
            color=MUTED,
            arrowprops={"arrowstyle": "-", "linewidth": 0.35, "color": LINE, "shrinkA": 2, "shrinkB": 2},
        )
    ax.set_xlim(0, 15.0)
    ax.set_xticks(np.arange(0, 15.1, 3))
    ax.set_ylim(0.16, 0.55)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: f"{x * 100:.0f}%"))
    ax.set_xlabel("Median runtime (min)", fontproperties=SERIF, labelpad=3)
    ax.set_ylabel("Pass rate", fontproperties=SERIF, labelpad=3)
    clean(ax, y_grid=True)
    fig.subplots_adjust(left=0.16, right=0.98, bottom=0.18, top=0.98)
    save_all(fig, TOPLINE, "figC_pass_rate_vs_runtime")


def make_main_results() -> None:
    available = pd.read_csv(DATA / "model_summary_available_runs.csv").sort_values("pass_rate", ascending=False)
    common = pd.read_csv(DATA / "model_summary_common_instances.csv").sort_values("pass_rate", ascending=False)
    repl = pd.read_csv(DATA / "replicate_robustness_by_model.csv")
    available["label"] = [model_label(m, h, short=True) for m, h in zip(available["model"], available["harness"])]
    common["label"] = [model_label(m, h, short=True) for m, h in zip(common["model"], common["harness"])]
    repl["label"] = [model_label(m, h, short=True) for m, h in zip(repl["model"], repl["harness"])]
    available["rank"] = np.arange(1, len(available) + 1)
    common["rank"] = np.arange(1, len(common) + 1)

    fig = plt.figure(figsize=(8.45, 4.65))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.32, 1.08, 0.98], wspace=0.37)

    ax = fig.add_subplot(gs[0, 0])
    plot = available.sort_values("pass_rate", ascending=True).reset_index(drop=True)
    y = np.arange(len(plot))
    colors = [ACCENT if rank <= 3 else GRAY for rank in plot["rank"]]
    ax.barh(y, plot["pass_rate"], height=0.52, color=colors, edgecolor="none", alpha=0.96)
    add_bar_cis(ax, plot, y)
    ax.set_yticks(y)
    ax.set_yticklabels(plot["label"], fontsize=6.75, fontproperties=SERIF, color=TEXT)
    percent_axis(ax, 0.70, 0.10)
    ax.set_xlabel("Run-level pass rate", fontproperties=SERIF, labelpad=4)
    clean(ax)
    ax.yaxis.grid(False)
    for lab in ax.get_yticklabels():
        lab.set_fontproperties(SERIF)
        lab.set_color(TEXT)
    for yi, row in zip(y, plot.itertuples(index=False)):
        ax.text(
            min(row.pass_rate_wilson_high + 0.022, 0.640),
            yi,
            f"{int(row.pass_n)}/{int(row.n_runs)}",
            ha="left",
            va="center",
            fontsize=5.9,
            fontproperties=MONO,
            color=MUTED,
        )
    panel_label(ax, "A", -0.09, 1.025)

    ax2 = fig.add_subplot(gs[0, 1])
    plot = common.sort_values("pass_rate", ascending=True).reset_index(drop=True)
    y = np.arange(len(plot))
    colors = [ACCENT if rank <= 3 else GRAY for rank in plot["rank"]]
    ax2.barh(y, plot["pass_rate"], height=0.52, color=colors, edgecolor="none", alpha=0.96)
    add_bar_cis(ax2, plot, y)
    ax2.set_yticks([])
    percent_axis(ax2, 0.70, 0.10)
    ax2.set_xlabel("Balanced-design pass rate", fontproperties=SERIF, labelpad=4)
    clean(ax2)
    ax2.yaxis.grid(False)
    for yi, row in zip(y, plot.itertuples(index=False)):
        ax2.text(
            min(row.pass_rate_wilson_high + 0.022, 0.640),
            yi,
            f"{int(row.pass_n)}/{int(row.n_runs)}",
            ha="left",
            va="center",
            fontsize=5.9,
            fontproperties=MONO,
            color=MUTED,
        )
    panel_label(ax2, "B", -0.07, 1.025)

    ax3 = fig.add_subplot(gs[0, 2])
    heat = available[["model_harness", "label"]].merge(
        repl[["model_harness", "any_pass_rate", "majority_pass_rate", "all_pass_rate"]],
        on="model_harness",
        how="left",
    )
    cols = ["any_pass_rate", "majority_pass_rate", "all_pass_rate"]
    matrix = heat[cols].to_numpy()
    cmap = LinearSegmentedColormap.from_list("replicate", [WARM, "#D7AE96", ACCENT])
    ax3.imshow(matrix, aspect="auto", cmap=cmap, vmin=0.12, vmax=0.66)
    ax3.set_xticks(range(3))
    ax3.set_xticklabels(["Any", "Majority", "All"], fontsize=6.8, fontproperties=SERIF)
    ax3.set_yticks([])
    ax3.tick_params(axis="x", length=0)
    for i in range(matrix.shape[0]):
        n = int(repl.loc[repl["model_harness"].eq(heat.loc[i, "model_harness"]), "n_eval_model_pairs"].iloc[0])
        for j in range(3):
            value = matrix[i, j]
            color = "#FFFFFF" if value > 0.48 else TEXT
            ax3.text(j, i, f"{round(value * n):.0f}/{n}", ha="center", va="center", fontsize=5.45, fontproperties=MONO, color=color)
    for spine in ax3.spines.values():
        spine.set_visible(False)
    ax3.set_xlabel("Evaluation-level replicate rate", fontproperties=SERIF, labelpad=6)
    ax3.grid(False)
    panel_label(ax3, "C", -0.12, 1.025)
    fig.subplots_adjust(left=0.085, right=0.99, bottom=0.13, top=0.95)
    save_all(fig, RESULTS, "main_results_summary")


def make_source_horizon() -> None:
    source = pd.read_csv(DATA / "summary_by_source_prefix.csv").sort_values("pass_rate", ascending=False)
    source["label"] = source["source_prefix"].map(source_label)
    source["rank"] = np.arange(1, len(source) + 1)
    kit_task = pd.read_csv(DATA / "summary_by_kit_task.csv")
    inv = pd.read_csv(DATA / "eval_inventory.csv")

    fig = plt.figure(figsize=(8.75, 4.25))
    gs = fig.add_gridspec(1, 3, width_ratios=[0.98, 1.52, 1.02], wspace=0.54)

    ax = fig.add_subplot(gs[0, 0])
    plot = source.sort_values("pass_rate", ascending=True).reset_index(drop=True)
    y = np.arange(len(plot))
    colors = [ACCENT if rank >= 5 else GRAY for rank in plot["rank"]]
    ax.barh(y, plot["pass_rate"], height=0.56, color=colors, edgecolor="none", alpha=0.96)
    add_bar_cis(ax, plot, y)
    ax.set_yticks(y)
    ax.set_yticklabels(plot["label"], fontsize=7.0, fontproperties=SERIF, color=TEXT)
    percent_axis(ax, 0.66, 0.20)
    ax.set_xlabel("Pass rate", fontproperties=SERIF, labelpad=4)
    clean(ax)
    ax.yaxis.grid(False)
    for lab in ax.get_yticklabels():
        lab.set_fontproperties(SERIF)
        lab.set_color(TEXT)
    for yi, row in zip(y, plot.itertuples(index=False)):
        label = "1 eval" if int(row.n_evals) == 1 else f"{int(row.n_evals)} evals"
        ax.text(0.635, yi, label, ha="right", va="center", fontsize=5.7, fontproperties=MONO, color=MUTED)
    panel_label(ax, "A", -0.09, 1.035)

    ax2 = fig.add_subplot(gs[0, 1])
    row_order = ["atac", "cold", "zebrafish", "gse149608", "chipseq", "gse149609"]
    col_order = ["qc", "differential_expression", "normalization", "dimensionality_reduction", "clustering", "spatial_analysis"]
    cross = (
        inv.groupby(["source_prefix", "task_family"], as_index=False)
        .agg(n_evals=("eval_name", "nunique"))
        .merge(
            pd.read_csv(DATA / "summary_by_source_prefix.csv")[["source_prefix"]],
            on="source_prefix",
            how="right",
        )
    )
    rates = pd.read_csv(DATA / "run_results.csv").groupby(["source_prefix", "task_family"], as_index=False).agg(
        pass_rate=("passed", "mean"),
        pass_n=("passed", "sum"),
        n_runs=("passed", "size"),
    )
    table = rates.merge(cross.drop_duplicates(["source_prefix", "task_family"]), on=["source_prefix", "task_family"], how="left")
    mat = np.full((len(row_order), len(col_order)), np.nan)
    counts = np.zeros_like(mat)
    eval_counts = np.zeros_like(mat)
    for i, src in enumerate(row_order):
        for j, task in enumerate(col_order):
            sub = table[(table["source_prefix"].eq(src)) & (table["task_family"].eq(task))]
            if not sub.empty:
                mat[i, j] = sub["pass_rate"].iloc[0]
                counts[i, j] = sub["n_runs"].iloc[0]
                eval_counts[i, j] = sub["n_evals"].iloc[0] if pd.notna(sub["n_evals"].iloc[0]) else 0
    cmap = LinearSegmentedColormap.from_list("source_task", [WARM, "#D8B09D", ACCENT])
    ax2.imshow(np.ma.masked_invalid(mat), aspect="auto", cmap=cmap, vmin=0, vmax=0.65)
    ax2.set_xticks(range(len(col_order)))
    short_task_labels = ["QC", "Diff.", "Norm.", "Dim.", "Clust.", "Spatial"]
    ax2.set_xticklabels(short_task_labels, fontsize=4.8, fontproperties=SERIF)
    ax2.set_yticks(range(len(row_order)))
    ax2.set_yticklabels([source_label(r) for r in row_order], fontsize=6.9, fontproperties=SERIF)
    ax2.tick_params(length=0)
    for i in range(len(row_order)):
        for j in range(len(col_order)):
            if np.isnan(mat[i, j]):
                ax2.text(j, i, "--", ha="center", va="center", fontsize=6.1, fontproperties=MONO, color="#A9A39C")
            else:
                color = "#FFFFFF" if mat[i, j] > 0.46 else TEXT
                eval_label = "1 eval" if int(eval_counts[i, j]) == 1 else f"{int(eval_counts[i, j])} evals"
                ax2.text(j, i - 0.04, f"{mat[i, j] * 100:.0f}%", ha="center", va="center", fontsize=5.7, fontproperties=MONO, color=color)
                ax2.text(j, i + 0.23, eval_label, ha="center", va="center", fontsize=4.9, fontproperties=MONO, color=color)
    ax2.set_xlabel("Task family", fontproperties=SERIF, labelpad=5)
    for spine in ax2.spines.values():
        spine.set_visible(False)
    ax2.set_xticks(np.arange(-0.5, len(col_order), 1), minor=True)
    ax2.set_yticks(np.arange(-0.5, len(row_order), 1), minor=True)
    ax2.grid(which="minor", color="#FFFFFF", linewidth=0.9)
    ax2.grid(False)
    panel_label(ax2, "B", -0.08, 1.035)

    ax3 = fig.add_subplot(gs[0, 2])
    counts_df = (
        inv.groupby(["source_prefix", "time_horizon"], as_index=False)["eval_name"]
        .nunique()
        .rename(columns={"eval_name": "n"})
    )
    count_plot = pd.DataFrame({"source_prefix": row_order, "label": [source_label(x) for x in row_order]})
    count_plot["small"] = [
        int(counts_df[(counts_df["source_prefix"].eq(src)) & (counts_df["time_horizon"].eq("small"))]["n"].sum()) for src in row_order
    ]
    count_plot["long"] = [
        int(counts_df[(counts_df["source_prefix"].eq(src)) & (counts_df["time_horizon"].eq("long"))]["n"].sum()) for src in row_order
    ]
    y = np.arange(len(count_plot))
    ax3.barh(y, count_plot["small"], height=0.56, color=VIOLET, edgecolor="none", alpha=0.94, label="Small")
    ax3.barh(y, count_plot["long"], left=count_plot["small"], height=0.56, color=TEAL, edgecolor="none", alpha=0.96, label="Long")
    for yi, row in zip(y, count_plot.itertuples(index=False)):
        total = int(row.small + row.long)
        ax3.text(total + 1.1, yi, str(total), va="center", ha="left", fontsize=5.9, fontproperties=MONO, color=MUTED)
        if row.small >= 4:
            ax3.text(row.small / 2, yi, str(int(row.small)), va="center", ha="center", fontsize=5.8, fontproperties=MONO, color="#FFFFFF")
        elif row.small > 0:
            ax3.text(row.small + 0.65, yi - 0.18, str(int(row.small)), va="center", ha="left", fontsize=5.5, fontproperties=MONO, color=VIOLET)
        if row.long >= 4:
            ax3.text(row.small + row.long / 2, yi, str(int(row.long)), va="center", ha="center", fontsize=5.8, fontproperties=MONO, color="#FFFFFF")
        elif row.long > 0:
            ax3.text(row.small + row.long + 0.65, yi + 0.18, str(int(row.long)), va="center", ha="left", fontsize=5.5, fontproperties=MONO, color=TEAL_DARK)
    ax3.set_yticks(y)
    ax3.set_yticklabels(count_plot["label"], fontsize=7.0, fontproperties=SERIF, color=TEXT)
    ax3.set_xlim(0, 58)
    ax3.set_xticks([0, 20, 40])
    ax3.set_xlabel("Evaluation count", fontproperties=SERIF, labelpad=4)
    clean(ax3)
    ax3.yaxis.grid(False)
    for lab in ax3.get_yticklabels():
        lab.set_fontproperties(SERIF)
        lab.set_color(TEXT)
    ax3.legend(frameon=False, loc="lower right", prop=serif_prop(6.0), handlelength=1.2)
    panel_label(ax3, "C", -0.08, 1.035)
    fig.subplots_adjust(left=0.075, right=0.99, bottom=0.17, top=0.92)
    save_all(fig, RESULTS, "source_and_horizon_summary")


def make_partial_credit() -> None:
    run = pd.read_csv(DATA / "run_results.csv")
    fields = pd.read_csv(DATA / "field_scores.csv")
    failure = pd.read_csv(DATA / "summary_by_failure_mode.csv")
    eval_diff = pd.read_csv(DATA / "eval_difficulty.csv")

    fig = plt.figure(figsize=(8.8, 4.7))
    gs = fig.add_gridspec(2, 2, width_ratios=[1.18, 1.22], height_ratios=[1.0, 1.0], wspace=0.50, hspace=0.52)

    ax = fig.add_subplot(gs[:, 0])
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
    labels = [textwrap.fill(g.replace(": differential analysis", ":\ndifferential analysis"), width=24) for g in dumbbell["group"]]
    y = np.arange(len(dumbbell))
    for yi, row in zip(y, dumbbell.itertuples(index=False)):
        ax.plot([row.endpoint_pass, row.field_pass], [yi, yi], color=LINE, linewidth=1.15, zorder=1)
    ax.scatter(dumbbell["endpoint_pass"], y, s=24, color=ACCENT, edgecolor="none", label="Endpoint pass", zorder=3)
    ax.scatter(dumbbell["field_pass"], y, s=24, color=TEAL, edgecolor="none", label="Field pass", zorder=3)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=6.4, fontproperties=SERIF, color=TEXT)
    percent_axis(ax, 0.90, 0.20)
    ax.set_xlabel("Pass rate", fontproperties=SERIF, labelpad=4)
    clean(ax)
    ax.yaxis.grid(False)
    for lab in ax.get_yticklabels():
        lab.set_fontproperties(SERIF)
        lab.set_color(TEXT)
    ax.legend(frameon=False, loc="lower right", prop=serif_prop(6.0), handletextpad=0.4)
    panel_label(ax, "A", -0.10, 1.02)

    ax2 = fig.add_subplot(gs[0, 1])
    eval_field = fields.groupby("eval_name", as_index=False).agg(field_pass=("field_passed", "mean"))
    diff = eval_diff[["eval_name", "pass_rate", "kit"]].merge(eval_field, on="eval_name", how="left")
    diff = diff.sort_values(["pass_rate", "field_pass"], ascending=[True, True]).reset_index(drop=True)
    x = np.arange(len(diff))
    endpoint_colors = diff["kit"].map({"atacseq": ACCENT, "chipseq": GRAY_DARK, "cuttag_cutrun": VIOLET, "methylseq": TEAL}).fillna(GRAY)
    ax2.scatter(x, diff["field_pass"], s=6.5, color=TEAL, alpha=0.22, edgecolor=TEAL_DARK, linewidth=0.15, label="Field", zorder=2)
    ax2.scatter(x, diff["pass_rate"], s=6.0, color=endpoint_colors, alpha=0.95, edgecolor="none", label="Endpoint", zorder=3)
    ax2.set_xlim(-2, len(diff) + 1)
    ax2.set_ylim(-0.03, 1.03)
    ax2.yaxis.set_major_formatter(FuncFormatter(lambda v, pos: f"{v * 100:.0f}%"))
    ax2.set_xticks([])
    ax2.set_xlabel("Evaluations sorted by endpoint difficulty", fontproperties=SERIF, labelpad=4)
    ax2.set_ylabel("Pass rate", fontproperties=SERIF, labelpad=4)
    clean(ax2, y_grid=True)
    ax2.legend(
        handles=[
            Line2D([0], [0], marker="o", linestyle="none", markerfacecolor=ACCENT, markeredgecolor="none", markersize=3.2, label="Endpoint"),
            Line2D([0], [0], marker="o", linestyle="none", markerfacecolor=TEAL, markeredgecolor=TEAL_DARK, alpha=0.35, markersize=3.2, label="Field"),
        ],
        frameon=False,
        loc="lower right",
        prop=serif_prop(5.9),
        handletextpad=0.35,
    )
    panel_label(ax2, "B", -0.06, 1.04)

    ax3 = fig.add_subplot(gs[1, 1])
    fail = failure.sort_values(["n_evals", "pass_rate"], ascending=[False, True]).head(9).copy()
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
    colors = [ACCENT if p < 0.15 else TEAL if p > 0.30 else GRAY for p in fail["pass_rate"]]
    ax3.barh(y, fail["pass_rate"], height=0.52, color=colors, edgecolor="none", alpha=0.96)
    ax3.set_yticks(y)
    ax3.set_yticklabels([fail_label(m) for m in fail["failure_mode"]], fontsize=5.6, fontproperties=SERIF, color=TEXT)
    percent_axis(ax3, 0.48, 0.10)
    ax3.set_xlabel("Pass rate on annotated evals", fontproperties=SERIF, labelpad=4)
    clean(ax3)
    ax3.yaxis.grid(False)
    for lab in ax3.get_yticklabels():
        lab.set_fontproperties(SERIF)
        lab.set_color(TEXT)
    for yi, row in zip(y, fail.itertuples(index=False)):
        text = "1 eval" if int(row.n_evals) == 1 else f"{int(row.n_evals)} evals"
        ax3.text(min(row.pass_rate + 0.018, 0.425), yi, text, ha="left", va="center", fontsize=5.25, fontproperties=MONO, color=MUTED)
    panel_label(ax3, "C", -0.06, 1.04)
    fig.subplots_adjust(left=0.11, right=0.99, bottom=0.12, top=0.94)
    save_all(fig, RESULTS, "partial_credit_failure_diagnostics")


def main() -> None:
    make_topline_a()
    make_topline_b()
    make_topline_c()
    make_main_results()
    make_source_horizon()
    make_partial_credit()


if __name__ == "__main__":
    main()
