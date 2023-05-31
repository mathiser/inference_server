import os
os.environ["LOG_LEVEL"] = "10"

import unittest

from database.db_exceptions import TaskNotFoundException, \
    ZipFileMissingException, ContradictingZipFileException, ModelNotFoundException

from database.db_sql_impl import DBSQLiteImpl
from testing.mock_components.mock_models_and_tasks import MockModelsAndTasks

class TestSQLiteImpl(unittest.TestCase):
    """
    This is a testing of functions in database/test_db_sqlite_impl.py
    """
    def setUp(self) -> None:
        self.base_dir = ".tmp"
        self.repo = MockModelsAndTasks()
        self.db = DBSQLiteImpl(base_dir=self.base_dir)

    def tearDown(self):
        self.db.purge()
        self.repo.purge()

    def test_post_task_intended(self):
        with open(self.repo.input_zip, "rb") as r:
            task = self.db.post_task(model_human_readable_id=self.repo.model.human_readable_id,
                                     zip_file=r)
        self.assertIn(self.repo.model.human_readable_id, task.model_human_readable_id)
        return task

    def test_set_task_status_intended(self):
        task = self.test_post_task_intended()
        self.assertEqual(task.status, -1)
        self.db.set_task_status(task.uid, 0)

        new_retrieval = self.db.get_task(task.uid)
        self.assertEqual(new_retrieval.status, 0)

        return task

    def test_get_task_intended(self):
        ref_task = self.test_post_task_intended()
        db_task = self.db.get_task(ref_task.uid)

        self.assertEqual(ref_task.dict(), db_task.dict())

    def test_get_task_TaskNotFoundException(self):
        self.assertRaises(TaskNotFoundException, self.db.get_task, "HeltUniktUid")

    def test_get_tasks(self):
        task = self.test_post_task_intended()
        tasks = self.db.get_tasks()
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].dict(), task.dict())

    def test_delete_task_intended(self):
        task = self.test_post_task_intended()
        self.assertFalse(task.is_deleted)
        self.db.delete_task(task.uid)

        self.assertRaises(TaskNotFoundException, self.db.get_task, uid=task.uid)

    def test_delete_task_TaskNotFoundException(self):
        self.assertRaises(TaskNotFoundException, self.db.get_task, uid="some uid that does not exist")


    def test_add_model_intended(self):
        model = self.repo.model
        with open(self.repo.model_zip, "rb") as model_zip:
            echo_model = self.db.post_model(container_tag=model.container_tag,
                                            human_readable_id=model.human_readable_id,
                                            model_available=model.model_available,
                                            zip_file=model_zip,
                                            description=model.description,
                                            use_gpu=model.use_gpu,
                                            )
        model = self.db.get_model(human_readable_id=echo_model.human_readable_id)

        self.assertEqual(echo_model.dict(), model.dict())

        if echo_model.model_available:
            with open(self.repo.model_zip, "rb") as model_zip:
                with open(echo_model.model_zip, "rb") as db_model_zip:
                    self.assertEqual(model_zip.read(), db_model_zip.read())

        return echo_model

    def test_add_model_ZipFileMissingException(self):
        model = self.repo.model
        kw = {
            "container_tag": model.container_tag,
            "human_readable_id": model.human_readable_id,
            "model_available": model.model_available,
            "zip_file": None,
            "description": model.description,
            "use_gpu": model.use_gpu,
        }
        self.assertRaises(ZipFileMissingException, self.db.post_model, **kw)


    def test_add_model_bare_minimum(self):
        model = self.repo.model
        kw = {
            "container_tag": model.container_tag,
            "human_readable_id": model.human_readable_id,
        }
        model = self.db.post_model(**kw)
        self.assertIsNotNone(model)
        self.assertIsNotNone(model.id)
        self.assertIsNotNone(model.uid)
        self.assertEqual(model.human_readable_id, kw["human_readable_id"])
        self.assertIsNone(model.description)
        self.assertEqual(model.container_tag, kw["container_tag"])
        self.assertTrue(model.use_gpu)
        self.assertFalse(model.model_available)
        self.assertIsNone(model.model_zip)
        self.assertIsNotNone(model.model_volume_id)

    def test_add_model_ContradictingZipFileException(self):
        model = self.repo.model
        with open(self.repo.model_zip, "rb") as model_zip:
            kw = {
                "container_tag": model.container_tag,
                "human_readable_id": model.human_readable_id,
                "model_available": False
                }
            self.assertRaises(ContradictingZipFileException,
                              self.db.post_model,
                              zip_file=model_zip,
                              **kw)

    def test_add_model_ModelInsertionException(self):
        model = self.repo.model
        with open(self.repo.model_zip, "rb") as model_zip:
            kw = {
                "container_tag": model.container_tag,
                "human_readable_id": model.human_readable_id,
                "model_available": True,
                "model_mountpoint": "/model"
                }
            self.assertRaises(TypeError,
                              self.db.post_model,
                              zip_file=model_zip,
                              **kw)

    def test_get_model_intended_uid(self):
        model = self.test_add_model_intended()
        echo_model = self.db.get_model(uid=model.uid)
        self.assertEqual(model.dict(), echo_model.dict())

        echo_model = self.db.get_model(human_readable_id=model.human_readable_id)
        self.assertEqual(model.dict(), echo_model.dict())

    def test_get_model_ModelNotFoundException(self):
        self.assertRaises(ModelNotFoundException, self.db.get_model, uid="-1")
        self.assertRaises(ModelNotFoundException, self.db.get_model, human_readable_id="HeltUnikModel")

    def test_get_models(self):
        model = self.test_add_model_intended()
        models = self.db.get_models()
        self.assertEqual(len(models), 1)
        self.assertEqual(models[0].dict(), model.dict())

    def test_post_output(self):
        task = self.test_post_task_intended()
        with open(self.repo.output_zip, "rb") as r:
            echo_task = self.db.post_output_zip(task.uid, r)

        with open(task.output_zip, "rb") as ref_zip:
            with open(echo_task.output_zip, "rb") as echo_zip:
                self.assertEqual(ref_zip.read(), echo_zip.read())

    def test_post_output_TaskNotFound(self):
        with open(self.repo.output_zip, "rb") as r:
            self.assertRaises(TaskNotFoundException, self.db.post_output_zip, "AnthonioBanderas - dale!", r)



if __name__ == '__main__':
    unittest.main()
