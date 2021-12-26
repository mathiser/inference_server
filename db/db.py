import os
import secrets
from datetime import datetime
from urllib.parse import unquote

from fastapi import FastAPI, File, UploadFile, HTTPException
from starlette.responses import FileResponse

from init_db import Session, input_base_folder, output_base_folder
from init_rabbit import rabbit_channel
from models import Task

app = FastAPI()


@app.get("/")
def hello_world():
    return {"message": "Hello world - Welcome to the private database API"}


@app.post("/tasks/{container_tag}")
def upload_file(container_tag: str, file: UploadFile = File(...)):
    # Give this request a unique identifier
    uid = secrets.token_urlsafe(32)

    # Decode url encoded container_tag
    container_tag = unquote(container_tag)

    # Define input folder and output folder
    input_folder = os.path.abspath(os.path.join(input_base_folder, uid))
    input_zip = os.path.join(input_folder, "input.zip")
    output_folder = os.path.abspath(os.path.join(output_base_folder, uid))
    output_zip = os.path.join(output_folder, "output.zip")

    # Create input and output folders
    for p in [input_folder, output_folder]:
        if not os.path.exists(p):
            os.makedirs(p)
        else:
            raise Exception("Two tasks with same UID!?")

    # Extract uploaded zipfile to input_folder
    with open(input_zip, 'wb') as out_file:
        out_file.write(file.file.read())

    # Define the DB-entry for the task
    t = Task(uid=uid,
             container_tag=container_tag,
             image_zip=input_zip,
             prediction_zip=output_zip,
             )

    # Publish the task in "container_jobs"
    rabbit_channel.basic_publish(exchange="", routing_key="container_jobs", body=t.id)

    # Add the task to DB and commit changes
    with Session() as s:
        s.add(t)
        s.commit()
        return t.id

@app.get("/tasks/{id}")
def get_task(id: int):
    with Session() as s:
        t = s.query(Task).filter_by(id=id).first()
        return t

@app.get("/tasks/")
def get_tasks():
    with Session() as s:
        tasks = s.query(Task)
        return list(tasks)

# Function to mark datetime started
@app.get("/tasks/started/{id}")
def get_tasks(id: int):
    with Session() as s:
        t = s.query(Task).filter_by(id=id).first()
        t.datetime_started = datetime.utcnow()
        s.commit()
        return t


@app.post("/outputs/")
def upload_output(id: int, file: UploadFile = File(...)):
    with Session() as s:
        # Get the task
        t = s.query(Task).filter_by(id=id).first()

        # Extract uploaded zipfile to output_zip_path
        with open(t.output_zip, 'wb') as out_file:
            out_file.write(file.file.read())

        # Publish the finished job to "finished_jobs"
        rabbit_channel.basic_publish(exchange="", routing_key="finished_jobs", body=id)

        # Set task as finished and finished_datetime
        t.is_fininished = True
        t.datetime_finished = datetime.utcnow()

        # Save changes
        s.commit()
        return t.id


@app.get("/outputs/{id}")
def get_output_zip(id: int):
    # Zip the output for return
    task = get_task(id)
    if task.is_finished: ## Not doing this with os.path.exists(task.output.zip) to avoid that some of the file is sent before all written
        return FileResponse(task.output_zip)
    else:
        raise HTTPException(status_code=404, detail="Output zip not found")


@app.get("/inputs/{id}")
def get_image_zip(id: int):
    task = get_task(id)
    if os.path.exists(task.input_zip):
        return FileResponse(task.input_zip)
    else:
        raise HTTPException(status_code=404, detail="Input zip not found")
