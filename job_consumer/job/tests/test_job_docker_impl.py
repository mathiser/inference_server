import secrets
import unittest

from docker_helper import volume_functions
from job.job_docker_impl import JobDockerImpl
from testing.mock_components.mock_db import MockDB

from testing.mock_components.mock_models_and_tasks import MockModelsAndTasks


class TestJob(unittest.TestCase):
    def setUp(self) -> None:
        self.db = MockDB()
        self.repo = MockModelsAndTasks()
        self.job = JobDockerImpl(db=self.db)

    def tearDown(self) -> None:
        for task in self.db.get_tasks():
            if volume_functions.volume_exists(task.input_volume_uuid):
                volume_functions.delete_volume(task.input_volume_uuid)

            if volume_functions.volume_exists(task.output_volume_uuid):
                volume_functions.delete_volume(task.output_volume_uuid)

        for model in self.db.get_models():
            if volume_functions.volume_exists(model.model_volume_uuid):
                volume_functions.delete_volume(model.model_volume_uuid)

        self.repo.purge()
        self.db.purge()

    def test_volume_methods(self):
        volume = volume_functions.create_empty_volume()
        self.assertIsNotNone(volume)
        self.assertTrue(volume_functions.volume_exists(volume))
        volume_functions.delete_volume(volume_uuid=volume)
        self.assertFalse(volume_functions.volume_exists(volume_uuid=volume))

    def test_add_task(self):
        with open(self.repo.input_zip, "rb") as r:
            task = self.db.add_task(model_human_readable_id=self.repo.model.human_readable_id,
                                    zip_file=r,
                                    uid=secrets.token_urlsafe(32))
        return task

    def test_get_task_by_id(self):
        model = self.test_add_model()
        ref_task = self.test_add_task()
        db_task = self.db.get_task_by_id(ref_task.id)

        self.assertEqual(ref_task.to_dict(), db_task.to_dict())

    def test_get_task_by_uid(self):
        ref_task = self.test_add_task()
        db_task = self.db.get_task_by_uid(ref_task.uid)

        self.assertEqual(ref_task.to_dict(), db_task.to_dict())

    def test_get_tasks(self):
        with open(self.repo.input_zip, "rb") as r:
            task = self.test_add_task()

        tasks = self.db.get_tasks()
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].to_dict(), task.to_dict())

    def test_add_model(self):
        model = self.repo.model
        with open(self.repo.model_zip, "rb") as model_zip:
            echo_model = self.db.add_model(container_tag=model.container_tag,
                                           human_readable_id=model.human_readable_id,
                                           model_available=model.model_available,
                                           zip_file=model_zip,
                                           description=model.description,
                                           input_mountpoint=model.input_mountpoint,
                                           output_mountpoint=model.output_mountpoint,
                                           use_gpu=model.use_gpu,
                                           model_mountpoint=model.model_mountpoint
                                           )
        model = self.db.get_model_by_human_readable_id(echo_model.human_readable_id)

        self.assertEqual(echo_model.to_dict(), model.to_dict())

        if echo_model.model_available:
            with open(self.repo.model_zip, "rb") as model_zip:
                with open(echo_model.model_zip, "rb") as db_model_zip:
                    self.assertEqual(model_zip.read(), db_model_zip.read())

        return echo_model

    def test_get_model_by_id(self):
        model = self.test_add_model()
        echo_model = self.db.get_model_by_id(model.id)
        self.assertEqual(model.to_dict(), echo_model.to_dict())

    def test_get_models(self):
        model = self.test_add_model()
        models = self.db.get_models()
        self.assertEqual(len(models), 1)
        self.assertEqual(models[0].to_dict(), model.to_dict())

    def test_post_output_by_uid(self):
        task = self.test_add_task()
        with open(self.repo.output_zip, "rb") as r:
            echo_task = self.db.post_output_by_uid(task.uid, r)

        with open(task.output_zip, "rb") as ref_zip:
            with open(echo_task.output_zip, "rb") as echo_zip:
                self.assertEqual(ref_zip.read(), echo_zip.read())


    def test_dispatch_docker_job(self):
        model = self.test_add_model()
        task = self.test_add_task()
        self.job.set_task(task)
        self.job.set_model(model)
        self.job.execute()

