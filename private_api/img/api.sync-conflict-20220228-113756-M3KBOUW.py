import logging
import os
import secrets
import uuid
from datetime import datetime
from typing import Optional, List
from urllib.parse import urljoin

import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from starlette.responses import FileResponse

from db import Session, input_base_folder, output_base_folder, model_base_folder, database
from disposable_rabbit_connection import DisposablePikaConnection
from models import Task, Model

LOG_FORMAT = '%(levelname)s:%(asctime)s:%(message)s'

logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
app = FastAPI()

@app.on_event("startup")
def startup():
    logging.info("Connecting to DB")
    database.connect()
    logging.info("Connecting to DB successful")


@app.on_event("shutdown")
def shutdown():
    logging.info("Disonnecting from DB")
    database.disconnect()
    logging.info("Disconnecting from DB sucessful")

@app.get("/")
def hello_world():
    logging.info("Hello world - Welcome to the private database API")
    return {"message": "Hello world - Welcome to the private database API"}

######## TASKS #########
@app.get(os.environ["GET_TASKS"])
def get_tasks():
    with Session() as s:
        tasks = s.query(Task)
        return list(tasks)

@app.get(urljoin(os.environ['GET_TASK_BY_ID'], "{id}"))
def get_task_by_id(id: int):
    with Session() as s:
        return s.query(Task).filter_by(id=id).first()

@app.get(urljoin(os.environ['GET_TASK_BY_UID'], "{uid}"))
def get_task_by_uid(uid: str):
    with Session() as s:
        return s.query(Task).filter_by(uid=uid).first()



######## INPUTS ########
######## PUBLIC ########
@app.post(os.environ['POST_TASK'])
def post_task(model_ids: List[int] = Query(None),
                    zip_file: UploadFile = File(...),
                    uid=None) -> Task:
    """
    Method receives a posted task. Saves it appropriately, adds it to the DB and publishes it in job queue
    for unfinished jobs to be consumed by job-consumers.
    :param model_ids: List of model ids to be stacked.
    :param zip_file: Zip with task input zip.
    :param uid: UID provided by public-api - else none.
    :return:
    """
    # A task must have a model to run on.
    if not (len(model_ids) >= 1):
        raise HTTPException(404, "Task must have at least ONE model - try again")

    for model in model_ids:
        if not get_model_by_id(model):
            raise HTTPException(404, f"Model id '{model}' does not exist")

    # Create UID if None. UID exists if task comes from public_api. If directly on the private_api this is used.
    if not uid:
        uid = secrets.token_urlsafe(32)

    logging.info(f"{uid}: Received a task with model_ids: {model_ids}")

    # Define input and output that serve the user
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
    # Save the uploaded zip to the declared input_zip
    with open(input_zip, 'wb') as out_file:
        out_file.write(zip_file.file.read())

    logging.info(f"{uid}: Define the DB-entry for the task")
    # Create the task to be saved in the DB
    t = Task(uid=uid,
             input_zip=input_zip,
             output_zip=output_zip,
             model_ids=model_ids
             )
    logging.info(f"{uid}: Task: {t.__dict__}")

    logging.info(f"{uid}: Open db session and add task")
    # Open DB, add task and commit.
    with Session() as s:
        s.add(t)
        s.commit()
        s.refresh(t)

    logging.info(f'{uid}: Publish the task in os.environ["UNFINISHED_JOB_QUEUE"]')

    # Publish the newly arrived task in unfinished tasks queue. The body is the uid of the task
    DisposablePikaConnection(exchange="", queue=os.environ["UNFINISHED_JOB_QUEUE"], body=t.uid,
                             host=os.environ["RABBIT_HOST"])

    return t


@app.get(urljoin(os.environ['GET_INPUT_ZIP_BY_ID'], "{id}"))
def get_input_zip_by_id(id: int) -> FileResponse:
    with Session() as s:
        t = s.query(Task).filter_by(id=id).first()

    if os.path.exists(t.input_zip):
        return FileResponse(t.input_zip)
    else:
        raise HTTPException(status_code=404, detail="Input zip not found - try posting task again")


######## OUTPUTS ########
@app.post(urljoin(os.environ['POST_OUTPUT_ZIP_BY_UID'], "{uid}"))
def post_output_by_uid(uid: str, zip_file: UploadFile = File(...)) -> Task:
    """
    Method receives an output of a task from the job-consumer. It places the zip locally and stores the location, so it can
    be served to a user.
    :param uid: Task uid
    :param zip_file: Output zip file
    :return: Task
    """
    with Session() as s:
        # Get the task
        t = s.query(Task).filter_by(uid=uid).first()

        # Write zip_file to task.output_zip
        with open(t.output_zip, 'wb') as out_file:
            out_file.write(zip_file.file.read())

        # Set task as finished and finished_datetime
        t.is_finished = True
        t.datetime_finished = datetime.utcnow()

        # Save changes
        s.commit()
        s.refresh(t)

        # Publish the finished job to "finished_jobs"
        DisposablePikaConnection(exchange="", queue=os.environ["FINISHED_JOB_QUEUE"], body=t.uid, uid=t.uid, host=os.environ["RABBIT_HOST"])

        return t

######## PUBLIC ########
@app.get(urljoin(os.environ['GET_OUTPUT_ZIP_BY_UID'], "{uid}"))
def get_output_zip_by_uid(uid: str) -> FileResponse:
    # Zip the output for return
    with Session() as s:
        task = s.query(Task).filter_by(uid=uid).first()
        if task is None:
            raise HTTPException(status_code=404,
                                detail="Task not in DB yet. If you very recently uploaded it - or uploaded a very large file - try again in a moment")

        if task.is_finished:  ## Not doing this with os.path.exists(task.output.zip) to avoid that some of the file is sent before all written
            return FileResponse(task.output_zip)
        else:
            raise HTTPException(status_code=404, detail="Output zip not found - this is normal behavior if you are polling for an output")


@app.get(urljoin(os.environ['GET_TASK_BY_ID'], "{id}"))
def get_task_by_id(id: int) -> Task:
    with Session() as s:
        return s.query(Task).filter_by(id=id).first()

@app.get(urljoin(os.environ['GET_TASK_BY_UID'], "{uid}"))
def get_task_by_uid(uid: str) -> Task:
    with Session() as s:
        return s.query(Task).filter_by(uid=uid).first()



######## MODELS ########
@app.post(os.environ['POST_MODEL'])
def post_model(container_tag: str,
                     input_mountpoint: str,
                     output_mountpoint: str,
                     model_mountpoint: Optional[str] = None,
                     description: Optional[str] = None,
                     zip_file: Optional[UploadFile] = File(None),
                     model_available: Optional[bool] = True,
                     use_gpu: Optional[bool] = True,
                     ) -> Model:

    """
    :param description: description of model
    :param container_tag: docker tag to use
    :param input_mountpoint: path to where the docker container expects the input folder to be mounted
    :param output_mountpoint: path to where the docker container dumps output
    :param model_mountpoint: path to where the docker container expects the a model to be located. optional
    :param zip_file: zip file with model content inside.
    :param model_available: set to False if model volume is not used
    :param use_gpu: Set True if model requires GPU and to False if CPU only. Will eventually become two queues
    :return: Returns the dict of the model updated from DB
    """

    # Create new uid for the model. Models can for now only be added directly on the private_api.
    uid = secrets.token_urlsafe(32)

    # Initiate variables
    model_zip = None
    model_volume = None
    if model_available: ## User set if a model zip is provided and used.
        model_zip = os.path.join(model_base_folder, uid, "model.zip")
        model_volume = str(uuid.uuid4())

        # Create model_path
        if not os.path.exists(os.path.dirname(model_zip)):
            os.makedirs(os.path.dirname(model_zip))
        else:
            raise Exception(f"{uid}: Two models with same UID!?")

        # write model_zip to model_zip
        with open(model_zip, 'wb') as f:
            f.write(zip_file.file.read())

    # Model for the DB
    m = Model(
        description=description,
        container_tag=container_tag,
        model_zip=model_zip,
        model_volume=model_volume,
        input_mountpoint=input_mountpoint,
        output_mountpoint=output_mountpoint,
        model_mountpoint=model_mountpoint,
        model_available=model_available,
        use_gpu=use_gpu
    )

    ## Add model to DB
    with Session() as s:
        s.add(m)
        s.commit()
        s.refresh(m)

    return m

@app.get(urljoin(os.environ['GET_MODEL_BY_ID'], "{id}"))
def get_model_by_id(id: int) -> Model:
    with Session() as s:
        return s.query(Model).filter_by(id=id).first()

@app.get(os.environ['GET_MODELS'])
def get_models() -> List[Model]:
    with Session() as s:
        return list(s.query(Model))

@app.get(urljoin(os.environ['GET_MODEL_ZIP_BY_ID'], "{id}"))
def get_model_zip_by_id(id: int) -> FileResponse:
    with Session() as s:
        m = s.query(Model).filter_by(id=id).first()

    if os.path.exists(m.model_zip):
        return FileResponse(m.model_zip)
    else:
        raise HTTPException(status_code=404, detail="Model zip not found - try posting task again")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=os.environ.get("API_PORT"))