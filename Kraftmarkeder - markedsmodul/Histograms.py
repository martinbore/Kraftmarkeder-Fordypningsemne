# price_histograms.py
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# ====== Paths ======
base_dir = Path(r"C:\TET4565 Kraftmarkeder\Kraftmarkeder - markedsmodul")

spot_file = base_dir / "spot_prices_NO2_2015_2024.csv"
balancing_file = base_dir / "balancing_prices_NO_2_all_years.csv"

# ====== Les spotpris ======
df_spot = pd.read_csv(spot_file, skiprows=1, names=["Time", "SpotPrice"])
df_spot['Time'] = pd.to_datetime(df_spot['Time'], utc=True, errors='coerce')
df_spot = df_spot.dropna(subset=['Time'])

# ====== Les balancing prices ======
df_bal = pd.read_csv(balancing_file)
df_bal['Time'] = pd.to_datetime(df_bal['Unnamed: 0'], utc=True, errors='coerce')
df_bal = df_bal.dropna(subset=['Time'])

# Filtrer mFRR Up og Down
df_up = df_bal[(df_bal["ReserveType"].str.lower() == "mfrr") & (df_bal["Direction"] == "Up")]
df_down = df_bal[(df_bal["ReserveType"].str.lower() == "mfrr") & (df_bal["Direction"] == "Down")]

# Merge alle på Time (hourly)
df_merge = pd.merge(df_spot, df_up[['Time','Price']], on='Time', how='inner')
df_merge = pd.merge(df_merge, df_down[['Time','Price']], on='Time', how='inner')
df_merge = df_merge.rename(columns={'Price_x':'mFRR_Up','Price_y':'mFRR_Down'})

# ====== Histogram ======
plt.figure(figsize=(10,6))
plt.hist(df_merge['SpotPrice'], bins=200, alpha=0.5, label='Spot Price')
plt.hist(df_merge['mFRR_Up'], bins=200, alpha=0.5, label='mFRR Up')
plt.hist(df_merge['mFRR_Down'], bins=200, alpha=0.5, label='mFRR Down')

plt.xlabel("Price (EUR/MWh)")
plt.xlim(-50, 500)
plt.ylabel("Frequency")
plt.title("Price Distribution Histogram")
plt.legend()
plt.tight_layout()

# Lagre og vis
outdir = base_dir / "plots"
outdir.mkdir(exist_ok=True)
plt.savefig(outdir / "price_distribution_histogram.png")
plt.show()
plt.close()
