import tempfile
import unittest

import dotenv

from database.db_requests_impl import DBRequestsImpl
from testing.mock_components.mock_db import MockDB
from testing.mock_components.mock_fast_api_testclient import MockDBClient
from testing.mock_components.mock_models_and_tasks import MockModelsAndTasks
from testing.mock_components.mock_private_fast_api import MockPrivateFastAPI

dotenv.load_dotenv()


class TestDBImpl(unittest.TestCase):
    """
    This is a testing of functions in public_api/database/tests/test_mock_db.py
    """

    def setUp(self) -> None:
        self.base_dir = ".tmp"
        self.repo = MockModelsAndTasks()
        self.db_backend = MockDB()
        self.app = MockPrivateFastAPI(db=self.db_backend)
        self.db_client = MockDBClient(self.app)
        self.db = DBRequestsImpl(db_client=self.db_client)

    def tearDown(self):
        self.repo.purge()
        self.db_backend.purge()

    def test_post_task(self):
        with open(self.repo.task.input_zip, "br") as r:
            task = self.db.post_task(zip_file=r,
                                     model_human_readable_id=self.repo.model.human_readable_id)
        self.assertIsNotNone(task)
        return task

    def test_post_model(self):
        with open(self.repo.model_zip, "br") as r:
            model = self.db.post_model(container_tag=self.repo.model.container_tag,
                                       human_readable_id=self.repo.model.human_readable_id,
                                       input_mountpoint=self.repo.model.input_mountpoint,
                                       output_mountpoint=self.repo.model.output_mountpoint,
                                       zip_file=r,
                                       model_mountpoint=self.repo.model.model_mountpoint,
                                       description=self.repo.model.description,
                                       model_available=self.repo.model.model_available,
                                       use_gpu=self.repo.model.use_gpu)
        self.assertIsNotNone(model)
        return model

    def test_get_models(self):
        model = self.test_post_model()
        print(f"model: {model}")
        models = self.db.get_models()
        print(f"models: {models}")
        self.assertEqual(len(models), 1)
        for k, v in model.items():
            self.assertIn(k, models[0].keys())
            self.assertEqual(models[0][k], v)

        model = self.test_post_model()
        models = self.db.get_models()
        self.assertEqual(len(models), 2)

    def test_get_output_by_uid(self):
        task = self.test_post_task()
        print(f"test_get_output_by_uid: {task}")

        with self.db.get_output_zip_by_uid(task["uid"]) as tmp_file:
            self.assertIn(b"Hello hello world", tmp_file.read())


if __name__ == '__main__':
    unittest.main()
