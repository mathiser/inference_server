from fastapi import FastAPI, File, UploadFile, HTTPException
from starlette.responses import FileResponse

import logging
import os
import secrets
from datetime import datetime
from init_db import Session, input_base_folder, output_base_folder, database
from init_rabbit import rabbit_channel
from models import Task

logging.basicConfig(filename='api.log', encoding='utf-8', level=logging.INFO)

app = FastAPI()

@app.on_event("startup")
async def startup():
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


@app.get("/")
def hello_world():
    print("Hello world - Welcome to the private database API")
    return {"message": "Hello world - Welcome to the private database API"}

######## TASKS #########

@app.get("/tasks/")
async def get_tasks():
    with Session() as s:
        tasks = s.query(Task)
        return list(tasks)

@app.get("/tasks/{id}")
async def get_task_by_id(id: int):
    with Session() as s:
        return s.query(Task).filter_by(id=id).first()

@app.get("/tasks/uid/{uid}")
async def get_task_by_uid(uid: str):
    with Session() as s:
        return s.query(Task).filter_by(uid=uid).first()



######## INPUTS ########
######## PUBLIC ########
@app.post("/inputs/")
async def upload_input(container_tag: str, model: str, file: UploadFile = File(...)):
    # Give this request a unique identifier
    uid = secrets.token_urlsafe(32)

    print(f"Received a task to run on {container_tag}")

    # Define input folder and output folder
    input_folder = os.path.abspath(os.path.join(input_base_folder, uid))
    input_zip = os.path.join(input_folder, "input.zip")
    output_folder = os.path.abspath(os.path.join(output_base_folder, uid))
    output_zip = os.path.join(output_folder, "output.zip")

    print(f"Input_zip: {input_zip}")
    print(f"Output_zip: {output_zip}")
    print(f"uid: {uid}")

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
             model=model,
             input_zip=input_zip,
             output_zip=output_zip)

    # Open db session and add task
    with Session() as s:
        s.add(t)
        s.commit()
        s.refresh(t)

    # Publish the task in os.environ["UNFINISHED_JOB_QUEUE"]
    rabbit_channel.basic_publish(exchange="", routing_key=os.environ["UNFINISHED_JOB_QUEUE"], body=t.uid)

    return t


@app.get("/inputs/{id}")
async def get_image_zip(id: int):
    with Session() as s:
        t = s.query(Task).filter_by(id=id).first()
    print(t.__dict__)
    print(os.path.exists(t.input_zip))
    if os.path.exists(t.input_zip):
        return FileResponse(t.input_zip)
    else:
        raise HTTPException(status_code=404, detail="Input zip not found")


######## OUTPUTS ########
@app.post("/outputs/{id}")
async def upload_output(id: int, file: UploadFile = File(...)):
    with Session() as s:
        # Get the task
        t = s.query(Task).filter_by(id=id).first()

        # Extract uploaded zipfile to output_zip_path
        with open(t.output_zip, 'wb') as out_file:
            out_file.write(file.file.read())

        # Publish the finished job to "finished_jobs"
        rabbit_channel.basic_publish(exchange="", routing_key=os.environ["FINISHED_JOB_QUEUE"], body=t.uid)

        # Set task as finished and finished_datetime
        t.is_fininished = True
        t.datetime_finished = datetime.utcnow()

        # Save changes
        s.commit()
        s.refresh(t)
        return t

######## PUBLIC ########
@app.get("/outputs/{id}")
async def get_output_zip(id: int):
    # Zip the output for return
    with Session() as s:
        task = s.query(Task).filter_by(id=id).first

        if not task:
            raise HTTPException(status_code=404, detail="Invalid UID")
        try:
            if task.is_finished:  ## Not doing this with os.path.exists(task.output.zip) to avoid that some of the file is sent before all written
                return FileResponse(task.output_zip)
            else:
                raise HTTPException(status_code=404, detail="Output zip not found")
        except Exception as e:
            raise HTTPException(status_code=404, detail=e)
