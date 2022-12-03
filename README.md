# Determining Rotation Matching Using Linear Sum Optimization
## Authors
1. <sup>a</sup>[Roshan Lodha](https://roshanlodha.github.io)
2. <sup>a</sup>[Tori Rogness]()
3. <sup>a</sup>[Alan Shen]()
4. <sup>a</sup>[Craig Nielson]()

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
To determine the performance of the rotation assignment, we defined a novel error metric, ε, as the `total_cost / n / b`. The range of ε was [0, 1], with a lower ε representing better performance. 

## Results
1. source from Alan and Tori
2. compare number of post-assignment swaps from previous years vs this year
3. real world this year (number of swaps, satisfaction, etc.)

## Discussion
1. summary/key findings
2. discussion of optimality and completeness
3. future endeavors including skew cost with cost modifying functions
4. discussion of game theory and optimal student strategy

## References