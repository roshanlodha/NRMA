from pathlib import Path

from flask import Flask, redirect, render_template, request, send_file
from werkzeug.utils import secure_filename

from nrma import assign_rotations_from_file
from stress_tests import (
    DISTRIBUTIONS,
    build_charts,
    run_trials,
    summarize_results,
)

app = Flask(__name__)
UPLOAD_DIR = Path(app.root_path) / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
ASSIGNMENT_FILENAME = "assignment.csv"
DEFAULT_SIM_SETTINGS = {
    "runs": 25,
    "students": 80,
    "beans": 24,
    "penalty": "beans",
    "seed": 44106,
}


@app.route("/")
def upload_file() -> str:
    return render_template(
        "upload.html",
        active_page="upload",
        assignment_ready=False,
        assignment_table=None,
        assignment_columns=[],
    )


@app.route("/upload", methods=["POST"])
def upload_file_post():
    if "file" not in request.files:
        return redirect(request.url)

    file = request.files["file"]
    if not file or file.filename == "":
        return redirect(request.url)

    filepath = UPLOAD_DIR / secure_filename(file.filename)
    file.save(filepath)

    assignment_path = UPLOAD_DIR / ASSIGNMENT_FILENAME
    performance, summary = assign_rotations_from_file(
        filepath,
        output_path=assignment_path,
    )
    assignment_columns = list(performance.columns)
    assignment_table = performance.to_dict(orient="records")

    return render_template(
        "upload.html",
        assignment_ready=True,
        summary=summary,
        active_page="upload",
        assignment_table=assignment_table,
        assignment_columns=assignment_columns,
    )


@app.route("/download")
def download_file():
    assignment_filepath = UPLOAD_DIR / ASSIGNMENT_FILENAME
    if assignment_filepath.exists():
        return send_file(assignment_filepath, as_attachment=True)
    return "Assignment file not found."


@app.route("/simulations", methods=["GET", "POST"])
def simulations():
    settings = DEFAULT_SIM_SETTINGS.copy()
    selected_distributions = list(DISTRIBUTIONS.keys())
    results_records = []
    summary_records = []
    charts = {}
    error_message = None

    if request.method == "POST":
        selected = request.form.getlist("distributions")
        if selected:
            selected_distributions = selected

        try:
            settings["runs"] = max(1, int(request.form.get("runs", settings["runs"])))
            settings["students"] = max(
                4, int(request.form.get("students", settings["students"]))
            )
            settings["beans"] = max(1, int(request.form.get("beans", settings["beans"])))
            settings["seed"] = int(request.form.get("seed", settings["seed"]))
            settings["penalty"] = request.form.get(
                "penalty", settings["penalty"]
            ).lower()

            if not selected_distributions:
                raise ValueError("Select at least one distribution.")

            results = run_trials(
                selected_distributions,
                runs=settings["runs"],
                n_students=settings["students"],
                n_beans=settings["beans"],
                penalty=settings["penalty"],
                seed=settings["seed"],
            )
            summary = summarize_results(results)
            charts = build_charts(results)

            summary_records = summary.to_dict(orient="records")
            results_records = results.to_dict(orient="records")[:25]
        except ValueError as exc:
            error_message = str(exc)

    return render_template(
        "simulations.html",
        active_page="simulations",
        settings=settings,
        distributions=DISTRIBUTIONS,
        selected_distributions=selected_distributions,
        summary_records=summary_records,
        results_records=results_records,
        charts=charts,
        error_message=error_message,
    )


if __name__ == "__main__":
    app.run(debug=True)
