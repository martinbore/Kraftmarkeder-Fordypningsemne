# Creating an Benders implementation for the deterministic inflow scenario 3:
from pyomo.environ import *
import pandas as pd
import matplotlib.pyplot as plt

# Creating an Benders implementation for the deterministic inflow scenario 3:
# Sets
T = list(range(1,49))      # 1..48
T1 = list(range(1,25))     # 1..24
T2 = list(range(25,49))    # 25..48

# Parameters
p = {t: 50+t for t in T}

# Inflows
I = {t: 50 for t in T1}   # deterministic inflow day 1
I_2 = {t: 20 for t in T2} # deterministic inflow for day 3 based on scneario 3

# Constants:
V0 = 3.0
Vmax = 4.5
Pmax = 86.5
Qmax = 100.0
M_conv = 3.6/1000    
E_conv = 0.657       
WV_end = 52600.0 



# Creating master and sub:
def create_master():
    master = ConcreteModel()
    master.T1 = Set(initialize=T1)
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

    # Benders cut variable
    master.alfa = Var(domain=Reals, initialize = 0)

    # Constraints
    def reservoir_day1_rule(m,t):
        if t == 1:
            return m.V[t] == m.V0 + m.M_conv*(m.I[t] - m.Q[t])
        return m.V[t] == m.V[t-1] + m.M_conv*(m.I[t] - m.Q[t])
    master.res_day1 = Constraint(master.T1, rule=reservoir_day1_rule)

    def prod_day1_rule(m,t):
        return m.x[t] == m.E_conv*m.M_conv*m.Q[t]*1000
    master.prod_day1 = Constraint(master.T1, rule=prod_day1_rule)

    def Obje_1(m):
        return sum(m.p[t]*m.x[t] for t in m.T1) + m.alfa

    # Objective function
    master.obj = Objective(rule=Obje_1, sense=maximize)

    return master

def create_sub(V_24):
    sub = ConcreteModel()
    sub.T2 = Set(initialize=T2)
    sub.p = Param(sub.T2, initialize={t: p[t] for t in T2})
    sub.I_2 = Param(sub.T2, initialize={t: I_2[t] for t in T2})
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
            return m.V_s[t] == V_24 + m.M_conv*(m.I_2[t] - m.Q_s[t])
        return m.V_s[t] == m.V_s[t-1] + m.M_conv*(m.I_2[t] - m.Q_s[t])
    sub.res_day2 = Constraint(sub.T2, rule=reservoir_day2_rule) 

    def prod_day2_rule(m,t):
        return m.x_s[t] == m.E_conv*m.M_conv*m.Q_s[t]*1000
    sub.prod_day2 = Constraint(sub.T2, rule=prod_day2_rule)

    def Obje_2(m):
        return sum(m.p[t]*m.x_s[t] for t in m.T2) + m.WV_end*m.V_s[48]

    # Objective function
    sub.obj = Objective(rule=Obje_2, sense=maximize)

    return sub


# Defining Benders:
# Master problem: First stage variabel with the given constraints. 
# The subproblem: The second stage variables with the given constraints. 
def Benders_algo():
    master = create_master()
    UB = 1e5
    LB = -1e5
    tol = 1e-1
    it = 0
    cuts = []
    while abs(UB-LB)>tol:
        it += 1
        opt = SolverFactory('glpk')
        # Solve master and ensure solution is loaded into the model
        # Prevent master from being unbounded at the very first iteration: fix alfa=0
        if it == 1:
            master.alfa.fix(0)

        # Solving the master problem and extracting the value to send to sub_problem:
        res_master = opt.solve(master, tee=False)
        master.dual = Suffix(direction=Suffix.IMPORT)
        V_24 = value(master.V[24])
    

        # Create and solve subproblem for this V_24
        sub = create_sub(V_24)
        sub.dual = Suffix(direction=Suffix.IMPORT)
        res_sub = opt.solve(sub, tee=False)
    

        # Compute bounds: LB is master objective (with current alfa), UB is first-stage profit + true second-stage objective
        LB = value(master.obj)
        first_stage_profit = sum(value(master.p[t]) * value(master.x[t]) for t in master.T1)
        second_stage_profit = value(sub.obj)
        UB = first_stage_profit + second_stage_profit
        print(f'LB: {LB}, UB: {UB}, Gap: {abs(UB-LB)}')

        # Get dual of reservoir constraint at time 25 (connecting variable)
        dual_lambda = sub.dual[sub.res_day2[25]]

        # Add Benders optimality cut: alfa <= phi_k + pi_k*(V24 - V24_k)
        phi_k = value(sub.obj)
        expr = master.alfa <= phi_k + dual_lambda * (master.V[24] - V_24)
        cname = f"cut_{it}"
        setattr(master, cname, Constraint(expr=expr)) # Appends the cut to master
        cuts.append(cname)

    print(f"Covergence after {it} iterations")
    print(f"Objective function value = {LB:.4f}")

Benders_algo()
