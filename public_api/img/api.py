from fastapi import FastAPI, UploadFile, File

import httpx as httpx
import logging
import os
from pydantic import BaseModel
from urllib.parse import urljoin

app = FastAPI()


class Task(BaseModel):
    tag: str
    model: str

@app.get("/")
def hello_world():
    logging.info("Hello world - Welcome to the public database API")
    return {"message": "Hello world - Welcome to the public database API"}

@app.post("/api/inputs/")
async def upload_input(container_tag: str, model: str, file: UploadFile = File(...)):
    # Give this request a unique identifier
    async with httpx.AsyncClient() as client:
        res = await client.post(urljoin(os.environ['API_URL'], "/inputs/"),
                    params={"container_tag": container_tag,
                            "model": model},
                    files={"file": file})

    return res.content
@app.get("/api/tasks/{uid}")
async def get_task(uid: str):
    async with httpx.AsyncClient() as client:
        res = await client.get(urljoin(os.environ['API_URL'], f"/output/uid/{uid}"))
        return res.content