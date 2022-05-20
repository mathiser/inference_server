import os
import secrets
import shutil
import uuid
from typing import BinaryIO, List, Optional

from database.models import Model, Task
from database.db_interface import DBInterface


class MockDB(DBInterface):
    def __init__(self):
        self.base_dir = ".tmp"

        ## Folders for input and output
        self.input_base_folder = os.path.join(self.base_dir, "input")
        self.output_base_folder = os.path.join(self.base_dir, "output")

        # model volume mount point
        self.model_base_folder = os.path.join(self.base_dir, "models")

        # Create all folders
        for p in [self.base_dir, self.input_base_folder, self.output_base_folder, self.model_base_folder]:
            os.makedirs(p, exist_ok=True)

        self.task_id = 1
        self.tasks = []
        self.model_id = 1
        self.models = []

        self.input_zip = os.path.join(self.base_dir, "input.zip")
        with open(self.input_zip, 'w') as myzip:
            myzip.write("Important zip")

        self.output_zip = os.path.join(self.base_dir, "output.zip")
        with open(self.output_zip, 'w') as myzip:
            myzip.write("Important zip")

        self.model_zip = os.path.join(self.base_dir, "model.zip")
        with open(self.model_zip, 'w') as myzip:
            myzip.write("Important zip")

    def purge(self):
        shutil.rmtree(self.base_dir)

    def add_task(self, zip_file: BinaryIO, model_human_readable_id: str, uid: str) -> Task:
        t = Task(id=self.task_id,
                 uid=uid,
                 model_human_readable_id=model_human_readable_id,
                 input_zip=os.path.abspath(os.path.join(self.input_base_folder, uid, "input.zip")),
                 input_volume_uuid=str(uuid.uuid4()),
                 output_zip=os.path.abspath(os.path.join(self.output_base_folder, uid, "output.zip")),
                 output_volume_uuid=str(uuid.uuid4())
                 )
        self.tasks.append(t)
        self.task_id += 1
        return t

    def get_task_by_id(self, id: int) -> Task:
        for task in self.tasks:
            if task.id == id:
                return task

    def get_task_by_uid(self, uid: str) -> Task:
        for task in self.tasks:
            if task.uid == uid:
                return task

    def get_tasks(self) -> List[Task]:
        return self.tasks

    def add_model(self, container_tag: str,
                  human_readable_id: str,
                  zip_file: BinaryIO,
                  input_mountpoint: Optional[str] = None,
                  output_mountpoint: Optional[str] = None,
                  model_mountpoint: Optional[str] = None,
                  description: Optional[str] = None,
                  model_available: Optional[bool] = True,
                  use_gpu: Optional[bool] = True) -> Model:

        uid = str(uuid.uuid4())
        model_zip = None
        if model_available:
            model_zip = os.path.join(self.model_base_folder, uid, "model.zip")
            os.makedirs(os.path.dirname(model_zip))
            with open(model_zip, 'wb') as out_file:
                out_file.write(zip_file.read())
        model = Model(
            id=self.model_id,
            uid=uid,
            description=description,
            human_readable_id=human_readable_id,
            container_tag=container_tag,
            model_zip=model_zip,
            model_volume_uuid=str(uuid.uuid4()),
            input_mountpoint=input_mountpoint,
            output_mountpoint=output_mountpoint,
            model_mountpoint=model_mountpoint,
            model_available=model_available,
            use_gpu=use_gpu
        )
        self.model_id += 1
        self.models.append(model)

        return model

    def get_model_by_id(self, id: int) -> Model:
        for model in self.models:
            if model.id == id:
                return model

    def get_model_by_human_readable_id(self, human_readable_id: str) -> Model:
        for model in self.models:
            if model.human_readable_id == human_readable_id:
                return model

    def get_models(self) -> List[Model]:
        return self.models

    def post_output_by_uid(self, uid: str, zip_file: BinaryIO) -> Task:
        task = self.get_task_by_uid(uid)
        # Write zip_file to task.output_zip
        os.makedirs(os.path.dirname(task.output_zip))
        with open(task.output_zip, 'wb') as out_file:
            out_file.write(zip_file.read())
        return task
