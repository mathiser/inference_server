import os
from urllib.parse import urljoin
import json
import requests


def post_model(container_tag: str,
               input_mountpoint: str,
               output_mountpoint: str,
               description: str = None,
               model_mountpoint: str = None,
               zip_file=None,
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
    res = requests.post(os.environ["API_URL"] + os.environ["POST_MODEL"], params=params,
                        files={"zip_file": zip_file})

    return res


def get_model_by_id(id: int):
    res = requests.get(os.environ["API_URL"] + urljoin(os.environ["GET_MODEL_BY_ID"], str(id)))
    return dict(json.loads(res.content))


def get_model_by_uid(uid: str):
    res = requests.get(os.environ["API_URL"] + urljoin(os.environ["GET_MODEL_BY_UID"], uid))
    return dict(json.loads(res.content))

def get_model_zip_by_id(id: int):
    yield requests.get(os.environ["API_URL"] + urljoin(os.environ["GET_MODEL_ZIP_BY_ID"], str(id)), stream=True)


def get_model_zip_by_uid(uid: str):
    yield requests.get(os.environ["API_URL"] + urljoin(os.environ["GET_MODEL_ZIP_BY_UID"], uid), stream=True)