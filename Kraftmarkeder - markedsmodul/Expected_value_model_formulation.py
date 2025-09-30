# Formulating the problem just using expected values:
from pyomo.environ import *
import random


# Sets
T = list(range(1,49))      # 1..48
T1 = list(range(1,25))     # 1..24
T2 = list(range(25,49))    # 25..48
S = [0,1,2,3,4]            # inflow scenarios


# Parameters
p = {t: 50+t for t in T}

# Inflows
I = {t: 50 for t in T1}   # deterministic inflow day 1
E_I = {} # Expected inflow

for t in T2:
    E_I[(t)] = 0
    for s in S:
        E_I[(t)]+=(1/len(S))*10*s
        


# Constants
V0 = 3.0
Vmax = 4.5
Pmax = 86.5
Qmax = 100.0
M_conv = 3.6/1000     # Mm3 per (m3/s) per hour
E_conv = 0.657        # kWh per m3
WV_end = 52600.0      # EUR per Mm3

model = ConcreteModel()

# Sets
model.T = Set(initialize = T)
model.T1 = Set(initialize=T1)
model.T2 = Set(initialize=T2)
model.S  = Set(initialize=S)

# Parameters
model.p  = Param(model.T1|model.T2, initialize=p)
model.I  = Param(model.T1|model.T2, initialize=I)
model.E_I = Param(model.T2, initialize=E_I)
model.V0 = Param(initialize=V0)
model.Vmax = Param(initialize=Vmax)
model.Pmax = Param(initialize=Pmax)
model.Qmax = Param(initialize=Qmax)
model.M_conv = Param(initialize=M_conv)
model.E_conv = Param(initialize=E_conv)
model.WV_end = Param(initialize=WV_end)


# Decision variables
model.x  = Var(model.T, domain=NonNegativeReals, bounds=(0,Pmax))
model.Q  = Var(model.T, domain=NonNegativeReals, bounds=(0,Qmax))
model.V  = Var(model.T, domain=NonNegativeReals, bounds=(0,Vmax))


# Objective function:
def objective_func(m):
    return sum(m.p[t]*m.x[t] for t in m.T1) + sum(m.p[t]*m.x[t] for t in m.T2) + m.WV_end*m.V[48]

# Constraints:
def reservoir_day1_rule(m,t):
    if t == 1:
        return m.V[t] == m.V0 + m.M_conv*(m.I[t] - m.Q[t])
    return m.V[t] == m.V[t-1] + m.M_conv*(m.I[t] - m.Q[t])
model.res_day1 = Constraint(model.T1, rule=reservoir_day1_rule)

def reservoir_day2_rule(m,t):
    if t == 25:
        return m.V[t] == m.V[24] + m.M_conv*(m.E_I[t] - m.Q[t])
    return m.V[t] == m.V[t-1] + m.M_conv*(m.E_I[t] - m.Q[t])
model.res_day2 = Constraint(model.T2, rule=reservoir_day2_rule) 

def prod_constraint(m,t):
    return m.x[t] == m.E_conv*m.M_conv*m.Q[t]*1000
model.prod_con = Constraint(model.T, rule = prod_constraint)

model.Obj = Objective(rule=objective_func, sense=maximize)
solver = SolverFactory("glpk")
result = solver.solve(model, tee=False)
print("Objective value:", value(model.Obj), "EUR")
print("Reservoir at t=24:", value(model.V[24]), "Mm3")
print("Reservoir at t=48:", value(model.V[48]), "Mm3")
for t in model.T:
    print(f"Hour {t}: Production = {value(model.x[t]):.2f} MW, Discharge = {value(model.Q[t]):.2f} m3/s, Volume = {value(model.V[t]):.2f} Mm3")


