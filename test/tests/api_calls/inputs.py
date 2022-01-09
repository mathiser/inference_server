import os
from urllib.parse import urljoin

import requests


def get_input_zip_by_id(id: int):
    yield requests.get(os.environ["API_URL"] + urljoin(os.environ["GET_TASK_BY_ID"], str(id)), stream=True)



def post_task_by_model_id(model_id: int, zip_file):
    res = requests.post(os.environ["API_URL"] + urljoin(os.environ["POST_TASK_BY_MODEL_ID"], str(model_id)),
                        files={"zip_file": zip_file})
    return res
