import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import os

# ====== Paths ======
# Absolutt sti til mappen der skript og filer ligger
# base_dir = Path(r"C:\TET4565 Kraftmarkeder\Kraftmarkeder - markedsmodul") Sigurd
base_dir = Path(r"\\sambaad.stud.ntnu.no\martbore\Documents\Kraftmarkeder2\Kraftmarkeder-Fordypningsemne\Kraftmarkeder - markedsmodul") #Martin

base_dir = Path(r"C:\TET4565 Kraftmarkeder\Kraftmarkeder-Fordypningsemne\Kraftmarkeder - markedsmodul")
balancing_file = base_dir / "balancing_prices_NO_2_all_years.csv"
spot_file = base_dir / "spot_prices_NO2_2015_2024.csv"


df_spot = pd.read_csv(spot_file, skiprows=1, names=["Time", "Price"])
df_spot['Time'] = pd.to_datetime(df_spot['Time'], utc=True, errors='coerce')
df_spot = df_spot.dropna(subset=['Time'])
df_spot['Month'] = df_spot['Time'].dt.to_period('M')
monthly_spot = df_spot.groupby('Month')['Price'].mean()


df = pd.read_csv(balancing_file)
df['Time'] = pd.to_datetime(df['Unnamed: 0'], utc=True, errors='coerce')
df = df.dropna(subset=['Time'])
df['Month'] = df['Time'].dt.to_period('M')


df_res = df[df["ReserveType"].str.lower() == "mfrr"]


plt.figure(figsize=(12, 6))


for direction in ["Up", "Down"]:
    df_dir = df_res[df_res["Direction"] == direction]
    monthly_avg = df_dir.groupby('Month')['Price'].mean()
    plt.plot(monthly_avg.index.to_timestamp(), monthly_avg.values, label=f"mFRR {direction}")

plt.plot(monthly_spot.index.to_timestamp(), monthly_spot.values, label="Spot Price", linestyle='--', color='black')

plt.title("NO2 - mFRR - Average monthly price (Up/Down) + Spot Price")
plt.xlabel("Month")
plt.ylabel("Average prices (EUR/MWh)")
plt.legend()
plt.tight_layout()


outdir = base_dir / "plots"
os.makedirs(outdir, exist_ok=True)
plt.savefig(outdir / "NO2_mFRR_monthly_avg_with_spot.png")
plt.show()
plt.close()

print("Plotting completed.")

# Hent ut ulik statistikk om median, snitt, maks, min, standardavvik og antall 0-observasjoner
# Gjøres både for mFRR Up og Down og spotpris

stats = {}
for direction in ["Up", "Down"]:
    df_dir = df_res[df_res["Direction"] == direction]
    stats[direction] = {
        "Median": df_dir['Price'].median(),
        "Mean": df_dir['Price'].mean(),
        "Max": df_dir['Price'].max(),
        "Min": df_dir['Price'].min(),
        "StdDev": df_dir['Price'].std(),
        "ZeroCount": (df_dir['Price'] == 0).sum()
    }

# Spotpris statistikk
stats["Spot"] = {
    "Median": df_spot['Price'].median(),
    "Mean": df_spot['Price'].mean(),
    "Max": df_spot['Price'].max(),
    "Min": df_spot['Price'].min(),
    "StdDev": df_spot['Price'].std(),
    "ZeroCount": (df_spot['Price'] == 0).sum()
}

# Print statistikk
for key, value in stats.items():
    print(f"Statistics for {key}:")
    for stat_name, stat_value in value.items():
        print(f"  {stat_name}: {stat_value}")
    print()

# Lagre statistikk til CSV
stats_df = pd.DataFrame(stats).T
stats_df.to_csv(outdir / "price_statistics.csv")

# Plot statistikk i bar chart utenom null-observasjoner
plt.figure(figsize=(10, 6))
stats_no_zero = stats_df.drop(columns=['ZeroCount'])
stats_no_zero.plot(kind='bar', ax=plt.gca())
plt.title("Price Statistics (excluding Zero Counts)")
plt.ylabel("Value (EUR/MWh)")
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig(outdir / "price_statistics_bar.png")
plt.show()
plt.close()

# Nytt plott som sammenligner null-observasjoner i mFRR Up / Down og spotpris
plt.figure(figsize=(8, 5))
zero_counts = stats_df['ZeroCount']
zero_counts.plot(kind='bar', color=['blue', 'orange', 'green'])
plt.title("Count of Zero Price Observations")
plt.ylabel("Count")
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig(outdir / "zero_price_counts.png")
plt.show()
plt.close()

