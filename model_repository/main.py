import json
import os
import docker
import requests

cli = docker.from_env()
try:
    for fol, subs, files in os.walk("./models"):
        for f in files:
            if f.endswith(".json"):
                detail_file_path = os.path.join(fol, f)
                with open(detail_file_path, "r") as r:
                    model_details = json.loads(r.read())
                print(model_details)
                if "zip_file" in model_details.keys():
                    with open(os.path.join(fol, model_details["zip_file"]), "rb") as r:
                        res = requests.post("http://api:6000/models/",
                                            params=model_details,
                                            files={"zip_file": r}
                                            )
                else:
                    res = requests.post("http://api:6000/models/",
                                        params=model_details)
                print(f"building: {model_details['container_tag']}")
                cli.images.build(path=os.path.join(os.path.dirname(detail_file_path), "img"),
                                 tag=model_details["container_tag"])
except Exception as e:
    cli.close()
    print(e)