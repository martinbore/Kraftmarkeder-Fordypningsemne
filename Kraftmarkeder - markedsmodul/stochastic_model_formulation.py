# The deterministic equivalent model formulation for the given problem:
from pyomo.environ import *
import random
import pandas as pd
import matplotlib.pyplot as plt


# Sets
T = list(range(1,49))      # 1..48
T1 = list(range(1,25))     # 1..24
T2 = list(range(25,49))    # 25..48
S = [0,1,2,3,4]            # inflow scenarios


# Parameters
p = {t: 50+t for t in T}

# Inflows
I = {t: 50 for t in T1}   # deterministic inflow day 1
I_s = {}

for s in S:
    for t in T2:
        I_s[(t,s)] = 10*s
        print(I_s[(t,s)])



# Scenario probabilities
pi = {s: 1.0/len(S) for s in S}

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
model.T1 = Set(initialize=T1)
model.T2 = Set(initialize=T2)
model.S  = Set(initialize=S)

# Parameters
model.p  = Param(model.T1|model.T2, initialize=p)
model.I  = Param(model.T1, initialize=I)
model.I_s = Param(model.T2, model.S, initialize=I_s)
model.pi = Param(model.S, initialize=pi)
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

model.x_s = Var(model.T2, model.S, domain=NonNegativeReals, bounds=(0,Pmax))
model.Q_s = Var(model.T2, model.S, domain=NonNegativeReals, bounds=(0,Qmax))
model.V_s = Var(model.T2, model.S, domain=NonNegativeReals, bounds=(0,Vmax))
model.spill = Var(model.T2, model.S, domain=NonNegativeReals, bounds=(0,Vmax))


# Constraints
# Reservoir balance day 1
def reservoir_day1_rule(m,t):
    if t == 1:
        return m.V[t] == m.V0 + m.M_conv*(m.I[t] - m.Q[t])
    return m.V[t] == m.V[t-1] + m.M_conv*(m.I[t] - m.Q[t])
model.res_day1 = Constraint(model.T1, rule=reservoir_day1_rule)

# Reservoir balance day 2
def reservoir_day2_rule(m,t,s):
    if t == 25:
        return m.V_s[t,s] == m.V[24] + m.M_conv*(m.I_s[t,s] - m.Q_s[t,s]) - m.spill[t,s]
    return m.V_s[t,s] == m.V_s[t-1,s] + m.M_conv*(m.I_s[t,s] - m.Q_s[t,s]) - m.spill[t,s]
model.res_day2 = Constraint(model.T2, model.S, rule=reservoir_day2_rule)

# Link production and discharge (day 1)
def prod_day1_rule(m,t):
    return m.x[t] == m.E_conv*m.M_conv*m.Q[t]*1000
model.prod_day1 = Constraint(model.T1, rule=prod_day1_rule)

# Link production and discharge (day 2)
def prod_day2_rule(m,t,s):
    return m.x_s[t,s] == m.E_conv*m.M_conv*m.Q_s[t,s]*1000
model.prod_day2 = Constraint(model.T2, model.S, rule=prod_day2_rule)


# Objective function
def obj_rule(m):
    term1 = sum(m.p[t]*m.x[t] for t in m.T1)
    term2 = sum(m.pi[s]*(sum(m.p[t]*m.x_s[t,s] for t in m.T2) + m.WV_end*m.V_s[48,s]) for s in m.S)
    return term1 + term2
model.Obj = Objective(rule=obj_rule, sense=maximize)

# Solving the model
if __name__ == "__main__":
    # solver = SolverFactory("glpk")
    solver = SolverFactory("gurobi")
    result = solver.solve(model, tee=True)
    print("\nObjective value:", value(model.Obj), "EUR")
    print("Reservoir at t=24:", value(model.V[24]), "Mm3")
    print("Reservoir at t=48 (scenario 1):", value(model.V_s[48,1]), "Mm3")
    for t in model.T1:
        print(f"Hour {t}: Production = {value(model.x[t]):.2f} MW, Discharge = {value(model.Q[t]):.2f} m3/s, Volume = {value(model.V[t]):.2f} Mm3")
    for s in model.S:
        print(f"\nScenario {s+1}:")
        for t in model.T2:
            print(f"Hour {t}: Production = {value(model.x_s[t,s]):.2f} MW, Discharge = {value(model.Q_s[t,s]):.2f} m3/s, Volume = {value(model.V_s[t,s]):.2f} Mm3, Spillage = {value(model.spill[t,s]):.2f} Mm3")


# Plotting the results for production, reservoir volume and discharge for the two day schedule
plt.figure(figsize=(12, 6))
t_1 = T1
production_1 = [value(model.x[t]) for t in T1]
plt.plot(t_1, production_1, label='Day 1 Production', color='blue')
t_2 = T2
for s in S:
    production_2 = [value(model.x_s[t,s]) for t in T2]
    plt.plot(t_2, production_2, label=f'Day 2 Production Scenario {s+1}')
plt.xlabel('Hour')
plt.ylabel('Production (MW)')
plt.title('Production Schedule Over 48 Hours')
plt.grid(True)
plt.xticks(T)
plt.legend()
# plt.show()
plt.savefig('production_schedule.png')

plt.figure(figsize=(12, 6))
t_1 = T1
reservoir_volume_1 = [value(model.V[t]) for t in T1]
plt.plot(t_1, reservoir_volume_1, label='Day 1 Reservoir Volume', color='orange')
t_2 = T2
for s in S:
    reservoir_volume_2 = [value(model.V_s[t,s]) for t in T2]
    plt.plot(t_2, reservoir_volume_2, label=f'Day 2 Reservoir Volume Scenario {s+1}')
plt.xlabel('Hour')
plt.ylabel('Reservoir Volume (Mm3)')
plt.title('Reservoir Volume Over 48 Hours')
plt.grid(True)
plt.xticks(T)
plt.legend()
# plt.show()
plt.savefig('reservoir_volume.png')
