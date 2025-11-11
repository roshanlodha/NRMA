#!/usr/bin/env python3
"""Generate manuscript figures from the NRMA stress-test simulations.

This script reproduces the four figures embedded in the LaTeX manuscript by
running the modern `stress_tests` simulator and exporting seaborn charts to the
`manuscript/images` directory. It intentionally mirrors the settings used by
the web UI (80 students, 24 beans, 25 Monte Carlo runs per distribution) so
that the manuscript visuals align with the interactive tool.
"""

from __future__ import annotations

from pathlib import Path
import sys

import matplotlib.pyplot as plt
import seaborn as sns

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from stress_tests import DISTRIBUTIONS, run_trials

# Keep the visual style consistent with the simulator page.
sns.set_theme(style="whitegrid")

OUTPUT_DIR = Path(__file__).parent / "images"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

RUNS = 25
STUDENTS = 80
BEANS = 24
SEED = 44106
BEAN_SWEEP = list(range(4, 101, 4))
STUDENT_SWEEP = list(range(4, 301, 4))
DIST_KEYS = list(DISTRIBUTIONS.keys())


def _plot_metric(
    data,
    *,
    x: str,
    y: str,
    title: str,
    xlabel: str,
    ylabel: str,
    outfile: Path,
    ylim: tuple[float, float] | None = None,
) -> None:
    """Helper that plots a seaborn line chart with confidence bands."""
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
    ax.legend(title="distribution", loc="best")
    fig.tight_layout()
    fig.savefig(outfile, dpi=150)
    plt.close(fig)


def generate_bean_sweep_figures() -> None:
    """Sweep beans-per-student and export the first two manuscript figures."""
    bean_results = run_trials(
        DIST_KEYS,
        runs=RUNS,
        n_students=STUDENTS,
        n_beans=BEANS,
        penalty="beans",
        seed=SEED,
        bean_values=BEAN_SWEEP,
    )
    _plot_metric(
        bean_results,
        x="beans",
        y="pct_first_choice",
        title="First Choice Rate vs Beans",
        xlabel="Beans per Student",
        ylabel="First Choice Hit Rate",
        outfile=OUTPUT_DIR / "beans_error_beans.png",
        ylim=(0, 1),
    )
    _plot_metric(
        bean_results,
        x="beans",
        y="average_error",
        title="Average Error vs Beans",
        xlabel="Beans per Student",
        ylabel="Average Error",
        outfile=OUTPUT_DIR / "beans_error_linear.png",
    )


def generate_student_sweep_figures() -> None:
    """Sweep cohort size and export the remaining two manuscript figures."""
    student_results = run_trials(
        DIST_KEYS,
        runs=RUNS,
        n_students=STUDENTS,
        n_beans=BEANS,
        penalty="beans",
        seed=SEED,
        student_values=STUDENT_SWEEP,
    )
    _plot_metric(
        student_results,
        x="students",
        y="average_error",
        title="Average Error vs Students",
        xlabel="Students",
        ylabel="Average Error",
        outfile=OUTPUT_DIR / "students_error_beans.png",
    )
    _plot_metric(
        student_results,
        x="students",
        y="per_student_penalty",
        title="Penalty per Student vs Students",
        xlabel="Students",
        ylabel="Penalty (Beans)",
        outfile=OUTPUT_DIR / "students_error_linear.png",
    )


def main() -> None:
    generate_bean_sweep_figures()
    generate_student_sweep_figures()


if __name__ == "__main__":
    main()
