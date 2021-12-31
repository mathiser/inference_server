import zipfile

import requests
import os

import sys
f = sys.argv[1]
i = sys.argv[2]

#url = "http://inference.localhost/upload/"
url = "http://localhost:80/tasks/"
with open(f, "rb") as r:
    res = requests.post(url, files={"file": r}, timeout=60*5)

with open(f"{i}.zip", "wb") as f:
    f.write(res.content)

with zipfile.ZipFile(f"{i}.zip", "r") as r:
    r.extractall(i)
