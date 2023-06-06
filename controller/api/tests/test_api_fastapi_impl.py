import tarfile
import tempfile
import unittest
from io import BytesIO
from fastapi.testclient import TestClient

from api.api_fastapi_impl import APIFastAPIImpl
from database.tests.test_db_sqlite_impl import TestSQLiteImpl
from database.db_models import Task, Model
from testing.mock_components.mock_message_mq import MockMQRabbitImpl
from testing.mock_components.mock_models_and_tasks import MockModelsAndTasks
def generate_tar():
    tar_file = tempfile.TemporaryFile()
    with tarfile.TarFile.open(fileobj=tar_file, mode='w:gz') as tar_obj:
        tar_obj.add(__file__)
    tar_file.seek(0)
    return tar_file

class TestFastAPIImpl(unittest.TestCase):
    """
    This is a testing of functions in api/img/api/private_fastapi_impl.py
    """

    def setUp(self) -> None:
        self.db_tests = TestSQLiteImpl()
        self.db_tests.setUp()
        self.db = self.db_tests.db
        self.repo = MockModelsAndTasks()

        self.mq = MockMQRabbitImpl()
        self.api = APIFastAPIImpl(db=self.db, mq=self.mq)
        self.cli = TestClient(self.api)
        
        self.task_endpoint = "/api/tasks/"
        self.input_endpoint = "/api/tasks/inputs/"
        self.output_endpoint = "/api/tasks/outputs/"
        self.model_endpoint = "/api/models/"
        self.model_tar_endpoint = "/api/models/tars"
        self.x_token = self.api.x_token
        
    def tearDown(self) -> None:
        self.db_tests.tearDown()

    def test_hello_world(self):
        res = self.cli.get("/")
        self.assertIn("message", res.json().keys())
        self.assertIn("Hello world", res.json()["message"])

    def test_post_task(self):
        model = self.test_post_model()
        with generate_tar() as model_tar:
            res = self.cli.post(self.task_endpoint,
                            params={"human_readable_id": self.repo.model.human_readable_id},
                            files={"tar_file": model_tar})
        self.assertEqual(res.status_code, 200)
        task = res.json()
        self.assertEqual(task["model"]["human_readable_id"], self.repo.model.human_readable_id)
        return res.json()

    def test_get_tasks(self):
        task = self.test_post_task()
        res = self.cli.get(self.task_endpoint,
                           headers={"X-Token": self.x_token})
        self.assertEqual(200, res.status_code)
        tasks = res.json()
        self.assertEqual(len(tasks), 1)
        print(task)
        print(tasks)
        self.assertEqual(task, tasks[0])
        return tasks

    def test_get_task_by_uid(self):
        task = self.test_post_task()
        res = self.cli.get(self.task_endpoint,
                           params={"task_id": task["id"]},
                           headers={"X-Token": self.x_token})
        print(res)
        self.assertEqual(res.status_code, 200)  # Pending task
        echo = res.json()
        print(type(echo))
        self.assertDictEqual(task, echo)
        return echo

    def test_delete_task_by_uid_intended(self):
        task = self.test_post_task()
        res = self.cli.delete(self.task_endpoint,
                              params={"uid": str(task["uid"])},
                              headers={"X-Token": self.x_token})

        self.assertEqual(res.status_code, 200)
        echo = res.json()
        self.assertTrue(echo["is_deleted"])

    def test_delete_task_by_uid_TaskNotFoundException(self):
        res = self.cli.delete(self.task_endpoint,
                              params={"uid": "ImportantButNonExistingUID"},
                              headers={"X-Token": self.x_token})
        self.assertEqual(res.status_code, 554)

    def test_set_task_status_by_uid_finished_tar_not_exist(self):
        task = self.test_post_task()
        self.assertEqual(task["status"], -1)

        # set status to finished
        res = self.cli.put(self.task_endpoint,
                           params={"task_id": task["id"], "status": 1},
                           headers={"X-Token": self.x_token})

        self.assertEqual(res.status_code, 200)
        echo = res.json()
        self.assertEqual(echo["status"], 1)

        # Get to check status code
        res = self.cli.get(self.output_endpoint,
                           params={"uid": task["uid"]},
                           headers={"X-Token": self.x_token})
        self.assertEqual(res.status_code, 553)

    def test_set_task_status_by_uid_pending(self):
        task = self.test_post_task()
        self.assertEqual(task["status"], -1)

        # Get to check status code
        res = self.cli.get(self.output_endpoint,
                           headers={"X-Token": self.x_token},
                           params={"uid": task["uid"]})
        self.assertEqual(res.status_code, 551)

    def test_set_task_status_by_uid_failed(self):
        task = self.test_post_task()
        self.assertEqual(task["status"], -1)

        # set status to finished
        res = self.cli.put(self.task_endpoint,
                           params={"task_id": task["id"], "status": 0},
                           headers={"X-Token": self.x_token})
        self.assertEqual(res.status_code, 200)
        echo = res.json()
        self.assertEqual(echo["status"], 0)

        # Get to check status code
        res = self.cli.get(self.output_endpoint,
                           params={"uid": task["uid"]},
                           headers={"X-Token": self.x_token})
        self.assertEqual(res.status_code, 552)

    def test_post_model(self):
        with generate_tar() as r:
            res = self.cli.post(self.model_endpoint,
                                params={
                                    "container_tag": self.repo.model.container_tag,
                                    "human_readable_id": self.repo.model.human_readable_id,
                                    "description": self.repo.model.description,
                                    "model_available": self.repo.model.model_available,
                                    "use_gpu": self.repo.model.use_gpu
                                },
                                files={"tar_file": r},
                                headers={"X-Token": self.x_token})

        self.assertEqual(res.status_code, 200)
        echo = res.json()
        self.assertEqual(echo["container_tag"], self.repo.model.container_tag)
        return res.json()

    def test_get_input_tar(self):
        task = self.test_post_task()
        
        res = self.cli.get(self.input_endpoint,
                            params={
                                "task_id": task["id"]
                            },
                            headers={"X-Token": self.x_token})
        res_file = BytesIO(res.content)
        tar = tarfile.TarFile.open(fileobj=res_file)
        self.assertIn(tar.getmembers()[0].path, __file__)

    def test_post_output_tar(self):
        task = self.test_post_task()
        with generate_tar() as r:
            res = self.cli.post(self.output_endpoint,
                                params={
                                    "task_id": task["id"]
                                },
                                files={"tar_file": r},
                                headers={"X-Token": self.x_token})
            self.assertTrue(res.status_code == 200)
            
            echo_res = self.cli.get(self.output_endpoint,
                                      params={"uid": task["uid"]},
                                      headers={"X-Token": self.x_token})
            # orig_tar = tarfile.TarFile(fileobj=BytesIO(r))
            # echo_tar = tarfile.TarFile(fileobj=BytesIO(echo_res.content))
            r.seek(0)
            self.assertEqual(r.read(), BytesIO(echo_res.content).read())

    def test_get_model_tar(self):
        model = self.test_post_model()

        res = self.cli.get(self.model_tar_endpoint,
                           params={
                               "model_id": model["id"]
                           },
                           headers={"X-Token": self.x_token})
        self.assertEqual(res.status_code, 200)
        print(res.content)
        res_file = BytesIO(res.content)
        tar = tarfile.TarFile.open(fileobj=res_file)
        self.assertIn(tar.getmembers()[0].path, __file__)

if __name__ == '__main__':
    unittest.main()
