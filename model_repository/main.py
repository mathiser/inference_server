import json
import os
import docker
import requests

cli = docker.from_env()
models = requests.get("http://api:6000/models/").json()
model_container_tags = [d["container_tag"] for d in models]
try:
    for fol, subs, files in os.walk("./models"):
        for f in sorted(files):
            if f.endswith(".json"):
                detail_file_path = os.path.join(fol, f)

                with open(detail_file_path, "r") as r:
                    model_details = json.loads(r.read())

                print(f"building: {model_details['container_tag']}")
                print(cli.images.build(path=os.path.join(os.path.dirname(detail_file_path), "img"),
                                 tag=model_details["container_tag"]))

                if model_details["container_tag"] in model_container_tags:
                    print(f"container_tag already exist - change if you intend to make new model: {model_details}")
                    continue
                print(f"inserting model: {model_details}")
                if "zip_file" in model_details.keys():
                    with open(os.path.join(fol, model_details["zip_file"]), "rb") as r:
                        res = requests.post("http://api:6000/models/",
                                            params=model_details,
                                            files={"zip_file": r}
                                            )
                else:
                    res = requests.post("http://api:6000/models/",
                                        params=model_details)

except Exception as e:
    cli.close()
    print(e)