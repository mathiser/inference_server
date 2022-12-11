import os
import secrets
import unittest

os.environ["TZ"] = "Europe/Copenhagen"
os.environ["API_HOSTNAME"] = "private_api"
os.environ["API_PORT"] = "7000"
os.environ["API_URL"] = "http://private_api:7000"
os.environ["LOG_LEVEL"] = "10"

os.environ["DATA_DIR"] = "/opt/app/data/"
os.environ["API_TASKS"] = "/api/tasks/"

os.environ["API_OUTPUT_ZIPS"] = "/api/tasks/outputs/"
os.environ["API_INPUT_ZIPS"] = "/api/tasks/inputs/"
os.environ["API_MODELS"] = "/api/models/"
os.environ["API_MODELS_BY_HUMAN_READABLE_ID"] = "/api/models/human_readable_id/"
os.environ["API_MODEL_ZIPS"] = "/api/models/zips/"

from database.db_impl import DBImpl
from database.tests.mock_fast_api_testclient import MockDBClient
from testing.mock_components.mock_models_and_tasks import MockModelsAndTasks
from database.tests.mock_private_fast_api import MockPrivateFastAPI

class TestDBImpl(unittest.TestCase):
    """
    This is a testing of functions in public_api/database/tests/test_mock_db.py
    """

    def setUp(self) -> None:
        self.base_dir = ".tmp"
        self.repo = MockModelsAndTasks()
        self.private_api = MockPrivateFastAPI()

        self.db_client = MockDBClient(self.private_api)
        self.db = DBImpl(db_client=self.db_client)

    def tearDown(self):
        self.repo.purge()
        self.private_api.purge()

    def test_post_task_intended(self):
        with open(self.repo.task.input_zip, "br") as r:
            echo = self.db.post_task(zip_file=r,
                                     model_human_readable_id=self.repo.model.human_readable_id,
                                     uid=secrets.token_urlsafe())
        self.assertIsNotNone(echo)
        self.assertEqual(echo["model_human_readable_id"], self.repo.model.human_readable_id)
        self.assertIn("uid", echo.keys())

        return echo

    def test_post_model_intended(self):
        with open(self.repo.model_zip, "br") as r:
            model = self.db.post_model(container_tag=self.repo.model.container_tag,
                                       human_readable_id=self.repo.model.human_readable_id,
                                       zip_file=r,
                                       description=self.repo.model.description,
                                       model_available=self.repo.model.model_available,
                                       use_gpu=self.repo.model.use_gpu)
        self.assertIsNotNone(model)
        return model

    def test_get_models(self):
        model = self.test_post_model_intended()
        print(f"model: {model}")
        models = self.db.get_models()
        print(f"models: {models}")
        self.assertEqual(len(models), 1)

        model = self.test_post_model_intended()
        models = self.db.get_models()
        self.assertEqual(len(models), 2)

    # This test must be made at some point.
    # def test_get_output_by_uid(self):
    #     task = self.test_post_task_intended()
    #
    #     res = self.db.get_output_zip_by_uid(task["uid"])
    #     self.assertEqual()


if __name__ == '__main__':
    unittest.main()
