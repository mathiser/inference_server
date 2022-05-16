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

        self.id_lookup = {}
        self.id_lookup["one"] = 1
        self.id_lookup["two"] = 2
        self.id_lookup["three"] = 3
        self.model1 = Model(container_tag="hello-world",
                            id=1,
                            human_readable_id="one",
                            input_mountpoint="/input",
                            output_mountpoint="/output",
                            model_mountpoint="/model",
                            description="This is a tests of a very important database",
                            model_available=True,
                            use_gpu=True
                            )
        self.model2 = Model(container_tag="hello-world",
                            id=2,
                            human_readable_id="two",
                            input_mountpoint="/input1",
                            output_mountpoint="/output2",
                            model_mountpoint=None,
                            description="This is a tests of a very important database",
                            model_available=False,
                            use_gpu=False
                            )
        self.model3 = Model(container_tag="hello-world",
                            id=3,
                            human_readable_id="three",
                            input_mountpoint="/input11",
                            output_mountpoint="/outputff2",
                            model_mountpoint=None,
                            description="This is a tesdfsdfsts of a very important database",
                            model_available=True,
                            use_gpu=False
                            )
        self.task1 = Task(
            id=1,
            uid=secrets.token_urlsafe(32),
            model_ids=[self.model1.id, self.model2.id, self.model3.id],
            human_readable_ids=["one", "two", "three"],
            input_zip=self.input_zip,
            output_zip=self.output_zip,
            input_volume_uuid=str(uuid.uuid4()),
            output_volume_uuid=str(uuid.uuid4())
        )

    def purge(self):
        shutil.rmtree(self.base_dir)

    def add_task(self, zip_file: BinaryIO, human_readable_ids: List[str], uid: str) -> Task:
        t = Task(id=self.task_id,
                 uid=uid,
                 human_readable_ids=human_readable_ids,
                 model_ids=[self.id_lookup[hid] for hid in human_readable_ids],
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

    def add_model(self, container_tag: str, human_readable_id: str, input_mountpoint: str, output_mountpoint: str,
                  zip_file: BinaryIO, model_mountpoint: Optional[str] = None, description: Optional[str] = None,
                  model_available: Optional[bool] = True, use_gpu: Optional[bool] = True) -> Model:

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

    def get_models(self) -> List[Model]:
        return self.models

    def post_output_by_uid(self, uid: str, zip_file: BinaryIO) -> Task:
        task = self.get_task_by_uid(uid)
        # Write zip_file to task.output_zip
        os.makedirs(os.path.dirname(task.output_zip))
        with open(task.output_zip, 'wb') as out_file:
            out_file.write(zip_file.read())
        return task
