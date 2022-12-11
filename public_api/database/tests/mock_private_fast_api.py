import datetime
import os
import secrets
import shutil
from typing import Any, Optional
from urllib.parse import urljoin

from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse

from interfaces.db_models import Task, Model


class MockPrivateFastAPI(FastAPI):
    def __init__(self, **extra: Any):
        super().__init__(**extra)

        self.base_dir = ".tmp"

        ## Folders for input and output
        self.input_base_folder = os.path.join(self.base_dir, "inputs")
        self.output_base_folder = os.path.join(self.base_dir, "outputs")
        self.model_base_folder = os.path.join(self.base_dir, "models")

        # Create all folders
        for p in [self.base_dir, self.input_base_folder, self.output_base_folder, self.model_base_folder]:
            os.makedirs(p, exist_ok=True)

        self.task_id = 1
        self.tasks = []
        self.model_id = 1
        self.models = []

        @self.get("/")
        def hello_world():
            return {"message": "Hello world - Welcome to the public database API"}

        @self.post(os.environ['API_TASKS'])
        def post_task(model_human_readable_id: str,
                      zip_file: UploadFile = File(...),
                      uid=None) -> Task:
            if not uid:
                uid = secrets.token_urlsafe()

            t = Task(id=self.task_id,
                     uid=uid,
                     model_human_readable_id=model_human_readable_id,
                     input_zip=os.path.abspath(os.path.join(self.input_base_folder, uid, "input.zip")),
                     input_volume_id=secrets.token_urlsafe(),
                     output_zip=os.path.abspath(os.path.join(self.output_base_folder, uid, "output.zip")),
                     output_volume_id=secrets.token_urlsafe(),
                     status=-1,
                     is_deleted=False,
                     datetime_created=datetime.datetime.now(),

                     )

            self.tasks.append(t)
            self.task_id += 1

            os.makedirs(os.path.dirname(t.input_zip), exist_ok=True)
            with open(t.input_zip, "bw") as f:
                f.write(zip_file.file.read())
            return t
        @self.get(urljoin(os.environ['API_OUTPUT_ZIPS'], "{uid}"))
        def get_output_zip(uid: str):
            # Zip the output for return
            task = self.get_task(uid)
            if not task:
                raise Exception("Task does not exist")
            def iterfile(task):
                with open(task.output_zip, "br") as tmp_file:
                    yield from tmp_file.read()

            return StreamingResponse(iterfile(task))

        @self.post(os.environ['API_MODELS'])
        def post_model(container_tag: str,
                       human_readable_id: str,
                       description: Optional[str] = None,
                       zip_file: Optional[UploadFile] = File(None),
                       model_available: Optional[bool] = True,
                       use_gpu: Optional[bool] = True,
                       ) -> Model:
            uid = secrets.token_urlsafe(32)
            model_zip = None
            if model_available:
                model_zip = os.path.join(self.model_base_folder, uid, "model.zip")
                os.makedirs(os.path.dirname(model_zip))
                with open(model_zip, 'wb') as out_file:
                    out_file.write(zip_file.file.read())

            model = Model(
                id=self.model_id,
                description=description,
                human_readable_id=human_readable_id,
                container_tag=container_tag,
                model_zip=model_zip,
                model_volume_id=secrets.token_urlsafe(),
                model_available=model_available,
                use_gpu=use_gpu,
                uid=uid
            )

            self.model_id += 1
            self.models.append(model)

            return model

        @self.get(os.environ['API_MODELS'])
        def get_models():
            return self.models

    def get_task(self, uid: str) -> Task:
        for task in self.tasks:
            if task.uid == uid:
                return task

    def purge(self):
        shutil.rmtree(self.base_dir)