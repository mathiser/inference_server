import os

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

import shutil
import tempfile
import unittest

from fastapi.testclient import TestClient

from api.api_fastapi_impl import APIFastAPIImpl
from database.tests.test_db_sqlite_impl import TestSQLiteImpl
from interfaces.db_models import Task, Model
from message_queue.tests.test_mq_rabbit_impl import TestMessageQueueRabbitMQImpl
from testing.mock_components.mock_models_and_tasks import MockModelsAndTasks


class TestFastAPIImpl(unittest.TestCase):
    """
    This is a testing of functions in api/img/api/private_fastapi_impl.py
    """

    def setUp(self) -> None:
        self.tmp_basedir = tempfile.mkdtemp()
        self.db_tests = TestSQLiteImpl()
        self.db_tests.setUp()
        self.db = self.db_tests.db
        self.repo = MockModelsAndTasks()
        self.mq_tests = TestMessageQueueRabbitMQImpl()
        self.mq_tests.setUp()
        self.mq = self.mq_tests.mq_client

        api = APIFastAPIImpl(db=self.db, mq=self.mq)
        self.cli = TestClient(api.app)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp_basedir)
        self.db.purge()

    def test_hello_world(self):
        res = self.cli.get("/")
        self.assertIn("message", res.json().keys())
        self.assertIn("Hello world", res.json()["message"])

    def test_post_task(self):
        model = self.test_post_model()
        with open(self.repo.input_zip, "rb") as r:
            res = self.cli.post(os.environ['API_TASKS'],
                                params={"model_human_readable_id": self.repo.model.human_readable_id},
                                files={"zip_file": r})
        self.assertEqual(res.status_code, 200)
        return Task(**res.json())

    def test_get_tasks(self):
        task = self.test_post_task()
        res = self.cli.get(os.environ.get("API_TASKS"))
        self.assertEqual(res.status_code, 200)
        tasks = [Task(**t) for t in res.json()]
        self.assertEqual(len(tasks), 1)
        self.assertEqual(task.dict(), tasks[0].dict())
        return tasks

    def test_get_task_by_uid(self):
        task = self.test_post_task()
        res = self.cli.get(os.environ['API_TASKS'] + str(task.uid))
        self.assertEqual(res.status_code, 200)
        echo = Task(**res.json())
        self.assertEqual(task.dict(), echo.dict())
        return echo

    def test_delete_task_by_uid_intended(self):
        task = self.test_post_task()
        res = self.cli.delete(os.environ['API_TASKS'] + str(task.uid))
        self.assertEqual(res.status_code, 200)
        echo = Task(**res.json())
        self.assertNotEqual(task.dict(), echo.dict())
        self.assertTrue(echo.is_deleted)

    def test_delete_task_by_uid_TaskNotFoundException(self):
        res = self.cli.delete(os.environ['API_TASKS'] + "ImportantButNonExistingUID")
        self.assertEqual(res.status_code, 554)

    def test_set_task_status_by_uid_finished_zip_not_exist(self):
        task = self.test_post_task()
        self.assertEqual(task.status, -1)

        # set status to finished
        res = self.cli.put(os.environ['API_TASKS'], params={"uid": task.uid, "status": 1})
        self.assertEqual(res.status_code, 200)
        echo = Task(**res.json())
        self.assertEqual(echo.status, 1)

        # Get to check status code
        res = self.cli.get(os.environ['API_OUTPUT_ZIPS'] + str(task.uid))
        self.assertEqual(res.status_code, 553)

    def test_set_task_status_by_uid_pending(self):
        task = self.test_post_task()
        self.assertEqual(task.status, -1)

        # Get to check status code
        res = self.cli.get(os.environ['API_OUTPUT_ZIPS'] + str(task.uid))
        self.assertEqual(res.status_code, 551)

    def test_set_task_status_by_uid_failed(self):
        task = self.test_post_task()
        self.assertEqual(task.status, -1)

        # set status to finished
        res = self.cli.put(os.environ['API_TASKS'], params={"uid": task.uid, "status": 0})
        self.assertEqual(res.status_code, 200)
        echo = Task(**res.json())
        self.assertEqual(echo.status, 0)

        # Get to check status code
        res = self.cli.get(os.environ['API_OUTPUT_ZIPS'] + str(task.uid))
        self.assertEqual(res.status_code, 552)

    def test_post_model(self):
        with open(self.repo.model_zip, "rb") as r:
            res = self.cli.post(os.environ['API_MODELS'],
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


if __name__ == '__main__':
    #unittest.main()
    suite = unittest.TestSuite()
    suite.addTest(TestFastAPIImpl())
    unittest.TextTestRunner().run(suite)
