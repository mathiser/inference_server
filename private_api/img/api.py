from typing import Optional
from urllib.parse import urljoin

from fastapi import FastAPI, File, UploadFile, HTTPException, status
from starlette.responses import FileResponse
import tempfile
import logging
import os
import secrets
from datetime import datetime
from init_db import Session, input_base_folder, output_base_folder, database
from disposable_rabbit_connection import DisposablePikaConnection
from models import Task, Model
import zipfile
LOG_FORMAT = ('%(levelname) -10s %(asctime)s %(name) -30s %(funcName) '
              '-35s %(lineno) -5d: %(message)s')
LOGGER = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
app = FastAPI()

@app.on_event("startup")
async def startup():
    logging.info("Connecting to DB")
    await database.connect()
    logging.info("Connecting to DB successful")


@app.on_event("shutdown")
async def shutdown():
    logging.info("Disonnecting from DB")
    await database.disconnect()
    logging.info("Disconnecting from DB sucessful")

@app.get("/")
def hello_world():
    logging.info("Hello world - Welcome to the private database API")
    return {"message": "Hello world - Welcome to the private database API"}

######## TASKS #########
@app.get(os.environ["GET_TASKS"])
async def get_tasks():
    with Session() as s:
        tasks = s.query(Task)
        return list(tasks)

@app.get(urljoin(os.environ['GET_TASKS_BY_ID'], "{id}"))
async def get_task_by_id(id: int):
    with Session() as s:
        return s.query(Task).filter_by(id=id).first()

@app.get(urljoin(os.environ['GET_TASKS_BY_UID'], "{uid}"))
async def get_task_by_uid(uid: str):
    with Session() as s:
        return s.query(Task).filter_by(uid=uid).first()



######## INPUTS ########
######## PUBLIC ########
@app.post(os.environ['POST_TASK_BY_MODEL_ID'])
async def post_task_by_model_id(model_id: int, file: UploadFile = File(...)):
    # Give this request a unique identifier
    uid = secrets.token_urlsafe(32)

    logging.info(f"{uid}: Received a task with model_id: {model_id}")

    logging.info("{uid}: Define input folder and output folders")
    input_folder = os.path.abspath(os.path.join(input_base_folder, uid))
    input_zip = os.path.join(input_folder, "input.zip")
    output_folder = os.path.abspath(os.path.join(output_base_folder, uid))
    output_zip = os.path.join(output_folder, "output.zip")

    logging.info(f"{uid}: Input_zip: {input_zip}")
    logging.info(f"{uid}: Output_zip: {output_zip}")

    # Create input and output folders
    for p in [input_folder, output_folder]:
        if not os.path.exists(p):
            os.makedirs(p)
        else:
            logging.error(f"{uid}: Error when creating {input_folder} and {output_folder}."
                          f" They appear to exist for a two different tasks")
            raise Exception(f"{uid}: Two tasks with same UID!?")

    logging.info(f"{uid}: Extract uploaded zipfile to input_folder")
    with open(input_zip, 'wb') as out_file:
        out_file.write(file.file.read())

    logging.info(f"{uid}: Define the DB-entry for the task")
    t = Task(uid=uid,
             model_id=model_id,
             input_zip=input_zip,
             output_zip=output_zip)
    logging.info(f"{uid}: Task: {t.__dict__}")

    logging.info(f"{uid}: Open db session and add task")
    with Session() as s:
        s.add(t)
        s.commit()
        s.refresh(t)

    logging.info(f'{uid}: Publish the task in os.environ["UNFINISHED_JOB_QUEUE"]')
    DisposablePikaConnection(exchange="", queue=os.environ["UNFINISHED_JOB_QUEUE"], body=t.uid, uid=t.uid,
                             host=os.environ["RABBIT_HOST"])

    return t


@app.get(urljoin(os.environ['GET_INPUT_BY_ID'], "{id}"))
async def get_input_by_id(id: int):
    with Session() as s:
        t = s.query(Task).filter_by(id=id).first()
    if os.path.exists(t.input_zip):
        return FileResponse(t.input_zip)
    else:
        raise HTTPException(status_code=404, detail="Input zip not found")


######## OUTPUTS ########
@app.post(urljoin(os.environ['POST_OUTPUT_BY_UID'], "{uid}"))
async def post_output_by_uid(uid: str, file: UploadFile = File(...)):
    with Session() as s:
        # Get the task
        t = s.query(Task).filter_by(uid=uid).first()

        # Extract uploaded zipfile to output_zip_path
        with open(t.output_zip, 'wb') as out_file:
            out_file.write(file.file.read())

        # Publish the finished job to "finished_jobs"
        DisposablePikaConnection(exchange="", queue=os.environ["FINISHED_JOB_QUEUE"], body=t.uid, uid=t.uid, host=os.environ["RABBIT_HOST"])

        # Set task as finished and finished_datetime
        t.is_finished = True
        t.datetime_finished = datetime.utcnow()

        # Save changes
        s.commit()
        s.refresh(t)
        return t

######## PUBLIC ########
@app.get(urljoin(os.environ['GET_OUTPUT_BY_ID'], "{id}"))
async def get_output_by_id(id: int):
    # Zip the output for return
    with Session() as s:
        task = s.query(Task).filter_by(id=id).first()

        if task.is_finished:  ## Not doing this with os.path.exists(task.output.zip) to avoid that some of the file is sent before all written
            return FileResponse(task.output_zip)
        else:
            raise HTTPException(status_code=404, detail="Output zip not found - this is normal behavior if you are polling for an output")


@app.get(urljoin(os.environ['GET_TASKS_BY_ID'], "{id}"))
async def get_task_by_id(id: int):
    with Session() as s:
        return s.query(Task).filter_by(id=id).first()

@app.get(urljoin(os.environ['GET_TASKS_BY_UID'], "{uid}"))
async def get_task_by_uid(uid: str):
    with Session() as s:
        return s.query(Task).filter_by(uid=uid).first()



######## MODELS ########
@app.post(os.environ['POST_MODEL'])
async def post_model(description: Optional[str],
                     container_tag: str,
                     input_mountpoint: str,
                     output_mountpoint: str,
                     model_mountpoint: Optional[str],
                     file: UploadFile = File(...)):

    """
    :param description: description of model
    :param container_tag: docker tag to use
    :param input_mountpoint: path to where the docker container expects the input folder to be mounted
    :param output_mountpoint: path to where the docker container dumps output
    :param model_mountpoint: path to where the docker container expects the a model to be located. optional
    :param file:
    :return:
    """

    uid = secrets.token_urlsafe(32)
    model_path = os.path.join(os.environ["MODELS_DIR"], uid)

    # Create model_path
    if not os.path.exists(model_path):
        os.makedirs(model_path)
    else:
        raise Exception(f"{uid}: Two models with same UID!?")

    m = Model(
        uid=uid,
        description=description,
        container_tag=container_tag,
        model_path=model_path,
        input_mountpoint=input_mountpoint,
        output_mountpoint=output_mountpoint,
        model_mountpoint=model_mountpoint
    )

    ## Add model to DB
    with Session() as s:
        s.add(m)
        s.commit()
        s.refresh(m)

    # Extract model_zip to model_path. This path serves as the source for model_mountpoint in the container
    with tempfile.TemporaryFile() as tmp_model_file:
        # Write UploadFile to tmp_model_file
        tmp_model_file.write(file.file.read())

        # Extract tmp_model_file to model_path
        with zipfile.ZipFile(tmp_model_file, "r") as zip:
            zip.extractall(path=model_path)

    return m
