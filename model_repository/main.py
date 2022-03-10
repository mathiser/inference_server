import json
import os
from pprint import pprint

import docker
import requests

class Model:
    def __init__(self, path, docker_cli):
        self.path = path
        self.cli = docker_cli
        for f in os.listdir(self.path):
            fpath = os.path.join(self.path, f)
            if fpath.endswith(".json"):
                self.detail_file_path = fpath
                break
        else:
            raise Exception(f"No json meta file found in {path}")

        with open(self.detail_file_path, "r") as r:
            self.model_details = json.loads(r.read())

        pprint(self.__dict__)

    def build_docker_image(self):
        print(f"building: {self.model_details['container_tag']}")
        image = self.cli.images.build(path=os.path.join(self.path, self.model_details["docker_image_context"]),
                                      tag=self.model_details["container_tag"])


cli = docker.from_env()
models = requests.get("http://api:6000/models/").json()
server_human_readable_ids = [d["human_readable_id"] for d in models]

try:
    for f in os.listdir("/models"):
        path = os.path.join("/models", f)
        if os.path.isdir(path):
            model = Model(path, cli)
            if model.model_details["human_readable_id"] in server_human_readable_ids:
                model.build_docker_image()
                print(f"Rebuilding docker image, but model_zip stays the same - change human_readable_id if you intend to make new model: {model.model_details}")
                continue
            else:
                print(f"inserting model: {model.model_details}")
                if "zip_file" in model.model_details.keys():
                    with open(os.path.join(model.path, model.model_details["zip_file"]), "rb") as r:
                        res = requests.post("http://api:6000/models/",
                                            params=model.model_details,
                                            files={"zip_file": r}
                                            )
                else:
                    res = requests.post("http://api:6000/models/",
                                        params=model.model_details)

except Exception as e:
    cli.close()
    print(e)