import logging
import secrets
from typing import Optional, BinaryIO, Union

from database import DBInterface, Task, Model
from message_queue import MQInterface
from .private_api_interface import PrivateAPIInterface

LOG_FORMAT = '%(levelname)s:%(asctime)s:%(message)s'

logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)


class PrivateAPIImpl(PrivateAPIInterface):
    def __init__(self, db: DBInterface, mq: MQInterface):
        self.db = db
        self.mq = mq

    def hello_world(self):
        logging.info("Hello world - Welcome to the private database API")
        return {"message": "Hello world - Welcome to the private database API"}

    def get_tasks(self):
        return self.db.get_tasks()

    def get_task_by_id(self, id: int):
        return self.db.get_task_by_id(id=id)

    def get_task_by_uid(self, uid: str):
        return self.db.get_task_by_uid(uid=uid)

    def post_task(self, model_human_readable_id: str,
                  zip_file: BinaryIO,
                  uid=None) -> Task:

        if not uid:
            uid = secrets.token_urlsafe(32)

        t = self.db.post_task(zip_file=zip_file,
                             model_human_readable_id=model_human_readable_id,
                             uid=uid)

        self.mq.publish_unfinished_task(t)

        return t

    def post_output_zip_by_uid(self, uid: str, zip_file: BinaryIO) -> Task:

        # Get the task
        task = self.db.post_output_zip_by_uid(uid=uid,
                                          zip_file=zip_file)

        # Publish the finished job to "finished_jobs"
        self.mq.publish_finished_task(task=task)

        return task

    def post_model(self,
                   container_tag: str,
                   human_readable_id: str,
                   input_mountpoint: Union[str, None] = None,
                   output_mountpoint: Union[str, None] = None,
                   model_mountpoint: Union[str, None] = None,
                   description: Union[str, None] = None,
                   zip_file: Union[BinaryIO, None] = None,
                   model_available: Union[bool, None] = None,
                   use_gpu: Union[bool, None] = None,
                   ) -> Model:

        return self.db.post_model(
            container_tag=container_tag,
            human_readable_id=human_readable_id,
            input_mountpoint=input_mountpoint,
            output_mountpoint=output_mountpoint,
            zip_file=zip_file,
            model_mountpoint=model_mountpoint,
            description=description,
            model_available=model_available,
            use_gpu=use_gpu,
        )

    def get_model_by_id(self, id: int):
        return self.db.get_model_by_id(id=id)

    def get_model_by_human_readable_id(self, human_readable_id: str):
        return self.db.get_model_by_human_readable_id(human_readable_id=human_readable_id)

    def get_models(self):
        return self.db.get_models()