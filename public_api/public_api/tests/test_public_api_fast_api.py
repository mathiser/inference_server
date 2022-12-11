import os
import unittest

from database.db_impl import DBImpl
from database.tests.test_db_requests_impl import TestDBImpl

os.environ["TZ"] = "Europe/Copenhagen"
os.environ["API_HOSTNAME"] = "private_api"
os.environ["API_PORT"] = "7000"
os.environ["API_URL"] = "http://private_api:7000"
os.environ["LOG_LEVEL"] = "20"

os.environ["DATA_DIR"] = "/opt/app/data/"
os.environ["API_TASKS"] = "/api/tasks/"

os.environ["API_OUTPUT_ZIPS"] = "/api/tasks/outputs/"
os.environ["API_INPUT_ZIPS"] = "/api/tasks/inputs/"
os.environ["API_MODELS"] = "/api/models/"
os.environ["API_MODELS_BY_HUMAN_READABLE_ID"] = "/api/models/human_readable_id/"
os.environ["API_MODEL_ZIPS"] = "/api/models/zips/"

from public_api.public_api_fast_api_impl import PublicFastAPI
from database.tests.mock_fast_api_testclient import MockDBClient
from testing.mock_components.mock_models_and_tasks import MockModelsAndTasks
from interfaces.db_models import Model

class TestPublicAPIFastAPI(unittest.TestCase):
    """
    This is a testing of functions in public_api/public_api_fast_api_impl.py
    """

    def setUp(self) -> None:
        self.base_dir = ".tmp"
        self.repo = MockModelsAndTasks()
        self.db_tests = TestDBImpl()
        self.db_tests.setUp()
        self.db_backend = DBImpl(self.db_tests.db_client)
    def tearDown(self):
        self.repo.purge()
        self.db_tests.private_api.purge()

    def test_hello_world(self):
        app = PublicFastAPI(db=self.db_backend)
        db_client = MockDBClient(app)
        res = db_client.get("/").json()
        self.assertIn("message", res.keys())
        self.assertIn("Hello world", res["message"])

    def test_public_post_task(self):
        os.environ["ALLOW_PUBLIC_POST_MODEL"] = "True"
        app = PublicFastAPI(db=self.db_backend)
        db_client = MockDBClient(app)

        model = self.test_public_post_model()
        with open(self.repo.input_zip, "rb") as r:
            res = db_client.post(os.environ['API_TASKS'],
                                 params={"model_human_readable_id": self.repo.model.human_readable_id},
                                 files={"zip_file": r})
        print(res.content)
        self.assertEqual(res.status_code, 200)
        return res.json()

    def test_public_post_model(self):
        os.environ["ALLOW_PUBLIC_POST_MODEL"] = "True"
        app = PublicFastAPI(db=self.db_backend)
        db_client = MockDBClient(app)

        with open(self.repo.model_zip, "rb") as r:
            res = db_client.post(os.environ['API_MODELS'],
                                 params={
                                     "container_tag": self.repo.model.container_tag,
                                     "human_readable_id": self.repo.model.human_readable_id,
                                     "description": self.repo.model.description,
                                     "model_available": self.repo.model.model_available,
                                     "use_gpu": self.repo.model.use_gpu
                                 },
                                 files={"zip_file": r})

        self.assertEqual(res.status_code, 200)
        echo = Model(**res.json())
        self.assertEqual(echo.container_tag, self.repo.model.container_tag)
        return Model(**res.json())

    def test_public_post_model_NOTALLOWED(self):
        os.environ["ALLOW_PUBLIC_POST_MODEL"] = ""
        app = PublicFastAPI(db=self.db_backend)
        db_client = MockDBClient(app)

        with open(self.repo.model_zip, "rb") as r:
            res = db_client.post(os.environ['API_MODELS'],
                                 params={
                                     "container_tag": self.repo.model.container_tag,
                                     "human_readable_id": self.repo.model.human_readable_id,
                                     "description": self.repo.model.description,
                                     "model_available": self.repo.model.model_available,
                                     "use_gpu": self.repo.model.use_gpu
                                 },
                                 files={"zip_file": r})
        self.assertEqual(res.status_code, 405)

    # def test_public_get_output_zip_by_uid(self):
    #     model = self.test_public_post_model()
    #     task = self.test_public_post_task()


if __name__ == '__main__':
    unittest.main()
