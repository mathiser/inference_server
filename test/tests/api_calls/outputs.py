import os
import requests
from  urllib.parse import urljoin
import json

def post_output_by_uid(uid: str, file_like_obj):
    res = requests.post(os.environ["API_URL"] + urljoin(os.environ['POST_OUTPUT_BY_UID'], uid),
                      files={"file": file_like_obj})

    return res

def get_output_by_id(id: int):
    res = requests.get(os.environ["API_URL"] + urljoin(os.environ["GET_OUTPUT_BY_ID"], id))
    return res.content
