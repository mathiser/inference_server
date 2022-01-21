import json
import os

import requests

for fol, subs, files in os.walk("./models"):
    for f in files:
        if f.endswith(".json"):
            detail_file_path = os.path.join(fol, f)
            with open(detail_file_path, "r") as r:
                model_details = json.loads(r.read())

            params = {
                "description": model_details["description"],
                "container_tag": model_details["container_tag"],
                "input_mountpoint": model_details["input_mountpoint"],
                "output_mountpoint": model_details["output_mountpoint"],
                "model_mountpoint": model_details["model_mountpoint"],
                "use_gpu": model_details["use_gpu"],
                "model_available": model_details["model_available"]
            }
            with open(os.path.join(fol, model_details["zip_file"]), "rb") as r:
                res = requests.post("http://api:6000/models/",
                                    params=params,
                                    files={"zip_file": r}
                                    )
