import unittest
import dotenv
from api.private_api_impl import PrivateAPIImpl
from testing.mock_components.mock_db import MockDB
from testing.mock_components.mock_mq import MockMQ
from testing.mock_components.mock_models_and_tasks import MockModelsAndTasks

dotenv.load_dotenv()


class TestPrivateAPIImpl(unittest.TestCase):
    """
    This is a testing of functions in api/img/api/private_fastapi_impl.py
    """

    def setUp(self) -> None:
        self.base_dir = ".tmp"
        self.db = MockDB()
        self.repo = MockModelsAndTasks()
        self.mq = MockMQ()
        self.api = PrivateAPIImpl(db=self.db, mq=self.mq)

    def tearDown(self):
        self.db.purge()
        self.repo.purge()

    def test_hello_world(self):
        self.assertIn("message", self.api.hello_world().keys())
        self.assertIn("Hello world", self.api.hello_world()["message"])

    def test_get_tasks(self):
        task = self.test_post_task()
        tasks = self.api.get_tasks()
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].to_dict(), task.to_dict())

    def test_post_task(self):
        with open(self.repo.task.input_zip, "br") as r:
            task = self.api.post_task(uid=self.repo.task.uid,
                                      zip_file=r,
                                      model_human_readable_id=self.repo.model.human_readable_id)
        self.assertIsNotNone(task)
        return task

    def test_get_task_by_uid(self):
        task = self.test_post_task()
        echo = self.api.get_task_by_uid(task.uid)
        self.assertEqual(task.to_dict(), echo.to_dict())

    def test_get_task_by_id(self):
        task = self.test_post_task()
        echo = self.api.get_task_by_id(task.id)
        self.assertEqual(task.to_dict(), echo.to_dict())

    def test_post_output_by_uid(self):
        task = self.test_post_task()
        with open(self.db.output_zip, "br") as r:
            self.api.post_output_by_uid(uid=task.uid, zip_file=r)

    def test_post_model(self):
        with open(self.db.model_zip, "br") as r:
            model = self.api.post_model(
                                description=self.repo.model.description,
                                human_readable_id=self.repo.model.human_readable_id,
                                container_tag=self.repo.model.container_tag,
                                input_mountpoint=self.repo.model.input_mountpoint,
                                output_mountpoint=self.repo.model.output_mountpoint,
                                model_mountpoint=self.repo.model.model_mountpoint,
                                model_available=self.repo.model.model_available,
                                use_gpu=self.repo.model.use_gpu,
                                zip_file=r)
        self.assertIsNotNone(model)
        return model

    def test_get_model_by_id(self):
        model = self.test_post_model()
        echo = self.api.get_model_by_id(model.id)
        self.assertEqual(model.to_dict(), echo.to_dict())

    def test_get_models(self):
        model = self.test_post_model()
        models = self.api.get_models()
        self.assertEqual(len(models), 1)
        self.assertEqual(model.to_dict(), models[0].to_dict())

        model = self.test_post_model()
        models = self.api.get_models()
        self.assertEqual(len(models), 2)
        self.assertEqual(model.to_dict(), models[1].to_dict())

if __name__ == '__main__':
    unittest.main()
