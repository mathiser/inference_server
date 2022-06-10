# import json
# import os
# import unittest
# from urllib.parse import urljoin
#
# import docker
# from docker import errors
# from dotenv import load_dotenv
# from fastapi.testclient import TestClient
#
# from api.api_fastapi_impl import APIFastAPIImpl
# from database import DBSQLiteImpl, Task, Model
# from database.db_exceptions import InsertTaskException, TaskNotFoundException, ZipFileMissingException, \
#     ContradictingZipFileException, ModelInsertionException, ModelMountPointMissingException, ModelNotFoundException
# from message_queue.rabbit_mq_impl import MQRabbitImpl
# from testing.mock_components.mock_models_and_tasks import MockModelsAndTasks
#
# load_dotenv(dotenv_path="testing/.env")
# cli = docker.from_env()
# RABBIT_NAME = "rapper_rabbit"
# RABBIT_HOST = "localhost"
# RABBIT_PORT = 5672
#
# try:
#     container = cli.containers.get(RABBIT_NAME)
#     container.stop()
#     container.remove()
# except errors.NotFound as e:
#     print(e)
#
# print(os.environ)
# cli.images.pull(os.environ.get("RABBIT_DOCKER_TAG"))
# print("Spinning up RabbitMQ")
#
# rabbit_container = cli.containers.run(os.environ.get("RABBIT_DOCKER_TAG"),
#                                       name=RABBIT_NAME,
#                                       hostname=RABBIT_HOST,
#                                       ports={RABBIT_PORT: RABBIT_PORT},
#                                       detach=True)
# print(rabbit_container)
#
#
# class TestFastAPIImpl(unittest.TestCase):
#     """
#     This is a testing of functions in api/img/api/private_fastapi_impl.py
#     """
#
#     def setUp(self) -> None:
#         self.hostname = "localhost"
#         self.port = 7000
#         self.base_url = f"http://{self.hostname}:{self.port}"
#
#         self.base_dir = ".tmp"
#         self.repo = MockModelsAndTasks()
#         self.db = DBSQLiteImpl(base_dir=self.base_dir)
#
#         self.RABBIT_HOST = "localhost"
#         self.RABBIT_PORT = 5672
#         self.mq = MQRabbitImpl(host=self.RABBIT_HOST,
#                                port=self.RABBIT_PORT,
#                                unfinished_queue_name="UNFINISHED_JOB_QUEUE",
#                                finished_queue_name="FINISHED_JOB_QUEUE")
#
#         self.app = APIFastAPIImpl(db=self.db, mq=self.mq)
#         self.cli = TestClient(self.app)
#
#     def tearDown(self) -> None:
#         self.db.purge()
#         self.repo.purge()
#
#     def test_hello_world(self):
#         res = self.cli.get("/")
#         self.assertIn("message", res.json().keys())
#         self.assertIn("Hello world", res.json()["message"])
#
#     def test_post_task_intended(self):
#         with open(self.repo.input_zip, "rb") as r:
#             res = self.cli.post(os.environ.get("POST_TASK"),
#                                 params={"model_human_readable_id": self.repo.model.human_readable_id},
#                                 files={"zip_file": r})
#             task = Task(**json.loads(res.content))
#         self.assertIn(self.repo.model.human_readable_id, task.model_human_readable_id)
#         return task
#
#     def test_post_task_InsertTaskException(self):
#         with open(self.repo.input_zip, "rb") as r:
#             params = {"model_human_readable_id": self.repo.model.human_readable_id,
#                       "uid": "asdf"}
#             files = {"zip_file": r}
#             res = self.cli.post(os.environ.get("POST_TASK"),
#                                 params=params,
#                                 files=files)
#             task = Task(**json.loads(res.content))
#
#             self.assertRaises(InsertTaskException,
#                               self.cli.post,
#                               url=os.environ.get("POST_TASK"),
#                               params=params,
#                               files=files)
#
#     def test_get_task_by_id_intended(self):
#         model = self.test_post_model_intended()
#         ref_task = self.test_post_task_intended()
#         db_task_res = self.cli.get(urljoin(os.environ['GET_TASK_BY_ID'], str(ref_task.id)))
#         db_task = Task(**json.loads(db_task_res.content))
#
#         self.assertEqual(ref_task.to_dict(), db_task.to_dict())
#
#     def test_get_task_by_id_TaskNotFoundException(self):
#         self.assertRaises(TaskNotFoundException, self.db.get_task_by_id, -1)
#
#     def test_get_task_by_uid_intended(self):
#         ref_task = self.test_post_task_intended()
#         db_task_res = self.cli.get(urljoin(os.environ['GET_TASK_BY_UID'], str(ref_task.uid)))
#         db_task = Task(**json.loads(db_task_res.content))
#
#         self.assertEqual(ref_task.to_dict(), db_task.to_dict())
#
#     def test_get_task_by_uid_TaskNotFoundException(self):
#         self.assertRaises(TaskNotFoundException,
#                           self.cli.get,
#                           url=urljoin(os.environ['GET_TASK_BY_UID'], "HeltUniktUid"))
#
#     def test_get_tasks(self):
#         task = self.test_post_task_intended()
#
#         tasks_res = self.cli.get(os.environ["GET_TASKS"])
#         tasks = [Task(**t) for t in json.loads(tasks_res.content)]
#         self.assertEqual(len(tasks), 1)
#         self.assertEqual(tasks[0].to_dict(), task.to_dict())
#
#     def test_post_model_intended(self):
#         model = self.repo.model
#
#         with open(self.repo.model_zip, "rb") as model_zip:
#             params = {
#                 "container_tag": model.container_tag,
#                 "human_readable_id": model.human_readable_id,
#                 "model_available": model.model_available,
#                 "description": model.description,
#                 "input_mountpoint": model.input_mountpoint,
#                 "output_mountpoint": model.output_mountpoint,
#                 "use_gpu": model.use_gpu,
#                 "model_mountpoint": model.model_mountpoint
#             }
#             files = {"zip_file": model_zip}
#
#             echo_model_res = self.cli.post(url=os.environ.get("POST_MODEL"),
#                                            params=params,
#                                            files=files
#                                            )
#             echo_model = Model(**json.loads(echo_model_res.content))
#             model = self.db.get_model_by_human_readable_id(echo_model.human_readable_id)
#
#             self.assertEqual(echo_model.to_dict(), model.to_dict())
#
#             if echo_model.model_available:
#                 with open(self.repo.model_zip, "rb") as model_zip:
#                     with open(echo_model.model_zip, "rb") as db_model_zip:
#                         self.assertEqual(model_zip.read(), db_model_zip.read())
#
#             return echo_model
#
#     def test_post_model_ZipFileMissingException(self):
#         model = self.repo.model
#         params = {
#             "container_tag": model.container_tag,
#             "human_readable_id": model.human_readable_id,
#             "model_available": model.model_available,
#             "zip_file": None,
#             "description": model.description,
#             "input_mountpoint": model.input_mountpoint,
#             "output_mountpoint": model.output_mountpoint,
#             "use_gpu": model.use_gpu,
#             "model_mountpoint": model.model_mountpoint
#         }
#
#         self.assertRaises(ZipFileMissingException,
#                           self.cli.post,
#                           url=os.environ.get("POST_MODEL"),
#                           params=params)
#
#     def test_post_model_bare_minimum(self):
#         model = self.repo.model
#
#         params = {
#             "container_tag": model.container_tag,
#             "human_readable_id": model.human_readable_id,
#         }
#         model_res = self.cli.post(url=os.environ.get("POST_MODEL"),
#                       params=params,
#                       files="")
#
#         if model_res.ok:
#             model = Model(**json.loads(model_res.content))
#             print(model.to_dict())
#
#             self.assertIsNotNone(model)
#             self.assertIsNotNone(model.id)
#             self.assertIsNotNone(model.uid)
#             self.assertEqual(model.human_readable_id, params["human_readable_id"])
#             self.assertIsNone(model.description)
#             self.assertEqual(model.container_tag, params["container_tag"])
#             self.assertTrue(model.use_gpu)
#             self.assertFalse(model.model_available)
#             self.assertIsNone(model.model_zip)
#             self.assertIsNone(model.model_volume_uuid)
#             self.assertIsNone(model.model_mountpoint)
#             self.assertEqual(model.input_mountpoint, "/input")
#             self.assertEqual(model.output_mountpoint, "/output")
#             self.assertIsNone(model.model_mountpoint)
#
#
#     def test_post_model_ContradictingZipFileException(self):
#         model = self.repo.model
#         with open(self.repo.model_zip, "rb") as model_zip:
#             params = {
#                 "container_tag": model.container_tag,
#                 "human_readable_id": model.human_readable_id,
#                 "model_available": False
#             }
#             self.assertRaises(ContradictingZipFileException,
#                               self.cli.post,
#                               url=os.environ["POST_MODEL"],
#                               params=params,
#                               files={"zip_file": model_zip},
#                               )
#
#     def test_post_model_ModelInsertionException(self):
#         model = self.repo.model
#         with open(self.repo.model_zip, "rb") as model_zip:
#             params = {
#                 "container_tag": model.container_tag,
#                 "human_readable_id": model.human_readable_id,
#                 "model_available": True,
#                 "model_mountpoint": "/model"
#             }
#             self.cli.post(os.environ.get("POST_MODEL"),
#                           params=params,
#                           files={"zip_file": model_zip})
#
#             self.assertRaises(ModelInsertionException,
#                               self.cli.post,
#                               url=os.environ.get("POST_MODEL"),
#                               params=params,
#                               files={"zip_file": model_zip}
#                               )
#
#     def test_post_model_ModelMountPointMissingException(self):
#         model = self.repo.model
#         with open(self.repo.model_zip, "rb") as model_zip:
#             params = {
#                 "container_tag": model.container_tag,
#                 "human_readable_id": model.human_readable_id,
#                 "model_available": True
#             }
#
#             self.assertRaises(ModelMountPointMissingException,
#                               self.cli.post,
#                               url=os.environ.get("POST_MODEL"),
#                               params=params,
#                               files={"zip_file": model_zip}
#                               )
#
#     def test_post_model_ContradictingZipFileException(self):
#         model = self.repo.model
#         with open(self.repo.model_zip, "rb") as model_zip:
#             params = {
#                 "container_tag": model.container_tag,
#                 "human_readable_id": model.human_readable_id,
#                 "model_available": False
#             }
#             self.assertRaises(ContradictingZipFileException,
#                             self.cli.post,
#                             url=os.environ.get("POST_MODEL"),
#                             params=params,
#                             files={"zip_file": model_zip}
#                             )
#
#     def test_get_model_by_id_intended(self):
#         model = self.test_post_model_intended()
#         echo_model_res = self.cli.get(urljoin(os.environ.get("GET_MODEL_BY_ID"), str(model.id)))
#         echo_model = Model(**json.loads(echo_model_res.content))
#         self.assertEqual(model.to_dict(), echo_model.to_dict())
#
#     def test_get_model_by_id_ModelNotFoundException(self):
#         self.assertRaises(ModelNotFoundException,
#                           self.cli.get,
#                           url=urljoin(os.environ.get("GET_MODEL_BY_ID"), str(-1)))
#
#     def test_get_model_by_human_readable_id_ModelNotFoundException(self):
#         self.assertRaises(ModelNotFoundException,
#                           self.cli.get,
#                           url=urljoin(os.environ.get("GET_MODEL_BY_HUMAN_READABLE_ID"), "Muy Importante Modelle"))    #
#
#     def test_get_models(self):
#         model = self.test_post_model_intended()
#
#         models_res = self.cli.get(os.environ["GET_MODELS"])
#         models = [Model(**t) for t in json.loads(models_res.content)]
#         self.assertEqual(len(models), 1)
#         self.assertEqual(models[0].to_dict(), model.to_dict())
#
#     def test_post_output_zip_by_uid(self):
#         task = self.test_post_task_intended()
#         with open(self.repo.output_zip, "rb") as r:
#             echo_task_res = self.cli.post(urljoin(os.environ.get("POST_OUTPUT_ZIP_BY_UID"), task.uid),
#                                      files={"zip_file": r})
#             echo_task = Task(**json.loads(echo_task_res.content))
#
#         with open(task.output_zip, "rb") as ref_zip:
#             with open(echo_task.output_zip, "rb") as echo_zip:
#                 self.assertEqual(ref_zip.read(), echo_zip.read())
#
#     def test_post_output_by_uid_TaskNotFound(self):
#         with open(self.repo.output_zip, "rb") as r:
#             self.assertRaises(TaskNotFoundException,
#                               self.cli.post,
#                               url=urljoin(os.environ.get("POST_OUTPUT_ZIP_BY_UID"), "AnthonioBanderas - dale!"),
#                               files={"zip_file": r})
#
#
# if __name__ == '__main__':
#     unittest.main()
