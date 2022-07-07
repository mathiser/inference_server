import os
import secrets
import shutil
import tempfile
import uuid
from typing import BinaryIO, List, Optional

from database.db_interface import DBInterface
from testing.mock_components.models import Model, Task


class MockDB(DBInterface):

    def __init__(self):
        self.base_dir = ".tmp"

        ## Folders for input and output
        self.input_base_folder = os.path.join(self.base_dir, "inputs")
        self.output_base_folder = os.path.join(self.base_dir, "outputs")

        # model volume mount point
        self.model_base_folder = os.path.join(self.base_dir, "models")

        # Create all folders
        for p in [self.base_dir, self.input_base_folder, self.output_base_folder, self.model_base_folder]:
            os.makedirs(p, exist_ok=True)

        self.task_id = 1
        self.tasks = []
        self.model_id = 1
        self.models = []

    def post_output_zip_by_uid(self, uid: str):
        task = self.get_task_by_uid(uid)
        print(f"Task: {task}")
        print([n.to_dict() for n in self.tasks])
        if task:
            os.makedirs(os.path.dirname(task.output_zip), exist_ok=True)
            with open(task.output_zip, "bw") as f:
                f.write(b"Hello hello world")

            return task
        else:
            raise Exception("Task does not exist")

    def get_output_zip_by_uid(self, uid: str):
        task = self.get_task_by_uid(uid)
        if task:
            try:
                return open(task.output_zip, "br")
            except FileNotFoundError as e:
                raise e
        else:
            raise Exception("Task does not exist")


    def purge(self):
        shutil.rmtree(self.base_dir)

    def post_task(self, model_human_readable_id: str, zip_file: BinaryIO, uid=None):
        if not uid:
            uid = secrets.token_urlsafe(32)

        t = Task(id=self.task_id,
                 uid=uid,
                 model_human_readable_id=model_human_readable_id,
                 input_zip=os.path.abspath(os.path.join(self.input_base_folder, uid, "input.zip")),
                 input_volume_uuid=str(uuid.uuid4()),
                 output_zip=os.path.abspath(os.path.join(self.output_base_folder, uid, "output.zip")),
                 output_volume_uuid=str(uuid.uuid4()),
                 status=-1,
                 is_deleted=False,
                 )

        self.tasks.append(t)
        self.task_id += 1

        os.makedirs(os.path.dirname(t.input_zip), exist_ok=True)
        with open(t.input_zip, "bw") as f:
            f.write(zip_file.read())
        return t

    def get_task_by_id(self, id: int) -> Task:
        for task in self.tasks:
            if task.id == id:
                return task

    def get_task_by_uid(self, uid: str) -> Task:
        for task in self.tasks:
            if task.uid == uid:
                print(f"Matching task was found: {task}")
                return task

    def delete_task_by_uid(self, uid: str) -> Task:
        for task in self.tasks:
            if task.uid == uid:
                task.is_deleted = True
                return task

    def get_tasks(self) -> List[Task]:
        return self.tasks

    def post_model(self,
                   container_tag: str,
                   human_readable_id: str,
                   input_mountpoint: Optional[str] = None,
                   output_mountpoint: Optional[str] = None,
                   model_mountpoint: Optional[str] = None,
                   description: Optional[str] = None,
                   zip_file: Optional[BinaryIO] = None,
                   model_available: Optional[bool] = True,
                   use_gpu: Optional[bool] = True,
                   ):
        uid = secrets.token_urlsafe(32)
        model_zip = None
        if model_available:
            model_zip = os.path.join(self.model_base_folder, uid, "model.zip")
            os.makedirs(os.path.dirname(model_zip))
            with open(model_zip, 'wb') as out_file:
                out_file.write(zip_file.read())

        model = Model(
            id=self.model_id,
            description=description,
            human_readable_id=human_readable_id,
            container_tag=container_tag,
            model_zip=model_zip,
            model_volume_uuid=str(uuid.uuid4()),
            input_mountpoint=input_mountpoint,
            output_mountpoint=output_mountpoint,
            model_mountpoint=model_mountpoint,
            model_available=model_available,
            use_gpu=use_gpu,
            uid=uid
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
        os.makedirs(os.path.dirname(task.output_zip), exist_ok=True)
        with open(task.output_zip, 'wb') as out_file:
            out_file.write(zip_file.read())
        return task
