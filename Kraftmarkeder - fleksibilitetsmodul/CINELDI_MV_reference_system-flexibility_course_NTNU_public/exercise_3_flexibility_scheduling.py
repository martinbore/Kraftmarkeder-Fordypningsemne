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
def soc_constraint(m,h):
    if(h == min(Hours)):
        return m.soc[h] == 0 + (m.x_c[h] * charging_efficiency - m.x_d[h] / discharging_efficiency)
    else:
        return m.soc[h] == m.soc[h-1] + (m.x_c[h] * charging_efficiency - m.x_d[h] / discharging_efficiency)
    
def energy_balance(m,h):
    return dict_Base_load[h] + m.x_c[h] == m.x_d[h] + dict_PV_prod[h]


# Task 3 - Solving the optimization model:

model.objective = en.Objective(rule = objective_rule, sense = en.minimize)
model.soc_con = en.Constraint(Hours, rule = soc_constraint)
model.energy_bal = en.Constraint(Hours, rule = energy_balance)
opt = SolverFactory('glpk')
start = time.time()
results = opt.solve(model)
print("Solver status:", results.solver.status)
print("Termination condition:", results.solver.termination_condition)
end = time.time()
print('Solving time (seconds): ', end - start)
print("Printing the schedules:")
for h in Hours:
    print('Hour: ', h, ' Charge (MW): ', en.value(model.x_c[h]), ' Discharge (MW): ', en.value(model.x_d[h]), ' State of Charge (MWh): ', en.value(model.soc[h]))



'''
# To display the results in the console:
model.display()
#%% Plotting the results
# Extract the results from the Pyomo variables:
x_c = np.zeros(len(Hours))
x_d = np.zeros(len(Hours))
soc = np.zeros(len(Hours))
for h in Hours:
    x_c[h] = en.value(model.x_c[h])
    x_d[h] = en.value(model.x_d[h])
    soc[h] = en.value(model.soc[h])
# Plot the results
plt.figure(figsize=(10,8))
plt.subplot(3,1,1)
'''



