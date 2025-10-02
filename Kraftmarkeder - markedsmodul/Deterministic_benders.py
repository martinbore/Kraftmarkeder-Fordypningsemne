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

model = ConcreteModel()

# Sets
model.T1 = Set(initialize=T1)
model.T2 = Set(initialize=T2)


# Parameters: 
model.p  = Param(model.T1|model.T2, initialize=p)
model.I  = Param(model.T1, initialize=I)
model.I_2 = Param(model.T2, initialize=I)
model.V0 = Param(initialize=V0)
model.Vmax = Param(initialize=Vmax)
model.Pmax = Param(initialize=Pmax)
model.Qmax = Param(initialize=Qmax)
model.M_conv = Param(initialize=M_conv)
model.E_conv = Param(initialize=E_conv)
model.WV_end = Param(initialize=WV_end)


# Decision variables
model.x  = Var(model.T1, domain=NonNegativeReals, bounds=(0,Pmax))
model.Q  = Var(model.T1, domain=NonNegativeReals, bounds=(0,Qmax))
model.V  = Var(model.T1, domain=NonNegativeReals, bounds=(0,Vmax))

model.x_2 = Var(model.T2, domain=NonNegativeReals, bounds=(0,Pmax))
model.Q_2 = Var(model.T2, domain=NonNegativeReals, bounds=(0,Qmax))
model.V_2 = Var(model.T2, domain=NonNegativeReals, bounds=(0,Vmax))


# Constraints
def reservoir_day1_rule(m,t):
    if t == 1:
        return m.V[t] == m.V0 + m.M_conv*(m.I[t] - m.Q[t])
    return m.V[t] == m.V[t-1] + m.M_conv*(m.I[t] - m.Q[t])
model.res_day1 = Constraint(model.T1, rule=reservoir_day1_rule)

def reservoir_day2_rule(m,t):
    if t == 25:
        return m.V_s[t] == m.V[24] + m.M_conv*(m.I_s[t] - m.Q_s[t])
    return m.V_s[t] == m.V_s[t-1] + m.M_conv*(m.I_s[t] - m.Q_s[t])
model.res_day2 = Constraint(model.T2, rule=reservoir_day2_rule) 

def prod_day1_rule(m,t):
    return m.x[t] == m.E_conv*m.M_conv*m.Q[t]*1000
model.prod_day1 = Constraint(model.T1, rule=prod_day1_rule)

def prod_day2_rule(m,t):
    return m.x_s[t] == m.E_conv*m.M_conv*m.Q_s[t]*1000
model.prod_day2 = Constraint(model.T2, rule=prod_day2_rule)

def obj_rule(m):
    term1 = sum(m.p[t]*m.x[t] for t in m.T1)
    term2 = sum(m.p[t]*m.x_s[t] for t in m.T2) + m.WV_end*m.V_s[48]


