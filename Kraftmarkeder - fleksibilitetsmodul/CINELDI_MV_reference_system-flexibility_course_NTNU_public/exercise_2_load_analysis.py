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

#Test push

# %% Define input data

# Location of (processed) data set for CINELDI MV reference system
# (to be replaced by your own local data folder)
#path_data_set         = r'C:\TET4565 Kraftmarkeder\Kraftmarkeder-Fordypningsemne\Kraftmarkeder - fleksibilitetsmodul\7703070\CINELDI_MV_reference_system_v_2023-03-06' #Sigurd
# path_data_set         = r'/Users/olavberger/Kraftmarkeder2 Fordypningsemne_ToUse/Kraftmarkeder-Fordypningsemne/Kraftmarkeder - fleksibilitetsmodul/7703070/CINELDI_MV_reference_system_v_2023-03-06' #Olav
path_data_set = r'C:\Users\marti\Documents\Kraftmarkeder Fordypningsemne\Kraftmarkeder-Fordypningsemne\Kraftmarkeder - Fleksibilitetsmodul\7703070\CINELDI_MV_reference_system_v_2023-03-06' #Martin PC
# path_data_set = r'\\sambaad.stud.ntnu.no\martbore\Documents\Kraftmarkeder2\Kraftmarkeder-Fordypningsemne\Kraftmarkeder - fleksibilitetsmodul\7703070\CINELDI_MV_reference_system_v_2023-03-06' #Martin Linux

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

# Create output directory for saving plots
script_dir = os.path.dirname(os.path.abspath(__file__))
output_dir = os.path.join(script_dir, 'plots')
os.makedirs(output_dir, exist_ok=True)
print(f"Plots will be saved to: {output_dir}")

# Function to safely save plots
def save_plot(filename, show_plot=False):
    """
    Safely save a plot to the output directory
    Args:
        filename (str): Name of the file to save (with .png extension)
        show_plot (bool): Whether to display the plot after saving
    """
    try:
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        full_path = os.path.join(output_dir, filename)
        plt.savefig(full_path, dpi=300, bbox_inches='tight')
        print(f"✓ Plot saved: {filename}")
        if show_plot:
            plt.show()
        return True
    except Exception as e:
        print(f"✗ Error saving {filename}: {e}")
        if show_plot:
            plt.show()  # Still show the plot even if saving fails
        return False

# Exercise 1 - Plot the voltage profile in the grid and find how low the voltage drops:
# pp.runpp(net,init='results',algorithm='bfsw')
# pp_plotting.pf_res_plotly(net)
# print('Minimum voltage in the system: ' + str(net.res_bus['vm_pu'].min()) + ' p.u.')

## Plot the voltage profile in the grid avoiding branches for better visibility. To do this we plot vm_pu vs bus index as long as the voltage 
## drops monotonically along the radial. 
# Extract bus indices and voltages
bus_indices = net.res_bus.index.tolist()
voltages = net.res_bus['vm_pu'].values

# Build a sequence of buses where the voltage strictly decreases or stays constant
monotone_buses = [bus_indices[0]]
monotone_voltages = [voltages[0]]

for i in range(1, len(bus_indices)):
    previous_voltage = monotone_voltages[-1]
    current_voltage = voltages[i]
    if current_voltage <= previous_voltage:
        monotone_buses.append(bus_indices[i])
        monotone_voltages.append(current_voltage)
    # If the voltage increases, skip the point (do not add to the plot)

# Plot the strictly non-increasing voltage profile
plt.figure(figsize=(12, 6))
plt.plot(monotone_buses, monotone_voltages, 'r-')
plt.plot(monotone_buses, 0.95*np.ones(len(monotone_buses)), 'k--')  # Markers for clarity
plt.xlabel('Bus index')
plt.ylabel('Voltage [p.u.]')
plt.title('Voltage profile (strictly non-increasing)')
plt.grid(True)
plt.savefig(os.path.join(output_dir, 'descending_voltage.png'), dpi=300, bbox_inches='tight')



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
save_plot('exercise_2_load_vs_voltage.png')

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
save_plot('exercise_2_load_vs_voltage_olav.png')

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
save_plot('exercise_3_load_time_series_individual_buses.png')


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
# plt.legend()
save_plot('exercise_3_aggregated_load_time_series.png')

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
save_plot('exercise_3_load_time_series_stacked.png')

# Separate aggregated-only plot (kept as an additional figure)
plt.figure(figsize=(12, 4))  # Create new figure
agg = aggregated_load_time_series.sum(axis=1)
plt.plot(agg.index.to_numpy(), agg.to_numpy(), color='black', linewidth=1.2, label='Aggregated Load Demand')
plt.xlabel('Time [h]')
plt.ylabel('Aggregated Load Demand [MW]')
plt.title('Aggregated Load Demand Time Series')
plt.legend()
plt.grid(True, linestyle=':', alpha=0.5)
plt.tight_layout()
save_plot('exercise_3_aggregated_load_time_series_clean.png')

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
save_plot('exercise_5_duration_curve.png')

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

# Create aggregated load time series including the new load
aggregated_load_existing = aggregated_load_time_series.sum(axis=1)
aggregated_load_with_new = aggregated_load_existing + new_load_time_series

# Create DataFrame for plotting
aggregated_load_time_series_with_new = pd.DataFrame({
    'Existing Load': aggregated_load_existing,
    'New Load': new_load_time_series,
    'Total Load': aggregated_load_with_new
})

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
save_plot('exercise_8_load_time_series_with_new_load.png')

# Also create a duration curve for the scenario with new load
sorted_load_with_new = np.sort(aggregated_load_with_new)[::-1]
plt.figure(figsize=(10, 6))
plt.plot(sorted_load_with_new, label='Duration Curve (with new load)', color='red')
plt.plot(P_lim * np.ones(8760), 'k--', label='Power Flow Limit (0.637 MW)', color = 'blue')
plt.xlabel("Hours")
plt.ylabel("Aggregated Load Demand [MW]")
plt.title("Duration Curve Including New Load")
plt.legend()
save_plot('exercise_8_duration_curve_with_new_load.png')


# Exercise 9 - Calculate the maximum amount of overloading in the area after the new load is added.
max_aggregated_load_with_new = aggregated_load_with_new.max()
print('Maximum aggregated load demand in the area including new load: ' + str(max_aggregated_load_with_new) + ' MW')
overloading_amount = max(0, max_aggregated_load_with_new - P_lim)
print('Amount of overloading (if any) with respect to the power flow limit of ' + str(P_lim) + ' MW: ' + str(overloading_amount) + ' MW')

# Exercise 10 - Find the number of hours per year that the load demand would have to be reduced to avoid congestion
hours_to_reduce = 0
for i in range(len(sorted_load_with_new)):
    if sorted_load_with_new[i] >= P_lim:
        hours_to_reduce = i + 1
    elif sorted_load_with_new[i] < P_lim:
        hours_to_reduce += ((P_lim - sorted_load_with_new[i-1]) / (sorted_load_with_new[i] - sorted_load_with_new[i-1])) * (i-i-1)
        break
print('Number of hours per year to reduce load demand to avoid congestion: ' + str(hours_to_reduce) + '\n')

# Exercise 11 - Characterize the need for flexibility in the area

print("A flexibility resource in this context should have the following characteristics:")
print("- Sufficient capacity to reduce load by at least " + str(overloading_amount) + " MW during peak hours.")
print("- Fast response time to quickly adjust to changing grid conditions.")
print("- Ability to provide both upward and downward flexibility.")
print("- Compatibility with existing grid infrastructure and technologies.")
print("Examples of relevant flexibility resources for the DSO include:")
print("- Demand Response Programs: Incentivizing consumers to reduce or shift their electricity usage during peak times.")
print("- Energy Storage Systems: Batteries or other storage technologies that can store excess energy and release it during peak demand.")
print("- Flexible Generation: Power plants that can quickly ramp up or down their output to match demand.")

# Exercise 12 -  Discuss the limitations of using a load duration curve to characterize the flexibility needs in this case

print("Limitations of using a load duration curve to characterize flexibility needs:")
print("- A load duration curve only provides a static view of load patterns and does not account for dynamic changes in demand or supply.")
print("- It does not capture the temporal aspects of flexibility, such as the speed of response or the duration for which flexibility is needed.")
print("- The curve may not reflect the actual operational constraints and capabilities of flexibility resources.")
print("- It does not consider the geographical distribution of loads and generation, which can impact flexibility requirements.")

# Exercise 13 - Compare load duration curves for different assumptions about the new load

# Prepare data for all three scenarios
# a) Constant new load of 0.4 MW
constant_new_load = 0.4
aggregated_load_with_constant_new = aggregated_load_existing + constant_new_load
sorted_load_with_constant_new = np.sort(aggregated_load_with_constant_new)[::-1]

# Create subplots for all three duration curves
fig, axes = plt.subplots(2, 2, figsize=(15, 10))
fig.suptitle('Comparison of Load Duration Curves', fontsize=16, fontweight='bold')

# Subplot 1: Constant new load
axes[0, 0].plot(sorted_load_with_constant_new, color='green', linewidth=2)
axes[0, 0].set_xlabel("Hours")
axes[0, 0].set_ylabel("Aggregated Load Demand [MW]")
axes[0, 0].set_title("a) Constant New Load (0.4 MW)")
axes[0, 0].grid(True, alpha=0.3)

# Subplot 2: Time-dependent new load
axes[0, 1].plot(sorted_load_with_new, color='red', linewidth=2)
axes[0, 1].set_xlabel("Hours")
axes[0, 1].set_ylabel("Aggregated Load Demand [MW]")
axes[0, 1].set_title("b) Time-Dependent New Load")
axes[0, 1].grid(True, alpha=0.3)

# Subplot 3: Existing loads only
axes[1, 0].plot(sorted_load, color='blue', linewidth=2)
axes[1, 0].set_xlabel("Hours")
axes[1, 0].set_ylabel("Aggregated Load Demand [MW]")
axes[1, 0].set_title("c) Existing Loads Only")
axes[1, 0].grid(True, alpha=0.3)

# Subplot 4: All curves on one plot for comparison
axes[1, 1].plot(sorted_load, color='blue', linewidth=2, label='Existing loads only')
axes[1, 1].plot(sorted_load_with_new, color='red', linewidth=2, label='Time-dependent new load')
axes[1, 1].plot(sorted_load_with_constant_new, color='green', linewidth=2, label='Constant new load')
axes[1, 1].set_xlabel("Hours")
axes[1, 1].set_ylabel("Aggregated Load Demand [MW]")
axes[1, 1].set_title("d) All Scenarios Comparison")
axes[1, 1].legend()
axes[1, 1].grid(True, alpha=0.3)

plt.tight_layout()
save_plot('exercise_13_comparison_duration_curves.png')

# Task 14 - Compare utilization times and coincidence factors for different assumptions about the load
# Calculate and compare in a table the utilization time and the coincidence factor for the loads
# in the grid area for cases (a)-(c) in task 13.

# Calculate utilization times and coincidence factors for all three scenarios
def calculate_metrics(aggregated_load, individual_max_loads_sum):
    max_aggregated = aggregated_load.max()
    tot_energy = aggregated_load.sum()  # MWh
    utilization_time = tot_energy / max_aggregated if max_aggregated > 0 else 0  # hours
    coincidence_factor = max_aggregated / individual_max_loads_sum  # MW / MW
    return utilization_time, coincidence_factor

# For existing loads: sum of individual bus maximum loads
individual_max_existing = aggregated_load_time_series.max().sum()

# For time-dependent new load: existing max loads + new load max
individual_max_time_dep = individual_max_existing + new_load_time_series.max()

# For constant new load: existing max loads + constant load (0.4 MW)
individual_max_const = individual_max_existing + constant_new_load

# Calculate metrics for all scenarios
util_time_existing, coinc_factor_existing = calculate_metrics(aggregated_load_existing, individual_max_existing)
util_time_time_dep, coinc_factor_time_dep = calculate_metrics(aggregated_load_with_new, individual_max_time_dep)
util_time_const, coinc_factor_const = calculate_metrics(aggregated_load_with_constant_new, individual_max_const)

# Create comparison table
comparison_table = pd.DataFrame({
    'Scenario': ['Existing Loads Only', 'Time-Dependent New Load', 'Constant New Load (0.4 MW)'],
    'Max Aggregated Load [MW]': [aggregated_load_existing.max(), aggregated_load_with_new.max(), aggregated_load_with_constant_new.max()],
    'Sum of Individual Max [MW]': [individual_max_existing, individual_max_time_dep, individual_max_const],
    'Utilization Time [hours]': [util_time_existing, util_time_time_dep, util_time_const],
    'Coincidence Factor': [coinc_factor_existing, coinc_factor_time_dep, coinc_factor_const]
})
comparison_table = comparison_table.round(4)
print("\nComparison of Utilization Times and Coincidence Factors:")
print(comparison_table.to_string(index=False))

# Exercise 15 -  Explain differences in coincidence factor, utilization time and needs for flexibility
print("Comment on this directly in overleaf report.")


# Summary of saved plots
print("\n" + "="*60)
print("SUMMARY: All plots have been saved to the 'plots' directory")
print("="*60)
saved_plots = [
    'exercise_2_load_vs_voltage.png',
    'exercise_2_load_vs_voltage_olav.png', 
    'exercise_3_load_time_series_individual_buses.png',
    'exercise_3_aggregated_load_time_series.png',
    'exercise_3_load_time_series_stacked.png',
    'exercise_3_aggregated_load_time_series_clean.png',
    'exercise_5_duration_curve.png',
    'exercise_8_load_time_series_with_new_load.png',
    'exercise_8_duration_curve_with_new_load.png',
    'exercise_13_comparison_duration_curves.png'
]

for i, plot in enumerate(saved_plots, 1):
    print(f"{i:2d}. {plot}")

print(f"\nPlot directory: {output_dir}")
print("="*60)
