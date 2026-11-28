import os
import re
import sys
import unicodedata
from datetime import date, datetime, timedelta
from scripts.getdata_2 import get_measures_between
from zoneinfo import ZoneInfo
import pandas as pd
import numpy as np

PARIS = ZoneInfo("Europe/Paris")

def dewpoint(table):
    """Point de rosée (°C). T en °C, RH en %. Magnus"""
    b, c = 17.62, 243.12
    g = np.log(table['Humidity'] / 100) + b * table['Temperature'] / (c + table['Temperature'])
    dp = c * g / (b - g)
    table['Dew_point'] = round(dp,1)
    return table

def wind_chill(table):
    """Température ressentie au vent (°C). T en °C, V en km/h.
    Hors validité (T > 10 °C ou V <= 4,8 km/h), on renvoie T."""
    v16 = np.power(table['WindStrength'], 0.16)
    wc = 13.12 + 0.6215 * table['Temperature'] - 11.37 * v16 + 0.3965 * table['Temperature'] * v16
    wc = np.where((table['Temperature'] <= 10) & (table['WindStrength'] > 4.8), wc, table['Temperature'])
    print(wc)
    quit()

def save_day(day):
    """Récupère le jour `day` (de 00:00 à 24:00, heure de Paris) et l'écrit dans un seul CSV."""
    start = datetime(day.year, day.month, day.day, tzinfo=PARIS)
    end = start + timedelta(days=1)
    tables = get_measures_between(start, end)
 
    columns = []
    for module, df in tables.items():
        if df.empty:
            continue
        df = df[(df.index >= start) & (df.index < end)].copy()
        df.columns = [f"{c}" for c in df.columns]
        # on garde les heures de Netatmo (xx:x2:30, xx:x7:30...) en les arrondissant à la minute
        # pour que les modules tombent sur la même ligne même avec quelques secondes d'écart
        # (arrondi fait en UTC pour ne pas buter sur le changement d'heure)
        df.index = df.index.tz_convert("UTC").floor("1min").tz_convert(PARIS)
        df = df[df.index < end].groupby(level=0).first()
        columns.append(df)
 
    if not columns:
        print(f"{day} : aucune mesure")
        return
    table = pd.concat(columns, axis=1, sort=True)
    table.index.name = "heure"

    table = dewpoint(table)
 
    folder = os.path.join("data", f"{day:%Y}", f"{day:%m}")
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, f"{day:%Y-%m-%d}.csv")
    table.to_csv(path, float_format="%.6g")
    print(f"{day} : {len(table)} lignes, {table.shape[1]} colonnes -> {path}")

def parse(d):
    return datetime.strptime(d, "%Y-%m-%d").date()

def clean(name):
    """'Extérieur' -> 'Exterieur' (noms de colonnes sans accents ni espaces)."""
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_")

if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        days = [datetime.now(PARIS).date() - timedelta(days=1)]          # la veille
    elif len(args) == 1:
        days = [parse(args[0])]
    else:
        d0, d1 = parse(args[0]), parse(args[1])
        days = [d0 + timedelta(days=i) for i in range((d1 - d0).days + 1)]
    for d in days:
        save_day(d)
