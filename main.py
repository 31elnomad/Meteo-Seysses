from datetime import datetime
import os
#from scripts.getdata import Token


if __name__ == "__main__":
    client_id = os.environ["CLIENT_ID"]
    refresh_token = os.environ["REFRESH_TOKEN"]
    client_secret = os.environ["CLIENT_SECRET"]
    print("Le script fonctionne !")
    print("Heure actuelle :", datetime.now())
    print(len(client_id), len(refresh_token), len(client_secret))
    print('ok')
