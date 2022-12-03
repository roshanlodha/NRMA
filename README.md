# Automating Clerkship Matching Using Linear Sum Optimization
## Introduction
Third-year medical students complete a series of core rotations covering internal medicine, surgery, paediatrics, obstetrics, gynaecology, neurology, psychiatry, and family medicine. Elective rotations often require a prerequisite core rotation; for example, to enroll in the orthopaedics elective, students must first complete the core surgery elective. Thus, students tend to have a preference for the order in which they are assigned to these rotations. 
[tori can you help with the introduction? it would be helpful to pull statistics from online about medical students and specalities and such]
Currently, rotation matching is done psuedo-stochastically. Unequal student preferences in clerkship order lead to challenges in finding an optimal assignment for all students, and simply using rank-based preference matching [assigns the problem of cost of an unfavorable preference away from the student]. Here we propose a student-centered clerkship assignment algorithm that finds the optimal student-order pairing. Notably, we allow students to choose the cost of an unfavorable assignment on an individual basis while ensuring an equal amount of students are assigned to each order.
## Methods
1. reframing question as a maximum cost problem
2. sourcing optimal costs and "beans" method 
3. matrix setup + linear sum optmization (scipy)
4. custom error metrics
### Problem Formulation and Encoding
We reframed the problem of optimal clerkship order as an minimum-cost assignment problem. Each student has the option of four rotation orders [add a table 1 with the order, abreviation, and the full meaning] which they assigned a cost to (see determining costs). These costs were used to formulate an `n` x `k` tall matrix, with `n` students each with `k = 4` rotations.
### Determining Costs 
Students were given `b` "beans" and were asked to divide assign these beans however they would like to the clerkship orders. Null submissions were assigned `b / k` beans to each rotation. All responses were scaled such that the sum of beans was exactly `b`. Each clerkship order's assigned beans was then converted to a cost by subtracting it from `b`. For example, if a clerkship was assigned c beans, its associated cost would be `b-c`.  In practice, 24 beans were chosen due to its factorization into 1, 2, 3, and 4 and due to emperical testing.
### Algorithm Design
#### Matrix Padding
Linear sum optimization requires a wide or square matrix. Thus, we add phantom students with no clerkship order preference until the number of rows is 0 in moduli space `k`. Subsequently, we tile the matrix to a width of `ceiling(n / k)` resulting in a `ceiling(n / k) * k` by `ceiling(n / k) * k` square matrix.
#### Linear Sum Optimization
The optimal clerkship order was calculated by feeding the resulting square cost matrix into a linear sum optimizer. The resulting solution was both complete and optimal in that each student was assigned to a single clerkship orer and that no single swap between two students would benefit both.
### Error Testing
To determine the performance of the clerkship assignment, we defined a novel error metric, ε, as the `total_cost / n / b`. The range of ε was [0, 1], with a lower ε representing better performance. 
## Results
source from Alan and Tori
compare number of post-assignment swaps from previous years vs this year
## Discussion
1. summary/key findings
2. discussion of optimality and completeness
3. future endeavors including skew cost with cost modifying functions
4. discussion of game theory and optimal student strategy
## References