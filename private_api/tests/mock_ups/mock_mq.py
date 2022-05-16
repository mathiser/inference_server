from private_api.img.database.models import Task
from private_api.img.message_queue.mq_interface import MQInterface


class MockMQ(MQInterface):
    unfinished = []
    finished = []
    def publish_unfinished_task(cls, task: Task):
        cls.unfinished.append(task.uid)
        return task

    def publish_finished_task(cls, task: Task):
        cls.finished.append(task.uid)
        return task