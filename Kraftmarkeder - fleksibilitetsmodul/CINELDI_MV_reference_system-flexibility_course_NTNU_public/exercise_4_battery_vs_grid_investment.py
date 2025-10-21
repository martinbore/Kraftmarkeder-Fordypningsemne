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
# print("Load time series data (first 5 rows):")
# print(load_time_series_mapped)
# print(len(load_time_series_mapped))



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

# Calculate peak load values for each year
peak_loads = peak_load_demand_development(P_max_start, growth_factor, years)
year_labels = list(range(years))

# Create the step plot
plt.figure(figsize=(10, 6))
plt.step(year_labels, peak_loads, where='post', linewidth=2, marker='o', markersize=6)

# Add horizontal red dashed line at 4 MW limit
plt.axhline(y=4, color='red', linestyle='--', linewidth=2, label='4 MW Limit')

plt.xlabel('Year')
plt.ylabel('Peak Load (MW)')
plt.title('Peak Load Development over 10 Years (3% Annual Growth)')
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

# Print the values
print("Peak load development over 10 years:")
for year, load in enumerate(peak_loads):
    print(f"Year {year}: {load:.2f} MW")



#### TASK 6 ####

# Reuse the same function from Task 2
# (function is already defined above)

# Plot peak load development over 10 years with battery insertion after Year 1
years = 10
P_max_start = 3.9  # MW
growth_factor = 0.03  # 3% annual growth

# Calculate peak load values for each year
peak_loads = peak_load_demand_development(P_max_start, growth_factor, years)
year_labels = list(range(years))

# Create the step plot
plt.figure(figsize=(10, 6))
plt.step(year_labels, peak_loads, where='post', linewidth=2, marker='o', markersize=6, label='Peak Load')

# Create dynamic limit line with clear jump at year 1
limit_years = [0, 1, 1, years]  # Include year 1 twice for the vertical jump
limit_values = [4, 4, 5, 5]     # 4MW until year 1, then jump to 5MW at year 1
plt.plot(limit_years, limit_values, color='red', linestyle='--', linewidth=2, label='Grid Limit (4MW → 5MW with battery)')

# Add vertical line to show when battery is inserted
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

for year in range(years):
    load = load_time_series_subset_aggr * (1 + growth_factor) ** year
    max_load = 4.0  # MW
    excess_load = load - max_load
    excess_load[excess_load < 0] = 0  # Only consider positive excess load
    cost_per_mwh = 2000  # NOK/MWh
    annual_cost = excess_load.sum() * cost_per_mwh * 20
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

# # Task 9 - Estimate the annual costs of energy not supplied for grid planning alternative A
c_ens = 0
for bus in bus_i_subset:
    c_ens += data_load_point.loc[bus, 'c_NOK_per_kWh_4h']  # NOK/kWh
    
c_ens = c_ens/len(bus_i_subset)  # Average cost of ENS across the buses in the area
# for year in range(years):
#     load = avg_load * (1 + growth_factor) ** year
#     ens = yearly_downtime * load  # MWh
#     annual_cost_ens = ens * 1000 * c_ens  # NOK
#     print("-----")
#     print(f"Estimated annual cost of ENS in year {year} : {annual_cost_ens:.0f} NOK")

# Task 10 - Estimate the annual costs of energy not supplied for grid planning alternative B (with battery)
for year in range(years):
    load = avg_load * (1 + growth_factor) ** year 
    ens_load = yearly_downtime * load  # MWh, assuming battery can cover 2 MW of load whenever failure occurs
    se_battery = expected_failures_per_year * 2  # MWh, energy supplied by battery during failures
    ens = max(0, ens_load - se_battery)  # MWh
    annual_cost_ens = ens * 1000 * c_ens  # NOK
    print("-----")
    print(f"Estimated annual ENS (with battery) in year {year}: {ens:.2f} MWh")
    print(f"Estimated annual cost of ENS with battery in year {year} : {annual_cost_ens:.0f} NOK")