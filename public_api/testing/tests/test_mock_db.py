import unittest

import dotenv

from testing.mock_components.mock_db import MockDB
from testing.mock_components.mock_models_and_tasks import MockModelsAndTasks

dotenv.load_dotenv()


class TestDBImpl(unittest.TestCase):
    """
    This is a testing of functions in public_api/database/tests/test_mock_db.py
    """

    def setUp(self) -> None:
        self.base_dir = ".tmp"
        self.db = MockDB()
        self.repo = MockModelsAndTasks()

    def tearDown(self):
        self.db.purge()
        self.repo.purge()

    def test_get_tasks(self):
        task = self.test_post_task()
        tasks = self.db.get_tasks()
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].to_dict(), task.to_dict())

    def test_post_task(self):
        with open(self.repo.task.input_zip, "br") as r:
            task = self.db.post_task(uid=self.repo.task.uid,
                                      zip_file=r,
                                      model_human_readable_id=self.repo.model.human_readable_id)
        self.assertIsNotNone(task)
        return task

    def test_get_task_by_uid(self):
        task = self.test_post_task()
        echo = self.db.get_task_by_uid(task.uid)
        self.assertEqual(task.to_dict(), echo.to_dict())

    def test_get_task_by_id(self):
        task = self.test_post_task()
        echo = self.db.get_task_by_id(task.id)
        self.assertEqual(task.to_dict(), echo.to_dict())

    def test_post_output_by_uid(self):
        task = self.test_post_task()
        with open(self.repo.output_zip, "br") as r:
            self.db.post_output_by_uid(uid=task.uid, zip_file=r)

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

    def test_get_model_by_id(self):
        model = self.test_post_model()
        echo = self.db.get_model_by_id(model.id)
        self.assertEqual(model.to_dict(), echo.to_dict())

    def test_get_models(self):
        model = self.test_post_model()
        models = self.db.get_models()
        self.assertEqual(len(models), 1)
        self.assertEqual(model.to_dict(), models[0].to_dict())

        model = self.test_post_model()
        models = self.db.get_models()
        self.assertEqual(len(models), 2)
        self.assertEqual(model.to_dict(), models[1].to_dict())

    def test_get_output_by_uid(self):
        task = self.test_post_task()

        self.assertRaises(FileNotFoundError, self.db.get_output_zip_by_uid, uid=task.uid)

        self.test_post_output_by_uid()
        with self.db.get_output_zip_by_uid(task.uid) as r:
            print(r)
            self.assertIn(b"Important zip", r.read())
if __name__ == '__main__':
    unittest.main()
