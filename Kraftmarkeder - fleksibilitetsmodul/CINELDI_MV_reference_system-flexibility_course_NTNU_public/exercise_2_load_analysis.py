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
path_data_set         = r'C:\TET4565 Kraftmarkeder\Kraftmarkeder-Fordypningsemne\Kraftmarkeder - fleksibilitetsmodul\7703070\CINELDI_MV_reference_system_v_2023-03-06'


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


    


