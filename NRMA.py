import pandas as pd
import numpy as np
# using optimized linear sums problem solver
from scipy.optimize import linear_sum_assignment
np.random.seed(44106)

preference_df = pd.read_csv("/work/preferences.csv")
studentIDs = preference_df['studentID']
n_student = len(studentIDs)
preference_df

n_beans = 24

cost_df = preference_df.drop(columns=['studentID']).astype(float)
cost_df = cost_df.div(cost_df.sum(axis = 1), axis = 0) * n_beans
cost_df = cost_df.fillna(0)
cost_df

cost_df = cost_df.sub(cost_df.sum(axis = 1), axis = 0) * -1
cost_matrix = pd.DataFrame.to_numpy(cost_df)
cost_matrix

# pad matrix to multiples of 4 :: add one ghost row and ceil(75/4) - 1 duplicate columns
cost = cost_matrix.copy()

phantom_students = 0
# add phantom rows of all equal until there are a multiple of 4 rows
while(np.shape(cost)[0] % 4 != 0):
	cost = np.vstack([cost, [n_beans, n_beans, n_beans, n_beans]])
	phantom_students += 1
	
# add duplicate columns to ensure square optimization problem 
cost = np.tile(cost, (1, np.shape(cost)[0] // 4))
print(np.shape(cost)) # should be a square matrix at this point

rotationdict = {
  0: "Option 1",
  1: "Option 2",
  2: "Option 3",
  3: "Option 4"
}

# run linear_sum_assignment on cost matrix --> optimal results are stored in col_index
def rotation_calc():
	row_ind, col_ind = linear_sum_assignment(cost) 
	err = cost[row_ind, col_ind].sum() # the "cost" in this case is the total deviation from everyone getting their first preference
	rotation_index = col_ind % 4 # re-wraps the indicies to their human readable form 
	rotations = [rotationdict.get(index) for index in rotation_index]
	update_cost_matrix(row_ind, rotation_index)
	return rotations, err

# greatly increases the penalty of rematching to the same rotation
def update_cost_matrix(row_ind, col_ind):
	for i in range(len(col_ind)):
		for mul in range(np.shape(cost)[0]//4):
			cost[i][(4 * mul) + col_ind[i]] = 1000

optimal_order, optimal_order_err = rotation_calc()
optimal_order_err = optimal_order_err - phantom_students * n_beans # correction factor for phantom students


import pandas as pd

df_dict = {
    "optimal_rotation": optimal_order, 
    }

rotations = pd.DataFrame(df_dict)
rotations.drop(rotations.tail(phantom_students).index, inplace = True) # remove the phantom students

option_to_order_dict = {
    "Option 1": "LAB – TBC2 – TBC3 – TBC1",
    "Option 2": "TBC2 – LAB – TBC1 – TBC3",
    "Option 3": "TBC3 – TBC1 – LAB – TBC2",
    "Option 4": "TBC1 – TBC3 – TBC2 – LAB"
}

performance = pd.concat([preference_df, rotations], axis=1)
performance['rotation_order'] = performance['optimal_rotation'].map(option_to_order_dict)

performance

print(f'Average error of assignment for first rotation:', optimal_order_err/n_student/n_beans)

performance.drop(columns=['studentID', 'optimal_rotation', 'rotation_order']).idxmax(axis=1) == performance['optimal_rotation']