#!/usr/bin/env python3
"""Generate manuscript figures from simulations + historical preference data.

Outputs PNGs to `figures/` and provides helpers to embed them into
`static/manuscript.html` as base64 data URIs.

Figures currently supported:
- Simulation delta (average error) vs beans/students under both `beans` and
  `linear` penalty modes (Figures 1 and 4 in the manuscript).
- Historical preference distributions: beans by option, split by cohort year
  (Figure 2a–c).
- Historical assignment outcomes: per-student bean-penalty distributions split
  by cohort year (Figure 3a–c).
"""

from __future__ import annotations

import argparse
import base64
from io import BytesIO
from pathlib import Path
import re
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import numpy as np
import pandas as pd
import seaborn as sns

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from nrma import ORDER_TO_ROTATION, ROTATION_TO_ORDER, load_preferences
from utils.stress_tests import DISTRIBUTIONS, run_trials

sns.set_theme(style="whitegrid")

DEFAULT_OUT_DIR = PROJECT_ROOT / "figures"

RUNS = 25
STUDENTS = 80
BEANS = 24
SEED = 44106
BEAN_SWEEP = list(range(4, 101, 4))
STUDENT_SWEEP = list(range(4, 301, 4))
DIST_KEYS = list(DISTRIBUTIONS.keys())

# Manuscript uses these `alt` strings; keep them stable so the embed step can
# replace images reliably.
ALT_DELTA_B = "delta as a function of b"
ALT_DELTA_N = "delta as a function of n"
ALT_DELTA_B_LINEAR = "delta as a function of b with linear penalty"
ALT_DELTA_N_LINEAR = "delta as a function of n with linear penalty"
ALT_HIST_BEANS_BY_OPTION_2023 = "beans distribution by option by year"
ALT_HIST_BEANS_BY_OPTION_2024 = "beans distribution by option (2024)"
ALT_HIST_BEANS_BY_OPTION_2025 = "beans distribution by option (2025)"
ALT_BEAN_PENALTY_DENSITY_2023 = "bean penalty distribution (2023)"
ALT_BEAN_PENALTY_DENSITY_2024 = "bean penalty distribution (2024)"
ALT_BEAN_PENALTY_DENSITY_2025 = "bean penalty distribution (2025)"

HISTORICAL_YEARS = (2023, 2024, 2025)


def fig_to_base64(fig: matplotlib.figure.Figure, *, dpi: int = 150) -> str:
    buffer = BytesIO()
    fig.savefig(buffer, format="png", dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode("ascii")


def fig_to_data_uri(fig: matplotlib.figure.Figure, *, dpi: int = 150) -> str:
    return f"data:image/png;base64,{fig_to_base64(fig, dpi=dpi)}"


def file_to_base64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


def file_to_data_uri(path: Path, *, mime: str = "image/png") -> str:
    return f"data:{mime};base64,{file_to_base64(path)}"


def _plot_metric(
    data: pd.DataFrame,
    *,
    x: str,
    y: str,
    title: str,
    xlabel: str,
    ylabel: str,
    outfile: Path,
    ylim: tuple[float, float] | None = None,
) -> None:
    fig, ax = plt.subplots(figsize=(7, 4))
    sns.lineplot(
        data=data,
        x=x,
        y=y,
        hue="distribution",
        errorbar=("ci", 95),
        ax=ax,
    )
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    if ylim:
        ax.set_ylim(*ylim)

    legend = ax.legend(
        title="distribution",
        loc="center left",
        bbox_to_anchor=(1.02, 0.5),
        borderaxespad=0,
        frameon=False,
    )
    fig.tight_layout()
    fig.savefig(outfile, dpi=150, bbox_extra_artists=(legend,), bbox_inches="tight")
    plt.close(fig)


def generate_simulation_figures(
    out_dir: Path,
    *,
    runs: int = RUNS,
    students: int = STUDENTS,
    beans: int = BEANS,
    seed: int = SEED,
    distributions: list[str] | None = None,
    bean_sweep: list[int] = BEAN_SWEEP,
    student_sweep: list[int] = STUDENT_SWEEP,
) -> dict[str, Path]:
    """Generate the four simulation figures used in `static/manuscript.html`."""
    out_dir.mkdir(parents=True, exist_ok=True)
    dist_keys = distributions or DIST_KEYS

    outputs: dict[str, Path] = {}

    bean_results = run_trials(
        dist_keys,
        runs=runs,
        n_students=students,
        n_beans=beans,
        penalty="beans",
        seed=seed,
        bean_values=bean_sweep,
    )
    outfile = out_dir / "figure1a_delta_vs_beans.png"
    _plot_metric(
        bean_results,
        x="beans",
        y="average_error",
        title="δ vs Beans (Beans Penalty)",
        xlabel="Beans per Student",
        ylabel="δ (Average Error)",
        outfile=outfile,
        ylim=(0, 1),
    )
    outputs[ALT_DELTA_B] = outfile

    student_results = run_trials(
        dist_keys,
        runs=runs,
        n_students=students,
        n_beans=beans,
        penalty="beans",
        seed=seed,
        student_values=student_sweep,
    )
    outfile = out_dir / "figure1b_delta_vs_students.png"
    _plot_metric(
        student_results,
        x="students",
        y="average_error",
        title="δ vs Students (Beans Penalty)",
        xlabel="Students",
        ylabel="δ (Average Error)",
        outfile=outfile,
        ylim=(0, 1),
    )
    outputs[ALT_DELTA_N] = outfile

    bean_results_linear = run_trials(
        dist_keys,
        runs=runs,
        n_students=students,
        n_beans=beans,
        penalty="linear",
        seed=seed,
        bean_values=bean_sweep,
    )
    outfile = out_dir / "figure4a_delta_vs_beans_linear.png"
    _plot_metric(
        bean_results_linear,
        x="beans",
        y="average_error",
        title="δ vs Beans (Linear Penalty)",
        xlabel="Beans per Student",
        ylabel="δ (Average Error)",
        outfile=outfile,
        ylim=(0, 1),
    )
    outputs[ALT_DELTA_B_LINEAR] = outfile

    student_results_linear = run_trials(
        dist_keys,
        runs=runs,
        n_students=students,
        n_beans=beans,
        penalty="linear",
        seed=seed,
        student_values=student_sweep,
    )
    outfile = out_dir / "figure4b_delta_vs_students_linear.png"
    _plot_metric(
        student_results_linear,
        x="students",
        y="average_error",
        title="δ vs Students (Linear Penalty)",
        xlabel="Students",
        ylabel="δ (Average Error)",
        outfile=outfile,
        ylim=(0, 1),
    )
    outputs[ALT_DELTA_N_LINEAR] = outfile

    return outputs


def _load_historical_preferences(data_dir: Path) -> pd.DataFrame:
    bean_cols = list(ROTATION_TO_ORDER.values())
    frames: list[pd.DataFrame] = []
    for year in HISTORICAL_YEARS:
        df = load_preferences(data_dir / f"responses{year}.csv", shuffle=False)
        long = df.melt(
            id_vars=["studentID"],
            value_vars=bean_cols,
            var_name="rotation_order",
            value_name="beans",
        )
        long["option"] = long["rotation_order"].map(ORDER_TO_ROTATION)
        long["year"] = str(year)
        frames.append(long)
    return pd.concat(frames, ignore_index=True)


def generate_historical_figures(
    out_dir: Path,
    *,
    data_dir: Path = PROJECT_ROOT / "data",
) -> dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    df = _load_historical_preferences(data_dir)
    option_order = ["Option 1", "Option 2", "Option 3", "Option 4"]

    palette = sns.color_palette("tab10", n_colors=len(option_order))
    bean_alts = {
        2023: ALT_HIST_BEANS_BY_OPTION_2023,
        2024: ALT_HIST_BEANS_BY_OPTION_2024,
        2025: ALT_HIST_BEANS_BY_OPTION_2025,
    }
    penalty_alts = {
        2023: ALT_BEAN_PENALTY_DENSITY_2023,
        2024: ALT_BEAN_PENALTY_DENSITY_2024,
        2025: ALT_BEAN_PENALTY_DENSITY_2025,
    }

    outputs: dict[str, Path] = {}

    legend_handles = [
        Patch(facecolor=color, edgecolor=color, alpha=0.75, label=label)
        for color, label in zip(palette, option_order)
    ]

    for idx, year in enumerate(HISTORICAL_YEARS):
        year_str = str(year)
        subset = df[df["year"] == year_str]
        fig, ax = plt.subplots(figsize=(6.2, 3.6))
        sns.kdeplot(
            data=subset,
            x="beans",
            hue="option",
            hue_order=option_order,
            palette=palette,
            fill=True,
            multiple="fill",
            common_norm=False,
            cut=0,
            clip=(0, BEANS),
            bw_adjust=0.8,
            legend=False,
            ax=ax,
        )
        ax.set_title(f"Year {year_str}")
        ax.set_xlim(-0.5, BEANS + 0.5)
        ax.set_xlabel("Beans Assigned")
        ax.set_ylabel("Proportion")
        ax.set_ylim(0, 1)
        ax.set_xticks([0, 6, 12, 18, 24])

        legend = ax.legend(
            handles=legend_handles,
            title="Rotation Option",
            loc="center left",
            bbox_to_anchor=(1.02, 0.5),
            frameon=False,
        )

        panel = chr(ord("a") + idx)
        outfile = out_dir / f"figure2{panel}_historical_beans_by_option_{year_str}.png"
        fig.tight_layout()
        save_kwargs: dict[str, object] = {"dpi": 150, "bbox_inches": "tight"}
        if legend is not None:
            save_kwargs["bbox_extra_artists"] = (legend,)
        fig.savefig(outfile, **save_kwargs)
        plt.close(fig)
        outputs[bean_alts[year]] = outfile

    from nrma import assign_rotations

    bean_cols = list(ROTATION_TO_ORDER.values())
    col_index = {col: idx for idx, col in enumerate(bean_cols)}
    for idx, year in enumerate(HISTORICAL_YEARS):
        year_str = str(year)
        prefs = load_preferences(data_dir / f"responses{year_str}.csv", shuffle=False)
        performance, _ = assign_rotations(prefs, penalty="beans", n_beans=BEANS)

        beans = performance[bean_cols].astype(float)
        beans = beans.div(beans.sum(axis=1), axis=0).mul(BEANS).fillna(0)
        assigned_idx = performance["rotation_order"].map(col_index).to_numpy()
        assigned_beans = beans.to_numpy()[np.arange(len(performance)), assigned_idx]
        penalties = BEANS - assigned_beans

        fig, ax = plt.subplots(figsize=(6.2, 3.6))
        sns.kdeplot(
            x=penalties,
            fill=True,
            cut=0,
            clip=(0, BEANS),
            bw_adjust=0.8,
            ax=ax,
        )
        ax.set_title(f"Year {year_str}")
        ax.set_xlabel("Penalty (Beans)")
        ax.set_ylabel("Density")
        ax.set_xlim(-0.5, BEANS + 0.5)
        ax.set_xticks([0, 6, 12, 18, 24])

        panel = chr(ord("a") + idx)
        outfile = out_dir / f"figure3{panel}_bean_penalty_density_{year_str}.png"
        fig.tight_layout()
        fig.savefig(outfile, dpi=150, bbox_inches="tight")
        plt.close(fig)
        outputs[penalty_alts[year]] = outfile

    return outputs


def _replace_img_src(html: str, *, alt: str, src: str) -> str:
    pattern = re.compile(
        rf'(<img\s+[^>]*\bsrc=")([^"]*)("[^>]*\balt="{re.escape(alt)}"[^>]*>)'
    )
    updated, count = pattern.subn(rf"\1{src}\3", html, count=1)
    if count != 1:
        raise ValueError(f"Expected exactly one <img> with alt='{alt}', found {count}.")
    return updated


def embed_figures_in_manuscript(
    manuscript_path: Path,
    *,
    figures_by_alt: dict[str, Path],
) -> None:
    html = manuscript_path.read_text(encoding="utf-8")

    for alt, path in figures_by_alt.items():
        html = _replace_img_src(html, alt=alt, src=file_to_data_uri(path))

    manuscript_path.write_text(html, encoding="utf-8")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate NRMA manuscript figures.")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=DEFAULT_OUT_DIR,
        help="Where to write PNG files.",
    )
    parser.add_argument(
        "--manuscript-html",
        type=Path,
        default=None,
        help="If set, embeds generated figures into this HTML file as base64 data URIs.",
    )
    parser.add_argument("--runs", type=int, default=RUNS)
    parser.add_argument("--students", type=int, default=STUDENTS)
    parser.add_argument("--beans", type=int, default=BEANS)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument(
        "--distributions",
        nargs="+",
        default=None,
        help=f"Subset of distributions to plot. Choices: {list(DISTRIBUTIONS.keys())}",
    )
    parser.add_argument("--skip-simulations", action="store_true")
    parser.add_argument("--skip-historical", action="store_true")
    parser.add_argument(
        "--print-data-uris",
        action="store_true",
        help="Print a mapping of alt text to data URI (useful for manual embedding).",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()

    figures_by_alt: dict[str, Path] = {}
    if not args.skip_simulations:
        figures_by_alt.update(
            generate_simulation_figures(
                args.out_dir,
                runs=args.runs,
                students=args.students,
                beans=args.beans,
                seed=args.seed,
                distributions=args.distributions,
            )
        )
    if not args.skip_historical:
        figures_by_alt.update(generate_historical_figures(args.out_dir))

    if args.manuscript_html:
        embed_figures_in_manuscript(args.manuscript_html, figures_by_alt=figures_by_alt)

    if args.print_data_uris:
        for alt, path in figures_by_alt.items():
            print(f"{alt}={file_to_data_uri(path)}")


if __name__ == "__main__":
    main()
