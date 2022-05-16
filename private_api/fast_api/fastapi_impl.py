import logging
import os
from typing import Optional, List, Any
from urllib.parse import urljoin

from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from starlette.responses import FileResponse

from database.models import Task, Model
from api import PrivateAPIInterface

LOG_FORMAT = '%(levelname)s:%(asctime)s:%(message)s'

logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)


class FastAPIImpl(FastAPI):
    def __init__(self, api: PrivateAPIInterface, **extra: Any):
        super().__init__(**extra)
        self.api = api

        @self.get("/")
        def hello_world():
            return self.api.hello_world()

        @self.get(os.environ["GET_TASKS"])
        def get_tasks():
            return self.api.get_tasks()

        @self.get(urljoin(os.environ['GET_TASK_BY_ID'], "{id}"))
        def get_task_by_id(id: int):
            return self.api.get_task_by_id(id=id)

        @self.get(urljoin(os.environ['GET_TASK_BY_UID'], "{uid}"))
        def get_task_by_uid(uid: str):
            return self.api.get_task_by_uid(uid=uid)

        @self.post(os.environ['POST_TASK'])
        def post_task(human_readable_ids: List[str] = Query(None),
                      zip_file: UploadFile = File(...),
                      uid=None) -> Task:
            logging.info(f"Human readable ids: {human_readable_ids}")
            if not (len(human_readable_ids) >= 1):
                raise HTTPException(500, "Task must have at least ONE model - try again")

            t = self.api.post_task(zip_file=zip_file.file,
                                   human_readable_ids=human_readable_ids,
                                   uid=uid)
            return t

        @self.get(urljoin(os.environ['GET_INPUT_ZIP_BY_ID'], "{id}"))
        def get_input_zip_by_id(id: int) -> FileResponse:
            task = self.api.get_task_by_id(id=id)

            if os.path.exists(task.input_zip):
                return FileResponse(task.input_zip)
            else:
                raise HTTPException(status_code=404, detail="Input zip not found - try posting task again")

        @self.post(urljoin(os.environ['POST_OUTPUT_ZIP_BY_UID'], "{uid}"))
        def post_output_by_uid(uid: str, zip_file: UploadFile = File(...)) -> Task:
            return self.api.post_output_by_uid(uid=uid,
                                               zip_file=zip_file.file)

        @self.get(urljoin(os.environ['GET_OUTPUT_ZIP_BY_UID'], "{uid}"))
        def get_output_zip_by_uid(uid: str):
            # Zip the output for return
            task = self.api.get_task_by_uid(uid=uid)
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
            return self.api.get_task_by_id(id=id)

        @self.get(urljoin(os.environ['GET_TASK_BY_UID'], "{uid}"))
        def get_task_by_uid(uid: str):
            return self.api.get_task_by_uid(uid=uid)

        @self.post(os.environ['POST_MODEL'])
        def post_model(container_tag: str,
                       human_readable_id: str,
                       input_mountpoint: str,
                       output_mountpoint: str,
                       model_mountpoint: Optional[str] = None,
                       description: Optional[str] = None,
                       zip_file: Optional[UploadFile] = File(None),
                       model_available: Optional[bool] = True,
                       use_gpu: Optional[bool] = True,
                       ) -> Model:

            return self.api.post_model(
                container_tag=container_tag,
                human_readable_id=human_readable_id,
                input_mountpoint=input_mountpoint,
                output_mountpoint=output_mountpoint,
                zip_file=zip_file.file,
                model_mountpoint=model_mountpoint,
                description=description,
                model_available=model_available,
                use_gpu=use_gpu,
            )

        @self.get(urljoin(os.environ['GET_MODEL_BY_ID'], "{id}"))
        def get_model_by_id(id: int):
            return self.api.get_model_by_id(id=id)

        @self.get(os.environ['GET_MODELS'])
        def get_models():
            return self.api.get_models()

        @self.get(urljoin(os.environ['GET_MODEL_ZIP_BY_ID'], "{id}"))
        def get_model_zip_by_id(id: int) -> FileResponse:
            model = self.api.get_model_by_id(id=id)

            if os.path.exists(model.model_zip):
                return FileResponse(model.model_zip)
            else:
                raise HTTPException(status_code=404, detail="Model zip not found - try posting task again")