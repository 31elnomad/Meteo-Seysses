from datetime import datetime
import os
import time
import json
from scripts.getdata_ import get_access_token, get_station_data

a = get_access_token()
b = get_station_data()

tmp = b['body']['devices'][0]

dashboard = station["dashboard_data"]

results = {
  "date": time.strftime("%d.%m.%Y à %H:%M"),
  "pression": dashboard.get("Pressure")
}



print(results)
#print(b['body']['devices'][0].keys())

