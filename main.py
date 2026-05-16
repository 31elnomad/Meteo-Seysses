from datetime import datetime
import os

print("Le script fonctionne !")
print("Heure actuelle :", datetime.now())
client_id = os.environ["CLIENT_ID"]
refresh_token = os.environ["REFRESH_TOKEN"]
print(bool(client_id), bool(refresh_token))
print('ok')
