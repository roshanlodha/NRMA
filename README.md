# Rotation Order Matching Algorithm

This algorithm is designed to help third year medical students assign to the rotation order of their preference using a linear sum optimizer. The algorithm takes in the preferences of the students and the availability of the rotations, and assigns the students to the rotations in a way that maximizes the overall satisfaction of the students.

## Requirements

In order to use this algorithm, you will need to have the following packages installed:

* Python3 
* Pandas (for data manipulation and analysis)
* Scipy (for optimization functions)
* Numpy (for numerical computing)

You can install these packages by running the following command in the downloaded path:
```
pip3 install requirements.txt
```

## Usage

To use the algorithm, the path of the preference matrix should be specified as the `filename` variable in `NRMA.py`. The preference matrix should be a csv file with rows representing the students and columns representing the rotation preferences. The values in the matrix should represent the student's preference for the rotation, with higher values indicating a stronger preference.

The optimal rotation order assignment can be found by running the following command:

```
python3 NRMA.py
```

### Beans vs Linear Mode
The `linear` mode requires a preference.csv file with ranked preferences, while the `beans` mode requires a performance,csv file with assigned beans. More information about beans assignment can be found [here](./MANUSCRIPT.md).

### Simulation File
Advanced testing for different penalty functions can be done via `NRMA_simulate.py`.

## Example

Running `python3 NRMA.py` on the provided test file assigns a group of 8 students to 4 rotation orders.
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
Percent of students who recieved their first choice rotation: 0.625
```
Note that the order of students is stochastic. 