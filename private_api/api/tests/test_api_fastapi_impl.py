import os
import unittest

import dotenv
from fastapi.testclient import TestClient

from database.models import Task, Model
from api.api_fastapi_impl import APIFastAPIImpl
from testing.mock_components.mock_db import MockDB
from testing.mock_components.mock_mq import MockMQ
from testing.mock_components.mock_models_and_tasks import MockModelsAndTasks


dotenv.load_dotenv(".env")

class TestFastAPIImpl(unittest.TestCase):
    """
    This is a testing of functions in api/img/api/private_fastapi_impl.py
    """

    def setUp(self) -> None:
        self.hostname = "localhost"
        self.port = 6000
        self.base_url = f"http://{self.hostname}:{self.port}"

        self.db = MockDB()
        self.repo = MockModelsAndTasks()
        self.mq = MockMQ()
        dotenv.load_dotenv()

        app = APIFastAPIImpl(db=self.db, mq=self.mq)
        self.cli = TestClient(app)

    def tearDown(self) -> None:
        self.db.purge()

    def test_hello_world(self):
        res = self.cli.get(self.base_url)
        self.assertIn("message", res.json().keys())
        self.assertIn("Hello world", res.json()["message"])

    def test_post_task(self):
        model = self.test_post_model()
        with open(self.repo.input_zip, "rb") as r:
            res = self.cli.post(os.environ['POST_TASK'],
                                params={"model_human_readable_id": self.repo.model.human_readable_id},
                                files={"zip_file": r})
        print(res.content)
        self.assertEqual(res.status_code, 200)
        return Task(**res.json())

    def test_get_tasks(self):
        self.test_post_model()
        task = self.test_post_task()
        res = self.cli.get(os.environ.get("GET_TASKS"))
        self.assertEqual(res.status_code, 200)
        tasks = [Task(**t) for t in res.json()]
        self.assertEqual(len(tasks), 1)
        self.assertEqual(task.to_dict(), tasks[0].to_dict())
        return tasks

    def test_get_task_by_id(self):
        task = self.test_post_task()
        res = self.cli.get(os.environ['GET_TASK_BY_ID'] + str(task.id))
        self.assertEqual(res.status_code, 200)
        echo = Task(**res.json())
        self.assertEqual(task.to_dict(), echo.to_dict())

    def test_get_task_by_id(self):
        task = self.test_post_task()
        res = self.cli.get(os.environ['GET_TASK_BY_ID'] + str(task.id))
        self.assertEqual(res.status_code, 200)
        echo = Task(**res.json())
        self.assertEqual(task.to_dict(), echo.to_dict())
    def test_post_model(self):
        with open(self.repo.model_zip, "rb") as r:
            res = self.cli.post(os.environ['POST_MODEL'],
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
