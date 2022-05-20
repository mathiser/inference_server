import os
import unittest

import dotenv

from public_api.public_api_fast_api_impl import PublicFastAPI
from testing.mock_components.mock_db import MockDB
from testing.mock_components.mock_fast_api_testclient import MockDBClient
from testing.mock_components.mock_models_and_tasks import MockModelsAndTasks
from testing.mock_components.models import Task, Model

dotenv.load_dotenv()


class TestPublicAPIFastAPI(unittest.TestCase):
    """
    This is a testing of functions in public_api/public_api_fast_api_impl.py
    """

    def setUp(self) -> None:
        self.base_dir = ".tmp"
        self.repo = MockModelsAndTasks()
        self.db_backend = MockDB()
        self.app = PublicFastAPI(db=self.db_backend)
        self.db_client = MockDBClient(self.app)

    def tearDown(self):
        self.repo.purge()
        self.db_backend.purge()

    def test_hello_world(self):
        res = self.db_client.get("/").json()
        self.assertIn("message", res.keys())
        self.assertIn("Hello world", res["message"])

    def test_post_task(self):
        model = self.test_post_model()
        with open(self.repo.input_zip, "rb") as r:
            res = self.db_client.post(os.environ['PUBLIC_POST_TASK'],
                                params={"model_human_readable_id": self.repo.model.human_readable_id},
                                files={"zip_file": r})
        print(res.content)
        self.assertEqual(res.status_code, 200)
        return Task(**res.json())

    def test_post_model(self):
        with open(self.repo.model_zip, "rb") as r:
            res = self.db_client.post(os.environ['PUBLIC_POST_MODEL'],
                                params={
                                    "container_tag": self.repo.model.container_tag,
                                    "human_readable_id": self.repo.model.human_readable_id,
                                    "input_mountpoint": self.repo.model.input_mountpoint,
                                    "output_mountpoint": self.repo.model.output_mountpoint,
                                    "model_mountpoint": self.repo.model.model_mountpoint,
                                    "description": self.repo.model.description,
                                    "model_available": self.repo.model.model_available,
                                    "use_gpu": self.repo.model.use_gpu
                                },
                                files={"zip_file": r})

        self.assertEqual(res.status_code, 200)
        echo = Model(**res.json())
        self.assertEqual(echo.container_tag, self.repo.model.container_tag)
        return Model(**res.json())


if __name__ == '__main__':
    unittest.main()
