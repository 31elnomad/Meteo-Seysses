from datetime import datetime

print("Le script fonctionne !")
print("Heure actuelle :", datetime.now())

import os

client_id = os.environ["CLIENT_ID"]
refresh_token = os.environ["REFRESH_TOKEN"]

print(client_id, refresh_token)
