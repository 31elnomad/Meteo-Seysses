from datetime import datetime
import os
#from scripts.getdata import Token

print("Le script fonctionne !")
print("Heure actuelle :", datetime.now())
client_id = os.environ["CLIENT_ID"]
refresh_token = os.environ["REFRESH_TOKEN"]
print(len(client_id), len(refresh_token))
print('ok')
