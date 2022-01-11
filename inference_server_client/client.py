import json
from urllib.parse import urljoin

import dotenv
import requests


class Client:
    def __init__(self, envfile):
        self.vars = dotenv.dotenv_values("api_details")
        


    def get_task_output(self, uid: str, dst):
        res = requests.get(self.vars["PUBLIC_API_URL"] + urljoin(self.vars['GET_OUTPUT_ZIP_BY_UID'], uid), stream=True)
        if res.ok:
            with open(dst, "wb") as f:
                for chunk in res.iter_content(chunk_size=1000000):
                    f.write(chunk)
            return True
        else:
            print(json.loads(res.content))
            return False


    def post_task_by_model_id(self, model_id: int, zip_file_path):
        with open(zip_file_path, "rb") as r:
            return requests.post(self.vars["PUBLIC_API_URL"] + urljoin(self.vars["POST_TASK_BY_MODEL_ID"], str(model_id)),
                                 files={"zip_file": r})

    def post_model(self,
                   container_tag: str,
                   input_mountpoint: str,
                   output_mountpoint: str,
                   description: str = None,
                   model_mountpoint: str = None,
                   zip_file_path=None,
                   use_gpu=True,
                   model_available=True):
        params = {
            "description": description,
            "container_tag": container_tag,
            "input_mountpoint": input_mountpoint,
            "output_mountpoint": output_mountpoint,
            "model_mountpoint": model_mountpoint,
            "use_gpu": use_gpu,
            "model_available": model_available
        }
        with open(zip_file_path, "rb") as r:
            return requests.post(self.vars["PUBLIC_API_URL"] + self.vars["POST_MODEL"], params=params,
                                 files={"zip_file": zip_file_path})

    def get_model_details(self, uid: str):
        res = requests.get(self.vars["PUBLIC_API_URL"] + urljoin(self.vars['GET_MODEL_BY_UID'], uid))
        return dict(json.loads(res.content))
