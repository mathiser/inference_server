import os
import shutil
import unittest

import dotenv
from fastapi.testclient import TestClient

from database.models import Task
from fast_api.fastapi_impl import FastAPIImpl
from api.private_api_impl import PrivateAPIImpl
from .mock_ups.mock_db import MockDB
from .mock_ups.mock_mq import MockMQ

dotenv.load_dotenv()


class TestFastAPIImpl(unittest.TestCase):
    """
    This is a tests of functions in api/img/api/private_fastapi_impl.py
    """

    def setUp(self) -> None:
        self.hostname = "localhost"
        self.port = 6000
        self.base_url = f"http://{self.hostname}:{self.port}"

        self.db = MockDB()
        self.mq = MockMQ()
        dotenv.load_dotenv()

        api_backend = PrivateAPIImpl(db=self.db, mq=self.mq)
        app = FastAPIImpl(api=api_backend)
        self.cli = TestClient(app)

    def tearDown(self) -> None:
        self.db.purge()

    def test_hello_world(self):
        res = self.cli.get(self.base_url)
        self.assertIn("message", res.json().keys())
        self.assertIn("Hello world", res.json()["message"])

    def test_post_tast(self):
        with open(self.db.input_zip, "rb") as r:
            res = self.cli.post(os.environ['POST_TASK'],
                               params={"human_readable_ids": self.db.task1.human_readable_ids},
                               files={"zip_file": r})
        self.assertEqual(res.status_code, 200)
        return Task(**res.json())

    def test_get_tasks(self):
        task = self.test_post_tast()
        res = self.cli.get(os.environ.get("GET_TASKS"))
        self.assertEqual(res.status_code, 200)
        tasks = [Task(**t) for t in res.json()]
        self.assertEqual(len(tasks), 1)
        self.assertEqual(task.to_dict(), tasks[0].to_dict())
        return tasks

    def test_get_task_by_id(self):
        task = self.test_post_tast()
        res = self.cli.get(os.environ['GET_TASK_BY_ID'] + str(task.id))
        self.assertEqual(res.status_code, 200)
        echo = Task(**res.json())
        self.assertEqual(task.to_dict(), echo.to_dict())

if __name__ == '__main__':
    unittest.main()

