from datetime import datetime
import os
from scripts.getdata_ import get_access_token, get_station_data

a = get_access_token()
b = get_station_data()
print(b['body']['devices'][0].keys().tolist())

