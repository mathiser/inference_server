import os
import time
import unittest

import docker

from message_queue.rabbit_mq_impl import MQRabbitImpl
from .mock_ups.mock_db import MockDB

from dotenv import load_dotenv

load_dotenv()

cli = docker.from_env()

try:
    container = cli.containers.get(os.environ.get("RABBIT_NAME"))
    container.stop()
    container.remove()
except Exception as e:
    print(e)
cli.images.pull("rabbitmq:3.9.17")
rabbit_container = cli.containers.run("rabbitmq:3.9.17",
                                      name=os.environ.get("RABBIT_NAME"),
                                      hostname=os.environ.get("RABBIT_HOSTNAME"),
                                      ports={"5672": "5672"},
                                      detach=True)

class TestPublisherImpl(unittest.TestCase):
    """
    This is a tests of functions in api/img/message_queue/rabbit_mq_impl.py
    """

    def setUp(self) -> None:

        self.base_dir = ".tmp"
        self.db = MockDB()
        self.mq_client = None


        counter = 0
        while counter < 60:
            try:
                self.mq_client = MQRabbitImpl(os.environ.get("RABBIT_HOSTNAME"), self.db)
                break
            except Exception as e:
                print(e)
                counter += 5
                time.sleep(5)

    def test_publish_unfinished(self):
        self.mq_client.publish_unfinished_task(self.db.task1)
        method_frame, header_frame, body = self.mq_client.get_from_queue(self.mq_client.unfinished_queue_name)
        self.assertEqual(body.decode(), self.db.task1.uid)
        self.mq_client.ack_method_frame(method_frame)

        self.assertIsNone(self.mq_client.get_from_queue(self.mq_client.unfinished_queue_name))

    def test_publish_finished(self):
        self.mq_client.publish_finished_task(self.db.task1)
        method_frame, header_frame, body = self.mq_client.get_from_queue(self.mq_client.finished_queue_name)
        self.assertEqual(body.decode(), self.db.task1.uid)
        self.mq_client.ack_method_frame(method_frame)

        self.assertIsNone(self.mq_client.get_from_queue(self.mq_client.finished_queue_name))


if __name__ == '__main__':
    unittest.main()
