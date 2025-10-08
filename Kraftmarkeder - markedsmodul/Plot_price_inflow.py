import matplotlib.pyplot as plt
import pandas as pd

# Extracting data from excel file
df_p = pd.read_excel(r"C:\Users\marti\Documents\Kraftmarkeder Fordypningsemne\Kraftmarkeder-Fordypningsemne\Kraftmarkeder - markedsmodul\Data_input_exercise 1.xlsx", sheet_name="Power Prices")
df_i = pd.read_excel(r"C:\Users\marti\Documents\Kraftmarkeder Fordypningsemne\Kraftmarkeder-Fordypningsemne\Kraftmarkeder - markedsmodul\Data_input_exercise 1.xlsx", sheet_name="Inflow Scenarios")

print(df_p.head())
print(df_i.head())

time = df_p['Time step']
price = df_p['Price']
inflow = df_i['Inflow']
scenario = df_i['Scenario']

# Plotting the data
plt.figure(figsize=(12, 6))
plt.plot(time, price, label='Power Price', color='blue')
plt.xlabel('Time Step (Hours)')
plt.ylabel('Price (NOK/MWh)')
plt.title('Power Price vs Time')
plt.legend()
plt.grid()
plt.savefig('power_price_vs_time.png')

# The inflow vs scenario must be a bar plot
plt.figure(figsize=(12, 6))
plt.bar(scenario, inflow, label='Inflow', color='green')
plt.xlabel('Scenario')
plt.ylabel('Inflow (m3/s)')
plt.title('Inflow vs Scenario')
plt.legend()
plt.savefig('inflow_vs_scenario.png')

