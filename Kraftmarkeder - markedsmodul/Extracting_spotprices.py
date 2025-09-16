import pandas as pd
from entsoe import EntsoePandasClient
import datetime


API_KEY = "ab23f244-da60-4bff-8a00-062135e2a42b"
client = EntsoePandasClient(api_key=API_KEY)


start = pd.Timestamp('2015-01-01', tz='UTC')
end = pd.Timestamp('2024-12-31', tz='UTC')


prices = client.query_day_ahead_prices('NO_2', start=start, end=end)


prices.to_csv('spot_prices_NO2_2015_2024.csv')

print("Data saved as 'spot_prices_NO2_2015_2024.csv'")
