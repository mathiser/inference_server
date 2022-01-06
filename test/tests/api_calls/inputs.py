import os
from urllib.parse import urljoin

import requests


def get_input_by_id(id: int):
    res = requests.get(os.environ["API_URL"] + urljoin(os.environ["GET_TASK_BY_ID"], str(id)))
    return res.content


def post_task_by_model_id(model_id: int, file):
    res = requests.post(os.environ["API_URL"] + urljoin(os.environ["POST_TASK_BY_MODEL_ID"], str(model_id)),
                        files={"file": file})
    return res
