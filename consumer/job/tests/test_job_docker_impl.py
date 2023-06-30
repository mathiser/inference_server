import os.path
import secrets
import tarfile
import tempfile
import unittest
import uuid

import docker
from database.db_models import Task, Model
from docker_helper import volume_functions
from job.job_docker_functions import exec_job
from io import BytesIO


def generate_tar():
    tar_file = tempfile.TemporaryFile()
    with tarfile.TarFile.open(fileobj=tar_file, mode='w') as tar_obj:
        tar_obj.add(__file__)
    tar_file.seek(0)
    return tar_file

def build_input_echo_container(container_tag, dockerfile):
    cli = docker.from_env()
    cli.images.build(tag=container_tag,
                     fileobj=BytesIO(dockerfile),
                     pull=False)
    cli.close()

class TestJob(unittest.TestCase):
    def setUp(self) -> None:
        self.model_vanilla = Model(human_readable_id="hello-world",
                                   container_tag="hello-world",
                                   use_gpu=False,
                                   model_available=False,
                                   model_volume_id=str(uuid.uuid4()),
                                   uid=secrets.token_urlsafe(4),
                                   id=1)
        self.model_with_tar = Model(human_readable_id="hello-world",
                                    container_tag="hello-world",
                                    use_gpu=False,
                                    model_available=True,
                                    model_volume_id=str(uuid.uuid4()),
                                    uid=secrets.token_urlsafe(4),
                                    id=2)
        self.model_gpu = Model(human_readable_id="hello-world",
                               container_tag="hello-world",
                               use_gpu=True,
                               model_available=False,
                               model_volume_id=str(uuid.uuid4()),
                               uid=secrets.token_urlsafe(4),
                               id=3)

        self.input_uid = str(uuid.uuid4())
        self.input_tar = generate_tar()

        self.output_uid = str(uuid.uuid4())

        self.model_uid = str(uuid.uuid4())
        self.model_tar = generate_tar()

    def tearDown(self) -> None:
        self.model_tar.close()
        self.input_tar.close()

    def test_JobDockerImpl_vanilla(self):
        task = Task(human_readable_id="hello-world",
                    model_id=self.model_vanilla.id,
                    model=self.model_vanilla)
        
        j = exec_job(task=task,
                     gpu_uuid=None,
                     task_input_tar=self.input_tar,
                     model_tar=None)
        
        self.assertIsInstance(j, BytesIO)
        self.assertFalse(volume_functions.volume_exists(self.input_uid))
        self.assertFalse(volume_functions.volume_exists(self.output_uid))
        self.assertFalse(volume_functions.volume_exists(self.model_uid))

    def test_JobDockerImpl_model_available(self):
        task = Task(human_readable_id="hello-world",
                    model_id=self.model_vanilla.id,
                    model=self.model_with_tar)

        j = exec_job(task=task,
                     gpu_uuid=None,
                     task_input_tar=self.input_tar,
                     model_tar=self.model_tar)
        self.assertIsInstance(j, BytesIO)
        self.assertFalse(volume_functions.volume_exists(self.input_uid))
        self.assertFalse(volume_functions.volume_exists(self.output_uid))
        self.assertFalse(volume_functions.volume_exists(self.model_uid))

    def test_echo_job_cp_input_to_output(self):
        tag = "cper:test"
        dockerfile = b"""
        FROM busybox
        CMD cp -r /input/* /output/
        """
        build_input_echo_container(tag, dockerfile)

        model = Model(human_readable_id="copy-world",
                               container_tag=tag,
                               use_gpu=False,
                               model_available=False,
                               model_volume_id=str(uuid.uuid4()),
                               uid=secrets.token_urlsafe(4),
                               id=1)

        task = Task(human_readable_id="copy-world",
                    model_id=model.id,
                    model=model)

        j = exec_job(task=task,
                     gpu_uuid=None,
                     task_input_tar=self.input_tar,
                     model_tar=None,
                     pull_on_every_run=False)
        
        echo_tarf = tarfile.TarFile.open(fileobj=j, mode="r|*")
        self.assertEqual(echo_tarf.getmembers()[0].name, os.path.basename(__file__))
        echo_tarf.close()
        j.close()
        
    def test_echo_job_cp_model_to_output(self):
        tag = "cper:model"
        dockerfile = b"""
        FROM busybox
        CMD cp -r /model/* /output/
        """
        build_input_echo_container(tag, dockerfile)

        model = Model(human_readable_id="copy-world",
                      container_tag=tag,
                      use_gpu=False,
                      model_available=True,
                      model_volume_id=str(uuid.uuid4()),
                      uid=secrets.token_urlsafe(4),
                      id=1)

        task = Task(human_readable_id="copy-world",
                    model_id=model.id,
                    model=model)

        j = exec_job(task=task,
                     gpu_uuid=None,
                     input_tar=self.input_tar,
                     model_tar=self.model_tar,
                     pull_on_every_run=False)
        
        echo_tarf = tarfile.TarFile.open(fileobj=j, mode="r|*")
        self.assertEqual(echo_tarf.getmembers()[0].name, os.path.basename(__file__))
        echo_tarf.close()
        j.close()
