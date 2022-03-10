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
from fastapi import FastAPI, UploadFile, File, HTTPException, Query
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
def public_post_task(human_readable_ids: List[str] = Query(None),
                     zip_file: UploadFile = File(...)):
    logging.info(f"Task with models: {human_readable_ids}")

    # Give this request a unique identifier
    def post_task_thread(url, zip_file_from_res, params):
            res = requests.post(url, files={"zip_file": zip_file_from_res}, params=params)
            logging.info(res.content)
            logging.info("Finished running post_task")

    uid = secrets.token_urlsafe(32)
    params = {
        "human_readable_ids": human_readable_ids,
        "uid": uid
    }
    url = os.environ['API_URL'] + os.environ.get("POST_TASK")
    t = threading.Thread(target=post_task_thread, args=(url, zip_file.file, params))
    t.start()
    threads.append(t)

    return params

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

def on_exit():
    for t in threads:
        t.join()

atexit.register(on_exit)