from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Tuple

import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment

Penalty = Literal["beans", "linear"]

ROTATION_LABELS = {0: "Option 1", 1: "Option 2", 2: "Option 3", 3: "Option 4"}
ROTATION_TO_ORDER = {
    "Option 1": "LAB – TBC2 – TBC3 – TBC1",
    "Option 2": "TBC2 – LAB – TBC1 – TBC3",
    "Option 3": "TBC3 – TBC1 – LAB – TBC2",
    "Option 4": "TBC1 – TBC3 – TBC2 – LAB",
}
ORDER_TO_ROTATION = {v: k for k, v in ROTATION_TO_ORDER.items()}
N_ROTATIONS = len(ROTATION_LABELS)


@dataclass
class AssignmentSummary:
    total_error: float
    average_error: float
    pct_first_choice: float
    per_student_penalty: float
    output_path: Path | None = None


def load_preferences(
    filepath: str | Path,
    *,
    shuffle: bool = True,
) -> pd.DataFrame:
    """
    Load the CSV exported from Qualtrics/Forms and normalize column names.
    Expects the structure from example_responses.csv:
    Index 2: caseID
    Indices 7-10: Bean counts
    """
    preference_df = pd.read_csv(filepath, encoding="cp1252")

    # Select CaseID (idx 2) and the 4 bean columns (idx 7, 8, 9, 10)
    preference_df = preference_df.iloc[:, [2, 7, 8, 9, 10]]

    preference_df = preference_df.set_axis(
        ["studentID"] + list(ROTATION_TO_ORDER.values()), axis=1
    )

    if shuffle:
        preference_df = preference_df.sample(frac=1).reset_index(drop=True)

    return preference_df


def assign_rotations(
    preference_df: pd.DataFrame,
    *,
    penalty: Penalty = "beans",
    n_beans: int = 24,
) -> Tuple[pd.DataFrame, AssignmentSummary]:
    cost_matrix, phantom_students = _build_cost_matrix(
        preference_df, penalty=penalty, n_beans=n_beans
    )
    rotations, total_error = _rotation_calc(cost_matrix, phantom_students, n_beans)
    performance = _combine_results(preference_df, rotations, phantom_students)
    summary = _summarize_results(performance, total_error, n_beans)
    return performance, summary


def assign_rotations_from_file(
    filepath: str | Path,
    *,
    penalty: Penalty = "beans",
    n_beans: int = 24,
    shuffle: bool = True,
    output_path: str | Path | None = None,
) -> Tuple[pd.DataFrame, AssignmentSummary]:
    preference_df = load_preferences(
        filepath, shuffle=shuffle
    )
    performance, summary = assign_rotations(
        preference_df, penalty=penalty, n_beans=n_beans
    )

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        performance.to_csv(output_path, index=False)
        summary.output_path = output_path

    return performance, summary


def _build_cost_matrix(
    preference_df: pd.DataFrame,
    *,
    penalty: Penalty,
    n_beans: int,
) -> Tuple[np.ndarray, int]:
    """
    Convert weighted bean preferences into a padded square matrix ready for
    linear sum assignment.
    """
    cost_df = preference_df.drop(columns=["studentID"]).astype(float)
    cost_df = cost_df.div(cost_df.sum(axis=1), axis=0) * n_beans
    cost_df = cost_df.fillna(0)

    cost_df = cost_df.sub(cost_df.sum(axis=1), axis=0) * -1
    cost_matrix = pd.DataFrame.to_numpy(cost_df)

    if penalty == "linear":
        cost_matrix = _cost_to_rank(cost_matrix)

    return _pad_matrix(cost_matrix, n_beans)


def _cost_to_rank(cost_matrix: np.ndarray) -> np.ndarray:
    """
    Convert bean counts into a rank preference penalty structure.
    """
    ranked = cost_matrix.copy()
    for rank in range(N_ROTATIONS):
        ranked[np.where(ranked == np.max(ranked))] = rank - N_ROTATIONS
    return ranked * -1


def _pad_matrix(cost: np.ndarray, n_beans: int) -> Tuple[np.ndarray, int]:
    """
    1. Pad rows to a multiple of the number of rotations.
    2. Tile columns to maintain a square cost matrix for linear assignment.
    """
    phantom_students = 0
    padded = cost

    while padded.shape[0] % N_ROTATIONS != 0:
        padded = np.vstack([padded, np.full(N_ROTATIONS, n_beans)])
        phantom_students += 1

    padded = np.tile(padded, (1, padded.shape[0] // N_ROTATIONS))
    return padded, phantom_students


def _rotation_calc(
    cost_matrix: np.ndarray, phantom_students: int, n_beans: int
) -> Tuple[list[str], float]:
    row_ind, col_ind = linear_sum_assignment(cost_matrix)
    total_error = cost_matrix[row_ind, col_ind].sum()

    rotation_index = col_ind % N_ROTATIONS
    rotations = [ROTATION_LABELS.get(index, "Option 1") for index in rotation_index]

    total_error -= phantom_students * n_beans
    return rotations, total_error


def _combine_results(
    preference_df: pd.DataFrame, rotations: list[str], phantom_students: int
) -> pd.DataFrame:
    rotation_frame = pd.DataFrame({"optimal_rotation": rotations})
    if phantom_students:
        rotation_frame = rotation_frame.iloc[:-phantom_students]

    performance = pd.concat([preference_df.reset_index(drop=True), rotation_frame], axis=1)
    performance["rotation_order"] = performance["optimal_rotation"].map(
        ROTATION_TO_ORDER
    )
    return performance.sort_values(by=["studentID"]).reset_index(drop=True)


def _summarize_results(
    performance: pd.DataFrame,
    total_error: float,
    n_beans: int,
) -> AssignmentSummary:
    n_students = len(performance)
    avg_error = total_error / (n_students * n_beans) if n_students else 0
    avg_penalty = total_error / n_students if n_students else 0
    matches = (
        performance.drop(columns=["studentID", "optimal_rotation"])
        .filter(items=list(ROTATION_TO_ORDER.values()))
        .idxmax(axis=1)
    )
    pct_first_choice = (
        (matches == performance["rotation_order"]).mean() if n_students else 0
    )

    return AssignmentSummary(
        total_error=total_error,
        average_error=avg_error,
        pct_first_choice=float(pct_first_choice),
        per_student_penalty=avg_penalty,
    )


__all__ = [
    "AssignmentSummary",
    "assign_rotations",
    "assign_rotations_from_file",
    "load_preferences",
    "ORDER_TO_ROTATION",
    "ROTATION_LABELS",
    "ROTATION_TO_ORDER",
]


def _parse_cli_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Assign students to rotations based on preference beans."
    )
    parser.add_argument("csv_path", help="Path to the preference CSV.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("out/rotations.csv"),
        help="Where to write the resulting assignment CSV.",
    )
    parser.add_argument(
        "--penalty",
        choices=["beans", "linear"],
        default="beans",
        help="Penalty structure to use when constructing the cost matrix.",
    )
    parser.add_argument(
        "--beans",
        type=int,
        default=24,
        help="Total number of beans allocated per student.",
    )
    parser.add_argument(
        "--no-shuffle",
        action="store_true",
        help="Disable shuffling before running the optimizer.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_cli_args()
    _, summary = assign_rotations_from_file(
        args.csv_path,
        output_path=args.output,
        penalty=args.penalty,
        n_beans=args.beans,
        shuffle=not args.no_shuffle,
    )
    print(f"Wrote assignments to {args.output}")
    print(f"Total error: {summary.total_error:.2f}")
    print(f"Average error: {summary.average_error:.4f}")
    print(f"Avg penalty per student: {summary.per_student_penalty:.2f}")
    print(f"First choice hit rate: {summary.pct_first_choice:.2%}")


if __name__ == "__main__":
    main()
