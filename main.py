from datetime import datetime
import os
import time
import json
from scripts.getdata_ import get_access_token, get_station_data
from scripts.getdata_2 import get_measures_between

ddeb = "2026-11-25"
dfin = "2026-11-26"

if __name__ == "__main__":
    os.makedirs("data", exist_ok=True) 
    data = get_measures_between(ddeb, dfin)
    print(data)
    quit()
    for module, df in data.items():
        print(f"\n{module} : {len(df)} mesures")
        print(df.head(3))
        df.to_csv(f"data/netatmo_{module}.csv")

"""station = b['body']['devices'][0]

dashboard = station["dashboard_data"]

results = {
  "date": time.strftime("%d.%m.%Y à %H:%M"),
  "pression": dashboard.get("Pressure")
}

with open("data.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(results)
for module in station['modules']:
  print(module)
#print(b['body']['devices'][0].keys())"""

