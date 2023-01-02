import pandas as pd
import numpy as np
import sys

# using optimized elinear sums problem solver
from scipy.optimize import linear_sum_assignment

# used for optimal number of beans
from scipy.special import factorial

# np.random.seed(44106)

# mutable global variables
global preference_df
global studentIDs
global phantom_students
global error_df

simulate = True
penalty = sys.argv[1]
n_beans = 24
n_student = 75
n_rotations = 4
stat = 1 # increase to decrease the measured statistical variance

# definitions and converters
rotationdict = {0: "Option 1", 1: "Option 2", 2: "Option 3", 3: "Option 4"}
option_to_order_dict = {
	"Option 1": "LAB – TBC2 – TBC3 – TBC1",
	"Option 2": "TBC2 – LAB – TBC1 – TBC3",
	"Option 3": "TBC3 – TBC1 – LAB – TBC2",
	"Option 4": "TBC1 – TBC3 – TBC2 – LAB",
}


def create_cost_matrix():
	# add penalty
	cost_matrix = np.random.randint(n_beans // n_rotations, size=(n_student, n_rotations))
	if penalty == "beans":
		pass
	elif penalty == "linear":
		cost_matrix = np.random.randint(n_rotations, size=(n_student, n_rotations))
	return pad_matrix(cost_matrix)


def build_cost_matrix(preference_df):
	"""
	convert preferences to cost and apply optional penalties to skew costs
	"""
	# normalize to max number of beans
	cost_df = preference_df.drop(columns=["studentID"]).astype(float)
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
	else:
		pass

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
	1. pad matrix to multiples of n_rotations
	2. add one ghost row and ceil(n_students/n_rotations) - 1 duplicate columns
	3. add duplicate columns to ensure square optimization problem
	"""
	global phantom_students
	phantom_students = 0

	while np.shape(cost)[0] % n_rotations != 0:
		cost = np.vstack([cost, np.full(n_rotations, n_beans)])
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

	rotation_index = (
		col_ind % n_rotations
	)  # re-wraps the indicies to their human readable form
	rotations = [rotationdict.get(index) for index in rotation_index]
	# update_cost_matrix(row_ind, rotation_index)

	err = err - phantom_students * n_beans  # correction factor for phantom students

	return rotations, err


def analyze(optimal_order, optimal_order_err):
	global error_df
	delta = optimal_order_err / n_student / n_beans

	temp_df = pd.DataFrame(
		data=[[n_student, n_beans, delta]],
		# temp_df = pd.DataFrame(data = [[n_student, n_beans, optimal_order_err]],
		columns=["students", "beans", "error"],
	)
	error_df = pd.concat([error_df, temp_df])


def update_cost_matrix(row_ind, col_ind):
	"""
	greatly increases the penalty of rematching to the same rotation
	this is a legacy function that is no longer necessary in the current interpretation of the problem
	"""
	for i in range(len(col_ind)):
		for mul in range(np.shape(cost)[0] // n_rotations):
			cost[i][(n_rotations * mul) + col_ind[i]] = 1000


def main():
	cost = create_cost_matrix()

	optimal_order, optimal_order_err = rotation_calc(cost)

	analyze(optimal_order, optimal_order_err)


def plot_students():
	import matplotlib.pyplot as plt
	import seaborn as sns

	sns.lineplot(data=error_df, x="students", y="error", errorbar="sd").set(
		title="Number of Students vs Error"
	)
	figname = "./plots/students_error_" + penalty + ".png"
	plt.savefig(figname)
	plt.clf()


def plot_beans():
	import matplotlib.pyplot as plt
	import seaborn as sns

	sns.lineplot(data=error_df, x="beans", y="error", errorbar="sd").set(
		title="Number of Beans vs Error"
	)
	figname = "./plots/beans_error_" + penalty + ".png"
	plt.savefig(figname)
	plt.clf()


error_df = pd.DataFrame(columns=["students", "beans", "error"])
for i in range(2 * n_rotations - 1, 301):
	n_student = i
	for j in range(stat):
		main()
plot_students()

error_df = pd.DataFrame(columns=["students", "beans", "error"])
for i in range(factorial(n_rotations, exact=True), 96):
	n_beans = i
	for j in range(stat):
		main()
plot_beans()
