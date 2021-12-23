import zipfile

import requests
import os

import sys
f = sys.argv[1]
i = sys.argv[2]

url = "http://127.0.0.1:8000/upload/"
with open(f, "rb") as r:
    res = requests.post(url, files={"file": r}, timeout=60*5)

with open(f"{i}.zip", "wb") as f:
    f.write(res.content)

with zipfile.ZipFile(f"{i}.zip", "r") as r:
    r.extractall(i)
