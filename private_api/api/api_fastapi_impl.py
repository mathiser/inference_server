import logging
import os
import secrets
from typing import Any, Union, Optional
from urllib.parse import urljoin

import dotenv
from database.models import Task, Model
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse

from database.db_interface import DBInterface
from message_queue.mq_interface import MQInterface

from database.db_exceptions import TaskNotFoundException, ModelNotFoundException, InsertTaskException

LOG_FORMAT = '%(levelname)s:%(asctime)s:%(message)s'

logging.basicConfig(level=int(os.environ.get("LOG_LEVEL")), format=LOG_FORMAT)

dotenv.load_dotenv(".env")


class APIFastAPIImpl(FastAPI):
    def __init__(self, db: DBInterface, mq: MQInterface, **extra: Any):
        super().__init__(**extra)
        self.threads = []
        self.db = db
        self.mq = mq

        @self.get("/")
        def hello_world():
            return {"message": "Hello world - Welcome to the private database API"}

        @self.get(os.environ["PRIVATE_TASKS"])
        def get_tasks():
            return self.db.get_tasks()

        @self.get(urljoin(os.environ['PRIVATE_TASKS_BY_ID'], "{id}"))
        def get_task_by_id(id: int):
            try:
                return self.db.get_task_by_id(id=id)
            except TaskNotFoundException as e:
                raise HTTPException(status_code=554,
                                    detail=e.msg())

        @self.put(os.environ['PRIVATE_TASKS'])
        def set_task_status_by_uid(uid: str, status: int):
            try:
                return self.db.set_task_status_by_uid(uid=uid, status=status)
            except TaskNotFoundException as e:
                raise HTTPException(status_code=554,
                                    detail=e.msg())

        @self.get(urljoin(os.environ['PRIVATE_TASKS_BY_UID'], "{uid}"))
        def get_task_by_uid(uid: str):
            try:
                return self.db.get_task_by_uid(uid=uid)
            except TaskNotFoundException as e:
                raise HTTPException(status_code=554,
                                    detail=e.msg())

        @self.delete(urljoin(os.environ['PRIVATE_TASKS_BY_UID'], "{uid}"))
        def delete_task_by_uid(uid: str):
            try:
                return self.db.delete_task_by_uid(uid=uid)
            except TaskNotFoundException as e:
                raise HTTPException(status_code=554,
                                    detail=e.msg())

        @self.post(os.environ['PRIVATE_TASKS'])
        def post_task(model_human_readable_id: str,
                      zip_file: UploadFile = File(...),
                      uid: Union[str, None] = None) -> str:
            if not uid:
                uid = secrets.token_urlsafe(32)


            try:
                task = self.db.post_task(zip_file=zip_file.file,
                                     model_human_readable_id=model_human_readable_id,
                                     uid=uid)
                self.mq.publish_unfinished_task(task)

            except InsertTaskException as e:
                raise HTTPException(status_code=554,
                                    detail=e.msg())

            return task

        @self.get(urljoin(os.environ['PRIVATE_INPUT_ZIPS_BY_ID'], "{id}"))
        def get_input_zip_by_id(id: int) -> FileResponse:
            try:
                task = self.db.get_task_by_id(id=id)
            except TaskNotFoundException as e:
                raise HTTPException(status_code=554,
                                    detail=e.msg())

            if os.path.exists(task.input_zip):
                return FileResponse(task.input_zip)
            else:
                raise HTTPException(status_code=554, detail="Input zip not found - try posting task again")

        @self.post(urljoin(os.environ['PRIVATE_OUTPUT_ZIPS_BY_UID'], "{uid}"))
        def post_output_zip_by_uid(uid: str,
                                   zip_file: UploadFile = File(...)) -> Task:

            try:
                task = self.db.post_output_zip_by_uid(uid=uid, zip_file=zip_file.file)
            except TaskNotFoundException as e:
                raise HTTPException(status_code=554,
                                    detail=e.msg())
            except Exception as e:
                logging.error(e)
                raise e

            logging.info(task)
            self.mq.publish_finished_task(task)
            return task

        @self.get(urljoin(os.environ['PRIVATE_OUTPUT_ZIPS_BY_UID'], "{uid}"))
        def get_output_zip_by_uid(uid: str):
            # Zip the output for return
            try:
                task = self.db.get_task_by_uid(uid=uid)
                logging.info(str(task))
            except TaskNotFoundException as e:
                raise HTTPException(status_code=554,
                                    detail=e.msg())

            # Not doing this with os.path.exists(task.output.zip) to avoid that some of the file is sent before all written
            if os.path.exists(task.output_zip) and task.status == 1:
                return FileResponse(task.output_zip)
            elif not os.path.exists(task.output_zip) and task.status == 1:
                raise HTTPException(status_code=553,
                                    detail="Job status is 'finished', but output zip does not exist")
            elif task.status == 0:
                raise HTTPException(status_code=552,
                                    detail="Job status is 'failed'")
            elif task.status == -1:
                raise HTTPException(status_code=551,
                                    detail="Job status is 'pending'")
            else:
                logging.error(str(task))
                raise HTTPException(status_code=500,
                                    detail="Internal Server Error - should not be possible")

        @self.get(urljoin(os.environ['PRIVATE_TASK_BY_ID'], "{id}"))
        def get_task_by_id(id: int):
            try:
                return self.db.get_task_by_id(id=id)
            except TaskNotFoundException as e:
                raise HTTPException(status_code=554,
                                    detail=e.msg())

        @self.get(urljoin(os.environ['PRIVATE_TASK_BY_UID'], "{uid}"))
        def get_task_by_uid(uid: str):
            try:
                return self.db.get_task_by_uid(uid=uid)
            except TaskNotFoundException as e:
                raise HTTPException(status_code=554,
                                    detail=e.msg())

        @self.post(os.environ['PRIVATE_MODELS'])
        def post_model(container_tag: str,
                       human_readable_id: str,
                       input_mountpoint: Union[str, None] = None,
                       output_mountpoint: Union[str, None] = None,
                       model_mountpoint: Union[str, None] = None,
                       description: Union[str, None] = None,
                       zip_file: Optional[Union[UploadFile, None]] = None,
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

        @self.get(urljoin(os.environ['PRIVATE_MODEL_BY_ID'], "{id}"))
        def get_model_by_id(id: int):
            try:
                return self.db.get_model_by_id(id=id)
            except ModelNotFoundException as e:
                raise HTTPException(status_code=554,
                                    detail=e.msg())

        @self.get(urljoin(os.environ['PRIVATE_MODEL_BY_HUMAN_READABLE_ID'], "{human_readable_id}"))
        def get_model_by_human_readable_id(human_readable_id: str):
            try:
                return self.db.get_model_by_human_readable_id(human_readable_id=human_readable_id)
            except ModelNotFoundException as e:
                raise HTTPException(status_code=554,
                                    detail=e.msg())

        @self.get(os.environ['PRIVATE_MODELS'])
        def get_models():
            return self.db.get_models()

        @self.get(urljoin(os.environ['PRIVATE_MODEL_BY_ID'], "{id}"))
        def get_model_zip_by_id(id: int) -> FileResponse:
            try:
                model = self.db.get_model_by_id(id=id)
            except ModelNotFoundException as e:
                raise HTTPException(status_code=554,
                                    detail=e.msg())

            if os.path.exists(model.model_zip):
                return FileResponse(model.model_zip)
            else:
                raise HTTPException(status_code=554, detail="Model zip not found - try posting task again")

    def __del__(self):
        for t in self.threads:
            t.join()
