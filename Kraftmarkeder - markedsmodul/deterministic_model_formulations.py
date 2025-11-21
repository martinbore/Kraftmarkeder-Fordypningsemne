from pyomo.environ import *
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


# Model
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



# Running a loop for each scenario:
for s in S:
    print(f"Solving for scenario {s}:")
    model_s = ConcreteModel()

    # Sets
    model_s.T1 = Set(initialize=T1)
    model_s.T2 = Set(initialize=T2)

    # Parameters
    model_s.p  = Param(model_s.T1|model_s.T2, initialize=p)
    model_s.I  = Param(model_s.T1, initialize=I)
    model_s.I_s = Param(model_s.T2, initialize={t: I_s[(t,s)] for t in T2})
    model_s.V0 = Param(initialize=V0)
    model_s.Vmax = Param(initialize=Vmax)
    model_s.Pmax = Param(initialize=Pmax)
    model_s.Qmax = Param(initialize=Qmax)
    model_s.M_conv = Param(initialize=M_conv)
    model_s.E_conv = Param(initialize=E_conv)
    model_s.WV_end = Param(initialize=WV_end)

    # Decision variables
    model_s.x  = Var(model_s.T1, domain=NonNegativeReals, bounds=(0,Pmax))
    model_s.Q  = Var(model_s.T1, domain=NonNegativeReals, bounds=(0,Qmax))
    model_s.V  = Var(model_s.T1, domain=NonNegativeReals, bounds=(0,Vmax))

    model_s.x_s = Var(model_s.T2, domain=NonNegativeReals, bounds=(0,Pmax))
    model_s.Q_s = Var(model_s.T2, domain=NonNegativeReals, bounds=(0,Qmax))
    model_s.V_s = Var(model_s.T2, domain=NonNegativeReals, bounds=(0,Vmax))
    model_s.spill = Var(model_s.T2, domain=NonNegativeReals, bounds=(0,Vmax))

    # Constraints
    def reservoir_day1_rule(m,t):
        if t == 1:
            return m.V[t] == m.V0 + m.M_conv*(m.I[t] - m.Q[t]) 
        return m.V[t] == m.V[t-1] + m.M_conv*(m.I[t] - m.Q[t]) 
    model_s.res_day1 = Constraint(model_s.T1, rule=reservoir_day1_rule)
    
    def reservoir_day2_rule(m,t):
        if t == 25:
            return m.V_s[t] == m.V[24] + m.M_conv*(m.I_s[t] - m.Q_s[t]) - m.spill[t]
        return m.V_s[t] == m.V_s[t-1] + m.M_conv*(m.I_s[t] - m.Q_s[t]) - m.spill[t]
    model_s.res_day2 = Constraint(model_s.T2, rule=reservoir_day2_rule) 
    
    def prod_day1_rule(m,t):
        return m.x[t] == m.E_conv*m.M_conv*m.Q[t]*1000
    model_s.prod_day1 = Constraint(model_s.T1, rule=prod_day1_rule)
    
    def prod_day2_rule(m,t):
        return m.x_s[t] == m.E_conv*m.M_conv*m.Q_s[t]*1000
    model_s.prod_day2 = Constraint(model_s.T2, rule=prod_day2_rule)
    
    def obj_rule(m):
        term1 = sum(m.p[t]*m.x[t] for t in m.T1)
        term2 = sum(m.p[t]*m.x_s[t] for t in m.T2) + m.WV_end*m.V_s[48]
        return term1 + term2
    
    model_s.Obj = Objective(rule=obj_rule, sense=maximize)
    model_s.dual = Suffix(direction=Suffix.IMPORT)
    # solver = SolverFactory("gurobi")
    solver = SolverFactory("glpk")
    result = solver.solve(model_s, tee=False)

    print("Objective value:", round(value(model_s.Obj), 2), "EUR")
    print("Reservoir at t=24:", round(value(model_s.V[24]), 2), "Mm3")
    print("Reservoir at t=48:", round(value(model_s.V_s[48]), 2), "Mm3")
    for t in model_s.T1:
        print(f"Hour {t}: Production = {value(model_s.x[t]):.2f} MW, Discharge = {value(model_s.Q[t]):.2f} m3/s, Volume = {value(model_s.V[t]):.2f} Mm3")
    for t in model_s.T2:
        print(f"Hour {t}: Production = {value(model_s.x_s[t]):.2f} MW, Discharge = {value(model_s.Q_s[t]):.2f} m3/s, Volume = {value(model_s.V_s[t]):.2f} Mm3, Spillage: {value(model_s.spill[t]):.2f} Mm3")
    print("\n-----------------------------")



    # Making a dataframe for each scenario and storing results, such that the results can be easily analyzed later through plots
    df_results = pd.DataFrame({
        'Hour': list(model_s.T1) + list(model_s.T2),
        'Production_MW': [value(model_s.x[t]) for t in model_s.T1] + [value(model_s.x_s[t]) for t in model_s.T2],
        'Discharge_m3s': [value(model_s.Q[t]) for t in model_s.T1] + [value(model_s.Q_s[t]) for t in model_s.T2],
        'Volume_Mm3': [value(model_s.V[t]) for t in model_s.T1] + [value(model_s.V_s[t]) for t in model_s.T2]
    })
    df_results.to_csv(f'scenario_{s}_results.csv', index=False)


plt.figure(figsize=(12, 6))
for s in S:
    df = pd.read_csv(f'scenario_{s}_results.csv')
    plt.plot(df['Hour'], df['Production_MW'], label=f'Scenario {s+1}')
plt.xlabel('Hour')
plt.ylabel('Production (MW)')
plt.title('Production over Time for Different Inflow Scenarios')
plt.grid(True)
plt.xticks(T)
plt.legend()
plt.show()
plt.savefig('production_scenarios.png')

plt.figure(figsize=(12, 6))
for s in S:
    df = pd.read_csv(f'scenario_{s}_results.csv')
    plt.plot(T, df['Volume_Mm3'], label=f'Scenario {s+1}')
plt.xlabel('Hour')
plt.ylabel('Reservoir Volume (Mm3)')
plt.title('Reservoir Volume over Time for Different Inflow Scenarios')
plt.grid(True)
plt.xticks(T)
plt.legend()
plt.show()
plt.savefig('reservoir_volume_scenarios.png')


# plt.figure(figsize=(12, 6))
# for s in S:
#     df = pd.read_csv(f'scenario_{s}_results.csv')
#     plt.plot(df['Hour'], df['Discharge_m3s'], label=f'Scenario {s+1}')
# plt.xlabel('Hour')
# plt.ylabel('Discharge (m3/s)')
# plt.title('Discharge over Time for Different Inflow Scenarios')
# plt.legend()
# plt.show()

