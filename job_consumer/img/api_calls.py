import json
import os
from urllib.parse import urljoin

import requests


def get_task_by_uid(uid):
    res = requests.get(os.environ["API_URL"] + urljoin(os.environ["GET_TASK_BY_UID"], uid))
    return dict(json.loads(res.content))


def get_input_by_id(id: int):
    res = requests.get(os.environ["API_URL"] + urljoin(os.environ["GET_TASK_BY_ID"], str(id)))
    return res.content


def get_model_by_id(id: int):
    res = requests.get(os.environ["API_URL"] + urljoin(os.environ["GET_MODEL_BY_ID"], str(id)))
    return dict(json.loads(res.content))


def post_output_by_uid(uid: str, file_like_obj):
    res = requests.post(os.environ["API_URL"] + urljoin(os.environ['POST_OUTPUT_BY_UID'], uid),
                        files={"file": file_like_obj})

    return res
