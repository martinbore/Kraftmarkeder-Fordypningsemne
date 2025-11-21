# Solving the problem using SDP - Stochastic Dynamic Programming
# First stage decision - Decide how much to produce for the first 24 hours
# Second stage decision - Decide how much to produce for hour 25-48. 
from doctest import master
from pyomo.environ import *
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import time
# Sets
T = list(range(1,49))      # 1..48
T1 = list(range(1,25))     # 1..24
T2 = list(range(25,49))    # 25..48
S = [0,1,2,3,4]            # inflow scenarios
# S = [1]                    # inflow scenario

# Parameters
p = {t: 50+t for t in T}

# Inflows
I = {t: 50 for t in T1}   # deterministic inflow day 1
I_s = {}
for s in S:
    for t in T2:
        I_s[(t,s)] = 10*s


# Scenario probabilities
pi = 1/len(S)


# Constants:
V0 = 3.0
Vmax = 4.5
Pmax = 86.5
Qmax = 100.0
M_conv = 3.6/1000    
E_conv = 0.657       
WV_end = 52600.0 


# Discretizing the values for the reservoiar storage at the end of the first period. 
# Using 10 discrete values:
# Min reservoiar: 3, max reservoiar: 4.5
V_24_list = list(np.linspace(3, 4.5, 10))

# Solving using 3 discrete values:
# Min reservoiar: 3, max reservoiar: 4.5
# V_24_list = list(np.linspace(3,4.5, 3))

# Creating the sub-problem to obtain the second stage variables and corresponding dual values:
def create_sub(V_24, s):
    sub = ConcreteModel()
    sub.T2 = Set(initialize=T2)
    # Spillage:
    sub.S_s = Var(sub.T2, domain=NonNegativeReals)

    sub.p = Param(sub.T2, initialize={t: p[t] for t in T2})
    sub.I_s = Param(sub.T2, initialize={t: I_s[t,s] for t in T2})
    sub.Pmax = Param(initialize=Pmax)
    sub.Qmax = Param(initialize=Qmax)
    sub.M_conv = Param(initialize=M_conv)
    sub.E_conv = Param(initialize=E_conv)
    sub.WV_end = Param(initialize=WV_end)
    

    # Second stage variables
    sub.x_s = Var(sub.T2, domain=NonNegativeReals, bounds=(0,Pmax))
    sub.Q_s = Var(sub.T2, domain=NonNegativeReals, bounds=(0,Qmax))
    sub.V_s = Var(sub.T2, domain=NonNegativeReals, bounds=(0,Vmax))

    # Constraints
    def reservoir_day2_rule(m,t):
        if t == 25:
            return m.V_s[t] == V_24 + m.M_conv*(m.I_s[t] - m.Q_s[t]- m.S_s[t])
        return m.V_s[t] == m.V_s[t-1] + m.M_conv*(m.I_s[t] - m.Q_s[t]- m.S_s[t])
    sub.res_day2 = Constraint(sub.T2, rule=reservoir_day2_rule)

    def prod_day2_rule(m,t):
        return m.x_s[t] == m.E_conv*m.M_conv*m.Q_s[t]*1000
    sub.prod_day2 = Constraint(sub.T2, rule=prod_day2_rule)

    def Obje_2(m):
        return (sum(m.p[t]*m.x_s[t] for t in m.T2) + m.WV_end*m.V_s[48])

    # Objective function
    sub.obj = Objective(rule=Obje_2, sense=maximize)

    # prepare dual suffix once for this submodel
    sub.dual = Suffix(direction=Suffix.IMPORT)

    return sub


# In the master we solve for a given dual value and update the first stage variables:
def create_master():
    master = ConcreteModel()
    master.T1 = Set(initialize=T1)

    master.S = Var(master.T1, domain=NonNegativeReals)
    master.p = Param(master.T1, initialize={t: p[t] for t in T1})
    master.I = Param(master.T1, initialize=I)
    master.Pmax = Param(initialize=Pmax)
    master.Qmax = Param(initialize=Qmax)
    master.M_conv = Param(initialize=M_conv)
    master.E_conv = Param(initialize=E_conv)
    master.V0 = Param(initialize=V0)
    master.Vmax = Param(initialize=Vmax)

    # First stage variables
    master.x = Var(master.T1, domain=NonNegativeReals, bounds=(0,Pmax))
    master.Q = Var(master.T1, domain=NonNegativeReals, bounds=(0,Qmax))
    master.V = Var(master.T1, domain=NonNegativeReals, bounds=(0,Vmax))

    # Defining alfa, with the upper bound corresponding to the same as the one in Benders:
    alpha_upper = 1e6
    master.alfa = Var(bounds=(None, alpha_upper))

    # Constraints
    def reservoir_day1_rule(m,t):
        if t == 1:
            return m.V[t] == m.V0 + m.M_conv*(m.I[t] - m.Q[t])- m.S[t]
        return m.V[t] == m.V[t-1] + m.M_conv*(m.I[t] - m.Q[t])- m.S[t]
    master.res_day1 = Constraint(master.T1, rule=reservoir_day1_rule)

    def prod_day1_rule(m,t):
        return m.x[t] == m.E_conv*m.M_conv*m.Q[t]*1000
    master.prod_day1 = Constraint(master.T1, rule=prod_day1_rule)

    def Obje_1(m):
        return sum(m.p[t]*m.x[t] for t in m.T1) + m.alfa

    # Objective function
    master.obj = Objective(rule=Obje_1, sense=maximize)

    # Dual suffix
    master.dual = Suffix(direction=Suffix.IMPORT)

    return master


# After solving the sub-problem, we can solve the master problem:
second_stage_solutions = {}
def SDP_algo():
    # Creating the master problem:
    master = create_master()
    cuts = []
    solver = SolverFactory('glpk')
    for i,val in enumerate(V_24_list):
        exp_sub_obj = 0
        cut_expr = 0
        exp_dual = 0
        for s in S:
            sub = create_sub(val, s)
            res_sub = solver.solve(sub, tee=False)
            sub.solutions.load_from(res_sub)
            sub_obj = value(sub.obj)
            exp_sub_obj += pi*sub_obj
            cut_expr += pi*sub.dual[sub.res_day2[25]] * (master.V[24] - val)
            exp_dual += pi*sub.dual[sub.res_day2[25]]
            print(res_sub.solver.termination_condition)
            
        # After aggregating based on each scenario, we can append the cut to the master problem:
        phi_k = exp_sub_obj
        expr = master.alfa <= phi_k + cut_expr
        cname = f"cut_{i}"
        setattr(master, cname, Constraint(expr=expr)) # Defines and appends cut to the master problem
        cuts.append(cname) # Appends cut to the list of cuts
        
    solver.solve(master, tee=False)
    print("The objective function of master problem:", value(master.obj))

start_time = time.time()
SDP_algo()
end_time = time.time()

print("Time: ", end_time - start_time, "seconds")




