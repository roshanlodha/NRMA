#!/usr/bin/env python3
"""Generate manuscript figures from simulations + historical preference data.

Outputs PNGs to `figures/` and provides helpers to embed them into
`static/manuscript.html` as base64 data URIs.

Figures currently supported:
- Simulation delta (average error) vs beans/students under both `beans` and
  `linear` penalty modes (Figures 1–2 in the manuscript).
- Historical preference distributions: beans by option, faceted by year.
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
ALT_HIST_BEANS_BY_OPTION_YEAR = "beans distribution by option by year"


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
        marker="o",
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
    outfile = out_dir / "figure2a_delta_vs_beans_linear.png"
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
    outfile = out_dir / "figure2b_delta_vs_students_linear.png"
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
    for year in (2023, 2024, 2025):
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

    grid = sns.catplot(
        data=df,
        x="option",
        y="beans",
        col="year",
        kind="violin",
        inner="quartile",
        cut=0,
        order=option_order,
        height=3.4,
        aspect=0.9,
        color=sns.color_palette("crest")[2],
        sharey=True,
    )
    grid.set_axis_labels("Rotation Option", "Beans Assigned")
    grid.set_titles("Year {col_name}")
    for ax in grid.axes.flat:
        ax.set_ylim(-0.5, 24.5)

    outfile = out_dir / "historical_beans_by_option_year.png"
    grid.figure.tight_layout()
    grid.figure.savefig(outfile, dpi=150, bbox_inches="tight")
    plt.close(grid.figure)
    return {ALT_HIST_BEANS_BY_OPTION_YEAR: outfile}


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
        if alt in (
            ALT_DELTA_B,
            ALT_DELTA_N,
            ALT_DELTA_B_LINEAR,
            ALT_DELTA_N_LINEAR,
        ):
            html = _replace_img_src(html, alt=alt, src=file_to_data_uri(path))

    if ALT_HIST_BEANS_BY_OPTION_YEAR in figures_by_alt:
        hist_uri = file_to_data_uri(figures_by_alt[ALT_HIST_BEANS_BY_OPTION_YEAR])
        if ALT_HIST_BEANS_BY_OPTION_YEAR not in html:
            insert_at = html.find("<h2>Acknowledgments</h2>")
            if insert_at == -1:
                raise ValueError(
                    "Could not find the Acknowledgments section to insert historical figure."
                )
            figure_block = f"""
    <p>Figure 3 summarizes how students distributed their 24 beans across the four rotation-order options in each cohort year.</p>
    <figure>
        <img src=\"{hist_uri}\" alt=\"{ALT_HIST_BEANS_BY_OPTION_YEAR}\">
        <figcaption style=\"text-align: center; display: block; margin-top: -1rem; margin-bottom: 2rem;\">Figure 3: Distribution of beans assigned to each rotation-order option by year.</figcaption>
    </figure>

"""
            html = html[:insert_at] + figure_block + html[insert_at:]
        else:
            html = _replace_img_src(html, alt=ALT_HIST_BEANS_BY_OPTION_YEAR, src=hist_uri)

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
