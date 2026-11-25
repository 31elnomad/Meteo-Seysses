import time
import pandas as pd
from datetime import datetime


def get_measures_between(start, end, scale="5min"):
    """Toutes les mesures entre `start` et `end` (heure de Paris), pour chaque module.
    scale : "max" (brut, ~5 min), "30min", "1hour", "3hours", "1day".
    Renvoie {nom du module: DataFrame indexé par l'heure de Paris}."""
    def to_ts(d):
        if isinstance(d, str):
            d = datetime.strptime(d, "%Y-%m-%d %H:%M" if " " in d else "%Y-%m-%d")
        return int((d.replace(tzinfo=PARIS) if d.tzinfo is None else d).timestamp())
    t0, t1 = to_ts(start), to_ts(end)

    access_token = get_access_token()
    headers = {"Authorization": f"Bearer {access_token}"}
    devices = get_station_data()["body"]["devices"]

    tables = {}
    for dev in devices:
        modules = [(dev["module_name"], dev["type"], None)] + \
                  [(m["module_name"], m["type"], m["_id"]) for m in dev.get("modules", [])]
        for name, mtype, module_id in modules:
            if mtype not in TYPES:
                continue
            types = TYPES[mtype].split(",")
            rows, begin = {}, t0
            while begin < t1:                      # Netatmo renvoie 1024 mesures max par requête
                params = {"device_id": dev["_id"], "scale": scale, "type": TYPES[mtype],
                          "date_begin": begin, "date_end": t1, "limit": 1024, "optimize": "false"}
                if module_id:
                    params["module_id"] = module_id
                r = requests.get("https://api.netatmo.com/api/getmeasure",
                                 headers=headers, params=params, timeout=60)
                r.raise_for_status()
                body = r.json()["body"]
                if not body:
                    break
                rows.update({int(k): v for k, v in body.items()})
                if len(body) < 1024:
                    break                          # tout est arrivé
                begin = max(rows) + 1              # page suivante
                time.sleep(0.3)                    # limite Netatmo : 50 requêtes / 10 s
            if not rows:
                tables[name] = pd.DataFrame(columns=types)
                continue
            df = pd.DataFrame.from_dict(rows, orient="index", columns=types).sort_index()
            df.index = pd.to_datetime(df.index, unit="s", utc=True).tz_convert(PARIS)
            df.index.name = "heure"
            tables[name] = df
    return tables


if __name__ == "__main__":
    data = get_measures_between("2026-11-18", "2026-11-25 12:00")
    for module, df in data.items():
        print(f"\n{module} : {len(df)} mesures")
        print(df.head(3))
        df.to_csv(f"netatmo_{module}.csv")
