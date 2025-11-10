# Rotation Order Matching Algorithm

This algorithm is designed to help third year medical students assign to the rotation order of their preference using a linear sum optimizer. The algorithm takes in the preferences of the students and the availability of the rotations, and assigns the students to the rotations in a way that maximizes the overall satisfaction of the students.

To use this application via a web-interface, run the bundled Flask application (see below) or visit [NRMA](https://nrma.pythonanywhere.com).

## Requirements

In order to use this algorithm, you will need to have the following packages installed:

* Python3 
* Pandas (for data manipulation and analysis)
* SciPy (for optimization functions)
* NumPy (for numerical computing)

You can install these packages by running the following command in the downloaded path:
```
pip3 install -r requirements.txt
```

## Usage

### Web interface

1. Install the requirements described above.
2. Start the Flask server from the project root:
   ```
   python app.py
   ```
3. Visit `http://127.0.0.1:5000/`, upload the CSV export, and download the generated `assignment.csv`.
4. Open the **Stress Tests** tab to generate simulation runs, view charts, and download the aggregated results when stress-testing new policies.

### Command-line utility

The assignment logic now lives in `nrma.py`. You can run it directly from a Python shell or script:

```python
from nrma import assign_rotations_from_file
assign_rotations_from_file("batch_test.csv", output_path="out/rotations.csv")
```

The helper returns both the processed dataframe and a performance summary (average error, percent of students receiving their first choice, etc.).

### Beans vs Linear Mode
The `linear` mode requires a preference.csv file with ranked preferences, while the `beans` mode requires a performance,csv file with assigned beans. More information about beans assignment can be found [here](./MANUSCRIPT.md).

### Simulation File
Advanced testing for different penalty functions can be done via the modern simulator: `python stress_tests.py --runs 100 --students 120 --distributions uniform clustered`. The same simulator powers the `/simulations` page in the Flask UI, so you can tune parameters and view charts without leaving the browser.

The original CLI script is preserved at `manuscript/NRMAcli.py` for archival/documentation purposes.

## Example

Running `python nrma.py responses.csv --output out/rotations.csv` on the provided test file assigns a group of 8 students to 4 rotation orders.
The output of this code should be:
```
  studentID  ...            rotation_order
0      abc6  ...  TBC1 – TBC3 – TBC2 – LAB
1      abc8  ...  TBC2 – LAB – TBC1 – TBC3
2      abc3  ...  TBC1 – TBC3 – TBC2 – LAB
3      abc4  ...  TBC3 – TBC1 – LAB – TBC2
4      abc1  ...  LAB – TBC2 – TBC3 – TBC1
5      abc5  ...  TBC3 – TBC1 – LAB – TBC2
6      abc2  ...  LAB – TBC2 – TBC3 – TBC1
7      abc7  ...  TBC2 – LAB – TBC1 – TBC3

[8 rows x 7 columns]
Average error of assignment for first rotation: 0.421875
Percent of students who received their first choice rotation: 0.625
```
Note that the order of students is stochastic. 
