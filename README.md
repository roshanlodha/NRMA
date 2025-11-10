# NRMA Rotation Assignment Toolkit

A modernized toolkit for assigning third-year medical students to clinical rotation tracks. It bundles a production-ready Flask UI, a composable Python module, and an interactive stress-test lab so you can audit fairness before schedules go live.

## Highlights
- **Web experience** – Upload the Qualtrics/Forms CSV, review summary metrics, and download the optimized `assignment.csv`.
- **Static runner** – Serve `nrma_static/index.html` from any static host to process preference files without Flask or Python.
- **Simulation lab** – Explore how the optimizer performs under uniform, clustered, polarized, or custom preference distributions, with charts rendered directly in the browser.
- **Python API & CLI** – Import `nrma.py` in your own notebooks or run it from the command line for scripted workflows.
- **Reproducible stress tests** – The `stress_tests.py` CLI mirrors the UI experience and produces CSV summaries for further analysis.
- **Legacy reference** – The original CLI script lives on in `manuscript/NRMAcli.py` for archival and manuscript reproducibility.

## Repository Layout
```
.
├── app.py               # Flask entry point (upload + stress-test pages)
├── nrma.py              # Core assignment logic & CLI
├── stress_tests.py      # Simulation library + CLI
├── templates/           # Shared UI templates (base + upload + simulations)
├── nrma_static/         # HTML + JS bundle for running assignments in the browser
├── uploads/             # Runtime output directory for assignment.csv
├── out/, plots/         # Optional analysis artifacts
├── responses.csv        # Sample preferences file for local testing
└── manuscript/          # Manuscript assets and the archival NRMAcli script
```

## Prerequisites
- Python 3.9+
- System dependencies required by SciPy/matplotlib (e.g., `gcc`, `libopenblas`)
- Python packages listed in `requirements.txt`

Install everything inside a virtual environment:
```bash
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
```

## Running the Web App
1. Activate your virtual environment.
2. Start the server from the project root:
   ```bash
   python app.py
   ```
3. Open `http://127.0.0.1:5000/`.
4. Use the **Assignments** tab to upload the CSV export and download the generated `assignment.csv` (stored under `uploads/`).
5. Switch to **Stress Tests** to configure distributions, run simulations, and inspect the charts/summary tables inline.

The UI uses the same assignment engine and simulation code paths as the CLI tools, so you can trust that browser experiments match scripted runs.

## Python Module & CLI
`nrma.py` exposes both reusable helpers and an ergonomic CLI:
```bash
python nrma.py responses.csv \
  --output out/rotations.csv \
  --penalty beans \
  --beans 24
```

Programmatic usage:
```python
from nrma import assign_rotations_from_file

performance_df, summary = assign_rotations_from_file(
    "responses.csv",
    output_path="out/rotations.csv",
    penalty="beans",
    n_beans=24,
)
print(summary)
```

Key CLI flags:
- `--penalty {beans,linear}` – choose bean weighting or rank-based penalties.
- `--beans N` – total beans per student (default 24).
- `--keep-identifiers` – prevent automatic removal of identifying columns 2 & 3.
- `--no-shuffle` – preserve original student order when debugging.

## Stress-Test CLI
The same simulation engine that powers the web UI is available at the command line:
```bash
python stress_tests.py \
  --distributions uniform clustered polarized \
  --runs 200 \
  --students 120 \
  --beans 24 \
  --penalty beans \
  --output out/simulations
```

Outputs:
- `out/simulations/simulation_runs.csv` – every run with detailed metrics.
- `out/simulations/distribution_summary.csv` – aggregated stats (avg error, hit rates, etc.).

The CLI automatically produces the images embedded in the UI when invoked from Flask, but you can import `build_charts` in notebooks if you need custom dashboards.

## Sample Data
- `responses.csv` – anonymized example you can use to test both the CLI and the UI.
- Generated artifacts appear in `uploads/assignment.csv` (web) or whatever `--output` path you specify.

## Legacy + Manuscript Assets
- `manuscript/NRMAcli.py` – original CLI preserved for manuscript reproducibility.
- `manuscript/NRMA.tex`, poster, images, and bibliography – supporting research materials. They are untouched by the modern toolchain but remain available for reference.

## Support & Contributions
Bug reports, feature ideas, or performance findings from your own stress tests are welcome. Please open an issue or a PR with reproducible steps (including sample CSVs or simulator settings) so the maintainers can iterate quickly. Happy matching!
