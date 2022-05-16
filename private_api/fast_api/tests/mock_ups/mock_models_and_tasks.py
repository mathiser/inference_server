import os
import secrets
import shutil
import tempfile
import uuid
import zipfile

from database.models import Model, Task


class MockModelsAndTasks():

    def __init__(self):
        self.base_dir = tempfile.mkdtemp()
        self.dst = tempfile.mkdtemp()
        ## Folders for input and output
        self.input_base_folder = os.path.join(self.base_dir, "input")
        self.output_base_folder = os.path.join(self.base_dir, "output")

        # model volume mount point
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
                            use_gpu=True,
                            model_zip=self.model_zip,
                            )
        self.model2 = Model(container_tag="hello-world",
                            id=2,
                            human_readable_id="two",
                            input_mountpoint="/input1",
                            output_mountpoint="/output2",
                            model_mountpoint=None,
                            model_zip=self.model_zip,
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


        self.task1 = Task(
            id=1,
            uid=uid,
            model_ids=[self.model1.id, self.model2.id, self.model3.id],
            human_readable_ids=["one", "two", "three"],
            input_zip=task_input,
            output_zip=task_output,
            input_volume_uuid=str(uuid.uuid4()),
            output_volume_uuid=str(uuid.uuid4())
        )

    def clean_up(self):
        shutil.rmtree(self.base_dir)
        shutil.rmtree(self.dst)