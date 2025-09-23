# -*- coding: utf-8 -*-
"""
Created on 2023-07-14

@author: ivespe

Intro script for Exercise 2 ("Load analysis to evaluate the need for flexibility") 
in specialization course module "Flexibility in power grid operation and planning" 
at NTNU (TET4565/TET4575) 

"""

# %% Dependencies

import pandapower as pp
import pandapower.plotting as pp_plotting
import pandas as pd
import os
import load_scenarios as ls
import load_profiles as lp
import pandapower_read_csv as ppcsv
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np


# %% Define input data

# Location of (processed) data set for CINELDI MV reference system
# (to be replaced by your own local data folder)
#path_data_set         = r'C:\TET4565 Kraftmarkeder\Kraftmarkeder-Fordypningsemne\Kraftmarkeder - fleksibilitetsmodul\7703070\CINELDI_MV_reference_system_v_2023-03-06' #Sigurd
# path_data_set         = r'/Users/olavberger/Kraftmarkeder2 Fordypningsemne_ToUse/Kraftmarkeder-Fordypningsemne/Kraftmarkeder - fleksibilitetsmodul/7703070/CINELDI_MV_reference_system_v_2023-03-06' #Olav
path_data_set = r'C:\Users\marti\Documents\Kraftmarkeder Fordypningsemne\Kraftmarkeder-Fordypningsemne\Kraftmarkeder-Fordypningsemne\Kraftmarkeder - fleksibilitetsmodul\7703070\CINELDI_MV_reference_system_v_2023-03-06' #Martin

filename_load_data_fullpath = os.path.join(path_data_set,'load_data_CINELDI_MV_reference_system.csv')
filename_load_mapping_fullpath = os.path.join(path_data_set,'mapping_loads_to_CINELDI_MV_reference_grid.csv')

# Subset of load buses to consider in the grid area, considering the area at the end of the main radial in the grid
bus_i_subset = [90, 91, 92, 96]

# Assumed power flow limit in MW that limit the load demand in the grid area (through line 85-86)
P_lim = 0.637 

# Maximum load demand of new load being added to the system
P_max_new = 0.4

# Which time series from the load data set that should represent the new load
i_time_series_new_load = 90


# %% Read pandapower network

net = ppcsv.read_net_from_csv(path_data_set, baseMVA=10)

# %% Extract hourly load time series for a full year for all the load points in the CINELDI reference system
# (this code is made available for solving task 3)

load_profiles = lp.load_profiles(filename_load_data_fullpath)

# Get all the days of the year
repr_days = list(range(1,366))

# Get normalized load profiles for representative days mapped to buses of the CINELDI reference grid;
# the column index is the bus number (1-indexed) and the row index is the hour of the year (0-indexed)
profiles_mapped = load_profiles.map_rel_load_profiles(filename_load_mapping_fullpath,repr_days)

# Retrieve normalized load time series for new load to be added to the area
new_load_profiles = load_profiles.get_profile_days(repr_days)
new_load_time_series = new_load_profiles[i_time_series_new_load]*P_max_new

# Calculate load time series in units MW (or, equivalently, MWh/h) by scaling the normalized load time series by the
# maximum load value for each of the load points in the grid data set (in units MW); the column index is the bus number
# (1-indexed) and the row index is the hour of the year (0-indexed)
load_time_series_mapped = profiles_mapped.mul(net.load['p_mw'])
# %%


# Exercise 1 - Plot the voltage profile in the grid and find how low the voltage drops:
pp.runpp(net,init='results',algorithm='bfsw')
pp_plotting.pf_res_plotly(net)
print('Minimum voltage in the system: ' + str(net.res_bus['vm_pu'].min()) + ' p.u.')

# Exercise 2 - Find how much the voltages decrease as the load demand in the area increases
power_df = pd.DataFrame()
Demand_bus_90 = net.load[net.load['bus'] == 90]['p_mw'].values
Demand_bus_91 = net.load[net.load['bus'] == 91]['p_mw'].values
Demand_bus_92 = net.load[net.load['bus'] == 92]['p_mw'].values
Demand_bus_96 = net.load[net.load['bus'] == 96]['p_mw'].values


Scaling_factors = np.arange(1,2.25,0.25) 
plotting_dict = {}
for factor in Scaling_factors:
    net.load.loc[net.load['bus'] == 90, 'p_mw'] = Demand_bus_90 * factor
    net.load.loc[net.load['bus'] == 91, 'p_mw'] = Demand_bus_91 * factor
    net.load.loc[net.load['bus'] == 92, 'p_mw'] = Demand_bus_92 * factor
    net.load.loc[net.load['bus'] == 96, 'p_mw'] = Demand_bus_96 * factor
    pp.runpp(net,init='results',algorithm='bfsw')
    min_voltage = net.res_bus['vm_pu'].min()
    bus_min_voltage = net.res_bus['vm_pu'].idxmin()
    lowest = [bus_min_voltage]
    load_demand_low = net.load.loc[net.load['bus'].isin(lowest), 'p_mw'].sum()
    # Hent last kun for bussene du endrer
    aggregated_load_demand = net.load.loc[net.load['bus'].isin(bus_i_subset), 'p_mw'].sum()
    plotting_dict[factor] = (bus_min_voltage, min_voltage, load_demand_low, aggregated_load_demand)

min_voltages = []
load_demands = []
for key in plotting_dict:
    min_voltages.append(plotting_dict[key][1])
    load_demands.append(plotting_dict[key][3])  

plt.plot(load_demands, min_voltages, marker='o', linestyle='-')

plt.xlabel("Aggregated Load demand [MW]")
plt.ylabel("Minimum voltage [p.u.]")
plt.title("Load vs. Minimum Voltage")
plt.show()

#
#
#Made by Olav, new way to solve Excercise 2
#
#
power_df = pd.DataFrame()
Demand_bus_90 = net.load[net.load['bus'] == 90]['p_mw'].values
Demand_bus_91 = net.load[net.load['bus'] == 91]['p_mw'].values
Demand_bus_92 = net.load[net.load['bus'] == 92]['p_mw'].values
Demand_bus_96 = net.load[net.load['bus'] == 96]['p_mw'].values

# Keep a snapshot of original loads for the selected buses
original_loads = {
    90: float(Demand_bus_90[0]) if len(Demand_bus_90) else 0.0,
    91: float(Demand_bus_91[0]) if len(Demand_bus_91) else 0.0,
    92: float(Demand_bus_92[0]) if len(Demand_bus_92) else 0.0,
    96: float(Demand_bus_96[0]) if len(Demand_bus_96) else 0.0,
}


Scaling_factors = np.arange(1,2.25,0.25) 
plotting_dict = {}
for factor in Scaling_factors:
    net.load.loc[net.load['bus'] == 90, 'p_mw'] = Demand_bus_90 * factor
    net.load.loc[net.load['bus'] == 91, 'p_mw'] = Demand_bus_91 * factor
    net.load.loc[net.load['bus'] == 92, 'p_mw'] = Demand_bus_92 * factor
    net.load.loc[net.load['bus'] == 96, 'p_mw'] = Demand_bus_96 * factor
    pp.runpp(net,init='results',algorithm='bfsw')
    min_voltage = net.res_bus['vm_pu'].min()
    bus_min_voltage = net.res_bus['vm_pu'].idxmin()
    lowest = [bus_min_voltage]
    load_demand_low = net.load.loc[net.load['bus'].isin(lowest), 'p_mw'].sum()
    # Hent last kun for bussene du endrer
    aggregated_load_demand = net.load.loc[net.load['bus'].isin(bus_i_subset), 'p_mw'].sum()
    plotting_dict[factor] = (bus_min_voltage, min_voltage, load_demand_low, aggregated_load_demand)

min_voltages = []
load_demands = []
for key in plotting_dict:
    min_voltages.append(plotting_dict[key][1])
    load_demands.append(plotting_dict[key][3])  

plt.plot(load_demands, min_voltages, marker='o', linestyle='-')

plt.xlabel("Aggregated Load demand [MW]")
plt.ylabel("Minimum voltage [p.u.]")
plt.title("Load vs. Minimum Voltage")
plt.show()

# Restore original loads after the sweep to avoid affecting later calculations
for bus, p in original_loads.items():
    net.load.loc[net.load['bus'] == bus, 'p_mw'] = p

# Create compact scaling table for the selected buses (like the sample table)
scaling_factors_table = [1.0, 1.2, 1.4, 1.6, 1.8, 2.0]
buses_for_table = [90, 91, 92, 96]

# Use per-bus original Pd values from res_bus to avoid side effects and duplication
base_loads = {bus: float(net.res_bus.loc[bus, 'p_mw']) for bus in buses_for_table}

table_cols = [str(sf) for sf in scaling_factors_table]
row_labels = [f"Bus {bus}" for bus in buses_for_table] + ["Aggregated load in system [MW]"]
scaling_table = pd.DataFrame(index=row_labels, columns=table_cols, dtype=float)

for sf in scaling_factors_table:
    # Per-bus scaled values
    for bus in buses_for_table:
        scaling_table.loc[f"Bus {bus}", str(sf)] = base_loads[bus] * sf
    # Aggregated over the specified buses
    scaling_table.loc["Aggregated load in system [MW]", str(sf)] = sum(base_loads.values()) * sf

# Round for neat display
scaling_table = scaling_table.round(4)

print("\nLoad demand values [MW] of existing load points:")
print(scaling_table.to_string())

# Save to CSV next to this script
script_dir = os.path.dirname(os.path.abspath(__file__))
out_csv = os.path.join(script_dir, "ex2_scaling_table.csv")
scaling_table.to_csv(out_csv)
print(f"Saved scaling table to: {out_csv}")

#
#
#Above made by Olav, new way to solve Excercise 2
#
#


# Exercise 3 - Plot the aggregated load demand time series for the grid area
aggregated_load_time_series = load_time_series_mapped[bus_i_subset]

# Plot the load demand time series for the grid area:
plt.figure(figsize=(10, 6))
for bus in bus_i_subset:
    plt.plot(
        aggregated_load_time_series.index,
        aggregated_load_time_series[bus],
        label=f'Bus {bus}'
    )

plt.xlabel("Time [h]")
plt.ylabel("Load Demand [MW]")
plt.title("Load Demand Time Series")
plt.legend()
plt.show()


# Plot the aggregated load demand time series for the grid area:
# Aggregated load demand plot:
plt.figure(figsize=(10, 6))
plt.plot(
    aggregated_load_time_series.index,
    aggregated_load_time_series.sum(axis=1),
    label='Aggregated Load Demand',
    color='black'
)   

plt.xlabel("Time [h]")
plt.ylabel("Aggregated Load Demand [MW]")
plt.title("Aggregated Load Demand Time Series")
plt.legend()
plt.show()

#
#
#Below made by Olav, new way to solve Excercise 3
#
#

aggregated_load_time_series = load_time_series_mapped[bus_i_subset]

# Stacked area plot (improves readability vs overlapping lines)
x = aggregated_load_time_series.index.to_numpy()
y_series = [aggregated_load_time_series[bus].to_numpy() for bus in bus_i_subset]

# Consistent colors (optional) — adjust to taste
color_map = {
    90: '#1f77b4',  # blue
    91: '#ff7f0e',  # orange
    92: '#2ca02c',  # green
    96: '#d62728',  # red
}
colors = [color_map.get(bus, None) for bus in bus_i_subset]
labels = [f'Bus {bus}' for bus in bus_i_subset]

fig, ax = plt.subplots(figsize=(12, 6))
stack_handles = ax.stackplot(x, *y_series, labels=labels, colors=colors, alpha=0.9)

ax.set_xlabel('Hour of the year')
ax.set_ylabel('Load demand [MW]')
ax.set_title('Real-time load demand for the area (stacked)')
ax.grid(True, linestyle=':', alpha=0.5)

ax.legend(loc='upper left', ncol=2, frameon=True)
plt.tight_layout()
plt.show()

# Separate aggregated-only plot (kept as an additional figure)
plt.figure(figsize=(12, 4))
agg = aggregated_load_time_series.sum(axis=1)
plt.plot(agg.index.to_numpy(), agg.to_numpy(), color='black', linewidth=1.2, label='Aggregated Load Demand')
plt.xlabel('Time [h]')
plt.ylabel('Aggregated Load Demand [MW]')
plt.title('Aggregated Load Demand Time Series')
plt.legend()
plt.grid(True, linestyle=':', alpha=0.5)
plt.tight_layout()
plt.show()

#
#
#Above made by Olav, new way to solve Excercise 3
#
#


# Exercise 4 - Find and explain the maximum of the aggregated load time series
max_aggregated_load = aggregated_load_time_series.sum(axis=1).max()
print('Maximum aggregated load demand in the area: ' + str(max_aggregated_load) + ' MW')


# Exercise 5 - Plotting the duration curve for the aggregated load demand in the area:
sorted_load = np.sort(aggregated_load_time_series.sum(axis=1))[::-1]
plt.figure(figsize=(10, 6))
plt.plot(sorted_load, label='Duration Curve', color='blue')
plt.xlabel("Hours")
plt.ylabel("Aggregated Load Demand [MW]")
plt.title("Duration Curve of Aggregated Load Demand")
plt.legend()
plt.show()

# Exercise 6 - Calculate the utilization time and the coincidence factor for the loads in the grid area.
tot_energy = aggregated_load_time_series.sum(axis=1) # MWh
utilization_time = tot_energy.sum() / max_aggregated_load # hours
coincidence_factor = max_aggregated_load / (aggregated_load_time_series.max().sum()) # MW / MW
print('Utilization time: ' + str(utilization_time) + ' hours')
print('Coincidence factor: ' + str(coincidence_factor)) 


# Exercise 7 Capacity margin of the area with respect to the power flow limit 0.637 MW
capacity_margin = P_lim - max_aggregated_load
print('Capacity margin with respect to the power flow limit of ' + str(P_lim) + ' MW: ' + str(capacity_margin) + ' MW')

# Exercise 8 - Plot the aggregated load demand time series for the grid area including the new load
aggregated_load_time_series_with_new = aggregated_load_time_series.copy()
aggregated_load_time_series_with_new['New Load'] = new_load_time_series
plt.figure(figsize=(10, 6))
for column in aggregated_load_time_series_with_new.columns:
    plt.plot(
        aggregated_load_time_series_with_new.index,
        aggregated_load_time_series_with_new[column],
        label=f'{column}'
    )   
plt.xlabel("Time [h]")
plt.ylabel("Load Demand [MW]")
plt.title("Load Demand Time Series Including New Load")
plt.legend()
plt.show()
plt.close()

