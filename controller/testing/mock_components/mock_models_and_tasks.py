import os
import secrets
import shutil
import tempfile
import tarfile

from database.db_models import Model, Task


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

        self.input_tar = os.path.join(self.base_dir, "input.tar.gz")
        self.output_tar = os.path.join(self.base_dir, "output.tar.gz")
        self.model_tar = os.path.join(self.base_dir, "model.tar.gz")

        for tar in [self.input_tar, self.output_tar, self.model_tar]:
            with open(tar.replace(".tar", ".txt"), 'w') as mytar:
                mytar.write("Important tar")
            with tarfile.TarFile(tar, 'w') as mytar:
                mytar.add(tar.replace(".tar", ".txt"))

        self.model = Model(id=1,
                           container_tag="hello-world",
                           human_readable_id="one",
                           description="This is a testing of a very important database",
                           model_available=True,
                           use_gpu=True,
                           model_tar=self.model_tar)

        task_input = os.path.join(self.input_base_folder, str(self.model.id), "input.tar")
        os.makedirs(os.path.dirname(task_input), exist_ok=True)
        shutil.copy2(self.input_tar, task_input)

        task_output = os.path.join(self.output_base_folder, str(self.model.id), "output.tar")
        os.makedirs(os.path.dirname(task_output), exist_ok=True)
        shutil.copy2(self.output_tar, task_output)

        self.task = Task(
            model_id=self.model.id,
            input_tar=task_input,
            output_tar=task_output,
        )

    def purge(self):
        shutil.rmtree(self.base_dir)
        shutil.rmtree(self.dst)
