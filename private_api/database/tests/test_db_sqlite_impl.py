import unittest

from database.db_exceptions import InsertTaskException, TaskNotFoundException, \
    ZipFileMissingException, ContradictingZipFileException, ModelInsertionException, ModelMountPointMissingException, \
    ModelNotFoundException
from database.db_sql_impl import DBSQLiteImpl
from testing.mock_components.mock_models_and_tasks import MockModelsAndTasks


class TestSQLiteImpl(unittest.TestCase):
    """
    This is a testing of functions in api/img/db_rest_impl.py
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


    def test_post_task_InsertTaskException(self):
        with open(self.repo.input_zip, "rb") as r:
            self.db.post_task(model_human_readable_id=self.repo.model.human_readable_id,
                                     zip_file=r,
                                     uid="asdf")

            self.assertRaises(InsertTaskException,
                          self.db.post_task,
                          model_human_readable_id=self.repo.model.human_readable_id,
                          zip_file=r,
                          uid="asdf")

    def test_set_task_status_intended(self):
        task = self.test_post_task_intended()
        self.assertEqual(task.status, -1)
        self.db.set_task_status_by_uid(task.uid, 0)

        new_retrieval = self.db.get_task_by_uid(task.uid)
        self.assertEqual(new_retrieval.status, 0)

        return task


    def test_get_task_by_id_intended(self):
        model = self.test_add_model_intended()
        ref_task = self.test_post_task_intended()
        db_task = self.db.get_task_by_id(ref_task.id)

        self.assertEqual(ref_task.to_dict(), db_task.to_dict())

    def test_get_task_by_id_TaskNotFoundException(self):
        self.assertRaises(TaskNotFoundException, self.db.get_task_by_id, -1)

    def test_get_task_by_uid_intended(self):
        ref_task = self.test_post_task_intended()
        db_task = self.db.get_task_by_uid(ref_task.uid)

        self.assertEqual(ref_task.to_dict(), db_task.to_dict())

    def test_get_task_by_uid_TaskNotFoundException(self):
        self.assertRaises(TaskNotFoundException, self.db.get_task_by_uid, "HeltUniktUid")

    def test_get_tasks(self):
        with open(self.repo.input_zip, "rb") as r:
            task = self.test_post_task_intended()

        tasks = self.db.get_tasks()
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].to_dict(), task.to_dict())

    def test_delete_task_by_uid_intended(self):
        task = self.test_post_task_intended()
        self.assertFalse(task.is_deleted)
        self.db.delete_task_by_uid(task.uid)

        self.assertRaises(TaskNotFoundException, self.db.get_task_by_uid, uid=task.uid)

    def test_delete_task_by_uid_TaskNotFoundException(self):
        self.assertRaises(TaskNotFoundException, self.db.get_task_by_uid, uid="some uid that does not exist")


    def test_add_model_intended(self):
        model = self.repo.model
        with open(self.repo.model_zip, "rb") as model_zip:
            echo_model = self.db.post_model(container_tag=model.container_tag,
                                           human_readable_id=model.human_readable_id,
                                           model_available=model.model_available,
                                           zip_file=model_zip,
                                           description=model.description,
                                           input_mountpoint=model.input_mountpoint,
                                           output_mountpoint=model.output_mountpoint,
                                           use_gpu=model.use_gpu,
                                           model_mountpoint=model.model_mountpoint
                                           )
        model = self.db.get_model_by_human_readable_id(echo_model.human_readable_id)

        self.assertEqual(echo_model.to_dict(), model.to_dict())

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
            "input_mountpoint": model.input_mountpoint,
            "output_mountpoint": model.output_mountpoint,
            "use_gpu": model.use_gpu,
            "model_mountpoint": model.model_mountpoint
        }
        self.assertRaises(ZipFileMissingException, self.db.post_model, **kw)


    def test_add_model_bare_minimum(self):
        model = self.repo.model
        with open(self.repo.model_zip, "rb") as model_zip:
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
            self.assertIsNone(model.model_volume_uuid)
            self.assertIsNone(model.model_mountpoint)
            self.assertEqual(model.input_mountpoint, "/input")
            self.assertEqual(model.output_mountpoint, "/output")
            self.assertIsNone(model.model_mountpoint)
            print(model.to_dict())



    def test_add_model_ModelInsertionException(self):
        model = self.repo.model
        with open(self.repo.model_zip, "rb") as model_zip:
            kw = {
                "container_tag": model.container_tag,
                "human_readable_id": model.human_readable_id,
                "model_available": True,
                "model_mountpoint": "/model"
                }
            self.db.post_model(zip_file=model_zip, **kw)
            self.assertRaises(ModelInsertionException,
                              self.db.post_model,
                              zip_file=model_zip,
                              **kw)

    def test_add_model_ModelMountPointMissingException(self):
        model = self.repo.model
        with open(self.repo.model_zip, "rb") as model_zip:
            kw = {
                "container_tag": model.container_tag,
                "human_readable_id": model.human_readable_id,
                "model_available": True
                }
            self.assertRaises(ModelMountPointMissingException,
                              self.db.post_model,
                              zip_file=model_zip,
                              **kw)

    def test_get_model_by_id_intended(self):
        model = self.test_add_model_intended()
        echo_model = self.db.get_model_by_id(model.id)
        self.assertEqual(model.to_dict(), echo_model.to_dict())

    def test_get_model_by_id_ModelNotFoundException(self):
        self.assertRaises(ModelNotFoundException, self.db.get_model_by_id, -1)

    def test_get_model_by_human_readable_id_ModelNotFoundException(self):
        self.assertRaises(ModelNotFoundException, self.db.get_model_by_human_readable_id, "HeltUnikModel")

    def test_get_models(self):
        model = self.test_add_model_intended()
        models = self.db.get_models()
        self.assertEqual(len(models), 1)
        self.assertEqual(models[0].to_dict(), model.to_dict())

    def test_post_output_by_uid(self):
        task = self.test_post_task_intended()
        with open(self.repo.output_zip, "rb") as r:
            echo_task = self.db.post_output_zip_by_uid(task.uid, r)

        with open(task.output_zip, "rb") as ref_zip:
            with open(echo_task.output_zip, "rb") as echo_zip:
                self.assertEqual(ref_zip.read(), echo_zip.read())

    def test_post_output_by_uid_TaskNotFound(self):
        with open(self.repo.output_zip, "rb") as r:
            self.assertRaises(TaskNotFoundException, self.db.post_output_zip_by_uid, "AnthonioBanderas - dale!", r)



if __name__ == '__main__':
    unittest.main()
