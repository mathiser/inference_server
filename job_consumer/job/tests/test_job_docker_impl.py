import random
import secrets
import unittest
import os

from docker import errors

os.environ["LOG_LEVEL"] = "20"
os.environ["VOLUME_SENDER_DOCKER_TAG"] = ""
os.environ["GPU_UUID"] = ""
os.environ["NETWORK_NAME"] = ""
os.environ["API_URL"] = ""
os.environ["API_OUTPUT_ZIPS"] = ""

from docker_helper import volume_functions
from job.job_docker_impl import JobDockerImpl
from testing.mock_components.mock_db import MockDB

from testing.mock_components.mock_models_and_tasks import MockModelsAndTasks


class TestJob(unittest.TestCase):
    def setUp(self) -> None:
        self.db = MockDB()
        self.repo = MockModelsAndTasks()
        self.job = JobDockerImpl(db=self.db,
                                 volume_sender_docker_tag="",
                                 gpu_uuid="",
                                 network_name="",
                                 api_output_zips="",
                                 api_url="")

    def tearDown(self) -> None:
        for task in self.db.get_tasks():
            if volume_functions.volume_exists(task.input_volume_id):
                volume_functions.delete_volume(task.input_volume_id)

            if volume_functions.volume_exists(task.output_volume_id):
                volume_functions.delete_volume(task.output_volume_id)

        for model in self.db.get_models():
            if volume_functions.volume_exists(model.model_volume_id):
                volume_functions.delete_volume(model.model_volume_id)

        self.db.purge()

    def post_task(self):
        with open(self.repo.input_zip, "rb") as r:
            task = self.db.add_task(model_human_readable_id=self.repo.model.human_readable_id,
                                    zip_file=r,
                                    uid=secrets.token_urlsafe(32))
        return task

    def test_get_task(self):
        model = self.test_add_model()
        ref_task = self.post_task()
        db_task = self.db.get_task(ref_task.uid)

        self.assertEqual(ref_task.dict(), db_task.dict())

    def test_get_tasks(self):
        with open(self.repo.input_zip, "rb") as r:
            task = self.post_task()

        tasks = self.db.get_tasks()
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].dict(), task.dict())

    def test_add_model(self):
        model = self.repo.model
        with open(self.repo.model_zip, "rb") as model_zip:
            echo_model = self.db.add_model(container_tag=model.container_tag,
                                           human_readable_id=model.human_readable_id,
                                           model_available=model.model_available,
                                           zip_file=model_zip,
                                           description=model.description,
                                           use_gpu=model.use_gpu,
                                           )
        model = self.db.get_model_by_human_readable_id(echo_model.human_readable_id)

        self.assertEqual(echo_model.dict(), model.dict())

        if echo_model.model_available:
            with open(self.repo.model_zip, "rb") as model_zip:
                with open(echo_model.model_zip, "rb") as db_model_zip:
                    self.assertEqual(model_zip.read(), db_model_zip.read())

        return echo_model

    def test_get_model(self):
        model = self.test_add_model()
        echo_model = self.db.get_model(model.uid)
        self.assertEqual(model.dict(), echo_model.dict())

    def test_get_models(self):
        model = self.test_add_model()
        models = self.db.get_models()
        self.assertEqual(len(models), 1)
        self.assertEqual(models[0].dict(), model.dict())

    def test_post_output(self):
        task = self.post_task()
        with open(self.repo.output_zip, "rb") as r:
            echo_task = self.db.post_output(task.uid, r)

        with open(task.output_zip, "rb") as ref_zip:
            with open(echo_task.output_zip, "rb") as echo_zip:
                self.assertEqual(ref_zip.read(), echo_zip.read())

    def test_dispatch_docker_job(self):
        model = self.test_add_model()
        task = self.post_task()
        self.job.set_task(task)
        self.job.set_model(model)
        self.job.execute()

    def test_add_failing_model(self):
        model = self.repo.failing_model
        with open(self.repo.model_zip, "rb") as model_zip:
            echo_model = self.db.add_model(container_tag=model.container_tag,
                                           human_readable_id=model.human_readable_id,
                                           model_available=model.model_available,
                                           zip_file=model_zip,
                                           description=model.description,
                                           use_gpu=model.use_gpu,
                                           )
        model = self.db.get_model_by_human_readable_id(echo_model.human_readable_id)

        self.assertEqual(echo_model.dict(), model.dict())

        if echo_model.model_available:
            with open(self.repo.model_zip, "rb") as model_zip:
                with open(echo_model.model_zip, "rb") as db_model_zip:
                    self.assertEqual(model_zip.read(), db_model_zip.read())

        return echo_model
    def test_dispatch_docker_job_error(self):
        model = self.test_add_failing_model()
        task = self.post_task()
        self.job.set_task(task)
        self.job.set_model(model)

        self.assertRaises(errors.ImageNotFound, self.job.execute)






