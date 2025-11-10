from __future__ import annotations

import argparse
import base64
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Callable, Dict, Iterable, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from nrma import ROTATION_TO_ORDER, assign_rotations

sns.set_theme(style="whitegrid")

DistributionFn = Callable[[np.random.Generator, int, int], pd.DataFrame]


@dataclass(frozen=True)
class Distribution:
    name: str
    description: str
    generator: DistributionFn


def uniform_distribution(rng: np.random.Generator, n_students: int, n_beans: int) -> pd.DataFrame:
    """
    Every student samples preferences from a flat Dirichlet.
    """
    probs = rng.dirichlet(alpha=np.ones(len(ROTATION_TO_ORDER)), size=n_students)
    return _build_preferences_from_probs(rng, probs, n_beans)


def single_peak_distribution(
    rng: np.random.Generator, n_students: int, n_beans: int
) -> pd.DataFrame:
    """
    Strong majority prefers Option 1 with small noise across other rotations.
    """
    alpha = np.array([6, 1, 1, 1])
    probs = rng.dirichlet(alpha=alpha, size=n_students)
    return _build_preferences_from_probs(rng, probs, n_beans)


def clustered_distribution(
    rng: np.random.Generator, n_students: int, n_beans: int
) -> pd.DataFrame:
    """
    Students are split into clusters that each prefer a different rotation order.
    """
    cluster_templates = np.array(
        [
            [0.65, 0.2, 0.1, 0.05],
            [0.25, 0.55, 0.1, 0.1],
            [0.1, 0.2, 0.6, 0.1],
            [0.1, 0.15, 0.2, 0.55],
        ]
    )
    assignments = rng.integers(0, len(cluster_templates), size=n_students)
    probs = np.array(
        [rng.dirichlet(cluster_templates[idx] * 8) for idx in assignments]
    )
    return _build_preferences_from_probs(rng, probs, n_beans)


def polarized_distribution(
    rng: np.random.Generator, n_students: int, n_beans: int
) -> pd.DataFrame:
    """
    Half the cohort fights for Option 1, the other half for Option 3.
    """
    half = n_students // 2
    alpha_a = np.array([7, 1, 1, 1])
    alpha_b = np.array([1, 1, 7, 1])
    probs_a = rng.dirichlet(alpha=alpha_a, size=half)
    probs_b = rng.dirichlet(alpha=alpha_b, size=n_students - half)
    probs = np.vstack([probs_a, probs_b])
    rng.shuffle(probs, axis=0)
    return _build_preferences_from_probs(rng, probs, n_beans)


def top_two_distribution(
    rng: np.random.Generator, n_students: int, n_beans: int
) -> pd.DataFrame:
    """
    Students strongly prefer two rotations while being indifferent to the rest.
    """
    probs = []
    for _ in range(n_students):
        top_choices = rng.choice(len(ROTATION_TO_ORDER), size=2, replace=False)
        base = np.full(len(ROTATION_TO_ORDER), 0.05)
        base[top_choices] = 0.45
        probs.append(rng.dirichlet(base * 10))
    probs = np.array(probs)
    return _build_preferences_from_probs(rng, probs, n_beans)


DISTRIBUTIONS: Dict[str, Distribution] = {
    "uniform": Distribution(
        "uniform",
        "Evenly random preferences.",
        uniform_distribution,
    ),
    "single_peak": Distribution(
        "single_peak",
        "Option 1 is overwhelmingly popular.",
        single_peak_distribution,
    ),
    "clustered": Distribution(
        "clustered",
        "Distinct cohorts that each prefer a specific track.",
        clustered_distribution,
    ),
    "polarized": Distribution(
        "polarized",
        "Two camps fight over different first choices.",
        polarized_distribution,
    ),
    "top_two": Distribution(
        "top_two",
        "Students fight for their top two rotations and randomize the rest.",
        top_two_distribution,
    ),
}


def _build_preferences_from_probs(
    rng: np.random.Generator, probs: np.ndarray, n_beans: int
) -> pd.DataFrame:
    beans = np.vstack([rng.multinomial(n_beans, pvals) for pvals in probs])
    df = pd.DataFrame(beans, columns=list(ROTATION_TO_ORDER.values()))
    df.insert(0, "studentID", [f"sim_{idx + 1:04d}" for idx in range(len(df))])
    return df


def run_trials(
    distribution_keys: Iterable[str],
    runs: int,
    n_students: int,
    n_beans: int,
    penalty: str,
    seed: int,
    bean_values: Sequence[int] | None = None,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    records = []
    beans_list = list(bean_values) if bean_values else [n_beans]
    for key in distribution_keys:
        if key not in DISTRIBUTIONS:
            raise ValueError(f"Unknown distribution '{key}'. Choices: {list(DISTRIBUTIONS)}")
        generator = DISTRIBUTIONS[key].generator
        for beans in beans_list:
            for run in range(1, runs + 1):
                preferences = generator(rng, n_students, beans)
                _, summary = assign_rotations(preferences, penalty=penalty, n_beans=beans)
                records.append(
                    {
                        "distribution": key,
                        "run": run,
                        "students": n_students,
                        "beans": beans,
                        "penalty": penalty,
                        "total_error": summary.total_error,
                        "average_error": summary.average_error,
                        "pct_first_choice": summary.pct_first_choice,
                    }
                )
    return pd.DataFrame(records)


def summarize_results(results: pd.DataFrame) -> pd.DataFrame:
    if results.empty:
        return pd.DataFrame(
            columns=[
                "distribution",
                "runs",
                "avg_total_error",
                "avg_average_error",
                "avg_first_choice",
                "worst_average_error",
                "best_first_choice",
            ]
        )

    return (
        results.groupby("distribution")
        .agg(
            runs=("run", "count"),
            avg_total_error=("total_error", "mean"),
            avg_average_error=("average_error", "mean"),
            avg_first_choice=("pct_first_choice", "mean"),
            worst_average_error=("average_error", "max"),
            best_first_choice=("pct_first_choice", "max"),
        )
        .reset_index()
    )


def build_charts(results: pd.DataFrame) -> Dict[str, str]:
    charts: Dict[str, str] = {}
    if results.empty:
        return charts

    summary = summarize_results(results)

    if not summary.empty:
        fig, ax = plt.subplots(figsize=(6, 4))
        sns.barplot(
            data=summary,
            x="distribution",
            y="avg_average_error",
            ax=ax,
            palette="crest",
        )
        ax.set_ylabel("Average Error")
        ax.set_xlabel("Distribution")
        ax.set_title("Average Error by Distribution")
        charts["Average Error by Distribution"] = _fig_to_data_uri(fig)

        fig, ax = plt.subplots(figsize=(6, 4))
        sns.barplot(
            data=summary,
            x="distribution",
            y="avg_first_choice",
            ax=ax,
            palette="flare",
        )
        ax.set_ylabel("First Choice Hit Rate")
        ax.set_ylim(0, 1)
        ax.set_xlabel("Distribution")
        ax.set_title("First Choice Probability")
        charts["First Choice Probability"] = _fig_to_data_uri(fig)

    fig, ax = plt.subplots(figsize=(7, 4))
    sns.lineplot(
        data=results,
        x="run",
        y="average_error",
        hue="distribution",
        marker="o",
        ax=ax,
    )
    ax.set_ylabel("Average Error")
    ax.set_title("Average Error Across Runs")
    charts["Run Trajectory"] = _fig_to_data_uri(fig)

    if results["beans"].nunique() > 1:
        fig, ax = plt.subplots(figsize=(7, 4))
        sns.lineplot(
            data=results,
            x="beans",
            y="average_error",
            hue="distribution",
            marker="o",
            ax=ax,
        )
        ax.set_xlabel("Beans per Student")
        ax.set_ylabel("Average Error")
        ax.set_title("Average Error vs Beans")
        charts["Average Error vs Beans"] = _fig_to_data_uri(fig)

        fig, ax = plt.subplots(figsize=(7, 4))
        sns.lineplot(
            data=results,
            x="beans",
            y="pct_first_choice",
            hue="distribution",
            marker="o",
            ax=ax,
        )
        ax.set_xlabel("Beans per Student")
        ax.set_ylabel("First Choice Hit Rate")
        ax.set_title("First Choice Rate vs Beans")
        ax.set_ylim(0, 1)
        charts["First Choice vs Beans"] = _fig_to_data_uri(fig)

    return charts


def save_results(results: pd.DataFrame, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    detailed_path = output_dir / "simulation_runs.csv"
    results.to_csv(detailed_path, index=False)

    summary = summarize_results(results)
    summary_path = output_dir / "distribution_summary.csv"
    summary.to_csv(summary_path, index=False)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run NRMA stress tests over multiple preference distributions."
    )
    parser.add_argument(
        "--distributions",
        nargs="+",
        default=list(DISTRIBUTIONS.keys()),
        help=f"Subset of distributions to run. Choices: {list(DISTRIBUTIONS.keys())}",
    )
    parser.add_argument("--runs", type=int, default=50, help="Number of simulations per distribution.")
    parser.add_argument(
        "--students", type=int, default=80, help="Number of simulated students per run."
    )
    parser.add_argument("--beans", type=int, default=24, help="Number of beans per student.")
    parser.add_argument(
        "--penalty",
        choices=["beans", "linear"],
        default="beans",
        help="Penalty mode to test.",
    )
    parser.add_argument(
        "--bean-range",
        action="store_true",
        help="Sweep bean counts from 4 to 100 (multiples of 4) instead of a fixed --beans value.",
    )
    parser.add_argument(
        "--beans-list",
        type=str,
        help="Comma-separated list of bean counts to test (overrides --bean-range and --beans).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("out/simulations"),
        help="Directory where CSV summaries are written.",
    )
    parser.add_argument("--seed", type=int, default=44106, help="Random seed.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    bean_values: Sequence[int] | None = None
    if args.beans_list:
        bean_values = [int(x.strip()) for x in args.beans_list.split(",") if x.strip()]
    elif args.bean_range:
        bean_values = list(range(4, 101, 4))
    results = run_trials(
        args.distributions,
        runs=args.runs,
        n_students=args.students,
        n_beans=args.beans,
        penalty=args.penalty,
        seed=args.seed,
        bean_values=bean_values,
    )
    save_results(results, args.output)
    print(f"Wrote {len(results)} simulation rows to {args.output}")


def _fig_to_data_uri(fig: matplotlib.figure.Figure) -> str:
    buffer = BytesIO()
    fig.tight_layout()
    fig.savefig(buffer, format="png", dpi=150)
    plt.close(fig)
    buffer.seek(0)
    encoded = base64.b64encode(buffer.read()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


if __name__ == "__main__":
    main()
