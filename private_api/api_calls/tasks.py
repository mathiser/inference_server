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


