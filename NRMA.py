import pandas as pd
import numpy as np

# using optimized elinear sums problem solver
from scipy.optimize import linear_sum_assignment
# used for optimal number of beans
from scipy.special import factorial
np.random.seed(44106)

# mutable global variables
global preference_df
global studentIDs
global phantom_students
global error_df

simulate = False
penalty = "beans"
n_beans = 24
n_student = 7
n_rotations = 4
filename = "./batch_test.csv"

# definitions and converters
rotationdict = {0: "Option 1", 1: "Option 2", 2: "Option 3", 3: "Option 4"}
option_to_order_dict = {
	"Option 1": "LAB – TBC2 – TBC3 – TBC1",
	"Option 2": "TBC2 – LAB – TBC1 – TBC3",
	"Option 3": "TBC3 – TBC1 – LAB – TBC2",
	"Option 4": "TBC1 – TBC3 – TBC2 – LAB",
}
order_to_option_dict = {v: k for k, v in option_to_order_dict.items()}

def create_cost_matrix():
	# add penalty
	cost_matrix = np.random.randint(n_beans // n_rotations, size = (75, n_rotations))
	if penalty == "beans":
		pass
	elif penalty == "linear":
		cost_matrix = np.random.randint(n_rotations, size = (75, n_rotations))
	return pad_matrix(cost_matrix)

def build_cost_matrix(preference_df):
	"""
	convert preferences to cost and apply optional penalties to skew costs
	"""
	# normalize to max number of beans
	cost_df = preference_df.drop(columns = ["studentID"]).astype(float)
	cost_df = cost_df.div(cost_df.sum(axis=1), axis=0) * n_beans
	cost_df = cost_df.fillna(0)

	# convert to costs
	cost_df = cost_df.sub(cost_df.sum(axis=1), axis=0) * -1
	cost_matrix = pd.DataFrame.to_numpy(cost_df)

	# add penalty
	if penalty == "beans":
		pass
	elif penalty == "linear":
		cost_matrix = cost_to_rank(cost_matrix)

	return pad_matrix(cost_matrix)

def cost_to_rank(cost_matrix):
	"""
	convert the number of beans to an optimal cost 
	"""
	for i in range(n_rotations):
		cost_matrix[np.where(cost_matrix == np.max(cost_matrix))] = i - n_rotations
	return cost_matrix * -1

def pad_matrix(cost):
	"""
	pad matrix to multiples of 4
	add one ghost row and ceil(75/4) - 1 duplicate columns
	add duplicate columns to ensure square optimization problem
	"""
	global phantom_students
	phantom_students = 0

	while np.shape(cost)[0] % n_rotations != 0:
		cost = np.vstack([cost, [n_beans, n_beans, n_beans, n_beans]])
		phantom_students += 1

	cost = np.tile(cost, (1, np.shape(cost)[0] // n_rotations))
	return cost


def rotation_calc(cost):
	"""
	run linear_sum_assignment on cost matrix
	optimal results are stored in col_index
	the "cost", or error in this case is the total deviation from everyone getting their first preference
	"""
	row_ind, col_ind = linear_sum_assignment(cost)
	err = cost[row_ind, col_ind].sum()

	rotation_index = col_ind % n_rotations # re-wraps the indicies to their human readable form
	rotations = [rotationdict.get(index) for index in rotation_index]
	# update_cost_matrix(row_ind, rotation_index)

	err = err - phantom_students * n_beans  # correction factor for phantom students

	return rotations, err


def analyze(optimal_order, optimal_order_err, performance = None):
	global error_df
	delta = optimal_order_err / n_student / n_beans
	
	print(
		f"Average error of assignment for first rotation:",
		delta,
	)
	matches = sum(
		preference_df.drop(columns=["studentID"]).idxmax(axis = 1)
		== performance["rotation_order"]
	)
	print(
		f"Percent of students who recieved their first choice rotation:",
		matches / n_student,
	)


def to_string(optimal_order, optimal_order_err):
	rotations = pd.DataFrame({"optimal_rotation": optimal_order})
	rotations.drop(
		rotations.tail(phantom_students).index, inplace = True
	)  # remove the phantom students

	performance = pd.concat([preference_df, rotations], axis=1)
	performance["rotation_order"] = performance["optimal_rotation"].map(
		option_to_order_dict
	)

	performance.to_csv("./out/rotations.csv", index = False)

	return performance


def update_cost_matrix(row_ind, col_ind):
	"""
	greatly increases the penalty of rematching to the same rotation
	this is a legacy function that is no longer necessary in the current interpretation of the problem
	"""
	for i in range(len(col_ind)):
		for mul in range(np.shape(cost)[0] // n_rotations):
			cost[i][(n_rotations * mul) + col_ind[i]] = 1000


def main():
	# load preference dataframe
	global preference_df
	preference_df = pd.read_csv(filename)
	preference_df = preference_df.set_axis(["studentID"] + list(option_to_order_dict.values()), axis = 1, copy = False)
	preference_df = preference_df.sample(frac = 1).reset_index(
		drop = True
	)  # shuffle the students so order no longer leads to preference
	studentIDs = preference_df["studentID"]

	global n_student
	n_student = len(studentIDs)

	cost = build_cost_matrix(preference_df)

	optimal_order, optimal_order_err = rotation_calc(cost)

	performance = to_string(optimal_order, optimal_order_err)
	print(performance)
	
	analyze(optimal_order, optimal_order_err, performance)

error_df = pd.DataFrame(columns = ['students', 'beans', 'error'])

main()