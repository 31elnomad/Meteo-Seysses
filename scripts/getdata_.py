import os
import requests

def get_access_token():
    url = "https://api.netatmo.com/oauth2/token"

    payload = {
        "grant_type": "refresh_token",
        "client_id": os.environ["CLIENT_ID"],
        "client_secret": os.environ["CLIENT_SECRET"],
        "refresh_token": os.environ["REFRESH_TOKEN"],
    }

    r = requests.post(url, data=payload)
    r.raise_for_status()
    return r.json()["access_token"]


def get_station_data():
    access_token = get_access_token()

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    r = requests.get(
        "https://api.netatmo.com/api/getstationsdata",
        headers=headers
    )
    r.raise_for_status()
    return r.json()


if __name__ == "__main__":
    data = get_station_data()
    print(data)
