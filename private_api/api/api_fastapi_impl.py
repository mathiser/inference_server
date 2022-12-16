import logging
import os
import secrets
from typing import Union, Optional
from urllib.parse import urljoin

import dotenv
from database.db_exceptions import TaskNotFoundException, ModelNotFoundException, InsertTaskException
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from interfaces.api_interface import APIInterface
from interfaces.db_interface import DBInterface
from interfaces.db_models import Task, Model
from interfaces.mq_interface import MQInterface

LOG_FORMAT = '%(levelname)s:%(asctime)s:%(message)s'
dotenv.load_dotenv(".env")

logging.basicConfig(level=10, format=LOG_FORMAT)


class APIFastAPIImpl(APIInterface):
    def __init__(self, db: DBInterface, mq: MQInterface):
        super().__init__()
        self.db = db
        self.mq = mq
        self.app = FastAPI()

        self.threads = []

        @self.app.get("/")
        def hello_world():
            return {"message": "Hello world - Welcome to the private database API"}

        @self.app.get(os.environ["API_TASKS"])
        def get_tasks():
            return self.db.get_tasks()

        @self.app.get(urljoin(os.environ['API_TASKS'], "{uid}"))
        def get_task(uid: str):
            try:
                return self.db.get_task(uid=uid)
            except TaskNotFoundException as e:
                raise HTTPException(status_code=554,
                                    detail=e.msg())

        @self.app.put(os.environ['API_TASKS'])
        def set_task_status(uid: str, status: int):
            try:
                return self.db.set_task_status(uid=uid, status=status)
            except TaskNotFoundException as e:
                raise HTTPException(status_code=554,
                                    detail=e.msg())


        @self.app.delete(urljoin(os.environ['API_TASKS'], "{uid}"))
        def delete_task(uid: str) -> Task:
            try:
                t = self.db.delete_task(uid=uid)
                return t
            except TaskNotFoundException as e:
                raise HTTPException(status_code=554,
                                    detail=e.msg())

        @self.app.post(os.environ['API_TASKS'])
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

        @self.app.get(urljoin(os.environ['API_INPUT_ZIPS'], "{uid}"))
        def get_input_zip(uid: str) -> FileResponse:
            try:
                task = self.db.get_task(uid=uid)
            except TaskNotFoundException as e:
                raise HTTPException(status_code=554,
                                    detail=e.msg())

            if os.path.exists(task.input_zip):
                return FileResponse(task.input_zip)
            else:
                raise HTTPException(status_code=554, detail="Input zip not found - try posting task again")

        @self.app.post(urljoin(os.environ['API_OUTPUT_ZIPS'], "{uid}"))
        def post_output_zip(uid: str,
                            zip_file: UploadFile = File(...)) -> Task:

            try:
                task = self.db.post_output_zip(uid=uid, zip_file=zip_file.file)
            except TaskNotFoundException as e:
                raise HTTPException(status_code=554,
                                    detail=e.msg())
            except Exception as e:
                logging.error(e)
                raise e

            logging.info(task)
            self.mq.publish_finished_task(task)
            return task

        @self.app.get(urljoin(os.environ['API_OUTPUT_ZIPS'], "{uid}"))
        def get_output_zip(uid: str):
            # Zip the output for return
            try:
                task = self.db.get_task(uid=uid)
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
            elif task.is_deleted == 1:
                raise HTTPException(status_code=552,
                                    detail="Job files are 'deleted'")
            elif task.status == 0:
                raise HTTPException(status_code=552,
                                    detail="Job status is 'failed'")
            elif task.status in [-1, 2]:
                raise HTTPException(status_code=551,
                                    detail="Job status is 'pending' or 'running'")
            else:
                logging.error(str(task))
                raise HTTPException(status_code=500,
                                    detail="Internal Server Error - should not be possible")

        @self.app.post(os.environ['API_MODELS'])
        def post_model(container_tag: str,
                       human_readable_id: str,
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
                zip_file=zip_file,
                description=description,
                model_available=model_available,
                use_gpu=use_gpu,
            )

        @self.app.get(urljoin(os.environ['API_MODELS'], "{uid}"))
        def get_model(uid: str):
            try:
                return self.db.get_model(uid=uid)
            except ModelNotFoundException as e:
                raise HTTPException(status_code=554,
                                    detail=e.msg())

        @self.app.get(urljoin(os.environ['API_MODELS_BY_HUMAN_READABLE_ID'], "{human_readable_id}"))
        def get_model_by_human_readable_id(human_readable_id: str):
            try:
                return self.db.get_model(human_readable_id=human_readable_id)
            except ModelNotFoundException as e:
                raise HTTPException(status_code=554,
                                    detail=e.msg())

        @self.app.get(os.environ['API_MODELS'])
        def get_models():
            return self.db.get_models()

        @self.app.get(urljoin(os.environ['API_MODEL_ZIPS'], "{id}"))
        def get_model_zip(uid: str) -> FileResponse:
            try:
                model = self.db.get_model(uid=uid)
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
