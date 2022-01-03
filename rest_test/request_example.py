from time import sleep
from urllib.parse import urljoin

import requests
import json

url = "http://localhost/"

payload = {
    "container_tag": "mathiser/nnunet:nnunet_base",
    "model": "Task5003_WholeHeart"
}

with open("test.zip", "rb") as r:
    res = requests.post(url + "inputs/", params=payload,
                        files={"file": r})

print(res)
task = json.loads(res.content)
print(task)
t = 0
while True:
    res = requests.get(urljoin(url, f"outputs/{task['id']}"))
    if res.ok:
        with open(f"{task['id']}.zip", "wb") as f:
            f.write(res.content)
        break
    else:
        print(f"Slept for {t} seconds")
        sleep(1)
        t += 1

