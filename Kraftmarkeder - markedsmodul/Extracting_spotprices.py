import pandas as pd
from entsoe import EntsoePandasClient
from datetime import datetime

# Sett inn din API-nøkkel her
API_KEY = "ab23f244-da60-4bff-8a00-062135e2a42b"

# Opprett klientobjekt
client = EntsoePandasClient(api_key=API_KEY)

# Definer tidsperioden
start = pd.Timestamp('2015-01-01', tz='UTC')
end = pd.Timestamp('2024-12-31', tz='UTC')

# Hent spotpriser for NO2 (Norge Sør)
prices = client.query_day_ahead_prices('NO_2', start=start, end=end)

# Lagre dataene i en CSV-fil
prices.to_csv('spotpriser_NO2_2015_2024.csv')

print("Data lagret som 'spotpriser_NO2_2015_2024.csv'")
