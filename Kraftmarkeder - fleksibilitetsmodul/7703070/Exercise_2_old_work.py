power_df = pd.DataFrame()
Demand_bus_90 = {"PW": net.load[net.load['bus'] == 90]['p_mw'].values, "QW": net.load[net.load['bus'] == 90]['q_mvar'].values}
Demand_bus_91 = {"PW": net.load[net.load['bus'] == 91]['p_mw'].values, "QW": net.load[net.load['bus'] == 91]['q_mvar'].values}
Demand_bus_92 = {"PW": net.load[net.load['bus'] == 92]['p_mw'].values, "QW": net.load[net.load['bus'] == 92]['q_mvar'].values}
Demand_bus_96 = {"PW": net.load[net.load['bus'] == 96]['p_mw'].values, "QW": net.load[net.load['bus'] == 96]['q_mvar'].values}




Scaling_factors = np.arange(1,2.2,0.2) 
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



Made by Olav, new way to solve Excercise 2


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



# Above made by Olav, new way to solve Excercise 2

