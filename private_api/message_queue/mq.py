import logging

from database.db_interface import DBInterface, Task
from message_queue import MQRabbitImpl, MQInterface

LOG_FORMAT = ('%(levelname) -10s %(asctime)s %(name) -30s %(funcName) '
              '-35s %(lineno) -5d: %(message)s')
LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)


class MQ(MQInterface):
    def __init__(self, host, db: DBInterface):
        self.rabbit = MQRabbitImpl(host=host, db=db)

    def publish_unfinished_task(self, task: Task):
        return self.rabbit.publish_unfinished_task(task=task)

    def publish_finished_task(self, task: Task):
        return self.rabbit.publish_finished_task(task=task)
