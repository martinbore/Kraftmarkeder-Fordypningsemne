# correlation_matrix.py
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


base_dir = Path(r"C:\TET4565 Kraftmarkeder\Kraftmarkeder-Fordypningsemne\Kraftmarkeder - markedsmodul")

spot_file = base_dir / "spot_prices_NO2_2015_2024.csv"
balancing_file = base_dir / "balancing_prices_NO_2_all_years.csv"

df_spot = pd.read_csv(spot_file, skiprows=1, names=["Time", "SpotPrice"])
df_spot['Time'] = pd.to_datetime(df_spot['Time'], utc=True, errors='coerce')
df_spot = df_spot.dropna(subset=['Time'])


df_bal = pd.read_csv(balancing_file)
df_bal['Time'] = pd.to_datetime(df_bal['Unnamed: 0'], utc=True, errors='coerce')
df_bal = df_bal.dropna(subset=['Time'])


df_up = df_bal[(df_bal["ReserveType"].str.lower() == "mfrr") & (df_bal["Direction"] == "Up")]
df_down = df_bal[(df_bal["ReserveType"].str.lower() == "mfrr") & (df_bal["Direction"] == "Down")]


df_merge = pd.merge(df_spot, df_up[['Time','Price']], on='Time', how='inner')
df_merge = pd.merge(df_merge, df_down[['Time','Price']], on='Time', how='inner')
df_merge = df_merge.rename(columns={'Price_x':'mFRR_Up','Price_y':'mFRR_Down'})


corr_matrix = df_merge[['SpotPrice','mFRR_Up','mFRR_Down']].corr()


plt.figure(figsize=(6,5))
plt.imshow(corr_matrix, cmap='coolwarm', vmin=-1, vmax=1)
plt.colorbar(label='Correlation')
plt.xticks(range(3), corr_matrix.columns)
plt.yticks(range(3), corr_matrix.columns)


for i in range(3):
    for j in range(3):
        plt.text(j, i, f"{corr_matrix.iloc[i,j]:.2f}", ha='center', va='center', color='black')

plt.title("Correlation Matrix (Hourly Prices)")
plt.tight_layout()

outdir = base_dir / "plots"
outdir.mkdir(exist_ok=True)
plt.savefig(outdir / "correlation_matrix_hourly.png")
plt.show()
plt.close()
