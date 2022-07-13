import os
import time
import unittest

import docker
from docker import errors
from message_queue.rabbit_mq_impl import MQRabbitImpl
from testing.mock_components.mock_db import MockDB
from testing.mock_components.mock_models_and_tasks import MockModelsAndTasks
from dotenv import load_dotenv

load_dotenv(dotenv_path="testing/.test_env")
cli = docker.from_env()
RABBIT_NAME = "rapper_rabbit"
RABBIT_HOSTNAME = "localhost"
RABBIT_PORT = 5672

try:
    container = cli.containers.get(RABBIT_NAME)
    container.stop()
    container.remove()
except errors.NotFound as e:
    print(e)
print(os.environ)
cli.images.pull(os.environ.get("RABBIT_DOCKER_TAG"))
print("Spinning up RabbitMQ")

rabbit_container = cli.containers.run(os.environ.get("RABBIT_DOCKER_TAG"),
                                      name=RABBIT_NAME,
                                      hostname=RABBIT_HOSTNAME,
                                      ports={RABBIT_PORT: RABBIT_PORT},
                                      detach=True)
print(rabbit_container)


class TestMessageQueueRabbitMQImpl(unittest.TestCase):
    """
    This is a tests of functions in api/img/message_queue/rabbit_mq_impl.py
    """

    def setUp(self) -> None:
        self.base_dir = ".tmp"
        self.db = MockDB()
        self.repo = MockModelsAndTasks()
        self.mq_client = None

        self.mq_client = MQRabbitImpl(host=RABBIT_HOSTNAME,
                                      port=int(RABBIT_PORT),
                                      unfinished_queue_name=os.environ["UNFINISHED_JOB_QUEUE"],
                                      finished_queue_name=os.environ["FINISHED_JOB_QUEUE"])

    def test_get_connection_and_channel(self):
        self.conn, self.chan = self.mq_client.get_connection_and_channel()
        self.assertTrue(self.conn.is_open)
        self.assertTrue(self.chan.is_open)
        return self.conn, self.chan

    def test_publish_unfinished(self):
        self.mq_client.publish_unfinished_task(self.repo.task)
        conn, chan = self.mq_client.get_connection_and_channel()
        method_frame, header_frame, body = chan.basic_get(self.mq_client.unfinished_queue_name)
        self.assertEqual(body.decode(), self.repo.task.uid)
        chan.basic_ack(method_frame.delivery_tag)
        self.mq_client.close(conn, chan)

    def test_publish_finished(self):
        self.mq_client.publish_finished_task(self.repo.task)
        conn, chan = self.mq_client.get_connection_and_channel()
        method_frame, header_frame, body = chan.basic_get(self.mq_client.finished_queue_name)
        self.assertEqual(body.decode(), self.repo.task.uid)
        chan.basic_ack(method_frame.delivery_tag)
        self.mq_client.close(conn, chan)

if __name__ == '__main__':
    unittest.main()
