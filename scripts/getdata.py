from datetime import timedelta
from typing import Dict, Any
import os
import requests


class Token:
    VALID_SCALES = {
        "max": (300, 2),
        "5min": (300, 2),
        "30min": (1800, 14),
        "1hour": (3600, 28),
        "1day": (86400, 365),
        "1week": (604800, 365),
    }

    def __init__(self, config: Dict[str, Any], date) -> None:
        self.config = config

        self.client_id = os.environ["CLIENT_ID"]
        self.client_secret = os.environ["CLIENT_SECRET"]
        self.refresh_token = os.environ["REFRESH_TOKEN"]

        self.access_token = config.get("access_token")

        self.start = date
        self.end = self.start + timedelta(seconds=86399)

        self.scale = config["date"]["scale"]

        if self.scale not in self.VALID_SCALES:
            raise ValueError(
                f"scale doit être dans {list(self.VALID_SCALES.keys())}"
            )

        self.scale_sec, self.ndays_max = self.VALID_SCALES[self.scale]
        self.nbdays = (self.end - self.start).days + 1

    def refresh_access_token(self) -> str:
        url = "https://api.netatmo.com/oauth2/token"

        payload = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        response = requests.post(url, data=payload, timeout=30)
        response.raise_for_status()

        tokens = response.json()

        self.access_token = tokens["access_token"]

        if "refresh_token" in tokens:
            self.refresh_token = tokens["refresh_token"]

        return self.access_token

    def get_mod_device(self) -> dict:
        if not self.access_token:
            self.refresh_access_token()

        url = "https://api.netatmo.com/api/getstationsdata"

        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }

        response = requests.get(url, headers=headers, timeout=30)

        if response.status_code == 401:
            self.refresh_access_token()
            headers["Authorization"] = f"Bearer {self.access_token}"
            response = requests.get(url, headers=headers, timeout=30)

        response.raise_for_status()
        return response.json()
