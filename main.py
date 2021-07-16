import requests
from decouple import config
import json

baseurl = "https://api.github.com/repos/German-Immersive-Railroading-Community/BetaBranch"

r = requests.get(baseurl)
if r.status_code != 200:
    print(f"Ja scheiße... {r.status_code}")
    exit()
print(r.json())
