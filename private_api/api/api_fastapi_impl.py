import logging
import os
from typing import Any, Union
from urllib.parse import urljoin

import dotenv
from database.models import Task, Model
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse

from database.db_interface import DBInterface
from message_queue.mq_interface import MQInterface

LOG_FORMAT = '%(levelname)s:%(asctime)s:%(message)s'

logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)

dotenv.load_dotenv(".env")
class APIFastAPIImpl(FastAPI):
    def __init__(self, db: DBInterface, mq: MQInterface, **extra: Any):
        super().__init__(**extra)
        self.db = db
        self.mq = mq

        @self.get("/")
        def hello_world():
            return {"message": "Hello world - Welcome to the private database API"}

        @self.get(os.environ["GET_TASKS"])
        def get_tasks():
            return self.db.get_tasks()

        @self.get(urljoin(os.environ['GET_TASK_BY_ID'], "{id}"))
        def get_task_by_id(id: int):
            return self.db.get_task_by_id(id=id)

        @self.get(urljoin(os.environ['GET_TASK_BY_UID'], "{uid}"))
        def get_task_by_uid(uid: str):
            return self.db.get_task_by_uid(uid=uid)

        @self.post(os.environ['POST_TASK'])
        def post_task(model_human_readable_id: str,
                      zip_file: Union[UploadFile, None] = None,
                      uid: Union[str, None] = None) -> Task:

            task = self.db.post_task(zip_file=zip_file.file,
                                   model_human_readable_id=model_human_readable_id,
                                   uid=uid)

            self.mq.publish_unfinished_task(task)

            return task

        @self.get(urljoin(os.environ['GET_INPUT_ZIP_BY_ID'], "{id}"))
        def get_input_zip_by_id(id: int) -> FileResponse:
            task = self.db.get_task_by_id(id=id)

            if os.path.exists(task.input_zip):
                return FileResponse(task.input_zip)
            else:
                raise HTTPException(status_code=404, detail="Input zip not found - try posting task again")

        @self.post(urljoin(os.environ['POST_OUTPUT_ZIP_BY_UID'], "{uid}"))
        def post_output_zip_by_uid(uid: str,
                                   zip_file: UploadFile = File(...)) -> Task:

            task = self.db.post_output_zip_by_uid(uid=uid,
                                               zip_file=zip_file.file)
            self.mq.publish_finished_task(task)
            return self.db.post_output_zip_by_uid(uid=uid,
                                               zip_file=zip_file.file)

        @self.get(urljoin(os.environ['GET_OUTPUT_ZIP_BY_UID'], "{uid}"))
        def get_output_zip_by_uid(uid: str):
            # Zip the output for return
            task = self.db.get_task_by_uid(uid=uid)
            if task is None:
                raise HTTPException(status_code=404,
                                    detail="Task not in DB yet. If you very recently uploaded it - or uploaded a very large file - try again in a moment")

            # Not doing this with os.path.exists(task.output.zip) to avoid that some of the file is sent before all written
            if task.is_finished:
                return FileResponse(task.output_zip)
            else:
                raise HTTPException(status_code=404,
                                    detail="Output zip not found - this is normal behavior if you are polling for an output")

        @self.get(urljoin(os.environ['GET_TASK_BY_ID'], "{id}"))
        def get_task_by_id(id: int):
            return self.db.get_task_by_id(id=id)

        @self.get(urljoin(os.environ['GET_TASK_BY_UID'], "{uid}"))
        def get_task_by_uid(uid: str):
            return self.db.get_task_by_uid(uid=uid)

        @self.post(os.environ['POST_MODEL'])
        def post_model(container_tag: str,
                       human_readable_id: str,
                       input_mountpoint: Union[str, None] = None,
                       output_mountpoint: Union[str, None] = None,
                       model_mountpoint: Union[str, None] = None,
                       description: Union[str, None] = None,
                       zip_file: Union[UploadFile, None] = None,
                       model_available: Union[bool, None] = None,
                       use_gpu: Union[bool, None] = None,
                       ) -> Model:
            if zip_file:
                zip_file = zip_file.file

            return self.db.post_model(
                container_tag=container_tag,
                human_readable_id=human_readable_id,
                input_mountpoint=input_mountpoint,
                output_mountpoint=output_mountpoint,
                zip_file=zip_file,
                model_mountpoint=model_mountpoint,
                description=description,
                model_available=model_available,
                use_gpu=use_gpu,
            )

        @self.get(urljoin(os.environ['GET_MODEL_BY_ID'], "{id}"))
        def get_model_by_id(id: int):
            return self.db.get_model_by_id(id=id)

        @self.get(urljoin(os.environ['GET_MODEL_BY_HUMAN_READABLE_ID'], "{human_readable_id}"))
        def get_model_by_human_readable_id(human_readable_id: str):
            return self.db.get_model_by_human_readable_id(human_readable_id=human_readable_id)

        @self.get(os.environ['GET_MODELS'])
        def get_models():
            return self.db.get_models()

        @self.get(urljoin(os.environ['GET_MODEL_ZIP_BY_ID'], "{id}"))
        def get_model_zip_by_id(id: int) -> FileResponse:
            model = self.db.get_model_by_id(id=id)

            if os.path.exists(model.model_zip):
                return FileResponse(model.model_zip)
            else:
                raise HTTPException(status_code=404, detail="Model zip not found - try posting task again")