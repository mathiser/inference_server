import queue

from database.db_models import Task
from message_queue.mq_interface import MQInterface


class MockMQRabbitImpl(MQInterface):
    def __init__(self):
        self.unfinished_queue = queue.Queue()
        self.finished_queue = queue.Queue()
    def publish_finished_task(self, task: Task):
        self.finished_queue.put(task)

    def publish_unfinished_task(self, task: Task):
        self.unfinished_queue.put(task)
