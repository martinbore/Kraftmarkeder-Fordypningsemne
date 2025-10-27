# -*- coding: utf-8 -*-
"""
Created on Fri Mar 31 15:30:27 2023

@author: merkebud, ivespe

Intro script for Exercise 3 ("Scheduling flexibility resources") 
in specialization course module "Flexibility in power grid operation and planning" 
at NTNU (TET4565/TET4575) 

"""
#%%
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from pyomo.opt import SolverFactory
from pyomo.core import Var
import pyomo.environ as en
import time
import os

#%% Read battery specifications
os.chdir(os.path.dirname(os.path.abspath(__file__)))
parametersinput = pd.read_csv('./battery_data.csv', index_col=0)
parameters = parametersinput.loc[1]

#Parse battery specification
capacity=parameters['Energy_capacity']
charging_power_limit=parameters["Power_capacity"]
discharging_power_limit=parameters["Power_capacity"]
charging_efficiency=parameters["Charging_efficiency"]
discharging_efficiency=parameters["Discharging_efficiency"]
#%% Read load demand and PV production profile data
testData = pd.read_csv('./profile_input.csv')

# Convert the various timeseries/profiles to numpy arrays
Hours = testData['Hours'].values
print(Hours)
Base_load = testData['Base_load'].values
PV_prod = testData['PV_prod'].values
Price = testData['Price'].values

# Make dictionaries (for simpler use in Pyomo)
dict_Prices = dict(zip(Hours, Price))
dict_Base_load = dict(zip(Hours, Base_load))
dict_PV_prod = dict(zip(Hours, PV_prod))
# %%


# Task 2 - Implementing the optimization model:
model = en.ConcreteModel()

# Charging and discharging power variables:
# This is given in MW:
model.x_c = Var(Hours, within = en.NonNegativeReals, bounds = (0,charging_power_limit))
model.x_d = Var(Hours, within = en.NonNegativeReals, bounds = (0,discharging_power_limit))

# State of charge variable:
# This is given in MWh:
model.soc = Var(Hours, within = en.NonNegativeReals, bounds = (0,capacity))

# Objective function - minimize the net cost of electricity:
# Note: We have assumed that the discharge and charging variables are from the grid perspective:
def objective_rule(m):
    return sum((dict_Prices[h] * (dict_Base_load[h] - dict_PV_prod[h] + m.x_c[h] - m.x_d[h])) for h in Hours)

# The constraints:
print(Hours)
def soc_constraint(m,h):
    if (h == min(Hours)):
        return m.soc[h] == (m.x_c[h] * charging_efficiency - m.x_d[h] / discharging_efficiency)
    else:
        return m.soc[h] == m.soc[h-1] + (m.x_c[h] * charging_efficiency - m.x_d[h] / discharging_efficiency)



# Task 3 - Solving the optimization model:

model.objective = en.Objective(rule = objective_rule, sense = en.minimize)
model.soc_con = en.Constraint(Hours, rule = soc_constraint)
opt = SolverFactory('glpk')
start = time.time()
results = opt.solve(model)
print("Solver status:", results.solver.status)
print("Termination condition:", results.solver.termination_condition)
end = time.time()
print('Solving time (seconds): ', end - start)
print("Printing the schedules:")
for h in Hours:
    print('Hour: ', h, ' Charge (kW): ', en.value(model.x_c[h]), ' Discharge (kW): ', en.value(model.x_d[h]), ' State of Charge (kWh): ', en.value(model.soc[h]))




# To display the results in the console:
model.display()
#%% Plotting the results
# Extract the results from the Pyomo variables:
x_c = np.zeros(len(Hours))
x_d = np.zeros(len(Hours))
soc = np.zeros(len(Hours))
for h in Hours:
    x_c[h-1] = en.value(model.x_c[h])
    x_d[h-1] = en.value(model.x_d[h])
    soc[h-1] = en.value(model.soc[h])
# Plot the results
plt.figure(figsize=(10,8))
plt.subplot(2,1,1)
plt.plot(Hours, x_c, label='Charging power (kW)')
plt.plot(Hours, x_d, label='Discharging power (kW)')
plt.title('Battery Charging and Discharging Power Schedule')
plt.xlabel('Hour')
plt.ylabel('Power (kW)')
plt.legend()
plt.grid()
plt.subplot(2,1,2)
plt.plot(Hours, soc, label='State of Charge (kWh)', color='orange')
plt.title('Battery State of Charge')
plt.xlabel('Hour')
plt.ylabel('Energy (kWh)')
plt.legend()
plt.grid()
plt.tight_layout()
plt.show()
# Plot the electricity price profile with the production and load profile
plt.figure(figsize=(10,8))
plt.subplot(2,1,1)
plt.plot(Hours, Price, label='Electricity Price (NOK/kWh)', color='green')
plt.title('Electricity Price Profile')
plt.xlabel('Hour')
plt.ylabel('Price (NOK/kWh)')
plt.legend()
plt.grid()
plt.subplot(2,1,2)
plt.plot(Hours, Base_load, label='Base Load (kWh)', color='red')
plt.plot(Hours, PV_prod, label='PV Production (kWh)', color='blue')
plt.title('Load and PV Production Profile')
plt.xlabel('Hour')
plt.ylabel('Energy (kWh)')
plt.legend()
plt.grid()
plt.tight_layout()
plt.show()



# Task 4 - Plot and explain the net profile for the Household:

net_profile_with_battery = Base_load - PV_prod + x_c - x_d
net_profile_without_battery = Base_load - PV_prod
plt.figure(figsize=(10,5))
plt.plot(Hours, net_profile_with_battery, label='Net Load Profile with Battery (kWh)', color='purple')
plt.plot(Hours, net_profile_without_battery, label='Net Load Profile without Battery (kWh)', color='orange')
plt.title('Net Load Profile with and without Battery Operation')
plt.xlabel('Hour')
plt.ylabel('Energy (kWh)')
plt.legend()
plt.grid()
plt.show()

# Task 6 - Add a constraint for limiting the power imported from the grid to the household
# We limit the net power consumption, i.e the import from the grid for each hour
P_limit = 5.8
def power_limit_constraint(m,h):
    return (dict_Base_load[h] - dict_PV_prod[h] + m.x_c[h] - m.x_d[h]) <= P_limit

model_new = en.ConcreteModel()

# Charging and discharging power variables:
# This is given in kW:
model_new.x_c = Var(Hours, within = en.NonNegativeReals, bounds = (0,charging_power_limit))
model_new.x_d = Var(Hours, within = en.NonNegativeReals, bounds = (0,discharging_power_limit))

# State of charge variable:
# This is given in kWh:
model_new.soc = Var(Hours, within = en.NonNegativeReals, bounds = (0,capacity))

model_new.power_limit_con = en.Constraint(Hours, rule=power_limit_constraint)
model_new.objective = en.Objective(rule = objective_rule, sense = en.minimize)
model_new.soc_con = en.Constraint(Hours, rule = soc_constraint)
opt = SolverFactory('glpk')
results = opt.solve(model_new)
print("Solver status:", results.solver.status)
for h in Hours:
    print('Hour: ', h, ' Charge (kW): ', en.value(model_new.x_c[h]), ' Discharge (kW): ', en.value(model_new.x_d[h]), ' State of Charge (kWh): ', en.value(model_new.soc[h]))
print("The net system cost: ", en.value(model_new.objective))

#%% Plotting the results
# Extract the results from the Pyomo variables:
x_c = np.zeros(len(Hours))
x_d = np.zeros(len(Hours))
soc = np.zeros(len(Hours))
for h in Hours:
    x_c[h-1] = en.value(model_new.x_c[h])
    x_d[h-1] = en.value(model_new.x_d[h])
    soc[h-1] = en.value(model_new.soc[h])
# Plot the results
plt.figure(figsize=(10,8))
plt.subplot(2,1,1)
plt.plot(Hours, x_c, label='Charging power (kW)')
plt.plot(Hours, x_d, label='Discharging power (kW)')
plt.title('Battery Charging and Discharging Power Schedule including household power limit')
plt.xlabel('Hour')
plt.ylabel('Power (kW)')
plt.legend()
plt.grid()
plt.subplot(2,1,2)
plt.plot(Hours, soc, label='State of Charge (kWh)', color='orange')
plt.title('Battery State of Charge')
plt.xlabel('Hour')
plt.ylabel('Energy (kWh)')
plt.legend()
plt.grid()
plt.tight_layout()
plt.show()
# Plot the electricity price profile with the production and load profile
plt.figure(figsize=(10,8))
plt.subplot(2,1,1)
plt.plot(Hours, Price, label='Electricity Price (NOK/kWh)', color='green')
plt.title('Electricity Price Profile including household power limit')
plt.xlabel('Hour')
plt.ylabel('Price (NOK/kWh)')
plt.legend()
plt.grid()
plt.subplot(2,1,2)
plt.plot(Hours, Base_load, label='Base Load (kWh)', color='red')
plt.plot(Hours, PV_prod, label='PV Production (kWh)', color='blue')
plt.title('Load and PV Production Profile including household power limit')
plt.xlabel('Hour')
plt.ylabel('Energy (kWh)')
plt.legend()
plt.grid()
plt.tight_layout()
plt.show()


net_profile_with_battery = Base_load - PV_prod + x_c - x_d
net_profile_without_battery = Base_load - PV_prod
plt.figure(figsize=(10,5))
plt.plot(Hours, net_profile_with_battery, label='Net Load Profile with Battery (kWh)', color='purple')
plt.plot(Hours, net_profile_without_battery, label='Net Load Profile without Battery (kWh)', color='orange')
plt.title('Net Load Profile with and without Battery Operation with Power limit')
plt.xlabel('Hour')
plt.ylabel('Energy (kWh)')
plt.legend()
plt.grid()
plt.show()

