import os
os.environ["LOG_LEVEL"] = "10"

import unittest

from database.db_exceptions import TaskNotFoundException, \
    TarFileMissingException, ContradictingTarFileException, ModelNotFoundException

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
        model = self.test_add_model_intended()
        with open(self.repo.input_tar, "rb") as r:
            task = self.db.post_task(human_readable_id=model.human_readable_id,
                                     tar_file=r)
        self.assertEqual(model.human_readable_id, task.model.human_readable_id)
        return task

    def test_set_task_status_intended(self):
        task = self.test_post_task_intended()
        self.assertEqual(task.status, -1)
        self.db.set_task_status(task.id, 0)

        new_retrieval = self.db.get_task(task_id=task.id)
        self.assertEqual(new_retrieval.status, 0)

        return task

    def test_get_task_intended(self):
        ref_task = self.test_post_task_intended()
        db_task = self.db.get_task(task_id=ref_task.id)

        self.assertEqual(ref_task.dict(), db_task.dict())

    def test_get_tasks(self):
        task = self.test_post_task_intended()
        tasks = self.db.get_tasks()
        self.assertEqual(len(tasks), 1)

        self.assertDictEqual(tasks[0].dict(), task.dict())

    def test_delete_task_intended(self):
        task = self.test_post_task_intended()
        self.assertFalse(task.is_deleted)
        self.db.delete_task(task.uid)

        self.assertIsNone(self.db.get_task(task_id=task.id))

    def test_delete_task_TaskNotFoundException(self):
        self.assertIsNone(self.db.get_task(task_id=99990))


    def test_add_model_intended(self):
        model = self.repo.model
        with open(self.repo.model_tar, "rb") as model_tar:
            echo_model = self.db.post_model(container_tag=model.container_tag,
                                            human_readable_id=model.human_readable_id,
                                            model_available=model.model_available,
                                            tar_file=model_tar,
                                            description=model.description,
                                            use_gpu=model.use_gpu,
                                            )
        model = self.db.get_model(human_readable_id=echo_model.human_readable_id)

        self.assertDictEqual(echo_model.dict(), model.dict())

        if echo_model.model_available:
            with open(self.repo.model_tar, "rb") as model_tar:
                with open(echo_model.model_tar, "rb") as db_model_tar:
                    self.assertEqual(model_tar.read(), db_model_tar.read())

        return echo_model

    def test_add_model_TarFileMissingException(self):
        model = self.repo.model
        kw = {
            "container_tag": model.container_tag,
            "human_readable_id": model.human_readable_id,
            "model_available": model.model_available,
            "tar_file": None,
            "description": model.description,
            "use_gpu": model.use_gpu,
        }
        self.assertRaises(TarFileMissingException, self.db.post_model, **kw)


    def test_add_model_bare_minimum(self):
        model = self.repo.model
        kw = {
            "container_tag": model.container_tag,
            "human_readable_id": model.human_readable_id,
        }
        model = self.db.post_model(**kw)
        self.assertIsNotNone(model)
        self.assertIsNotNone(model.id)
        self.assertEqual(model.human_readable_id, kw["human_readable_id"])
        self.assertIsNone(model.description)
        self.assertEqual(model.container_tag, kw["container_tag"])
        self.assertTrue(model.use_gpu)
        self.assertFalse(model.model_available)
        self.assertIsNone(model.model_tar)
        self.assertIsNotNone(model.model_volume_id)

    def test_add_model_ContradictingTarFileException(self):
        model = self.repo.model
        with open(self.repo.model_tar, "rb") as model_tar:
            kw = {
                "container_tag": model.container_tag,
                "human_readable_id": model.human_readable_id,
                "model_available": False
                }
            self.assertRaises(ContradictingTarFileException,
                              self.db.post_model,
                              tar_file=model_tar,
                              **kw)

    def test_add_model_ModelInsertionException(self):
        model = self.repo.model
        with open(self.repo.model_tar, "rb") as model_tar:
            kw = {
                "container_tag": model.container_tag,
                "human_readable_id": model.human_readable_id,
                "model_available": True,
                "model_mountpoint": "/model"
                }
            self.assertRaises(TypeError,
                              self.db.post_model,
                              tar_file=model_tar,
                              **kw)

    def test_get_model_intended_uid(self):
        model = self.test_add_model_intended()
        echo_model = self.db.get_model(model_id=model.id)
        self.assertEqual(model.dict(), echo_model.dict())

        echo_model = self.db.get_model(human_readable_id=model.human_readable_id)
        self.assertEqual(model.dict(), echo_model.dict())

    def test_get_model_ModelNotFoundException(self):
        self.assertRaises(ModelNotFoundException, self.db.get_model, model_id=-1)
        self.assertRaises(ModelNotFoundException, self.db.get_model, human_readable_id="HeltUnikModel")

    def test_get_models(self):
        model = self.test_add_model_intended()
        models = self.db.get_models()
        self.assertEqual(len(models), 1)
        self.assertEqual(models[0].dict(), model.dict())

    def test_post_output(self):
        task = self.test_post_task_intended()
        with open(self.repo.output_tar, "rb") as r:
            echo_task = self.db.post_output_tar(task.id, r)

        with open(task.output_tar, "rb") as ref_tar:
            with open(echo_task.output_tar, "rb") as echo_tar:
                self.assertEqual(ref_tar.read(), echo_tar.read())

    def test_post_output_TaskNotFound(self):
        with open(self.repo.output_tar, "rb") as r:
            self.assertRaises(TaskNotFoundException, self.db.post_output_tar, "AnthonioBanderas - dale!", r)



if __name__ == '__main__':
    unittest.main()
