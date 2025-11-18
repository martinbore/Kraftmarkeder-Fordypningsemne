# -*- coding: utf-8 -*-
"""
Created on 2023-10-10

@author: ivespe

Intro script for Exercise 4 ("Battery energy storage system in the grid vs. grid investments") 
in specialization course module "Flexibility in power grid operation and planning" 
at NTNU (TET4565/TET4575) 

"""


# %% Dependencies

import pandas as pd
import os
import load_profiles as lp
import pandapower_read_csv as ppcsv
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# %% Define input data

# Location of (processed) data set for CINELDI MV reference system
# (to be replaced by your own local data folder)
# path_data_set         = 'C:/Users/ivespe/Data_sets/CINELDI_MV_reference_system/'
# path_data_set = '/Users/olavberger/Kraftmarkeder2 Fordypningsemne_ToUse/Kraftmarkeder-Fordypningsemne/Kraftmarkeder - fleksibilitetsmodul/7703070/'
path_data_set = r'C:/Users/marti/Documents/Kraftmarkeder Fordypningsemne/Kraftmarkeder-Fordypningsemne/Kraftmarkeder - fleksibilitetsmodul/7703070/'

filename_load_data_fullpath = os.path.join(path_data_set,'load_data_CINELDI_MV_reference_system.csv')
filename_load_mapping_fullpath = os.path.join(path_data_set,'mapping_loads_to_CINELDI_MV_reference_grid.csv')
filename_standard_overhead_lines = os.path.join(path_data_set,'standard_overhead_line_types.csv')
filename_reldata = os.path.join(path_data_set,'reldata_for_component_types.csv')
filename_load_point = os.path.join(path_data_set,'CINELDI_MV_reference_system_load_point.csv')

# Subset of load buses to consider in the grid area, considering the area at the end of the main radial in the grid
bus_i_subset = [90, 91, 92, 96]

# Assumed power flow limit in MW that limit the load demand in the grid area (through line 85-86)
P_lim = 4

# Factor to scale the loads for this exercise compared with the base version of the CINELDI reference system data set
scaling_factor = 10

# Read standard data for overhead lines
data_standard_overhead_lines = pd.read_csv(filename_standard_overhead_lines, delimiter=';')
data_standard_overhead_lines.set_index(keys = 'type', drop = True, inplace = True)

# Read standard component reliability data
data_comp_rel = pd.read_csv(filename_reldata, delimiter=';')
data_comp_rel.set_index(keys = 'main_type', drop = True, inplace = True)

# Read load point data (incl. specific rates of costs of energy not supplied) for data
data_load_point = pd.read_csv(filename_load_point, delimiter=';')
data_load_point.set_index(keys = 'bus_i', drop = True, inplace = True)


# %% Read pandapower network

net = ppcsv.read_net_from_csv(path_data_set, baseMVA=10)


# %% Set up hourly normalized load time series for a representative day (task 2; this code is provided to the students)

load_profiles = lp.load_profiles(filename_load_data_fullpath)

# Consider only the day with the peak load in the area (28 February)
repr_days = [31+28]

# Get relative load profiles for representative days mapped to buses of the CINELDI test network;
# the column index is the bus number (1-indexed) and the row index is the hour of the year (0-indexed)
profiles_mapped = load_profiles.map_rel_load_profiles(filename_load_mapping_fullpath,repr_days)

# Calculate load time series in units MW (or, equivalently, MWh/h) by scaling the normalized load time series by the
# maximum load value for each of the load points in the grid data set (in units MW); the column index is the bus number
# (1-indexed) and the row index is the hour of the year (0-indexed)
load_time_series_mapped = profiles_mapped.mul(net.load['p_mw'])


# %% Aggregate the load demand in the area

# Aggregated load time series for the subset of load buses
load_time_series_subset = load_time_series_mapped[bus_i_subset] * scaling_factor
load_time_series_subset_aggr = load_time_series_subset.sum(axis=1)


P_max = load_time_series_subset_aggr.max()

#### TASK 2 ####

def peak_load_demand_development(P_max, factor, years):
   Peak_load_values_each_year = []
   for year in range(years):
         Peak_load_values_each_year.append(P_max * (1 + factor) ** year)
   return Peak_load_values_each_year

# Plot peak load development over 10 years
years = 10
P_max_start = 3.9  # MW
growth_factor = 0.03  # 3% annual growth

# # Calculate peak load values for each year
peak_loads = peak_load_demand_development(P_max_start, growth_factor, years)
year_labels = list(range(years))

# # Create the step plot
plt.figure(figsize=(10, 6))
plt.step(year_labels, peak_loads, where='post', linewidth=2, marker='o', markersize=6)

# # Add horizontal red dashed line at 4 MW limit
plt.axhline(y=4, color='red', linestyle='--', linewidth=2, label='4 MW Limit')

plt.xlabel('Year')
plt.ylabel('Peak Load (MW)')
plt.title('Peak Load Development over 10 Years (3% Annual Growth)')
plt.grid(True, alpha=0.3)
plt.xticks(range(years + 1))  # Show x-axis from 0 to 10
plt.xlim(-0.5, years)  # Set x-axis limits to show year 10

# # Add value labels on each point
for i, value in enumerate(peak_loads):
    plt.annotate(f'{value:.2f}', (i, value), textcoords="offset points", 
                xytext=(0,10), ha='center', fontsize=9)

plt.legend()
plt.tight_layout()
plt.show()

# # Print the values
print("Peak load development over 10 years:")
for year, load in enumerate(peak_loads):
    print(f"Year {year}: {load:.2f} MW")



# Task 6 - Find how a battery in the grid can postpone grid investments and reduce its present value

# # Plot peak load development over 10 years with battery insertion after Year 1
years = 10
P_max_start = 3.9  # MW
growth_factor = 0.03  # 3% annual growth

# # Calculate peak load values for each year
peak_loads = peak_load_demand_development(P_max_start, growth_factor, years)
year_labels = list(range(years))

# # Create the step plot
plt.figure(figsize=(10, 6))
plt.step(year_labels, peak_loads, where='post', linewidth=2, marker='o', markersize=6, label='Peak Load')

# # Create dynamic limit line with clear jump at year 1
limit_years = [0, 1, 1, years]  # Include year 1 twice for the vertical jump
limit_values = [4, 4, 5, 5]     # 4MW until year 1, then jump to 5MW at year 1
plt.plot(limit_years, limit_values, color='red', linestyle='--', linewidth=2, label='Grid Limit (4MW → 5MW with battery)')

# # Add vertical line to show when battery is inserted
plt.axvline(x=1, color='green', linestyle=':', linewidth=2, alpha=0.7, label='Battery Insertion')

plt.xlabel('Year')
plt.ylabel('Peak Load (MW)')
plt.title('Peak Load Development with Battery Insertion (3% Annual Growth)')
plt.grid(True, alpha=0.3)
plt.xticks(range(years + 1))  # Show x-axis from 0 to 10
plt.xlim(-0.5, years)  # Set x-axis limits to show year 10

# Add value labels on each point
for i, value in enumerate(peak_loads):
    plt.annotate(f'{value:.2f}', (i, value), textcoords="offset points", 
                xytext=(0,10), ha='center', fontsize=9)

plt.legend()
plt.tight_layout()
plt.show()

# Task 7 - Estimate the annual operational costs of using battery for congestion management in the grid area

operation_cost = []
for year in range(years):
    load = load_time_series_subset_aggr * (1 + growth_factor) ** year
    max_load = 4.0  # MW
    excess_load = load - max_load
    excess_load[excess_load < 0] = 0  # Only consider positive excess load
    cost_per_mwh = 2000  # NOK/MWh
    annual_cost = excess_load.sum() * cost_per_mwh * 20
    operation_cost.append(annual_cost)
    print("-----")
    print(f"Excess load profile sum for year {year}: {20*excess_load.sum():3f} MWh")
    print(f"Estimated annual operational cost for year {year}: {annual_cost:.0f} NOK")


# Task 8 - Estimate the annual expected energy not supplied for grid planning alternative A
lambda_perm = data_comp_rel.loc['Overhead line (1_22 kV)', 'lambda_perm'] # Failure rate for lines (failures per 100 km/year)
line_length = 20 # km
expected_failures_per_year = (lambda_perm / 100) * line_length
duration_per_failure = data_comp_rel.loc['Overhead line (1_22 kV)', 'r_perm']  # hours
yearly_downtime = expected_failures_per_year * duration_per_failure
avg_load = 1.841 # MW (mean load in the grid area)

for year in range(years):
    load = avg_load * (1 + growth_factor) ** year
    ens = yearly_downtime * load  # MWh
    print("-----")
    print(f"Estimated annual ENS for year {year} : {ens:.2f} MWh")

# Task 9 - Estimate the annual costs of energy not supplied for grid planning alternative A
c_ens = 0
for bus in bus_i_subset:
    c_ens += data_load_point.loc[bus, 'c_NOK_per_kWh_4h']  # NOK/kWh
    
c_ens = c_ens/len(bus_i_subset)  # Average cost of ENS across the buses in the area
Interruption_costs_A = []
for year in range(years):
    load = avg_load * (1 + growth_factor) ** year
    ens = yearly_downtime * load  # MWh
    annual_cost_ens = ens * 1000 * c_ens  # NOK
    Interruption_costs_A.append(annual_cost_ens)
    print("-----")
    print(f"Estimated annual cost of ENS in year {year} : {annual_cost_ens:.0f} NOK")

# Task 10 - Estimate the annual costs of energy not supplied for grid planning alternative B (with battery)
Interruption_costs_B = []
for year in range(years):
    if year != years-1:
        load = avg_load * (1 + growth_factor) ** year 
        ens_load = yearly_downtime * load  # MWh, assuming battery can cover 2 MW of load whenever failure occurs
        se_battery = expected_failures_per_year * 2  # MWh, energy supplied by battery during failures
        ens = max(0, ens_load - se_battery)  # MWh
        annual_cost_ens = ens * 1000 * c_ens  # NOK
        Interruption_costs_B.append(annual_cost_ens)
        print("-----")
        print(f"Estimated annual ENS (with battery) in year {year}: {ens:.2f} MWh")
        print(f"Estimated annual cost of ENS with battery in year {year} : {annual_cost_ens:.0f} NOK")
    else:
        annual_cost_ens = Interruption_costs_A[-1]
        Interruption_costs_B.append(annual_cost_ens)
        print("-----")
        print(f"Estimated annual ENS (with battery) in year {year}: {ens:.2f} MWh")
        print(f"Estimated annual cost of ENS with battery in year {year} : {annual_cost_ens:.0f} NOK")



# # Task 12 Calculate total present value of the socio-economic costs of grid planning alternative A
C_km = 759408 #NOK/km
C_inv = C_km * line_length  # NOK
print("------")
print(C_inv)

r = 0.04  # discount rate

t_end = 20
t_investment = 1
t_life = 40

C_residual = C_inv * (t_life - (t_end - t_investment)) / t_life
NPV_total_A = C_inv/(1 + r) ** (t_investment) - C_residual / (1 + r) ** (t_end)
NPV_cens_A = 0

for i in range(len(Interruption_costs_A)):
    NPV_cens_A += Interruption_costs_A[i] / (1 + r) **(i)
    print("-----")
    print(f"NPV of interruption costs year {i}: {Interruption_costs_A[i]/ (1 + r) **(i):.0f} NOK")

NPV_secio_economic_costs_A = NPV_total_A + NPV_cens_A
print("===================================")
print(f"NPV of investment costs alternative A: {NPV_total_A:.0f} NOK")
print(f"NPV of interruption costs alternative A: {NPV_cens_A:.0f} NOK")
print(f"NPV of total socio-economic costs alternative A: {NPV_secio_economic_costs_A:.0f} NOK")

# # Task 13 - Calculate total present value of the socio-economic costs of grid planning alternative B (with battery)
operation_cost_PV = []
Interruption_costs_B_PV = [Interruption_costs_A[0]]
for year in range(len(operation_cost)):
    if year != len(operation_cost)-1:
        operation_cost_PV.append(operation_cost[year] / (1 + r) **(year))
    else:
        operation_cost_PV.append(0)  # No operation cost in year 10, as we only consider 10 years
    if year > 0:
        Interruption_costs_B_PV.append(Interruption_costs_B[year] / (1 + r) **(year))
    print("-----")
    print(f"PV of operation costs year {year}: {operation_cost_PV[year]:.0f} NOK")
    print(f"PV of interruption costs year {year}: {Interruption_costs_B_PV[year]:.0f} NOK")



def present_value(t_end, t_inv, r, C_inv, t_life):
    C_residual = C_inv * (t_life - (t_end - t_inv)) / t_life
    NPV_total = C_inv/(1 + r) ** (t_inv) - C_residual / (1 + r) ** (t_end)
    return NPV_total

NPV_inv_B = present_value(20, 9, 0.04, C_inv, 40)  # NOK
print("------")
print(f"NPV of investment costs alternative B: {NPV_inv_B:.0f} NOK")
print("------")
print(f"NPV of operation costs alternative B: {sum(operation_cost_PV):.0f} NOK")
print("------")
print(f"NPV of interruption costs alternative B: {sum(Interruption_costs_B_PV):.0f} NOK")
NPV_secio_economic_costs_B = NPV_inv_B + sum(operation_cost_PV) + sum(Interruption_costs_B_PV)
print("===================================")
print(f"NPV of total socio-economic costs alternative B: {NPV_secio_economic_costs_B:.0f} NOK")

# Task 14 - Modify the optimization model from Exercise 3 to model the operation of the battery
from pyomo.opt import SolverFactory
from pyomo.core import Var
import pyomo.environ as en
import time

#---------------------- COPY OF EXERCISE 3 CODE - MODIFIED FOR EXERCISE 4 ----------------------#

# #%% Read battery specifications
os.chdir(os.path.dirname(os.path.abspath(__file__)))
parametersinput = pd.read_csv('./battery_data.csv', index_col=0)
parameters = parametersinput.loc[1]

# #Parse battery specification
# capacity=2 #MWh
# charging_power_limit=1 #MW
# discharging_power_limit=parameters["Power_capacity"]
charging_efficiency=parameters["Charging_efficiency"]
discharging_efficiency=parameters["Discharging_efficiency"]
# #%% Read load demand and PV production profile data
# testData = pd.read_csv('./profile_input.csv')

# # Convert the various timeseries/profiles to numpy arrays
# Hours = testData['Hours'].values
# Base_load = load_time_series_subset_aggr.values* (1+ growth_factor) ** 6 # Using the base year load profile
# PV_prod = testData['PV_prod'].values*0 # Setting PV production to zero for this exercise
# Price = testData['Price'].values

# # Make dictionaries (for simpler use in Pyomo)
# dict_Prices = dict(zip(Hours, Price))
# dict_Base_load = dict(zip(Hours, Base_load))
# dict_PV_prod = dict(zip(Hours, PV_prod))
# # %%


# # Task 2 - Implementing the optimization model:
# model = en.ConcreteModel()

# # Charging and discharging power variables:
# # This is given in MW:
# model.x_c = Var(Hours, within = en.NonNegativeReals, bounds = (0,charging_power_limit))
# model.x_d = Var(Hours, within = en.NonNegativeReals, bounds = (0,discharging_power_limit))

# # State of charge variable:
# # This is given in MWh:
# model.soc = Var(Hours, within = en.NonNegativeReals, bounds = (0,capacity))

# # Objective function - minimize the net cost of electricity:
# # Note: We have assumed that the discharge and charging variables are from the grid perspective:
# def objective_rule(m):
#     return sum((dict_Prices[h] * (dict_Base_load[h] - dict_PV_prod[h] + m.x_c[h] - m.x_d[h])) for h in Hours)

# # The constraints:
# # print(Hours)
# def soc_constraint(m,h):
#     if (h == min(Hours)):
#         return m.soc[h] == (m.x_c[h] * charging_efficiency - m.x_d[h] / discharging_efficiency)
#     else:
#         return m.soc[h] == m.soc[h-1] + (m.x_c[h] * charging_efficiency - m.x_d[h] / discharging_efficiency)



# # Task 3 - Solving the optimization model:

# model.objective = en.Objective(rule = objective_rule, sense = en.minimize)
# model.soc_con = en.Constraint(Hours, rule = soc_constraint)
# opt = SolverFactory('gurobi')
# start = time.time()
# results = opt.solve(model)
# print("Solver status:", results.solver.status)
# print("Termination condition:", results.solver.termination_condition)
# end = time.time()
# print('Solving time (seconds): ', end - start)
# print('Objective value: ', en.value(model.objective))
# print("Printing the schedules:")
# for h in Hours:
#     print('Hour: ', h, ' Charge (kW): ', en.value(model.x_c[h]), ' Discharge (kW): ', en.value(model.x_d[h]), ' State of Charge (kWh): ', en.value(model.soc[h]))




# # To display the results in the console:
# model.display()

# # Task 6 - Add a constraint for limiting the power imported from the grid to the household
# # We limit the net power consumption, i.e the import from the grid for each hour
# P_limit = 4 # MW
# def power_limit_constraint(m,h):
#     return (dict_Base_load[h] - dict_PV_prod[h] + m.x_c[h] - m.x_d[h]) <= P_limit

# model_new = en.ConcreteModel()

# # Charging and discharging power variables:
# # This is given in kW:
# model_new.x_c = Var(Hours, within = en.NonNegativeReals, bounds = (0,charging_power_limit))
# model_new.x_d = Var(Hours, within = en.NonNegativeReals, bounds = (0,discharging_power_limit))

# # State of charge variable:
# # This is given in kWh:
# model_new.soc = Var(Hours, within = en.NonNegativeReals, bounds = (0,capacity))

# model_new.power_limit_con = en.Constraint(Hours, rule=power_limit_constraint)
# model_new.objective = en.Objective(rule = objective_rule, sense = en.minimize)
# model_new.soc_con = en.Constraint(Hours, rule = soc_constraint)
# opt = SolverFactory('gurobi')
# results = opt.solve(model_new)
# print("Objective value with power limit: ", en.value(model_new.objective))
# print("Solver status:", results.solver.status)
# for h in Hours:
#     print('Hour: ', h, ' Charge (kW): ', en.value(model_new.x_c[h]), ' Discharge (kW): ', en.value(model_new.x_d[h]), ' State of Charge (kWh): ', en.value(model_new.soc[h]))
# print("The net system cost: ", en.value(model_new.objective))

# #%% Plotting the results
# # Extract the results from the Pyomo variables:
# x_c = np.zeros(len(Hours))
# x_d = np.zeros(len(Hours))
# soc = np.zeros(len(Hours))
# for h in Hours:
#     x_c[h-1] = en.value(model_new.x_c[h])
#     x_d[h-1] = en.value(model_new.x_d[h])
#     soc[h-1] = en.value(model_new.soc[h])
# # Plot the results
# plt.figure(figsize=(10,8))
# plt.subplot(2,1,1)
# plt.plot(Hours, x_c, label='Charging power (kW)')
# plt.plot(Hours, x_d, label='Discharging power (kW)')
# plt.title('Battery Charging and Discharging Power Schedule including household power limit')
# plt.xlabel('Hour')
# plt.ylabel('Power (kW)')
# plt.legend()
# plt.grid()
# plt.subplot(2,1,2)
# plt.plot(Hours, soc, label='State of Charge (kWh)', color='orange')
# plt.title('Battery State of Charge')
# plt.xlabel('Hour')
# plt.ylabel('Energy (kWh)')
# plt.legend()
# plt.grid()
# plt.tight_layout()
# # plt.show()
# plt.savefig('./plots/Exercise_4_14_battery_schedule.png')

# # Plot the electricity price profile with the production and load profile
# plt.figure(figsize=(10,8))
# plt.subplot(2,1,1)
# plt.plot(Hours, Price, label='Electricity Price (NOK/kWh)', color='green')
# plt.title('Electricity Price Profile including household power limit')
# plt.xlabel('Hour')
# plt.ylabel('Price (NOK/kWh)')
# plt.legend()
# plt.grid()
# plt.subplot(2,1,2)
# plt.plot(Hours, Base_load, label='Base Load (kWh)', color='red')
# plt.plot(Hours, PV_prod, label='PV Production (kWh)', color='blue')
# plt.title('Load and PV Production Profile including household power limit')
# plt.xlabel('Hour')
# plt.ylabel('Energy (kWh)')
# plt.legend()
# plt.grid()
# plt.tight_layout()
# # plt.show()
# plt.savefig('./plots/Exercise_4_14_electricity_price_and_load.png')


# net_profile_with_battery = Base_load - PV_prod + x_c - x_d
# net_profile_without_battery = Base_load - PV_prod
# plt.figure(figsize=(10,5))
# plt.plot(Hours, net_profile_with_battery, label='Net Load Profile with Battery (kWh)', color='purple')
# plt.plot(Hours, net_profile_without_battery, label='Net Load Profile without Battery (kWh)', color='orange')
# plt.title('Net Load Profile with and without Battery Operation with Power limit')
# plt.xlabel('Hour')
# plt.ylabel('Energy (kWh)')
# plt.legend()
# plt.grid()
# # plt.show()
# plt.savefig('./plots/Exercise_4_14_net_load_profile.png')

### END OF COPY OF EXERCISE 3 ###

# # Task 15 - Solve the model for P_base_load for year 6
load_time_series_subset_aggr_year6 = load_time_series_subset_aggr * (1 + growth_factor) ** 6
congestion_mwh = []
congestion_mwh_aggr = 0
congestion_mwh_aggr_list = []
battery_SoC = 0  # MWh
power_limit = 1 # MW
energy_capacity = 2 # MWh

for load in load_time_series_subset_aggr_year6:
    excess_load = load - P_lim
    if excess_load > 0:
        # There is congestion
        if battery_SoC > 0:
            # Battery can help reduce congestion
            discharge = min(excess_load, power_limit, battery_SoC)
            battery_SoC -= discharge*discharging_efficiency
            excess_load -= discharge*discharging_efficiency
        congestion_mwh.append(excess_load)
        congestion_mwh_aggr += excess_load
    else:
        # No congestion, charge the battery if possible
        charge = min(-excess_load, power_limit, energy_capacity - battery_SoC)
        battery_SoC += charge*charging_efficiency
        congestion_mwh.append(0)
    congestion_mwh_aggr_list.append(congestion_mwh_aggr)
    # print(f"Load: {load:.2f} MW, Excess Load: {excess_load:.2f} MW, Battery SoC: {battery_SoC:.2f} MWh")
    

# Plot the accumulated congestion MWh over the day
plt.figure(figsize=(10, 6))
plt.plot(range(1, 25), congestion_mwh, label='Hourly Congestion (MWh)', color='purple')
c=0
for h in range(len(congestion_mwh)):
    if congestion_mwh[h] > 0:
        c+=1
        plt.scatter(h+1, congestion_mwh[h], color='red', alpha=0.5, label=f'Congestion Occurrence n={c}' if c==12 else "")
plt.title('Hourly Congestion Over the Day')
plt.xlabel('Hour')
plt.ylabel('Congested energy (MWh)')
plt.legend()
plt.grid()
# plt.show()
plt.savefig('./plots/Exercise_4_14_accumulated_congestion.png')

delta_PV_A = present_value(20, 7, 0.04, C_inv, 40) - present_value(20, 9, 0.04, C_inv, 40)
print("------")
print(f"Difference in NPV of investment costs (A - A*): {delta_PV_A:.0f} NOK")