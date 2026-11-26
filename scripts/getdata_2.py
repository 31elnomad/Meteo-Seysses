import os
import time
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import requests

PARIS = ZoneInfo("Europe/Paris")

TYPES = {
    "NAMain":    "Temperature,Humidity,CO2,Pressure,Noise",           # station intérieure
    "NAModule1": "Temperature,Humidity",                              # module extérieur
    "NAModule2": "WindStrength,WindAngle,GustStrength,GustAngle",     # anémomètre
    "NAModule3": "Rain",                                              # pluviomètre
    "NAModule4": "Temperature,Humidity,CO2",                          # module intérieur
}

_access_token = None


def get_access_token():
    """Renouvelle le jeton une seule fois par lancement.
    Netatmo renvoie un NOUVEAU refresh token : on l'enregistre dans new_refresh_token.txt,
    à recopier dans la variable REFRESH_TOKEN (sinon l'ancien finit par ne plus marcher)."""
    global _access_token
    if _access_token:
        return _access_token

    payload = {
        "grant_type": "refresh_token",
        "client_id": os.environ["CLIENT_ID"],
        "client_secret": os.environ["CLIENT_SECRET"],
        "refresh_token": os.environ["REFRESH_TOKEN"],
    }
    r = requests.post("https://api.netatmo.com/oauth2/token", data=payload, timeout=30)
    r.raise_for_status()
    tok = r.json()

    new = tok.get("refresh_token")
    if new and new != os.environ["REFRESH_TOKEN"]:
        with open("new_refresh_token.txt", "w") as f:
            f.write(new)
        os.environ["REFRESH_TOKEN"] = new
        print("Nouveau refresh token enregistré dans new_refresh_token.txt "
              "(mets-le dans REFRESH_TOKEN pour le prochain lancement)")

    _access_token = tok["access_token"]
    return _access_token


def netatmo_get(url, headers, params=None, tries=4):        # <-- NOUVELLE FONCTION ICI
    """GET avec nouvelles tentatives si Netatmo est surchargé (429, 500, 502, 503)."""
    for i in range(tries):
        r = requests.get(url, headers=headers, params=params, timeout=60)
        if r.status_code not in (429, 500, 502, 503):
            r.raise_for_status()
            return r
        wait = 30 * (i + 1)
        print(f"Netatmo répond {r.status_code}, nouvel essai dans {wait} s")
        time.sleep(wait)
    r.raise_for_status()


def get_station_data():
    headers = {"Authorization": f"Bearer {get_access_token()}"}
    r = netatmo_get("https://api.netatmo.com/api/getstationsdata", headers)   # <-- modifié
    return r.json()


def to_ts(d):
    """'2026-11-18' ou '2026-11-18 14:30' (heure de Paris) -> secondes UTC."""
    if isinstance(d, str):
        d = datetime.strptime(d, "%Y-%m-%d %H:%M" if " " in d else "%Y-%m-%d")
    return int((d.replace(tzinfo=PARIS) if d.tzinfo is None else d).timestamp())


def get_measures_between(start, end, scale="5min"):
    """Toutes les mesures entre `start` et `end` (heure de Paris), pour chaque module.
    scale : "max" (brut, ~5 min), "30min", "1hour", "3hours", "1day".
    Renvoie {nom du module: DataFrame indexé par l'heure de Paris}."""
    t0, t1 = to_ts(start), to_ts(end)
    headers = {"Authorization": f"Bearer {get_access_token()}"}
    devices = get_station_data()["body"]["devices"]

    tables = {}
    for dev in devices:
        modules = [(dev.get("module_name") or dev["type"], dev["type"], None)] + \
          [(m.get("module_name") or m["type"], m["type"], m["_id"]) for m in dev.get("modules", [])]
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
