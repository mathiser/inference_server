from urllib.parse import urljoin

import requests
import os
import json

def get_private_hello_world():
    res = requests.get(os.environ["API_URL"])
    return dict(json.loads(res.content))

def get_task_by_uid(uid):
    res = requests.get(os.environ["API_URL"] + urljoin(os.environ["GET_TASK_BY_UID"], uid))
    return dict(json.loads(res.content))

def get_task_by_id(id):
    res = requests.get(os.environ["API_URL"] + urljoin(os.environ["GET_TASK_BY_ID"], id))
    return dict(json.loads(res.content))

def get_tasks(): ## NOT TESTED
    res = requests.get(os.environ["API_URL"] + os.environ["GET_TASKS"])
    return dict(json.loads(res.content))

def post_task_by_model_id(model_id: int, file):
    res = requests.post(os.environ["API_URL"] + urljoin(os.environ["POST_TASK_BY_MODEL_ID"], model_id),
                      files={"file": file})
    return res

def get_input_by_id(id):
    res = requests.get(os.environ["API_URL"] + urljoin(os.environ["GET_TASK_BY_ID"], id))
    return res.content

def post_output_by_uid(uid: str, file_like_obj):
    res = requests.post(os.environ["API_URL"] + urljoin(os.environ['POST_OUTPUT_BY_UID'], uid),
                      files={"file": file_like_obj})

    return res

def get_output_by_id(id: int):
    res = requests.get(os.environ["API_URL"] + urljoin(os.environ["GET_OUTPUT_BY_ID"], id))
    return res.content


def post_model(container_tag: str,
               input_mountpoint: str,
               output_mountpoint: str,
               description: str = None,
               model_mountpoint: str = None,
               model_zip=None):

    params = {
        "description": description,
        "container_tag": container_tag,
        "input_mountpoint": input_mountpoint,
        "output_mountpoint": output_mountpoint,
        "model_mountpoint": model_mountpoint
    }
    res = requests.post(os.environ["API_URL"] + os.environ["POST_MODEL"], params=params,
                      files={"file": model_zip})

    return res