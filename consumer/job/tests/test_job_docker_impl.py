import os
import secrets
import tempfile
import unittest
import uuid
import zipfile

from docker import errors

from database.db_models import Task, Model

from docker_helper import volume_functions
from job.job_docker_impl import JobDockerImpl


class TestJob(unittest.TestCase):
    def setUp(self) -> None:
        self.model_vanilla = Model(human_readable_id="hello-world",
                                   container_tag="hello-world",
                                   use_gpu=False,
                                   model_available=False,
                                   model_volume_id=str(uuid.uuid4()),
                                   uid=secrets.token_urlsafe(4),
                                   id=1)
        self.model_with_zip = Model(human_readable_id="hello-world",
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
        volume_functions.create_empty_volume(self.input_uid)
        self.output_uid = str(uuid.uuid4())
        volume_functions.create_empty_volume(self.output_uid)
        self.model_uid = str(uuid.uuid4())
        volume_functions.create_empty_volume(self.model_uid)

    def tearDown(self) -> None:
        volume_functions.delete_volume(self.input_uid)
        volume_functions.delete_volume(self.output_uid)
        volume_functions.delete_volume(self.model_uid)

    def test_JobDockerImpl_vanilla(self):
        task = Task(human_readable_id="hello-world",
                    model_id=self.model_vanilla.id,
                    input_volume_id=self.input_uid,
                    output_volume_id=self.output_uid,
                    model=self.model_vanilla)
        j = JobDockerImpl(task)
        print(j.execute())
