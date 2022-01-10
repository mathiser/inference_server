import atexit
import json
import logging
import os
import secrets
import threading
from typing import Optional
from urllib.parse import urljoin

import requests
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse
app = FastAPI()

threads = []


@app.get("/")
def hello_world():
    logging.info("Hello world - Welcome to the public database API")
    return {"message": "Hello world - Welcome to the public database API"}

@app.post(urljoin(os.environ['PUBLIC_POST_TASK_BY_MODEL_ID'], "{model_id}"))
async def public_post_task_by_model_id(model_id: int, zip_file: UploadFile = File(...)):
    # Give this request a unique identifier
    def post_task_thread(url, file_obj, params):
        return requests.post(url, files={"zip_file": file_obj}, params=params)

    uid = secrets.token_urlsafe(32)
    params = {
        "model_id": model_id,
        "uid": uid
    }
    url = os.environ['API_URL'] + os.environ.get("POST_TASK_BY_MODEL_ID")
    t = threading.Thread(target=post_task_thread, args=(url, zip_file.file, params))
    t.start()
    threads.append(t)

    return {"id": uid}

@app.get(urljoin(os.environ['PUBLIC_GET_OUTPUT_ZIP_BY_UID'], "{uid}"))
async def get_output_zip_by_uid(uid: str):
    # Zip the output for return
    res = requests.get(urljoin(os.environ['GET_OUTPUT_ZIP_BY_UID'], f"{uid}"), stream=True)
    def iterfile():
        for chunk in res.iter_content():
            yield chunk
    if res.ok:
        return StreamingResponse(iterfile())
    else:
        return res.content


######## MODELS ########
@app.post(os.environ['PUBLIC_POST_MODEL'])
async def post_model(container_tag: str,
                     input_mountpoint: str,
                     output_mountpoint: str,
                     model_mountpoint: Optional[str] = None,
                     description: Optional[str] = None,
                     zip_file: UploadFile = File(...),
                     model_available: Optional[bool] = True,
                     use_gpu: Optional[bool] = True,
                     ):

    uid = secrets.token_urlsafe(32)
    params = {
        "description": description,
        "container_tag": container_tag,
        "input_mountpoint": input_mountpoint,
        "output_mountpoint": output_mountpoint,
        "model_mountpoint": model_mountpoint,
        "use_gpu": use_gpu,
        "model_available": model_available
    }

    url = os.environ["API_URL"] + os.environ["POST_MODEL"]
    res = requests.post(url, files={"zip_file": zip_file}, params=params)

    return dict(json.loads(res.content))

def on_exit():
    for t in threads:
        t.join()

atexit.register(on_exit)