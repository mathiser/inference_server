import datetime
import os
import secrets
import shutil
import tempfile
import uuid
import zipfile

from interfaces.db_models import Model, Task


class MockModelsAndTasks:

    def __init__(self):
        self.base_dir = tempfile.mkdtemp()
        self.dst = tempfile.mkdtemp()

        ## Folders for input and output
        self.input_base_folder = os.path.join(self.base_dir, "input")
        self.output_base_folder = os.path.join(self.base_dir, "output")
        self.model_base_folder = os.path.join(self.base_dir, "models")

        # Create all folders
        for p in [self.base_dir, self.input_base_folder, self.output_base_folder, self.model_base_folder, self.dst]:
            os.makedirs(p, exist_ok=True)

        self.input_zip = os.path.join(self.base_dir, "input.zip")
        self.output_zip = os.path.join(self.base_dir, "output.zip")
        self.model_zip = os.path.join(self.base_dir, "model.zip")

        for zip in [self.input_zip, self.output_zip, self.model_zip]:
            with open(zip.replace(".zip", ".txt"), 'w') as myzip:
                myzip.write("Important zip")
            with zipfile.ZipFile(zip, 'w') as myzip:
                myzip.write(zip.replace(".zip", ".txt"))

        self.model = Model(container_tag="hello-world",
                           id=1,
                           uid=secrets.token_urlsafe(),
                           human_readable_id="one",
                           description="This is a testing of a very important database",
                           model_available=True,
                           use_gpu=False,
                           model_zip=self.model_zip,
                           )

        uid = secrets.token_urlsafe(32)
        task_input = os.path.join(self.input_base_folder, uid, "input.zip")
        os.makedirs(os.path.dirname(task_input), exist_ok=True)
        shutil.copy2(self.input_zip, task_input)

        task_output = os.path.join(self.output_base_folder, uid, "output.zip")
        os.makedirs(os.path.dirname(task_output), exist_ok=True)
        shutil.copy2(self.output_zip, task_output)

        self.task = Task(
            id=1,
            uid=uid,
            model_human_readable_id=self.model.human_readable_id,
            input_zip=task_input,
            output_zip=task_output,
            input_volume_id=str(uuid.uuid4()),
            output_volume_id=str(uuid.uuid4()),
            status=-1,
            datetime_created=datetime.datetime.now()
        )

        self.failing_model = Model(container_tag="hellords-world",
                                   id=2,
                                   uid=secrets.token_urlsafe(),
                                   human_readable_id="two",
                                   description="This is a testing of a very important database",
                                   model_available=True,
                                   use_gpu=False,
                                   model_zip=self.model_zip,
                                   )

    def __del__(self):
        shutil.rmtree(self.base_dir)
        shutil.rmtree(self.dst)
