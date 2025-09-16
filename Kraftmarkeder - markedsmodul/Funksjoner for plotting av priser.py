import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import os

# ====== Paths ======
# Absolutt sti til mappen der skript og filer ligger
base_dir = Path(r"C:\TET4565 Kraftmarkeder\Kraftmarkeder - markedsmodul")

# Balancing prices fil
balancing_file = base_dir / "balancing_prices_NO_2_all_years.csv"

# Spotpris fil
spot_file = base_dir / "spot_prices_NO2_2015_2024.csv"

# Sjekk at filene finnes
if not balancing_file.exists():
    raise FileNotFoundError(f"Balancing file not found: {balancing_file}")
if not spot_file.exists():
    raise FileNotFoundError(f"Spot price file not found: {spot_file}")

# ====== Les spotpris ======
df_spot = pd.read_csv(spot_file, skiprows=1, names=["Time", "Price"])
df_spot['Time'] = pd.to_datetime(df_spot['Time'], utc=True, errors='coerce')
df_spot = df_spot.dropna(subset=['Time'])
df_spot['Month'] = df_spot['Time'].dt.to_period('M')
monthly_spot = df_spot.groupby('Month')['Price'].mean()

# ====== Les balancing prices ======
df = pd.read_csv(balancing_file)
df['Time'] = pd.to_datetime(df['Unnamed: 0'], utc=True, errors='coerce')
df = df.dropna(subset=['Time'])
df['Month'] = df['Time'].dt.to_period('M')

# Filtrer for mFRR
df_res = df[df["ReserveType"].str.lower() == "mfrr"]

# ====== Lag plott ======
plt.figure(figsize=(12, 6))

# Plot mFRR Up/Down
for direction in ["Up", "Down"]:
    df_dir = df_res[df_res["Direction"] == direction]
    monthly_avg = df_dir.groupby('Month')['Price'].mean()
    plt.plot(monthly_avg.index.to_timestamp(), monthly_avg.values, label=f"mFRR {direction}")

# Plot spotpris
plt.plot(monthly_spot.index.to_timestamp(), monthly_spot.values, label="Spot Price", linestyle='--', color='black')

plt.title("NO2 - mFRR - Average monthly price (Up/Down) + Spot Price")
plt.xlabel("Month")
plt.ylabel("Average prices (EUR/MWh)")
plt.legend()
plt.tight_layout()

# Lagre figur
outdir = base_dir / "plots"
os.makedirs(outdir, exist_ok=True)
plt.savefig(outdir / "NO2_mFRR_monthly_avg_with_spot.png")

# Vis plottet
plt.show()
plt.close()

print("Plotting completed.")
