import atexit
import json
import logging
import os
import secrets
import tempfile
import threading
from typing import Optional, List
from urllib.parse import urljoin

import requests
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
app = FastAPI()

threads = []

LOG_FORMAT = ('%(levelname)s:%(asctime)s:%(message)s')
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)

@app.get("/")
def hello_world():
    logging.info("Hello world - Welcome to the public database API")
    return {"message": "Hello world - Welcome to the public database API"}

@app.post(os.environ['PUBLIC_POST_TASK'])
def public_post_task(models: List[int],
                     zip_file: UploadFile = File(...)):
    logging.info(f"Task with models: {models}")

    # Give this request a unique identifier
    def post_task_thread(url, zip_file_from_res, params):
            res = requests.post(url, files={"zip_file": zip_file_from_res}, params=params)
            logging.info(res.content)
            logging.info("Finished running post_task")

    uid = secrets.token_urlsafe(32)
    params = {
        "models": models,
        "uid": uid
    }
    url = os.environ['API_URL'] + os.environ.get("POST_TASK")
    t = threading.Thread(target=post_task_thread, args=(url, zip_file.file, params))
    t.start()
    threads.append(t)

    return {"uid": uid}

@app.get(urljoin(os.environ['PUBLIC_GET_OUTPUT_ZIP_BY_UID'], "{uid}"))
def get_output_zip_by_uid(uid: str):
    # Zip the output for return
    url = os.environ.get("API_URL") + urljoin(os.environ['GET_OUTPUT_ZIP_BY_UID'], f"{uid}")
    res = requests.get(url, stream=True)
    if res.ok:
        def iterfile():
            with tempfile.TemporaryFile() as tmp_file:
                for chunk in res.iter_content(1000000):
                    tmp_file.write(chunk)
                tmp_file.seek(0)

                yield from tmp_file

        return StreamingResponse(iterfile())
    else:
        c = dict(json.loads(res.content))
        raise HTTPException(status_code=res.status_code, detail=c["detail"])

@app.get(os.environ["PUBLIC_GET_MODELS"])
def get_models():
    url = os.environ["API_URL"] + os.environ["GET_MODELS"]
    res = requests.get(url)
    return json.loads(res.content)

######## MODELS ########
#@app.post(os.environ['PUBLIC_POST_MODEL']) This is deprecated already.
# It should not be possible to upload models from public api. At least for now.
def post_model(container_tag: str,
                     input_mountpoint: str,
                     output_mountpoint: str,
                     model_mountpoint: Optional[str] = None,
                     description: Optional[str] = None,
                     zip_file: UploadFile = File(...),
                     model_available: Optional[bool] = True,
                     use_gpu: Optional[bool] = True,
                     ):
    params = {
        "description": description,
        "container_tag": container_tag,
        "input_mountpoint": input_mountpoint,
        "output_mountpoint": output_mountpoint,
        "model_mountpoint": model_mountpoint,
        "use_gpu": use_gpu,
        "model_available": model_available,
    }

    url = os.environ["API_URL"] + os.environ["POST_MODEL"]
    res = requests.post(url, files={"zip_file": zip_file.file}, params=params)
    model = dict(json.loads(res.content))

    return {
        "id": model["id"],
        "container_tag": model["container_tag"],
        "input_mountpoint": model["input_mountpoint"],
        "output_mountpoint": model["output_mountpoint"],
        "model_mountpoint": model["model_mountpoint"],
        "description": model["description"],
        "model_available": model["model_available"],
        "use_gpu": model["use_gpu"]
    }

def on_exit():
    for t in threads:
        t.join()

atexit.register(on_exit)