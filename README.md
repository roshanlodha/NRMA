# Determining Rotation Matching Using Linear Sum Optimization
## Authors
1. <sup>a</sup>[Roshan Lodha](https://roshanlodha.github.io)
2. <sup>a</sup>Neil Mehta, <sup>a</sup>Craig Nielsen

<sup>a</sup>Cleveland Clinic Lerner College of Medicine 
## Introduction
Third-year medical students complete a series of core rotations in internal medicine, surgery, paediatrics, obstetrics, gynecology, neurology, psychiatry, and family medicine. Elective rotations often require a prerequisite core rotation; for example, to enroll in the orthopedics elective, students must first complete the core surgery rotation. Thus, students tend to have a preference for the order in which they are assigned to these rotations.

{tori can you help with the introduction? it would be helpful to pull statistics from online about medical students and specalities and such}

Currently, rotation matching is done psuedo-stochastically, posing a huge time cost. Unequal student preferences in rotation order lead to challenges in finding an optimal assignment for all students, and simply using rank-based preference matching assigns the problem of cost of an unfavorable preference away from the student. Here we propose a student-centered rotation assignment algorithm that finds the optimal student-order pairing. Notably, we allow students to choose the cost of an unfavorable assignment on an individual basis while ensuring an equal amount of students are assigned to each order.

## Methods

### Problem Formulation and Encoding
We reframed the problem of optimal rotation order as an minimum-cost assignment problem. Each student has the option of `k` rotation orders {add a table 1 with the order, abreviation, and the full meaning} which they assigned a cost to. These costs were used to formulate an `n` x `k` tall matrix, with `n` students each with `k = 4` rotations.

#### Determining Costs 
Students were given `b` "beans" and were asked to divide assign these beans however they would like to the rotation orders. Null submissions were assigned `b / k` beans to each rotation. All responses were scaled such that the sum of beans was exactly `b`. Each rotation order's assigned beans was then converted to a cost by subtracting it from `b`. For example, if a rotation was assigned `c` beans, its associated cost would be `b - c`. Generally, the optimal number of beans is 0 in moduli space `b`. Hyperparameter optimization is used to determine the optimal number of beans for a given application.

### Algorithm Design

#### Matrix Padding
Linear sum optimization requires a wide or square matrix. Thus, we add phantom students with no rotation order preference until the number of rows is 0 in moduli space `k`. Subsequently, we tile the matrix to a width of `ceiling(n / k)` resulting in a `ceiling(n / k) * k` by `ceiling(n / k) * k` square matrix. The row order was then randomly shuffled to ensure that submission time was not a factor in determining rotation order preference. 

#### Linear Sum Optimization
The optimal rotation order was calculated by feeding the resulting square cost matrix into a python based linear sum optimizer. The resulting solution was both complete and optimal in that each student was assigned to a single rotation orer and that no single swap between two students would benefit both.

### Error Testing
To determine the performance of the rotation assignment, we defined a novel error metric, δ, as the `total_cost / n / b, {δ ∈ R | [0, 1]}`. 

## Results


### The optimal number of beans is highly variable.
An optimal number of beans was selected using hyperparameter optimization. For ease of student use, the minimum number of beans was chosen to be `k!`, as it allows for integer divisions between rotation orders. Testing across a wide range of beans revealed that a minimum number of beans minimized error (Figure 1). The cost matrix was sampled randomly and uniformly.
![Figure 1. Error versus number of beans](./plots/beans_error.png)
*Error as a function of number of beans.*
Analysis of a sample set of real world data showed a skew towards certain rotation orders. Further testing must be done to determine how the number of beans effect the overall error under various sampling distributions. We hypothesize that in real world deployment, increasing the number of beans would decrease the error due to sampling skew and a maximal difference between costs for a given student.

### The error reduces as the number of students increases. 
As the number of students increases, the total delta error decreased exponentially (Figure 2). In other words, the error was roughly constant despite increasing the number of students, suggesting better performance as the number of students increases. 
![Figure 2. Error versus number of students](./plots/students_error.png)

### Deployment and Student Satisfaction
* real world this year (number of swaps, satisfaction, etc.)
* compare number of post-assignment swaps from previous years vs this year

## Discussion
1. summary/key findings
2. discussion of optimality and completeness
3. future endeavors including skew cost with cost modifying functions
4. discussion of game theory and optimal student strategy

## References
